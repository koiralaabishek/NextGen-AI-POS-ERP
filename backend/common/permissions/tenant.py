from rest_framework import permissions


class IsTenantMember(permissions.BasePermission):
    """
    Ensures that the authenticated user is an active member of the request organization.
    Platform admins bypass this check.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if getattr(request.user, "is_platform_admin", False) or request.user.is_superuser:
            return True

        if not hasattr(request, "organization") or not request.organization:
            return False

        from apps.tenants.models import Membership

        return Membership.objects.filter(
            organization=request.organization,
            user=request.user,
            is_active=True,
        ).exists()


class HasTenantPermission(permissions.BasePermission):
    """
    Checks if the user has a specific permission code assigned via their Role
    in the active organization.
    """

    def __init__(self, required_permission: str = None):
        self.required_permission = required_permission

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if getattr(request.user, "is_platform_admin", False) or request.user.is_superuser:
            return True

        required_perm = getattr(view, "required_permission", self.required_permission)
        if not required_perm:
            return True

        from apps.tenants.models import Membership

        membership = Membership.objects.filter(
            organization=request.organization,
            user=request.user,
            is_active=True,
        ).select_related("role").first()

        if not membership or not membership.role:
            return False

        # Role name 'owner' or 'admin' has blanket access
        if membership.role.is_owner or membership.role.is_admin:
            return True

        return membership.role.permissions.filter(code=required_perm).exists()


class HasBranchAccess(permissions.BasePermission):
    """
    Checks if user is assigned or allowed access to a specified branch.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if getattr(request.user, "is_platform_admin", False) or request.user.is_superuser:
            return True

        branch_id = request.headers.get("X-Branch-ID") or request.query_params.get("branch_id")
        if not branch_id:
            return True  # Branch-agnostic endpoint

        from apps.tenants.models import Membership

        membership = Membership.objects.filter(
            organization=request.organization,
            user=request.user,
            is_active=True,
        ).first()

        if not membership:
            return False

        # If user has no specific branch restrictions, they can access all branches in their org
        if not membership.branches.exists():
            return True

        return membership.branches.filter(id=branch_id).exists()


class HasFeatureEntitlement(permissions.BasePermission):
    """
    Validates that the organization has an active SaaS subscription entitlement
    for a given feature code.
    """

    def __init__(self, feature_code: str = None):
        self.feature_code = feature_code

    def has_permission(self, request, view):
        feature = getattr(view, "required_feature", self.feature_code)
        if not feature:
            return True

        if getattr(request.user, "is_platform_admin", False):
            return True

        if not hasattr(request, "organization") or not request.organization:
            return False

        from apps.subscriptions.services import FeatureEntitlementService

        return FeatureEntitlementService.has_feature(request.organization, feature)


class IsPlatformAdmin(permissions.BasePermission):
    """Allows access only to platform administrators."""

    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and (getattr(request.user, "is_platform_admin", False) or request.user.is_superuser)
        )
