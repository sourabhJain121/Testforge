"""
test_multi_target_benchmarking.py - Verification Suite for GAP-009 Multi-Target Benchmark Suite.

Validates:
1. Four diverse target modules exist and compile cleanly into ASTs:
   - samples/discount.py (Pricing calculations & business boundaries)
   - samples/lru_cache.py (Data structures & state mutation)
   - samples/order_fsm.py (Finite state machine & transition guards)
   - samples/stats_calculator.py (Numerical statistics & Bessel correction)
2. MultiTargetBenchmarkRunner execution across all 4 targets with metric aggregation.
3. Branch coverage (GAP-003) and equivalent mutant recalibration (GAP-006) tracking.
4. Cross-target statistical aggregation (arithmetic mean, geometric mean, relative delta).
5. Machine-readable JSON and publication-ready Markdown summary generation.
6. REST API endpoints:
   - GET /api/benchmark/multi-target/summary
   - POST /api/benchmark/multi-target/run
"""

from __future__ import annotations
import os
import ast
import json
import pytest
from starlette.testclient import TestClient

from testforge.benchmarking import (
    CANONICAL_TARGET_MODULES,
    MultiTargetBenchmarkRunner,
    run_multi_target_benchmark,
    generate_markdown_benchmark_summary,
    _arithmetic_mean,
    _geometric_mean,
)
from server import app


class TestTargetModulesSetup:
    """Verifies that all 4 diverse benchmark modules are present and valid."""
    __test__ = True

    def test_canonical_target_modules_count(self):
        assert len(CANONICAL_TARGET_MODULES) == 4
        expected_modules = {
            "samples/discount.py",
            "samples/lru_cache.py",
            "samples/order_fsm.py",
            "samples/stats_calculator.py",
        }
        assert set(CANONICAL_TARGET_MODULES) == expected_modules

    def test_all_targets_exist_and_compile(self):
        for path in CANONICAL_TARGET_MODULES:
            assert os.path.exists(path), f"Canonical target not found on disk: {path}"
            with open(path, "r", encoding="utf-8") as f:
                code = f.read()
            tree = ast.parse(code)
            assert tree is not None
            non_comment_loc = len([l for l in code.splitlines() if l.strip() and not l.strip().startswith("#")])
            assert non_comment_loc >= 15, f"{path} LOC too low: {non_comment_loc}"


class TestMultiTargetBenchmarkExecution:
    """Verifies multi-target benchmark execution and statistical aggregation."""
    __test__ = True

    def test_arithmetic_and_geometric_mean_helpers(self):
        values = [10.0, 20.0, 40.0]
        # Arithmetic mean: (10 + 20 + 40) / 3 = 23.33
        assert _arithmetic_mean(values) == pytest.approx(23.33, rel=1e-2)
        # Geometric mean: (10 * 20 * 40)^(1/3) = 8000^(1/3) = 20.0
        assert _geometric_mean(values) == pytest.approx(20.0, rel=1e-2)

        # Empty handling
        assert _arithmetic_mean([]) == 0.0
        assert _geometric_mean([]) == 0.0

    def test_multi_target_runner_fast_execution(self, tmp_path):
        runner = MultiTargetBenchmarkRunner(
            target_modules=list(CANONICAL_TARGET_MODULES),
            scenarios=["baseline", "zeroshot", "agentic_reflection"],
            repetitions=1,
            fast_mode=True,
            output_dir=str(tmp_path),
        )
        results = runner.run()

        # Structural assertions
        assert "targets" in results
        assert "cross_target_summary" in results
        assert len(results["targets"]) == 4

        # Verify each target module has valid measurements
        for target_path in CANONICAL_TARGET_MODULES:
            assert target_path in results["targets"]
            t_data = results["targets"][target_path]
            assert t_data["loc"] > 0
            assert t_data["total_mutants"] > 0
            assert len(t_data["operator_diversity"]) >= 3
            assert t_data["discovered_callables"] >= 1

            scs = t_data["scenarios"]
            for s in ("baseline", "zeroshot", "agentic_reflection"):
                assert s in scs
                assert scs[s]["line_coverage_pct"] > 0.0
                assert scs[s]["branch_coverage_pct"] > 0.0
                assert scs[s]["raw_mutation_score"] is not None

        # Verify Cross-Target Aggregation
        summary = results["cross_target_summary"]
        assert "scenarios" in summary
        assert "relative_gains" in summary
        assert "baseline" in summary["scenarios"]
        assert "agentic_reflection" in summary["scenarios"]

        base_summary = summary["scenarios"]["baseline"]
        refl_summary = summary["scenarios"]["agentic_reflection"]

        assert base_summary["arithmetic_mean_line_coverage"] > 0.0
        assert base_summary["arithmetic_mean_branch_coverage"] > 0.0
        assert base_summary["geometric_mean_branch_coverage"] > 0.0

        # Reflection should outperform baseline in mutation score and branch coverage
        assert refl_summary["arithmetic_mean_raw_mutation_score"] > base_summary["arithmetic_mean_raw_mutation_score"]
        assert refl_summary["arithmetic_mean_branch_coverage"] >= base_summary["arithmetic_mean_branch_coverage"]

        # Output artifact generation
        assert os.path.exists(results["saved_json_path"])
        assert os.path.exists(results["saved_markdown_path"])

        # Check JSON loadability
        with open(results["saved_json_path"], "r", encoding="utf-8") as jf:
            loaded_json = json.load(jf)
        assert len(loaded_json["targets"]) == 4

    def test_markdown_summary_generation(self, tmp_path):
        results = run_multi_target_benchmark(
            target_modules=list(CANONICAL_TARGET_MODULES),
            scenarios=["baseline", "zeroshot", "agentic_reflection"],
            repetitions=1,
            fast_mode=True,
            output_dir=str(tmp_path),
        )
        md = generate_markdown_benchmark_summary(results)

        # Markdown header & table checks
        assert "# TestForge Multi-Target Empirical Benchmark Evaluation Matrix" in md
        assert "Target Modules Characterization & Mutation Space" in md
        assert "Multi-Scenario Empirical Performance Scorecard" in md
        assert "Cross-Target Statistical Aggregation (GAP-009)" in md
        assert "discount.py" in md
        assert "lru_cache.py" in md
        assert "order_fsm.py" in md
        assert "stats_calculator.py" in md
        assert "Arithmetic Mean Line Coverage" in md
        assert "Geometric Mean Branch Coverage" in md
        assert "Arithmetic Mean Raw Mutation Score" in md


