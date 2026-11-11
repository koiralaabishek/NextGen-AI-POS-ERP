from rest_framework import serializers
from apps.catalog.models import Category, Brand, Unit, Product, ProductVariant, PriceList, ProductPrice


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "parent", "name", "slug", "description"]


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ["id", "name", "slug"]


class UnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = Unit
        fields = ["id", "name", "abbreviation"]


class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = ["id", "sku", "barcode", "attributes_json", "cost_price", "selling_price", "reorder_level", "is_active"]


class ProductSerializer(serializers.ModelSerializer):
    variants = ProductVariantSerializer(many=True, required=False)
    category_name = serializers.ReadOnlyField(source="category.name")
    unit_abbreviation = serializers.ReadOnlyField(source="unit.abbreviation")

    class Meta:
        model = Product
        fields = [
            "id", "category", "category_name", "brand", "unit", "unit_abbreviation",
            "sku", "name", "description", "product_type", "tax_rate", "is_active",
            "image_url", "variants", "created_at"
        ]
        read_only_fields = ["id", "created_at"]

    def create(self, validated_data):
        variants_data = validated_data.pop("variants", [])
        org = self.context["request"].organization
        product = Product.objects.create(organization=org, **validated_data)

        if variants_data:
            for v_data in variants_data:
                ProductVariant.objects.create(product=product, **v_data)
        else:
            # Create a default variant if none provided
            ProductVariant.objects.create(
                product=product,
                sku=f"{product.sku}-DEF",
                barcode=product.sku,
                cost_price=0.00,
                selling_price=0.00,
            )
        return product


class PriceListSerializer(serializers.ModelSerializer):
    class Meta:
        model = PriceList
        fields = ["id", "name", "currency", "is_default"]
