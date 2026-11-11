import pytest
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.utils import timezone
from rest_framework.test import APIClient
from apps.accounts.models import User, Role
from apps.tenants.models import Organization, Membership
from apps.branches.models import Branch, Warehouse
from apps.catalog.models import Product, ProductVariant
from apps.inventory.models import StockBalance, StockMovement, StockTransfer, StockTransferItem
from apps.procurement.models import Supplier, PurchaseOrder, PurchaseOrderItem
from apps.procurement.services import ProcurementService
from apps.pos.models import PosTerminal, CashierShift, HeldSale
from apps.pos.services import CheckoutService
from apps.sales.models import Customer, Sale
from apps.sales.services.receipt import ThermalReceiptGenerator
from apps.wholesale.models import CreditTransaction
from apps.accounting.models import JournalEntry
from common.middleware.tenant import set_current_tenant_id, clear_current_tenant


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def base_setup(db):
    user = User.objects.create_user(email="manager@mart.com", password="password123", first_name="Bikash")
    org = Organization.objects.create(name="Bikash Supermart", slug="bikash-mart", currency="NPR", tax_number="302918273")
    role = Role.objects.create(organization=org, name="Manager", is_owner=True, is_admin=True)
    Membership.objects.create(organization=org, user=user, role=role)

    branch = Branch.objects.create(organization=org, name="Kathmandu Main", code="KTM-01", address="New Road, Kathmandu")
    wh1 = Warehouse.objects.create(organization=org, branch=branch, name="Store Floor WH", code="WH-FLOOR", is_primary=True)
    wh2 = Warehouse.objects.create(organization=org, branch=branch, name="Central Storage WH", code="WH-CENTRAL")

    terminal = PosTerminal.objects.create(organization=org, branch=branch, terminal_code="T-01", name="Till 1")

    product = Product.objects.create(organization=org, name="Sunflow Sunflower Oil 1L", sku="OIL-SUNFLOW-1L", tax_rate=Decimal("13.00"))
    variant = ProductVariant.objects.create(
        product=product,
        sku="OIL-SUNFLOW-1L-DEF",
        barcode="8901239876543",
        cost_price=Decimal("200.00"),
        selling_price=Decimal("250.00"),
        reorder_level=Decimal("10.00")
    )

    # Initial stock: 100 units in wh1
    StockMovement.record_movement(
        organization=org,
        warehouse=wh1,
        variant=variant,
        movement_type="PURCHASE",
        quantity=Decimal("100.000"),
        unit_cost=Decimal("200.00"),
        notes="Initial stock"
    )

    return {
        "user": user,
        "org": org,
        "branch": branch,
        "wh1": wh1,
        "wh2": wh2,
        "terminal": terminal,
        "product": product,
        "variant": variant,
    }


@pytest.mark.django_db
def test_cashier_shift_reconciliation(api_client, base_setup):
    """
    Verifies that cashier shift opening, sales cash accumulation, and shift closing
    reconciles expected cash against tendered sales and computes discrepancy.
    """
    user = base_setup["user"]
    org = base_setup["org"]
    terminal = base_setup["terminal"]
    branch = base_setup["branch"]
    variant = base_setup["variant"]

    # 1. Open shift with Rs. 2,000 opening cash
    shift = CashierShift.objects.create(
        organization=org,
        terminal=terminal,
        cashier=user,
        opening_cash=Decimal("2000.00"),
        status="OPEN"
    )

    # 2. Complete POS cash sale: 2 units @ Rs. 250 + 13% VAT = Rs. 565.00
    CheckoutService.process_checkout(
        organization=org,
        user=user,
        client_transaction_id="shift-tx-001",
        branch_id=str(branch.id),
        terminal_id=str(terminal.id),
        items=[{"variant_id": str(variant.id), "quantity": Decimal("2")}],
        payments=[{"method": "CASH", "amount": Decimal("565.00")}],
    )

    # 3. Close shift via API with Rs. 2,565 closing cash (exact match)
    api_client.force_authenticate(user=user)
    res = api_client.post(
        f"/api/v1/pos/shifts/{shift.id}/close/",
        {"closing_cash": "2565.00", "notes": "Shift ended smoothly"},
        HTTP_X_ORGANIZATION_ID=str(org.id)
    )

    assert res.status_code == 200
    shift.refresh_from_db()
    assert shift.status == "CLOSED"
    assert shift.expected_cash == Decimal("2565.00")
    assert shift.closing_cash == Decimal("2565.00")
    assert shift.discrepancy == Decimal("0.00")


