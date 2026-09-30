import os
import sys
sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import pytest
from samples.discount import *


def test_price_zero_and_negative():
    assert calculate_discount(0.0, 10, True) == 0.0
    assert calculate_discount(-1.0, 5, True) == 0.0
    assert calculate_discount(-100.50, 1, False) == 0.0


def test_price_boundary_positive():
    assert calculate_discount(0.01, 1, False) == 0.01
    assert calculate_discount(0.01, 5, True) == 0.01


def test_quantity_boundary_below_five():
    # Quantity 4 should NOT trigger volume discount
    assert calculate_discount(100.0, 4, False) == 100.0
    assert calculate_discount(100.0, 4, True) == 90.0


def test_quantity_boundary_exactly_five():
    # Quantity 5 SHOULD trigger volume discount (10%)
    assert calculate_discount(100.0, 5, False) == 90.0
    assert calculate_discount(100.0, 5, True) == 80.0


def test_quantity_above_five():
    # Quantity 6 SHOULD trigger volume discount (10%)
    assert calculate_discount(100.0, 6, False) == 90.0
    assert calculate_discount(100.0, 6, True) == 80.0


def test_quantity_zero_and_negative():
    assert calculate_discount(100.0, 0, False) == 100.0
    assert calculate_discount(100.0, -5, False) == 100.0


def test_membership_discount():
    assert calculate_discount(100.0, 1, True) == 90.0
    assert calculate_discount(100.0, 1, False) == 100.0


def test_both_discounts_applied():
    # 10% volume + 10% membership = 20% discount
    assert calculate_discount(100.0, 5, True) == 80.0
    assert calculate_discount(200.0, 10, True) == 160.0


@pytest.mark.parametrize(
    "price, quantity, is_member, expected",
    [
        (50.0, 1, False, 50.0),
        (50.0, 5, False, 45.0),
        (50.0, 1, True, 45.0),
        (50.0, 5, True, 40.0),
        (33.33, 5, True, 26.66),  # 33.33 * 0.8 = 26.664 -> rounded to 26.66
        (12.345, 1, False, 12.35),  # Rounding check
        (19.99, 4, True, 17.99),  # 19.99 * 0.9 = 17.991 -> rounded to 17.99
    ],
)
def test_discount_combinations_and_rounding(price, quantity, is_member, expected):
    assert calculate_discount(price, quantity, is_member) == expected