import uuid
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.utils import timezone
from common.models.base import UUIDBaseModel, TimestampedModel


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_platform_admin", True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin, UUIDBaseModel, TimestampedModel):
    """
    Custom user model authenticated via email.
    Supports multi-tenancy memberships across multiple organizations.
    """
    email = models.EmailField(unique=True, db_index=True)
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    phone = models.CharField(max_length=32, blank=True)
    avatar_url = models.URLField(blank=True, null=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_platform_admin = models.BooleanField(
        default=False,
        help_text="Designates platform-level administrators managing SaaS tenants and plans."
    )
    last_login_at = models.DateTimeField(null=True, blank=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        db_table = "users"
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return self.email

    @property
    def full_name(self):
        name = f"{self.first_name} {self.last_name}".strip()
        return name if name else self.email


class Permission(UUIDBaseModel):
    """System-defined functional permissions."""
    code = models.CharField(max_length=100, unique=True, db_index=True)
    name = models.CharField(max_length=150)
    module = models.CharField(max_length=50, db_index=True)  # pos, inventory, accounting, etc.
    description = models.TextField(blank=True)

    class Meta:
        db_table = "permissions"
        ordering = ["module", "code"]

    def __str__(self):
        return f"{self.module}:{self.code}"


class Role(UUIDBaseModel, TimestampedModel):
    """Organization-specific role with assigned permissions."""
    organization = models.ForeignKey(
        "tenants.Organization",
        on_delete=models.CASCADE,
        related_name="roles",
        db_index=True
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    is_owner = models.BooleanField(default=False)
    is_admin = models.BooleanField(default=False)
    permissions = models.ManyToManyField(Permission, through="RolePermission", related_name="roles")

    class Meta:
        db_table = "roles"
        unique_together = ("organization", "name")

    def __str__(self):
        return f"{self.organization.name} - {self.name}"


class RolePermission(UUIDBaseModel):
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)

    class Meta:
        db_table = "role_permissions"
        unique_together = ("role", "permission")
