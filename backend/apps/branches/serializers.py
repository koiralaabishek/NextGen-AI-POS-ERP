from rest_framework import serializers
from apps.branches.models import Branch, Warehouse, Device


class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = ["id", "branch", "name", "code", "is_primary", "is_active", "created_at"]
        read_only_fields = ["id", "created_at"]


class BranchSerializer(serializers.ModelSerializer):
    warehouses = WarehouseSerializer(many=True, read_only=True)

    class Meta:
        model = Branch
        fields = ["id", "name", "code", "address", "phone", "email", "is_active", "is_headquarters", "warehouses", "created_at"]
        read_only_fields = ["id", "created_at"]


class DeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Device
        fields = ["id", "branch", "device_code", "device_name", "device_type", "last_seen", "is_active", "created_at"]
        read_only_fields = ["id", "created_at"]
