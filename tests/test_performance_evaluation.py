"""
Unit and integration tests for TestForge Criterion 10 End-to-End Performance Evaluation.
Tests cover:
- EndToEndPerformanceEvaluator instantiation and execution
- Prompt architecture and developer persona configuration
- Token accounting and Gemini 1.5 Flash cost modeling
- Statistical distribution metrics (mean, median, stddev, IQR, min, max)
- Multi-run matrix aggregation
- Benchmark artifact export integrity
"""

import json
import tempfile
from pathlib import Path

import pytest

from testforge.performance_evaluator import (
    GEMINI_FLASH_COMPLETION_RATE_PER_1M,
    GEMINI_FLASH_PROMPT_RATE_PER_1M,
    DeveloperPersona,
    EndToEndPerformanceEvaluator,
    PerformanceRunRecord,
    PromptStrategy,
    aggregate_run_statistics,
    compute_distribution_stats,
)

SAMPLE_CODE = """
def calculate_discount(price: float, is_vip: bool) -> float:
    if price < 0:
        raise ValueError("Price cannot be negative")
    if is_vip:
        return price * 0.8
    if price >= 100:
        return price * 0.9
    return price
"""


def test_compute_distribution_stats_empty():
    stats = compute_distribution_stats([])
    assert stats.mean == 0.0
    assert stats.median == 0.0
    assert stats.stddev == 0.0
    assert stats.iqr == 0.0
    assert stats.min == 0.0
    assert stats.max == 0.0


def test_compute_distribution_stats_single_value():
    stats = compute_distribution_stats([42.5])
    assert stats.mean == 42.5
    assert stats.median == 42.5
    assert stats.stddev == 0.0
    assert stats.iqr == 0.0
    assert stats.min == 42.5
    assert stats.max == 42.5


def test_compute_distribution_stats_known_distribution():
    # [10, 20, 30, 40, 50]
    values = [10.0, 20.0, 30.0, 40.0, 50.0]
    stats = compute_distribution_stats(values)
    assert stats.mean == 30.0
    assert stats.median == 30.0
    assert stats.min == 10.0
    assert stats.max == 50.0
    assert stats.stddev > 0.0
    assert stats.iqr > 0.0


def test_evaluator_single_run_zero_shot():
    evaluator = EndToEndPerformanceEvaluator(SAMPLE_CODE, target_name="test_discount.py")
    record = evaluator.execute_single_run(
        strategy=PromptStrategy.ZERO_SHOT,
        persona=DeveloperPersona.BEGINNER,
        repetition_index=1,
    )
    assert isinstance(record, PerformanceRunRecord)
    assert record.target_name == "test_discount.py"
    assert record.strategy == PromptStrategy.ZERO_SHOT
    assert record.persona == DeveloperPersona.BEGINNER
    assert record.success is True
    assert record.total_generated_tests > 0
    assert record.raw_mutation_score > 0.0
    assert record.total_duration_sec > 0.0
    assert record.prompt_tokens > 0
    assert record.completion_tokens > 0
    assert record.total_tokens == record.prompt_tokens + record.completion_tokens
    assert record.actual_billed_cost_usd == 0.0


def test_evaluator_cost_calculation():
    evaluator = EndToEndPerformanceEvaluator(SAMPLE_CODE, target_name="test_discount.py")
    record = evaluator.execute_single_run(
        strategy=PromptStrategy.FEW_SHOT,
        persona=DeveloperPersona.QA_ENGINEER,
        repetition_index=1,
    )
    expected_cost = round(
        (record.prompt_tokens * GEMINI_FLASH_PROMPT_RATE_PER_1M / 1_000_000)
        + (record.completion_tokens * GEMINI_FLASH_COMPLETION_RATE_PER_1M / 1_000_000),
        6,
    )
    assert record.estimated_cost_usd == expected_cost
    assert record.is_live_call is False


