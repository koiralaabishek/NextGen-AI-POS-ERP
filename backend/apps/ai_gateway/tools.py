from decimal import Decimal
from django.db.models import Sum, Count, F, Q
from django.utils import timezone
from apps.sales.models import Sale, SaleItem
from apps.inventory.models import StockBalance
from apps.accounting.models import Expense


class BusinessAITools:
    """
    Sanitized, tenant-isolated query tools providing structured business intelligence
    to the AI service without granting arbitrary SQL execution capabilities.
    """

    @classmethod
    def get_sales_summary(cls, organization, start_date=None, end_date=None, branch_id=None):
        qs = Sale.objects.filter(organization=organization, status="COMPLETED")
        if start_date:
            qs = qs.filter(created_at__date__gte=start_date)
        if end_date:
            qs = qs.filter(created_at__date__lte=end_date)
        if branch_id:
            qs = qs.filter(branch_id=branch_id)

        metrics = qs.aggregate(
            total_sales_count=Count("id"),
            total_revenue=Sum("total_amount"),
            total_vat_collected=Sum("tax_amount"),
            total_discounts=Sum("discount_amount"),
        )
        return {
            "period": {"start_date": str(start_date), "end_date": str(end_date)},
            "total_transactions": metrics["total_sales_count"] or 0,
            "total_revenue": str(metrics["total_revenue"] or Decimal("0.00")),
            "total_vat_collected": str(metrics["total_vat_collected"] or Decimal("0.00")),
            "total_discounts": str(metrics["total_discounts"] or Decimal("0.00")),
            "currency": organization.currency,
        }

    @classmethod
    def get_top_products(cls, organization, limit=5, start_date=None, end_date=None):
        qs = SaleItem.objects.filter(
            sale__organization=organization,
            sale__status="COMPLETED"
        )
        if start_date:
            qs = qs.filter(sale__created_at__date__gte=start_date)
        if end_date:
            qs = qs.filter(sale__created_at__date__lte=end_date)

        top_items = qs.values(
            "variant__sku", "variant__product__name"
        ).annotate(
            total_quantity=Sum("quantity"),
            total_gross=Sum("subtotal")
        ).order_by("-total_quantity")[:limit]

        return [
            {
                "sku": item["variant__sku"],
                "name": item["variant__product__name"],
                "quantity_sold": str(item["total_quantity"]),
                "gross_revenue": str(item["total_gross"]),
            }
            for item in top_items
        ]

    @classmethod
    def get_low_stock_products(cls, organization, warehouse_id=None):
        qs = StockBalance.objects.filter(
            organization=organization,
            quantity__lte=F("variant__reorder_level")
        ).select_related("variant", "variant__product", "warehouse")

        if warehouse_id:
            qs = qs.filter(warehouse_id=warehouse_id)

        return [
            {
                "sku": b.variant.sku,
                "name": b.variant.product.name,
                "warehouse": b.warehouse.name,
                "current_stock": str(b.quantity),
                "reorder_level": str(b.variant.reorder_level),
            }
            for b in qs[:20]
        ]
