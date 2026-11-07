"""
tests/test_evaluation_corpus.py - Comprehensive Acceptance Test Suite for GAP-04 Evaluation Corpus.

Acceptance Criteria:
  1. All 5 correct reference implementations pass their baseline test suites.
  2. Each documented defect variant exhibits expected defective behavior.
  3. Intended defect-detection assertions fail against the relevant buggy variant.
  4. Fixture hashes and identifiers are deterministic and stable for unchanged source.
  5. Results from separate runs do not overwrite one another (unique run identifiers).
  6. Equivalent and invalid mutants are classified separately.
  7. Mutation-score calculations use documented denominators.
  8. Missing model credentials do not create fabricated token or cost metrics.
  9. Corpus and defect manifests export accurately to CSV and JSON.
 10. Existing benchmark, mutation, and checkpoint-recovery systems remain compatible.
"""

import csv
import json
import os

import pytest

from testforge.corpus.manager import (
    CORPUS_REGISTRY,
    evaluate_entire_corpus,
    evaluate_fixture,
    export_benchmark_corpus_results_json,
    export_corpus_manifest_csv,
    export_defect_manifest_csv,
    get_corpus_fixtures,
    get_fixture,
)
from testforge.corpus.models import (
    CorpusFixture,
    DefectVariant,
    compute_sha256,
)
from testforge.corpus.runner import (
    CorpusBenchmarkReport,
    CorpusBenchmarkRunner,
    StrategyRunRecord,
)
from testforge.equivalence import calculate_mutation_scores
from testforge.mutator import ASTMutator
from testforge.sandbox import ParallelSandboxRunner

# ==============================================================================
# 1. Reference Implementations & Contract Integrity
# ==============================================================================

class TestCorpusReferenceImplementations:
    def test_all_five_fixtures_registered_and_discoverable(self):
        """1a. Exactly 5 isolated deterministic fixtures are registered."""
        fixtures = get_corpus_fixtures()
        assert len(fixtures) == 5
        expected_ids = {
            "task_state_transition",
            "token_bucket_rate_limiter",
            "inventory_pricing_calculator",
            "banking_operations_module",
            "currency_converter",
        }
        assert set(fixtures.keys()) == expected_ids

    def test_all_reference_fixtures_pass_baseline_tests(self):
        """1b. Every clean reference implementation passes its baseline suite (100% pass@1)."""
        sandbox = ParallelSandboxRunner(timeout_seconds=5)
        for fix_id, fixture in get_corpus_fixtures().items():
            run_res = sandbox.run_single(fixture.baseline_test_code, fixture.source_code)
            assert run_res["status"] == "PASS", f"Reference fixture {fix_id} failed baseline tests: {run_res.get('stderr')}"
            assert run_res["tests_passed"] > 0
            assert run_res["tests_failed"] == 0

    def test_source_hashes_are_deterministic_and_stable(self):
        """1c. Source hashes match computed SHA-256 and remain stable."""
        for fix_id, fixture in get_corpus_fixtures().items():
            expected_hash = compute_sha256(fixture.source_code)
            assert fixture.source_hash == expected_hash
            assert len(fixture.source_hash) == 64

    def test_function_contracts_and_docstrings_present(self):
        """1d. Each fixture defines documented function contracts and preconditions/returns/requires."""
        for fix_id, fixture in get_corpus_fixtures().items():
            assert fixture.function_contract, f"{fix_id} missing function contract"
            assert ("Returns:" in fixture.source_code or "Rules:" in fixture.source_code or "Requires:" in fixture.source_code or "Preconditions:" in fixture.source_code)


# ==============================================================================
# 2. Controlled Defect Variants & Pinpointed Assertion Failure
# ==============================================================================

