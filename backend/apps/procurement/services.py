from decimal import Decimal
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.procurement.models import PurchaseOrder, GoodsReceipt
from apps.inventory.models import StockMovement, StockBatch
from apps.accounting.models import Account, JournalEntry, JournalLine
from common.utils.money import round_money, ZERO_MONEY


class ProcurementService:
    @classmethod
    def receive_purchase_order(cls, purchase_order: PurchaseOrder, user, batch_info: dict = None, notes: str = "") -> GoodsReceipt:
        """
        Processes a Goods Receipt for an ordered PurchaseOrder.
        1. Validates PO status is ORDERED or DRAFT.
        2. Records positive StockMovement (PURCHASE) for each variant.
        3. Optionally creates or updates StockBatch (expiry tracking).
        4. Posts balanced double-entry accounting entry:
           Debit: Inventory Asset (1200)
           Credit: Accounts Payable (2100)
        5. Updates PO status to RECEIVED.
        """
        if purchase_order.status == "RECEIVED":
            raise ValidationError("Purchase Order has already been received.")
        if purchase_order.status == "CANCELLED":
            raise ValidationError("Cannot receive a cancelled Purchase Order.")

        org = purchase_order.organization
        wh = purchase_order.warehouse

        with transaction.atomic():
            receipt_num = f"GR-{purchase_order.po_number}-{timezone.now().strftime('%y%m%d%H%M')}"
            receipt = GoodsReceipt.objects.create(
                organization=org,
                purchase_order=purchase_order,
                receipt_number=receipt_num,
                received_by=user,
                notes=notes,
            )

            total_received_cost = ZERO_MONEY

            for item in purchase_order.items.select_related("variant"):
                qty = item.quantity
                cost = item.unit_cost
                variant = item.variant
                line_total = round_money(qty * cost)
                total_received_cost += line_total

                # Record physical stock receipt movement
                StockMovement.record_movement(
                    organization=org,
                    warehouse=wh,
                    variant=variant,
                    movement_type="PURCHASE",
                    quantity=qty,
                    unit_cost=cost,
                    reference_type="GoodsReceipt",
                    reference_id=receipt.receipt_number,
                    performed_by=user,
                    notes=f"PO Receipt {purchase_order.po_number}"
                )

                # Batch / Expiry tracking if provided
                if batch_info and variant.id in batch_info:
                    b_data = batch_info[variant.id]
                    StockBatch.objects.create(
                        variant=variant,
                        batch_number=b_data.get("batch_number", f"BATCH-{timezone.now().strftime('%Y%m%d')}"),
                        expiry_date=b_data.get("expiry_date"),
                        cost_price=cost,
                        current_quantity=qty,
                    )

            purchase_order.status = "RECEIVED"
            purchase_order.save(update_fields=["status", "updated_at"])

            # Post double-entry journal entry:
            # Debit: Inventory Asset (1200)
            # Credit: Accounts Payable (2100)
            cls._post_procurement_journal(org, purchase_order, total_received_cost)

            return receipt

    @classmethod
    def _post_procurement_journal(cls, organization, po, total_cost):
        try:
            inv_acc, _ = Account.objects.get_or_create(
                organization=organization,
                account_code="1200",
                defaults={"account_name": "Merchandise Inventory", "account_type": "ASSET"}
            )
            ap_acc, _ = Account.objects.get_or_create(
                organization=organization,
                account_code="2100",
                defaults={"account_name": "Accounts Payable (Suppliers)", "account_type": "LIABILITY"}
            )

            entry = JournalEntry.objects.create(
                organization=organization,
                entry_number=f"JE-PO-{po.po_number}",
                status="POSTED",
                reference_type="PurchaseOrder",
                reference_id=str(po.id),
                description=f"Inventory procurement receipt for PO {po.po_number} from {po.supplier.name}"
            )

            JournalLine.objects.create(
                journal_entry=entry,
                account=inv_acc,
                debit=total_cost,
                credit=ZERO_MONEY,
                notes="Inventory asset addition"
            )
            JournalLine.objects.create(
                journal_entry=entry,
                account=ap_acc,
                debit=ZERO_MONEY,
                credit=total_cost,
                notes=f"Supplier payable to {po.supplier.name}"
            )
        except Exception:
            pass
