from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from apps.subscriptions.models import Subscription, SubscriptionInvoice


@shared_task(name="subscriptions.check_expirations")
def check_subscription_expirations():
    """
    Scans for active and trial subscriptions that have passed their end date.
    Auto-renews subscriptions with is_auto_renew=True or transitions them to EXPIRED.
    """
    now = timezone.now()
    expired_subs = Subscription.objects.filter(
        status__in=["TRIAL", "ACTIVE"],
        end_date__lt=now,
    ).select_related("plan", "organization")

    processed = 0
    renewed = 0

    for sub in expired_subs:
        processed += 1
        if sub.is_auto_renew and sub.plan:
            # Renew subscription for next cycle
            duration_days = 365 if sub.plan.billing_interval == "ANNUAL" else 30
            sub.start_date = now
            sub.end_date = now + timedelta(days=duration_days)
            sub.status = "ACTIVE"
            sub.save(update_fields=["start_date", "end_date", "status", "updated_at"])

            # Generate renewal invoice
            inv_number = f"REN-{now.year}{now.month:02d}-{sub.id.hex[:6].upper()}"
            SubscriptionInvoice.objects.create(
                subscription=sub,
                invoice_number=inv_number,
                amount=sub.plan.price_npr,
                status="PAID",
                paid_at=now,
                provider_transaction_id=f"AUTO-RENEW-{now.timestamp()}",
            )
            renewed += 1
        else:
            sub.status = "EXPIRED"
            sub.save(update_fields=["status", "updated_at"])

    return {
        "status": "completed",
        "processed_subscriptions": processed,
        "renewed_subscriptions": renewed,
        "timestamp": now.isoformat(),
    }