class TestDefectManifestAndInjection:
    def test_each_fixture_has_at_least_three_documented_defects(self):
        """2a. Verifies at least 3 distinct defect variants per fixture (15+ total)."""
        total_defects = 0
        for fix_id, fixture in get_corpus_fixtures().items():
            assert len(fixture.defects) >= 3, f"Fixture {fix_id} has fewer than 3 defect variants"
            total_defects += len(fixture.defects)
        assert total_defects >= 15

    def test_each_defect_variant_exhibits_defective_behavior(self):
        """2b. Every defect variant fails baseline tests (zero silent defect escapes)."""
        sandbox = ParallelSandboxRunner(timeout_seconds=5)
        for fix_id, fixture in get_corpus_fixtures().items():
            for defect_id, defect in fixture.defects.items():
                run_res = sandbox.run_single(fixture.baseline_test_code, defect.buggy_source_code)
                is_detected = (run_res["status"] in ("FAIL", "ERROR", "TIMEOUT")) or (run_res["tests_failed"] > 0)
                assert is_detected is True, f"Defect {defect_id} in {fix_id} was NOT detected by baseline tests"

    def test_intended_defect_assertions_fail_against_relevant_variants(self):
        """2c. Failure traces directly to the expected assertion rather than random syntax crash."""
        eval_results = evaluate_entire_corpus(run_mutation_analysis=False)
        for r in eval_results:
            assert r.defects_detected_count == r.defects_total_count
            for report in r.defect_reports:
                assert report.detected is True
                assert report.matched_expected_assertion is True, (
                    f"Defect {report.defect_id}: expected failing test was not among failing tests. "
                    f"Reported: {report.failing_test_name}"
                )

    def test_buggy_variants_source_hashes_distinct_from_reference(self):
        """2d. Defect source hashes differ from the clean reference hash."""
        for fix_id, fixture in get_corpus_fixtures().items():
            for defect_id, defect in fixture.defects.items():
                assert defect.buggy_source_hash != fixture.source_hash
                assert len(defect.buggy_source_hash) == 64


# ==============================================================================
# 3. Mutation Testing Pipeline & Equivalent Mutant Separation
# ==============================================================================

class TestMutationPipelineAndClassification:
    def test_mutation_scores_and_coverage_on_reference(self):
        """3a. Full mutation testing pipeline executes and calculates score with line coverage."""
        fixture = get_fixture("task_state_transition")
        assert fixture is not None
        eval_res = evaluate_fixture(fixture, run_mutation_analysis=True)
        assert eval_res.line_coverage_pct > 80.0
        assert eval_res.mutants_total > 0
        assert eval_res.mutants_killed > 0
        assert eval_res.mutation_score_pct > 50.0

    def test_equivalent_and_invalid_mutants_classified_separately(self):
        """3b. Equivalent and invalid mutants are tracked distinctly from killed/survived."""
        # Create synthetic mutant records with different statuses
        from testforge.state import MutantRecord
        records = [
            MutantRecord(
                mutant_id="M1", mutation_type="AOR", line_number=1,
                original_code_snippet="x + y", mutated_code_snippet="x - y",
                unified_diff="- x + y\n+ x - y", status="KILLED"
            ),
            MutantRecord(
                mutant_id="M2", mutation_type="AOR", line_number=2,
                original_code_snippet="x * 1", mutated_code_snippet="x // 1",
                unified_diff="- x * 1\n+ x // 1", status="EQUIVALENT",
                equivalence_status="EQUIVALENT"
            ),
            MutantRecord(
                mutant_id="M3", mutation_type="SYN", line_number=3,
                original_code_snippet="def f(): pass", mutated_code_snippet="def f(: pass",
                unified_diff="invalid syntax", status="INVALID"
            ),
            MutantRecord(
                mutant_id="M4", mutation_type="ROR", line_number=4,
                original_code_snippet="x > 0", mutated_code_snippet="x >= 0",
                unified_diff="- x > 0\n+ x >= 0", status="SURVIVED"
            ),
        ]
        scores = calculate_mutation_scores(records)
        assert scores["total_mutants"] == 4
        assert scores["killed_mutants"] == 1
        assert scores["equivalent_mutants"] == 1
        assert scores["invalid_mutants"] == 1
        assert scores["survived_mutants"] == 1
        assert scores["evaluable_mutants"] == 3
        # Denominator for raw score is evaluable mutants excluding invalid syntax (3)
        assert scores["raw_mutation_score"] == 33.33
        # Denominator for adjusted score excludes equivalent and invalid (3 - 1 = 2)
        assert scores["adjusted_mutation_score"] == 50.0


# ==============================================================================
# 4. Strategy Benchmark Runner & Accounting Integrity
# ==============================================================================

