"""
tests/test_external_judge_comparison.py

Verification tests for Stage 1.6: External Mutation Judge (mutmut) Independent Comparison.
Verifies:
  1. qa_artifacts/EXTERNAL_MUTATION_JUDGE_RESULTS.json exists and contains all 4 canonical targets.
  2. Both mutmut and TestForge scores are populated and non-zero.
  3. Pearson correlation between mutmut and TestForge raw scores exceeds 0.95 (strong linear correlation).
  4. docs/EXTERNAL_MUTATION_JUDGE.md exists and contains the full comparison table.
"""

import json
from pathlib import Path
import pytest


def test_external_judge_results_json_structure():
    path = Path("qa_artifacts/EXTERNAL_MUTATION_JUDGE_RESULTS.json")
    assert path.exists()

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "metadata" in data
    assert "mutmut" in data["metadata"]["external_judge"]
    assert "targets" in data

    canonical = ["discount.py", "lru_cache.py", "order_fsm.py", "stats_calculator.py"]
    for tgt in canonical:
        assert tgt in data["targets"]
        t_data = data["targets"][tgt]
        assert "mutmut" in t_data
        assert "testforge" in t_data
        assert t_data["mutmut"]["total_mutants"] > 0
        assert t_data["mutmut"]["killed_mutants"] > 0
        assert t_data["mutmut"]["raw_mutation_score"] > 0
        assert t_data["testforge"]["total_mutants"] > 0
        assert t_data["testforge"]["killed_mutants"] > 0
        assert t_data["testforge"]["raw_mutation_score"] > 0

    summary = data["summary"]
    assert "mutmut_macro_avg_score" in summary
    assert "testforge_macro_avg_raw_score" in summary
    assert "pearson_correlation" in summary

    # Pearson correlation must indicate near-perfect alignment (> 0.95)
    assert summary["pearson_correlation"] > 0.95


def test_external_judge_markdown_documentation():
    path = Path("docs/EXTERNAL_MUTATION_JUDGE.md")
    assert path.exists()
    content = path.read_text(encoding="utf-8")
    assert "mutmut" in content
    assert "Pearson Correlation" in content
    assert "discount.py" in content
    assert "order_fsm.py" in content
    assert len(content) > 1000
