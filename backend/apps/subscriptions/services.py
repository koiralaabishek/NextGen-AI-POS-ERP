from django.utils import timezone
from apps.subscriptions.models import Subscription, PlanFeature


class FeatureEntitlementService:
    """
    Central entitlement service validating whether an organization has an active
    subscription and is entitled to a specific feature code or limit.
    """

    @classmethod
    def get_active_subscription(cls, organization):
        now = timezone.now()
        return Subscription.objects.filter(
            organization=organization,
            status__in=["TRIAL", "ACTIVE"],
            end_date__gte=now,
        ).select_related("plan").first()

    @classmethod
    def has_feature(cls, organization, feature_code: str) -> bool:
        subscription = cls.get_active_subscription(organization)
        if not subscription:
            return False

        # Check if plan contains active feature
        return PlanFeature.objects.filter(
            plan=subscription.plan,
            feature_code=feature_code,
            is_enabled=True,
        ).exists()

    @classmethod
    def get_feature_limit(cls, organization, feature_code: str):
        subscription = cls.get_active_subscription(organization)
        if not subscription:
            return 0

        feat = PlanFeature.objects.filter(
            plan=subscription.plan,
            feature_code=feature_code,
            is_enabled=True,
        ).first()

        return feat.limit_value if feat else 0
