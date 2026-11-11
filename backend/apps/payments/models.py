from decimal import Decimal
from django.db import models
from django.conf import settings
from common.models.base import TenantScopedModel, UUIDBaseModel, TimestampedModel


class Payment(TenantScopedModel):
    PAYMENT_METHODS = [
        ("CASH", "Cash"),
        ("ESEWA", "eSewa Mobile Wallet"),
        ("KHALTI", "Khalti Digital Wallet"),
        ("FONEPAY", "Fonepay QR / Interbank"),
        ("CARD", "Credit / Debit Card (POS Terminal)"),
        ("BANK_TRANSFER", "Direct Bank Transfer"),
        ("CREDIT", "Customer Credit / Khata Account"),
    ]

    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("SUCCESS", "Success"),
        ("FAILED", "Failed"),
        ("REVERSED", "Reversed"),
    ]

    sale = models.ForeignKey("sales.Sale", on_delete=models.CASCADE, related_name="payments")
    payment_method = models.CharField(max_length=30, choices=PAYMENT_METHODS, default="CASH")
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    currency = models.CharField(max_length=3, default="NPR")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="SUCCESS")
    provider_reference = models.CharField(max_length=150, blank=True, help_text="eSewa / Khalti transaction ID")
    provider_response = models.JSONField(default=dict, blank=True)

    class Meta:
        db_table = "payments"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.payment_method} - {self.amount} {self.currency} ({self.status})"


class Refund(TenantScopedModel):
    STATUS_CHOICES = [
        ("PENDING", "Pending Approval"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
        ("COMPLETED", "Completed"),
    ]
    sale = models.ForeignKey("sales.Sale", on_delete=models.CASCADE, related_name="refunds")
    amount = models.DecimalField(max_digits=14, decimal_places=2)
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="COMPLETED")
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        db_table = "refunds"


class RefundItem(UUIDBaseModel, TimestampedModel):
    refund = models.ForeignKey(Refund, on_delete=models.CASCADE, related_name="items")
    sale_item = models.ForeignKey("sales.SaleItem", on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=12, decimal_places=3)
    amount = models.DecimalField(max_digits=14, decimal_places=2)

    class Meta:
        db_table = "refund_items"
