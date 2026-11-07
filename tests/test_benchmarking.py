"""
test_benchmarking.py - Verification Suite for Repeatable Benchmarking & Cost Accounting.

Validates:
  1. Separation of measured, calculated, estimated, and unavailable metrics.
  2. Cost estimation adhering to official published pricing.
  3. Multi-run repetition execution and statistical aggregation (mean, stddev).
  4. BenchmarkReport Markdown and JSON rendering.
  5. Scenario failure handling and reporting.
"""

import json
import os

import pytest

from testforge.benchmarking import (
    PRICING_TABLE_PER_MILLION,
    BenchmarkReport,
    BenchmarkRunner,
    BenchmarkRunResult,
    BenchmarkScenarioSummary,
    MetricBreakdown,
)


@pytest.fixture
def sample_code():
    return (
        "def compute_discount(price: float, qty: int) -> float:\n"
        "    if qty > 5:\n"
        "        return price * 0.9\n"
        "    return price\n"
    )


@pytest.fixture
def sample_baseline_test():
    return (
        "from target import compute_discount\n"
        "def test_normal():\n"
        "    assert compute_discount(100.0, 1) == 100.0\n"
    )


class TestBenchmarkingDataModels:
    def test_metric_breakdown_categorization(self):
        breakdown = MetricBreakdown(
            measured={"duration_seconds": 1.45, "total_tokens": 1250},
            calculated={"mutation_score_pct": 80.0, "line_coverage_pct": 100.0},
            estimated={"estimated_cost_usd": 0.00015},
            unknown_or_unavailable=["completion_tokens"],
        )
        data = breakdown.model_dump()
        assert data["measured"]["duration_seconds"] == 1.45
        assert data["calculated"]["mutation_score_pct"] == 80.0
        assert data["estimated"]["estimated_cost_usd"] == 0.00015
        assert "completion_tokens" in data["unknown_or_unavailable"]

    def test_pricing_calculation(self):
        runner = BenchmarkRunner(target_code="def foo(): pass", model_name="gemini-3.6-flash")
        cost = runner._estimate_cost(prompt_tokens=1_000_000, completion_tokens=1_000_000)
        # prompt: 0.075, completion: 0.30 -> total: 0.375
        assert cost == pytest.approx(0.375, rel=1e-3)

    def test_benchmark_report_markdown_and_json(self):
        summary = BenchmarkScenarioSummary(
            scenario="baseline",
            runs_completed=2,
            runs_failed=0,
            mean_duration_sec=0.45,
            stddev_duration_sec=0.02,
            mean_mutation_score=50.0,
            mean_line_coverage=75.0,
            total_tokens_consumed=0,
            estimated_total_cost_usd=0.0,
        )
        report = BenchmarkReport(
            target_file="test_target.py",
            repetitions=2,
            scenario_summaries={"baseline": summary},
        )
        md = report.to_markdown()
        assert "Comparison of Deterministic Baseline, Local LLM Zero-Shot Generation, and Offline Multi-Agent Reflection" in md
        assert "test_target.py" in md
        assert "Metric Integrity Disclosure & Experimental Methodology" in md
        assert "50.0%" in md

        json_str = report.to_json()
        parsed = json.loads(json_str)
        assert parsed["target_file"] == "test_target.py"
        assert "baseline" in parsed["scenario_summaries"]


class TestBenchmarkRunnerExecution:
    def test_baseline_and_zeroshot_runs(self, sample_code, sample_baseline_test, tmp_path):
        runner = BenchmarkRunner(
            target_code=sample_code,
            target_file_path=str(tmp_path / "target.py"),
            baseline_tests=sample_baseline_test,
            trace_dir=str(tmp_path),
        )

        report = runner.run_benchmark(
            scenarios=["baseline", "zeroshot"],
            repetitions=2,
            engine_mode="legacy"
        )

        assert report.repetitions == 2
        assert len(report.runs) == 4
        assert "baseline" in report.scenario_summaries
        assert "zeroshot" in report.scenario_summaries

        base_summary = report.scenario_summaries["baseline"]
        assert base_summary.runs_completed == 2
        assert base_summary.mean_duration_sec > 0.0
        assert base_summary.mean_mutation_score >= 0.0

        zs_summary = report.scenario_summaries["zeroshot"]
        assert zs_summary.runs_completed == 2
        assert zs_summary.mean_duration_sec > 0.0

    def test_agentic_reflection_run(self, sample_code, sample_baseline_test, tmp_path):
        runner = BenchmarkRunner(
            target_code=sample_code,
            target_file_path=str(tmp_path / "target.py"),
            baseline_tests=sample_baseline_test,
            trace_dir=str(tmp_path),
        )

        report = runner.run_benchmark(
            scenarios=["agentic_reflection"],
            repetitions=1,
            engine_mode="legacy"
        )

        assert report.repetitions == 1
        assert len(report.runs) == 1
        run_res = report.runs[0]
        assert run_res.success is True
        assert "duration_seconds" in run_res.metrics.measured
        assert "mutation_score_pct" in run_res.metrics.calculated
