import contextvars
import uuid
from typing import Optional
from django.utils.deprecation import MiddlewareMixin
from django.core.exceptions import PermissionDenied

_tenant_context: contextvars.ContextVar[Optional[uuid.UUID]] = contextvars.ContextVar(
    "current_tenant_id", default=None
)


def get_current_tenant_id() -> Optional[uuid.UUID]:
    return _tenant_context.get()


def set_current_tenant_id(tenant_id: Optional[uuid.UUID | str]) -> None:
    if tenant_id is not None and not isinstance(tenant_id, uuid.UUID):
        try:
            tenant_id = uuid.UUID(str(tenant_id))
        except (ValueError, AttributeError):
            tenant_id = None
    _tenant_context.set(tenant_id)


def clear_current_tenant() -> None:
    _tenant_context.set(None)


class TenantMiddleware(MiddlewareMixin):
    """
    Multi-tenant middleware that extracts and validates organization context
    for every incoming API request.
    """

    def process_request(self, request):
        clear_current_tenant()
        request.organization = None

        org_header = request.headers.get("X-Organization-ID")
        if not org_header:
            return None

        try:
            org_id = uuid.UUID(org_header)
        except (ValueError, TypeError):
            return None

        # Deferred model import to avoid early app-loading circularity
        from apps.tenants.models import Organization, Membership

        try:
            org = Organization.objects.filter(id=org_id, is_active=True).first()
            if not org:
                return None

            # If user is already authenticated on the request, verify membership
            if hasattr(request, "user") and request.user.is_authenticated:
                # Platform superusers bypass org membership checks
                if not getattr(request.user, "is_platform_admin", False):
                    has_membership = Membership.objects.filter(
                        organization=org, user=request.user, is_active=True
                    ).exists()
                    if not has_membership:
                        raise PermissionDenied("User is not an active member of this organization.")

            request.organization = org
            set_current_tenant_id(org.id)
        except Exception:
            # Re-raise explicit permission denials
            raise

    def process_response(self, request, response):
        clear_current_tenant()
        return response

    def process_exception(self, request, exception):
        clear_current_tenant()
        return None
