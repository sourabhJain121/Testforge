import os
import sys
sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import pytest
from samples.math import multiply

def test_multiply_nominal():
    result = multiply(1, 1)
    assert result == 1
def test_multiply_extreme_x_zero():
    result = multiply(0, 1)
    assert result == 0
def test_multiply_extreme_x_negative_one():
    result = multiply(-1, 1)
    assert result == -1
def test_multiply_extreme_x_negative_large():
    result = multiply(-100, 1)
    assert result == -100
def test_multiply_extreme_x_large_positive():
    result = multiply(10000, 1)
    assert result == 10000
def test_multiply_extreme_y_zero():
    result = multiply(1, 0)
    assert result == 0
def test_multiply_extreme_y_negative_one():
    result = multiply(1, -1)
    assert result == -1
def test_multiply_extreme_y_negative_large():
    result = multiply(1, -100)
    assert result == -100
def test_multiply_extreme_y_large_positive():
    result = multiply(1, 10000)
    assert result == 10000
def test_multiply_property_non_negative_range():
    """[Property Invariant] Non-negative range invariant across probe space. property_confidence="MEDIUM"."""
    for test_val in [0, 1, 5, 20, 100]:
        res = multiply(test_val, 1)
        assert res >= 0
def test_multiply_property_monotonicity():
    """[Property Invariant] Monotonicity invariant across ordered sample inputs. property_confidence="MEDIUM"."""
    r1 = multiply(1, 1)
    r2 = multiply(100, 1)
    assert r1 <= r2