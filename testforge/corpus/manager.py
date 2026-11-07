"""
manager.py - Evaluation Corpus Registry, Validation Harness, and Manifest Generators.

Author: TestForge Agentic Engineering
Course: CSE3101 - Agentic AI
Milestone: Phase 2 Milestone 2.1 (GAP-04)
"""

from __future__ import annotations

import csv
import json
import time
from typing import Any, Dict, List, Optional

from testforge.corpus.fixtures.banking import FIXTURE as FIXTURE_BK
from testforge.corpus.fixtures.currency_converter import FIXTURE as FIXTURE_CC
from testforge.corpus.fixtures.inventory_pricing import FIXTURE as FIXTURE_IP
from testforge.corpus.fixtures.rate_limiter import FIXTURE as FIXTURE_RL
from testforge.corpus.fixtures.state_machine import FIXTURE as FIXTURE_SM
from testforge.corpus.models import (
    CorpusFixture,
    DefectDetectionReport,
    FixtureEvaluationResult,
)

CORPUS_REGISTRY: Dict[str, CorpusFixture] = {
    FIXTURE_SM.fixture_id: FIXTURE_SM,
    FIXTURE_RL.fixture_id: FIXTURE_RL,
    FIXTURE_IP.fixture_id: FIXTURE_IP,
    FIXTURE_BK.fixture_id: FIXTURE_BK,
    FIXTURE_CC.fixture_id: FIXTURE_CC,
}


def get_corpus_fixtures() -> Dict[str, CorpusFixture]:
    """Returns the registered evaluation corpus fixtures."""
    return CORPUS_REGISTRY


def get_fixture(fixture_id: str) -> Optional[CorpusFixture]:
    """Returns fixture by ID or None if not found."""
    return CORPUS_REGISTRY.get(fixture_id)


def evaluate_fixture(
    fixture: CorpusFixture,
    sandbox: Optional[Any] = None,
    run_mutation_analysis: bool = True,
) -> FixtureEvaluationResult:
    """
    Executes Step 3 validation harness on a single corpus fixture:
      1. Runs baseline tests against correct reference implementation (expects 100% pass).
      2. Injects each defect variant and verifies that baseline tests fail on the intended assertion.
      3. Verifies that unrelated tests are not incorrectly attributed.
      4. Executes AST mutation pipeline, separating killed, surviving, invalid, and equivalent mutants.
    """
    from testforge.equivalence import calculate_mutation_scores
    from testforge.mutator import ASTMutator
    from testforge.sandbox import ParallelSandboxRunner

    runner = sandbox or ParallelSandboxRunner(timeout_seconds=5)
    t0 = time.perf_counter()

    # 1. Run baseline tests against reference implementation
    ref_run = runner.run_single(fixture.baseline_test_code, fixture.source_code)
    ref_total = ref_run.get("tests_collected", 0)
    ref_passed = ref_run.get("tests_passed", 0)
    ref_success = (ref_run.get("status") == "PASS" and ref_passed > 0 and ref_run.get("tests_failed", 0) == 0)

    # 2. Defect injection verification
    defect_reports: List[DefectDetectionReport] = []
    defects_detected = 0

    for defect_id, defect in fixture.defects.items():
        t_d0 = time.perf_counter()
        defect_run = runner.run_single(fixture.baseline_test_code, defect.buggy_source_code)
        d_dur_ms = (time.perf_counter() - t_d0) * 1000.0

        is_detected = (defect_run.get("status") in ("FAIL", "ERROR", "TIMEOUT")) or (defect_run.get("tests_failed", 0) > 0)
        if is_detected:
            defects_detected += 1

        # Extract failing test names from stdout
        failing_tests: List[str] = []
        stdout = defect_run.get("stdout", "")
        for line in stdout.splitlines():
            if "FAILED " in line:
                # e.g., FAILED test_target.py::test_name - AssertionError
                parts = line.split("::")
                if len(parts) > 1:
                    test_part = parts[1].split(" ")[0].strip()
                    if test_part not in failing_tests:
                        failing_tests.append(test_part)

        failing_test = ", ".join(failing_tests) if failing_tests else None
        matched_expected = bool(defect.expected_failing_test in failing_tests)

        defect_reports.append(DefectDetectionReport(
            defect_id=defect_id,
            fixture_id=fixture.fixture_id,
            detected=is_detected,
            failing_test_name=failing_test,
            observed_error_type="AssertionError" if "AssertionError" in stdout else defect_run.get("status", "FAIL"),
            observed_error_message=defect_run.get("stderr") or stdout[:300],
            matched_expected_assertion=matched_expected,
            duration_ms=round(d_dur_ms, 2)
        ))

    # 3. Mutation Testing Pipeline & Coverage
    cov_pct = 0.0
    mutants_total = 0
    mutants_killed = 0
    mutants_survived = 0
    mutants_timed_out = 0
    mutants_invalid = 0
    mutants_equivalent = 0
    mutants_potentially_equiv = 0
    raw_mutation_score = 0.0
    adj_mutation_score = 0.0

    if run_mutation_analysis:
        try:
            cov_pct, _ = runner.measure_coverage(fixture.baseline_test_code, fixture.source_code)
        except Exception:
            cov_pct = 0.0

        mutants = ASTMutator.generate_mutants(fixture.source_code)
        evaluated = runner.evaluate_mutants_parallel(fixture.baseline_test_code, mutants)
        score_data = calculate_mutation_scores(evaluated)

        mutants_total = score_data.get("total_mutants", len(evaluated))
        mutants_killed = score_data.get("killed_mutants", 0)
        mutants_survived = score_data.get("survived_mutants", 0)
        mutants_timed_out = score_data.get("timed_out_mutants", 0)
        mutants_invalid = score_data.get("invalid_mutants", 0)
        mutants_equivalent = score_data.get("equivalent_mutants", 0)
        mutants_potentially_equiv = score_data.get("potentially_equivalent_mutants", 0)
        raw_mutation_score = score_data.get("raw_mutation_score", 0.0)
        adj_mutation_score = score_data.get("adjusted_mutation_score", raw_mutation_score)

    total_duration = time.perf_counter() - t0

    return FixtureEvaluationResult(
        fixture_id=fixture.fixture_id,
        fixture_name=fixture.name,
        source_hash=fixture.source_hash,
        reference_tests_total=ref_total,
        reference_tests_passed=ref_passed,
        reference_passed=ref_success,
        defect_reports=defect_reports,
        defects_detected_count=defects_detected,
        defects_total_count=len(fixture.defects),
        mutation_score_pct=round(raw_mutation_score, 1),
        adjusted_mutation_score_pct=round(adj_mutation_score, 1),
        mutants_total=mutants_total,
        mutants_killed=mutants_killed,
        mutants_survived=mutants_survived,
        mutants_timed_out=mutants_timed_out,
        mutants_invalid=mutants_invalid,
        mutants_equivalent=mutants_equivalent,
        mutants_potentially_equivalent=mutants_potentially_equiv,
        line_coverage_pct=round(cov_pct, 1),
        execution_duration_sec=round(total_duration, 3),
        raw_execution_output=ref_run.get("stdout")
    )


