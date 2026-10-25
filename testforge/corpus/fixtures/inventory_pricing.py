"""
inventory_pricing.py - Fixture 3: Inventory Tier Pricing Calculator.

Category: E-Commerce & Financial Logic
Domain: Tiered customer discounts, bulk item volume incentives, and conditional express shipping.
"""

from testforge.corpus.models import CorpusFixture, DefectVariant

REFERENCE_CODE = '''"""
inventory_pricing.py - Realistic e-commerce tiered discount and bulk inventory pricing engine.
"""

def compute_inventory_order(base_price: float, quantity: int, customer_tier: str, express_shipping: bool) -> float:
    """
    Computes total order price with multi-tiered discounts, volume cutoffs, and shipping fees.

    Preconditions:
      - base_price must be > 0.0.
      - quantity must be > 0.

    Rules:
      - Tier 'PLATINUM': 25% discount.
      - Tier 'GOLD': 15% discount.
      - Tier 'SILVER': 5% discount.
      - Other tiers: 0% discount.
      - Bulk incentive: If quantity >= 50, extra $2.00 off per item.
      - Express shipping: $25.00 flat fee, unless pre-discount subtotal >= 500.00 (then free).
      - Returns rounded total to 2 decimal places.
    """
    if base_price <= 0.0 or quantity <= 0:
        return 0.0

    subtotal = base_price * quantity

    # Determine tier percentage
    if customer_tier == "PLATINUM":
        tier_discount = 0.25
    elif customer_tier == "GOLD":
        tier_discount = 0.15
    elif customer_tier == "SILVER":
        tier_discount = 0.05
    else:
        tier_discount = 0.0

    discounted_subtotal = subtotal * (1.0 - tier_discount)

    # Bulk discount
    if quantity >= 50:
        discounted_subtotal = discounted_subtotal - (quantity * 2.0)

    # Shipping computation
    shipping_cost = 0.0
    if express_shipping:
        if subtotal < 500.0:
            shipping_cost = 25.0
        else:
            shipping_cost = 0.0

    total = discounted_subtotal + shipping_cost
    return round(max(0.0, total), 2)
'''

BASELINE_TESTS = '''"""
baseline_tests.py - Test suite for Inventory Pricing Calculator.
"""
from target import compute_inventory_order


def test_regular_tier_no_discount():
    # 10 items @ $10.0 = $100.0
    total = compute_inventory_order(10.0, 10, "REGULAR", False)
    assert total == 100.0


def test_platinum_tier_25_pct_discount():
    # 10 items @ $100.0 = $1000.0 - 25% = $750.0; subtotal >= 500 -> free shipping
    total = compute_inventory_order(100.0, 10, "PLATINUM", True)
    assert total == 750.0


def test_gold_tier_15_pct_discount():
    # 2 items @ $100.0 = $200.0 - 15% = $170.0; subtotal < 500 -> +$25 shipping = $195.0
    total = compute_inventory_order(100.0, 2, "GOLD", True)
    assert total == 195.0


def test_silver_tier_5_pct_discount():
    # 10 items @ $10.0 = $100.0 - 5% = $95.0
    total = compute_inventory_order(10.0, 10, "SILVER", False)
    assert total == 95.0


def test_bulk_volume_incentive_exact_boundary_50_items():
    # 50 items @ $10.0 = $500.0; regular tier -> 500.0 - (50 * $2) = $400.0
    total = compute_inventory_order(10.0, 50, "REGULAR", False)
    assert total == 400.0


def test_express_shipping_waiver_exact_boundary_500():
    # 5 items @ $100.0 = $500.0; express_shipping True; subtotal >= 500 -> shipping is $0
    total = compute_inventory_order(100.0, 5, "REGULAR", True)
    assert total == 500.0


def test_express_shipping_charged_under_500():
    # 4 items @ $100.0 = $400.0; subtotal < 500 -> +$25 shipping = $425.0
    total = compute_inventory_order(100.0, 4, "REGULAR", True)
    assert total == 425.0


def test_invalid_zero_or_negative_price():
    assert compute_inventory_order(0.0, 10, "REGULAR", False) == 0.0
    assert compute_inventory_order(-10.0, 10, "REGULAR", False) == 0.0


def test_invalid_zero_or_negative_quantity():
    assert compute_inventory_order(50.0, 0, "REGULAR", False) == 0.0
    assert compute_inventory_order(50.0, -2, "REGULAR", False) == 0.0
'''

