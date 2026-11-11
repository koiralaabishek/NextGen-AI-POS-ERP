from rest_framework import serializers
from apps.accounting.models import (
    Account,
    JournalEntry,
    JournalLine,
    FiscalPeriod,
    BankAccount,
    Expense,
    TaxRate,
)


class FiscalPeriodSerializer(serializers.ModelSerializer):
    class Meta:
        model = FiscalPeriod
        fields = ["id", "name", "start_date", "end_date", "is_closed", "created_at"]
        read_only_fields = ["id", "is_closed", "created_at"]


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = ["id", "account_code", "account_name", "account_type", "parent_account", "is_active"]


class JournalLineSerializer(serializers.ModelSerializer):
    account_code = serializers.ReadOnlyField(source="account.account_code")
    account_name = serializers.ReadOnlyField(source="account.account_name")

    class Meta:
        model = JournalLine
        fields = ["id", "account", "account_code", "account_name", "debit", "credit", "notes"]


class JournalEntrySerializer(serializers.ModelSerializer):
    lines = JournalLineSerializer(many=True, read_only=True)

    class Meta:
        model = JournalEntry
        fields = ["id", "entry_number", "entry_date", "status", "reference_type", "reference_id", "description", "lines", "created_at"]
        read_only_fields = ["id", "created_at"]


class ExpenseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Expense
        fields = ["id", "category", "amount", "expense_date", "payment_method", "notes"]


class TaxRateSerializer(serializers.ModelSerializer):
    class Meta:
        model = TaxRate
        fields = ["id", "tax_name", "percentage", "is_active"]
