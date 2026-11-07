"""
tests/test_quality_score_and_minimization.py - Automated Suite for Test Quality Scoring (TQS) & Minimization.

Verifies:
  1. Multi-dimensional Test Quality Score (TQS) calculation across all 5 dimensions.
  2. Severe penalty application for tautologies (assert True) and weak assertions (is not None).
  3. Letter grade categorization (A, B, C, D, F).
  4. AST deduplication removing identical test functions.
  5. Safe suite minimization with rollback protection if validation fails.
"""

import pytest

from testforge.crew_critic import TestQualityAnalyzer
from testforge.sandbox import ParallelSandboxRunner


class TestQualityScoreAndMinimization:
    """Verifies that TestQualityAnalyzer produces accurate TQS scores and safely minimizes suites."""

    def test_high_quality_suite_gets_high_tqs_score(self):
        target_code = "def add(a: int, b: int) -> int:\n    return a + b\n"
        test_code = """
import pytest
from target import add

def test_add_nominal():
    assert add(2, 3) == 5

def test_add_zero():
    assert add(0, 5) == 5

def test_add_negative():
    assert add(-2, -3) == -5
"""
        res = TestQualityAnalyzer.calculate_test_quality_score(
            test_code=test_code,
            target_source_code=target_code,
            mutation_score=100.0,
            line_coverage=100.0,
        )

        assert res["composite_score"] >= 85.0
        assert res["grade"] in ("A", "B")
        assert res["dimensions"]["assertion_strength"] == 100.0
        assert res["dimensions"]["mutation_effectiveness"] == 100.0
        assert res["dimensions"]["behavioral_coverage"] == 100.0
        assert res["findings_count"] == 0

    def test_tautology_and_weak_assertions_penalize_tqs_score(self):
        target_code = "def calculate(x: int) -> int:\n    if x > 10: return x * 2\n    return x\n"
        # Poor quality test suite with tautology and weak asserts
        test_code = """
import pytest
from target import calculate

def test_tautology():
    assert True

def test_weak():
    assert calculate(5) is not None

def test_len_weak():
    assert len([1]) >= 0
"""
        res = TestQualityAnalyzer.calculate_test_quality_score(
            test_code=test_code,
            target_source_code=target_code,
            mutation_score=30.0,
            line_coverage=50.0,
        )

        # Assertion strength should be heavily penalized
        assert res["dimensions"]["assertion_strength"] < 70.0
        assert res["composite_score"] < 65.0
        assert res["grade"] in ("D", "F")
        assert res["findings_summary"]["tautologies"] >= 1
        assert res["findings_summary"]["weak_assertions"] >= 1

    def test_deduplicate_and_minimize_removes_identical_tests(self):
        target_code = "def square(x: int) -> int:\n    return x * x\n"
        test_code = """
from target import square

def test_square_one():
    assert square(3) == 9

def test_square_duplicate_identical():
    assert square(3) == 9

def test_square_two():
    assert square(4) == 16
"""
        minimized_code, stats = TestQualityAnalyzer.deduplicate_and_minimize_suite(
            test_code=test_code,
            target_source_code=target_code,
            runner=ParallelSandboxRunner(timeout_seconds=5)
        )

        assert stats["duplicates_removed"] == 1
        assert stats["original_count"] == 3
        assert stats["minimized_count"] == 2
        assert stats["is_minimized"] is True
        assert stats["retained_all_passing"] is True

        # Verify minimized code is valid Python and only has 2 tests
        import ast
        tree = ast.parse(minimized_code)
        tests = [n.name for n in tree.body if isinstance(n, ast.FunctionDef) and n.name.startswith("test_")]
        assert len(tests) == 2
        assert "test_square_one" in tests
        assert "test_square_two" in tests

    def test_minimization_failsafe_retains_original_on_failure(self):
        target_code = "def identity(x): return x\n"
        test_code = """
from target import identity
def test_valid():
    assert identity(1) == 1
def test_valid_copy():
    assert identity(1) == 1
"""
        class FailingMockRunner:
            def run_single(self, t_code, s_code):
                return {"status": "FAIL", "exit_code": 1}

        minimized_code, stats = TestQualityAnalyzer.deduplicate_and_minimize_suite(
            test_code=test_code,
            target_source_code=target_code,
            runner=FailingMockRunner()
        )

        # When runner reports failure, failsafe guarantees original test code is retained
        assert minimized_code == test_code
        assert stats["retained_all_passing"] is False
