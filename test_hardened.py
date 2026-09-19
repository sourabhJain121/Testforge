import os
import sys
sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import pytest
from samples.discount import *


def test_discount_rules():
    assert calculate_discount(100.0, 5, True) == 80.0
    assert calculate_discount(100.0, 5, False) == 90.0
    assert calculate_discount(100.0, 4, True) == 90.0
    assert calculate_discount(100.0, 4, False) == 100.0
    assert calculate_discount(0.0, 5, True) == 0.0
    assert calculate_discount(-10.0, 5, True) == 0.0