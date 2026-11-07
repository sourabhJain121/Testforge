"""
tests/test_held_out_generalization_report.py

Verification tests for the empirical E2 Held-Out Mutants Report (Stage 1.5).
Verifies:
  1. qa_artifacts/HELD_OUT_MUTANTS_REPORT.json exists, is valid JSON, and has all 8 targets.
  2. Unseen seeds are [101, 102, 103].
  3. Held-out operators are BITWISE_OP and EXCEPTION_SWAP.
  4. Generalization gap is recorded and small (|gap| <= 15%).
  5. docs/HELD_OUT_MUTANTS.md exists and is populated.
"""

import json
from pathlib import Path
import pytest


def test_held_out_report_json_structure():
    path = Path("qa_artifacts/HELD_OUT_MUTANTS_REPORT.json")
    assert path.exists()

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "metadata" in data
    assert data["metadata"]["unseen_seeds"] == [101, 102, 103]
    assert data["metadata"]["held_out_operator_classes"] == ["BITWISE_OP", "EXCEPTION_SWAP"]
    assert data["metadata"]["target_count"] == 8

    expected_targets = [
        "discount.py",
        "lru_cache.py",
        "order_fsm.py",
        "stats_calculator.py",
        "expression_tokenizer.py",
        "sliding_window_rate_limiter.py",
        "interval_set.py",
        "inventory_ledger.py",
    ]
    for target in expected_targets:
        assert target in data["targets"]
        t_data = data["targets"][target]
        assert "mean_seen_raw_ms" in t_data
        assert "mean_held_out_raw_ms" in t_data
        assert "mean_combined_raw_ms" in t_data
        assert "generalization_gap" in t_data
        assert len(t_data["seen_runs"]) == 3
        assert len(t_data["held_out_runs"]) == 3
        assert len(t_data["combined_runs"]) == 3

    summary = data["summary"]
    assert "macro_avg_seen_raw_ms" in summary
    assert "macro_avg_held_out_raw_ms" in summary
    assert "macro_avg_combined_raw_ms" in summary
    assert "macro_avg_generalization_gap" in summary

    # The generalization gap between seen and held-out should be tightly bounded (|gap| < 15%)
    assert abs(summary["macro_avg_generalization_gap"]) < 15.0


def test_held_out_documentation_exists():
    path = Path("docs/HELD_OUT_MUTANTS.md")
    assert path.exists()
    content = path.read_text(encoding="utf-8")
    assert "TestForge E2 Held-Out Mutants Evaluation" in content
    assert "BITWISE_OP" in content
    assert "EXCEPTION_SWAP" in content
    assert "[101, 102, 103]" in content
    assert len(content) > 1000
