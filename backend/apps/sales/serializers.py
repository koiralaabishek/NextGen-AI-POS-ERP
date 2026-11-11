from rest_framework import serializers
from apps.sales.models import Customer, Sale, SaleItem, SaleTax, Quotation, SalesOrder
from apps.payments.models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ["id", "payment_method", "amount", "currency", "status", "provider_reference", "created_at"]


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = [
            "id", "name", "phone", "email", "tax_number", "address",
            "credit_limit", "current_credit", "loyalty_points", "is_active"
        ]
        read_only_fields = ["id"]


class SaleItemSerializer(serializers.ModelSerializer):
    variant_sku = serializers.ReadOnlyField(source="variant.sku")
    product_name = serializers.ReadOnlyField(source="variant.product.name")

    class Meta:
        model = SaleItem
        fields = [
            "id", "variant", "variant_sku", "product_name",
            "quantity", "unit_price", "discount_amount",
            "tax_rate", "tax_amount", "subtotal"
        ]


class SaleTaxSerializer(serializers.ModelSerializer):
    class Meta:
        model = SaleTax
        fields = ["id", "tax_type", "rate", "taxable_amount", "tax_amount"]


class SaleSerializer(serializers.ModelSerializer):
    items = SaleItemSerializer(many=True, read_only=True)
    taxes = SaleTaxSerializer(many=True, read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)
    customer_name = serializers.ReadOnlyField(source="customer.name")
    branch_name = serializers.ReadOnlyField(source="branch.name")

    class Meta:
        model = Sale
        fields = [
            "id", "invoice_number", "client_transaction_id", "status",
            "branch", "branch_name", "terminal", "cashier", "customer",
            "customer_name", "subtotal", "discount_amount", "tax_amount",
            "total_amount", "paid_amount", "currency", "notes",
            "items", "taxes", "payments", "synced_at", "created_at"
        ]
        read_only_fields = ["id", "invoice_number", "synced_at", "created_at"]
