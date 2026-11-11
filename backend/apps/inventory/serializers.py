from rest_framework import serializers
from apps.inventory.models import (
    StockBalance,
    StockMovement,
    StockBatch,
    StockTransfer,
    StockTransferItem,
    StockAdjustment,
)
from apps.catalog.serializers import ProductVariantSerializer


class StockBalanceSerializer(serializers.ModelSerializer):
    variant_details = ProductVariantSerializer(source="variant", read_only=True)
    warehouse_name = serializers.ReadOnlyField(source="warehouse.name")

    class Meta:
        model = StockBalance
        fields = ["id", "warehouse", "warehouse_name", "variant", "variant_details", "quantity", "reserved_quantity", "available_quantity", "updated_at"]
        read_only_fields = ["id", "quantity", "reserved_quantity", "available_quantity", "updated_at"]


class StockMovementSerializer(serializers.ModelSerializer):
    variant_sku = serializers.ReadOnlyField(source="variant.sku")
    warehouse_name = serializers.ReadOnlyField(source="warehouse.name")

    class Meta:
        model = StockMovement
        fields = [
            "id", "warehouse", "warehouse_name", "variant", "variant_sku",
            "movement_type", "quantity", "unit_cost", "reference_type",
            "reference_id", "notes", "created_at"
        ]
        read_only_fields = ["id", "created_at"]


class StockBatchSerializer(serializers.ModelSerializer):
    variant_sku = serializers.ReadOnlyField(source="variant.sku")

    class Meta:
        model = StockBatch
        fields = ["id", "variant", "variant_sku", "batch_number", "expiry_date", "cost_price", "current_quantity"]


class StockTransferItemSerializer(serializers.ModelSerializer):
    variant_sku = serializers.ReadOnlyField(source="variant.sku")
    product_name = serializers.ReadOnlyField(source="variant.product.name")

    class Meta:
        model = StockTransferItem
        fields = ["id", "variant", "variant_sku", "product_name", "quantity"]
        read_only_fields = ["id"]


class StockTransferSerializer(serializers.ModelSerializer):
    items = StockTransferItemSerializer(many=True, required=False)
    source_name = serializers.ReadOnlyField(source="source_warehouse.name")
    destination_name = serializers.ReadOnlyField(source="destination_warehouse.name")

    class Meta:
        model = StockTransfer
        fields = [
            "id", "source_warehouse", "source_name", "destination_warehouse",
            "destination_name", "transfer_number", "status", "notes", "items", "created_at"
        ]
        read_only_fields = ["id", "created_at"]

    def create(self, validated_data):
        items_data = validated_data.pop("items", [])
        org = self.context["request"].organization
        transfer = StockTransfer.objects.create(organization=org, **validated_data)
        for item in items_data:
            StockTransferItem.objects.create(transfer=transfer, **item)
        return transfer


class StockAdjustmentSerializer(serializers.ModelSerializer):
    warehouse_name = serializers.ReadOnlyField(source="warehouse.name")

    class Meta:
        model = StockAdjustment
        fields = ["id", "warehouse", "warehouse_name", "reason", "status", "approved_by", "created_at"]
        read_only_fields = ["id", "status", "approved_by", "created_at"]
