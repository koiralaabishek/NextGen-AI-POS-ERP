from decimal import Decimal
from django.db import models
from django.core.exceptions import ValidationError
from common.models.base import TenantScopedModel, UUIDBaseModel, TimestampedModel
from common.utils.money import round_money, ZERO_MONEY


class FiscalPeriod(TenantScopedModel):
    name = models.CharField(max_length=50)  # e.g. FY 2083/84
    start_date = models.DateField()
    end_date = models.DateField()
    is_closed = models.BooleanField(default=False)

    class Meta:
        db_table = "fiscal_periods"
        unique_together = ("organization", "name")

    def __str__(self):
        return f"{self.name} ({self.start_date} to {self.end_date})"


class Account(TenantScopedModel):
    ACCOUNT_TYPES = [
        ("ASSET", "Asset"),
        ("LIABILITY", "Liability"),
        ("EQUITY", "Equity"),
        ("REVENUE", "Revenue"),
        ("EXPENSE", "Expense"),
    ]

    account_code = models.CharField(max_length=50)
    account_name = models.CharField(max_length=150)
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPES)
    parent_account = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, related_name="sub_accounts"
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "accounts"
        unique_together = ("organization", "account_code")
        ordering = ["account_code"]

    def __str__(self):
        return f"{self.account_code} - {self.account_name} ({self.account_type})"


class JournalEntry(TenantScopedModel):
    STATUS_CHOICES = [
        ("DRAFT", "Draft"),
        ("POSTED", "Posted (Immutable)"),
        ("REVERSED", "Reversed"),
    ]

    entry_number = models.CharField(max_length=50)
    entry_date = models.DateField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="DRAFT")
    reference_type = models.CharField(max_length=50, blank=True)
    reference_id = models.CharField(max_length=100, blank=True)
    description = models.TextField(blank=True)

    class Meta:
        db_table = "journal_entries"
        unique_together = ("organization", "entry_number")
        ordering = ["-entry_date", "-created_at"]

    def __str__(self):
        return f"{self.entry_number} ({self.status})"

    def post(self):
        """
        Validates that sum(Debit) == sum(Credit) before posting.
        Posted financial records cannot be modified or deleted.
        """
        lines = self.lines.all()
        total_debit = round_money(sum((line.debit for line in lines), ZERO_MONEY))
        total_credit = round_money(sum((line.credit for line in lines), ZERO_MONEY))

        if total_debit != total_credit:
            raise ValidationError(
                f"Double-entry balance check failed! Total Debits ({total_debit}) != Total Credits ({total_credit})."
            )

        self.status = "POSTED"
        self.save(update_fields=["status", "updated_at"])


class JournalLine(UUIDBaseModel, TimestampedModel):
    journal_entry = models.ForeignKey(JournalEntry, on_delete=models.CASCADE, related_name="lines")
    account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name="journal_lines")
    debit = models.DecimalField(max_digits=14, decimal_places=2, default=ZERO_MONEY)
    credit = models.DecimalField(max_digits=14, decimal_places=2, default=ZERO_MONEY)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = "journal_lines"

    def clean(self):
        super().clean()
        if self.debit > ZERO_MONEY and self.credit > ZERO_MONEY:
            raise ValidationError("A journal line cannot have both Debit and Credit amounts.")
        if self.debit == ZERO_MONEY and self.credit == ZERO_MONEY:
            raise ValidationError("A journal line must specify either a Debit or Credit amount.")


class BankAccount(TenantScopedModel):
    bank_name = models.CharField(max_length=150)
    account_number = models.CharField(max_length=100)
    account_name = models.CharField(max_length=150)
    branch_name = models.CharField(max_length=150, blank=True)
    balance = models.DecimalField(max_digits=14, decimal_places=2, default=ZERO_MONEY)

    class Meta:
        db_table = "bank_accounts"
        unique_together = ("organization", "account_number")

    def __str__(self):
        return f"{self.bank_name} - {self.account_number}"


class Expense(TenantScopedModel):
    category = models.CharField(max_length=100)  # Rent, Utilities, Wages, Raw materials
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    expense_date = models.DateField()
    payment_method = models.CharField(max_length=50, default="CASH")
    notes = models.TextField(blank=True)

    class Meta:
        db_table = "expenses"
        ordering = ["-expense_date"]


class TaxRate(TenantScopedModel):
    tax_name = models.CharField(max_length=50)  # VAT, Service Charge
    percentage = models.DecimalField(max_digits=5, decimal_places=2)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "tax_rates"
        unique_together = ("organization", "tax_name")