@pytest.mark.django_db
def test_procurement_goods_receipt_stock_and_journal(base_setup):
    """
    Verifies that receiving goods against a Purchase Order:
    1. Changes PO status to RECEIVED.
    2. Records positive StockMovement.
    3. Increases StockBalance.
    4. Posts balanced double-entry accounting journal (Debit Inventory, Credit AP).
    """
    user = base_setup["user"]
    org = base_setup["org"]
    wh1 = base_setup["wh1"]
    variant = base_setup["variant"]

    supplier = Supplier.objects.create(organization=org, name="Kedia Agro Supplies", phone="9841000000")
    po = PurchaseOrder.objects.create(
        organization=org,
        supplier=supplier,
        warehouse=wh1,
        po_number="PO-2026-001",
        status="ORDERED",
        total_amount=Decimal("10000.00")
    )
    PurchaseOrderItem.objects.create(
        purchase_order=po,
        variant=variant,
        quantity=Decimal("50.000"),
        unit_cost=Decimal("200.00"),
        subtotal=Decimal("10000.00")
    )

    balance_before = StockBalance.objects.get(warehouse=wh1, variant=variant).quantity

    # Receive PO
    receipt = ProcurementService.receive_purchase_order(
        purchase_order=po,
        user=user,
        notes="Received in full at loading bay"
    )

    assert receipt is not None
    po.refresh_from_db()
    assert po.status == "RECEIVED"

    # Verify inventory balance updated (+50)
    balance_after = StockBalance.objects.get(warehouse=wh1, variant=variant).quantity
    assert balance_after == balance_before + Decimal("50.000")

    # Verify posted double-entry journal entry
    je = JournalEntry.objects.filter(reference_type="PurchaseOrder", reference_id=str(po.id)).first()
    assert je is not None
    assert je.status == "POSTED"
    lines = je.lines.all()
    assert sum(l.debit for l in lines) == sum(l.credit for l in lines) == Decimal("10000.00")


@pytest.mark.django_db
def test_stock_transfer_flow(api_client, base_setup):
    """
    Tests inter-warehouse transfer:
    WH1 (100) -> WH2 (0).
    Dispatch 30 units: WH1 (70), WH2 (0, in transit).
    Receive 30 units: WH1 (70), WH2 (30).
    """
    user = base_setup["user"]
    org = base_setup["org"]
    wh1 = base_setup["wh1"]
    wh2 = base_setup["wh2"]
    variant = base_setup["variant"]

    transfer = StockTransfer.objects.create(
        organization=org,
        source_warehouse=wh1,
        destination_warehouse=wh2,
        transfer_number="TRF-001",
        status="DRAFT"
    )
    StockTransferItem.objects.create(transfer=transfer, variant=variant, quantity=Decimal("30.000"))

    api_client.force_authenticate(user=user)

    # 1. Dispatch
    res_dispatch = api_client.post(
        f"/api/v1/inventory/transfers/{transfer.id}/dispatch/",
        HTTP_X_ORGANIZATION_ID=str(org.id)
    )
    assert res_dispatch.status_code == 200
    transfer.refresh_from_db()
    assert transfer.status == "IN_TRANSIT"

    # Check WH1 reduced to 70
    wh1_bal = StockBalance.objects.get(warehouse=wh1, variant=variant).quantity
    assert wh1_bal == Decimal("70.000")

    # 2. Receive
    res_receive = api_client.post(
        f"/api/v1/inventory/transfers/{transfer.id}/receive/",
        HTTP_X_ORGANIZATION_ID=str(org.id)
    )
    assert res_receive.status_code == 200
    transfer.refresh_from_db()
    assert transfer.status == "RECEIVED"

    # Check WH2 now has 30
    wh2_bal = StockBalance.objects.get(warehouse=wh2, variant=variant).quantity
    assert wh2_bal == Decimal("30.000")


