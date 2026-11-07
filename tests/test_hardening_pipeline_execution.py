"""
test_hardening_pipeline_execution.py - Comprehensive End-to-End Regression Tests for Hardening Pipeline.

Verifies:
1. Valid Python file with one simple function executes and hardens cleanly.
2. Python file with multiple functions discovers callables and runs baseline.
3. Python file containing conditional branches generates branch mutants and evaluates.
4. Python file with boundary conditions extracts comparison vectors.
5. Python file with intentional syntax error safely reports failure without crashes.
6. Python file with an import error cleanly records EXECUTION_ERROR (not false baseline pass).
7. Python file with empty/unsupported target returns honest failure verdict.
8. Generated test suite is discoverable by Pytest.
9. Baseline test suite executes successfully when target is clean.
10. Baseline test suite that genuinely fails reports FAILED_BASELINE with actual errors.
11. Mutation evaluation generates and executes mutants, calculating raw and adjusted scores.
12. Pipeline distinguishes test generation, execution, and mutation evaluation failures.
"""

import os
import sys
import tempfile
from unittest import mock

import pytest

from testforge.equivalence import calculate_mutation_scores
from testforge.mutator import ASTMutator
from testforge.orchestrator import TestForgeOrchestrator
from testforge.sandbox import ParallelSandboxRunner, _run_single_test_task
from testforge.state import MutantRecord


