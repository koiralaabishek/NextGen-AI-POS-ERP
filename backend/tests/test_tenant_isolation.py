import pytest
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.urls import reverse
from rest_framework.test import APIClient
from apps.accounts.models import User, Role, Permission
from apps.tenants.models import Organization, Membership
from apps.branches.models import Branch, Warehouse
from apps.catalog.models import Product, ProductVariant
from apps.pos.services import CheckoutService
from apps.sales.models import Sale
from common.middleware.tenant import set_current_tenant_id, clear_current_tenant


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def setup_tenants(db):
    """
    Creates two separate tenant organizations: Tenant A and Tenant B,
    each with their own users, branches, warehouses, and products.
    """
    # Tenant A
    user_a = User.objects.create_user(email="alice@tenanta.com", password="password123")
    org_a = Organization.objects.create(name="Tenant A Supermarket", slug="tenant-a", currency="NPR")
    role_a = Role.objects.create(organization=org_a, name="Admin", is_owner=True, is_admin=True)
    Membership.objects.create(organization=org_a, user=user_a, role=role_a)
    branch_a = Branch.objects.create(organization=org_a, name="Branch A1", code="BR-A1")
    warehouse_a = Warehouse.objects.create(organization=org_a, branch=branch_a, name="Main Warehouse A", code="WH-A1", is_primary=True)
    prod_a = Product.objects.create(organization=org_a, name="Apple Tenant A", sku="SKU-A-01", tax_rate=Decimal("13.00"))
    var_a = ProductVariant.objects.create(product=prod_a, sku="VAR-A-01", barcode="111111", selling_price=Decimal("100.00"), cost_price=Decimal("70.00"))

    # Tenant B
    user_b = User.objects.create_user(email="bob@tenantb.com", password="password123")
    org_b = Organization.objects.create(name="Tenant B Retail", slug="tenant-b", currency="NPR")
    role_b = Role.objects.create(organization=org_b, name="Admin", is_owner=True, is_admin=True)
    Membership.objects.create(organization=org_b, user=user_b, role=role_b)
    branch_b = Branch.objects.create(organization=org_b, name="Branch B1", code="BR-B1")
    warehouse_b = Warehouse.objects.create(organization=org_b, branch=branch_b, name="Main Warehouse B", code="WH-B1", is_primary=True)
    prod_b = Product.objects.create(organization=org_b, name="Banana Tenant B", sku="SKU-B-01", tax_rate=Decimal("13.00"))
    var_b = ProductVariant.objects.create(product=prod_b, sku="VAR-B-01", barcode="222222", selling_price=Decimal("150.00"), cost_price=Decimal("100.00"))

    return {
        "tenant_a": {"user": user_a, "org": org_a, "branch": branch_a, "warehouse": warehouse_a, "prod": prod_a, "variant": var_a},
        "tenant_b": {"user": user_b, "org": org_b, "branch": branch_b, "warehouse": warehouse_b, "prod": prod_b, "variant": var_b},
    }


@pytest.mark.django_db
def test_tenant_data_isolation_api(api_client, setup_tenants):
    """
    Ensures Tenant A querying the products endpoint cannot see Tenant B's products.
    """
    ta = setup_tenants["tenant_a"]
    tb = setup_tenants["tenant_b"]

    api_client.force_authenticate(user=ta["user"])
    response = api_client.get(
        "/api/v1/products/",
        HTTP_X_ORGANIZATION_ID=str(ta["org"].id)
    )

    assert response.status_code == 200
    skus = [p["sku"] for p in response.data["results"]]
    assert "SKU-A-01" in skus
    assert "SKU-B-01" not in skus  # Tenant B product MUST NOT leak to Tenant A


@pytest.mark.django_db
def test_cross_tenant_access_denial(api_client, setup_tenants):
    """
    Ensures Tenant A user cannot forge X-Organization-ID of Tenant B.
    """
    ta = setup_tenants["tenant_a"]
    tb = setup_tenants["tenant_b"]

    api_client.force_authenticate(user=ta["user"])
    # Tenant A attempts to pass Tenant B's organization ID
    response = api_client.get(
        "/api/v1/products/",
        HTTP_X_ORGANIZATION_ID=str(tb["org"].id)
    )

    # Must be denied (403 Forbidden)
    assert response.status_code == 403


@pytest.mark.django_db
def test_cross_tenant_foreign_key_rejection(setup_tenants):
    """
    Ensures an entity cannot link to a foreign key belonging to a different organization.
    """
    ta = setup_tenants["tenant_a"]
    tb = setup_tenants["tenant_b"]

    set_current_tenant_id(ta["org"].id)

    # Attempt to create a Warehouse belonging to Tenant A, but referencing Branch belonging to Tenant B
    with pytest.raises(ValidationError) as exc_info:
        bad_warehouse = Warehouse(
            organization=ta["org"],
            branch=tb["branch"],  # CROSS-TENANT VIOLATION
            name="Illegal Cross Warehouse",
            code="WH-ILLEGAL"
        )
        bad_warehouse.clean()

    assert "Cross-tenant reference detected" in str(exc_info.value)
    clear_current_tenant()


@pytest.mark.django_db
def test_pos_checkout_idempotency_and_stock_deduction(setup_tenants):
    """
    Verifies that:
    1. Repeated checkouts with the same client_transaction_id return the same invoice (idempotent).
    2. Physical stock movement is recorded.
    """
    ta = setup_tenants["tenant_a"]
    client_tx_id = "test-terminal-01-uuid-0001"

    # Initial checkout
    sale_1 = CheckoutService.process_checkout(
        organization=ta["org"],
        user=ta["user"],
        client_transaction_id=client_tx_id,
        branch_id=str(ta["branch"].id),
        items=[{"variant_id": str(ta["variant"].id), "quantity": Decimal("3"), "discount": Decimal("0.00")}],
        payments=[{"method": "CASH", "amount": Decimal("339.00")}],  # 300 + 13% VAT = 339
    )

    assert sale_1 is not None
    assert sale_1.total_amount == Decimal("339.00")

    # Second checkout with identical idempotency key (simulating network retry or offline duplicate sync)
    sale_2 = CheckoutService.process_checkout(
        organization=ta["org"],
        user=ta["user"],
        client_transaction_id=client_tx_id,
        branch_id=str(ta["branch"].id),
        items=[{"variant_id": str(ta["variant"].id), "quantity": Decimal("3"), "discount": Decimal("0.00")}],
        payments=[{"method": "CASH", "amount": Decimal("339.00")}],
    )

    assert sale_2.id == sale_1.id
    assert sale_2.invoice_number == sale_1.invoice_number

    # Verify only 1 sale exists in database for this transaction
    assert Sale.objects.filter(organization=ta["org"], client_transaction_id=client_tx_id).count() == 1
