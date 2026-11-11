from rest_framework import serializers
from apps.tenants.models import Organization, Membership, BusinessSettings, AuditLog
from apps.accounts.serializers import UserProfileSerializer, RoleSerializer


class BusinessSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = BusinessSettings
        fields = ["id", "settings_json", "updated_at"]


class OrganizationSerializer(serializers.ModelSerializer):
    settings = BusinessSettingsSerializer(read_only=True)

    class Meta:
        model = Organization
        fields = [
            "id", "name", "slug", "business_type", "country", "currency",
            "timezone", "tax_number", "phone", "email", "address",
            "logo_url", "is_active", "onboarding_completed", "settings",
            "created_at"
        ]
        read_only_fields = ["id", "created_at"]


class MembershipSerializer(serializers.ModelSerializer):
    user = UserProfileSerializer(read_only=True)
    role_details = RoleSerializer(source="role", read_only=True)
    user_email = serializers.EmailField(write_only=True, required=False)
    role_id = serializers.UUIDField(write_only=True, required=False)

    class Meta:
        model = Membership
        fields = [
            "id", "organization", "user", "role", "role_details",
            "branches", "is_active", "joined_at", "user_email", "role_id"
        ]
        read_only_fields = ["id", "organization", "joined_at"]

    def create(self, validated_data):
        user_email = validated_data.pop("user_email", None)
        role_id = validated_data.pop("role_id", None)
        org = self.context["request"].organization

        from apps.accounts.models import User, Role
        user = User.objects.filter(email=user_email).first()
        if not user:
            raise serializers.ValidationError({"user_email": "User with this email was not found."})

        role = None
        if role_id:
            role = Role.objects.filter(id=role_id, organization=org).first()

        membership, _ = Membership.objects.update_or_create(
            organization=org,
            user=user,
            defaults={"role": role, "is_active": True}
        )
        return membership


class AuditLogSerializer(serializers.ModelSerializer):
    actor_email = serializers.ReadOnlyField(source="actor.email")

    class Meta:
        model = AuditLog
        fields = [
            "id", "actor_email", "action", "resource_type",
            "resource_id", "before_state", "after_state",
            "ip_address", "timestamp"
        ]
