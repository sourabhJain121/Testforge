"""
tests/test_extra_benchmark_targets.py

Automated test suite verifying Handout Criterion 1.3:
4 Extra Real-World-Style Benchmark Targets (50-150 LOC) with Permissive MIT Licenses:
  1. Tokenizer: samples/expression_tokenizer.py (108 LOC, 76 mutants)
  2. Rate Limiter: samples/sliding_window_rate_limiter.py (86 LOC, 67 mutants)
  3. Interval Utility: samples/interval_set.py (96 LOC, 67 mutants)
  4. Bank / Inventory: samples/inventory_ledger.py (123 LOC, 97 mutants)
"""

from pathlib import Path

import pytest

from samples.expression_tokenizer import ExpressionTokenizer, TokenType
from samples.interval_set import Interval, IntervalSet
from samples.inventory_ledger import InventoryLedger, ReservationStatus
from samples.sliding_window_rate_limiter import SlidingWindowRateLimiter, Tier
from testforge.mutator import ASTMutator

TARGET_FILES = [
    "samples/expression_tokenizer.py",
    "samples/sliding_window_rate_limiter.py",
    "samples/interval_set.py",
    "samples/inventory_ledger.py",
]


@pytest.mark.parametrize("target_path", TARGET_FILES)
def test_target_loc_and_license_compliance(target_path):
    p = Path(target_path)
    assert p.is_file(), f"Target file '{target_path}' must exist"
    code = p.read_text(encoding="utf-8")

    # Verify Permissive License
    assert "License: MIT" in code, f"Target '{target_path}' must declare permissive MIT license"

    # Verify LOC between 50 and 150 (excluding blank lines and pure comments)
    loc = len([line for line in code.splitlines() if line.strip() and not line.strip().startswith("#")])
    assert 50 <= loc <= 150, f"Target '{target_path}' LOC ({loc}) must be between 50 and 150"

    # Verify rich mutation space
    mutator = ASTMutator()
    mutants = mutator.mutate(code)
    assert len(mutants) >= 50, f"Target '{target_path}' must yield at least 50 mutants, got {len(mutants)}"


def test_expression_tokenizer_behavior():
    tok = ExpressionTokenizer("price * (1.0 + tax) >= 100.50 && status == 'ACTIVE'")
    tokens = tok.tokenize()
    types = [t.type for t in tokens]
    assert TokenType.IDENTIFIER in types
    assert TokenType.OPERATOR in types
    assert TokenType.NUMBER in types
    assert TokenType.STRING in types
    assert TokenType.EOF in types
    assert tokens[-1].type == TokenType.EOF


def test_sliding_window_rate_limiter_behavior():
    limiter = SlidingWindowRateLimiter(default_tier=Tier.FREE)
    now = 1000.0
    # Free tier limit: 10 + 2 burst = 12 requests
    allowed, remaining, reset = limiter.acquire("user_1", current_time=now, cost=10)
    assert allowed is True
    assert remaining == 2

    # Request exceeding burst
    allowed_burst, rem_burst, _ = limiter.acquire("user_1", current_time=now + 1.0, cost=5)
    assert allowed_burst is False
    assert rem_burst == 0


def test_interval_set_behavior():
    iset = IntervalSet([Interval(1.0, 5.0), Interval(10.0, 20.0)])
    assert len(iset) == 2
    assert iset.total_length == 14.0

    # Merge overlapping span [4.0, 12.0) -> merges into [1.0, 20.0)
    iset.add(Interval(4.0, 12.0))
    assert len(iset) == 1
    assert iset.to_tuples() == [(1.0, 20.0)]
    assert iset.contains_point(15.0) is True
    assert iset.contains_point(25.0) is False


def test_inventory_ledger_behavior():
    ledger = InventoryLedger(default_ttl_seconds=60.0)
    ledger.restock("SKU_WIDGET", 100)

    on_hand, reserved, avail = ledger.get_stock("SKU_WIDGET")
    assert on_hand == 100 and reserved == 0 and avail == 100

    now = 500.0
    res_ok = ledger.create_reservation("RES_001", "SKU_WIDGET", 25, current_time=now)
    assert res_ok is True

    _, reserved_now, avail_now = ledger.get_stock("SKU_WIDGET")
    assert reserved_now == 25 and avail_now == 75

    # Commit reservation
    committed = ledger.commit_reservation("RES_001", current_time=now + 10.0)
    assert committed is True
    final_on_hand, final_res, final_avail = ledger.get_stock("SKU_WIDGET")
    assert final_on_hand == 75 and final_res == 0 and final_avail == 75
