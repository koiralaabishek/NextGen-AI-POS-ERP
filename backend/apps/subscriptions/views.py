from datetime import timedelta
from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from drf_spectacular.types import OpenApiTypes
from apps.subscriptions.models import Plan, Subscription, SubscriptionInvoice
from apps.subscriptions.serializers import (
    PlanSerializer,
    SubscriptionSerializer,
    UpgradePlanRequestSerializer,
)


class PlanViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Public and tenant listing of available SaaS subscription tiers (Starter, Professional, Enterprise).
    """
    queryset = Plan.objects.filter(is_active=True).prefetch_related("features")
    serializer_class = PlanSerializer
    permission_classes = [permissions.AllowAny]


class SubscriptionViewSet(viewsets.ModelViewSet):
    """
    Manage tenant subscription, inspect entitlements, and execute plan upgrade/downgrade.
    """
    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        org = getattr(self.request, "organization", None)
        if not org:
            return Subscription.objects.none()
        return Subscription.objects.filter(organization=org).select_related("plan").prefetch_related("invoices")

    @extend_schema(
        request=UpgradePlanRequestSerializer,
        responses={200: SubscriptionSerializer},
        description="Upgrades or switches the tenant's current SaaS subscription plan and generates an invoice.",
    )
    @action(detail=False, methods=["post"], url_path="upgrade")
    def upgrade_plan(self, request):
        org = getattr(request, "organization", None)
        if not org:
            return Response({"error": "No active tenant organization specified in headers."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = UpgradePlanRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        plan_id = serializer.validated_data["plan_id"]
        interval = serializer.validated_data["billing_interval"]

        try:
            target_plan = Plan.objects.get(id=plan_id, is_active=True)
        except Plan.DoesNotExist:
            return Response({"error": "Invalid plan selected."}, status=status.HTTP_404_NOT_FOUND)

        now = timezone.now()
        duration_days = 365 if interval == "ANNUAL" else 30
        end_date = now + timedelta(days=duration_days)

        # Deactivate previous active subscription
        Subscription.objects.filter(organization=org, status="ACTIVE").update(status="EXPIRED")

        # Create new active subscription
        subscription = Subscription.objects.create(
            organization=org,
            plan=target_plan,
            status="ACTIVE",
            start_date=now,
            end_date=end_date,
            is_auto_renew=True,
        )

        # Generate invoice
        inv_number = f"SUB-{now.year}{now.month:02d}-{subscription.id.hex[:6].upper()}"
        price = target_plan.price_npr * (12 if interval == "ANNUAL" else 1)
        SubscriptionInvoice.objects.create(
            subscription=subscription,
            invoice_number=inv_number,
            amount=price,
            status="PAID",
            paid_at=now,
            provider_transaction_id=f"SUB-TX-{now.timestamp()}",
        )

        output_serializer = SubscriptionSerializer(subscription)
        return Response(output_serializer.data, status=status.HTTP_200_OK)
