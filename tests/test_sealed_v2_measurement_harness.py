"""
tests/test_sealed_v2_measurement_harness.py

Unit and regression tests for Sealed V2 measurement harness integrity:
1. Invalid suite handling (fails against clean target code -> INVALID_SUITE, 0 kills)
2. Coverage disambiguation (single target metrics, no statement doubling from aliases)
3. Kill reason classification (ASSERTION_FAIL vs EXCEPTION_FAIL vs TIMEOUT vs IMPORT_OR_SYNTAX_ERROR)
4. Uncovered mutant consistency check (mutants on unreached lines cannot be counted as killed)
"""

import pytest
from testforge.benchmarking import BenchmarkRunner, SuiteEvaluationResult
from testforge.mutator import ASTMutator, MutantRecord
from testforge.sandbox import ParallelSandboxRunner, parse_pytest_output


def test_invalid_suite_clean_reference_failure():
    """A suite that fails on clean code must be marked INVALID_SUITE with 0 kills."""
    target_code = "def add(a, b): return a + b\n"
    # Broken test that fails against clean code:
    failing_test_code = "from target import add\ndef test_add(): assert add(1, 2) == 999\n"

    runner = BenchmarkRunner(target_code=target_code)
    eval_res = runner.evaluate_suite(failing_test_code)

    assert eval_res.baseline_passed is False
    assert eval_res.invalid_suite is True
    assert eval_res.killed == 0
    assert eval_res.score == 0.0


def test_coverage_disambiguation_no_statement_doubling():
    """Ensure target coverage uses single target file statements, not inflated alias totals."""
    target_code = """def calc(x):\n    if x > 0:\n        return x * 2\n    return 0\n"""
    test_code = "from target import calc\ndef test_calc(): assert calc(5) == 10\n"

    sandbox = ParallelSandboxRunner(timeout_seconds=5)
    pct, cov_info = sandbox.measure_coverage(test_code, target_code, target_file_path="samples/discount.py")

    assert cov_info["baseline_passed"] is True
    # Target code has 4 statements, calc(5) executes 3 statements (def, if, return x*2) = 75%
    assert cov_info["num_statements"] == 4
    assert cov_info["covered_lines"] == 3
    assert cov_info["line_coverage_pct"] == 75.0
    assert len(cov_info["executed_lines"]) == 3


def test_parse_pytest_output_kill_classification():
    """Distinguish ASSERTION_FAIL, EXCEPTION_FAIL, TIMEOUT, and IMPORT_OR_SYNTAX_ERROR."""
    # 1. Assertion failure
    stdout_assert = "collected 1 item\nFAILED test_foo.py::test_1 - AssertionError: assert 1 == 2\n1 failed in 0.05s"
    res1 = parse_pytest_output(stdout_assert, "", 1)
    assert res1["status"] == "FAIL"
    assert res1["failure_type"] == "ASSERTION_FAIL"

    # 2. Target runtime exception
    stdout_exc = "collected 1 item\nFAILED test_foo.py::test_1 - ZeroDivisionError: division by zero\n1 failed in 0.05s"
    res2 = parse_pytest_output(stdout_exc, "", 1)
    assert res2["status"] == "FAIL"
    assert res2["failure_type"] == "EXCEPTION_FAIL"

    # 3. Timeout
    res3 = parse_pytest_output("", "timed out", -1)
    assert res3["status"] == "TIMEOUT"
    assert res3["failure_type"] == "TIMEOUT"

    # 4. Import / Syntax error
    res4 = parse_pytest_output("", "SyntaxError: invalid syntax", 2)
    assert res4["status"] == "ERROR"
    assert res4["failure_type"] == "IMPORT_OR_SYNTAX_ERROR"

    # 5. Clean pass
    stdout_pass = "collected 1 item\n1 passed in 0.02s"
    res5 = parse_pytest_output(stdout_pass, "", 0)
    assert res5["status"] == "PASS"
    assert res5["failure_type"] == "SURVIVED"


def test_uncovered_line_mutant_cannot_be_killed():
    """If a mutant is located on an uncovered line, it cannot count as killed."""
    sandbox = ParallelSandboxRunner(timeout_seconds=5)
    mutant = MutantRecord(
        mutant_id="MUT_01",
        mutation_type="AOR",
        line_number=99,  # Line 99 is NOT executed
        original_code_snippet="a + b",
        mutated_code_snippet="a - b",
        unified_diff=""
    )

    # Covered lines only contains lines 1, 2, 3
    evaluated = sandbox.evaluate_mutants_parallel(
        test_code="def test_dummy(): assert True\n",
        mutants=[mutant],
        baseline_passed=True,
        covered_lines=[1, 2, 3]
    )

    assert evaluated[0].status == "SURVIVED"
    assert evaluated[0].kill_classification == "UNCOVERED"
    assert "uncovered line" in evaluated[0].equivalence_reason


def test_bisect_algo_sequence_inference_and_measurement():
    """Verify bisect_algo sequence parameter inference, clean-code preflight, and >0% mutation score."""
    from testforge.intelligent_generator import IntelligentASTSynthesizer
    with open("samples/sealed_v2/bisect_algo.py", "r", encoding="utf-8") as f:
        src = f.read()

    synth = IntelligentASTSynthesizer().synthesize_test_suite(src)
    assert synth.total_test_count > 0

    runner = BenchmarkRunner(target_code=src, target_file_path="samples/sealed_v2/bisect_algo.py")
    res = runner.evaluate_suite(synth.test_code)

    assert res.baseline_passed is True, "bisect_algo must pass clean reference preflight (Pass@1 == 100%)"
    assert res.invalid_suite is False
    assert res.score > 0.0, f"bisect_algo must achieve > 0% mutation score, got {res.score}%"
    assert res.killed > 0


def test_lru_cache_stateful_lifecycle_synthesis():
    """Verify stateful class lifecycle generation for LRUCache."""
    from testforge.intelligent_generator import IntelligentASTSynthesizer
    with open("samples/lru_cache.py", "r", encoding="utf-8") as f:
        src = f.read()

    synth = IntelligentASTSynthesizer().synthesize_test_suite(src)
    assert "test_lrucache_lifecycle_eviction" in synth.test_code
    assert "test_lrucache_key_replacement" in synth.test_code

    runner = BenchmarkRunner(target_code=src, target_file_path="samples/lru_cache.py")
    res = runner.evaluate_suite(synth.test_code)

    assert res.baseline_passed is True, "LRUCache must pass clean reference preflight (Pass@1 == 100%)"
    assert res.invalid_suite is False
    assert res.score > 0.0, f"LRUCache must achieve > 0% mutation score, got {res.score}%"
    assert res.killed > 0

