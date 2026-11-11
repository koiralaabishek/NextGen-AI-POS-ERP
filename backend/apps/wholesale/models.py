from decimal import Decimal
from django.db import models
from common.models.base import TenantScopedModel, UUIDBaseModel, TimestampedModel


class PriceTier(TenantScopedModel):
    name = models.CharField(max_length=100)  # e.g., Wholesale A (10+ pcs), Wholesale B (50+ pcs)
    min_quantity = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("10.00"))
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("5.00"))

    class Meta:
        db_table = "price_tiers"
        unique_together = ("organization", "name")


class CustomerCreditLimit(TenantScopedModel):
    customer = models.OneToOneField("sales.Customer", on_delete=models.CASCADE, related_name="credit_account")
    credit_limit = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("50000.00"))
    grace_period_days = models.PositiveIntegerField(default=30)
    is_blocked = models.BooleanField(default=False)

    class Meta:
        db_table = "customer_credit_limits"


class CreditTransaction(TenantScopedModel):
    TRANSACTION_TYPES = [
        ("INVOICE_DEBIT", "Invoice Credit Purchase"),
        ("PAYMENT_CREDIT", "Khata Payment Settlement"),
        ("ADJUSTMENT", "Manual Khata Adjustment"),
    ]
    customer = models.ForeignKey("sales.Customer", on_delete=models.CASCADE, related_name="credit_transactions")
    transaction_type = models.CharField(max_length=30, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    balance_after = models.DecimalField(max_digits=14, decimal_places=2)
    reference_id = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "credit_transactions"
        ordering = ["-created_at"]
