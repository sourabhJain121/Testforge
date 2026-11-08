"""
Unit tests for the Never-Regress Guard in TestForgeOrchestrator.
Scope: DEVELOPMENT TARGETS ONLY (samples/discount.py, samples/order_fsm.py).
Protocol Guarantee: Sealed V2 targets remain frozen pre-fix; these tests verify post-fix behavior.
"""

from unittest.mock import patch

from testforge.blackboard import Blackboard
from testforge.callbacks import CallbackRegistry
from testforge.equivalence import calculate_mutation_scores
from testforge.mutator import ASTMutator
from testforge.orchestrator import TestForgeOrchestrator
from testforge.sandbox import CandidateSuiteValidationResult
from testforge.state import IterationMetrics

DISCOUNT_TARGET = """
def calculate_discount(price: float, quantity: int, is_member: bool) -> float:
    if price <= 0.0:
        return 0.0
    discount_rate = 0.0
    if quantity >= 5:
        discount_rate = discount_rate + 0.10
    if is_member:
        discount_rate = discount_rate + 0.10
    final_price = price * (1.0 - discount_rate)
    return round(final_price, 2)
"""

HIGH_SCORING_TESTS = """
from target import calculate_discount

def test_discount_normal():
    assert calculate_discount(100.0, 1, False) == 100.0

def test_discount_quantity():
    assert calculate_discount(100.0, 5, False) == 90.0

def test_discount_member():
    assert calculate_discount(100.0, 1, True) == 90.0

def test_discount_both():
    assert calculate_discount(100.0, 5, True) == 80.0

def test_discount_zero_price():
    assert calculate_discount(0.0, 1, False) == 0.0

def test_discount_negative_price():
    assert calculate_discount(-10.0, 1, False) == 0.0
"""

WEAK_DEGRADED_TESTS = """
from target import calculate_discount

def test_discount_weak():
    assert calculate_discount(100.0, 1, False) == 100.0
"""


def test_never_regress_guard_restores_best_suite_on_degradation():
    """
    Verifies that if Iteration 1 scores high and Iteration 2 generates a degraded suite,
    the Never-Regress Guard triggers, restoring the peak-performing test suite and metrics.
    """
    bb = Blackboard()
    callbacks = CallbackRegistry()
    logged_events = []
    callbacks.register(lambda ev: logged_events.append(ev))

    orch = TestForgeOrchestrator(
        target_source_code=DISCOUNT_TARGET,
        initial_test_code=HIGH_SCORING_TESTS,
        max_iterations=2,
        target_mutation_score=100.0,
        engine_mode="legacy",
        blackboard=bb,
        callbacks=callbacks,
    )

    degraded_validation = CandidateSuiteValidationResult(
        overall_status="VALID",
        total_candidates=1,
        retained_count=1,
        retained_test_code=WEAK_DEGRADED_TESTS,
        summary="Simulated degraded candidate suite."
    )

    # In iteration 2, simulate candidate validation yielding degraded test code
    with patch.object(orch.sandbox, "validate_and_filter_candidate_suite", return_value=degraded_validation):
        final_state = orch.run()

    # Verify that the guard was triggered and restored the peak suite
    assert orch._guard_restored is True
    assert final_state.final_mutation_score == orch._best_raw_mutation_score
    assert final_state.final_mutation_score > 70.0  # Peak score preserved
    assert "test_discount_both" in final_state.current_test_code
    assert bb.get_suite_space().current_test_code == orch._best_test_code
    assert bb.get_metrics_space().final_mutation_score == final_state.final_mutation_score

    # Verify event logged
    events = orch.logger.get_events_by_type("NEVER_REGRESS_GUARD_TRIGGERED")
    assert len(events) >= 1
    assert events[0]["data"]["restored_iteration"] == 1