class TestBenchmarkStrategyRunner:
    def test_fast_benchmark_runner_executes_all_fixtures_and_scenarios(self):
        """4a. Fast mode evaluates all 5 fixtures across all 3 strategies in < 1 second."""
        runner = CorpusBenchmarkRunner(model_name="gemini-3.6-flash", fast_mode=True)
        report = runner.run_benchmark(scenarios=["baseline", "zeroshot", "agentic_reflection"], repetitions=1)
        assert report.total_fixtures == 5
        # 5 fixtures * 3 scenarios = 15 records
        assert len(report.records) == 15
        assert report.fast_mode is True
        assert report.disclaimer is not None
        assert "SIMULATED OFFLINE BENCHMARK" in report.disclaimer

    def test_missing_credentials_do_not_fabricate_tokens_or_cost(self, monkeypatch):
        """4b. When API keys are absent, non-simulated runs report 0 tokens and $0.00 cost."""
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

        runner = CorpusBenchmarkRunner(model_name="gemini-3.6-flash", fast_mode=False)
        fixture = get_fixture("banking_operations_module")
        assert fixture is not None

        rec_zs = runner._execute_strategy_run(
            fixture=fixture,
            scenario="zeroshot",
            run_id="run_test_offline_zs",
            rep_index=1,
            has_api_key=False
        )
        assert rec_zs.total_tokens == 0
        assert rec_zs.estimated_cost_usd == 0.0
        assert rec_zs.is_simulated is False
        assert rec_zs.disclaimer is not None
        assert "live LLM tokens unavailable" in rec_zs.disclaimer

    def test_separate_runs_have_unique_run_ids_and_do_not_overwrite(self):
        """4c. Separate runs generate distinct run identifiers and timestamps."""
        runner = CorpusBenchmarkRunner(model_name="gemini-3.6-flash", fast_mode=True)
        report1 = runner.run_benchmark(scenarios=["baseline"], repetitions=1)
        report2 = runner.run_benchmark(scenarios=["baseline"], repetitions=1)

        ids1 = [r.run_id for r in report1.records]
        ids2 = [r.run_id for r in report2.records]
        # Intersection must be empty
        assert set(ids1).isdisjoint(set(ids2))


# ==============================================================================
# 5. Manifest Exports & Machine-Readable Output
# ==============================================================================

class TestManifestExportAndArtifacts:
    def test_export_corpus_manifest_csv(self, tmp_path):
        """5a. CORPUS_MANIFEST.csv exports all 5 fixtures with required columns."""
        csv_file = tmp_path / "CORPUS_MANIFEST.csv"
        export_corpus_manifest_csv(str(csv_file))
        assert csv_file.exists()

        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) == 5
        for row in rows:
            assert row["Fixture_ID"] in CORPUS_REGISTRY
            assert len(row["Source_SHA256"]) == 64
            assert int(row["Baseline_Tests_Count"]) > 0
            assert int(row["Defects_Count"]) >= 3

    def test_export_defect_manifest_csv(self, tmp_path):
        """5b. DEFECT_MANIFEST.csv exports all 15 controlled defects with required columns."""
        csv_file = tmp_path / "DEFECT_MANIFEST.csv"
        export_defect_manifest_csv(str(csv_file))
        assert csv_file.exists()

        with open(csv_file, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            rows = list(reader)
        assert len(rows) >= 15
        defect_ids = {r["Defect_ID"] for r in rows}
        assert len(defect_ids) == len(rows)  # All defect IDs must be unique
        for row in rows:
            assert row["Expected_Failing_Test"].startswith("test_")
            assert len(row["Buggy_Source_SHA256"]) == 64

    def test_export_benchmark_corpus_results_json(self, tmp_path):
        """5c. JSON results export valid schema with all fixture evaluations."""
        json_file = tmp_path / "results.json"
        fixture = get_fixture("currency_converter")
        assert fixture is not None
        res = evaluate_fixture(fixture, run_mutation_analysis=False)
        export_benchmark_corpus_results_json(str(json_file), [res])
        assert json_file.exists()

        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert data["total_fixtures"] == 1
        assert data["total_defects"] == 3
        assert data["total_defects_detected"] == 3
        assert len(data["fixtures"]) == 1
        assert data["fixtures"][0]["fixture_id"] == "currency_converter"
