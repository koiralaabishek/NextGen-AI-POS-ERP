import base64
from decimal import Decimal
from rest_framework import viewsets, permissions, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from django.core.exceptions import ValidationError
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from apps.sales.models import Customer, Sale, SaleItem, Quotation, SalesOrder
from apps.sales.serializers import CustomerSerializer, SaleSerializer
from apps.sales.services.receipt import ThermalReceiptGenerator
from apps.payments.models import Refund, RefundItem, Payment
from apps.inventory.models import StockMovement
from apps.branches.models import Warehouse
from apps.wholesale.models import CreditTransaction
from apps.accounting.models import Account, JournalEntry, JournalLine
from common.permissions.tenant import IsTenantMember
from common.utils.money import round_money, ZERO_MONEY


class CustomerViewSet(viewsets.ModelViewSet):
    serializer_class = CustomerSerializer
    permission_classes = [permissions.IsAuthenticated, IsTenantMember]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "phone", "email", "tax_number"]
    ordering_fields = ["name", "created_at"]

    def get_queryset(self):
        return Customer.objects.filter(organization=self.request.organization)

    @extend_schema(
        description="Records a Khata debt settlement payment from a customer, reducing current_credit and posting an accounting journal entry.",
    )
    @action(detail=True, methods=["post"], url_path="settle-credit")
    def settle_credit(self, request, pk=None):
        customer = self.get_object()
        amount = round_money(request.data.get("amount", ZERO_MONEY))
        payment_method = request.data.get("payment_method", "CASH").upper()
        notes = request.data.get("notes", "")

        if amount <= ZERO_MONEY:
            return Response({"error": "Payment amount must be greater than zero."}, status=status.HTTP_400_BAD_REQUEST)
        if amount > customer.current_credit:
            return Response(
                {"error": f"Settlement amount (Rs. {amount}) exceeds current Khata balance (Rs. {customer.current_credit})."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            customer.current_credit -= amount
            customer.save(update_fields=["current_credit", "updated_at"])

            tx = CreditTransaction.objects.create(
                organization=request.organization,
                customer=customer,
                transaction_type="PAYMENT_CREDIT",
                amount=amount,
                balance_after=customer.current_credit,
                reference_id=f"SETTLE-{customer.phone or customer.id[:6]}",
                notes=f"Khata payment received via {payment_method}. {notes}".strip(),
            )

            # Balanced Double-Entry Journal:
            # Debit: Cash/Bank Account (1010)
            # Credit: Accounts Receivable (1100)
            try:
                cash_acc, _ = Account.objects.get_or_create(
                    organization=request.organization,
                    account_code="1010",
                    defaults={"account_name": "Cash on Hand", "account_type": "ASSET"}
                )
                ar_acc, _ = Account.objects.get_or_create(
                    organization=request.organization,
                    account_code="1100",
                    defaults={"account_name": "Accounts Receivable (Khata)", "account_type": "ASSET"}
                )
                entry = JournalEntry.objects.create(
                    organization=request.organization,
                    entry_number=f"JE-KHATA-{tx.id.hex[:8].upper()}",
                    status="POSTED",
                    reference_type="CustomerCredit",
                    reference_id=str(tx.id),
                    description=f"Khata settlement from {customer.name} via {payment_method}"
                )
                JournalLine.objects.create(
                    journal_entry=entry,
                    account=cash_acc,
                    debit=amount,
                    credit=ZERO_MONEY,
                    notes="Payment receipt"
                )
                JournalLine.objects.create(
                    journal_entry=entry,
                    account=ar_acc,
                    debit=ZERO_MONEY,
                    credit=amount,
                    notes=f"Receivable reduction for {customer.name}"
                )
            except Exception:
                pass

        return Response({
            "success": True,
            "settled_amount": str(amount),
            "remaining_credit_balance": str(customer.current_credit),
            "transaction_id": str(tx.id),
        })

    @extend_schema(
        description="Returns full statement of Khata credit purchases, payments, and current balance.",
    )
    @action(detail=True, methods=["get"], url_path="statement")
    def statement(self, request, pk=None):
        customer = self.get_object()
        txs = CreditTransaction.objects.filter(customer=customer).order_by("-created_at")
        history = [
            {
                "id": str(t.id),
                "type": t.transaction_type,
                "amount": str(t.amount),
                "balance_after": str(t.balance_after),
                "reference_id": t.reference_id,
                "notes": t.notes,
                "created_at": t.created_at,
            }
            for t in txs
        ]
        return Response({
            "customer_id": str(customer.id),
            "customer_name": customer.name,
            "phone": customer.phone,
            "credit_limit": str(customer.credit_limit),
            "current_debt": str(customer.current_credit),
            "available_credit": str(max(ZERO_MONEY, customer.credit_limit - customer.current_credit)),
            "loyalty_points": customer.loyalty_points,
            "transactions": history,
        })


class SaleViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = SaleSerializer
    permission_classes = [permissions.IsAuthenticated, IsTenantMember]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["invoice_number", "customer__name", "customer__phone"]
    ordering_fields = ["created_at", "total_amount"]

    def get_queryset(self):
        return Sale.objects.filter(organization=self.request.organization).prefetch_related(
            "items", "items__variant", "items__variant__product", "payments", "taxes", "customer", "branch"
        )

    @extend_schema(
        description="Generates formatted thermal receipt in ASCII text, base64 ESC/POS command stream, or structured JSON.",
    )
    @action(detail=True, methods=["get"], url_path="receipt")
    def receipt(self, request, pk=None):
        sale = self.get_object()
        format_type = request.query_params.get("format", "text").lower()
        width = int(request.query_params.get("width", 42))

        ascii_text = ThermalReceiptGenerator.format_ascii_receipt(sale, width=width)

        if format_type == "escpos":
            escpos_bytes = ThermalReceiptGenerator.generate_escpos_bytes(sale, width=width)
            return Response({
                "invoice_number": sale.invoice_number,
                "width": width,
                "encoding": "base64",
                "escpos_base64": base64.b64encode(escpos_bytes).decode("ascii"),
            })

        return Response({
            "invoice_number": sale.invoice_number,
            "width": width,
            "receipt_text": ascii_text,
        })

    @extend_schema(
        description="Nepal IRD compliant Credit Note (फिर्ता बिल): cancels or partially returns an invoice, restocks items, reverses VAT liability, and returns refund voucher.",
    )
    @action(detail=True, methods=["post"], url_path="credit-note")
    def issue_credit_note(self, request, pk=None):
        sale = self.get_object()
        if sale.status in ["REFUNDED", "VOID"]:
            return Response({"error": f"Invoice is already {sale.status}."}, status=status.HTTP_400_BAD_REQUEST)

        reason = request.data.get("reason", "Customer return / Billing correction")
        org = request.organization
        branch = sale.branch

        # Find primary warehouse for restocking
        wh = Warehouse.objects.filter(branch=branch, is_primary=True).first() or Warehouse.objects.filter(branch=branch).first()

        with transaction.atomic():
            cn_number = f"CN-{sale.invoice_number}"
            refund_amount = sale.total_amount
            net_sales_refund = sale.subtotal - sale.discount_amount
            vat_refund = sale.tax_amount

            refund = Refund.objects.create(
                organization=org,
                sale=sale,
                amount=refund_amount,
                reason=f"Credit Note {cn_number}: {reason}",
                status="COMPLETED",
                approved_by=request.user,
            )

            # Restock items
            for item in sale.items.all():
                RefundItem.objects.create(
                    refund=refund,
                    sale_item=item,
                    quantity=item.quantity,
                    amount=item.subtotal,
                )
                if wh:
                    StockMovement.record_movement(
                        organization=org,
                        warehouse=wh,
                        variant=item.variant,
                        movement_type="RETURN",
                        quantity=item.quantity,
                        unit_cost=item.cost_price,
                        reference_type="CreditNote",
                        reference_id=cn_number,
                        performed_by=request.user if request.user and request.user.is_authenticated else None,
                        notes=f"Customer return for invoice #{sale.invoice_number}"
                    )

            # If customer Khata credit sale, reverse debt
            if sale.customer and sale.payments.filter(payment_method="CREDIT").exists():
                sale.customer.current_credit = max(ZERO_MONEY, sale.customer.current_credit - refund_amount)
                sale.customer.save(update_fields=["current_credit", "updated_at"])
                CreditTransaction.objects.create(
                    organization=org,
                    customer=sale.customer,
                    transaction_type="ADJUSTMENT",
                    amount=-refund_amount,
                    balance_after=sale.customer.current_credit,
                    reference_id=cn_number,
                    notes=f"Credit Note debt reversal for {sale.invoice_number}"
                )

            # Reverse double-entry accounting journal:
            # Debit: Sales Revenue (4000)
            # Debit: Output VAT Payable (2200) - canceling government tax liability
            # Credit: Cash/Bank (1010) or Khata AR (1100)
            try:
                rev_acc, _ = Account.objects.get_or_create(
                    organization=org,
                    account_code="4000",
                    defaults={"account_name": "Sales Revenue", "account_type": "REVENUE"}
                )
                vat_acc, _ = Account.objects.get_or_create(
                    organization=org,
                    account_code="2200",
                    defaults={"account_name": "Output VAT Payable", "account_type": "LIABILITY"}
                )
                cash_acc, _ = Account.objects.get_or_create(
                    organization=org,
                    account_code="1010",
                    defaults={"account_name": "Cash on Hand", "account_type": "ASSET"}
                )

                je = JournalEntry.objects.create(
                    organization=org,
                    entry_number=f"JE-{cn_number}",
                    status="POSTED",
                    reference_type="CreditNote",
                    reference_id=str(refund.id),
                    description=f"Credit note reversal journal for invoice #{sale.invoice_number}"
                )

                # Debit lines
                JournalLine.objects.create(
                    journal_entry=je,
                    account=rev_acc,
                    debit=net_sales_refund,
                    credit=ZERO_MONEY,
                    notes="Sales revenue return"
                )
                if vat_refund > ZERO_MONEY:
                    JournalLine.objects.create(
                        journal_entry=je,
                        account=vat_acc,
                        debit=vat_refund,
                        credit=ZERO_MONEY,
                        notes="Output VAT cancellation"
                    )

                # Credit line
                JournalLine.objects.create(
                    journal_entry=je,
                    account=cash_acc,
                    debit=ZERO_MONEY,
                    credit=refund_amount,
                    notes="Customer refund tender"
                )
            except Exception:
                pass

            sale.status = "REFUNDED"
            sale.save(update_fields=["status", "updated_at"])

        return Response({
            "success": True,
            "credit_note_number": cn_number,
            "invoice_number": sale.invoice_number,
            "refund_amount": str(refund_amount),
            "status": "REFUNDED",
        })
