"""
tests/test_hypothesis_property_testing.py

Automated Test Suite for Hypothesis Property-Based Testing Generation (Sub-Task 5.5).
"""

import ast
import pytest

from testforge.property_generator import PropertyEvaluationResult, PropertyTestGenerator
from testforge.sandbox import ParallelSandboxRunner


def test_synthesize_property_suite_syntax():
    gen = PropertyTestGenerator("samples/discount.py")
    with open("samples/discount.py", "r", encoding="utf-8") as f:
        src = f.read()

    code = gen.synthesize_property_suite("samples/discount.py", src)
    assert "@given(" in code
    assert "@settings(" in code
    assert "from hypothesis import" in code

    tree = ast.parse(code)
    func_names = [n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
    assert len(func_names) >= 3
    assert any("upper_bound" in fn for fn in func_names)


def test_property_tests_pass_clean_target():
    gen = PropertyTestGenerator("samples/discount.py")
    with open("samples/discount.py", "r", encoding="utf-8") as f:
        src = f.read()

    code = gen.synthesize_property_suite("samples/discount.py", src)
    sandbox = ParallelSandboxRunner(target_file_path="samples/discount.py")
    res = sandbox.validate_and_filter_candidate_suite(code, src)

    assert res.overall_status in ("ALL_VALID", "PASS", "PARTIAL_PASS")
    assert res.retained_count >= 3


def test_property_vs_example_evaluation_lift():
    gen = PropertyTestGenerator("samples/discount.py")
    with open("samples/discount.py", "r", encoding="utf-8") as f:
        src = f.read()

    weak_example_suite = """
from samples.discount import calculate_discount

def test_single_item():
    assert calculate_discount(100.0, 1, False) == 100.0
"""
    res = gen.evaluate_property_vs_example(weak_example_suite, src, "samples/discount.py")

    assert isinstance(res, PropertyEvaluationResult)
    assert res.property_killed_count > res.example_killed_count
    assert res.property_only_killed_count > 0
    assert res.combined_mutation_score > res.example_mutation_score
    assert res.score_lift_pct > 0.0
