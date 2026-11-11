from rest_framework import serializers
from apps.pos.models import PosTerminal, CashierShift, HeldSale
from apps.sales.serializers import SaleSerializer


class CheckoutItemSerializer(serializers.Serializer):
    variant_id = serializers.UUIDField()
    quantity = serializers.DecimalField(max_digits=12, decimal_places=3)
    unit_price = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    discount = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, default=0.00)


class CheckoutPaymentSerializer(serializers.Serializer):
    method = serializers.CharField(max_length=30)
    amount = serializers.DecimalField(max_digits=14, decimal_places=2)
    provider_reference = serializers.CharField(max_length=150, required=False, allow_blank=True, default="")


class CheckoutRequestSerializer(serializers.Serializer):
    client_transaction_id = serializers.CharField(max_length=120)
    branch_id = serializers.UUIDField()
    terminal_id = serializers.UUIDField(required=False, allow_null=True)
    customer_id = serializers.UUIDField(required=False, allow_null=True)
    items = CheckoutItemSerializer(many=True)
    payments = CheckoutPaymentSerializer(many=True)
    currency = serializers.CharField(max_length=3, default="NPR")
    notes = serializers.CharField(required=False, allow_blank=True, default="")


class PosTerminalSerializer(serializers.ModelSerializer):
    branch_name = serializers.ReadOnlyField(source="branch.name")

    class Meta:
        model = PosTerminal
        fields = ["id", "branch", "branch_name", "terminal_code", "name", "status", "device_fingerprint", "is_active"]
        read_only_fields = ["id"]


class CashierShiftSerializer(serializers.ModelSerializer):
    cashier_email = serializers.ReadOnlyField(source="cashier.email")
    terminal_code = serializers.ReadOnlyField(source="terminal.terminal_code")

    class Meta:
        model = CashierShift
        fields = [
            "id", "terminal", "terminal_code", "cashier", "cashier_email", "status",
            "opened_at", "closed_at", "opening_cash", "closing_cash",
            "expected_cash", "discrepancy", "notes"
        ]
        read_only_fields = ["id", "cashier", "opened_at", "closed_at", "expected_cash", "discrepancy"]


class CloseShiftSerializer(serializers.Serializer):
    closing_cash = serializers.DecimalField(max_digits=14, decimal_places=2)
    notes = serializers.CharField(required=False, allow_blank=True, default="")


class HeldSaleSerializer(serializers.ModelSerializer):
    customer_name = serializers.ReadOnlyField(source="customer.name")

    class Meta:
        model = HeldSale
        fields = ["id", "terminal", "customer", "customer_name", "cart_data", "notes", "created_at"]
        read_only_fields = ["id", "created_at"]
