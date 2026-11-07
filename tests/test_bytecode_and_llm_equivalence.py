"""
tests/test_bytecode_and_llm_equivalence.py

Automated Test Suite for Bytecode dis Comparison & Advanced Equivalence Detection (Sub-Task 5.4).
"""

import pytest

from testforge.equivalence import (
    EquivalenceClassification,
    EquivalenceMethod,
    EquivalentMutantAnalyzer,
    compare_bytecode_instructions,
)
from testforge.state import MutantRecord


def test_compare_bytecode_instructions_identical():
    c1 = "def calc(x):\n    return x + (1 + 2)\n"
    c2 = "def calc(x):\n    return x + 3\n"

    is_ident, reason = compare_bytecode_instructions(c1, c2)
    assert is_ident is True
    assert "strictly identical" in reason.lower()


def test_compare_bytecode_instructions_different():
    c1 = "def calc(x):\n    return x + 1\n"
    c2 = "def calc(x):\n    return x - 1\n"

    is_ident, reason = compare_bytecode_instructions(c1, c2)
    assert is_ident is False
    assert reason is None


def test_analyzer_bytecode_identity_rule():
    orig = "def membership(val):\n    return val in (10, 20)\n"
    mut = "def membership(val):\n    return val in [10, 20]\n"

    record = MutantRecord(
        mutant_id="MUT_BC_001",
        mutation_type="COLLECTION_OP",
        line_number=2,
        original_code_snippet=orig,
        mutated_code_snippet=mut,
        unified_diff=f"- {orig}\n+ {mut}",
        is_valid_syntax=True,
        is_executed=True,
        status="SURVIVED",
    )

    res = EquivalentMutantAnalyzer.analyze_mutant(record, original_source=orig)
    assert res.status == EquivalenceClassification.EQUIVALENT
    assert res.method == EquivalenceMethod.BYTECODE_IDENTITY
    assert "bytecode" in res.reason.lower()


def test_analyzer_zero_false_positives_on_real_faults():
    # Real functional defect: reversing inequality
    orig = "def is_positive(x):\n    return x > 0\n"
    mut = "def is_positive(x):\n    return x < 0\n"

    record = MutantRecord(
        mutant_id="MUT_REAL_FAULT_001",
        mutation_type="COMP_OP",
        line_number=2,
        original_code_snippet=orig,
        mutated_code_snippet=mut,
        unified_diff=f"- {orig}\n+ {mut}",
        is_valid_syntax=True,
        is_executed=True,
        status="SURVIVED",
    )

    res = EquivalentMutantAnalyzer.analyze_mutant(record, original_source=orig)
    # Must NOT be classified as EQUIVALENT
    assert res.status != EquivalenceClassification.EQUIVALENT
    assert res.status in (EquivalenceClassification.UNKNOWN, EquivalenceClassification.NOT_EQUIVALENT)
