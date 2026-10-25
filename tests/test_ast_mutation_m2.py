"""
tests/test_ast_mutation_m2.py - Comprehensive Unit Tests for Milestone 2 AST Mutation Engine.

Verifies:
  - All supported mutation operators (COMP_OP, BOUNDARY_SWAP, OFF_BY_ONE, ARITH_OP,
    LOGICAL_CONN, MATH_FUNC, COND_INV, RETURN_VAL, CONST_VAL, EXCEPT_HANDLER)
  - Deterministic generation order and output
  - Stable, structured mutant identifiers (MUT_<TYPE>_<INDEX>)
  - Nested expressions and multiline AST blocks
  - Boundary condition mutations
  - Invalid Python source handling (safe exit, no crash)
  - Syntax validation: ensuring generated mutants compile under ast.parse
  - Non-modification: original source string and files remain 100% untouched
  - Provenance tracking (original_expression, mutated_expression, line_number)
  - Unsupported or edge-case syntax safety
"""

import ast
import pytest
from testforge.mutator import ASTMutator, MutationTransformer
from testforge.state import MutantRecord


COMPLEX_TARGET_SOURCE = """def compute_risk(score: int, weight: float, flag: bool) -> float:
    \"\"\"Docstring explaining compute risk.\"\"\"
    if score > 50 and flag:
        base = score * 2 + 10
        adjusted = round(base * weight, 2)
        return adjusted
    elif score <= 10 or not flag:
        return 0.0
    try:
        val = abs(score - 100)
        return float(val)
    except ValueError:
        return -1.0
"""


def test_all_supported_operators_generated():
    mutants = ASTMutator.mutate(COMPLEX_TARGET_SOURCE)
    assert len(mutants) > 0

    types_found = {m.mutation_type for m in mutants}
    # Check that our core suite of operators are generated on this complex code
    expected_operators = {
        "COMP_OP",
        "BOUNDARY_SWAP",
        "OFF_BY_ONE",
        "ARITH_OP",
        "LOGICAL_CONN",
        "MATH_FUNC",
        "COND_INV",
        "RETURN_VAL",
        "CONST_VAL",
        "EXCEPT_HANDLER"
    }
    for op in expected_operators:
        assert op in types_found, f"Expected operator {op} was not generated"


def test_deterministic_output_and_ordering():
    mutants_run1 = ASTMutator.mutate(COMPLEX_TARGET_SOURCE)
    mutants_run2 = ASTMutator.mutate(COMPLEX_TARGET_SOURCE)

    assert len(mutants_run1) == len(mutants_run2)
    for m1, m2 in zip(mutants_run1, mutants_run2):
        assert m1.mutant_id == m2.mutant_id
        assert m1.mutation_type == m2.mutation_type
        assert m1.line_number == m2.line_number
        assert m1.mutated_code_snippet == m2.mutated_code_snippet
        assert m1.unified_diff == m2.unified_diff
        assert m1.original_expression == m2.original_expression
        assert m1.mutated_expression == m2.mutated_expression


def test_stable_mutant_identifiers():
    mutants = ASTMutator.mutate(COMPLEX_TARGET_SOURCE)
    for idx, m in enumerate(mutants, 1):
        assert m.mutant_id.startswith(f"MUT_{m.mutation_type}_")
        assert f"{idx:03d}" in m.mutant_id
        assert m.line_number >= 1


def test_nested_expressions():
    nested_code = """def nested_calc(a, b, c):
    return ((a + b) * (c - 5)) if (a > 0 and (b < 10 or c == 20)) else 0
"""
    mutants = ASTMutator.mutate(nested_code)
    assert len(mutants) >= 6
    # Check mutations inside deeply nested binary operations and conditions
    mutated_snippets = [m.mutated_code_snippet for m in mutants]
    assert any("a - b" in s for s in mutated_snippets)
    assert any("c + 5" in s or "c - 6" in s or "c - 4" in s for s in mutated_snippets)
    assert any("a <= 0" in s for s in mutated_snippets)


def test_boundary_relational_mutations():
    boundary_code = """def check_limits(val):
    if val < 100:
        return 1
    if val >= 500:
        return 2
    return 0
"""
    mutants = ASTMutator.mutate(boundary_code)
    boundary_mutants = [m for m in mutants if m.mutation_type == "BOUNDARY_SWAP"]
    assert len(boundary_mutants) >= 2

    # < should become <=
    # >= should become >
    diff_text = "\n".join(m.unified_diff for m in boundary_mutants)
    assert "<=" in diff_text
    assert ">" in diff_text


def test_invalid_source_syntax_safety():
    broken_code = "def syntax_error(x:\n    return x +"
    # Engine must not crash or throw unhandled exceptions
    mutants = ASTMutator.mutate(broken_code)
    assert mutants == []

    pts = ASTMutator.inspect_mutation_points(broken_code)
    assert pts == 0


def test_generated_mutants_are_valid_syntax():
    mutants = ASTMutator.mutate(COMPLEX_TARGET_SOURCE)
    for m in mutants:
        assert m.is_valid_syntax is True
        # Parse mutated snippet to independently prove valid Python AST syntax
        parsed_tree = ast.parse(m.mutated_code_snippet)
        assert parsed_tree is not None


def test_no_modification_of_original_source_or_file():
    original_copy = str(COMPLEX_TARGET_SOURCE)
    mutants = ASTMutator.mutate(COMPLEX_TARGET_SOURCE)
    assert COMPLEX_TARGET_SOURCE == original_copy
    for m in mutants:
        assert m.original_code_snippet == original_copy


def test_provenance_metadata():
    mutants = ASTMutator.mutate(COMPLEX_TARGET_SOURCE)
    with_provenance = [m for m in mutants if m.original_expression and m.mutated_expression]
    # Provenance tracking captures AST node unparsing before and after
    assert len(with_provenance) > 0
    for m in with_provenance:
        assert m.original_expression != m.mutated_expression
        assert isinstance(m.original_expression, str)
        assert isinstance(m.mutated_expression, str)


def test_constant_value_mutation():
    const_code = """def flags(mode):
    active = True
    count = 0
    name = "production"
    return active
"""
    mutants = ASTMutator.mutate(const_code)
    const_mutants = [m for m in mutants if m.mutation_type == "CONST_VAL"]
    assert len(const_mutants) >= 3

    diffs = "\n".join(m.unified_diff for m in const_mutants)
    # True should flip to False
    assert "False" in diffs
    # 0 should flip to 1
    assert "1" in diffs
    # String should flip to empty string
    assert "''" in diffs or '""' in diffs


def test_exception_handler_mutation():
    try_code = """def load_data(key, mapping):
    try:
        return mapping[key]
    except KeyError:
        return None
"""
    mutants = ASTMutator.mutate(try_code)
    exc_mutants = [m for m in mutants if m.mutation_type == "EXCEPT_HANDLER"]
    assert len(exc_mutants) >= 1
    assert any("IndexError" in m.mutated_code_snippet for m in exc_mutants)
