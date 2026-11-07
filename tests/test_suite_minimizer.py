"""
tests/test_suite_minimizer.py

Automated Test Suite for Kill-Matrix Greedy Set Cover Test Minimization (Sub-Task 5.1).
"""

import ast
import os
import pytest

from testforge.minimizer import KillMatrixData, MinimizationResult, TestSuiteMinimizer


@pytest.fixture
def discount_context():
    with open("samples/discount.py", "r", encoding="utf-8") as f:
        src = f.read()
    with open("qa_artifacts/test_hardened_discount.py", "r", encoding="utf-8") as f:
        tests = f.read()
    return src, tests


def test_build_kill_matrix_structure(discount_context):
    src, tests = discount_context
    minimizer = TestSuiteMinimizer(target_file_path="samples/discount.py")
    matrix_data = minimizer.build_kill_matrix(tests, src)

    assert isinstance(matrix_data, KillMatrixData)
    assert len(matrix_data.test_names) >= 10
    assert len(matrix_data.mutant_ids) >= 15
    assert len(matrix_data.matrix) == len(matrix_data.test_names)
    assert all(len(row) == len(matrix_data.mutant_ids) for row in matrix_data.matrix)
    assert matrix_data.killable_mutants > 0


def test_solve_greedy_set_cover_parity(discount_context):
    src, tests = discount_context
    minimizer = TestSuiteMinimizer(target_file_path="samples/discount.py")
    matrix_data = minimizer.build_kill_matrix(tests, src)

    res = minimizer.solve_greedy_set_cover(tests, matrix_data, target_module_name="discount.py")
    assert isinstance(res, MinimizationResult)

    # Significant test reduction achieved
    assert res.reduction_pct >= 50.0
    assert res.minimized_test_count < res.original_test_count
    assert len(res.redundant_tests) > 0

    # Strict 100.0% score parity retention
    assert res.score_retention_pct == 100.0
    assert res.minimized_killed_mutants == res.original_killed_mutants


def test_minimized_code_valid_syntax(discount_context):
    src, tests = discount_context
    minimizer = TestSuiteMinimizer(target_file_path="samples/discount.py")
    res = minimizer.minimize(tests, src, target_module_name="discount.py")

    # Minimized code must parse cleanly
    tree = ast.parse(res.minimized_test_code)
    func_names = [n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]

    assert len(func_names) == res.minimized_test_count
    assert set(func_names) == set(res.selected_tests)
    assert all(t not in func_names for t in res.redundant_tests)


def test_minimizer_api_endpoints():
    from starlette.testclient import TestClient
    from server import app

    client = TestClient(app)
    # GET summary
    resp = client.get("/api/minimizer/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert "macro_reduction_pct" in data or "targets" in data

    # POST minimize
    resp = client.post("/api/minimizer/minimize", json={
        "target_path": "samples/discount.py",
        "test_path": "qa_artifacts/test_hardened_discount.py"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["score_retention_pct"] == 100.0
    assert data["reduction_pct"] >= 50.0
    assert len(data["selected_tests"]) > 0

