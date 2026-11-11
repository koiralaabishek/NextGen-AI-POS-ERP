from decimal import Decimal
from django.utils import timezone
from django.db.models import Sum
from rest_framework import viewsets, status, permissions
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from apps.pos.models import PosTerminal, CashierShift, HeldSale
from apps.payments.models import Payment
from apps.pos.serializers import (
    PosTerminalSerializer,
    CashierShiftSerializer,
    CloseShiftSerializer,
    HeldSaleSerializer,
    CheckoutRequestSerializer,
)
from apps.pos.services import CheckoutService
from apps.sales.serializers import SaleSerializer
from common.permissions.tenant import IsTenantMember
from common.utils.money import round_money, ZERO_MONEY


class CheckoutAPIView(APIView):
    """
    POST /api/v1/pos/checkout/
    Idempotent, authoritative POS transaction processing endpoint.
    Recalculates prices, updates stock, records payments, creates invoice.
    """
    permission_classes = [permissions.IsAuthenticated, IsTenantMember]
    serializer_class = CheckoutRequestSerializer

    @extend_schema(
        request=CheckoutRequestSerializer,
        responses={201: SaleSerializer},
        description="Processes an authoritative, idempotent checkout transaction. Deducts physical inventory and posts accounting journal lines.",
    )
    def post(self, request, *args, **kwargs):
        serializer = CheckoutRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        sale = CheckoutService.process_checkout(
            organization=request.organization,
            user=request.user,
            client_transaction_id=data["client_transaction_id"],
            branch_id=data["branch_id"],
            terminal_id=data.get("terminal_id"),
            customer_id=data.get("customer_id"),
            items=data["items"],
            payments=data["payments"],
            currency=data.get("currency", "NPR"),
            notes=data.get("notes", ""),
        )

        output_serializer = SaleSerializer(sale)
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)


class PosTerminalViewSet(viewsets.ModelViewSet):
    serializer_class = PosTerminalSerializer
    permission_classes = [permissions.IsAuthenticated, IsTenantMember]

    def get_queryset(self):
        return PosTerminal.objects.filter(organization=self.request.organization)


class CashierShiftViewSet(viewsets.ModelViewSet):
    serializer_class = CashierShiftSerializer
    permission_classes = [permissions.IsAuthenticated, IsTenantMember]

    def get_queryset(self):
        return CashierShift.objects.filter(organization=self.request.organization).select_related(
            "terminal", "cashier"
        )

    def perform_create(self, serializer):
        serializer.save(
            organization=self.request.organization,
            cashier=self.request.user
        )

    @extend_schema(
        responses={200: CashierShiftSerializer},
        description="Returns the currently active OPEN shift for the authenticated cashier.",
    )
    @action(detail=False, methods=["get"], url_path="current")
    def current(self, request):
        shift = CashierShift.objects.filter(
            organization=request.organization,
            cashier=request.user,
            status="OPEN"
        ).first()
        if not shift:
            return Response({"active_shift": None}, status=status.HTTP_200_OK)
        return Response({"active_shift": CashierShiftSerializer(shift).data})

    @extend_schema(
        request=CloseShiftSerializer,
        responses={200: CashierShiftSerializer},
        description="Closes the cashier shift, computes expected cash, and records any cash discrepancy.",
    )
    @action(detail=True, methods=["post"], url_path="close")
    def close(self, request, pk=None):
        shift = self.get_object()
        if shift.status != "OPEN":
            return Response(
                {"error": f"Shift is already {shift.status}."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        serializer = CloseShiftSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        closing_cash = round_money(serializer.validated_data["closing_cash"])
        notes = serializer.validated_data.get("notes", "")

        # Compute cash payments recorded between shift open and now
        cash_sales = Payment.objects.filter(
            sale__organization=request.organization,
            sale__terminal=shift.terminal,
            sale__cashier=shift.cashier,
            payment_method="CASH",
            status="SUCCESS",
            created_at__gte=shift.opened_at,
        ).aggregate(total=Sum("amount"))["total"] or ZERO_MONEY

        expected_cash = round_money(shift.opening_cash + cash_sales)
        discrepancy = round_money(closing_cash - expected_cash)

        shift.closing_cash = closing_cash
        shift.expected_cash = expected_cash
        shift.discrepancy = discrepancy
        shift.notes = (shift.notes + "\n" + notes).strip()
        shift.status = "CLOSED"
        shift.closed_at = timezone.now()
        shift.save()

        return Response(CashierShiftSerializer(shift).data)


class HeldSaleViewSet(viewsets.ModelViewSet):
    serializer_class = HeldSaleSerializer
    permission_classes = [permissions.IsAuthenticated, IsTenantMember]

    def get_queryset(self):
        qs = HeldSale.objects.filter(organization=self.request.organization)
        terminal_id = self.request.query_params.get("terminal_id")
        if terminal_id:
            qs = qs.filter(terminal_id=terminal_id)
        return qs

    def perform_create(self, serializer):
        serializer.save(organization=self.request.organization)
