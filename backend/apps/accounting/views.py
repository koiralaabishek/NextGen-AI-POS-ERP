from rest_framework import viewsets, permissions, filters, status
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from apps.accounting.models import (
    Account,
    JournalEntry,
    FiscalPeriod,
    Expense,
    TaxRate,
)
from apps.accounting.serializers import (
    AccountSerializer,
    JournalEntrySerializer,
    FiscalPeriodSerializer,
    ExpenseSerializer,
    TaxRateSerializer,
)
from apps.accounting.services.reports import FinancialReportService
from common.permissions.tenant import IsTenantMember


class AccountViewSet(viewsets.ModelViewSet):
    serializer_class = AccountSerializer
    permission_classes = [permissions.IsAuthenticated, IsTenantMember]

    def get_queryset(self):
        return Account.objects.filter(organization=self.request.organization)


class JournalEntryViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = JournalEntrySerializer
    permission_classes = [permissions.IsAuthenticated, IsTenantMember]
    filter_backends = [filters.SearchFilter]
    search_fields = ["entry_number", "description", "reference_id"]

    def get_queryset(self):
        return JournalEntry.objects.filter(organization=self.request.organization).prefetch_related("lines", "lines__account")


class FiscalPeriodViewSet(viewsets.ModelViewSet):
    serializer_class = FiscalPeriodSerializer
    permission_classes = [permissions.IsAuthenticated, IsTenantMember]

    def get_queryset(self):
        return FiscalPeriod.objects.filter(organization=self.request.organization)

    @extend_schema(description="Locks a fiscal period, preventing subsequent accounting postings.")
    @action(detail=True, methods=["post"], url_path="close")
    def close_period(self, request, pk=None):
        period = self.get_object()
        period.is_closed = True
        period.save(update_fields=["is_closed", "updated_at"])
        return Response(FiscalPeriodSerializer(period).data)


class ExpenseViewSet(viewsets.ModelViewSet):
    serializer_class = ExpenseSerializer
    permission_classes = [permissions.IsAuthenticated, IsTenantMember]

    def get_queryset(self):
        return Expense.objects.filter(organization=self.request.organization)


class TaxRateViewSet(viewsets.ModelViewSet):
    serializer_class = TaxRateSerializer
    permission_classes = [permissions.IsAuthenticated, IsTenantMember]

    def get_queryset(self):
        return TaxRate.objects.filter(organization=self.request.organization)


# ==============================================================================
# Financial & Tax Reporting Endpoints
# ==============================================================================

class TrialBalanceAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsTenantMember]

    @extend_schema(
        parameters=[
            OpenApiParameter("start_date", str, required=False),
            OpenApiParameter("end_date", str, required=False),
        ],
        responses={200: OpenApiTypes.OBJECT},
        description="Generates Trial Balance report verifying sum(Debits) == sum(Credits).",
    )
    def get(self, request):
        start = request.query_params.get("start_date")
        end = request.query_params.get("end_date")
        data = FinancialReportService.get_trial_balance(request.organization, start, end)
        return Response(data)


class ProfitAndLossAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsTenantMember]

    @extend_schema(
        parameters=[
            OpenApiParameter("start_date", str, required=False),
            OpenApiParameter("end_date", str, required=False),
        ],
        responses={200: OpenApiTypes.OBJECT},
        description="Generates Income Statement (Profit & Loss): Revenue - Expenses = Net Profit.",
    )
    def get(self, request):
        start = request.query_params.get("start_date")
        end = request.query_params.get("end_date")
        data = FinancialReportService.get_profit_and_loss(request.organization, start, end)
        return Response(data)


class BalanceSheetAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsTenantMember]

    @extend_schema(
        parameters=[
            OpenApiParameter("as_of_date", str, required=False),
        ],
        responses={200: OpenApiTypes.OBJECT},
        description="Generates Balance Sheet as of a given date (Assets = Liabilities + Equity).",
    )
    def get(self, request):
        as_of = request.query_params.get("as_of_date")
        data = FinancialReportService.get_balance_sheet(request.organization, as_of)
        return Response(data)


class VatSalesBookAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsTenantMember]

    @extend_schema(
        parameters=[
            OpenApiParameter("start_date", str, required=False),
            OpenApiParameter("end_date", str, required=False),
        ],
        responses={200: OpenApiTypes.OBJECT},
        description="Nepal IRD Annex 5 (Sales Book / बिक्री खाता) report.",
    )
    def get(self, request):
        start = request.query_params.get("start_date")
        end = request.query_params.get("end_date")
        data = FinancialReportService.get_nepal_vat_sales_book(request.organization, start, end)
        return Response(data)


class VatPurchaseBookAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsTenantMember]

    @extend_schema(
        parameters=[
            OpenApiParameter("start_date", str, required=False),
            OpenApiParameter("end_date", str, required=False),
        ],
        responses={200: OpenApiTypes.OBJECT},
        description="Nepal IRD Annex 7 (Purchase Book / खरिद खाता) report.",
    )
    def get(self, request):
        start = request.query_params.get("start_date")
        end = request.query_params.get("end_date")
        data = FinancialReportService.get_nepal_vat_purchase_book(request.organization, start, end)
        return Response(data)


class VatReturnSummaryAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated, IsTenantMember]

    @extend_schema(
        parameters=[
            OpenApiParameter("start_date", str, required=False),
            OpenApiParameter("end_date", str, required=False),
        ],
        responses={200: OpenApiTypes.OBJECT},
        description="Nepal IRD Monthly VAT Return Summary (Output VAT - Input VAT = Net Payable).",
    )
    def get(self, request):
        start = request.query_params.get("start_date")
        end = request.query_params.get("end_date")
        data = FinancialReportService.get_vat_return_summary(request.organization, start, end)
        return Response(data)
