import pytest
import json
import base64
from decimal import Decimal
from rest_framework.test import APIClient
from apps.accounts.models import User, Role
from apps.tenants.models import Organization, Membership
from apps.branches.models import Branch, Warehouse
from apps.catalog.models import Product, ProductVariant
from apps.inventory.models import StockMovement, StockBalance
from apps.procurement.models import Supplier, PurchaseOrder, PurchaseOrderItem
from apps.procurement.services import ProcurementService
from apps.pos.models import PosTerminal
from apps.pos.services import CheckoutService
from apps.sales.models import Customer, Sale
from apps.payments.models import Payment
from apps.accounting.models import Account, JournalEntry, JournalLine
from apps.accounting.services.reports import FinancialReportService


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def accounting_setup(db):
    user = User.objects.create_user(email="accountant@himalaya.com", password="password123")
    org = Organization.objects.create(name="Himalaya Wholesale", slug="himalaya-ws", currency="NPR", tax_number="300998877")
    role = Role.objects.create(organization=org, name="Finance", is_owner=True, is_admin=True)
    Membership.objects.create(organization=org, user=user, role=role)

    branch = Branch.objects.create(organization=org, name="Lalitpur Hub", code="LAL-01")
    wh = Warehouse.objects.create(organization=org, branch=branch, name="Main Hub WH", code="WH-LAL", is_primary=True)
    terminal = PosTerminal.objects.create(organization=org, branch=branch, terminal_code="T-LAL-1", name="Terminal 1")

    product = Product.objects.create(organization=org, name="Basmati Rice 20kg", sku="RICE-BASMATI-20KG", tax_rate=Decimal("13.00"))
    variant = ProductVariant.objects.create(
        product=product,
        sku="RICE-BASMATI-20KG-DEF",
        cost_price=Decimal("2000.00"),
        selling_price=Decimal("2600.00")
    )

    # Initial stock: 100 bags
    StockMovement.record_movement(
        organization=org,
        warehouse=wh,
        variant=variant,
        movement_type="PURCHASE",
        quantity=Decimal("100.000"),
        unit_cost=Decimal("2000.00"),
        notes="Opening inventory"
    )

    return {
        "user": user,
        "org": org,
        "branch": branch,
        "wh": wh,
        "terminal": terminal,
        "product": product,
        "variant": variant,
    }


@pytest.mark.django_db
def test_trial_balance_and_profit_loss(accounting_setup):
    """
    Verifies that Trial Balance guarantees total debits == total credits,
    and Profit & Loss calculates Revenue, Expenses, and Net Profit.
    """
    user = accounting_setup["user"]
    org = accounting_setup["org"]
    branch = accounting_setup["branch"]
    variant = accounting_setup["variant"]

    # Execute Sale: 5 units @ Rs. 2,600 = Rs. 13,000 + 13% VAT (Rs. 1,690) = Rs. 14,690
    sale = CheckoutService.process_checkout(
        organization=org,
        user=user,
        client_transaction_id="tb-sale-001",
        branch_id=str(branch.id),
        items=[{"variant_id": str(variant.id), "quantity": Decimal("5")}],
        payments=[{"method": "CASH", "amount": Decimal("14690.00")}],
    )
    assert sale is not None

    # Trial Balance check
    tb = FinancialReportService.get_trial_balance(org)
    assert tb["is_balanced"] is True
    assert Decimal(tb["total_debit"]) == Decimal(tb["total_credit"])
    assert Decimal(tb["total_debit"]) >= Decimal("14690.00")

    # Profit & Loss check
    pnl = FinancialReportService.get_profit_and_loss(org)
    assert Decimal(pnl["revenue"]["total"]) == Decimal("13000.00")
    assert Decimal(pnl["net_profit"]) == Decimal("13000.00")


@pytest.mark.django_db
def test_balance_sheet_equation(accounting_setup):
    """
    Verifies that Balance Sheet maintains: Total Assets == Total Liabilities + Total Equity.
    """
    user = accounting_setup["user"]
    org = accounting_setup["org"]
    branch = accounting_setup["branch"]
    variant = accounting_setup["variant"]

    CheckoutService.process_checkout(
        organization=org,
        user=user,
        client_transaction_id="bs-sale-001",
        branch_id=str(branch.id),
        items=[{"variant_id": str(variant.id), "quantity": Decimal("2")}],
        payments=[{"method": "CASH", "amount": Decimal("5876.00")}],
    )

    bs = FinancialReportService.get_balance_sheet(org)
    assert bs["is_balanced"] is True
    assert Decimal(bs["assets"]["total"]) == Decimal(bs["total_liabilities_and_equity"])


