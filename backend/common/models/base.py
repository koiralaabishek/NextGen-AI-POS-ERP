import uuid
from django.db import models
from django.utils import timezone
from django.core.exceptions import ValidationError
from common.middleware.tenant import get_current_tenant_id


class UUIDBaseModel(models.Model):
    """Abstract base model with a UUID primary key."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    class Meta:
        abstract = True


class TimestampedModel(models.Model):
    """Abstract model adding created_at and updated_at timestamps."""
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SoftDeletableModel(models.Model):
    """Abstract model allowing soft-deletion."""
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        abstract = True

    def soft_delete(self):
        self.is_deleted = True
        self.deleted_at = timezone.now()
        self.save(update_fields=["is_deleted", "deleted_at"])

    def restore(self):
        self.is_deleted = False
        self.deleted_at = None
        self.save(update_fields=["is_deleted", "deleted_at"])


class TenantQuerySet(models.QuerySet):
    """QuerySet that automatically scopes queries to current tenant context."""

    def for_tenant(self, tenant_id: uuid.UUID):
        return self.filter(organization_id=tenant_id)

    def current_tenant(self):
        current_id = get_current_tenant_id()
        if current_id:
            return self.filter(organization_id=current_id)
        return self


class TenantManager(models.Manager):
    """Default manager for TenantScopedModel."""

    def get_queryset(self):
        qs = TenantQuerySet(self.model, using=self._db)
        current_id = get_current_tenant_id()
        if current_id:
            return qs.filter(organization_id=current_id)
        return qs

    def all_tenants(self):
        """Explicitly bypass tenant filtering for background jobs / admin tasks."""
        return TenantQuerySet(self.model, using=self._db)


class TenantScopedModel(UUIDBaseModel, TimestampedModel):
    """
    Core abstract model for all tenant-owned entities.
    Enforces tenant scoping, cross-tenant FK protection, and automatic org binding.
    """
    organization = models.ForeignKey(
        "tenants.Organization",
        on_delete=models.CASCADE,
        related_name="%(class)ss",
        db_index=True,
    )

    objects = TenantManager()
    all_objects = models.Manager()

    class Meta:
        abstract = True

    def clean(self):
        super().clean()
        if not self.organization_id:
            current_id = get_current_tenant_id()
            if current_id:
                self.organization_id = current_id
            else:
                raise ValidationError({"organization": "Organization is required for tenant-scoped records."})

        # Verify that all related TenantScopedModel fields belong to the same tenant
        for field in self._meta.fields:
            if isinstance(field, models.ForeignKey) and field.name != "organization":
                rel_model = field.remote_field.model
                if issubclass(rel_model, TenantScopedModel):
                    rel_val = getattr(self, field.name, None)
                    if rel_val and getattr(rel_val, "organization_id", None) != self.organization_id:
                        raise ValidationError({
                            field.name: f"Cross-tenant reference detected: {field.name} belongs to a different organization."
                        })

    def save(self, *args, **kwargs):
        if not self.organization_id:
            current_id = get_current_tenant_id()
            if current_id:
                self.organization_id = current_id
        self.full_clean()
        super().save(*args, **kwargs)
