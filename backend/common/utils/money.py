"""
Financial and monetary calculation utilities.
Always uses Decimal with ROUND_HALF_UP to prevent floating-point inaccuracies.
"""
from decimal import Decimal, ROUND_HALF_UP

ZERO_MONEY = Decimal("0.00")
MONEY_QUANTIZATION = Decimal("0.01")


def round_money(amount: Decimal | float | int | str, places: int = 2) -> Decimal:
    """
    Rounds an amount to the standard monetary decimal places using ROUND_HALF_UP.
    """
    if amount is None:
        return ZERO_MONEY
    if not isinstance(amount, Decimal):
        amount = Decimal(str(amount))
    
    quantize_pattern = Decimal("10") ** -places
    return amount.quantize(quantize_pattern, rounding=ROUND_HALF_UP)