def test_never_regress_guard_retains_monotonic_improvements():
    """
    Verifies that if Iteration 2 improves over Iteration 1, the guard does NOT roll back,
    and the higher-scoring Iteration 2 suite is preserved.
    """
    bb = Blackboard()
    orch = TestForgeOrchestrator(
        target_source_code=DISCOUNT_TARGET,
        initial_test_code=WEAK_DEGRADED_TESTS,
        max_iterations=2,
        target_mutation_score=100.0,
        engine_mode="legacy",
        blackboard=bb,
    )

    improved_validation = CandidateSuiteValidationResult(
        overall_status="VALID",
        total_candidates=6,
        retained_count=6,
        retained_test_code=HIGH_SCORING_TESTS,
        summary="Simulated improved candidate suite."
    )

    # In iteration 2, simulate candidate validation yielding improved test code
    with patch.object(orch.sandbox, "validate_and_filter_candidate_suite", return_value=improved_validation):
        final_state = orch.run()

    # Guard should NOT restore earlier suite since iteration 2 improved score
    assert orch._guard_restored is False
    assert final_state.final_mutation_score > 70.0
    assert "test_discount_both" in final_state.current_test_code
    assert orch._best_iteration == 2


def test_never_regress_guard_on_cancellation():
    """
    Verifies that if execution is cancelled or timed out after an intermediate degradation,
    _finalize_cancellation_or_timeout rolls back to the peak-scoring suite.
    """
    bb = Blackboard()
    orch = TestForgeOrchestrator(
        target_source_code=DISCOUNT_TARGET,
        initial_test_code=HIGH_SCORING_TESTS,
        max_iterations=2,
        target_mutation_score=100.0,
        engine_mode="legacy",
        blackboard=bb,
    )

    # Simulate iteration 1 running and recording high score
    orch.state.current_test_code = HIGH_SCORING_TESTS
    orch.state.baseline_passed = True
    orch.state.baseline_tests_passed = 6
    mutants = ASTMutator.mutate(DISCOUNT_TARGET)
    eval_res = orch.execution_agent.evaluate_mutants(HIGH_SCORING_TESTS, mutants)
    score_data = calculate_mutation_scores(eval_res)
    peak_score = score_data["raw_mutation_score"]

    metric1 = IterationMetrics(
        iteration=1,
        total_mutants=score_data["total_mutants"],
        killed_mutants=score_data["killed_mutants"],
        survived_mutants=score_data["survived_mutants"],
        timed_out_mutants=0,
        execution_errors=0,
        invalid_mutants=0,
        mutation_score=peak_score,
        raw_mutation_score=peak_score,
        adjusted_mutation_score=peak_score,
        line_coverage_pct=100.0,
        duration_seconds=1.0,
    )
    orch.state.history.append(metric1)
    orch._best_raw_mutation_score = peak_score
    orch._best_adjusted_mutation_score = peak_score
    orch._best_test_code = HIGH_SCORING_TESTS
    orch._best_iteration = 1
    orch._best_mutants_killed = score_data["killed_mutants"]

    # Now simulate iteration 2 with degraded score
    metric2 = IterationMetrics(
        iteration=2,
        total_mutants=score_data["total_mutants"],
        killed_mutants=1,
        survived_mutants=score_data["total_mutants"] - 1,
        timed_out_mutants=0,
        execution_errors=0,
        invalid_mutants=0,
        mutation_score=10.0,
        raw_mutation_score=10.0,
        adjusted_mutation_score=10.0,
        line_coverage_pct=50.0,
        duration_seconds=1.0,
    )
    orch.state.history.append(metric2)
    orch.state.current_test_code = WEAK_DEGRADED_TESTS

    # Trigger cancellation finalization
    orch._finalize_cancellation_or_timeout("CANCELLED", "User cancelled")

    # Verify guard restored iteration 1
    assert orch._guard_restored is True
    assert orch.state.final_mutation_score == peak_score
    assert orch.state.current_test_code == HIGH_SCORING_TESTS
    assert bb.get_metrics_space().final_mutation_score == peak_score
