import os
import sys
sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from target import discount
import pytest
from target import *

def test_vip_discount():
    assert discount(100.0, True) == pytest.approx(80.0)
    assert discount(0.0, True) == pytest.approx(0.0)
    assert discount(200.0, True) == pytest.approx(160.0)
    assert discount(-50.0, True) == pytest.approx(-40.0)

def test_large_amount_discount():
    assert discount(200, False) == 180.0

def test_regular_discount():
    assert discount(50, False) == 50.0

def test_non_vip_at_and_below_threshold_100():
    assert discount(100.0, False) == 100.0
    assert discount(99.0, False) == 99.0
    assert discount(99.99, False) == 99.99
    assert discount(0.0, False) == 0.0
    assert discount(-100.0, False) == -100.0

def test_non_vip_above_threshold_100_and_at_101():
    assert discount(100.01, False) == pytest.approx(100.01 * 0.9)
    assert discount(100.5, False) == pytest.approx(100.5 * 0.9)
    assert discount(101.0, False) == pytest.approx(90.9)
    assert discount(200.0, False) == pytest.approx(180.0)

@pytest.mark.parametrize('amount, is_vip, expected', [(100.0, False, 100.0), (100.0, True, 80.0), (101.0, False, 90.9), (99.0, False, 99.0), (100.0001, False, 100.0001 * 0.9), (0.0, False, 0.0), (-100.0, False, -100.0)])
def test_discount_parametrized(amount, is_vip, expected):
    assert discount(amount, is_vip) == pytest.approx(expected)