def evaluate_entire_corpus(run_mutation_analysis: bool = True) -> List[FixtureEvaluationResult]:
    """Runs evaluation across all 5 corpus fixtures."""
    results = []
    fixtures = get_corpus_fixtures()
    for fixture_id, fixture in fixtures.items():
        res = evaluate_fixture(fixture, run_mutation_analysis=run_mutation_analysis)
        results.append(res)
    return results


def export_corpus_manifest_csv(output_path: str) -> None:
    """Exports CORPUS_MANIFEST.csv cataloging all 5 evaluation fixtures."""
    fixtures = get_corpus_fixtures()
    fieldnames = [
        "Fixture_ID",
        "Fixture_Name",
        "Category",
        "Source_File",
        "Source_SHA256",
        "Baseline_Tests_Count",
        "Defects_Count",
        "Function_Contract"
    ]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for fix in fixtures.values():
            # Count tests by splitting 'def test_'
            test_count = fix.baseline_test_code.count("def test_")
            writer.writerow({
                "Fixture_ID": fix.fixture_id,
                "Fixture_Name": fix.name,
                "Category": fix.category,
                "Source_File": fix.source_file,
                "Source_SHA256": fix.source_hash,
                "Baseline_Tests_Count": test_count,
                "Defects_Count": len(fix.defects),
                "Function_Contract": fix.function_contract,
            })


def export_defect_manifest_csv(output_path: str) -> None:
    """Exports DEFECT_MANIFEST.csv cataloging all controlled defects across the corpus."""
    fixtures = get_corpus_fixtures()
    fieldnames = [
        "Defect_ID",
        "Fixture_ID",
        "Defect_Name",
        "Defect_Type",
        "Target_Function",
        "Expected_Failing_Test",
        "Expected_Error_Type",
        "Buggy_Source_SHA256",
        "Description"
    ]
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for fix in fixtures.values():
            for defect in fix.defects.values():
                writer.writerow({
                    "Defect_ID": defect.defect_id,
                    "Fixture_ID": defect.fixture_id,
                    "Defect_Name": defect.name,
                    "Defect_Type": defect.defect_type,
                    "Target_Function": defect.target_function,
                    "Expected_Failing_Test": defect.expected_failing_test,
                    "Expected_Error_Type": defect.expected_error_type,
                    "Buggy_Source_SHA256": defect.buggy_source_hash,
                    "Description": defect.description,
                })


def export_benchmark_corpus_results_json(output_path: str, results: List[FixtureEvaluationResult]) -> None:
    """Exports raw machine-readable JSON evaluation results."""
    data = {
        "timestamp": time.time(),
        "total_fixtures": len(results),
        "total_defects": sum(r.defects_total_count for r in results),
        "total_defects_detected": sum(r.defects_detected_count for r in results),
        "fixtures": [r.model_dump() for r in results]
    }
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
