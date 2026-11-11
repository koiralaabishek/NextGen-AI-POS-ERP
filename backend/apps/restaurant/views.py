from decimal import Decimal
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from drf_spectacular.types import OpenApiTypes

from apps.restaurant.models import RestaurantTable, DiningOrder, KitchenOrder, KitchenOrderItem
from apps.restaurant.serializers import (
    RestaurantTableSerializer,
    DiningOrderSerializer,
    KitchenOrderSerializer,
    CreateKOTRequestSerializer,
    SplitBillRequestSerializer,
)
from apps.catalog.models import ProductVariant
from common.utils.money import round_money, ZERO_MONEY


class RestaurantTableViewSet(viewsets.ModelViewSet):
    """
    Manages restaurant dining tables, seating capacity, and real-time floor availability.
    """
    serializer_class = RestaurantTableSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        org = getattr(self.request, "organization", None)
        if not org:
            return RestaurantTable.objects.none()
        qs = RestaurantTable.objects.filter(organization=org)
        branch_id = self.request.query_params.get("branch_id")
        if branch_id:
            qs = qs.filter(branch_id=branch_id)
        return qs.order_by("table_number")

    def perform_create(self, serializer):
        org = getattr(self.request, "organization", None)
        serializer.save(organization=org)

    @extend_schema(
        description="Marks a table as occupied by dining guests.",
        responses={200: RestaurantTableSerializer},
    )
    @action(detail=True, methods=["post"], url_path="occupy")
    def occupy_table(self, request, pk=None):
        table = self.get_object()
        table.status = "OCCUPIED"
        table.save(update_fields=["status", "updated_at"])
        return Response(RestaurantTableSerializer(table).data)

    @extend_schema(
        description="Releases an occupied table back to available state after bill settlement.",
        responses={200: RestaurantTableSerializer},
    )
    @action(detail=True, methods=["post"], url_path="release")
    def release_table(self, request, pk=None):
        table = self.get_object()
        table.status = "AVAILABLE"
        table.save(update_fields=["status", "updated_at"])
        return Response(RestaurantTableSerializer(table).data)


class DiningOrderViewSet(viewsets.ModelViewSet):
    """
    Manages active restaurant dining orders tied to a table and server.
    """
    serializer_class = DiningOrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        org = getattr(self.request, "organization", None)
        if not org:
            return DiningOrder.objects.none()
        return DiningOrder.objects.filter(organization=org).select_related("table").prefetch_related("kitchen_orders__items")

    def perform_create(self, serializer):
        org = getattr(self.request, "organization", None)
        order = serializer.save(organization=org)
        if order.table:
            order.table.status = "OCCUPIED"
            order.table.save(update_fields=["status", "updated_at"])

    @extend_schema(
        request=CreateKOTRequestSerializer,
        responses={201: KitchenOrderSerializer},
        description="Generates a Kitchen Order Ticket (KOT) for food preparation in the kitchen.",
    )
    @action(detail=True, methods=["post"], url_path="create-kot")
    def create_kot(self, request, pk=None):
        dining_order = self.get_object()
        serializer = CreateKOTRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        kot_count = dining_order.kitchen_orders.count() + 1
        table_num = dining_order.table.table_number if dining_order.table else "WALK-IN"
        kot_number = f"KOT-T{table_num}-{kot_count:02d}"

        kot = KitchenOrder.objects.create(
            organization=dining_order.organization,
            dining_order=dining_order,
            kot_number=kot_number,
            status="PENDING",
        )

        for item_data in serializer.validated_data["items"]:
            variant = ProductVariant.objects.get(id=item_data["variant_id"])
            KitchenOrderItem.objects.create(
                kitchen_order=kot,
                variant=variant,
                quantity=item_data["quantity"],
                special_instructions=item_data.get("special_instructions", ""),
            )

        return Response(KitchenOrderSerializer(kot).data, status=status.HTTP_201_CREATED)

    @extend_schema(
        request=SplitBillRequestSerializer,
        responses={200: OpenApiTypes.OBJECT},
        description="Calculates equal split amounts for diners wishing to split the check.",
    )
    @action(detail=True, methods=["post"], url_path="split-bill")
    def split_bill(self, request, pk=None):
        dining_order = self.get_object()
        serializer = SplitBillRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        split_count = serializer.validated_data["split_count"]

        # Calculate total from all KOT items
        total_amount = ZERO_MONEY
        for kot in dining_order.kitchen_orders.all():
            for item in kot.items.select_related("variant"):
                total_amount += round_money(item.variant.selling_price * item.quantity)

        per_person = round_money(total_amount / Decimal(split_count))
        return Response({
            "order_id": str(dining_order.id),
            "table_number": dining_order.table.table_number if dining_order.table else "N/A",
            "total_bill_npr": str(total_amount),
            "split_count": split_count,
            "per_person_npr": str(per_person),
        })


class KitchenOrderViewSet(viewsets.ModelViewSet):
    """
    Kitchen Display System (KDS) API: live kitchen queue for chefs and cooks.
    """
    serializer_class = KitchenOrderSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        org = getattr(self.request, "organization", None)
        if not org:
            return KitchenOrder.objects.none()
        qs = KitchenOrder.objects.filter(organization=org)
        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)
        return qs.select_related("dining_order__table").prefetch_related("items__variant__product").order_by("created_at")

    @extend_schema(
        responses={200: KitchenOrderSerializer},
        description="Advances KOT workflow: PENDING -> PREPARING -> READY -> SERVED.",
    )
    @action(detail=True, methods=["post"], url_path="advance-status")
    def advance_status(self, request, pk=None):
        kot = self.get_object()
        flow = {
            "PENDING": "PREPARING",
            "PREPARING": "READY",
            "READY": "SERVED",
            "SERVED": "SERVED",
        }
        kot.status = flow.get(kot.status, kot.status)
        kot.save(update_fields=["status", "updated_at"])
        return Response(KitchenOrderSerializer(kot).data)
