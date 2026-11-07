"""
tests/test_ablation_matrix.py

Verification tests for the empirical E1 Ablation Matrix (Stage 1.4).
Verifies:
  1. qa_artifacts/ABLATION_MATRIX_RESULTS.json exists, is valid JSON, and contains 7 configurations.
  2. All 8 benchmark targets are evaluated across all configurations.
  3. All 3 seeds are present in every evaluation cell with complete metrics.
  4. Monotonic progression holds: full TestForge (C7) achieves strictly higher
     average mutation score and line coverage than zero-shot baseline (C1).
  5. Markdown report (docs/ABLATION_STUDY.md) and chart (qa_artifacts/ablation_progression_chart.png) exist and are populated.
"""

import json
from pathlib import Path
import pytest


def test_ablation_matrix_json_structure():
    path = Path("qa_artifacts/ABLATION_MATRIX_RESULTS.json")
    assert path.exists(), "ABLATION_MATRIX_RESULTS.json does not exist"

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "metadata" in data
    assert data["metadata"]["seeds"] == [42, 43, 44]
    assert data["metadata"]["configuration_count"] == 7
    assert data["metadata"]["target_count"] == 8

    expected_configs = [
        "C1_ZeroShot",
        "C2_PlusRefExec",
        "C3_PlusReflection",
        "C4_PlusSelfConsistency",
        "C5_PlusToTReAct",
        "C6_PlusRAGMemory",
        "C7_FullTestForge",
    ]
    assert data["configurations"] == expected_configs

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
    assert data["targets"] == expected_targets

    # Check matrix integrity
    for cfg in expected_configs:
        assert cfg in data["matrix"], f"Config {cfg} missing from matrix"
        cfg_data = data["matrix"][cfg]
        assert "label" in cfg_data
        assert "flags" in cfg_data
        assert "targets" in cfg_data
        for t in expected_targets:
            assert t in cfg_data["targets"], f"Target {t} missing from config {cfg}"
            t_data = cfg_data["targets"][t]
            assert "seed_runs" in t_data
            assert len(t_data["seed_runs"]) == 3
            assert "mean_raw_mutation_score" in t_data
            assert "mean_adjusted_mutation_score" in t_data
            assert "mean_line_coverage" in t_data
            assert "mean_branch_coverage" in t_data


def test_ablation_progression_monotonicity():
    path = Path("qa_artifacts/ABLATION_MATRIX_RESULTS.json")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    summary_by_cfg = {item["config_id"]: item for item in data["summary"]}
    c1 = summary_by_cfg["C1_ZeroShot"]
    c7 = summary_by_cfg["C7_FullTestForge"]

    # Full TestForge must outperform zero-shot baseline substantially
    assert c7["avg_raw_mutation_score"] > c1["avg_raw_mutation_score"]
    assert c7["avg_adjusted_mutation_score"] > c1["avg_adjusted_mutation_score"]
    assert c7["avg_line_coverage"] > c1["avg_line_coverage"]
    assert c7["avg_branch_coverage"] > c1["avg_branch_coverage"]

    # In discount.py and order_fsm.py, C7 adjusted mutation score must reach high levels
    discount_c7 = data["matrix"]["C7_FullTestForge"]["targets"]["discount.py"]
    assert discount_c7["mean_adjusted_mutation_score"] == 100.0

    order_fsm_c7 = data["matrix"]["C7_FullTestForge"]["targets"]["order_fsm.py"]
    assert order_fsm_c7["mean_adjusted_mutation_score"] >= 97.0


def test_ablation_documentation_and_chart_exist():
    doc_path = Path("docs/ABLATION_STUDY.md")
    assert doc_path.exists()
    doc_text = doc_path.read_text(encoding="utf-8")
    assert "TestForge E1 Ablation Study" in doc_text
    assert "C1 (Zero-Shot Baseline)" in doc_text
    assert "C7 (+ critic - Full TestForge)" in doc_text
    assert len(doc_text) > 1000

    chart_path = Path("qa_artifacts/ablation_progression_chart.png")
    assert chart_path.exists()
    assert chart_path.stat().st_size > 10000
