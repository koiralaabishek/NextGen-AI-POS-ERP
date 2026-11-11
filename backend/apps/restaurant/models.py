from decimal import Decimal
from django.db import models
from common.models.base import TenantScopedModel, UUIDBaseModel, TimestampedModel


class RestaurantTable(TenantScopedModel):
    STATUS_CHOICES = [
        ("AVAILABLE", "Available"),
        ("OCCUPIED", "Occupied"),
        ("RESERVED", "Reserved"),
        ("BILLING", "Billing in progress"),
    ]
    branch = models.ForeignKey("branches.Branch", on_delete=models.CASCADE, related_name="tables")
    table_number = models.CharField(max_length=50)
    seating_capacity = models.PositiveIntegerField(default=4)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="AVAILABLE")

    class Meta:
        db_table = "restaurant_tables"
        unique_together = ("branch", "table_number")

    def __str__(self):
        return f"Table {self.table_number} ({self.status})"


class DiningOrder(TenantScopedModel):
    STATUS_CHOICES = [
        ("OPEN", "Open"),
        ("BILLED", "Billed"),
        ("PAID", "Paid & Completed"),
        ("CANCELLED", "Cancelled"),
    ]
    branch = models.ForeignKey("branches.Branch", on_delete=models.CASCADE)
    table = models.ForeignKey(RestaurantTable, on_delete=models.SET_NULL, null=True, blank=True, related_name="orders")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="OPEN")
    guest_count = models.PositiveIntegerField(default=1)

    class Meta:
        db_table = "dining_orders"


class KitchenOrder(TenantScopedModel):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("PREPARING", "Preparing in Kitchen"),
        ("READY", "Ready for Pickup"),
        ("SERVED", "Served to Table"),
    ]
    dining_order = models.ForeignKey(DiningOrder, on_delete=models.CASCADE, related_name="kitchen_orders")
    kot_number = models.CharField(max_length=50)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")

    class Meta:
        db_table = "kitchen_orders"


class KitchenOrderItem(UUIDBaseModel, TimestampedModel):
    kitchen_order = models.ForeignKey(KitchenOrder, on_delete=models.CASCADE, related_name="items")
    variant = models.ForeignKey("catalog.ProductVariant", on_delete=models.PROTECT)
    quantity = models.DecimalField(max_digits=8, decimal_places=2)
    special_instructions = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "kitchen_order_items"
