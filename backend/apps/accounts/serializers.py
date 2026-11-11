from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate
from apps.accounts.models import User, Role, Permission


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    organization_name = serializers.CharField(write_only=True, required=False)
    business_type = serializers.CharField(write_only=True, required=False, default="retail")

    class Meta:
        model = User
        fields = ["id", "email", "password", "first_name", "last_name", "phone", "organization_name", "business_type"]

    def create(self, validated_data):
        org_name = validated_data.pop("organization_name", None)
        biz_type = validated_data.pop("business_type", "retail")
        password = validated_data.pop("password")

        user = User.objects.create_user(password=password, **validated_data)

        # If user registered with an organization name, create organization and owner role
        if org_name:
            from apps.tenants.models import Organization, Membership
            from apps.branches.models import Branch, Warehouse

            slug = org_name.lower().replace(" ", "-")[:40]
            org = Organization.objects.create(
                name=org_name,
                slug=f"{slug}-{uuid_short()}",
                business_type=biz_type,
            )
            # Create default owner role
            owner_role = Role.objects.create(
                organization=org,
                name="Owner",
                is_owner=True,
                is_admin=True,
                description="Complete access to organization resources"
            )
            # Create default headquarters branch
            hq_branch = Branch.objects.create(
                organization=org,
                name="Headquarters",
                code="HQ-01",
                is_headquarters=True,
            )
            Warehouse.objects.create(
                organization=org,
                branch=hq_branch,
                name="Main Warehouse",
                code="MW-01",
                is_primary=True,
            )
            # Link membership
            Membership.objects.create(
                organization=org,
                user=user,
                role=owner_role,
            )

        return user


def uuid_short():
    import uuid
    return uuid.uuid4().hex[:6]


class UserProfileSerializer(serializers.ModelSerializer):
    organizations = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "email", "first_name", "last_name", "phone", "avatar_url", "is_platform_admin", "organizations"]

    def get_organizations(self, obj):
        from apps.tenants.models import Membership
        memberships = Membership.objects.filter(user=obj, is_active=True).select_related("organization", "role")
        return [
            {
                "id": str(m.organization.id),
                "name": m.organization.name,
                "slug": m.organization.slug,
                "business_type": m.organization.business_type,
                "role": m.role.name if m.role else None,
                "is_owner": m.role.is_owner if m.role else False,
            }
            for m in memberships
        ]


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user
        data["user"] = UserProfileSerializer(user).data
        return data


class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ["id", "code", "name", "module", "description"]


class RoleSerializer(serializers.ModelSerializer):
    permissions_list = PermissionSerializer(source="permissions", many=True, read_only=True)
    permission_ids = serializers.ListField(
        child=serializers.UUIDField(), write_only=True, required=False
    )

    class Meta:
        model = Role
        fields = ["id", "name", "description", "is_owner", "is_admin", "permissions_list", "permission_ids"]

    def create(self, validated_data):
        perm_ids = validated_data.pop("permission_ids", [])
        org = self.context["request"].organization
        role = Role.objects.create(organization=org, **validated_data)
        if perm_ids:
            perms = Permission.objects.filter(id__in=perm_ids)
            role.permissions.set(perms)
        return role

    def update(self, instance, validated_data):
        perm_ids = validated_data.pop("permission_ids", None)
        for attr, val in validated_data.items():
            setattr(instance, attr, val)
        instance.save()
        if perm_ids is not None:
            perms = Permission.objects.filter(id__in=perm_ids)
            instance.permissions.set(perms)
        return instance
