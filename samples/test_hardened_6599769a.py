import os
import sys
sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import pytest
from samples.sample_calc import *


def test_generic_sample_calc():
    res = sample_calc(2)
    assert res is not None