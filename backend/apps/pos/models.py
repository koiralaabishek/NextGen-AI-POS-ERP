from decimal import Decimal
from django.db import models
from django.conf import settings
from common.models.base import TenantScopedModel, UUIDBaseModel, TimestampedModel


class PosTerminal(TenantScopedModel):
    STATUS_CHOICES = [
        ("ONLINE", "Online"),
        ("OFFLINE", "Offline"),
        ("MAINTENANCE", "Maintenance"),
    ]
    branch = models.ForeignKey("branches.Branch", on_delete=models.CASCADE, related_name="terminals")
    terminal_code = models.CharField(max_length=50)
    name = models.CharField(max_length=100)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="ONLINE")
    device_fingerprint = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "pos_terminals"
        unique_together = ("organization", "terminal_code")

    def __str__(self):
        return f"{self.name} [{self.terminal_code}]"


class CashierShift(TenantScopedModel):
    STATUS_CHOICES = [
        ("OPEN", "Open"),
        ("CLOSED", "Closed"),
    ]
    terminal = models.ForeignKey(PosTerminal, on_delete=models.CASCADE, related_name="shifts")
    cashier = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="cashier_shifts")
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="OPEN")
    opened_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    opening_cash = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    closing_cash = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    expected_cash = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    discrepancy = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "cashier_shifts"
        ordering = ["-opened_at"]

    def __str__(self):
        return f"Shift #{self.id} - {self.cashier.email} ({self.status})"


class HeldSale(TenantScopedModel):
    """Temporary paused cart on POS terminal."""
    terminal = models.ForeignKey(PosTerminal, on_delete=models.CASCADE, related_name="held_sales")
    customer = models.ForeignKey("sales.Customer", on_delete=models.SET_NULL, null=True, blank=True)
    cart_data = models.JSONField(help_text="Serialized cart items and discounts")
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "held_sales"
        ordering = ["-created_at"]