class TestHardeningPipelineExecution:
    """Verifies complete failure-mode isolation and successful execution pathways."""

    def test_01_single_simple_function(self, tmp_path):
        """Scenario 1: Valid Python file with one simple function."""
        code = "def square(x: int) -> int:\n    return x * x\n"
        f = tmp_path / "simple.py"
        f.write_text(code)

        orch = TestForgeOrchestrator(
            target_source_code=code,
            target_file_path=str(f),
            max_iterations=1,
            engine_mode="legacy"
        )
        state = orch.run()
        assert state.baseline_tests_generated > 0
        assert state.baseline_tests_executed > 0
        assert state.baseline_passed is True
        assert state.baseline_tests_passed > 0
        assert state.final_hardening_status in ("TARGET_ACHIEVED", "TARGET_SCORE_UNREACHED")
        assert state.final_mutation_score is not None

    def test_02_multiple_functions(self, tmp_path):
        """Scenario 2: Python file with multiple functions."""
        code = (
            "def add(a: int, b: int) -> int:\n"
            "    return a + b\n\n"
            "def multiply(a: int, b: int) -> int:\n"
            "    return a * b\n"
        )
        f = tmp_path / "multi.py"
        f.write_text(code)

        orch = TestForgeOrchestrator(
            target_source_code=code,
            target_file_path=str(f),
            max_iterations=1,
            engine_mode="legacy"
        )
        state = orch.run()
        assert state.baseline_tests_generated >= 2
        assert state.baseline_tests_executed >= 2
        assert state.baseline_passed is True

    def test_03_conditional_branches(self, tmp_path):
        """Scenario 3: Python file containing conditional branches."""
        code = (
            "def classify_number(n: int) -> str:\n"
            "    if n > 0:\n"
            "        return 'positive'\n"
            "    elif n < 0:\n"
            "        return 'negative'\n"
            "    return 'zero'\n"
        )
        f = tmp_path / "branches.py"
        f.write_text(code)

        orch = TestForgeOrchestrator(
            target_source_code=code,
            target_file_path=str(f),
            max_iterations=1,
            engine_mode="legacy"
        )
        state = orch.run()
        assert state.baseline_passed is True
        assert state.mutants_generated > 0
        assert state.mutants_executed > 0
        assert state.lines_covered > 0

    def test_04_boundary_conditions(self, tmp_path):
        """Scenario 4: Python file with boundary conditions."""
        code = (
            "def check_discount_eligibility(age: int, score: float) -> bool:\n"
            "    if age >= 65 or score >= 90.0:\n"
            "        return True\n"
            "    if age < 18 and score < 50.0:\n"
            "        return False\n"
            "    return score > 75.0\n"
        )
        f = tmp_path / "boundary.py"
        f.write_text(code)

        orch = TestForgeOrchestrator(
            target_source_code=code,
            target_file_path=str(f),
            max_iterations=1,
            engine_mode="legacy"
        )
        state = orch.run()
        assert state.baseline_passed is True
        assert state.mutants_generated >= 5
        assert state.mutants_executed >= 5

    def test_05_intentional_syntax_error(self, tmp_path):
        """Scenario 5: Python file with an intentional syntax error."""
        code = "def broken_syntax(x)\n    return x ++\n"
        f = tmp_path / "syntax_err.py"
        f.write_text(code)

        orch = TestForgeOrchestrator(
            target_source_code=code,
            target_file_path=str(f),
            max_iterations=1,
            engine_mode="legacy"
        )
        state = orch.run()
        # Should cleanly flag EXECUTION_ERROR or FAILED without unhandled crash
        assert state.terminated is True
        assert state.baseline_passed is False
        assert state.final_hardening_status in ("EXECUTION_ERROR", "FAILED_BASELINE", "FAILED")
        assert state.final_mutation_score is None

    def test_06_import_error_distinct_execution_error(self, tmp_path):
        """Scenario 6: Python file with missing/unresolvable import error."""
        code = (
            "import non_existent_external_package_12345\n\n"
            "def compute(val: int) -> int:\n"
            "    return val * 2\n"
        )
        f = tmp_path / "import_err.py"
        f.write_text(code)

        orch = TestForgeOrchestrator(
            target_source_code=code,
            target_file_path=str(f),
            max_iterations=1,
            engine_mode="legacy"
        )
        state = orch.run()
        assert state.terminated is True
        assert state.baseline_passed is False
        # Must be classified as EXECUTION_ERROR, NOT a passing run or 0% score
        assert state.final_hardening_status == "EXECUTION_ERROR"
        assert state.baseline_tests_executed == 0
        assert state.execution_errors >= 1
        assert "non_existent_external_package_12345" in (state.baseline_execution_error or "")
        assert state.final_mutation_score is None

    def test_07_empty_target(self, tmp_path):
        """Scenario 7: Empty target source code."""
        code = ""
        f = tmp_path / "empty.py"
        f.write_text(code)

        orch = TestForgeOrchestrator(
            target_source_code=code,
            target_file_path=str(f),
            max_iterations=1,
            engine_mode="legacy"
        )
        state = orch.run()
        assert state.terminated is True
        assert state.baseline_passed is False
        assert state.final_hardening_status == "FAILED"

    def test_08_pytest_discovery_in_sandbox(self, tmp_path):
        """Scenario 8: Generated test suite is discoverable by Pytest."""
        target_code = "def greet(name: str) -> str:\n    return f'Hello, {name}!'\n"
        test_code = (
            "import pytest\n"
            "from target import greet\n\n"
            "def test_greet_nominal():\n"
            "    assert greet('World') == 'Hello, World!'\n"
        )
        runner = ParallelSandboxRunner(timeout_seconds=5)
        res = runner.run_single(test_code, target_code)
        assert res["status"] == "PASS"
        assert res["tests_collected"] == 1
        assert res["tests_passed"] == 1
        assert res["tests_failed"] == 0
        assert res["has_exec_error"] is False

    def test_09_baseline_executes_successfully(self, tmp_path):
        """Scenario 9: Baseline test suite executes and passes 100% on clean target."""
        code = open("samples/discount.py").read()
        orch = TestForgeOrchestrator(
            target_source_code=code,
            target_file_path="samples/discount.py",
            max_iterations=1,
            engine_mode="legacy"
        )
        state = orch.run()
        assert state.baseline_passed is True
        assert state.baseline_tests_executed >= 4
        assert state.baseline_tests_passed == state.baseline_tests_executed
        assert state.baseline_tests_failed == 0

    def test_10_baseline_fails_assertions_reported_honestly(self, tmp_path):
        """Scenario 10: Baseline tests execute but genuinely fail assertions."""
        target_code = "def get_val():\n    return 42\n"
        # Test code asserts wrong return value (assertion failure on clean code)
        test_code = (
            "import pytest\n"
            "from target import get_val\n\n"
            "def test_get_val_wrong():\n"
            "    assert get_val() == 999\n"
        )
        runner = ParallelSandboxRunner(timeout_seconds=5)
        res = runner.run_single(test_code, target_code)
        assert res["status"] == "FAIL"
        assert res["tests_collected"] == 1
        assert res["tests_failed"] == 1
        assert res["tests_passed"] == 0
        assert res["has_exec_error"] is False

    def test_11_mutation_evaluation_score_calculation(self):
        """Scenario 11: Mutation evaluation calculates raw and adjusted scores."""
        mutants = [
            MutantRecord(
                mutant_id="M1", mutation_type="ARITH_OP", line_number=1,
                original_code_snippet="x + y", mutated_code_snippet="x - y",
                unified_diff="--- a\n+++ b\n@@ -1 +1 @@\n-x + y\n+x - y\n",
                status="KILLED", equivalence_status="NOT_EQUIVALENT"
            ),
            MutantRecord(
                mutant_id="M2", mutation_type="COMP_OP", line_number=2,
                original_code_snippet="x > 0", mutated_code_snippet="x >= 0",
                unified_diff="--- a\n+++ b\n@@ -1 +1 @@\n-x > 0\n+x >= 0\n",
                status="SURVIVED", equivalence_status="NOT_EQUIVALENT"
            ),
            MutantRecord(
                mutant_id="M3", mutation_type="CONST_VAL", line_number=3,
                original_code_snippet="x == 0", mutated_code_snippet="x == 1",
                unified_diff="--- a\n+++ b\n@@ -1 +1 @@\n-x == 0\n+x == 1\n",
                status="EQUIVALENT", equivalence_status="EQUIVALENT"
            ),
        ]
        scores = calculate_mutation_scores(mutants)
        # Evaluables = 3, Killed = 1 -> Raw = 1/3 = 33.33%
        assert scores["raw_mutation_score"] == 33.33
        # Adjusted excludes equivalent: 1 / (3 - 1) = 50.0%
        assert scores["adjusted_mutation_score"] == 50.0
        assert scores["equivalent_mutants"] == 1

    def test_12_mutation_generation_failed_when_no_mutants(self, tmp_path):
        """Scenario 12: Pipeline cleanly handles target code yielding zero mutants."""
        code = "def add(a: int, b: int) -> int:\n    return a + b\n"
        f = tmp_path / "add.py"
        f.write_text(code)

        with mock.patch("testforge.orchestrator.ASTMutator.mutate", return_value=[]):
            orch = TestForgeOrchestrator(
                target_source_code=code,
                target_file_path=str(f),
                max_iterations=1,
                engine_mode="legacy"
            )
            state = orch.run()
            assert state.final_hardening_status == "MUTATION_GENERATION_FAILED"
            assert state.final_mutation_score is None
