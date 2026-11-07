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
    assert discount(100.0, True) == 80.0
    assert discount(200.0, True) == 160.0
    assert discount(0.0, True) == 0.0
    assert discount(-50.0, True) == -40.0

def test_discount_non_vip_boundary_exact():
    assert discount(100.0, False) == 100.0

def test_discount_non_vip_boundary_above():
    assert discount(101.0, False) == pytest.approx(90.9)
    assert discount(100.1, False) == pytest.approx(90.09)

def test_discount_non_vip_boundary_below():
    assert discount(99.0, False) == 99.0
    assert discount(99.9, False) == 99.9

def test_discount_non_vip_edge_and_general():
    assert discount(200.0, False) == 180.0
    assert discount(0.0, False) == 0.0
    assert discount(-100.0, False) == -100.0