@pytest.mark.django_db
def test_customer_khata_credit_limit_and_settlement(api_client, base_setup):
    """
    Tests:
    1. Credit purchase respects customer credit limit.
    2. Over-limit checkout is rejected.
    3. Khata debt settlement decreases current_credit and posts balanced journal.
    """
    user = base_setup["user"]
    org = base_setup["org"]
    branch = base_setup["branch"]
    variant = base_setup["variant"]

    customer = Customer.objects.create(
        organization=org,
        name="Ramesh Sharma",
        phone="9851000000",
        credit_limit=Decimal("5000.00"),
        current_credit=Decimal("0.00"),
    )

    # 1. Allowed credit sale (Rs. 1,130)
    # 4 units @ Rs. 250 + 13% VAT = Rs. 1,130.00
    sale_1 = CheckoutService.process_checkout(
        organization=org,
        user=user,
        client_transaction_id="khata-tx-001",
        branch_id=str(branch.id),
        customer_id=str(customer.id),
        items=[{"variant_id": str(variant.id), "quantity": Decimal("4")}],
        payments=[{"method": "CREDIT", "amount": Decimal("1130.00")}],
    )
    assert sale_1 is not None
    customer.refresh_from_db()
    assert customer.current_credit == Decimal("1130.00")

    # Check CreditTransaction created
    tx = CreditTransaction.objects.filter(customer=customer, transaction_type="INVOICE_DEBIT").first()
    assert tx is not None
    assert tx.amount == Decimal("1130.00")

    # 2. Over-limit credit sale: customer credit limit is 5,000.
    # Current debt is 1,130. Requesting another 4,500 would equal 5,630 (> 5,000). Must fail!
    with pytest.raises(ValidationError) as exc:
        CheckoutService.process_checkout(
            organization=org,
            user=user,
            client_transaction_id="khata-tx-002",
            branch_id=str(branch.id),
            customer_id=str(customer.id),
            items=[{"variant_id": str(variant.id), "quantity": Decimal("16")}],
            payments=[{"method": "CREDIT", "amount": Decimal("4520.00")}],
        )
    assert "Credit limit exceeded" in str(exc.value)

    # 3. Settle partial Khata debt: Rs. 1,000 via Cash
    api_client.force_authenticate(user=user)
    settle_res = api_client.post(
        f"/api/v1/customers/{customer.id}/settle-credit/",
        {"amount": "1000.00", "payment_method": "CASH", "notes": "Cash at counter"},
        HTTP_X_ORGANIZATION_ID=str(org.id)
    )
    assert settle_res.status_code == 200
    customer.refresh_from_db()
    assert customer.current_credit == Decimal("130.00")

    # Statement check
    stmt_res = api_client.get(
        f"/api/v1/customers/{customer.id}/statement/",
        HTTP_X_ORGANIZATION_ID=str(org.id)
    )
    assert stmt_res.status_code == 200
    assert stmt_res.data["current_debt"] == "130.00"
    assert len(stmt_res.data["transactions"]) == 2  # 1 purchase debit, 1 settlement credit


@pytest.mark.django_db
def test_thermal_receipt_generation(base_setup):
    """
    Tests formatting of 58mm/80mm ASCII receipts and binary ESC/POS byte sequence generation.
    """
    user = base_setup["user"]
    org = base_setup["org"]
    branch = base_setup["branch"]
    variant = base_setup["variant"]

    sale = CheckoutService.process_checkout(
        organization=org,
        user=user,
        client_transaction_id="receipt-tx-001",
        branch_id=str(branch.id),
        items=[{"variant_id": str(variant.id), "quantity": Decimal("2")}],
        payments=[{"method": "CASH", "amount": Decimal("565.00")}],
    )

    # Format ASCII
    ascii_text = ThermalReceiptGenerator.format_ascii_receipt(sale, width=42)
    assert "BIKASH SUPERMART" in ascii_text
    assert "PAN/VAT: 302918273" in ascii_text
    assert "Sunflow Sunflower Oil 1L" in ascii_text
    assert "VAT (13%):" in ascii_text
    assert "Rs. 565.00" in ascii_text

    # Generate ESC/POS bytes
    escpos_bytes = ThermalReceiptGenerator.generate_escpos_bytes(sale, width=42, open_drawer=True)
    assert escpos_bytes.startswith(b"\x1b@")  # ESC @ (Initialize)
    assert b"\x1dp\x00" in escpos_bytes or b"\x1bp\x00" in escpos_bytes  # Cash drawer kick
    assert b"\x1dVA\x00" in escpos_bytes  # Paper cut
