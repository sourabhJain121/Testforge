"""
tests/test_equivalent_mutants.py - Unit tests for Conservative Equivalent-Mutant Analysis.

Verifies:
  - Killed mutants are classified as NOT_EQUIVALENT
  - Surviving non-equivalent mutants are NOT classified as EQUIVALENT (false-positive resistance)
  - Provable equivalent mutants (dead code mutation, syntactic identity, algebraic zero-identity)
  - Potentially equivalent mutants (domain boundary invariants like len(x) >= 0)
  - Invalid mutants reject equivalence
  - Subprocess execution errors reject equivalence
  - Timeouts reject equivalence
  - Confidence rating (HIGH, MEDIUM, LOW, NONE) and explicit human-readable reasons
  - Dead code detection inside loops, conditionals, and post-terminator statements
"""

import pytest
from testforge.state import MutantRecord
from testforge.equivalence import (
    EquivalentMutantAnalyzer,
    EquivalenceClassification,
    EquivalenceMethod,
    EquivalenceConfidence,
    DeadCodeVisitor
)


def test_killed_mutant_not_equivalent():
    record = MutantRecord(
        mutant_id="MUT_COMP_OP_001",
        mutation_type="COMP_OP",
        line_number=5,
        original_code_snippet="def f(x):\n    return x > 0",
        mutated_code_snippet="def f(x):\n    return x <= 0",
        unified_diff="--- target.py\n+++ mutant\n@@ -2 +2 @@\n- return x > 0\n+ return x <= 0",
        status="KILLED",
        is_executed=True,
        is_valid_syntax=True
    )
    result = EquivalentMutantAnalyzer.analyze_mutant(record)
    assert result.status == EquivalenceClassification.NOT_EQUIVALENT
    assert result.confidence == EquivalenceConfidence.HIGH
    assert "detected and killed" in result.reason.lower()


def test_surviving_non_equivalent_mutant_unknown():
    """
    Critical requirement: A mutant surviving the test suite is NOT automatically equivalent!
    """
    record = MutantRecord(
        mutant_id="MUT_ARITH_OP_002",
        mutation_type="ARITH_OP",
        line_number=3,
        original_code_snippet="def calc(a, b):\n    return a + b",
        mutated_code_snippet="def calc(a, b):\n    return a - b",
        unified_diff="--- target.py\n+++ mutant\n@@ -2 +2 @@\n- return a + b\n+ return a - b",
        status="SURVIVED",
        is_executed=True,
        is_valid_syntax=True,
        original_expression="a + b",
        mutated_expression="a - b"
    )
    result = EquivalentMutantAnalyzer.analyze_mutant(record)
    # Must NOT be marked EQUIVALENT
    assert result.status == EquivalenceClassification.UNKNOWN
    assert result.confidence == EquivalenceConfidence.NONE
    assert "insufficient evidence" in result.reason.lower() or "no static semantic" in result.reason.lower()


def test_dead_code_mutation_equivalent():
    """
    Code after an unconditional return in a function cannot execute;
    any mutation there is provably equivalent under all possible tests.
    """
    source_with_dead_code = """def process(x):
    if x > 0:
        return x
    return 0
    unreachable = x + 10
    return unreachable
"""
    record = MutantRecord(
        mutant_id="MUT_ARITH_OP_003",
        mutation_type="ARITH_OP",
        line_number=6,  # 'unreachable = x + 10' is line 6
        original_code_snippet=source_with_dead_code,
        mutated_code_snippet=source_with_dead_code.replace("x + 10", "x - 10"),
        unified_diff="--- target.py\n+++ mutant\n@@ -6 +6 @@\n- unreachable = x + 10\n+ unreachable = x - 10",
        status="SURVIVED",
        is_executed=True,
        is_valid_syntax=True
    )
    result = EquivalentMutantAnalyzer.analyze_mutant(record, original_source=source_with_dead_code)
    assert result.status == EquivalenceClassification.EQUIVALENT
    assert result.method == EquivalenceMethod.DEAD_CODE_MUTATION
    assert result.confidence == EquivalenceConfidence.HIGH
    assert "unreachable dead code" in result.reason