# Defect 1: Bulk discount requires quantity > 50 instead of >= 50
BUGGY_CODE_DEFECT_1 = REFERENCE_CODE.replace(
    '    if quantity >= 50:',
    '    if quantity > 50:  # DEFECT: off-by-one strict inequality'
)

# Defect 2: Express shipping waiver logic inverted
BUGGY_CODE_DEFECT_2 = REFERENCE_CODE.replace(
    '        if subtotal < 500.0:\n            shipping_cost = 25.0\n        else:\n            shipping_cost = 0.0',
    '        if subtotal >= 500.0:  # DEFECT: inverted waiver\n            shipping_cost = 25.0\n        else:\n            shipping_cost = 0.0'
)

# Defect 3: Silver tier receives 0% discount
BUGGY_CODE_DEFECT_3 = REFERENCE_CODE.replace(
    '    elif customer_tier == "SILVER":\n        tier_discount = 0.05',
    '    elif customer_tier == "SILVER":\n        tier_discount = 0.0  # DEFECT: silver tier discount omitted'
)

DEFECTS = {
    "DEFECT-IP-001": DefectVariant(
        defect_id="DEFECT-IP-001",
        fixture_id="inventory_pricing_calculator",
        name="Bulk Volume Cutoff Strict Inequality Off-By-One",
        defect_type="Boundary Relational Error (> vs >=)",
        description="Requires quantity > 50 instead of >= 50, depriving exact 50-unit wholesale orders of the bulk incentive.",
        target_function="compute_inventory_order",
        buggy_source_code=BUGGY_CODE_DEFECT_1,
        expected_failing_test="test_bulk_volume_incentive_exact_boundary_50_items",
        expected_error_type="AssertionError",
        expected_message_substring="assert total == 400.0"
    ),
    "DEFECT-IP-002": DefectVariant(
        defect_id="DEFECT-IP-002",
        fixture_id="inventory_pricing_calculator",
        name="Express Shipping Waiver Inversion",
        defect_type="Condition Inversion / Business Logic Error",
        description="Inverts shipping fee condition, penalizing high-value orders ($500+) with shipping charges while waiving fees on small orders.",
        target_function="compute_inventory_order",
        buggy_source_code=BUGGY_CODE_DEFECT_2,
        expected_failing_test="test_express_shipping_waiver_exact_boundary_500",
        expected_error_type="AssertionError",
        expected_message_substring="assert total == 500.0"
    ),
    "DEFECT-IP-003": DefectVariant(
        defect_id="DEFECT-IP-003",
        fixture_id="inventory_pricing_calculator",
        name="Silver Tier Discount Omission",
        defect_type="Constant Valuation / Discount Drop",
        description="Sets Silver customer tier discount to 0.0 instead of 0.05 (5%), overcharging Silver customers.",
        target_function="compute_inventory_order",
        buggy_source_code=BUGGY_CODE_DEFECT_3,
        expected_failing_test="test_silver_tier_5_pct_discount",
        expected_error_type="AssertionError",
        expected_message_substring="assert total == 95.0"
    ),
}

FIXTURE = CorpusFixture(
    fixture_id="inventory_pricing_calculator",
    name="Inventory Tier Pricing Calculator",
    category="Pricing & Financial Rules",
    description="Multi-tier customer discount engine with bulk volume thresholds and conditional shipping waivers.",
    function_contract="compute_inventory_order(base_price: float, quantity: int, customer_tier: str, express_shipping: bool) -> float",
    source_file="samples/inventory_pricing.py",
    source_code=REFERENCE_CODE,
    baseline_test_code=BASELINE_TESTS,
    defects=DEFECTS,
)
