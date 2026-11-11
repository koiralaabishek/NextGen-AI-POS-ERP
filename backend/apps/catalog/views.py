from rest_framework import viewsets, permissions, filters
from apps.catalog.models import Category, Brand, Unit, Product, ProductVariant, PriceList
from apps.catalog.serializers import (
    CategorySerializer,
    BrandSerializer,
    UnitSerializer,
    ProductSerializer,
    ProductVariantSerializer,
    PriceListSerializer,
)
from common.permissions.tenant import IsTenantMember


class CategoryViewSet(viewsets.ModelViewSet):
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticated, IsTenantMember]

    def get_queryset(self):
        return Category.objects.filter(organization=self.request.organization)


class BrandViewSet(viewsets.ModelViewSet):
    serializer_class = BrandSerializer
    permission_classes = [permissions.IsAuthenticated, IsTenantMember]

    def get_queryset(self):
        return Brand.objects.filter(organization=self.request.organization)


class UnitViewSet(viewsets.ModelViewSet):
    serializer_class = UnitSerializer
    permission_classes = [permissions.IsAuthenticated, IsTenantMember]

    def get_queryset(self):
        return Unit.objects.filter(organization=self.request.organization)


class ProductViewSet(viewsets.ModelViewSet):
    serializer_class = ProductSerializer
    permission_classes = [permissions.IsAuthenticated, IsTenantMember]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "sku", "variants__barcode"]
    ordering_fields = ["name", "created_at"]

    def get_queryset(self):
        return Product.objects.filter(organization=self.request.organization).prefetch_related("variants", "category")


class ProductVariantViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ProductVariantSerializer
    permission_classes = [permissions.IsAuthenticated, IsTenantMember]
    filter_backends = [filters.SearchFilter]
    search_fields = ["sku", "barcode", "product__name"]

    def get_queryset(self):
        return ProductVariant.objects.filter(product__organization=self.request.organization)


class PriceListViewSet(viewsets.ModelViewSet):
    serializer_class = PriceListSerializer
    permission_classes = [permissions.IsAuthenticated, IsTenantMember]

    def get_queryset(self):
        return PriceList.objects.filter(organization=self.request.organization)
