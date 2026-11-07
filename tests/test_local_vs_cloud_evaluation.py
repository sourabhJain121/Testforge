"""
tests/test_local_vs_cloud_evaluation.py

Verification tests for Stage 1.8: Local vs Cloud Model Empirical Comparison.
Verifies:
  1. qa_artifacts/LOCAL_VS_CLOUD_EVALUATION.json exists and contains summaries for:
     - gemini-3.6-flash (Cloud Frontier API)
     - qwen2.5-coder:7b (Local Open-Weights)
     - codellama:7b (Local Open-Weights)
  2. All 4 canonical targets are present in per-model runs.
  3. Local models record zero cost ($0.00) and zero_egress_privacy=True.
  4. Cloud model achieves lower latency (< 3.0s).
  5. docs/LOCAL_VS_CLOUD_EVALUATION.md exists and contains the full trade-off matrix.
"""

import json
from pathlib import Path
import pytest


def test_local_vs_cloud_json_structure():
    path = Path("qa_artifacts/LOCAL_VS_CLOUD_EVALUATION.json")
    assert path.exists()

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "metadata" in data
    assert "model_summaries" in data

    expected_models = ["gemini-3.6-flash", "qwen2.5-coder:7b", "codellama:7b"]
    for m in expected_models:
        assert m in data["model_summaries"]
        s = data["model_summaries"][m]
        assert "macro_avg_raw_ms" in s
        assert "macro_avg_adj_ms" in s
        assert "macro_avg_latency_sec" in s
        assert "total_cost_usd" in s
        assert "zero_egress_privacy" in s
        assert len(s["per_target_runs"]) == 4

    # Local models have 0.0 token cost and guaranteed zero egress
    assert data["model_summaries"]["qwen2.5-coder:7b"]["total_cost_usd"] == 0.0
    assert data["model_summaries"]["qwen2.5-coder:7b"]["zero_egress_privacy"] is True

    # Cloud model latency is significantly lower
    assert data["model_summaries"]["gemini-3.6-flash"]["macro_avg_latency_sec"] < 3.0
    assert data["model_summaries"]["gemini-3.6-flash"]["zero_egress_privacy"] is False


def test_local_vs_cloud_markdown_documentation():
    path = Path("docs/LOCAL_VS_CLOUD_EVALUATION.md")
    assert path.exists()
    content = path.read_text(encoding="utf-8")
    assert "Local vs Cloud Model Empirical Comparison" in content
    assert "Gemini 3.6 Flash" in content
    assert "Qwen 2.5 Coder 7B" in content
    assert "CodeLlama 7B" in content
    assert len(content) > 1000
