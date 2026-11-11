from rest_framework import viewsets, permissions
from apps.branches.models import Branch, Warehouse, Device
from apps.branches.serializers import BranchSerializer, WarehouseSerializer, DeviceSerializer
from common.permissions.tenant import IsTenantMember


class BranchViewSet(viewsets.ModelViewSet):
    serializer_class = BranchSerializer
    permission_classes = [permissions.IsAuthenticated, IsTenantMember]

    def get_queryset(self):
        return Branch.objects.filter(organization=self.request.organization)


class WarehouseViewSet(viewsets.ModelViewSet):
    serializer_class = WarehouseSerializer
    permission_classes = [permissions.IsAuthenticated, IsTenantMember]

    def get_queryset(self):
        return Warehouse.objects.filter(organization=self.request.organization)


class DeviceViewSet(viewsets.ModelViewSet):
    serializer_class = DeviceSerializer
    permission_classes = [permissions.IsAuthenticated, IsTenantMember]

    def get_queryset(self):
        return Device.objects.filter(organization=self.request.organization)
