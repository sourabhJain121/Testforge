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

def test_discount_vip_precedence():
    """Verify that VIP discount (20%) is applied regardless of amount."""
    assert discount(100.0, True) == pytest.approx(80.0)
    assert discount(200.0, True) == pytest.approx(160.0)
    assert discount(50.0, True) == pytest.approx(40.0)
    assert discount(0.0, True) == pytest.approx(0.0)
    assert discount(-100.0, True) == pytest.approx(-80.0)

def test_discount_non_vip_boundary_exact_100():
    """
    Kills MUT_BOUNDARY_SWAP_006 (amount >= 100) and MUT_OFF_BY_ONE_008 (amount > 99).
    Amount of exactly 100 should NOT receive a discount for non-VIP.
    """
    assert discount(100.0, False) == 100.0

def test_discount_non_vip_boundary_just_above_100():
    """
    Kills MUT_OFF_BY_ONE_007 (amount > 101).
    Amounts strictly greater than 100 (e.g. 100.1, 101) must receive 10% discount.
    """
    assert discount(100.1, False) == pytest.approx(90.09)
    assert discount(101.0, False) == pytest.approx(90.9)

def test_discount_non_vip_boundary_just_below_100():
    """
    Kills MUT_OFF_BY_ONE_008 (amount > 99).
    Amounts strictly less than or equal to 100 should not receive discount.
    """
    assert discount(99.0, False) == 99.0
    assert discount(99.99, False) == 99.99

def test_discount_non_vip_zero_and_negative():
    """Verify zero and negative amounts for non-VIP."""
    assert discount(0.0, False) == 0.0
    assert discount(-50.0, False) == -50.0

def test_discount_non_vip_large_amount():
    """Verify standard discount for non-VIP with large amounts."""
    assert discount(500.0, False) == pytest.approx(450.0)