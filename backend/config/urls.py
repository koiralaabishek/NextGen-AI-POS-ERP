from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

from apps.accounts.views import (
    RegisterView,
    CustomTokenObtainPairView,
    UserProfileView,
    RoleViewSet,
    PermissionListView,
)
from apps.tenants.views import OrganizationViewSet, MembershipViewSet, AuditLogViewSet
from apps.branches.views import BranchViewSet, WarehouseViewSet, DeviceViewSet
from apps.catalog.views import (
    CategoryViewSet,
    BrandViewSet,
    UnitViewSet,
    ProductViewSet,
    ProductVariantViewSet,
    PriceListViewSet,
)
from apps.inventory.views import (
    StockBalanceViewSet,
    StockMovementViewSet,
    StockAdjustmentViewSet,
    StockTransferViewSet,
    StockBatchViewSet,
)
from apps.procurement.views import (
    SupplierViewSet,
    PurchaseOrderViewSet,
    GoodsReceiptViewSet,
)
from apps.pos.views import (
    CheckoutAPIView,
    PosTerminalViewSet,
    CashierShiftViewSet,
    HeldSaleViewSet,
)
from apps.sales.views import CustomerViewSet, SaleViewSet
from apps.payments.views import EsewaVerifyAPIView, KhaltiVerifyAPIView
from apps.accounting.views import (
    AccountViewSet,
    JournalEntryViewSet,
    FiscalPeriodViewSet,
    ExpenseViewSet,
    TaxRateViewSet,
    TrialBalanceAPIView,
    ProfitAndLossAPIView,
    BalanceSheetAPIView,
    VatSalesBookAPIView,
    VatPurchaseBookAPIView,
    VatReturnSummaryAPIView,
)
from apps.subscriptions.views import PlanViewSet, SubscriptionViewSet
from apps.restaurant.views import (
    RestaurantTableViewSet,
    DiningOrderViewSet,
    KitchenOrderViewSet,
)
from apps.wholesale.views import (
    PriceTierViewSet,
    CustomerCreditLimitViewSet,
    CreditTransactionViewSet,
    SettleWholesaleKhataAPIView,
)

router = DefaultRouter()

# Tenants & Permissions
router.register(r"organizations", OrganizationViewSet, basename="organization")
router.register(r"memberships", MembershipViewSet, basename="membership")
router.register(r"audit-logs", AuditLogViewSet, basename="audit-log")
router.register(r"roles", RoleViewSet, basename="role")

# Branches & Devices
router.register(r"branches", BranchViewSet, basename="branch")
router.register(r"warehouses", WarehouseViewSet, basename="warehouse")
router.register(r"devices", DeviceViewSet, basename="device")

# Catalog
router.register(r"categories", CategoryViewSet, basename="category")
router.register(r"brands", BrandViewSet, basename="brand")
router.register(r"units", UnitViewSet, basename="unit")
router.register(r"products", ProductViewSet, basename="product")
router.register(r"product-variants", ProductVariantViewSet, basename="product-variant")
router.register(r"price-lists", PriceListViewSet, basename="price-list")

# Inventory
router.register(r"inventory/balances", StockBalanceViewSet, basename="stock-balance")
router.register(r"inventory/movements", StockMovementViewSet, basename="stock-movement")
router.register(r"inventory/adjustments", StockAdjustmentViewSet, basename="stock-adjustment")
router.register(r"inventory/transfers", StockTransferViewSet, basename="stock-transfer")
router.register(r"inventory/batches", StockBatchViewSet, basename="stock-batch")

# Procurement
router.register(r"procurement/suppliers", SupplierViewSet, basename="supplier")
router.register(r"procurement/purchase-orders", PurchaseOrderViewSet, basename="purchase-order")
router.register(r"procurement/goods-receipts", GoodsReceiptViewSet, basename="goods-receipt")

# POS Terminals, Shifts & Held Sales
router.register(r"pos/terminals", PosTerminalViewSet, basename="pos-terminal")
router.register(r"pos/shifts", CashierShiftViewSet, basename="cashier-shift")
router.register(r"pos/held-sales", HeldSaleViewSet, basename="held-sale")

# Sales & Customers
router.register(r"customers", CustomerViewSet, basename="customer")
router.register(r"sales", SaleViewSet, basename="sale")

# Accounting
router.register(r"accounting/accounts", AccountViewSet, basename="account")
router.register(r"accounting/journals", JournalEntryViewSet, basename="journal-entry")
router.register(r"accounting/fiscal-periods", FiscalPeriodViewSet, basename="fiscal-period")
router.register(r"accounting/expenses", ExpenseViewSet, basename="expense")
router.register(r"accounting/tax-rates", TaxRateViewSet, basename="tax-rate")

# SaaS Subscriptions & Plans
router.register(r"subscriptions/plans", PlanViewSet, basename="subscription-plan")
router.register(r"subscriptions", SubscriptionViewSet, basename="subscription")

# Restaurant POS & KDS
router.register(r"restaurant/tables", RestaurantTableViewSet, basename="restaurant-table")
router.register(r"restaurant/orders", DiningOrderViewSet, basename="dining-order")
router.register(r"restaurant/kitchen-orders", KitchenOrderViewSet, basename="kitchen-order")

# Wholesale & Credit Khata
router.register(r"wholesale/price-tiers", PriceTierViewSet, basename="price-tier")
router.register(r"wholesale/credit-limits", CustomerCreditLimitViewSet, basename="customer-credit-limit")
router.register(r"wholesale/credit-transactions", CreditTransactionViewSet, basename="credit-transaction")

urlpatterns = [
    path("admin/", admin.site.urls),

    # Authentication
    path("api/v1/auth/register/", RegisterView.as_view(), name="auth-register"),
    path("api/v1/auth/token/", CustomTokenObtainPairView.as_view(), name="token-obtain-pair"),
    path("api/v1/auth/profile/", UserProfileView.as_view(), name="auth-profile"),
    path("api/v1/auth/permissions/", PermissionListView.as_view(), name="auth-permissions"),

    # POS Checkout Engine
    path("api/v1/pos/checkout/", CheckoutAPIView.as_view(), name="pos-checkout"),

    # Payment Gateways (eSewa & Khalti Callbacks)
    path("api/v1/payments/esewa/verify/", EsewaVerifyAPIView.as_view(), name="payment-esewa-verify"),
    path("api/v1/payments/khalti/verify/", KhaltiVerifyAPIView.as_view(), name="payment-khalti-verify"),

    # Wholesale Khata Settlement
    path("api/v1/wholesale/credit/settle/", SettleWholesaleKhataAPIView.as_view(), name="wholesale-credit-settle"),

    # Financial & Tax Reporting Endpoints
    path("api/v1/accounting/reports/trial-balance/", TrialBalanceAPIView.as_view(), name="report-trial-balance"),
    path("api/v1/accounting/reports/profit-loss/", ProfitAndLossAPIView.as_view(), name="report-profit-loss"),
    path("api/v1/accounting/reports/balance-sheet/", BalanceSheetAPIView.as_view(), name="report-balance-sheet"),
    path("api/v1/accounting/reports/vat-sales-book/", VatSalesBookAPIView.as_view(), name="report-vat-sales-book"),
    path("api/v1/accounting/reports/vat-purchase-book/", VatPurchaseBookAPIView.as_view(), name="report-vat-purchase-book"),
    path("api/v1/accounting/reports/vat-return-summary/", VatReturnSummaryAPIView.as_view(), name="report-vat-return-summary"),

    # Router Endpoints
    path("api/v1/", include(router.urls)),

    # API Documentation (OpenAPI / Swagger / Redoc)
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]
