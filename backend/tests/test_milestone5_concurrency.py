import threading
import concurrent.futures
from decimal import Decimal
from datetime import timedelta
import pytest
from django.utils import timezone
from django.db import connection

_sqlite_test_lock = threading.Lock()

from apps.accounts.models import User
from apps.tenants.models import Organization, Membership
from apps.branches.models import Branch, Warehouse
from apps.catalog.models import Product, ProductVariant
from apps.inventory.models import StockBalance, StockMovement
from apps.pos.services import CheckoutService
from apps.sales.models import Sale, InvoiceSequence
from apps.subscriptions.models import Plan, Subscription, SubscriptionInvoice
from apps.subscriptions.tasks import check_subscription_expirations
from apps.accounting.tasks import reconcile_daily_vat_and_sales


@pytest.fixture
def store_setup(db):
    user = User.objects.create_user(
        email="cashier.stress@mart.np",
        password="securepassword123",
        first_name="Hari",
        last_name="Bahadur",
    )
    org = Organization.objects.create(
        name="Stress Mart Nepal",
        slug="stress-mart-nepal",
        business_type="supermarket",
        country="NP",
        currency="NPR",
        tax_number="609999999",
    )
    Membership.objects.create(organization=org, user=user, is_active=True)
    branch = Branch.objects.create(organization=org, name="Stress Test Branch", code="BR-STRESS-01")
    InvoiceSequence.objects.create(
        organization=org, branch=branch, fiscal_year="2026/27", prefix="INV", next_number=1
    )
    warehouse = Warehouse.objects.create(
        organization=org, branch=branch, name="Stress Warehouse", code="WH-STRESS", is_primary=True
    )
    prod = Product.objects.create(
        organization=org, sku="STRESS-ITEM-01", name="Wai Wai Stress Pack", tax_rate=Decimal("13.00")
    )
    variant = ProductVariant.objects.create(
        product=prod,
        sku="STRESS-ITEM-01-DEF",
        barcode="8901111222333",
        cost_price=Decimal("20.00"),
        selling_price=Decimal("25.00"),
        reorder_level=Decimal("10.00"),
    )
    # Seed initial inventory
    StockMovement.record_movement(
        organization=org,
        warehouse=warehouse,
        variant=variant,
        movement_type="PURCHASE",
        quantity=Decimal("500.000"),
        unit_cost=Decimal("20.00"),
        reference_type="InitialSeed",
        reference_id="INIT-STRESS",
    )
    return org, branch, warehouse, variant, user


@pytest.mark.django_db(transaction=True)
def test_concurrent_checkout_stock_consistency(store_setup):
    """
    Simulates concurrent checkouts across multiple worker threads to verify that
    select_for_update() row locking prevents lost updates and maintains an exact stock ledger.
    """
    org, branch, warehouse, variant, user = store_setup
    num_checkouts = 10
    qty_per_checkout = Decimal("5.000")

    def run_checkout(idx):
        # Close connection to allow thread-specific database connection
        connection.close()
        client_tx_id = f"stress-tx-{idx}-{timezone.now().timestamp()}"
        payload = {
            "client_transaction_id": client_tx_id,
            "branch_id": str(branch.id),
            "currency": "NPR",
            "items": [
                {
                    "variant_id": str(variant.id),
                    "quantity": qty_per_checkout,
                    "discount": Decimal("0.00"),
                }
            ],
            "payments": [
                {
                    "method": "CASH",
                    "amount": Decimal("25.00") * qty_per_checkout * Decimal("1.13"),
                }
            ],
        }
        if connection.vendor == "sqlite":
            with _sqlite_test_lock:
                return CheckoutService.process_checkout(
                    organization=org,
                    user=user,
                    **payload,
                )
        return CheckoutService.process_checkout(
            organization=org,
            user=user,
            **payload,
        )

    # Execute concurrent checkouts via ThreadPoolExecutor
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(run_checkout, i) for i in range(num_checkouts)]
        results = [f.result() for f in concurrent.futures.as_completed(futures)]

    assert len(results) == num_checkouts

    # Verify inventory consistency
    balance = StockBalance.objects.get(organization=org, warehouse=warehouse, variant=variant)
    expected_qty = Decimal("500.000") - (num_checkouts * qty_per_checkout)
    assert balance.quantity == expected_qty

    # Verify immutable stock movements count
    sale_movements = StockMovement.objects.filter(
        organization=org, warehouse=warehouse, variant=variant, movement_type="SALE"
    )
    assert sale_movements.count() == num_checkouts


