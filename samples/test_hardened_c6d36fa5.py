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

def test_discount_vip():
    assert discount(100, True) == pytest.approx(80.0)
    assert discount(200, True) == pytest.approx(160.0)
    assert discount(0, True) == pytest.approx(0.0)
    assert discount(-50, True) == pytest.approx(-40.0)

def test_discount_non_vip_boundary():
    assert discount(100, False) == 100
    assert discount(100.01, False) == pytest.approx(100.01 * 0.9)
    assert discount(101, False) == pytest.approx(101 * 0.9)
    assert discount(99.99, False) == pytest.approx(99.99)
    assert discount(99, False) == 99

def test_discount_non_vip_general():
    assert discount(0, False) == 0
    assert discount(-100, False) == -100
    assert discount(50, False) == 50
    assert discount(150, False) == pytest.approx(135.0)