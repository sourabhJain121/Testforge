import os
import sys
sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import pytest
from samples.uploaded_uploaded_logistics_engine import calculate_item_discount

def test_calculate_item_discount_nominal():
    assert calculate_item_discount() is not None
