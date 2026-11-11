from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from django.core.exceptions import ValidationError
from drf_spectacular.utils import extend_schema
from apps.inventory.models import (
    StockBalance,
    StockMovement,
    StockBatch,
    StockTransfer,
    StockAdjustment,
)
from apps.inventory.serializers import (
    StockBalanceSerializer,
    StockMovementSerializer,
    StockBatchSerializer,
    StockTransferSerializer,
    StockAdjustmentSerializer,
)
from common.permissions.tenant import IsTenantMember


class StockBalanceViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = StockBalanceSerializer
    permission_classes = [permissions.IsAuthenticated, IsTenantMember]
    filter_backends = [filters.SearchFilter]
    search_fields = ["variant__sku", "variant__barcode", "variant__product__name"]

    def get_queryset(self):
        qs = StockBalance.objects.filter(organization=self.request.organization).select_related(
            "warehouse", "variant", "variant__product"
        )
        warehouse_id = self.request.query_params.get("warehouse_id")
        if warehouse_id:
            qs = qs.filter(warehouse_id=warehouse_id)
        return qs


class StockMovementViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = StockMovementSerializer
    permission_classes = [permissions.IsAuthenticated, IsTenantMember]

    def get_queryset(self):
        qs = StockMovement.objects.filter(organization=self.request.organization).select_related("warehouse", "variant")
        variant_id = self.request.query_params.get("variant_id")
        if variant_id:
            qs = qs.filter(variant_id=variant_id)
        return qs


class StockBatchViewSet(viewsets.ModelViewSet):
    serializer_class = StockBatchSerializer
    permission_classes = [permissions.IsAuthenticated, IsTenantMember]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ["expiry_date", "current_quantity"]

    def get_queryset(self):
        return StockBatch.objects.filter(variant__product__organization=self.request.organization).select_related("variant")


class StockTransferViewSet(viewsets.ModelViewSet):
    serializer_class = StockTransferSerializer
    permission_classes = [permissions.IsAuthenticated, IsTenantMember]

    def get_queryset(self):
        return StockTransfer.objects.filter(organization=self.request.organization).prefetch_related(
            "items", "items__variant", "source_warehouse", "destination_warehouse"
        )

    @extend_schema(
        request=None,
        responses={200: StockTransferSerializer},
        description="Dispatches goods from the source warehouse (status -> IN_TRANSIT), deducting source physical inventory.",
    )
    @action(detail=True, methods=["post"], url_path="dispatch")
    def dispatch_transfer(self, request, pk=None):
        transfer = self.get_object()
        if transfer.status != "DRAFT":
            return Response(
                {"error": f"Only DRAFT transfers can be dispatched. Current status is {transfer.status}."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            for item in transfer.items.all():
                StockMovement.record_movement(
                    organization=transfer.organization,
                    warehouse=transfer.source_warehouse,
                    variant=item.variant,
                    movement_type="TRANSFER_OUT",
                    quantity=-item.quantity,
                    unit_cost=item.variant.cost_price,
                    reference_type="StockTransfer",
                    reference_id=transfer.transfer_number,
                    performed_by=request.user if request.user and request.user.is_authenticated else None,
                    notes=f"Dispatched transfer #{transfer.transfer_number} to {transfer.destination_warehouse.name}",
                )

            transfer.status = "IN_TRANSIT"
            transfer.save(update_fields=["status", "updated_at"])

        return Response(StockTransferSerializer(transfer).data)

    @extend_schema(
        request=None,
        responses={200: StockTransferSerializer},
        description="Receives goods at the destination warehouse (status -> RECEIVED), adding to destination physical inventory.",
    )
    @action(detail=True, methods=["post"], url_path="receive")
    def receive_transfer(self, request, pk=None):
        transfer = self.get_object()
        if transfer.status != "IN_TRANSIT":
            return Response(
                {"error": f"Only IN_TRANSIT transfers can be received. Current status is {transfer.status}."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            for item in transfer.items.all():
                StockMovement.record_movement(
                    organization=transfer.organization,
                    warehouse=transfer.destination_warehouse,
                    variant=item.variant,
                    movement_type="TRANSFER_IN",
                    quantity=item.quantity,
                    unit_cost=item.variant.cost_price,
                    reference_type="StockTransfer",
                    reference_id=transfer.transfer_number,
                    performed_by=request.user if request.user and request.user.is_authenticated else None,
                    notes=f"Received transfer #{transfer.transfer_number} from {transfer.source_warehouse.name}",
                )

            transfer.status = "RECEIVED"
            transfer.save(update_fields=["status", "updated_at"])

        return Response(StockTransferSerializer(transfer).data)


class StockAdjustmentViewSet(viewsets.ModelViewSet):
    serializer_class = StockAdjustmentSerializer
    permission_classes = [permissions.IsAuthenticated, IsTenantMember]

    def get_queryset(self):
        return StockAdjustment.objects.filter(organization=self.request.organization)
