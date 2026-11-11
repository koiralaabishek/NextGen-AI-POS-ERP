from decimal import Decimal
import pytest
from rest_framework.test import APIClient
from rest_framework import status

from apps.accounts.models import User
from apps.tenants.models import Organization, Membership
from apps.branches.models import Branch
from apps.catalog.models import Product, ProductVariant
from apps.restaurant.models import RestaurantTable, DiningOrder, KitchenOrder
from apps.wholesale.models import PriceTier, CustomerCreditLimit, CreditTransaction
from apps.sales.models import Customer
from apps.accounting.models import Account, JournalEntry


@pytest.fixture
def org_and_user(db):
    user = User.objects.create_user(
        email="manager@nepalbiz.np",
        password="securepassword123",
        first_name="Rajan",
        last_name="Khadka",
    )
    org = Organization.objects.create(
        name="Thamel Dine & Wholesale",
        slug="thamel-dine-wholesale",
        business_type="restaurant",
        country="NP",
        currency="NPR",
        tax_number="603334445",
    )
    Membership.objects.create(organization=org, user=user, is_active=True)
    branch = Branch.objects.create(organization=org, name="Thamel Branch", code="BR-THAMEL-01")

    # Chart of accounts
    Account.objects.create(organization=org, account_code="1010", account_name="Digital Wallets", account_type="ASSET")
    Account.objects.create(organization=org, account_code="1100", account_name="Accounts Receivable", account_type="ASSET")

    # Catalog
    prod = Product.objects.create(organization=org, sku="STEAM-MOMO", name="Chicken Steam Momo", tax_rate=Decimal("13.00"))
    variant = ProductVariant.objects.create(
        product=prod,
        sku="STEAM-MOMO-DEF",
        barcode="8907766554433",
        cost_price=Decimal("120.00"),
        selling_price=Decimal("250.00"),
        reorder_level=Decimal("10.00"),
    )
    return org, branch, user, variant


@pytest.fixture
def auth_client(org_and_user):
    org, branch, user, variant = org_and_user
    client = APIClient()
    client.force_authenticate(user=user)
    client.credentials(HTTP_X_ORGANIZATION_ID=str(org.id))
    return client


@pytest.mark.django_db
def test_restaurant_table_dining_and_kds_workflow(org_and_user, auth_client):
    """
    Validates Restaurant POS: Table occupancy, dining orders, KOT generation,
    KDS status progression (PENDING -> PREPARING -> READY -> SERVED), and bill splitting.
    """
    org, branch, user, variant = org_and_user

    # 1. Create Restaurant Table
    table = RestaurantTable.objects.create(
        organization=org,
        branch=branch,
        table_number="T-04",
        seating_capacity=4,
        status="AVAILABLE",
    )

    # 2. Occupy table via API
    res_occupy = auth_client.post(f"/api/v1/restaurant/tables/{table.id}/occupy/")
    assert res_occupy.status_code == status.HTTP_200_OK
    assert res_occupy.data["status"] == "OCCUPIED"

    # 3. Create Dining Order
    res_order = auth_client.post(
        "/api/v1/restaurant/orders/",
        {
            "branch": str(branch.id),
            "table": str(table.id),
            "guest_count": 3,
            "status": "OPEN",
        },
        format="json",
    )
    assert res_order.status_code == status.HTTP_201_CREATED
    order_id = res_order.data["id"]

    # 4. Generate Kitchen Order Ticket (KOT)
    res_kot = auth_client.post(
        f"/api/v1/restaurant/orders/{order_id}/create-kot/",
        {
            "items": [
                {
                    "variant_id": str(variant.id),
                    "quantity": "3.00",
                    "special_instructions": "Extra spicy spicy dipping chutney",
                }
            ]
        },
        format="json",
    )
    assert res_kot.status_code == status.HTTP_201_CREATED
    kot_id = res_kot.data["id"]
    assert res_kot.data["status"] == "PENDING"
    assert "KOT-T" in res_kot.data["kot_number"]

    # 5. Advance KDS Status: PENDING -> PREPARING -> READY
    res_adv1 = auth_client.post(f"/api/v1/restaurant/kitchen-orders/{kot_id}/advance-status/")
    assert res_adv1.status_code == status.HTTP_200_OK
    assert res_adv1.data["status"] == "PREPARING"

    res_adv2 = auth_client.post(f"/api/v1/restaurant/kitchen-orders/{kot_id}/advance-status/")
    assert res_adv2.status_code == status.HTTP_200_OK
    assert res_adv2.data["status"] == "READY"

    # 6. Split Bill for 3 guests
    res_split = auth_client.post(
        f"/api/v1/restaurant/orders/{order_id}/split-bill/",
        {"split_count": 3},
        format="json",
    )
    assert res_split.status_code == status.HTTP_200_OK
    # 3 momos * 250 = 750 / 3 guests = 250 per person
    assert res_split.data["total_bill_npr"] == "750.00"
    assert res_split.data["per_person_npr"] == "250.00"

    # 7. Release table after dining
    res_rel = auth_client.post(f"/api/v1/restaurant/tables/{table.id}/release/")
    assert res_rel.status_code == status.HTTP_200_OK
    assert res_rel.data["status"] == "AVAILABLE"


