import os
import sys
sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import pytest
from target import calc

def test_calc_nominal():
    result = calc(1)
    assert result == 2
def test_calc_extreme_x_zero():
    result = calc(0)
    assert result == 0
def test_calc_extreme_x_negative_one():
    result = calc(-1)
    assert result == -2
def test_calc_extreme_x_negative_large():
    result = calc(-100)
    assert result == -200
def test_calc_extreme_x_large_positive():
    result = calc(10000)
    assert result == 20000
def test_calc_property_non_negative_range():
    """[Property Invariant] Non-negative range invariant across probe space. property_confidence="MEDIUM"."""
    for test_val in [0, 1, 5, 20, 100]:
        res = calc(test_val)
        assert res >= 0
def test_calc_property_monotonicity():
    """[Property Invariant] Monotonicity invariant across ordered sample inputs. property_confidence="MEDIUM"."""
    r1 = calc(1)
    r2 = calc(100)
    assert r1 <= r2