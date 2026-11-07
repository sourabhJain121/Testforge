"""
Unit tests verifying the 4 deterministic AST mutations.

Author: Shreshth
"""

import pytest

from testforge.mutator import ASTMutator

SAMPLE_CODE = """
def check_val(x, y):
    if x > 10:
        return x + y
    return False
"""

def test_ast_mutations_count_and_types():
    mutants = ASTMutator.generate_mutants(SAMPLE_CODE)
    assert len(mutants) >= 4

    types = {m.mutation_type for m in mutants}
    # Check all 4 categories are generated
    assert "COMP_OP" in types
    assert "ARITH_OP" in types
    assert "COND_INV" in types
    assert "RETURN_VAL" in types

def test_diff_generation():
    mutants = ASTMutator.generate_mutants(SAMPLE_CODE)
    for m in mutants:
        assert m.unified_diff != ""
        assert m.line_number > 0
        assert "target.py" in m.unified_diff


def test_subtle_ast_mutations():
    rich_code = """
def process(x: float, y: int, flag: bool) -> tuple[bool, float]:
    if x <= 10.0 and y > 5:
        total = round(x + float(y), 2)
        return True, abs(total)
    return False, 0.0
"""
    mutants = ASTMutator.generate_mutants(rich_code)
    types = {m.mutation_type for m in mutants}

    # Verify subtle mutations are detected and generated
    assert "BOUNDARY_SWAP" in types
    assert "OFF_BY_ONE" in types
    assert "LOGICAL_CONN" in types
    assert "MATH_FUNC" in types

    # Check that mutant IDs match format
    for m in mutants:
        assert m.mutant_id.startswith("MUT_")
        assert m.line_number >= 1

