from rest_framework import permissions
from apps.subscriptions.services import FeatureEntitlementService


class SubscriptionActivePermission(permissions.BasePermission):
    """
    Blocks API operations if the tenant organization does not have an active or trial subscription.
    """
    message = "Your organization subscription has expired or is suspended. Please upgrade your SaaS plan."

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_platform_admin:
            return True

        org = getattr(request, "organization", None)
        if not org:
            return True

        sub = FeatureEntitlementService.get_active_subscription(org)
        return sub is not None and sub.is_valid


def requires_feature(feature_code: str):
    """
    Factory for DRF permissions requiring a specific SaaS subscription feature flag.
    """
    class DynamicFeaturePermission(permissions.BasePermission):
        message = f"Your current subscription plan does not include the '{feature_code}' module."

        def has_permission(self, request, view):
            if not request.user or not request.user.is_authenticated:
                return False

            if request.user.is_platform_admin:
                return True

            org = getattr(request, "organization", None)
            if not org:
                return False

            return FeatureEntitlementService.has_feature(org, feature_code)

    return DynamicFeaturePermission
