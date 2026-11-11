from decimal import Decimal
from django.db import models
from django.conf import settings
from common.models.base import TenantScopedModel, UUIDBaseModel, TimestampedModel


class Supplier(TenantScopedModel):
    name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=150, blank=True)
    phone = models.CharField(max_length=32, blank=True)
    email = models.EmailField(blank=True)
    tax_number = models.CharField(max_length=50, blank=True, help_text="PAN / VAT Number")
    address = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "suppliers"
        unique_together = ("organization", "name")
        ordering = ["name"]

    def __str__(self):
        return self.name


class PurchaseOrder(TenantScopedModel):
    STATUS_CHOICES = [
        ("DRAFT", "Draft"),
        ("ORDERED", "Ordered"),
        ("RECEIVED", "Goods Received"),
        ("CANCELLED", "Cancelled"),
    ]
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name="purchase_orders")
    warehouse = models.ForeignKey("branches.Warehouse", on_delete=models.CASCADE, related_name="purchase_orders")
    po_number = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="DRAFT")
    order_date = models.DateField(auto_now_add=True)
    expected_delivery = models.DateField(null=True, blank=True)
    total_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    tax_amount = models.DecimalField(max_digits=14, decimal_places=2, default=Decimal("0.00"))
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "purchase_orders"
        unique_together = ("organization", "po_number")

    def __str__(self):
        return f"PO {self.po_number} - {self.supplier.name}"


class PurchaseOrderItem(UUIDBaseModel, TimestampedModel):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name="items")
    variant = models.ForeignKey("catalog.ProductVariant", on_delete=models.CASCADE)
    quantity = models.DecimalField(max_digits=14, decimal_places=3)
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2)
    subtotal = models.DecimalField(max_digits=14, decimal_places=2)
    tax_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    class Meta:
        db_table = "purchase_order_items"


class GoodsReceipt(TenantScopedModel):
    purchase_order = models.ForeignKey(PurchaseOrder, on_delete=models.CASCADE, related_name="receipts")
    receipt_number = models.CharField(max_length=50)
    received_at = models.DateTimeField(auto_now_add=True)
    received_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "goods_receipts"
