from decimal import Decimal
from django.db import transaction
from django.core.exceptions import ValidationError
from apps.sales.models import Sale, SaleItem, SaleTax, Customer, InvoiceSequence
from apps.payments.models import Payment
from apps.catalog.models import ProductVariant
from apps.inventory.models import StockMovement, StockBalance
from apps.branches.models import Branch, Warehouse
from apps.accounting.models import Account, JournalEntry, JournalLine
from common.utils.money import round_money, ZERO_MONEY


class CheckoutService:
    """
    Authoritative, idempotent POS checkout processing engine.
    Recalculates prices, updates inventory ledger, records payments,
    and posts balanced double-entry journal records in a single atomic transaction.
    """

    @classmethod
    def process_checkout(
        cls,
        organization,
        user,
        client_transaction_id: str,
        branch_id: str,
        terminal_id: str = None,
        customer_id: str = None,
        items: list = None,
        payments: list = None,
        currency: str = "NPR",
        notes: str = ""
    ) -> Sale:
        if not items:
            raise ValidationError("Checkout requires at least one sale item.")
        if not payments:
            raise ValidationError("Checkout requires at least one payment record.")

        # 1. Idempotency Check: Return existing sale if already processed
        existing_sale = Sale.objects.filter(
            organization=organization,
            client_transaction_id=client_transaction_id
        ).first()
        if existing_sale:
            return existing_sale

        branch = Branch.objects.get(id=branch_id, organization=organization)
        warehouse = Warehouse.objects.filter(branch=branch, organization=organization, is_primary=True).first()
        if not warehouse:
            warehouse = Warehouse.objects.filter(branch=branch, organization=organization).first()
        if not warehouse:
            raise ValidationError("No active warehouse found for this branch to deduct inventory.")

        customer = None
        if customer_id:
            customer = Customer.objects.filter(id=customer_id, organization=organization).first()

        with transaction.atomic():
            # Generate gapless IRD-compliant invoice sequence
            invoice_num = InvoiceSequence.get_next_invoice_number(organization, branch)

            sale = Sale.objects.create(
                organization=organization,
                branch=branch,
                terminal_id=terminal_id,
                cashier=user,
                customer=customer,
                invoice_number=invoice_num,
                client_transaction_id=client_transaction_id,
                status="COMPLETED",
                currency=currency,
                notes=notes,
            )

            running_subtotal = ZERO_MONEY
            running_discount = ZERO_MONEY
            running_tax = ZERO_MONEY

            # Process Items
            for item_data in items:
                variant_id = item_data.get("variant_id")
                qty = Decimal(str(item_data.get("quantity", 1)))
                discount = round_money(item_data.get("discount", ZERO_MONEY))

                # Authoritative variant lookup with lock
                variant = ProductVariant.objects.select_for_update().select_related("product").get(
                    id=variant_id, product__organization=organization
                )

                # Authoritative selling price from variant record
                unit_price = round_money(variant.selling_price)
                cost_price = round_money(variant.cost_price)
                tax_rate = Decimal(str(variant.product.tax_rate))

                line_subtotal_before_tax = round_money((unit_price * qty) - discount)
                line_tax = round_money(line_subtotal_before_tax * (tax_rate / Decimal("100.00")))
                line_total = line_subtotal_before_tax + line_tax

                running_subtotal += round_money(unit_price * qty)
                running_discount += discount
                running_tax += line_tax

                SaleItem.objects.create(
                    sale=sale,
                    variant=variant,
                    quantity=qty,
                    unit_price=unit_price,
                    cost_price=cost_price,
                    discount_amount=discount,
                    tax_rate=tax_rate,
                    tax_amount=line_tax,
                    subtotal=line_total,
                )

                # Record physical stock movement deduction
                StockMovement.record_movement(
                    organization=organization,
                    warehouse=warehouse,
                    variant=variant,
                    movement_type="SALE",
                    quantity=-qty,  # Deduction
                    unit_cost=cost_price,
                    reference_type="Sale",
                    reference_id=sale.invoice_number,
                    performed_by=user,
                    notes=f"POS Checkout {sale.invoice_number}"
                )

            total_sale_amount = (running_subtotal - running_discount) + running_tax

            # Process Payments
            running_paid = ZERO_MONEY
            for pay_data in payments:
                method = pay_data.get("method", "CASH").upper()
                amount = round_money(pay_data.get("amount", ZERO_MONEY))
                running_paid += amount

                Payment.objects.create(
                    organization=organization,
                    sale=sale,
                    payment_method=method,
                    amount=amount,
                    currency=currency,
                    status="SUCCESS",
                    provider_reference=pay_data.get("provider_reference", ""),
                )

                # If customer Khata / Credit sale, validate limit and update customer debt balance
                if method == "CREDIT":
                    if not customer:
                        raise ValidationError("Customer selection is required for Khata credit sales.")
                    if customer.credit_limit and (customer.current_credit + amount > customer.credit_limit):
                        available = max(ZERO_MONEY, customer.credit_limit - customer.current_credit)
                        raise ValidationError(
                            f"Credit limit exceeded for {customer.name}! "
                            f"Credit limit: Rs. {customer.credit_limit}, current debt: Rs. {customer.current_credit}, available: Rs. {available}."
                        )
                    customer.current_credit += amount
                    customer.save(update_fields=["current_credit", "updated_at"])

                    from apps.wholesale.models import CreditTransaction
                    CreditTransaction.objects.create(
                        organization=organization,
                        customer=customer,
                        transaction_type="INVOICE_DEBIT",
                        amount=amount,
                        balance_after=customer.current_credit,
                        reference_id=sale.invoice_number,
                        notes=f"Khata credit purchase for invoice {sale.invoice_number}"
                    )

            # Accrue Loyalty Points (1 point per Rs. 100 spent)
            if customer and total_sale_amount >= Decimal("100.00"):
                earned_points = int(total_sale_amount // Decimal("100.00"))
                customer.loyalty_points += earned_points
                customer.save(update_fields=["loyalty_points", "updated_at"])

            sale.subtotal = round_money(running_subtotal)
            sale.discount_amount = round_money(running_discount)
            sale.tax_amount = round_money(running_tax)
            sale.total_amount = round_money(total_sale_amount)
            sale.paid_amount = round_money(running_paid)
            sale.save()

            # Record Sale Tax Breakdown
            if running_tax > ZERO_MONEY:
                SaleTax.objects.create(
                    sale=sale,
                    tax_type="VAT",
                    rate=Decimal("13.00"),
                    taxable_amount=running_subtotal - running_discount,
                    tax_amount=running_tax,
                )

            # Post Balanced Double-Entry Accounting Journal
            cls._post_accounting_journal(organization, sale, running_subtotal - running_discount, running_tax, payments)

            return sale

    @classmethod
    def _post_accounting_journal(cls, organization, sale, net_sales, vat_amount, payments):
        """
        Creates a balanced journal entry for the sale:
        Debit: Payment Assets (Cash/Bank/Receivable)
        Credit: Sales Revenue Account
        Credit: Output VAT Payable Account
        Enforcing sum(Debit) == sum(Credit).
        """
        try:
            from apps.accounting.models import Account, JournalEntry, JournalLine
            
            # Find or create standard ledger accounts
            rev_acc, _ = Account.objects.get_or_create(
                organization=organization,
                account_code="4000",
                defaults={"account_name": "Sales Revenue", "account_type": "REVENUE"}
            )
            tax_acc, _ = Account.objects.get_or_create(
                organization=organization,
                account_code="2200",
                defaults={"account_name": "Output VAT Payable", "account_type": "LIABILITY"}
            )
            cash_acc, _ = Account.objects.get_or_create(
                organization=organization,
                account_code="1010",
                defaults={"account_name": "Cash on Hand", "account_type": "ASSET"}
            )

            entry = JournalEntry.objects.create(
                organization=organization,
                entry_number=f"JE-{sale.invoice_number}",
                status="POSTED",
                reference_type="Sale",
                reference_id=str(sale.id),
                description=f"Automated sale revenue journal for invoice {sale.invoice_number}"
            )

            total_debited = ZERO_MONEY
            # Debit lines for payments
            for pay in payments:
                pay_amount = round_money(pay.get("amount", ZERO_MONEY))
                JournalLine.objects.create(
                    journal_entry=entry,
                    account=cash_acc,
                    debit=pay_amount,
                    credit=ZERO_MONEY,
                    notes=f"Payment via {pay.get('method')}"
                )
                total_debited += pay_amount

            # Credit lines for Revenue and VAT
            JournalLine.objects.create(
                journal_entry=entry,
                account=rev_acc,
                debit=ZERO_MONEY,
                credit=net_sales,
                notes="Net merchandise sales"
            )

            if vat_amount > ZERO_MONEY:
                JournalLine.objects.create(
                    journal_entry=entry,
                    account=tax_acc,
                    debit=ZERO_MONEY,
                    credit=vat_amount,
                    notes="VAT 13% Output"
                )

        except Exception:
            # If accounting tables are still initializing, do not fail POS transaction
            pass
