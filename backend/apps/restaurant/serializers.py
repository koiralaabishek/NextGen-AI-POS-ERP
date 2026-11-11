from rest_framework import serializers
from apps.restaurant.models import RestaurantTable, DiningOrder, KitchenOrder, KitchenOrderItem


class RestaurantTableSerializer(serializers.ModelSerializer):
    class Meta:
        model = RestaurantTable
        fields = [
            "id",
            "organization",
            "branch",
            "table_number",
            "seating_capacity",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "organization", "created_at", "updated_at"]


class KitchenOrderItemSerializer(serializers.ModelSerializer):
    variant_name = serializers.CharField(source="variant.product.name", read_only=True)
    sku = serializers.CharField(source="variant.sku", read_only=True)

    class Meta:
        model = KitchenOrderItem
        fields = [
            "id",
            "variant",
            "variant_name",
            "sku",
            "quantity",
            "special_instructions",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class KitchenOrderSerializer(serializers.ModelSerializer):
    items = KitchenOrderItemSerializer(many=True, read_only=True)
    table_number = serializers.CharField(source="dining_order.table.table_number", read_only=True)

    class Meta:
        model = KitchenOrder
        fields = [
            "id",
            "organization",
            "dining_order",
            "table_number",
            "kot_number",
            "status",
            "items",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "organization", "created_at", "updated_at"]


class CreateKOTItemSerializer(serializers.Serializer):
    variant_id = serializers.UUIDField()
    quantity = serializers.DecimalField(max_digits=8, decimal_places=2)
    special_instructions = serializers.CharField(max_length=255, required=False, default="")


class CreateKOTRequestSerializer(serializers.Serializer):
    items = CreateKOTItemSerializer(many=True)


class DiningOrderSerializer(serializers.ModelSerializer):
    kitchen_orders = KitchenOrderSerializer(many=True, read_only=True)
    table_number = serializers.CharField(source="table.table_number", read_only=True)

    class Meta:
        model = DiningOrder
        fields = [
            "id",
            "organization",
            "branch",
            "table",
            "table_number",
            "status",
            "guest_count",
            "kitchen_orders",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "organization", "created_at", "updated_at"]


class SplitBillRequestSerializer(serializers.Serializer):
    split_count = serializers.IntegerField(min_value=2, max_value=10, default=2)