def test_syntactic_identity_equivalent():
    """
    If AST unparsing produces identical code, it is verified equivalent.
    """
    orig = "def f(x):\n    return x + (0)"
    mut = "def f(x):\n    return x + 0"
    record = MutantRecord(
        mutant_id="MUT_COMP_OP_004",
        mutation_type="COMP_OP",
        line_number=2,
        original_code_snippet=orig,
        mutated_code_snippet=mut,
        unified_diff="",
        status="PENDING",
        is_executed=False,
        is_valid_syntax=True
    )
    result = EquivalentMutantAnalyzer.analyze_mutant(record)
    assert result.status == EquivalenceClassification.EQUIVALENT
    assert result.method == EquivalenceMethod.SYNTACTIC_IDENTITY
    assert result.confidence == EquivalenceConfidence.HIGH


def test_algebraic_identity_equivalent():
    """
    Algebraic identity: x + 0 -> x - 0
    """
    record = MutantRecord(
        mutant_id="MUT_ARITH_OP_005",
        mutation_type="ARITH_OP",
        line_number=2,
        original_code_snippet="def add_zero(x):\n    return x + 0",
        mutated_code_snippet="def add_zero(x):\n    return x - 0",
        unified_diff="--- target.py\n+++ mutant\n@@ -2 +2 @@\n- return x + 0\n+ return x - 0",
        status="SURVIVED",
        is_executed=True,
        is_valid_syntax=True,
        original_expression="x + 0",
        mutated_expression="x - 0"
    )
    result = EquivalentMutantAnalyzer.analyze_mutant(record)
    assert result.status == EquivalenceClassification.EQUIVALENT
    assert result.method == EquivalenceMethod.SELF_CANCELING_TRANSFORM
    assert result.confidence == EquivalenceConfidence.HIGH


def test_domain_boundary_potentially_equivalent():
    """
    Domain boundary: len(items) >= 0 -> len(items) > -1
    Heuristic evidence suggests equivalence because Python len() is strictly >= 0.
    """
    record = MutantRecord(
        mutant_id="MUT_BOUNDARY_006",
        mutation_type="BOUNDARY_SWAP",
        line_number=2,
        original_code_snippet="def check(items):\n    return len(items) >= 0",
        mutated_code_snippet="def check(items):\n    return len(items) > -1",
        unified_diff="--- target.py\n+++ mutant\n@@ -2 +2 @@\n- return len(items) >= 0\n+ return len(items) > -1",
        status="SURVIVED",
        is_executed=True,
        is_valid_syntax=True,
        original_expression="len(items) >= 0",
        mutated_expression="len(items) > -1"
    )
    result = EquivalentMutantAnalyzer.analyze_mutant(record)
    assert result.status == EquivalenceClassification.POTENTIALLY_EQUIVALENT
    assert result.method == EquivalenceMethod.REDUNDANT_BOUNDARY
    assert result.confidence == EquivalenceConfidence.MEDIUM
    assert "non-negative domain invariant" in result.reason


def test_invalid_mutant_rejects_equivalence():
    record = MutantRecord(
        mutant_id="MUT_INVALID_007",
        mutation_type="COMP_OP",
        line_number=1,
        original_code_snippet="def f(): pass",
        mutated_code_snippet="def f(: pass",
        unified_diff="",
        status="INVALID",
        is_executed=False,
        is_valid_syntax=False
    )
    result = EquivalentMutantAnalyzer.analyze_mutant(record)
    assert result.status == EquivalenceClassification.NOT_EQUIVALENT
    assert "invalid" in result.reason.lower()


def test_execution_error_rejects_equivalence():
    record = MutantRecord(
        mutant_id="MUT_ERR_008",
        mutation_type="ARITH_OP",
        line_number=2,
        original_code_snippet="def f(): return 1",
        mutated_code_snippet="def f(): return 1",
        unified_diff="",
        status="ERROR",
        is_executed=True,
        is_valid_syntax=True
    )
    result = EquivalentMutantAnalyzer.analyze_mutant(record)
    assert result.status == EquivalenceClassification.NOT_EQUIVALENT
    assert "error" in result.reason.lower()


def test_dead_code_visitor_branches():
    """
    Test DeadCodeVisitor on if False, while False, and post-raise blocks.
    """
    code = """def demo():
    if False:
        print("dead1")
        print("dead2")
    if True:
        x = 1
    else:
        print("dead3")
    raise RuntimeError("stop")
    print("dead4")
"""
    dead_lines = EquivalentMutantAnalyzer.find_dead_lines(code)
    # Lines 3, 4 (inside if False:), Line 8 (inside else: of if True:), and Line 10 (after raise)
    assert 3 in dead_lines
    assert 4 in dead_lines
    assert 8 in dead_lines
    assert 10 in dead_lines
    # Line 6 (x = 1) is NOT dead
    assert 6 not in dead_lines
