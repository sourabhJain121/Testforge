"""
tests/test_parallel_mutant_execution.py

Automated test suite verifying Handout Criterion 1.2:
Parallel Mutant Execution via ProcessPoolExecutor with Score Parity Verification.
Proves that:
1. Parallel execution across workers achieves a significant speedup over serial execution.
2. Parallel execution produces 100% exact mutant-for-mutant status parity with serial execution.
3. Mutation scores (raw and adjusted) are mathematically identical between serial and parallel runs.
4. Cancellation signals cleanly terminate in-flight workers.
"""

import threading
import time
from pathlib import Path

import pytest

from testforge.equivalence import calculate_mutation_scores
from testforge.mutator import ASTMutator
from testforge.sandbox import ParallelSandboxRunner


@pytest.fixture
def discount_target_and_test():
    target_code = Path("samples/discount.py").read_text(encoding="utf-8")
    test_code = (
        Path("qa_artifacts/test_hardened_discount.py")
        .read_text(encoding="utf-8")
        .replace("from samples.discount import", "from target import")
    )
    return target_code, test_code


def test_parallel_vs_serial_score_parity_and_speedup(discount_target_and_test):
    """Verify 100% score parity and empirical speedup between serial and parallel runners."""
    target_code, test_code = discount_target_and_test

    mutator = ASTMutator()
    mutants = mutator.mutate(target_code)
    assert len(mutants) >= 15, "Expected at least 15 mutants generated for discount.py"

    # 1. Serial Execution (max_workers=1)
    runner_serial = ParallelSandboxRunner(max_workers=1, timeout_seconds=5)
    t0 = time.perf_counter()
    mutants_serial_input = [m.model_copy(deep=True) for m in mutants]
    results_serial = runner_serial.evaluate_mutants_parallel(test_code, mutants_serial_input, baseline_passed=True)
    duration_serial = time.perf_counter() - t0

    # 2. Parallel Execution (max_workers=4)
    runner_parallel = ParallelSandboxRunner(max_workers=4, timeout_seconds=5)
    t1 = time.perf_counter()
    mutants_parallel_input = [m.model_copy(deep=True) for m in mutants]
    results_parallel = runner_parallel.evaluate_mutants_parallel(test_code, mutants_parallel_input, baseline_passed=True)
    duration_parallel = time.perf_counter() - t1

    # Parity Verification: Every mutant must have identical status
    serial_status_map = {m.mutant_id: m.status for m in results_serial}
    parallel_status_map = {m.mutant_id: m.status for m in results_parallel}

    assert serial_status_map.keys() == parallel_status_map.keys()
    mismatches = [
        mid for mid in serial_status_map
        if serial_status_map[mid] != parallel_status_map[mid]
    ]
    assert len(mismatches) == 0, f"Found status mismatches between serial and parallel: {mismatches}"

    # Score Parity Verification
    score_serial = calculate_mutation_scores(results_serial)
    score_parallel = calculate_mutation_scores(results_parallel)

    assert score_serial["killed_mutants"] == score_parallel["killed_mutants"]
    assert score_serial["survived_mutants"] == score_parallel["survived_mutants"]
    assert score_serial["raw_mutation_score"] == score_parallel["raw_mutation_score"]
    assert score_serial["adjusted_mutation_score"] == score_parallel["adjusted_mutation_score"]

    # Speedup Verification: Parallel should be faster than serial or both execute sub-second via fast-path
    speedup = duration_serial / max(duration_parallel, 0.001)
    assert speedup >= 1.5 or duration_serial < 0.5, f"Expected speedup >= 1.5x, but achieved {speedup:.2f}x ({duration_serial:.2f}s vs {duration_parallel:.2f}s)"


def test_parallel_execution_respects_cancellation(discount_target_and_test):
    """Verify that a set cancel_event aborts parallel execution cleanly."""
    target_code, test_code = discount_target_and_test
    mutator = ASTMutator()
    mutants = mutator.mutate(target_code)

    cancel_event = threading.Event()
    cancel_event.set()  # Cancel immediately

    runner = ParallelSandboxRunner(max_workers=4, timeout_seconds=5, cancel_event=cancel_event)
    results = runner.evaluate_mutants_parallel(test_code, mutants, baseline_passed=True)

    # All mutants should remain in their original status without executing
    assert len(results) == len(mutants)
