import os
import sys
from decimal import Decimal
from datetime import timedelta
import pytest
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status

from apps.accounts.models import User
from apps.tenants.models import Organization, Membership
from apps.subscriptions.models import Plan, PlanFeature, Subscription, SubscriptionInvoice
from apps.subscriptions.services import FeatureEntitlementService

# Add ai-service to sys.path so we can test the AI service directly with TestClient
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../ai-service")))
from fastapi.testclient import TestClient
from app.main import app as ai_fastapi_app


@pytest.fixture
def org_and_user(db):
    user = User.objects.create_user(
        email="founder@mart.np",
        password="securepassword123",
        first_name="Suman",
        last_name="Shrestha",
    )
    org = Organization.objects.create(
        name="Namaste Mart SaaS",
        slug="namaste-mart-saas",
        business_type="supermarket",
        country="NP",
        currency="NPR",
        tax_number="601234567",
    )
    Membership.objects.create(organization=org, user=user, is_active=True)
    return org, user


@pytest.fixture
def api_client(org_and_user):
    org, user = org_and_user
    client = APIClient()
    client.force_authenticate(user=user)
    client.credentials(HTTP_X_ORGANIZATION_ID=str(org.id))
    return client


@pytest.mark.django_db
def test_saas_plan_entitlements_and_limits(org_and_user, api_client):
    """
    Validates SaaS subscription entitlements, feature limits, and plan upgrade workflows.
    """
    org, user = org_and_user

    # 1. Setup Starter and Enterprise plans
    starter_plan = Plan.objects.create(
        name="Starter Plan",
        slug="starter-plan",
        price_npr=Decimal("2500.00"),
        billing_interval="MONTHLY",
        max_branches=1,
        max_users=2,
        ai_monthly_credits=50,
    )
    PlanFeature.objects.create(
        plan=starter_plan,
        feature_code="pos.enabled",
        feature_name="POS Checkout",
        is_enabled=True,
    )
    PlanFeature.objects.create(
        plan=starter_plan,
        feature_code="branches.limit",
        feature_name="Branch Quota",
        is_enabled=True,
        limit_value=1,
    )

    enterprise_plan = Plan.objects.create(
        name="Enterprise Plan",
        slug="enterprise-plan",
        price_npr=Decimal("15000.00"),
        billing_interval="MONTHLY",
        max_branches=10,
        max_users=25,
        ai_monthly_credits=1000,
    )
    PlanFeature.objects.create(
        plan=enterprise_plan,
        feature_code="pos.enabled",
        feature_name="POS Checkout",
        is_enabled=True,
    )
    PlanFeature.objects.create(
        plan=enterprise_plan,
        feature_code="ai.copilot",
        feature_name="AI Copilot & Demand Forecasting",
        is_enabled=True,
    )
    PlanFeature.objects.create(
        plan=enterprise_plan,
        feature_code="branches.limit",
        feature_name="Branch Quota",
        is_enabled=True,
        limit_value=10,
    )

    # 2. Assign initial Starter Subscription
    now = timezone.now()
    sub = Subscription.objects.create(
        organization=org,
        plan=starter_plan,
        status="ACTIVE",
        start_date=now,
        end_date=now + timedelta(days=30),
    )

    # Check entitlements
    assert FeatureEntitlementService.has_feature(org, "pos.enabled") is True
    assert FeatureEntitlementService.has_feature(org, "ai.copilot") is False
    assert FeatureEntitlementService.get_feature_limit(org, "branches.limit") == 1

    # 3. Upgrade to Enterprise Plan via API
    res = api_client.post(
        "/api/v1/subscriptions/upgrade/",
        {
            "plan_id": str(enterprise_plan.id),
            "billing_interval": "MONTHLY",
        },
        format="json",
    )
    assert res.status_code == status.HTTP_200_OK
    data = res.data
    assert data["status"] == "ACTIVE"
    assert str(data["plan"]) == str(enterprise_plan.id)

    # Verify previous subscription is expired
    sub.refresh_from_db()
    assert sub.status == "EXPIRED"

    # Verify new entitlements after upgrade
    assert FeatureEntitlementService.has_feature(org, "ai.copilot") is True
    assert FeatureEntitlementService.get_feature_limit(org, "branches.limit") == 10

    # Verify invoice was created and paid
    invoice = SubscriptionInvoice.objects.filter(subscription_id=data["id"]).first()
    assert invoice is not None
    assert invoice.status == "PAID"
    assert invoice.amount == enterprise_plan.price_npr


def test_ai_service_demand_forecasting_and_recommendations():
    """
    Tests the FastAPI AI Intelligence microservice for statistical forecasting,
    market-basket recommendations, and multi-lingual business copilot.
    """
    client = TestClient(ai_fastapi_app)

    # 1. Health check
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json()["status"] == "ok"

    # 2. Demand Forecast (Holt's Linear Trend)
    history = [12.0, 15.0, 14.0, 18.0, 22.0, 25.0, 28.0]  # Upward trending sales
    forecast_req = {
        "variant_id": "v-flour-5kg",
        "branch_id": "branch-ktm-01",
        "historical_sales": history,
        "forecast_days": 7,
        "model_type": "holt_winters_trend",
    }
    res = client.post(
        "/v1/forecast",
        json=forecast_req,
        headers={"x-organization-id": "org-test-01"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["variant_id"] == "v-flour-5kg"
    assert len(data["daily_predictions"]) == 7
    assert data["trend_direction"] == "INCREASING"
    assert data["confidence_interval"]["lower"] <= data["projected_total_units"]
    assert data["confidence_interval"]["upper"] >= data["projected_total_units"]

    # 3. Cross-sell Basket Recommendations
    rec_req = {
        "cart_variant_ids": ["WHT-FLOUR-5KG-DEF"],
        "organization_id": "org-test-01",
        "limit": 2,
    }
    res = client.post(
        "/v1/recommendations",
        json=rec_req,
        headers={"x-organization-id": "org-test-01"},
    )
    assert res.status_code == 200
    recs = res.json()["recommendations"]
    assert len(recs) == 2
    assert recs[0]["variant_id"] == "MUSTARD-OIL-1L-DEF"
    assert recs[0]["confidence_score"] >= 0.8

    # 4. Multi-lingual AI Copilot (Nepali query)
    res_ne = client.post(
        "/v1/assistant",
        json={
            "user_query": "मेरो पसलमा आज सबैभन्दा बढी नाफा भएको सामान कुन हो?",
            "organization_id": "org-test-01",
            "language": "ne",
        },
        headers={"x-organization-id": "org-test-01"},
    )
    assert res_ne.status_code == 200
    assert "नाफा" in res_ne.json()["answer"]
    assert "Shakti Wheat Flour" in res_ne.json()["answer"]
    assert "get_profit_summary" in res_ne.json()["tools_executed"]

    # 5. Multi-lingual AI Copilot (English query)
    res_en = client.post(
        "/v1/assistant",
        json={
            "user_query": "What is our current monthly Nepal VAT liability?",
            "organization_id": "org-test-01",
            "language": "en",
        },
        headers={"x-organization-id": "org-test-01"},
    )
    assert res_en.status_code == 200
    assert "28,600" in res_en.json()["answer"]
    assert "get_vat_return_summary" in res_en.json()["tools_executed"]
