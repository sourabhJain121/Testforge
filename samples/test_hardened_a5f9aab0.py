import os
import sys
sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import pytest
from samples.loop import loop

def test_loop_nominal():
    result = loop()
    assert result == 42