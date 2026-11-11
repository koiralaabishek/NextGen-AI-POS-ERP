from django.db import models
from django.conf import settings
from common.models.base import UUIDBaseModel, TimestampedModel


class Organization(UUIDBaseModel, TimestampedModel):
    BUSINESS_TYPES = [
        ("retail", "Retail"),
        ("supermarket", "Supermarket"),
        ("restaurant", "Restaurant"),
        ("wholesale", "Wholesale & Distribution"),
    ]

    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=255, unique=True, db_index=True)
    business_type = models.CharField(max_length=30, choices=BUSINESS_TYPES, default="retail")
    country = models.CharField(max_length=2, default="NP")
    currency = models.CharField(max_length=3, default="NPR")
    timezone = models.CharField(max_length=50, default="Asia/Kathmandu")
    tax_number = models.CharField(max_length=50, blank=True, help_text="PAN / VAT Number")
    
    phone = models.CharField(max_length=32, blank=True)
    email = models.EmailField(blank=True)
    address = models.TextField(blank=True)
    logo_url = models.URLField(blank=True, null=True)

    is_active = models.BooleanField(default=True, db_index=True)
    onboarding_completed = models.BooleanField(default=False)

    class Meta:
        db_table = "organizations"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Membership(UUIDBaseModel, TimestampedModel):
    """Associates a User with an Organization, assigned a specific Role and optional branch restrictions."""
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="memberships")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="memberships")
    role = models.ForeignKey("accounts.Role", on_delete=models.SET_NULL, null=True, blank=True, related_name="memberships")
    branches = models.ManyToManyField("branches.Branch", blank=True, related_name="member_assignments")
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "memberships"
        unique_together = ("organization", "user")

    def __str__(self):
        return f"{self.user.email} in {self.organization.name}"


class BusinessSettings(UUIDBaseModel, TimestampedModel):
    """Configurable organization and industry-specific settings."""
    organization = models.OneToOneField(Organization, on_delete=models.CASCADE, related_name="settings")
    settings_json = models.JSONField(
        default=dict,
        help_text="Configurable settings: receipt_format, tax_included, low_stock_threshold, offline_sync_policy"
    )

    class Meta:
        db_table = "business_settings"

    def __str__(self):
        return f"Settings for {self.organization.name}"


class AuditLog(UUIDBaseModel):
    """Audit ledger tracking actor actions with before/after state snapshots."""
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name="audit_logs")
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="performed_actions"
    )
    action = models.CharField(max_length=100)  # CREATE, UPDATE, DELETE, CHECKOUT, CANCEL_INVOICE, REFUND
    resource_type = models.CharField(max_length=100)  # Sale, Product, StockAdjustment, etc.
    resource_id = models.CharField(max_length=100)
    before_state = models.JSONField(null=True, blank=True)
    after_state = models.JSONField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "audit_logs"
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.action} on {self.resource_type} ({self.resource_id})"
