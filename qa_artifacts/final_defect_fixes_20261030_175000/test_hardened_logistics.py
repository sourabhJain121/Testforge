import os
import sys
sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import pytest
from samples.uploaded_logistics_engine import calculate_item_discount

def test_calculate_item_discount_nominal():
    result = calculate_item_discount(10.0, 2)
    assert result is not None

def test_calculate_item_discount_boundary_nominal_alt():
    result = calculate_item_discount(20.0, 5)
    assert result is not None

def test_calculate_item_discount_adversarial_equal():
    result = calculate_item_discount(5.0, 5)
    assert result is not None