import os
import sys
sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import pytest
from samples.discount import discount

def test_discount_nominal():
    result = discount(1)
    assert result == pytest.approx(0.9, rel=1e-3)
def test_discount_extreme_amt_zero():
    result = discount(0)
    assert result == pytest.approx(0.0, rel=1e-3)
def test_discount_extreme_amt_negative_one():
    result = discount(-1)
    assert result == pytest.approx(-0.9, rel=1e-3)
def test_discount_extreme_amt_negative_large():
    result = discount(-100)
    assert result == pytest.approx(-90.0, rel=1e-3)
def test_discount_extreme_amt_large_positive():
    result = discount(10000)
    assert result == pytest.approx(9000.0, rel=1e-3)
def test_discount_property_non_negative_range():
    for test_val in [0, 5, 20, 100]:
        res = discount(test_val)
        assert res >= 0
def test_discount_property_monotonicity():
    r1 = discount(10)
    r2 = discount(100)
    assert r1 <= r2