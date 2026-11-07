"""
tests/test_held_out_mutators.py

Verification tests for Held-Out Mutation Operators (Stage 1.5):
  - BITWISE_OP: Bitwise binary operations (&, |, ^, <<, >>)
  - EXCEPTION_SWAP: Raising exception class swaps (ValueError <-> TypeError, KeyError <-> IndexError)
"""

import ast
import pytest
from testforge.mutator import ASTMutator


def test_bitwise_operator_mutations():
    code = """def mask_bits(flags: int, mask: int) -> int:
    a = flags & mask
    b = flags | mask
    c = flags ^ mask
    d = flags << 2
    e = flags >> 1
    return a + b + c + d + e
"""
    # Without include_held_out, no BITWISE_OP
    std_mutants = ASTMutator.mutate(code, include_held_out=False)
    assert not any(m.mutation_type == "BITWISE_OP" for m in std_mutants)

    # With include_held_out, BITWISE_OP are generated
    held_mutants = ASTMutator.mutate(code, include_held_out=True)
    bitwise_mutants = [m for m in held_mutants if m.mutation_type == "BITWISE_OP"]
    assert len(bitwise_mutants) >= 5

    # Check diffs contains expected swapped operators
    diff_text = "\n".join(m.unified_diff for m in bitwise_mutants)
    assert "|" in diff_text
    assert "&" in diff_text
    assert ">>" in diff_text
    assert "<<" in diff_text

    # All mutants compile
    for m in bitwise_mutants:
        assert m.is_valid_syntax is True
        ast.parse(m.mutated_code_snippet)


def test_exception_swap_mutations():
    code = """def validate_input(val: int):
    if val < 0:
        raise ValueError("Must be positive")
    if not isinstance(val, int):
        raise TypeError("Must be integer")
    if val > 100:
        raise KeyError("Key out of bounds")
"""
    # Without include_held_out, no EXCEPTION_SWAP
    std_mutants = ASTMutator.mutate(code, include_held_out=False)
    assert not any(m.mutation_type == "EXCEPTION_SWAP" for m in std_mutants)

    # With include_held_out, EXCEPTION_SWAP are generated
    held_mutants = ASTMutator.mutate(code, include_held_out=True)
    exc_swaps = [m for m in held_mutants if m.mutation_type == "EXCEPTION_SWAP"]
    assert len(exc_swaps) >= 3

    diff_text = "\n".join(m.unified_diff for m in exc_swaps)
    assert "TypeError" in diff_text
    assert "ValueError" in diff_text
    assert "IndexError" in diff_text

    for m in exc_swaps:
        assert m.is_valid_syntax is True
        ast.parse(m.mutated_code_snippet)


def test_generate_held_out_mutants_helper():
    code = """def process(x: int, y: int):
    if x < 0:
        raise ValueError("negative")
    res = x & y
    return res + 1
"""
    held_only = ASTMutator.generate_held_out_mutants(code)
    assert len(held_only) >= 2
    types = {m.mutation_type for m in held_only}
    assert types == {"EXCEPTION_SWAP", "BITWISE_OP"}


def test_statement_deletion_mutations():
    code = """def manage_inventory(ledger, count):
    ledger.record_action("restock")
    ledger.total += count
    return ledger.total
"""
    # Without include_held_out, no STATEMENT_DELETION
    std_mutants = ASTMutator.mutate(code, include_held_out=False)
    assert not any(m.mutation_type == "STATEMENT_DELETION" for m in std_mutants)

    # With include_held_out, STATEMENT_DELETION mutants are generated
    held_mutants = ASTMutator.mutate(code, include_held_out=True)
    stmt_dels = [m for m in held_mutants if m.mutation_type == "STATEMENT_DELETION"]
    assert len(stmt_dels) >= 2

    # Verify both function call and AugAssign were mutated to pass
    diff_text = "\n".join(m.unified_diff for m in stmt_dels)
    assert "pass" in diff_text

    # All mutants are syntactically valid
    for m in stmt_dels:
        assert m.is_valid_syntax is True
        ast.parse(m.mutated_code_snippet)


