from rest_framework import serializers
from apps.procurement.models import Supplier, PurchaseOrder, PurchaseOrderItem, GoodsReceipt


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = [
            "id", "name", "contact_person", "phone", "email",
            "tax_number", "address", "is_active", "created_at"
        ]
        read_only_fields = ["id", "created_at"]


class PurchaseOrderItemSerializer(serializers.ModelSerializer):
    variant_sku = serializers.ReadOnlyField(source="variant.sku")
    product_name = serializers.ReadOnlyField(source="variant.product.name")

    class Meta:
        model = PurchaseOrderItem
        fields = [
            "id", "variant", "variant_sku", "product_name",
            "quantity", "unit_cost", "tax_amount", "subtotal"
        ]
        read_only_fields = ["id"]


class PurchaseOrderSerializer(serializers.ModelSerializer):
    items = PurchaseOrderItemSerializer(many=True, required=False)
    supplier_name = serializers.ReadOnlyField(source="supplier.name")
    warehouse_name = serializers.ReadOnlyField(source="warehouse.name")

    class Meta:
        model = PurchaseOrder
        fields = [
            "id", "supplier", "supplier_name", "warehouse", "warehouse_name",
            "po_number", "status", "order_date", "expected_delivery",
            "total_amount", "tax_amount", "notes", "items", "created_at"
        ]
        read_only_fields = ["id", "created_at"]

    def create(self, validated_data):
        items_data = validated_data.pop("items", [])
        org = self.context["request"].organization
        po = PurchaseOrder.objects.create(organization=org, **validated_data)
        
        running_total = 0
        running_tax = 0
        for item in items_data:
            qty = item["quantity"]
            cost = item["unit_cost"]
            tax = item.get("tax_amount", 0)
            subtotal = (qty * cost) + tax
            PurchaseOrderItem.objects.create(
                purchase_order=po,
                variant=item["variant"],
                quantity=qty,
                unit_cost=cost,
                tax_amount=tax,
                subtotal=subtotal,
            )
            running_total += subtotal
            running_tax += tax
            
        po.total_amount = running_total
        po.tax_amount = running_tax
        po.save()
        return po


class GoodsReceiptSerializer(serializers.ModelSerializer):
    po_number = serializers.ReadOnlyField(source="purchase_order.po_number")
    received_by_email = serializers.ReadOnlyField(source="received_by.email")

    class Meta:
        model = GoodsReceipt
        fields = [
            "id", "purchase_order", "po_number", "receipt_number",
            "received_at", "received_by", "received_by_email", "notes"
        ]
        read_only_fields = ["id", "receipt_number", "received_at", "received_by"]
