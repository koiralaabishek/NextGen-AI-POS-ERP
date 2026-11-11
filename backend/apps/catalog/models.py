from django.db import models
from common.models.base import TenantScopedModel, UUIDBaseModel, TimestampedModel


class Category(TenantScopedModel):
    parent = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, related_name="children"
    )
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=180)
    description = models.TextField(blank=True)

    class Meta:
        db_table = "categories"
        unique_together = ("organization", "slug")
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name


class Brand(TenantScopedModel):
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=180)

    class Meta:
        db_table = "brands"
        unique_together = ("organization", "slug")

    def __str__(self):
        return self.name


class Unit(TenantScopedModel):
    name = models.CharField(max_length=50)  # Kilogram, Piece, Liter, Meter
    abbreviation = models.CharField(max_length=20)  # kg, pcs, ltr, m

    class Meta:
        db_table = "units"
        unique_together = ("organization", "abbreviation")

    def __str__(self):
        return f"{self.name} ({self.abbreviation})"


class Product(TenantScopedModel):
    PRODUCT_TYPES = [
        ("STANDARD", "Standard Physical Item"),
        ("VARIANT", "Item with Variants (Size/Color)"),
        ("SERVICE", "Service / Non-inventory"),
        ("COMBO", "Combo / Composite Kit"),
    ]

    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="products")
    brand = models.ForeignKey(Brand, on_delete=models.SET_NULL, null=True, blank=True, related_name="products")
    unit = models.ForeignKey(Unit, on_delete=models.SET_NULL, null=True, blank=True, related_name="products")
    sku = models.CharField(max_length=100)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    product_type = models.CharField(max_length=20, choices=PRODUCT_TYPES, default="STANDARD")
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=13.00, help_text="Default VAT % in Nepal is 13%")
    is_active = models.BooleanField(default=True, db_index=True)
    image_url = models.URLField(blank=True, null=True)

    class Meta:
        db_table = "products"
        unique_together = ("organization", "sku")
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} [{self.sku}]"


class ProductVariant(UUIDBaseModel, TimestampedModel):
    """Specific purchasable / barcode-scannable variant of a product."""
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="variants")
    sku = models.CharField(max_length=100)
    barcode = models.CharField(max_length=100, db_index=True, blank=True)
    attributes_json = models.JSONField(default=dict, blank=True, help_text="e.g. {'size': 'L', 'color': 'Red'}")
    cost_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    selling_price = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    reorder_level = models.DecimalField(max_digits=10, decimal_places=2, default=5.00)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "product_variants"
        unique_together = ("product", "sku")

    def __str__(self):
        attrs = ", ".join(f"{k}: {v}" for k, v in self.attributes_json.items()) if self.attributes_json else "Default"
        return f"{self.product.name} ({attrs})"


class PriceList(TenantScopedModel):
    name = models.CharField(max_length=100)
    currency = models.CharField(max_length=3, default="NPR")
    is_default = models.BooleanField(default=False)

    class Meta:
        db_table = "price_lists"
        unique_together = ("organization", "name")

    def __str__(self):
        return self.name


class ProductPrice(UUIDBaseModel, TimestampedModel):
    variant = models.ForeignKey(ProductVariant, on_delete=models.CASCADE, related_name="prices")
    price_list = models.ForeignKey(PriceList, on_delete=models.CASCADE, related_name="variant_prices")
    price = models.DecimalField(max_digits=12, decimal_places=2)

    class Meta:
        db_table = "product_prices"
        unique_together = ("variant", "price_list")