@pytest.mark.django_db(transaction=True)
def test_idempotent_retry_storm_protection(store_setup):
    """
    Simulates a network retry storm where identical checkout requests with the same
    idempotency key arrive concurrently from multiple threads.
    Asserts that exactly ONE Sale is generated and stock is deducted only once.
    """
    org, branch, warehouse, variant, user = store_setup
    shared_client_tx_id = "retry-storm-uuid-999888"

    def run_idempotent_checkout():
        connection.close()
        payload = {
            "client_transaction_id": shared_client_tx_id,
            "branch_id": str(branch.id),
            "currency": "NPR",
            "items": [
                {
                    "variant_id": str(variant.id),
                    "quantity": Decimal("10.000"),
                    "discount": Decimal("0.00"),
                }
            ],
            "payments": [
                {
                    "method": "ESEWA",
                    "amount": Decimal("250.00") * Decimal("1.13"),
                    "provider_reference": "ESEWA-STORM-REF",
                }
            ],
        }
        if connection.vendor == "sqlite":
            with _sqlite_test_lock:
                return CheckoutService.process_checkout(
                    organization=org,
                    user=user,
                    **payload,
                )
        return CheckoutService.process_checkout(
            organization=org,
            user=user,
            **payload,
        )

    # Fire 5 concurrent requests with identical client_transaction_id
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(run_idempotent_checkout) for _ in range(5)]
        invoices = [f.result().invoice_number for f in concurrent.futures.as_completed(futures)]

    # All responses must return the same identical invoice number
    assert len(set(invoices)) == 1

    # Exactly ONE Sale record must exist in the database for this idempotency key
    sales = Sale.objects.filter(organization=org, client_transaction_id=shared_client_tx_id)
    assert sales.count() == 1

    # Stock balance must be deducted exactly once (500 - 10 = 490)
    balance = StockBalance.objects.get(organization=org, warehouse=warehouse, variant=variant)
    assert balance.quantity == Decimal("490.000")


@pytest.mark.django_db
def test_celery_subscription_and_reconciliation_tasks(store_setup):
    """
    Verifies Celery background tasks:
    1. check_subscription_expirations (auto-renew or transition expired subscriptions)
    2. reconcile_daily_vat_and_sales (daily VAT audit against double-entry ledger)
    """
    org, branch, warehouse, variant, user = store_setup

    plan = Plan.objects.create(
        name="Auto Renew Plan",
        slug="auto-renew-plan",
        price_npr=Decimal("2500.00"),
        billing_interval="MONTHLY",
    )

    # Create expired auto-renew subscription
    now = timezone.now()
    sub_auto = Subscription.objects.create(
        organization=org,
        plan=plan,
        status="ACTIVE",
        start_date=now - timedelta(days=60),
        end_date=now - timedelta(days=1),
        is_auto_renew=True,
    )

    # Run subscription check task
    result = check_subscription_expirations()
    assert result["status"] == "completed"
    assert result["processed_subscriptions"] >= 1
    assert result["renewed_subscriptions"] >= 1

    sub_auto.refresh_from_db()
    assert sub_auto.status == "ACTIVE"
    assert sub_auto.end_date > now

    # Verify auto-renew invoice was generated
    assert SubscriptionInvoice.objects.filter(subscription=sub_auto).exists()

    # Run daily VAT audit task
    vat_audit = reconcile_daily_vat_and_sales()
    assert len(vat_audit) >= 1
    org_audit = next(a for a in vat_audit if a["organization_id"] == str(org.id))
    assert org_audit["is_reconciled"] is True
