from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.tenants.models import Organization, Membership, BusinessSettings, AuditLog
from apps.tenants.serializers import (
    OrganizationSerializer,
    MembershipSerializer,
    BusinessSettingsSerializer,
    AuditLogSerializer,
)
from common.permissions.tenant import IsTenantMember, IsPlatformAdmin


class OrganizationViewSet(viewsets.ModelViewSet):
    serializer_class = OrganizationSerializer

    def get_permissions(self):
        if self.action in ["list", "create"]:
            return [permissions.IsAuthenticated()]
        return [permissions.IsAuthenticated(), IsTenantMember()]

    def get_queryset(self):
        user = self.request.user
        if getattr(user, "is_platform_admin", False):
            return Organization.objects.all()
        return Organization.objects.filter(memberships__user=user, memberships__is_active=True).distinct()

    @action(detail=True, methods=["get", "patch"], url_path="settings")
    def settings(self, request, pk=None):
        org = self.get_object()
        settings_obj, _ = BusinessSettings.objects.get_or_create(organization=org)
        if request.method == "PATCH":
            serializer = BusinessSettingsSerializer(settings_obj, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        serializer = BusinessSettingsSerializer(settings_obj)
        return Response(serializer.data)


class MembershipViewSet(viewsets.ModelViewSet):
    serializer_class = MembershipSerializer
    permission_classes = [permissions.IsAuthenticated, IsTenantMember]

    def get_queryset(self):
        return Membership.objects.filter(organization=self.request.organization)


class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = AuditLogSerializer
    permission_classes = [permissions.IsAuthenticated, IsTenantMember]

    def get_queryset(self):
        return AuditLog.objects.filter(organization=self.request.organization)
