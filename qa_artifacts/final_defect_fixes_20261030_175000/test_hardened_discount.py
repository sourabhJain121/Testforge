import os
import sys
sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import pytest
from samples.discount import calculate_discount

def test_calculate_discount_nominal():
    result = calculate_discount(10.0, 2, False)
    assert result is not None

def test_calculate_discount_multi_arg_scenario():
    result = calculate_discount(10.0, 2, False)
    assert result is not None