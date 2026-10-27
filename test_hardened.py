import os
import sys
sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import pytest
from samples.discount import discount

def test_discount_nominal():
    assert discount(1) is not None
    assert discount(0) is not None
    assert discount(-1) is not None