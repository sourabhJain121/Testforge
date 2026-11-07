import os
import sys
sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from target import discount
import pytest

def test_vip_discount():
    assert discount(100, True) == 80.0

def test_large_amount_discount():
    assert discount(200, False) == 180.0

def test_regular_discount():
    assert discount(50, False) == 50.0

def test_discount_nominal():
    result = discount(100.0, False)
    assert result == pytest.approx(100.0, rel=0.001)

def test_discount_threshold_amount_100():
    result = discount(100, False)
    assert result == 100

def test_discount_threshold_amount_99():
    result = discount(99, False)
    assert result == 99

def test_discount_threshold_amount_101():
    result = discount(101, False)
    assert result == pytest.approx(90.9, rel=0.001)

def test_discount_branch_is_vip_True():
    result = discount(100.0, True)
    assert result == pytest.approx(80.0, rel=0.001)

def test_discount_branch_is_vip_False():
    result = discount(100.0, False)
    assert result == pytest.approx(100.0, rel=0.001)

def test_discount_extreme_amount_zero():
    result = discount(0, False)
    assert result == 0

def test_discount_extreme_amount_negative_one():
    result = discount(-1, False)
    assert result == -1

def test_discount_extreme_amount_negative_large():
    result = discount(-100, False)
    assert result == -100

def test_discount_extreme_amount_large_positive():
    result = discount(10000, False)
    assert result == pytest.approx(9000.0, rel=0.001)

def test_discount_property_non_negative_range():
    """[Property Invariant] Non-negative range invariant across probe space. property_confidence="HIGH"."""
    for test_val in [0.0, 1.0, 5.0, 20.0, 100.0]:
        res = discount(test_val, False)
        assert res >= 0

def test_discount_property_monotonicity():
    """[Property Invariant] Monotonicity invariant across ordered sample inputs. property_confidence="HIGH"."""
    r1 = discount(1.0, False)
    r2 = discount(100.0, False)
    assert r1 <= r2

def test_mutant_kill_mutant_7_amount_100():
    result = discount(100, False)
    assert result == 100

def test_mutant_kill_MUT_OFF_BY_ONE_008_amount_100():
    result = discount(100, False)
    assert result == 100