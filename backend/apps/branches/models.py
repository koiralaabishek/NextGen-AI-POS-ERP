from django.db import models
from common.models.base import TenantScopedModel


class Branch(TenantScopedModel):
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=50)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=32, blank=True)
    email = models.EmailField(blank=True)
    is_active = models.BooleanField(default=True, db_index=True)
    is_headquarters = models.BooleanField(default=False)

    class Meta:
        db_table = "branches"
        unique_together = ("organization", "code")
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.code})"


class Warehouse(TenantScopedModel):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name="warehouses")
    name = models.CharField(max_length=150)
    code = models.CharField(max_length=50)
    is_primary = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "warehouses"
        unique_together = ("organization", "code")
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} [{self.branch.name}]"


class Device(TenantScopedModel):
    DEVICE_TYPES = [
        ("POS_TERMINAL", "POS Terminal"),
        ("KDS", "Kitchen Display System"),
        ("SCANNER", "Mobile Barcode Scanner"),
        ("KIOSK", "Self-Checkout Kiosk"),
    ]
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name="devices")
    device_code = models.CharField(max_length=100)
    device_name = models.CharField(max_length=150)
    device_type = models.CharField(max_length=30, choices=DEVICE_TYPES, default="POS_TERMINAL")
    last_seen = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "devices"
        unique_together = ("organization", "device_code")

    def __str__(self):
        return f"{self.device_name} ({self.device_code})"
