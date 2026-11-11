from decimal import Decimal
from django.db import models, transaction
from django.conf import settings
from common.models.base import TenantScopedModel, UUIDBaseModel, TimestampedModel


class StockBalance(TenantScopedModel):
    """
    Maintained current stock level per warehouse and variant.
    Updated strictly via recorded StockMovements.
    """
    warehouse = models.ForeignKey("branches.Warehouse", on_delete=models.CASCADE, related_name="stock_balances")
    variant = models.ForeignKey("catalog.ProductVariant", on_delete=models.CASCADE, related_name="stock_balances")
    quantity = models.DecimalField(max_digits=14, decimal_places=3, default=Decimal("0.000"))
    reserved_quantity = models.DecimalField(max_digits=14, decimal_places=3, default=Decimal("0.000"))

    class Meta:
        db_table = "stock_balances"
        unique_together = ("warehouse", "variant")

    def __str__(self):
        return f"{self.variant} @ {self.warehouse.name}: {self.quantity}"

    @property
    def available_quantity(self):
        return self.quantity - self.reserved_quantity


class StockMovement(TenantScopedModel):
    """
    Immutable inventory ledger record. Every change in physical stock must originate here.
    """
    MOVEMENT_TYPES = [
        ("PURCHASE", "Purchase Receipt"),
        ("SALE", "POS / Sales Deduction"),
        ("TRANSFER_OUT", "Transfer Sent"),
        ("TRANSFER_IN", "Transfer Received"),
        ("ADJUSTMENT_ADD", "Inventory Count Positive Adjustment"),
        ("ADJUSTMENT_SUB", "Inventory Count Negative Adjustment / Waste"),
        ("RETURN", "Customer Sale Return Restock"),
    ]

    warehouse = models.ForeignKey("branches.Warehouse", on_delete=models.CASCADE, related_name="stock_movements")
    variant = models.ForeignKey("catalog.ProductVariant", on_delete=models.CASCADE, related_name="movements")
    movement_type = models.CharField(max_length=30, choices=MOVEMENT_TYPES)
    quantity = models.DecimalField(max_digits=14, decimal_places=3, help_text="Positive for additions, negative for deductions")
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    reference_type = models.CharField(max_length=50, blank=True)  # Sale, PurchaseOrder, StockTransfer, StockAdjustment
    reference_id = models.CharField(max_length=100, blank=True)
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True
    )
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "stock_movements"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.movement_type} {self.quantity} {self.variant} [{self.warehouse.name}]"

    @classmethod
    def record_movement(cls, organization, warehouse, variant, movement_type, quantity, unit_cost=Decimal("0.00"), reference_type="", reference_id="", performed_by=None, notes=""):
        """
        Atomically records a stock movement and updates the associated stock balance.
        """
        if performed_by and not getattr(performed_by, "is_authenticated", True):
            performed_by = None
        elif performed_by and getattr(performed_by, "is_anonymous", False):
            performed_by = None

        with transaction.atomic():
            movement = cls.objects.create(
                organization=organization,
                warehouse=warehouse,
                variant=variant,
                movement_type=movement_type,
                quantity=quantity,
                unit_cost=unit_cost,
                reference_type=reference_type,
                reference_id=str(reference_id),
                performed_by=performed_by,
                notes=notes,
            )
            # Update or create cached balance with select_for_update to avoid concurrency race conditions
            balance, _ = StockBalance.objects.select_for_update().get_or_create(
                organization=organization,
                warehouse=warehouse,
                variant=variant,
                defaults={"quantity": Decimal("0.000"), "reserved_quantity": Decimal("0.000")}
            )
            balance.quantity += Decimal(str(quantity))
            balance.save(update_fields=["quantity", "updated_at"])
            return movement


class StockBatch(UUIDBaseModel, TimestampedModel):
    """Batch and expiry tracking for FMCG, supermarkets, and pharma."""
    variant = models.ForeignKey("catalog.ProductVariant", on_delete=models.CASCADE, related_name="batches")
    batch_number = models.CharField(max_length=100)
    expiry_date = models.DateField(null=True, blank=True)
    cost_price = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    current_quantity = models.DecimalField(max_digits=14, decimal_places=3, default=Decimal("0.000"))

    class Meta:
        db_table = "stock_batches"
        unique_together = ("variant", "batch_number")

    def __str__(self):
        return f"{self.variant} - Batch {self.batch_number} (Exp: {self.expiry_date})"


class StockTransfer(TenantScopedModel):
    STATUS_CHOICES = [
        ("DRAFT", "Draft"),
        ("IN_TRANSIT", "In Transit"),
        ("RECEIVED", "Received"),
        ("CANCELLED", "Cancelled"),
    ]
    source_warehouse = models.ForeignKey(
        "branches.Warehouse", on_delete=models.CASCADE, related_name="transfers_out"
    )
    destination_warehouse = models.ForeignKey(
        "branches.Warehouse", on_delete=models.CASCADE, related_name="transfers_in"
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="DRAFT")
    transfer_number = models.CharField(max_length=50)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "stock_transfers"


class StockTransferItem(UUIDBaseModel, TimestampedModel):
    transfer = models.ForeignKey(StockTransfer, on_delete=models.CASCADE, related_name="items")
    variant = models.ForeignKey("catalog.ProductVariant", on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=14, decimal_places=3)

    class Meta:
        db_table = "stock_transfer_items"

    def __str__(self):
        return f"{self.variant.sku} x {self.quantity} in Transfer #{self.transfer.transfer_number}"


class StockAdjustment(TenantScopedModel):
    STATUS_CHOICES = [
        ("PENDING", "Pending Approval"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
    ]
    warehouse = models.ForeignKey("branches.Warehouse", on_delete=models.CASCADE)
    reason = models.CharField(max_length=255)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="approved_adjustments"
    )

    class Meta:
        db_table = "stock_adjustments"