class TestBenchmarkRESTEndpoints:
    """Verifies FastAPI REST endpoints for multi-target benchmarking."""
    __test__ = True

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_get_multi_target_summary_endpoint(self, client):
        response = client.get("/api/benchmark/multi-target/summary")
        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "SUCCESS"
        assert "results" in payload
        assert "targets" in payload["results"]
        assert "cross_target_summary" in payload["results"]

    def test_post_multi_target_run_endpoint_fast(self, client):
        req_body = {
            "target_modules": ["samples/discount.py", "samples/lru_cache.py"],
            "scenarios": ["baseline", "zeroshot"],
            "repetitions": 1,
            "fast_mode": True,
        }
        response = client.post("/api/benchmark/multi-target/run", json=req_body)
        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "SUCCESS"
        assert "results" in payload
        assert len(payload["results"]["targets"]) == 2


class TestBenchmarkArithmeticAndRawCounts:
    """Verifies Task 2 arithmetic integrity, unrounded raw count aggregation, and baseline configs."""

    def test_recomputed_geometric_mean_resolves_discrepancy(self):
        from testforge.benchmarking import compute_raw_unrounded_means, _geometric_mean, _arithmetic_mean

        # Per-target historical baselines:
        # discount: 1/19 (5.2632%), lru_cache: 3/25 (12.0%), order_fsm: 7/82 (8.5366%), stats: 5/34 (14.7059%)
        raw_counts = [(1, 19), (3, 25), (7, 82), (5, 34)]
        am, gm = compute_raw_unrounded_means(raw_counts)

        # Unrounded geometric mean evaluates to 9.44%, NOT the erroneous 9.62% reported earlier
        assert gm == pytest.approx(9.44, rel=1e-2)
        assert am == pytest.approx(10.13, rel=1e-2)
        assert gm != 9.62
        assert abs(gm - 9.62) > 0.15

        # Recomputed from explicit rounded percentage values [5.26, 12.00, 8.54, 14.71]
        rounded_vals = [5.26, 12.00, 8.54, 14.71]
        gm_from_rounded = _geometric_mean(rounded_vals)
        am_from_rounded = _arithmetic_mean(rounded_vals)
        assert gm_from_rounded == pytest.approx(9.44, rel=1e-2)
        assert am_from_rounded == pytest.approx(10.13, rel=1e-2)

    def test_raw_counts_and_preliminary_status_in_results(self, tmp_path):
        runner = MultiTargetBenchmarkRunner(
            target_modules=["samples/discount.py", "samples/lru_cache.py"],
            scenarios=["baseline", "zeroshot"],
            repetitions=1,
            fast_mode=True,
            output_dir=str(tmp_path),
        )
        res = runner.run()

        # Check raw counts presence
        for mod_path in ["samples/discount.py", "samples/lru_cache.py"]:
            t_data = res["targets"][mod_path]
            for sc in ["baseline", "zeroshot"]:
                sc_data = t_data["scenarios"][sc]
                assert "killed_mutants" in sc_data
                assert "total_mutants" in sc_data
                assert "survived_mutants" in sc_data
                assert "equivalent_mutants" in sc_data
                assert sc_data["run_status"] == "PRELIMINARY (n=1)"

        cross = res["cross_target_summary"]["scenarios"]
        assert cross["baseline"]["run_status"] == "PRELIMINARY (n=1)"
        assert "total_killed_mutants" in cross["baseline"]
        assert "total_mutants" in cross["baseline"]