def test_evaluator_react_strategy():
    evaluator = EndToEndPerformanceEvaluator(SAMPLE_CODE, target_name="test_discount.py")
    record = evaluator.execute_single_run(
        strategy=PromptStrategy.REACT,
        persona=DeveloperPersona.SECURITY_CONSCIOUS,
        repetition_index=1,
    )
    assert record.strategy == PromptStrategy.REACT
    assert record.persona == DeveloperPersona.SECURITY_CONSCIOUS
    assert record.success is True
    assert record.raw_mutation_score >= 80.0


def test_evaluator_matrix_execution():
    evaluator = EndToEndPerformanceEvaluator(SAMPLE_CODE, target_name="test_discount.py")
    # Execute a mini-matrix of 2 strategies x 2 personas x 1 repetition = 4 runs
    runs = evaluator.execute_evaluation_matrix(
        strategies=[PromptStrategy.ZERO_SHOT, PromptStrategy.FEW_SHOT],
        personas=[DeveloperPersona.BEGINNER, DeveloperPersona.EXPERIENCED],
        repetitions=1,
    )
    assert len(runs) == 4
    for r in runs:
        assert r.success is True
        assert r.total_tokens > 0
        assert r.total_duration_sec > 0.0


def test_aggregate_run_statistics():
    evaluator = EndToEndPerformanceEvaluator(SAMPLE_CODE, target_name="test_discount.py")
    runs = evaluator.execute_evaluation_matrix(
        strategies=[PromptStrategy.ZERO_SHOT, PromptStrategy.FEW_SHOT],
        personas=[DeveloperPersona.BEGINNER],
        repetitions=2,
    )
    summaries = aggregate_run_statistics(runs)
    assert len(summaries) == 2
    for s in summaries:
        assert s.total_runs == 2
        assert s.successful_runs == 2
        assert s.success_rate_pct == 100.0
        assert s.raw_mutation_score.mean > 0.0
        assert s.total_duration_sec.mean > 0.0


def test_benchmark_artifacts_integrity():
    base_dir = Path("docs/PERFORMANCE_EVALUATION")
    raw_results_file = base_dir / "BENCHMARK_RAW_RESULTS.json"
    results_csv_file = base_dir / "BENCHMARK_RESULTS.csv"
    stats_file = base_dir / "PERFORMANCE_STATISTICS.json"
    config_file = base_dir / "BENCHMARK_CONFIGURATION.json"

    assert raw_results_file.exists(), "Raw benchmark results JSON missing"
    assert results_csv_file.exists(), "Benchmark CSV results missing"
    assert stats_file.exists(), "Performance statistics JSON missing"
    assert config_file.exists(), "Benchmark configuration JSON missing"

    with open(raw_results_file) as f:
        raw_runs = json.load(f)
    assert len(raw_runs) == 60, f"Expected 60 runs, found {len(raw_runs)}"

    with open(stats_file) as f:
        stats = json.load(f)
    assert len(stats) == 12, f"Expected 12 matrix cells, found {len(stats)}"

    with open(config_file) as f:
        config = json.load(f)
    assert config["experimental_design"]["total_benchmark_runs"] == 60
    assert config["pricing_and_cost_model"]["actual_billed_api_cost_usd"] == 0.0


def test_performance_charts_exist():
    base_dir = Path("docs/PERFORMANCE_EVALUATION")
    expected_charts = [
        "mutation_score_by_prompt_architecture.png",
        "execution_time_by_prompt_architecture.png",
        "persona_performance_comparison.png",
        "estimated_cost_by_prompt_architecture.png",
        "token_consumption_by_prompt_architecture.png",
        "mutation_score_vs_runtime.png",
    ]
    for chart_name in expected_charts:
        chart_path = base_dir / chart_name
        assert chart_path.exists(), f"Expected chart missing: {chart_name}"
        assert chart_path.stat().st_size > 10_000, f"Chart file too small: {chart_name}"
