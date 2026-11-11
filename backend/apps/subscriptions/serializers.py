from rest_framework import serializers
from apps.subscriptions.models import Plan, PlanFeature, Subscription, SubscriptionInvoice


class PlanFeatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = PlanFeature
        fields = ["id", "feature_code", "feature_name", "is_enabled", "limit_value"]


class PlanSerializer(serializers.ModelSerializer):
    features = PlanFeatureSerializer(many=True, read_only=True)

    class Meta:
        model = Plan
        fields = [
            "id",
            "name",
            "slug",
            "billing_interval",
            "price_npr",
            "max_branches",
            "max_users",
            "ai_monthly_credits",
            "is_active",
            "features",
            "created_at",
        ]


class SubscriptionInvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionInvoice
        fields = ["id", "invoice_number", "amount", "status", "paid_at", "provider_transaction_id", "created_at"]


class SubscriptionSerializer(serializers.ModelSerializer):
    plan_details = PlanSerializer(source="plan", read_only=True)
    invoices = SubscriptionInvoiceSerializer(many=True, read_only=True)
    is_valid = serializers.BooleanField(read_only=True)

    class Meta:
        model = Subscription
        fields = [
            "id",
            "organization",
            "plan",
            "plan_details",
            "status",
            "start_date",
            "end_date",
            "trial_ends_at",
            "is_auto_renew",
            "is_valid",
            "invoices",
            "created_at",
        ]
        read_only_fields = ["id", "organization", "start_date", "created_at"]


class UpgradePlanRequestSerializer(serializers.Serializer):
    plan_id = serializers.UUIDField(help_text="UUID of the SaaS Plan to upgrade to.")
    billing_interval = serializers.ChoiceField(
        choices=["MONTHLY", "ANNUAL"],
        default="MONTHLY",
        help_text="Billing interval cycle",
    )