@pytest.mark.django_db
def test_wholesale_price_tiers_and_khata_settlement(org_and_user, auth_client):
    """
    Validates Wholesale POS: Volume discount tiers, customer credit limit management,
    and Khata debt settlement with double-entry journal posting.
    """
    org, branch, user, variant = org_and_user

    # 1. Create Volume Discount Tier
    res_tier = auth_client.post(
        "/api/v1/wholesale/price-tiers/",
        {
            "name": "Wholesale Bulk Tier B (50+ pcs)",
            "min_quantity": "50.00",
            "discount_percentage": "12.50",
        },
        format="json",
    )
    assert res_tier.status_code == status.HTTP_201_CREATED
    assert res_tier.data["discount_percentage"] == "12.50"

    # 2. Setup Wholesale Customer with Credit Limit
    customer = Customer.objects.create(
        organization=org,
        name="Lalitpur Traders Pvt. Ltd.",
        phone="9801998877",
        tax_number="601889900",
        credit_limit=Decimal("100000.00"),
        current_credit=Decimal("35000.00"),  # Rs. 35,000 outstanding debt
    )
    credit_limit_obj = CustomerCreditLimit.objects.create(
        organization=org,
        customer=customer,
        credit_limit=Decimal("100000.00"),
        grace_period_days=45,
        is_blocked=False,
    )

    # 3. Toggle Account Block
    res_block = auth_client.post(f"/api/v1/wholesale/credit-limits/{credit_limit_obj.id}/toggle-block/")
    assert res_block.status_code == status.HTTP_200_OK
    assert res_block.data["is_blocked"] is True

    # 4. Settle Rs. 15,000 Khata debt via eSewa
    res_settle = auth_client.post(
        "/api/v1/wholesale/credit/settle/",
        {
            "customer_id": str(customer.id),
            "amount": "15000.00",
            "payment_method": "ESEWA",
            "notes": "Bank transfer via eSewa merchant portal",
        },
        format="json",
    )
    assert res_settle.status_code == status.HTTP_200_OK
    data = res_settle.data
    assert data["settled_amount_npr"] == "15000.00"
    assert data["remaining_debt_npr"] == "20000.00"

    # Verify Customer model was updated
    customer.refresh_from_db()
    assert customer.current_credit == Decimal("20000.00")

    # Verify CreditTransaction audit record
    tx = CreditTransaction.objects.filter(customer=customer).first()
    assert tx is not None
    assert tx.transaction_type == "PAYMENT_CREDIT"
    assert tx.amount == Decimal("15000.00")
    assert tx.balance_after == Decimal("20000.00")

    # Verify Balanced Double-Entry Journal Entry
    je = JournalEntry.objects.get(entry_number=data["journal_entry"])
    assert je.status == "POSTED"
    lines = list(je.lines.all())
    assert len(lines) == 2
    # Total debits must equal total credits
    assert sum(l.debit for l in lines) == Decimal("15000.00")
    assert sum(l.credit for l in lines) == Decimal("15000.00")
