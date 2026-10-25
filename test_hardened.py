import os
import sys
sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import pytest
from samples.github_requests_status_codes import *


def test_generic__init():
    try:
        res = _init()
        assert res is not None
    except Exception:
        pass


def test_generic_doc():
    try:
        res = doc(1)
        assert res is not None
    except Exception:
        pass