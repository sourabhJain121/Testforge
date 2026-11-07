import os
import sys
sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import pytest
from samples.long_running import long_running

def test_long_running_nominal():
    result = long_running(2)
    assert result == 4
def test_long_running_extreme_n_zero():
    result = long_running(0)
    assert result == 0
def test_long_running_extreme_n_negative_one():
    result = long_running(-1)
    assert result == -2
def test_long_running_extreme_n_negative_large():
    result = long_running(-100)
    assert result == -200
def test_long_running_extreme_n_large_positive():
    result = long_running(10000)
    assert result == 20000
def test_long_running_property_non_negative_range():
    for test_val in [0, 5, 20, 100]:
        res = long_running(test_val)
        assert res >= 0
def test_long_running_property_monotonicity():
    r1 = long_running(10)
    r2 = long_running(100)
    assert r1 <= r2