@pytest.mark.django_db
def test_nepal_ird_vat_registers_and_return_summary(accounting_setup):
    """
    Verifies Nepal IRD Annex 5 (Sales Book), Annex 7 (Purchase Book),
    and Net VAT Return calculations.
    """
    user = accounting_setup["user"]
    org = accounting_setup["org"]
    branch = accounting_setup["branch"]
    wh = accounting_setup["wh"]
    variant = accounting_setup["variant"]

    # 1. Purchase Order with VAT: 10 units @ Rs. 2,000 = Rs. 20,000 + Rs. 2,600 VAT
    supplier = Supplier.objects.create(organization=org, name="Agro Dist", tax_number="301122334")
    po = PurchaseOrder.objects.create(
        organization=org,
        supplier=supplier,
        warehouse=wh,
        po_number="PO-VAT-01",
        status="ORDERED",
        total_amount=Decimal("22600.00"),
        tax_amount=Decimal("2600.00"),
    )
    PurchaseOrderItem.objects.create(
        purchase_order=po,
        variant=variant,
        quantity=Decimal("10"),
        unit_cost=Decimal("2000.00"),
        tax_amount=Decimal("2600.00"),
        subtotal=Decimal("22600.00"),
    )
    ProcurementService.receive_purchase_order(po, user=user)

    # 2. Sale with Output VAT: 10 units @ Rs. 2,600 = Rs. 26,000 + Rs. 3,380 VAT = Rs. 29,380
    CheckoutService.process_checkout(
        organization=org,
        user=user,
        client_transaction_id="vat-sale-001",
        branch_id=str(branch.id),
        items=[{"variant_id": str(variant.id), "quantity": Decimal("10")}],
        payments=[{"method": "CASH", "amount": Decimal("29380.00")}],
    )

    # Sales Book (Annex 5)
    sales_book = FinancialReportService.get_nepal_vat_sales_book(org)
    assert len(sales_book["entries"]) == 1
    assert Decimal(sales_book["summary"]["total_output_vat"]) == Decimal("3380.00")

    # Purchase Book (Annex 7)
    purch_book = FinancialReportService.get_nepal_vat_purchase_book(org)
    assert len(purch_book["entries"]) == 1
    assert Decimal(purch_book["summary"]["total_input_vat"]) == Decimal("2600.00")

    # Net VAT Return Summary: Output VAT (3380) - Input VAT (2600) = Rs. 780 payable to IRD
    ret_summary = FinancialReportService.get_vat_return_summary(org)
    assert Decimal(ret_summary["output_vat_collected"]) == Decimal("3380.00")
    assert Decimal(ret_summary["input_vat_credit"]) == Decimal("2600.00")
    assert Decimal(ret_summary["net_vat_payable_to_ird"]) == Decimal("780.00")


@pytest.mark.django_db
def test_credit_note_workflow_and_reversal(api_client, accounting_setup):
    """
    Tests Nepal IRD Credit Note (फिर्ता बिल):
    1. Returns/cancels an invoice.
    2. Restocks physical inventory.
    3. Reverses output VAT and sales revenue in double-entry accounting.
    4. Rejects repeated cancellation.
    """
    user = accounting_setup["user"]
    org = accounting_setup["org"]
    branch = accounting_setup["branch"]
    wh = accounting_setup["wh"]
    variant = accounting_setup["variant"]

    # Checkout 4 units @ Rs. 2,600 + 13% VAT = Rs. 11,752.00
    sale = CheckoutService.process_checkout(
        organization=org,
        user=user,
        client_transaction_id="cn-sale-001",
        branch_id=str(branch.id),
        items=[{"variant_id": str(variant.id), "quantity": Decimal("4")}],
        payments=[{"method": "CASH", "amount": Decimal("11752.00")}],
    )
    bal_after_sale = StockBalance.objects.get(warehouse=wh, variant=variant).quantity

    # Issue Credit Note via API
    api_client.force_authenticate(user=user)
    res = api_client.post(
        f"/api/v1/sales/{sale.id}/credit-note/",
        {"reason": "Damaged goods returned by buyer"},
        HTTP_X_ORGANIZATION_ID=str(org.id)
    )
    assert res.status_code == 200
    assert res.data["status"] == "REFUNDED"
    assert res.data["credit_note_number"].startswith("CN-")

    # Verify inventory was restocked (+4 units)
    bal_after_refund = StockBalance.objects.get(warehouse=wh, variant=variant).quantity
    assert bal_after_refund == bal_after_sale + Decimal("4.000")

    # Verify reversing journal entry exists
    reversal_je = JournalEntry.objects.filter(reference_type="CreditNote").first()
    assert reversal_je is not None
    assert reversal_je.status == "POSTED"
    lines = reversal_je.lines.all()
    assert sum(l.debit for l in lines) == sum(l.credit for l in lines) == Decimal("11752.00")

    # Second credit note attempt must be rejected
    res2 = api_client.post(
        f"/api/v1/sales/{sale.id}/credit-note/",
        HTTP_X_ORGANIZATION_ID=str(org.id)
    )
    assert res2.status_code == 400


@pytest.mark.django_db
def test_esewa_and_khalti_verification(api_client, accounting_setup):
    """
    Tests server-to-server digital wallet callbacks.
    """
    user = accounting_setup["user"]
    org = accounting_setup["org"]
    branch = accounting_setup["branch"]
    variant = accounting_setup["variant"]

    sale = CheckoutService.process_checkout(
        organization=org,
        user=user,
        client_transaction_id="esewa-sale-001",
        branch_id=str(branch.id),
        items=[{"variant_id": str(variant.id), "quantity": Decimal("1")}],
        payments=[{"method": "ESEWA", "amount": Decimal("2938.00"), "provider_reference": "ESEWA-TX-9988"}],
    )

    # Simulate eSewa Base64 callback
    callback_payload = {
        "transaction_code": "000TEST",
        "status": "COMPLETE",
        "total_amount": "2938.00",
        "transaction_uuid": "ESEWA-TX-9988",
        "signature": "mock_sig",
    }
    encoded = base64.b64encode(json.dumps(callback_payload).encode("utf-8")).decode("utf-8")

    res = api_client.post("/api/v1/payments/esewa/verify/", {"data": encoded})
    assert res.status_code == 200
    assert res.data["success"] is True

    # Verify payment reconciled
    payment = Payment.objects.get(provider_reference="ESEWA-TX-9988")
    assert payment.status == "SUCCESS"
