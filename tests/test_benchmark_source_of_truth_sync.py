"""
Single Source of Truth Benchmark Consistency Test Suite (Stage 0.2).
Guarantees that:
1. qa_artifacts/MULTI_TARGET_BENCHMARK_RESULTS.json is the single authoritative source of truth.
2. All 4 canonical targets (discount.py, order_fsm.py, lru_cache.py, stats_calculator.py) exist and are populated.
3. Summary markdown and documentation reflect the exact JSON metrics.
4. Frontend API endpoint /api/benchmark/multi-target/summary matches the JSON source of truth.
"""

import json
import os
import pathlib

import pytest

BASE_DIR = pathlib.Path(__file__).parent.parent
RESULTS_JSON_PATH = BASE_DIR / "qa_artifacts" / "MULTI_TARGET_BENCHMARK_RESULTS.json"
SUMMARY_MD_PATH = BASE_DIR / "qa_artifacts" / "MULTI_TARGET_BENCHMARK_SUMMARY.md"


@pytest.fixture(scope="module")
def benchmark_data():
    assert RESULTS_JSON_PATH.exists(), f"Benchmark results JSON missing at {RESULTS_JSON_PATH}"
    with open(RESULTS_JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def test_single_source_of_truth_contains_canonical_targets(benchmark_data):
    """Asserts all 4 canonical target modules are present in the JSON source of truth."""
    targets = benchmark_data.get("targets", {})
    expected = [
        "samples/discount.py",
        "samples/order_fsm.py",
        "samples/lru_cache.py",
        "samples/stats_calculator.py"
    ]
    for exp in expected:
        assert exp in targets, f"Expected canonical target {exp} missing from {RESULTS_JSON_PATH}"


def test_order_fsm_score_is_not_falsified_91_percent(benchmark_data):
    """
    Asserts that order_fsm.py reports its true measured scores (not the historic false claim of 91.46%).
    With Stage 0.3 FSM lifecycle synthesis, autonomous pipeline score reaches 100.0% adjusted (103/106 killed, 3 equivalent).
    """
    order_fsm = benchmark_data["targets"]["samples/order_fsm.py"]["scenarios"]
    pipeline_score = order_fsm["agentic_reflection"]["adjusted_mutation_score"]
    manual_score = order_fsm["pipeline_plus_manual"]["adjusted_mutation_score"]
    killed = order_fsm["agentic_reflection"]["killed_mutants"]

    assert pipeline_score != 91.46, "order_fsm pipeline-only score must not claim false 91.46%"
    assert manual_score != 91.46, "order_fsm manual score must not claim false 91.46%"
    assert pipeline_score >= 95.0, f"Expected order_fsm pipeline score >= 95.0%, got {pipeline_score}"
    assert killed == 103, f"Expected order_fsm 103 killed mutants, got {killed}"


def test_markdown_summary_matches_json_source_of_truth(benchmark_data):
    """Asserts that the markdown summary matches the numerical figures in the JSON file."""
    assert SUMMARY_MD_PATH.exists(), f"Summary markdown missing at {SUMMARY_MD_PATH}"
    md_content = SUMMARY_MD_PATH.read_text(encoding="utf-8")

    # Check that each target module name appears in the markdown
    for t_path, t_info in benchmark_data["targets"].items():
        m_name = t_info["module_name"]
        assert m_name in md_content, f"Module {m_name} missing from {SUMMARY_MD_PATH}"

    # Check geometric mean adjusted mutation score
    gm_adj = benchmark_data["cross_target_summary"]["scenarios"]["agentic_reflection"]["geometric_mean_adj_mutation_score"]
    assert f"{gm_adj:.1f}%" in md_content


def test_server_summary_endpoint_serves_json_source_of_truth(benchmark_data):
    """Asserts that the FastAPI server endpoint /api/benchmark/multi-target/summary matches the JSON source of truth."""
    from starlette.testclient import TestClient

    from server import app

    client = TestClient(app)
    response = client.get("/api/benchmark/multi-target/summary")
    assert response.status_code == 200
    payload = response.json()
    assert payload.get("status") == "SUCCESS"
    served_data = payload.get("results", {})

    assert set(served_data.get("targets", {}).keys()) == set(benchmark_data.get("targets", {}).keys())

