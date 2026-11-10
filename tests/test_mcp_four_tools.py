"""
tests/test_mcp_four_tools.py - Formal Verification Suite for FastMCP 4-Tool Protocol Suite.

Verifies:
  1. mcp_ast_symbol_analyzer: Symbols, cyclomatic complexity, functions, and branch boundaries.
  2. mcp_mutant_generator: AST mutants generation, bounding, operator diversity.
  3. mcp_sandbox_runner: Subprocess sandbox execution, exit code, and clean code integrity.
  4. mcp_equivalence_classifier: Syntactic, bytecode, and structural semantic equivalence.
  5. FastMCP server registration: create_protocol_suite_server and create_testforge_server tool exposure.
  6. HybridSynthesizer with Never-Regress Guard integration.
"""

from __future__ import annotations

import pytest

from testforge.hybrid_synthesizer import HybridSynthesizer
from testforge.mcp_server import (
    create_protocol_suite_server,
    create_testforge_server,
    mcp_ast_symbol_analyzer,
    mcp_equivalence_classifier,
    mcp_mutant_generator,
    mcp_sandbox_runner,
)

SAMPLE_CODE = """
def calculate_tax(income: float, is_resident: bool = True) -> float:
    if income <= 0.0:
        return 0.0
    rate = 0.15
    if not is_resident:
        rate = 0.25
    if income > 50000.0:
        rate = rate + 0.05
    return round(income * rate, 2)
"""

VALID_TEST = """
from target import calculate_tax

def test_tax_resident_low():
    assert calculate_tax(10000.0, True) == 1500.0

def test_tax_resident_high():
    assert calculate_tax(60000.0, True) == 12000.0

def test_tax_zero():
    assert calculate_tax(0.0, True) == 0.0
"""

FAILING_TEST = """
from target import calculate_tax

def test_tax_broken():
    assert calculate_tax(100.0) == 999999.0
"""


def test_mcp_ast_symbol_analyzer():
    res = mcp_ast_symbol_analyzer(SAMPLE_CODE)
    assert res["status"] == "SUCCESS"
    assert "calculate_tax" in res["symbols"]
    assert res["cyclomatic_complexity"] >= 3
    assert len(res["functions"]) == 1
    fn = res["functions"][0]
    assert fn["name"] == "calculate_tax"
    assert "income" in fn["args"]
    assert "is_resident" in fn["args"]
    assert len(res["branch_boundaries"]) >= 3

    # Error handling on invalid code
    bad_res = mcp_ast_symbol_analyzer("def syntax_err(: pass")
    assert bad_res["status"] == "ERROR"
    assert "Failed parsing AST" in bad_res["error"]


def test_mcp_mutant_generator():
    mutants = mcp_mutant_generator(SAMPLE_CODE, max_mutants=10)
    assert isinstance(mutants, list)
    assert 1 <= len(mutants) <= 10

    first = mutants[0]
    assert "id" in first
    assert "type" in first
    assert "line" in first
    assert "original" in first
    assert "mutated" in first
    assert "diff" in first

    types = {m["type"] for m in mutants}
    assert any(t in types for t in ("COMP_OP", "BOUNDARY_SWAP", "COND_INV", "CONST_VAL", "RETURN_VAL"))


def test_mcp_sandbox_runner_clean_and_failing():
    # 1. Clean valid test suite
    res_pass = mcp_sandbox_runner(VALID_TEST, SAMPLE_CODE, timeout_seconds=4.0)
    assert res_pass["clean_code_integrity"] is True
    assert res_pass["passed"] is True
    assert res_pass["exit_code"] == 0
    assert res_pass["tests_passed"] >= 3
    assert res_pass["tests_failed"] == 0

    # 2. Failing candidate test suite
    res_fail = mcp_sandbox_runner(FAILING_TEST, SAMPLE_CODE, timeout_seconds=4.0)
    assert res_fail["clean_code_integrity"] is False
    assert res_fail["passed"] is False
    assert res_fail["tests_failed"] >= 1


def test_mcp_equivalence_classifier():
    # 1. Syntactic identity
    eq_ident = mcp_equivalence_classifier(SAMPLE_CODE, SAMPLE_CODE)
    assert eq_ident["is_equivalent"] is True
    assert eq_ident["status"] == "EQUIVALENT"
    assert eq_ident["method"] == "SYNTACTIC_IDENTITY"

    # 2. Non-equivalent mutation
    mutated_code = SAMPLE_CODE.replace("rate = 0.15", "rate = 0.99")
    eq_diff = mcp_equivalence_classifier(SAMPLE_CODE, mutated_code)
    assert eq_diff["is_equivalent"] is False
    assert eq_diff["status"] == "NOT_EQUIVALENT"


def test_fastmcp_server_registrations():
    # Protocol suite server has exactly the 4 tools
    protocol_server = create_protocol_suite_server()
    p_tools = [t.name for t in protocol_server._tool_manager.list_tools()]
    assert set(p_tools) == {
        "mcp_ast_symbol_analyzer",
        "mcp_mutant_generator",
        "mcp_sandbox_runner",
        "mcp_equivalence_classifier",
    }

    # Native testforge server has all 4 tools plus lifecycle tools
    tf_server = create_testforge_server()
    tf_tools = [t.name for t in tf_server._tool_manager.list_tools()]
    assert "mcp_ast_symbol_analyzer" in tf_tools
    assert "mcp_mutant_generator" in tf_tools
    assert "mcp_sandbox_runner" in tf_tools
    assert "mcp_equivalence_classifier" in tf_tools
    assert "harden_module" in tf_tools
    assert "get_report" in tf_tools
    assert "list_jobs" in tf_tools


def test_hybrid_synthesizer_never_regress_guard():
    hybrid = HybridSynthesizer(
        target_code=SAMPLE_CODE,
        target_file_path="sample_tax.py",
        max_iterations=2,
        timeout_seconds=3.0,
    )
    result = hybrid.synthesize(initial_seed_tests=VALID_TEST)

    assert result.clean_pass is True
    assert result.final_raw_ms >= result.initial_raw_ms
    assert result.killed_mutants > 0
    assert result.total_mutants > 0
    assert result.line_coverage >= 70.0
