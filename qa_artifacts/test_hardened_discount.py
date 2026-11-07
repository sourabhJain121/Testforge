import os
import sys
sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import pytest
from samples.discount import calculate_discount

def test_calculate_discount_nominal():
    result = calculate_discount(100.0, 2, False)
    assert result == pytest.approx(100.0, rel=1e-3)
def test_calculate_discount_multi_arg_scenario():
    result = calculate_discount(100.0, 2, False)
    assert result == pytest.approx(100.0, rel=1e-3)
def test_calculate_discount_guard_price_returns_constant():
    result = calculate_discount(0.0, 2, False)
    assert result == pytest.approx(0.0, rel=1e-3)
def test_calculate_discount_threshold_price_0_0():
    result = calculate_discount(0.0, 2, False)
    assert result == pytest.approx(0.0, rel=1e-3)
def test_calculate_discount_threshold_price_neg_0_1():
    result = calculate_discount(-0.1, 2, False)
    assert result == pytest.approx(0.0, rel=1e-3)
def test_calculate_discount_threshold_price_0_1():
    result = calculate_discount(0.1, 2, False)
    assert result == pytest.approx(0.1, rel=1e-3)
def test_calculate_discount_threshold_quantity_5():
    result = calculate_discount(100.0, 5, False)
    assert result == pytest.approx(90.0, rel=1e-3)
def test_calculate_discount_threshold_quantity_4():
    result = calculate_discount(100.0, 4, False)
    assert result == pytest.approx(100.0, rel=1e-3)
def test_calculate_discount_threshold_quantity_6():
    result = calculate_discount(100.0, 6, False)
    assert result == pytest.approx(90.0, rel=1e-3)
def test_calculate_discount_branch_is_member_True():
    result = calculate_discount(100.0, 2, True)
    assert result == pytest.approx(90.0, rel=1e-3)
def test_calculate_discount_branch_is_member_False():
    result = calculate_discount(100.0, 2, False)
    assert result == pytest.approx(100.0, rel=1e-3)
def test_calculate_discount_extreme_price_zero():
    result = calculate_discount(0, 2, False)
    assert result == pytest.approx(0.0, rel=1e-3)
def test_calculate_discount_extreme_price_negative_one():
    result = calculate_discount(-1, 2, False)
    assert result == pytest.approx(0.0, rel=1e-3)
def test_calculate_discount_extreme_price_negative_large():
    result = calculate_discount(-100, 2, False)
    assert result == pytest.approx(0.0, rel=1e-3)
def test_calculate_discount_extreme_price_large_positive():
    result = calculate_discount(10000, 2, False)
    assert result == pytest.approx(10000.0, rel=1e-3)
def test_calculate_discount_extreme_quantity_zero():
    result = calculate_discount(100.0, 0, False)
    assert result == pytest.approx(100.0, rel=1e-3)
def test_calculate_discount_extreme_quantity_negative_one():
    result = calculate_discount(100.0, -1, False)
    assert result == pytest.approx(100.0, rel=1e-3)
def test_calculate_discount_extreme_quantity_negative_large():
    result = calculate_discount(100.0, -100, False)
    assert result == pytest.approx(100.0, rel=1e-3)
def test_calculate_discount_extreme_quantity_large_positive():
    result = calculate_discount(100.0, 10000, False)
    assert result == pytest.approx(90.0, rel=1e-3)
def test_calculate_discount_property_non_negative_range():
    """[Property Invariant] Non-negative range invariant across probe space. property_confidence="HIGH"."""
    for test_val in [0.0, 1.0, 5.0, 20.0, 100.0]:
        res = calculate_discount(test_val, 2, False)
        assert res >= 0
def test_calculate_discount_property_monotonicity():
    """[Property Invariant] Monotonicity invariant across ordered sample inputs. property_confidence="HIGH"."""
    r1 = calculate_discount(1.0, 2, False)
    r2 = calculate_discount(100.0, 2, False)
    assert r1 <= r2

def test_calculate_discount_two_decimal_precision():
    """Kills MUT_MATH_FUNC_018 (round to 1 decimal place mutant)."""
    assert calculate_discount(10.55, 1, False) == 10.55
