from decimal import Decimal
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.accounts.models import User
from apps.tenants.models import Organization, Membership, BusinessSettings
from apps.branches.models import Branch, Warehouse, Device
from apps.catalog.models import Category, Unit, Brand, Product, ProductVariant
from apps.inventory.models import StockBalance, StockMovement
from apps.accounting.models import Account, FiscalPeriod
from apps.sales.models import Customer, InvoiceSequence
from apps.subscriptions.models import Plan, PlanFeature, Subscription, SubscriptionInvoice


class Command(BaseCommand):
    help = "Seeds comprehensive, realistic demo data for NextGen AI POS & ERP (Nepal retail & supermarket demo)."

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting NextGen AI POS & ERP Demo Data Seeding..."))

        # 1. SaaS Subscription Plans
        self.stdout.write("1. Provisioning SaaS Subscription Plans...")
        starter_plan, _ = Plan.objects.get_or_create(
            slug="starter",
            defaults={
                "name": "Starter Plan",
                "price_npr": Decimal("2500.00"),
                "billing_interval": "MONTHLY",
                "max_branches": 1,
                "max_users": 2,
                "ai_monthly_credits": 50,
            },
        )
        pro_plan, _ = Plan.objects.get_or_create(
            slug="professional",
            defaults={
                "name": "Professional Plan",
                "price_npr": Decimal("6500.00"),
                "billing_interval": "MONTHLY",
                "max_branches": 3,
                "max_users": 8,
                "ai_monthly_credits": 250,
            },
        )
        enterprise_plan, _ = Plan.objects.get_or_create(
            slug="enterprise",
            defaults={
                "name": "Enterprise Plan",
                "price_npr": Decimal("15000.00"),
                "billing_interval": "MONTHLY",
                "max_branches": 20,
                "max_users": 50,
                "ai_monthly_credits": 1000,
            },
        )

        for plan in [starter_plan, pro_plan, enterprise_plan]:
            PlanFeature.objects.get_or_create(
                plan=plan, feature_code="pos.enabled", defaults={"feature_name": "POS Terminal", "is_enabled": True}
            )
            PlanFeature.objects.get_or_create(
                plan=plan, feature_code="ai.copilot", defaults={"feature_name": "AI Assistant", "is_enabled": True}
            )
            PlanFeature.objects.get_or_create(
                plan=plan, feature_code="accounting.full", defaults={"feature_name": "Double Entry ERP", "is_enabled": True}
            )

        # 2. Users
        self.stdout.write("2. Creating Platform Admin & Store Cashier Users...")
        admin_user, _ = User.objects.get_or_create(
            email="admin@namaste.np",
            defaults={
                "first_name": "Bikash",
                "last_name": "Adhikari",
                "is_platform_admin": True,
                "is_staff": True,
                "is_superuser": True,
            },
        )
        admin_user.set_password("password123")
        admin_user.save()

        cashier_user, _ = User.objects.get_or_create(
            email="cashier1@namaste.np",
            defaults={"first_name": "Pooja", "last_name": "Sharma"},
        )
        cashier_user.set_password("password123")
        cashier_user.save()

        # 3. Demo Organization
        self.stdout.write("3. Provisioning Organization: Namaste Supermarket Pvt. Ltd...")
        org, _ = Organization.objects.get_or_create(
            slug="namaste-mart",
            defaults={
                "name": "Namaste Supermarket Pvt. Ltd.",
                "business_type": "supermarket",
                "country": "NP",
                "currency": "NPR",
                "timezone": "Asia/Kathmandu",
                "tax_number": "601234567",
                "phone": "+977-1-4234567",
                "email": "contact@namaste.np",
                "address": "New Road, Ward 22, Kathmandu, Nepal",
                "onboarding_completed": True,
            },
        )

        Membership.objects.get_or_create(organization=org, user=admin_user, defaults={"is_active": True})
        Membership.objects.get_or_create(organization=org, user=cashier_user, defaults={"is_active": True})

        BusinessSettings.objects.get_or_create(
            organization=org,
            defaults={
                "settings_json": {
                    "vat_rate": 13.0,
                    "default_currency": "NPR",
                    "receipt_footer": "धन्यवाद! फेरि आउनुहोला।",
                    "fiscal_year": "2083/84",
                }
            },
        )

        # 4. Active Subscription
        now = timezone.now()
        sub, _ = Subscription.objects.get_or_create(
            organization=org,
            defaults={
                "plan": enterprise_plan,
                "status": "ACTIVE",
                "start_date": now,
                "end_date": now + timedelta(days=365),
                "is_auto_renew": True,
            },
        )

        # 5. Branch & Warehouses
        self.stdout.write("4. Creating Branches, Warehouses & POS Devices...")
        branch, _ = Branch.objects.get_or_create(
            organization=org,
            code="KTM-HQ-01",
            defaults={
                "name": "Kathmandu Flagship Store",
                "address": "New Road Gate, Kathmandu",
                "phone": "+977-1-4234567",
                "is_headquarters": True,
            },
        )

        wh_central, _ = Warehouse.objects.get_or_create(
            organization=org,
            code="WH-CENTRAL",
            defaults={"name": "Central Warehouse (KTM)", "branch": branch, "is_primary": True},
        )

        wh_store, _ = Warehouse.objects.get_or_create(
            organization=org,
            code="WH-STORE",
            defaults={"name": "Store Front Shelf", "branch": branch, "is_primary": False},
        )

        Device.objects.get_or_create(
            organization=org,
            device_code="TERM-KTM-01",
            defaults={"branch": branch, "device_name": "Checkout Lane 1 POS Terminal"},
        )

        InvoiceSequence.objects.get_or_create(
            organization=org,
            branch=branch,
            fiscal_year="2083/84",
            defaults={"prefix": "INV", "next_number": 105},
        )

        # 6. Chart of Accounts
        self.stdout.write("5. Initializing Nepal Chart of Accounts...")
        accounts_spec = [
            ("1000", "Cash in Hand (POS Till)", "ASSET"),
            ("1010", "Digital Wallets (eSewa / Khalti / Fonepay)", "ASSET"),
            ("1100", "Accounts Receivable (Customer Khata)", "ASSET"),
            ("1200", "Merchandise Inventory Asset", "ASSET"),
            ("2000", "Accounts Payable (Suppliers)", "LIABILITY"),
            ("2200", "Output VAT Payable (13% IRD)", "LIABILITY"),
            ("3000", "Owner's Equity & Capital", "EQUITY"),
            ("4000", "Gross Sales Revenue", "REVENUE"),
            ("5000", "Cost of Goods Sold (COGS)", "EXPENSE"),
        ]
        for code, name, acct_type in accounts_spec:
            Account.objects.get_or_create(
                organization=org,
                account_code=code,
                defaults={"account_name": name, "account_type": acct_type},
            )

        FiscalPeriod.objects.get_or_create(
            organization=org,
            name="Fiscal Year 2083/84",
            defaults={
                "start_date": timezone.now().date().replace(month=7, day=16),
                "end_date": timezone.now().date().replace(month=7, day=15) + timedelta(days=365),
                "is_closed": False,
            },
        )

        # 7. Catalog & Stock Balances
        self.stdout.write("6. Seeding Product Catalog & Multi-Warehouse Stock...")
        cat_staples, _ = Category.objects.get_or_create(organization=org, slug="grains-staples", defaults={"name": "Grains & Staples"})
        cat_oil, _ = Category.objects.get_or_create(organization=org, slug="oil-ghee", defaults={"name": "Cooking Oil & Ghee"})
        cat_snacks, _ = Category.objects.get_or_create(organization=org, slug="packaged-snacks", defaults={"name": "Packaged Snacks"})
        cat_dairy, _ = Category.objects.get_or_create(organization=org, slug="dairy-eggs", defaults={"name": "Dairy & Eggs"})

        unit_bag, _ = Unit.objects.get_or_create(organization=org, name="Bag", defaults={"abbreviation": "bag"})
        unit_bottle, _ = Unit.objects.get_or_create(organization=org, name="Bottle", defaults={"abbreviation": "btl"})
        unit_pkt, _ = Unit.objects.get_or_create(organization=org, name="Packet", defaults={"abbreviation": "pkt"})

        products_spec = [
            ("WHT-FLOUR-5KG", "8901234567890", "Shakti Wheat Flour 5kg", cat_staples, unit_bag, Decimal("410.00"), Decimal("475.00"), Decimal("13.00"), Decimal("25.00"), 180, 20),
            ("BASMATI-RICE-25KG", "8909876543210", "Himalayan Basmati Rice 25kg", cat_staples, unit_bag, Decimal("2400.00"), Decimal("2850.00"), Decimal("13.00"), Decimal("10.00"), 60, 10),
            ("MUSTARD-OIL-1L", "8901122334455", "Dhara Pure Mustard Oil 1L", cat_oil, unit_bottle, Decimal("210.00"), Decimal("245.00"), Decimal("13.00"), Decimal("20.00"), 50, 15),
            ("WAI-WAI-NOODLE", "8905544332211", "Wai Wai Quick Chicken 75g", cat_snacks, unit_pkt, Decimal("20.00"), Decimal("25.00"), Decimal("13.00"), Decimal("50.00"), 200, 40),
            ("MILK-FULL-CREAM", "8906677889900", "DDC Pasteurised Milk 500ml", cat_dairy, unit_pkt, Decimal("42.00"), Decimal("50.00"), Decimal("0.00"), Decimal("30.00"), 25, 10),
        ]

        for sku, barcode, name, cat, unit, cost, sell, tax, reorder, wh_central_qty, wh_store_qty in products_spec:
            p, _ = Product.objects.get_or_create(
                organization=org,
                sku=sku,
                defaults={"name": name, "category": cat, "unit": unit, "tax_rate": tax, "product_type": "STANDARD"},
            )
            v, _ = ProductVariant.objects.get_or_create(
                product=p,
                sku=f"{sku}-DEF",
                defaults={"barcode": barcode, "cost_price": cost, "selling_price": sell, "reorder_level": reorder},
            )

            # Ensure stock balances
            StockMovement.record_movement(
                organization=org,
                warehouse=wh_central,
                variant=v,
                movement_type="PURCHASE",
                quantity=Decimal(str(wh_central_qty)),
                unit_cost=cost,
                reference_type="InitialSeed",
                reference_id="SEED-01",
                performed_by=admin_user,
            )
            StockMovement.record_movement(
                organization=org,
                warehouse=wh_store,
                variant=v,
                movement_type="TRANSFER_IN",
                quantity=Decimal(str(wh_store_qty)),
                unit_cost=cost,
                reference_type="InitialSeed",
                reference_id="SEED-02",
                performed_by=admin_user,
            )

        # 8. Customers with Khata (Credit Ledger)
        self.stdout.write("7. Seeding Customer Khata profiles...")
        customers_spec = [
            ("Ramesh Sharma", "9851001122", "302948571", Decimal("10000.00"), Decimal("2450.00"), 340),
            ("Sita Thapa", "9841223344", "", Decimal("5000.00"), Decimal("0.00"), 120),
            ("Kushal Shrestha", "9801334455", "301928374", Decimal("25000.00"), Decimal("14200.00"), 850),
        ]
        for cname, phone, pan, limit, debt, pts in customers_spec:
            Customer.objects.get_or_create(
                organization=org,
                phone=phone,
                defaults={
                    "name": cname,
                    "tax_number": pan,
                    "credit_limit": limit,
                    "current_credit": debt,
                    "loyalty_points": pts,
                },
            )

        self.stdout.write(self.style.SUCCESS("✓ NextGen AI POS & ERP demo dataset successfully seeded!"))
        self.stdout.write(self.style.SUCCESS("  Admin credentials: admin@namaste.np / password123"))
        self.stdout.write(self.style.SUCCESS("  Cashier credentials: cashier1@namaste.np / password123"))
        self.stdout.write(self.style.SUCCESS("  Organization: Namaste Supermarket Pvt. Ltd. (slug: namaste-mart)"))
