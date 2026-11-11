from decimal import Decimal
from rest_framework import viewsets, permissions, status
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from drf_spectacular.utils import extend_schema
from drf_spectacular.types import OpenApiTypes

from apps.wholesale.models import PriceTier, CustomerCreditLimit, CreditTransaction
from apps.wholesale.serializers import (
    PriceTierSerializer,
    CustomerCreditLimitSerializer,
    CreditTransactionSerializer,
    SettleKhataPayloadSerializer,
)
from apps.sales.models import Customer
from apps.accounting.models import Account, JournalEntry, JournalLine
from common.utils.money import round_money


class PriceTierViewSet(viewsets.ModelViewSet):
    """
    Volume discount pricing tiers for wholesale customers (e.g. 10+ units: 5% off, 50+ units: 10% off).
    """
    serializer_class = PriceTierSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        org = getattr(self.request, "organization", None)
        if not org:
            return PriceTier.objects.none()
        return PriceTier.objects.filter(organization=org).order_by("min_quantity")

    def perform_create(self, serializer):
        org = getattr(self.request, "organization", None)
        serializer.save(organization=org)


class CustomerCreditLimitViewSet(viewsets.ModelViewSet):
    """
    Wholesale customer credit limits, grace periods, and account blocking.
    """
    serializer_class = CustomerCreditLimitSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        org = getattr(self.request, "organization", None)
        if not org:
            return CustomerCreditLimit.objects.none()
        return CustomerCreditLimit.objects.filter(organization=org).select_related("customer")

    def perform_create(self, serializer):
        org = getattr(self.request, "organization", None)
        serializer.save(organization=org)

    @extend_schema(
        description="Toggles credit hold blocking or unblocking a customer from making credit purchases.",
        responses={200: CustomerCreditLimitSerializer},
    )
    @action(detail=True, methods=["post"], url_path="toggle-block")
    def toggle_block(self, request, pk=None):
        limit_obj = self.get_object()
        limit_obj.is_blocked = not limit_obj.is_blocked
        limit_obj.save(update_fields=["is_blocked", "updated_at"])
        return Response(CustomerCreditLimitSerializer(limit_obj).data)


class CreditTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Audit ledger of all customer Khata purchases, payments, and settlements.
    """
    serializer_class = CreditTransactionSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        org = getattr(self.request, "organization", None)
        if not org:
            return CreditTransaction.objects.none()
        qs = CreditTransaction.objects.filter(organization=org).select_related("customer")
        customer_id = self.request.query_params.get("customer_id")
        if customer_id:
            qs = qs.filter(customer_id=customer_id)
        return qs.order_by("-created_at")


class SettleWholesaleKhataAPIView(APIView):
    """
    POST /api/v1/wholesale/credit/settle/
    Records customer Khata payment, decrements Accounts Receivable, and posts balanced double-entry journals.
    """
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        request=SettleKhataPayloadSerializer,
        responses={200: OpenApiTypes.OBJECT},
        description="Settles customer Khata credit balance and records financial journal entry.",
    )
    def post(self, request):
        org = getattr(request, "organization", None)
        if not org:
            return Response({"error": "No tenant organization specified."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = SettleKhataPayloadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        cust_id = serializer.validated_data["customer_id"]
        amount = round_money(serializer.validated_data["amount"])
        tender = serializer.validated_data["payment_method"]
        notes = serializer.validated_data.get("notes", "")

        with transaction.atomic():
            customer = Customer.objects.select_for_update().filter(id=cust_id, organization=org).first()
            if not customer:
                return Response({"error": "Customer not found."}, status=status.HTTP_404_NOT_FOUND)

            new_balance = max(Decimal("0.00"), customer.current_credit - amount)
            customer.current_credit = new_balance
            customer.save(update_fields=["current_credit", "updated_at"])

            ref_id = f"SETTLE-{timezone_now_ts()}"
            tx = CreditTransaction.objects.create(
                organization=org,
                customer=customer,
                transaction_type="PAYMENT_CREDIT",
                amount=amount,
                balance_after=new_balance,
                reference_id=ref_id,
                notes=f"Payment via {tender}. {notes}".strip(),
            )

            # Post double-entry journal (Debit Cash/Bank, Credit AR)
            acct_ar, _ = Account.objects.get_or_create(
                organization=org,
                account_code="1100",
                defaults={"account_name": "Accounts Receivable (Khata)", "account_type": "ASSET"},
            )
            asset_code = "1000" if tender == "CASH" else "1010"
            asset_name = "Cash in Hand" if tender == "CASH" else f"Bank / Digital Wallet ({tender})"
            acct_asset, _ = Account.objects.get_or_create(
                organization=org,
                account_code=asset_code,
                defaults={"account_name": asset_name, "account_type": "ASSET"},
            )

            entry_num = f"JE-SETTLE-{tx.id.hex[:6].upper()}"
            je = JournalEntry.objects.create(
                organization=org,
                entry_number=entry_num,
                reference_type="KhataSettlement",
                reference_id=ref_id,
                description=f"Khata payment of Rs. {amount} by {customer.name} via {tender}",
            )
            JournalLine.objects.create(journal_entry=je, account=acct_asset, debit=amount, credit=Decimal("0.00"))
            JournalLine.objects.create(journal_entry=je, account=acct_ar, debit=Decimal("0.00"), credit=amount)
            je.post()

        return Response({
            "success": True,
            "customer_id": str(customer.id),
            "customer_name": customer.name,
            "settled_amount_npr": str(amount),
            "remaining_debt_npr": str(new_balance),
            "payment_method": tender,
            "journal_entry": entry_num,
        })


def timezone_now_ts():
    from django.utils import timezone
    return int(timezone.now().timestamp())
