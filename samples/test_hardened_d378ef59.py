import os
import sys
sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from target import discount
import pytest
from target import *

def test_vip_discount():
    assert discount(100, True) == 80.0

def test_large_amount_discount():
    assert discount(200, False) == 180.0

def test_regular_discount():
    assert discount(50, False) == 50.0

def test_discount_vip_discount():
    assert discount(100.0, True) == pytest.approx(80.0)
    assert discount(200.0, True) == pytest.approx(160.0)
    assert discount(50.0, True) == pytest.approx(40.0)

def test_discount_vip_edge_cases():
    assert discount(0.0, True) == pytest.approx(0.0)
    assert discount(-50.0, True) == pytest.approx(-40.0)

@pytest.mark.parametrize('amount, expected', [(100.0, 100.0), (99.0, 99.0), (99.99, 99.99), (0.0, 0.0), (-10.0, -10.0)])
def test_discount_non_vip_no_discount(amount, expected):
    assert discount(amount, False) == pytest.approx(expected)

@pytest.mark.parametrize('amount, expected', [(100.01, 100.01 * 0.9), (101.0, 90.9), (200.0, 180.0)])
def test_discount_non_vip_discount(amount, expected):
    assert discount(amount, False) == pytest.approx(expected)