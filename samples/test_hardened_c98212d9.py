import os
import sys
sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import pytest
from samples.discount import calculate_fee

def test_calculate_fee_nominal():
    result = calculate_fee(100.0, False)
    assert result == pytest.approx(3.0, rel=1e-3)
def test_calculate_fee_guard_amount_returns_constant():
    result = calculate_fee(0.0, False)
    assert result == pytest.approx(0.0, rel=1e-3)
def test_calculate_fee_threshold_amount_0():
    result = calculate_fee(0, False)
    assert result == pytest.approx(0.0, rel=1e-3)
def test_calculate_fee_threshold_amount_neg_1():
    result = calculate_fee(-1, False)
    assert result == pytest.approx(0.0, rel=1e-3)
def test_calculate_fee_threshold_amount_1():
    result = calculate_fee(1, False)
    assert result == pytest.approx(0.03, rel=1e-3)
def test_calculate_fee_extreme_amount_zero():
    result = calculate_fee(0, False)
    assert result == pytest.approx(0.0, rel=1e-3)
def test_calculate_fee_extreme_amount_negative_one():
    result = calculate_fee(-1, False)
    assert result == pytest.approx(0.0, rel=1e-3)
def test_calculate_fee_extreme_amount_negative_large():
    result = calculate_fee(-100, False)
    assert result == pytest.approx(0.0, rel=1e-3)
def test_calculate_fee_extreme_amount_large_positive():
    result = calculate_fee(10000, False)
    assert result == pytest.approx(300.0, rel=1e-3)
def test_calculate_fee_property_non_negative_range():
    for test_val in [0, 5, 20, 100]:
        res = calculate_fee(test_val, False)
        assert res >= 0
def test_calculate_fee_property_monotonicity():
    r1 = calculate_fee(10, False)
    r2 = calculate_fee(100, False)
    assert r1 <= r2