from decimal import Decimal
from django.db.models import Sum, Q, F
from django.utils import timezone
from apps.accounting.models import Account, JournalEntry, JournalLine
from apps.sales.models import Sale, SaleItem
from apps.procurement.models import PurchaseOrder
from common.utils.money import round_money, ZERO_MONEY


class FinancialReportService:
    @classmethod
    def get_trial_balance(cls, organization, start_date=None, end_date=None):
        """
        Generates Trial Balance for all accounts with posted journal lines.
        Guarantees sum(Debits) == sum(Credits).
        """
        qs = JournalLine.objects.filter(
            journal_entry__organization=organization,
            journal_entry__status="POSTED"
        )
        if start_date:
            qs = qs.filter(journal_entry__entry_date__gte=start_date)
        if end_date:
            qs = qs.filter(journal_entry__entry_date__lte=end_date)

        accounts = Account.objects.filter(organization=organization, is_active=True).order_by("account_code")
        account_rows = []
        grand_debit = ZERO_MONEY
        grand_credit = ZERO_MONEY

        for acc in accounts:
            lines = qs.filter(account=acc)
            acc_debit = round_money(lines.aggregate(t=Sum("debit"))["t"] or ZERO_MONEY)
            acc_credit = round_money(lines.aggregate(t=Sum("credit"))["t"] or ZERO_MONEY)

            if acc_debit > ZERO_MONEY or acc_credit > ZERO_MONEY:
                net_debit = ZERO_MONEY
                net_credit = ZERO_MONEY
                if acc.account_type in ["ASSET", "EXPENSE"]:
                    if acc_debit >= acc_credit:
                        net_debit = acc_debit - acc_credit
                    else:
                        net_credit = acc_credit - acc_debit
                else:
                    if acc_credit >= acc_debit:
                        net_credit = acc_credit - acc_debit
                    else:
                        net_debit = acc_debit - acc_credit

                account_rows.append({
                    "account_code": acc.account_code,
                    "account_name": acc.account_name,
                    "account_type": acc.account_type,
                    "total_debit": str(acc_debit),
                    "total_credit": str(acc_credit),
                    "net_debit": str(net_debit),
                    "net_credit": str(net_credit),
                })
                grand_debit += acc_debit
                grand_credit += acc_credit

        is_balanced = (grand_debit == grand_credit)
        return {
            "period": {"start_date": str(start_date), "end_date": str(end_date)},
            "accounts": account_rows,
            "total_debit": str(grand_debit),
            "total_credit": str(grand_credit),
            "is_balanced": is_balanced,
        }

    @classmethod
    def get_profit_and_loss(cls, organization, start_date=None, end_date=None):
        """
        Generates Profit & Loss Statement (Income Statement):
        Revenue - Cost of Goods Sold = Gross Profit
        Gross Profit - Operating Expenses = Net Profit
        """
        tb = cls.get_trial_balance(organization, start_date, end_date)
        
        revenue_items = []
        expense_items = []
        total_revenue = ZERO_MONEY
        total_expenses = ZERO_MONEY

        for acc in tb["accounts"]:
            if acc["account_type"] == "REVENUE":
                # Revenue net balance is net_credit
                val = Decimal(acc["net_credit"])
                revenue_items.append({"name": acc["account_name"], "code": acc["account_code"], "amount": str(val)})
                total_revenue += val
            elif acc["account_type"] == "EXPENSE":
                val = Decimal(acc["net_debit"])
                expense_items.append({"name": acc["account_name"], "code": acc["account_code"], "amount": str(val)})
                total_expenses += val

        net_profit = total_revenue - total_expenses

        return {
            "period": {"start_date": str(start_date), "end_date": str(end_date)},
            "revenue": {
                "items": revenue_items,
                "total": str(total_revenue),
            },
            "expenses": {
                "items": expense_items,
                "total": str(total_expenses),
            },
            "net_profit": str(net_profit),
            "currency": organization.currency,
        }

    @classmethod
    def get_balance_sheet(cls, organization, as_of_date=None):
        """
        Generates Balance Sheet as of a specific date:
        Assets = Liabilities + Equity
        """
        tb = cls.get_trial_balance(organization, end_date=as_of_date)
        
        assets = []
        liabilities = []
        equity = []
        total_assets = ZERO_MONEY
        total_liabilities = ZERO_MONEY
        total_equity = ZERO_MONEY

        for acc in tb["accounts"]:
            if acc["account_type"] == "ASSET":
                val = Decimal(acc["net_debit"])
                assets.append({"name": acc["account_name"], "code": acc["account_code"], "amount": str(val)})
                total_assets += val
            elif acc["account_type"] == "LIABILITY":
                val = Decimal(acc["net_credit"])
                liabilities.append({"name": acc["account_name"], "code": acc["account_code"], "amount": str(val)})
                total_liabilities += val
            elif acc["account_type"] == "EQUITY":
                val = Decimal(acc["net_credit"])
                equity.append({"name": acc["account_name"], "code": acc["account_code"], "amount": str(val)})
                total_equity += val

        # Net profit flows into Equity
        pnl = cls.get_profit_and_loss(organization, end_date=as_of_date)
        retained_net_profit = Decimal(pnl["net_profit"])
        equity.append({"name": "Current Period Retained Net Profit", "code": "NET-PROFIT", "amount": str(retained_net_profit)})
        total_equity += retained_net_profit

        return {
            "as_of_date": str(as_of_date or timezone.now().date()),
            "assets": {"items": assets, "total": str(total_assets)},
            "liabilities": {"items": liabilities, "total": str(total_liabilities)},
            "equity": {"items": equity, "total": str(total_equity)},
            "total_liabilities_and_equity": str(total_liabilities + total_equity),
            "is_balanced": (total_assets == (total_liabilities + total_equity)),
        }

    @classmethod
    def get_nepal_vat_sales_book(cls, organization, start_date=None, end_date=None):
        """
        Nepal IRD Annex 5 (बिक्री खाता) - Mandatory Sales Register:
        Columns: Date, Invoice No, Buyer Name, Buyer PAN, Total Sales, Tax-Exempt Sales, Taxable Sales, 13% VAT.
        """
        qs = Sale.objects.filter(
            organization=organization,
            status__in=["COMPLETED", "REFUNDED", "PARTIALLY_REFUNDED"]
        ).select_related("customer").order_by("created_at")

        if start_date:
            qs = qs.filter(created_at__date__gte=start_date)
        if end_date:
            qs = qs.filter(created_at__date__lte=end_date)

        rows = []
        tot_sales = ZERO_MONEY
        tot_taxable = ZERO_MONEY
        tot_vat = ZERO_MONEY

        for s in qs:
            taxable = s.subtotal - s.discount_amount
            vat = s.tax_amount
            grand = s.total_amount

            rows.append({
                "date": s.created_at.strftime("%Y-%m-%d"),
                "invoice_number": s.invoice_number,
                "buyer_name": s.customer.name if s.customer else "Consumer (Cash)",
                "buyer_pan": s.customer.tax_number if s.customer else "N/A",
                "total_sales": str(grand),
                "tax_exempt_sales": "0.00",
                "taxable_sales": str(taxable),
                "vat_amount": str(vat),
                "status": s.status,
            })
            tot_sales += grand
            tot_taxable += taxable
            tot_vat += vat

        return {
            "period": {"start_date": str(start_date), "end_date": str(end_date)},
            "taxpayer_pan": organization.tax_number,
            "taxpayer_name": organization.name,
            "entries": rows,
            "summary": {
                "total_sales": str(tot_sales),
                "total_taxable_sales": str(tot_taxable),
                "total_output_vat": str(tot_vat),
            }
        }

    @classmethod
    def get_nepal_vat_purchase_book(cls, organization, start_date=None, end_date=None):
        """
        Nepal IRD Annex 7 (खरिद खाता) - Mandatory Purchase Register:
        Columns: Date, PO/Receipt No, Supplier Name, Supplier PAN, Total Purchase, Taxable Purchase, 13% VAT Paid.
        """
        qs = PurchaseOrder.objects.filter(
            organization=organization,
            status="RECEIVED"
        ).select_related("supplier").order_by("order_date")

        if start_date:
            qs = qs.filter(order_date__gte=start_date)
        if end_date:
            qs = qs.filter(order_date__lte=end_date)

        rows = []
        tot_purchases = ZERO_MONEY
        tot_vat = ZERO_MONEY

        for po in qs:
            grand = po.total_amount
            vat = po.tax_amount
            taxable = grand - vat

            rows.append({
                "date": str(po.order_date),
                "po_number": po.po_number,
                "supplier_name": po.supplier.name,
                "supplier_pan": po.supplier.tax_number or "N/A",
                "total_amount": str(grand),
                "taxable_amount": str(taxable),
                "vat_paid": str(vat),
            })
            tot_purchases += grand
            tot_vat += vat

        return {
            "period": {"start_date": str(start_date), "end_date": str(end_date)},
            "taxpayer_pan": organization.tax_number,
            "taxpayer_name": organization.name,
            "entries": rows,
            "summary": {
                "total_purchases": str(tot_purchases),
                "total_input_vat": str(tot_vat),
            }
        }

    @classmethod
    def get_vat_return_summary(cls, organization, start_date=None, end_date=None):
        """
        Computes Net VAT Payable to Nepal Inland Revenue Department (IRD):
        Output VAT (Sales) - Input VAT (Purchases) = Net VAT Payable.
        """
        sales_reg = cls.get_nepal_vat_sales_book(organization, start_date, end_date)
        purch_reg = cls.get_nepal_vat_purchase_book(organization, start_date, end_date)

        out_vat = Decimal(sales_reg["summary"]["total_output_vat"])
        in_vat = Decimal(purch_reg["summary"]["total_input_vat"])
        net_payable = out_vat - in_vat

        return {
            "period": {"start_date": str(start_date), "end_date": str(end_date)},
            "output_vat_collected": str(out_vat),
            "input_vat_credit": str(in_vat),
            "net_vat_payable_to_ird": str(max(ZERO_MONEY, net_payable)),
            "vat_credit_carried_forward": str(max(ZERO_MONEY, -net_payable)),
            "currency": organization.currency,
        }
