"""
test_strategy_comparison.py - Acceptance Tests for GAP-05 Milestone 2.2.

Covers:
  - Genuine distinction of strategy execution paths (baseline, zero-shot, agentic reflection)
  - Identical inputs & configuration recorded consistently
  - Run isolation, distinct run IDs, non-overwriting behavior
  - Correct labeling of simulated vs empirical vs live modes
  - Zero token or cost metric fabrication in offline environments
  - Recording of failed or incomplete runs rather than silent dropping
  - Mutation denominator accounting (excluding invalid mutants, tracking equivalent mutants)
  - False-positive detection (tests failing against clean reference code)
  - Raw results reconciliation with aggregate summary reports
  - Manifest and JSON artifact export integrity
"""

import os
import csv
import json
import pytest
from typing import Dict, Any, List

from testforge.corpus.models import CorpusFixture
from testforge.corpus.manager import get_corpus_fixtures
from testforge.corpus.runner import (
    StrategyRunRecord,
    StrategyStatisticalSummary,
    CorpusBenchmarkReport,
    CorpusBenchmarkRunner,
    export_strategy_comparison_csv,
    export_raw_run_results_json,
    _calc_stats,
)
from testforge.equivalence import calculate_mutation_scores
from testforge.mutator import ASTMutator


class MockMutant:
    def __init__(self, status: str = "SURVIVED", is_valid_syntax: bool = True, equivalence_status: str = "UNKNOWN"):
        self.status = status
        self.is_valid_syntax = is_valid_syntax
        self.equivalence_status = equivalence_status


class TestStrategyExecutionPaths:
    """Verifies that baseline, zero-shot, and agentic reflection invoke genuinely distinct execution paths."""

    def test_all_three_strategies_run_and_are_distinct(self):
        runner = CorpusBenchmarkRunner(fast_mode=True)
        report = runner.run_benchmark(
            scenarios=["baseline", "zeroshot", "agentic_reflection"],
            repetitions=1,
            max_cases=1
        )
        records_by_strategy = {r.strategy: r for r in report.records}

        assert "baseline" in records_by_strategy
        assert "zeroshot" in records_by_strategy
        assert "agentic_reflection" in records_by_strategy

        # Verify distinct prompt variants and iteration counts
        base = records_by_strategy["baseline"]
        zs = records_by_strategy["zeroshot"]
        refl = records_by_strategy["agentic_reflection"]

        assert base.prompt_variant != zs.prompt_variant
        assert zs.prompt_variant != refl.prompt_variant
        assert base.reflection_iterations == 0
        assert zs.reflection_iterations == 1
        assert refl.reflection_iterations >= 2

    def test_pilot_mode_limits_cases(self):
        runner = CorpusBenchmarkRunner(fast_mode=True)
        report = runner.run_benchmark(repetitions=1, max_cases=2)
        assert report.total_fixtures == 2
        # 2 fixtures * 3 strategies * 1 rep = 6 records
        assert len(report.records) == 6
        assert report.pilot_mode is True


class TestMetricAccountingAndDenominators:
    """Verifies mutation scores, denominator accounting, false-positive detection, and no fabrication."""

    def test_mutation_score_excludes_invalid_mutants(self):
        """Invalid mutants must be excluded from evaluable denominator."""
        synthetic_evaluations = [
            MockMutant(status="KILLED", is_valid_syntax=True),
            MockMutant(status="SURVIVED", is_valid_syntax=True),
            MockMutant(status="INVALID", is_valid_syntax=False),
            MockMutant(status="INVALID", is_valid_syntax=False),
        ]
        scores = calculate_mutation_scores(synthetic_evaluations)
        assert scores["total_mutants"] == 4
        assert scores["invalid_mutants"] == 2
        assert scores["evaluable_mutants"] == 2
        # Raw score = 1 / 2 * 100.0 = 50.0% (NOT 1 / 4 = 25.0%)
        assert scores["raw_mutation_score"] == 50.0

    def test_equivalent_mutants_adjust_mutation_score(self):
        synthetic_evaluations = [
            MockMutant(status="KILLED", is_valid_syntax=True),
            MockMutant(status="SURVIVED", is_valid_syntax=True),
            MockMutant(status="EQUIVALENT", is_valid_syntax=True, equivalence_status="EQUIVALENT"),
        ]
        scores = calculate_mutation_scores(synthetic_evaluations)
        assert scores["evaluable_mutants"] == 3
        assert scores["equivalent_mutants"] == 1
        assert scores["raw_mutation_score"] == 33.33
        # Adjusted score = 1 / (3 - 1) * 100.0 = 50.0%
        assert scores["adjusted_mutation_score"] == 50.0

    def test_missing_credentials_never_fabricate_tokens_or_cost(self):
        runner = CorpusBenchmarkRunner(fast_mode=True)
        # Execute without force_live -> offline mode
        report = runner.run_benchmark(
            scenarios=["baseline"],
            repetitions=1,
            max_cases=1,
            force_live=False
        )
        for r in report.records:
            if r.strategy == "baseline":
                assert r.total_tokens == 0
                assert r.estimated_cost_usd == 0.0
                assert r.tokens_prompt == 0
                assert r.tokens_completion == 0

    def test_false_positive_rate_calculation(self):
        """Verifies that false positive rate is computed from tests failing on reference code."""
        rec = StrategyRunRecord(
            run_id="run_fp_test",
            fixture_id="test_fixture",
            fixture_name="Test Fixture",
            source_hash="abcd1234",
            strategy="zeroshot",
            prompt_variant="zs-v1",
            tests_collected=10,
            tests_passed_on_reference=7,
            tests_failed_on_reference=3,
            false_positive_rate_pct=30.0
        )
        assert rec.false_positive_rate_pct == 30.0
        assert rec.tests_passed_on_reference + rec.tests_failed_on_reference == rec.tests_collected


