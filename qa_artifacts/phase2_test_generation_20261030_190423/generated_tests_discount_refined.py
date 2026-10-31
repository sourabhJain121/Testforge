import pytest
from target import calculate_discount

def test_calculate_discount_nominal():
    result = calculate_discount(100.0, 2, False)
    assert result == pytest.approx(100.0, rel=1e-3)
def test_calculate_discount_multi_arg_scenario():
    result = calculate_discount(100.0, 2, False)
    assert result == pytest.approx(100.0, rel=1e-3)
def test_calculate_discount_guard_price_returns_constant():
    result = calculate_discount(0.0, 2, False)
    assert result == pytest.approx(0.0, rel=1e-3)
def test_calculate_discount_threshold_price_0_0():
    result = calculate_discount(0.0, 2, False)
    assert result == pytest.approx(0.0, rel=1e-3)
def test_calculate_discount_threshold_price_neg_0_1():
    result = calculate_discount(-0.1, 2, False)
    assert result == pytest.approx(0.0, rel=1e-3)
def test_calculate_discount_threshold_price_0_1():
    result = calculate_discount(0.1, 2, False)
    assert result == pytest.approx(0.1, rel=1e-3)
def test_calculate_discount_threshold_quantity_5():
    result = calculate_discount(100.0, 5, False)
    assert result == pytest.approx(90.0, rel=1e-3)
def test_calculate_discount_threshold_quantity_4():
    result = calculate_discount(100.0, 4, False)
    assert result == pytest.approx(100.0, rel=1e-3)
def test_calculate_discount_threshold_quantity_6():
    result = calculate_discount(100.0, 6, False)
    assert result == pytest.approx(90.0, rel=1e-3)
def test_calculate_discount_branch_is_member_True():
    result = calculate_discount(100.0, 2, True)
    assert result == pytest.approx(90.0, rel=1e-3)
def test_calculate_discount_branch_is_member_False():
    result = calculate_discount(100.0, 2, False)
    assert result == pytest.approx(100.0, rel=1e-3)
def test_mutant_kill_MUT_DIFF_1_price_0_0():
    # Targeted test to kill mutant at line 9: if price <= 0.0: -> if price < 0.0:
    result = calculate_discount(0.0, 2, False)
    assert result == pytest.approx(0.0, rel=1e-3)
def test_mutant_kill_MUT_DIFF_2_exact():
    # Targeted discrimination for surviving mutant at line 20
    result = calculate_discount(100.0, 2, False)
    assert result == pytest.approx(100.0, rel=1e-3)