"""
currency_converter.py - Fixture 5: Deterministic Currency Converter.

Category: Currency Exchange & Forex Engine
Domain: Multi-currency conversion with fixed cross-rate matrix, VIP spread discounts, and threshold-based fee waivers.
"""

from testforge.corpus.models import CorpusFixture, DefectVariant

REFERENCE_CODE = '''"""
currency_converter.py - Deterministic offline foreign exchange conversion engine.
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
'''

BASELINE_TESTS = '''"""
baseline_tests.py - Test suite for Deterministic Currency Converter.
"""
import pytest
from target import convert_currency


def test_identical_currency_no_spread_or_fee():
    # 100.0 USD -> 100.0 USD
    assert convert_currency(100.0, "USD", "USD") == 100.0
    assert convert_currency(25.0, "EUR", "EUR") == 25.0


def test_usd_to_eur_conversion_nominal():
    # 100 USD to EUR: cross rate = 1.0 / 1.08 = 0.925926
    # spread = 20 bps = 0.002 -> (1 - 0.002) = 0.998
    # 100 * 0.925926 * 0.998 = 92.41; amount >= 50 -> fee is $0
    res = convert_currency(100.0, "USD", "EUR")
    assert res == 92.41


def test_gbp_to_usd_conversion_nominal():
    # 100 GBP to USD: cross rate = 1.25 / 1.0 = 1.25
    # spread = 20 bps = 0.002 -> 100 * 1.25 * 0.998 = 124.75; fee = $0
    res = convert_currency(100.0, "GBP", "USD")
    assert res == 124.75


def test_small_order_under_50_incurs_flat_fee():
    # 20.0 USD to EUR: 20 * (1.0 / 1.08) * 0.998 = 18.48 - $2.00 fee = 16.48
    res = convert_currency(20.0, "USD", "EUR", is_vip=False)
    assert res == 16.48


def test_vip_customer_receives_reduced_spread_and_fee_waiver():
    # 20.0 USD to EUR with VIP: spread halved (10 bps = 0.001); fee waived ($0)
    # 20 * (1.0 / 1.08) * 0.999 = 18.50 - $0 fee = 18.50
    res = convert_currency(20.0, "USD", "EUR", is_vip=True)
    assert res == 18.50


def test_zero_amount_returns_zero():
    assert convert_currency(0.0, "USD", "EUR") == 0.0


def test_negative_amount_raises_value_error():
    with pytest.raises(ValueError, match="Amount must be non-negative"):
        convert_currency(-10.0, "USD", "EUR")


def test_unsupported_currency_raises_value_error():
    with pytest.raises(ValueError, match="Unsupported currency"):
        convert_currency(100.0, "XYZ", "USD")
    with pytest.raises(ValueError, match="Unsupported currency"):
        convert_currency(100.0, "USD", "ABC")
'''

# Defect 1: Identical currency spread fee leak (does not early return on from == to)
BUGGY_CODE_DEFECT_1 = REFERENCE_CODE.replace(
    '    if from_curr_u == to_curr_u:\n        return round(amount, 2)',
    '    # DEFECT: omitted identity check\n    pass'
)

# Defect 2: Inverted cross rate (to / from instead of from / to)
BUGGY_CODE_DEFECT_2 = REFERENCE_CODE.replace(
    'cross_rate = BASE_RATES_TO_USD[from_curr_u] / BASE_RATES_TO_USD[to_curr_u]',
    'cross_rate = BASE_RATES_TO_USD[to_curr_u] / BASE_RATES_TO_USD[from_curr_u]  # DEFECT: inverted rate'
)

# Defect 3: VIP fee waiver condition inverted
BUGGY_CODE_DEFECT_3 = REFERENCE_CODE.replace(
    '    if amount < 50.0 and not is_vip:\n        flat_fee = 2.0',
    '    if amount < 50.0 and is_vip:  # DEFECT: fee applied to VIP instead of non-VIP\n        flat_fee = 2.0'
)

DEFECTS = {
    "DEFECT-CC-001": DefectVariant(
        defect_id="DEFECT-CC-001",
        fixture_id="currency_converter",
        name="Identical Currency Spread Fee Leak",
        defect_type="Short-Circuit Omission / Identity Leak",
        description="Fails to early-return on from_curr == to_curr, applying spread reductions and flat fees on identical currency requests.",
        target_function="convert_currency",
        buggy_source_code=BUGGY_CODE_DEFECT_1,
        expected_failing_test="test_identical_currency_no_spread_or_fee",
        expected_error_type="AssertionError",
        expected_message_substring="assert convert_currency(25.0, 'EUR', 'EUR') == 25.0"
    ),
    "DEFECT-CC-002": DefectVariant(
        defect_id="DEFECT-CC-002",
        fixture_id="currency_converter",
        name="Cross-Rate Matrix Ratio Inversion",
        defect_type="Arithmetic / Cross Rate Inversion",
        description="Calculates to_curr / from_curr instead of from_curr / to_curr, severely mispricing converted totals.",
        target_function="convert_currency",
        buggy_source_code=BUGGY_CODE_DEFECT_2,
        expected_failing_test="test_usd_to_eur_conversion_nominal",
        expected_error_type="AssertionError",
        expected_message_substring="assert res == 92.41"
    ),
    "DEFECT-CC-003": DefectVariant(
        defect_id="DEFECT-CC-003",
        fixture_id="currency_converter",
        name="VIP Fee Waiver Condition Inversion",
        defect_type="Conditional Logic Inversion",
        description="Charges flat transaction fees specifically to VIP customers while waiving fees for regular customers.",
        target_function="convert_currency",
        buggy_source_code=BUGGY_CODE_DEFECT_3,
        expected_failing_test="test_vip_customer_receives_reduced_spread_and_fee_waiver",
        expected_error_type="AssertionError",
        expected_message_substring="assert res == 18.50"
    ),
}

FIXTURE = CorpusFixture(
    fixture_id="currency_converter",
    name="Deterministic Offline Currency Converter",
    category="Foreign Exchange & Cross Rates",
    description="Deterministic cross-currency conversion engine with spread margins, VIP discounts, and flat fee thresholds.",
    function_contract="convert_currency(amount: float, from_curr: str, to_curr: str, is_vip: bool = False, spread_bps: int = 20) -> float",
    source_file="samples/currency_converter.py",
    source_code=REFERENCE_CODE,
    baseline_test_code=BASELINE_TESTS,
    defects=DEFECTS,
)
