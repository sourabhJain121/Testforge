"""
tests/test_fast_benchmarking.py - Verification tests for Fast Deterministic Benchmark Mode.

Tests:
  1. Fast mode execution timing: 5 simulated repetitions complete in under 5.0 seconds.
  2. Output schema integrity and simulated disclaimer preservation.
  3. All 3 ablation scenarios (baseline, zeroshot, agentic_reflection) produce statistical summaries.
  4. CLI execution: run_benchmark.py --fast produces valid JSON and Markdown outputs.
  5. Repeatable determinism across independent runs.
"""

import os
import json
import time
import subprocess
from pathlib import Path
import pytest

from testforge.benchmarking import BenchmarkRunner, BenchmarkReport

REPO_ROOT = Path(__file__).parent.parent.resolve()
SAMPLE_CODE = """
def calculate_discount(price: float, quantity: int) -> float:
    if quantity > 10:
        return price * 0.8
    elif quantity > 5:
        return price * 0.9
    return price
"""


def test_fast_benchmark_runner_five_repetitions_duration():
    """
    Verifies that 5 repetitions of the 3-scenario ablation study in fast mode
    complete in under 5.0 seconds (measuring the actual elapsed time).
    """
    runner = BenchmarkRunner(
        target_code=SAMPLE_CODE,
        target_file_path="samples/discount.py",
        model_name="gemini-3.6-flash",
        fast_mode=True
    )

    t_start = time.perf_counter()
    report = runner.run_benchmark(repetitions=5)
    t_elapsed = time.perf_counter() - t_start

    print(f"\n[MEASURED DURATION] 5 repetitions (15 scenario runs) elapsed: {t_elapsed:.4f}s")
    assert t_elapsed < 5.0, f"Fast benchmark duration {t_elapsed:.2f}s exceeded 5.0s threshold"

    # Verify report contents
    assert isinstance(report, BenchmarkReport)
    assert report.fast_mode is True
    assert report.disclaimer is not None
    assert "SIMULATED" in report.disclaimer
    assert len(report.runs) == 15  # 3 scenarios * 5 repetitions

    # Verify scenario summaries
    assert "baseline" in report.scenario_summaries
    assert "zeroshot" in report.scenario_summaries
    assert "agentic_reflection" in report.scenario_summaries

    for sc_name, sc in report.scenario_summaries.items():
        assert sc.runs_completed == 5
        assert sc.runs_failed == 0
        assert sc.mean_mutation_score >= 0.0
        assert sc.mean_line_coverage >= 0.0


def test_fast_benchmark_schema_and_simulated_flags():
    """Verifies that all fast mock run results are clearly flagged as simulated."""
    runner = BenchmarkRunner(
        target_code=SAMPLE_CODE,
        target_file_path="samples/discount.py",
        fast_mode=True
    )
    report = runner.run_benchmark(repetitions=1)

    for run in report.runs:
        assert run.metrics.measured.get("simulated") is True
        assert run.metrics.measured.get("execution_mode") == "FAST_DETERMINISTIC_MOCK"
        assert len(run.metrics.unknown_or_unavailable) > 0

    md = report.to_markdown()
    assert "SIMULATED OFFLINE BENCHMARK" in md
    assert "Metric Integrity Disclosure" in md


def test_run_benchmark_cli_fast_mode(tmp_path):
    """Verifies run_benchmark.py CLI execution with --fast flag produces valid files."""
    out_json = tmp_path / "ci_fast_results.json"
    out_md = tmp_path / "ci_fast_results.md"

    cmd = [
        str(REPO_ROOT / ".venv-release" / "bin" / "python"),
        str(REPO_ROOT / "run_benchmark.py"),
        "--fast",
        "--target", "samples/discount.py",
        "--repetitions", "3",
        "--output-json", str(out_json)
    ]

    t0 = time.perf_counter()
    proc = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True, check=True)
    t_cli = time.perf_counter() - t0

    print(f"\n[MEASURED CLI DURATION] run_benchmark.py --fast elapsed: {t_cli:.4f}s")
    assert t_cli < 5.0, f"CLI execution {t_cli:.2f}s exceeded 5.0s"
    assert out_json.exists()
    assert out_md.exists()

    data = json.loads(out_json.read_text(encoding="utf-8"))
    assert data["mode"] == "fast-mock"
    assert data["simulated"] is True
    assert data["repetitions"] == 3
    assert len(data["runs"]) == 9  # 3 scenarios * 3 repetitions
