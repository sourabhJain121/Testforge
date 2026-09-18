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
