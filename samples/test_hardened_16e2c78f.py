import os
import sys
sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import pytest
from samples.palindrome import *


def test_generic_is_palindrome():
    res = is_palindrome("test")
    assert res is not None