"""
tests/test_mutation_scores.py - Rigorous Unit Tests for Mutation Score Calculations.

Verifies:
  - Zero eligible mutants (safe 0.0 return, no ZeroDivisionError)
  - 100% kill scenario (raw = 100.0, adjusted = 100.0)
  - Partial survival scenario
  - Equivalent mutants excluded from adjusted score denominator
  - Invalid mutants excluded from evaluable pool
  - Subprocess errors excluded from evaluable pool
  - Timeouts counted correctly
  - Backward compatibility with legacy primary_score field
  - Explicit formula preservation
"""

import pytest
from testforge.state import MutantRecord
from testforge.equivalence import calculate_mutation_scores


def make_mutant(m_id: str, status: str, is_valid: bool = True, eq_status: str = None) -> MutantRecord:
    return MutantRecord(
        mutant_id=m_id,
        mutation_type="COMP_OP",
        line_number=1,
        original_code_snippet="x > 0",
        mutated_code_snippet="x <= 0",
        unified_diff="",
        status=status,
        is_valid_syntax=is_valid,
        equivalence_status=eq_status
    )


def test_zero_eligible_mutants():
    res = calculate_mutation_scores([])
    assert res["total_mutants"] == 0
    assert res["raw_mutation_score"] == 0.0
    assert res["adjusted_mutation_score"] == 0.0
    assert res["primary_score"] == 0.0


def test_all_mutants_killed():
    mutants = [
        make_mutant("M1", "KILLED"),
        make_mutant("M2", "KILLED"),
        make_mutant("M3", "TIMEOUT"),  # Timeouts represent caught infinite loops
    ]
    res = calculate_mutation_scores(mutants)
    assert res["total_mutants"] == 3
    assert res["killed_mutants"] == 2
    assert res["timed_out_mutants"] == 1
    assert res["raw_mutation_score"] == 100.0
    assert res["adjusted_mutation_score"] == 100.0


def test_surviving_mutants_partial_score():
    mutants = [
        make_mutant("M1", "KILLED"),
        make_mutant("M2", "KILLED"),
        make_mutant("M3", "SURVIVED"),
        make_mutant("M4", "SURVIVED"),
    ]
    res = calculate_mutation_scores(mutants)
    assert res["evaluable_mutants"] == 4
    assert res["killed_mutants"] == 2
    assert res["survived_mutants"] == 2
    assert res["raw_mutation_score"] == 50.0
    assert res["adjusted_mutation_score"] == 50.0


def test_equivalent_mutants_adjusts_denominator():
    """
    If there are 4 mutants:
    - 2 killed
    - 1 survived
    - 1 verified equivalent
    Raw score: (2 killed) / (4 evaluable) = 50.0%
    Adjusted score: (2 killed) / (4 evaluable - 1 equivalent) = 2 / 3 = 66.67%
    """
    mutants = [
        make_mutant("M1", "KILLED"),
        make_mutant("M2", "KILLED"),
        make_mutant("M3", "SURVIVED"),
        make_mutant("M4", "EQUIVALENT", eq_status="EQUIVALENT"),
    ]
    res = calculate_mutation_scores(mutants)
    assert res["raw_mutation_score"] == 50.0
    assert res["adjusted_mutation_score"] == 66.67
    assert res["equivalent_mutants"] == 1


def test_all_surviving_are_equivalent_gives_100_percent_adjusted():
    """
    If all killable mutants are killed and all remaining are equivalent,
    the adjusted score should be 100.0%.
    """
    mutants = [
        make_mutant("M1", "KILLED"),
        make_mutant("M2", "KILLED"),
        make_mutant("M3", "EQUIVALENT", eq_status="EQUIVALENT"),
    ]
    res = calculate_mutation_scores(mutants)
    assert res["raw_mutation_score"] == 66.67
    # 2 killed out of (3 - 1) = 2/2 = 100.0%
    assert res["adjusted_mutation_score"] == 100.0


def test_invalid_and_errored_mutants_excluded():
    """
    Invalid and errored mutants must NOT be silently treated as survived or killed,
    and must not inflate or deflate the evaluable denominator.
    """
    mutants = [
        make_mutant("M1", "KILLED"),
        make_mutant("M2", "SURVIVED"),
        make_mutant("M3", "INVALID", is_valid=False),
        make_mutant("M4", "ERROR"),
    ]
    res = calculate_mutation_scores(mutants)
    assert res["total_mutants"] == 4
    assert res["invalid_mutants"] == 1
    assert res["execution_errors"] == 1
    # Only M1 (killed) and M2 (survived) are evaluable
    assert res["evaluable_mutants"] == 2
    assert res["raw_mutation_score"] == 50.0
    assert res["adjusted_mutation_score"] == 50.0


def test_potentially_equivalent_recorded_explicitly():
    mutants = [
        make_mutant("M1", "KILLED"),
        make_mutant("M2", "POTENTIALLY_EQUIVALENT", eq_status="POTENTIALLY_EQUIVALENT"),
    ]
    res = calculate_mutation_scores(mutants)
    assert res["potentially_equivalent_mutants"] == 1
    # Potentially equivalent is in the evaluable pool but NOT excluded from adjusted denominator
    # (only verified equivalent mutants are excluded)
    assert res["raw_mutation_score"] == 50.0
    assert res["adjusted_mutation_score"] == 50.0
