"""
samples/currency_converter.py - Deterministic offline foreign exchange conversion engine.
"""
from typing import Dict

BASE_RATES_TO_USD: Dict[str, float] = {
    "USD": 1.0,
    "EUR": 1.08,
    "GBP": 1.25,
    "JPY": 0.008,
    "CAD": 0.75,
    "CHF": 1.10,
}


def convert_currency(
    amount: float,
    from_curr: str,
    to_curr: str,
    is_vip: bool = False,
    spread_bps: int = 20
) -> float:
    """
    Converts amount from from_curr to to_curr using deterministic base rates.

    Preconditions:
      - amount >= 0.0.
      - from_curr and to_curr must be known supported currencies.
      - spread_bps >= 0.

    Rules:
      - If amount == 0.0: returns 0.0.
      - If from_curr == to_curr: returns round(amount, 2) without spread or fees.
      - Base cross rate = BASE_RATES_TO_USD[from_curr] / BASE_RATES_TO_USD[to_curr].
      - Spread: spread_bps / 10000. If is_vip is True, spread is halved (50% VIP discount).
      - Converted before fee = amount * base_cross_rate * (1.0 - effective_spread).
      - Flat transaction fee: $2.00 (in target currency units) charged only if amount < 50.0 and not is_vip.
      - Returns net converted amount rounded to 2 decimal places.
    """
    if amount < 0.0:
        raise ValueError(f"Amount must be non-negative: {amount}")

    if amount == 0.0:
        return 0.0

    from_curr_u = from_curr.upper()
    to_curr_u = to_curr.upper()

    if from_curr_u not in BASE_RATES_TO_USD:
        raise ValueError(f"Unsupported currency: {from_curr}")
    if to_curr_u not in BASE_RATES_TO_USD:
        raise ValueError(f"Unsupported currency: {to_curr}")

    # Same currency conversion has 0 spread and 0 fee
    if from_curr_u == to_curr_u:
        return round(amount, 2)

    cross_rate = BASE_RATES_TO_USD[from_curr_u] / BASE_RATES_TO_USD[to_curr_u]

    # Calculate effective spread (1 bps = 0.0001)
    base_spread = spread_bps / 10000.0
    effective_spread = base_spread * 0.5 if is_vip else base_spread

    gross_converted = amount * cross_rate * (1.0 - effective_spread)

    # Apply small transaction fee unless waived
    flat_fee = 0.0
    if amount < 50.0 and not is_vip:
        flat_fee = 2.0

    net_converted = max(0.0, gross_converted - flat_fee)
    return round(net_converted, 2)
