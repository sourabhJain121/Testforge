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
    """Test VIP customers receive 20% discount regardless of amount."""
    assert discount(0, True) == 0.0
    assert discount(50, True) == pytest.approx(40.0)
    assert discount(100, True) == pytest.approx(80.0)
    assert discount(101, True) == pytest.approx(80.8)
    assert discount(200, True) == pytest.approx(160.0)
    assert discount(-100, True) == pytest.approx(-80.0)

def test_discount_non_vip_boundary_100():
    """Boundary tests around threshold amount > 100 for non-VIP."""
    assert discount(99, False) == 99.0
    assert discount(99.9, False) == 99.9
    assert discount(100, False) == 100.0
    assert discount(100.0, False) == 100.0
    assert discount(100.1, False) == pytest.approx(90.09)
    assert discount(101, False) == pytest.approx(90.9)
    assert discount(105, False) == pytest.approx(94.5)
    assert discount(200, False) == pytest.approx(180.0)

def test_discount_non_vip_edge_cases():
    """Zero and negative amounts for non-VIP."""
    assert discount(0, False) == 0.0
    assert discount(-10, False) == -10.0
    assert discount(-100, False) == -100.0