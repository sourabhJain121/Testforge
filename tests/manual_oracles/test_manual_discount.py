"""
MANUAL ORACLES: SAMPLES/DISCOUNT.PY
Classification: MANUAL (Hand-written, Human-Authored Oracle)
Provenance: Authored during Phase 2 precision analysis to kill MUT_MATH_FUNC_018 (round to 1 decimal place).
Rule: This file is tracked separately from autonomous pipeline synthesis.
"""

import pytest

from samples.discount import calculate_discount


def test_calculate_discount_two_decimal_precision():
    """
    [MANUAL ORACLE] Kills MUT_MATH_FUNC_018 (round to 1 decimal place mutant).
    Autonomous pipeline AST synthesis generated boundary and nominal inputs with 1 decimal place,
    failing to differentiate round(x, 1) from round(x, 2) when the second decimal digit is 0.
    """
    assert calculate_discount(10.55, 1, False) == 10.55
    assert calculate_discount(19.99, 5, True) == pytest.approx(15.99, rel=1e-2)