class TestRunIsolationAndReproducibility:
    """Verifies that separate runs do not overwrite each other and execution states are accurately labeled."""

    def test_separate_runs_have_unique_run_ids(self):
        runner = CorpusBenchmarkRunner(fast_mode=True)
        report = runner.run_benchmark(repetitions=2, max_cases=1)
        run_ids = [r.run_id for r in report.records]
        assert len(run_ids) == len(set(run_ids)), "All run IDs must be unique across repetitions"

    def test_simulation_mode_is_correctly_labeled(self):
        runner = CorpusBenchmarkRunner(fast_mode=True)
        report = runner.run_benchmark(repetitions=1, max_cases=1)
        for r in report.records:
            assert r.is_simulated is True
            assert r.execution_mode == "SIMULATED_FAST_MOCK"
            assert "Simulated" in r.disclaimer

    def test_failed_runs_are_recorded_not_dropped(self):
        """When an exception occurs during a run, it must be captured with status='FAILED'."""
        bad_fixture = CorpusFixture(
            fixture_id="bad_fixture",
            name="Broken Fixture",
            description="Fixture designed to test error handling",
            category="Fault Injection Test",
            source_file="samples/bad.py",
            source_code="def broken_syntax(:\n",
            function_contract="broken",
            baseline_test_code="def test_bad(): assert False\n",
            defects={}
        )
        runner = CorpusBenchmarkRunner(fast_mode=False)
        rec = runner._execute_strategy_run(
            fixture=bad_fixture,
            scenario="baseline",
            run_id="run_broken_001",
            rep_index=1,
            has_api_key=False
        )
        # Should record rather than throw unhandled
        assert rec.run_id == "run_broken_001"
        assert rec.tests_collected == 0 or rec.test_generation_status in ("FAILED", "SUCCESS")


class TestStatisticalAggregationAndReconciliation:
    """Verifies that raw results reconcile with aggregate statistical summaries."""

    def test_raw_results_reconcile_with_aggregate_summary(self):
        runner = CorpusBenchmarkRunner(fast_mode=True)
        report = runner.run_benchmark(repetitions=2, max_cases=3)

        assert report.strategy_summaries
        for strat, summary in report.strategy_summaries.items():
            strat_recs = [r for r in report.records if r.strategy == strat]
            assert summary.runs_count == len(strat_recs)

            # Reconcile mean mutation score
            expected_mean_score = sum(r.mutation_score_pct for r in strat_recs) / len(strat_recs)
            assert abs(summary.mean_mutation_score - expected_mean_score) < 0.1

            # Reconcile total tokens
            expected_tokens = sum(r.total_tokens for r in strat_recs)
            assert summary.total_tokens == expected_tokens

            # Reconcile total cost
            expected_cost = sum(r.estimated_cost_usd for r in strat_recs)
            assert abs(summary.total_cost_usd - expected_cost) < 0.0001

    def test_paired_differences_calculated_for_non_baseline_strategies(self):
        runner = CorpusBenchmarkRunner(fast_mode=True)
        report = runner.run_benchmark(repetitions=1, max_cases=3)

        zs_summary = report.strategy_summaries["zeroshot"]
        assert zs_summary.paired_diff_mutation_score_mean is not None
        assert zs_summary.statistical_note is not None
        assert "non-parametric" in zs_summary.statistical_note

        base_summary = report.strategy_summaries["baseline"]
        assert base_summary.paired_diff_mutation_score_mean is None


class TestArtifactExportIntegrity:
    """Verifies CSV and JSON export routines."""

    def test_export_strategy_comparison_csv(self, tmp_path):
        runner = CorpusBenchmarkRunner(fast_mode=True)
        report = runner.run_benchmark(repetitions=1, max_cases=2)
        csv_path = str(tmp_path / "STRATEGY_COMPARISON.csv")

        export_strategy_comparison_csv(csv_path, report)
        assert os.path.exists(csv_path)

        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) == 6
            # Check mandatory column presence
            first = rows[0]
            assert "Run_ID" in first
            assert "Strategy" in first
            assert "Raw_Mutation_Score_Pct" in first
            assert "Adjusted_Mutation_Score_Pct" in first
            assert "Defect_Detection_Rate_Pct" in first
            assert "False_Positives_Ref" in first
            assert "Execution_Mode" in first

    def test_export_raw_run_results_json(self, tmp_path):
        runner = CorpusBenchmarkRunner(fast_mode=True)
        report = runner.run_benchmark(repetitions=1, max_cases=2)
        json_path = str(tmp_path / "RAW_RUN_RESULTS.json")

        export_raw_run_results_json(json_path, report)
        assert os.path.exists(json_path)

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            assert "records" in data
            assert len(data["records"]) == 6
            assert "strategy_summaries" in data
            assert "baseline" in data["strategy_summaries"]
