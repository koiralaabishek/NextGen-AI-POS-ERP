from rest_framework import serializers
from apps.wholesale.models import PriceTier, CustomerCreditLimit, CreditTransaction


class PriceTierSerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceTier
        fields = [
            "id",
            "organization",
            "name",
            "min_quantity",
            "discount_percentage",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "organization", "created_at", "updated_at"]


class CustomerCreditLimitSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.name", read_only=True)
    customer_phone = serializers.CharField(source="customer.phone", read_only=True)
    current_debt = serializers.DecimalField(source="customer.current_credit", max_digits=14, decimal_places=2, read_only=True)

    class Meta:
        model = CustomerCreditLimit
        fields = [
            "id",
            "organization",
            "customer",
            "customer_name",
            "customer_phone",
            "credit_limit",
            "current_debt",
            "grace_period_days",
            "is_blocked",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "organization", "created_at", "updated_at"]


class CreditTransactionSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source="customer.name", read_only=True)

    class Meta:
        model = CreditTransaction
        fields = [
            "id",
            "organization",
            "customer",
            "customer_name",
            "transaction_type",
            "amount",
            "balance_after",
            "reference_id",
            "notes",
            "created_at",
        ]
        read_only_fields = ["id", "organization", "created_at"]


class SettleKhataPayloadSerializer(serializers.Serializer):
    customer_id = serializers.UUIDField(help_text="Customer UUID")
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, help_text="Settlement amount")
    payment_method = serializers.ChoiceField(
        choices=["CASH", "BANK_TRANSFER", "ESEWA", "KHALTI", "FONEPAY"],
        default="CASH",
    )
    notes = serializers.CharField(max_length=255, required=False, default="")
