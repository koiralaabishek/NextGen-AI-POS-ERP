from decimal import Decimal
from django.db import models
from django.utils import timezone
from common.models.base import UUIDBaseModel, TimestampedModel


class Plan(UUIDBaseModel, TimestampedModel):
    INTERVALS = [
        ("MONTHLY", "Monthly"),
        ("ANNUAL", "Annual"),
    ]
    name = models.CharField(max_length=100)  # Starter, Professional, Business, Enterprise
    slug = models.SlugField(unique=True)
    billing_interval = models.CharField(max_length=20, choices=INTERVALS, default="MONTHLY")
    price_npr = models.DecimalField(max_digits=10, decimal_places=2)
    max_branches = models.PositiveIntegerField(default=1)
    max_users = models.PositiveIntegerField(default=2)
    ai_monthly_credits = models.PositiveIntegerField(default=50)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "subscription_plans"
        ordering = ["price_npr"]

    def __str__(self):
        return f"{self.name} - Rs. {self.price_npr} / {self.billing_interval}"


class PlanFeature(UUIDBaseModel):
    plan = models.ForeignKey(Plan, on_delete=models.CASCADE, related_name="features")
    feature_code = models.CharField(max_length=100)  # pos.enabled, accounting.full, ai.assistant, etc.
    feature_name = models.CharField(max_length=150)
    is_enabled = models.BooleanField(default=True)
    limit_value = models.IntegerField(null=True, blank=True)

    class Meta:
        db_table = "plan_features"
        unique_together = ("plan", "feature_code")

    def __str__(self):
        return f"{self.plan.name} : {self.feature_code}"


class Subscription(UUIDBaseModel, TimestampedModel):
    STATUS_CHOICES = [
        ("TRIAL", "Trial"),
        ("ACTIVE", "Active"),
        ("PAST_DUE", "Past Due"),
        ("SUSPENDED", "Suspended"),
        ("CANCELLED", "Cancelled"),
        ("EXPIRED", "Expired"),
    ]
    organization = models.ForeignKey("tenants.Organization", on_delete=models.CASCADE, related_name="subscriptions")
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name="subscriptions")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="TRIAL")
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField()
    trial_ends_at = models.DateTimeField(null=True, blank=True)
    is_auto_renew = models.BooleanField(default=True)

    class Meta:
        db_table = "subscriptions"
        ordering = ["-start_date"]

    def __str__(self):
        return f"{self.organization.name} - {self.plan.name} ({self.status})"

    @property
    def is_valid(self):
        return self.status in ["TRIAL", "ACTIVE"] and (self.end_date is None or self.end_date >= timezone.now())


class SubscriptionInvoice(UUIDBaseModel, TimestampedModel):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("PAID", "Paid"),
        ("FAILED", "Failed"),
    ]
    subscription = models.ForeignKey(Subscription, on_delete=models.CASCADE, related_name="invoices")
    invoice_number = models.CharField(max_length=50, unique=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
    paid_at = models.DateTimeField(null=True, blank=True)
    provider_transaction_id = models.CharField(max_length=150, blank=True)

    class Meta:
        db_table = "subscription_invoices"


class UsageRecord(UUIDBaseModel):
    organization = models.ForeignKey("tenants.Organization", on_delete=models.CASCADE, related_name="usage_records")
    metric = models.CharField(max_length=100)  # e.g. ai_credits_used, sales_volume
    quantity = models.DecimalField(max_digits=12, decimal_places=2)
    recorded_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = "usage_records"
        ordering = ["-recorded_at"]
