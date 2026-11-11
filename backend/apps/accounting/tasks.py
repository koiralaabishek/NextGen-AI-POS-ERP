from decimal import Decimal
from celery import shared_task
from django.utils import timezone
from django.db.models import Sum
from apps.sales.models import Sale
from apps.accounting.models import JournalLine, Account
from apps.tenants.models import Organization, AuditLog


@shared_task(name="accounting.reconcile_daily_vat")
def reconcile_daily_vat_and_sales(target_date_str=None):
    """
    Automated daily audit reconciling POS sales invoices against double-entry journal postings.
    Asserts: Sum(Sale.tax_amount) == Sum(JournalLine.credit on Account 2200 Output VAT).
    """
    if target_date_str:
        target_date = timezone.datetime.fromisoformat(target_date_str).date()
    else:
        target_date = timezone.now().date()

    results = []
    organizations = Organization.objects.filter(is_active=True)

    for org in organizations:
        sales_vat = Sale.objects.filter(
            organization=org,
            status="COMPLETED",
            created_at__date=target_date,
        ).aggregate(total=Sum("tax_amount"))["total"] or Decimal("0.00")

        ledger_vat = JournalLine.objects.filter(
            journal_entry__organization=org,
            journal_entry__entry_date=target_date,
            account__account_code="2200",
        ).aggregate(total=Sum("credit"))["total"] or Decimal("0.00")

        discrepancy = abs(sales_vat - ledger_vat)
        is_reconciled = discrepancy < Decimal("0.01")

        if not is_reconciled:
            AuditLog.objects.create(
                organization=org,
                action="VAT_RECONCILIATION_DISCREPANCY",
                entity_type="Account",
                entity_id=org.id,
                payload_snapshot={
                    "date": str(target_date),
                    "sales_vat": str(sales_vat),
                    "ledger_vat": str(ledger_vat),
                    "discrepancy": str(discrepancy),
                },
            )

        results.append({
            "organization_id": str(org.id),
            "date": str(target_date),
            "sales_vat": str(sales_vat),
            "ledger_vat": str(ledger_vat),
            "is_reconciled": is_reconciled,
        })

    return results
