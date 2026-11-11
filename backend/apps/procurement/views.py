from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from apps.procurement.models import Supplier, PurchaseOrder, GoodsReceipt
from apps.procurement.serializers import (
    SupplierSerializer,
    PurchaseOrderSerializer,
    GoodsReceiptSerializer,
)
from apps.procurement.services import ProcurementService
from common.permissions.tenant import IsTenantMember


class SupplierViewSet(viewsets.ModelViewSet):
    serializer_class = SupplierSerializer
    permission_classes = [permissions.IsAuthenticated, IsTenantMember]

    def get_queryset(self):
        return Supplier.objects.filter(organization=self.request.organization)


class PurchaseOrderViewSet(viewsets.ModelViewSet):
    serializer_class = PurchaseOrderSerializer
    permission_classes = [permissions.IsAuthenticated, IsTenantMember]

    def get_queryset(self):
        return PurchaseOrder.objects.filter(organization=self.request.organization).prefetch_related(
            "items", "items__variant", "supplier", "warehouse"
        )

    @extend_schema(
        request=None,
        responses={200: GoodsReceiptSerializer},
        description="Receives goods for the purchase order, increments physical inventory, and posts accounting journals.",
    )
    @action(detail=True, methods=["post"], url_path="receive")
    def receive(self, request, pk=None):
        po = self.get_object()
        receipt = ProcurementService.receive_purchase_order(
            purchase_order=po,
            user=request.user,
            notes=request.data.get("notes", ""),
        )
        return Response(GoodsReceiptSerializer(receipt).data, status=status.HTTP_200_OK)


class GoodsReceiptViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = GoodsReceiptSerializer
    permission_classes = [permissions.IsAuthenticated, IsTenantMember]

    def get_queryset(self):
        return GoodsReceipt.objects.filter(organization=self.request.organization).select_related(
            "purchase_order", "received_by"
        )
