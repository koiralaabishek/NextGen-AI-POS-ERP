from rest_framework import serializers
from apps.payments.models import Payment, Refund, RefundItem


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            "id",
            "organization",
            "sale",
            "payment_method",
            "amount",
            "currency",
            "status",
            "provider_reference",
            "provider_response",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class RefundItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = RefundItem
        fields = ["id", "sale_item", "quantity", "amount", "created_at"]
        read_only_fields = ["id", "created_at"]


class RefundSerializer(serializers.ModelSerializer):
    items = RefundItemSerializer(many=True, read_only=True)

    class Meta:
        model = Refund
        fields = [
            "id",
            "organization",
            "sale",
            "amount",
            "reason",
            "status",
            "approved_by",
            "items",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class EsewaVerifyRequestSerializer(serializers.Serializer):
    data = serializers.CharField(
        help_text="Base64 encoded response string from eSewa ePay v2 containing total_amount, transaction_uuid, status, signature."
    )


class KhaltiVerifyRequestSerializer(serializers.Serializer):
    pidx = serializers.CharField(
        help_text="Khalti Payment Index (pidx) generated during payment initiation."
    )
