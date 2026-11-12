"""
tests/test_neuro_symbolic_solver.py - Neuro-Symbolic Boundary & Path Constraint Solver Verification Suite.

Tests deterministic boundary constraint extraction, ground-truth oracle execution,
boundary mutant killing, and full orchestrator reflection integration.
"""

import os
import sys
import tempfile
import pytest
from pathlib import Path

from testforge.orchestrator import TestForgeOrchestrator
from testforge.sandbox import ParallelSandboxRunner
from testforge.symbolic_solver import BoundaryConstraint, NeuroSymbolicBoundarySolver


# ==============================================================================
# 1. Unit Test: Numeric Relational Boundaries
# ==============================================================================

def test_extracts_numeric_relational_boundaries():
    clean_code = (
        "def check_threshold(x: int) -> str:\n"
        "    return 'high' if x >= 10 else 'low'\n"
    )
    mutant_code = (
        "def check_threshold(x: int) -> str:\n"
        "    return 'high' if x > 10 else 'low'\n"
    )
    surviving_mutant = {
        "mutant_id": "MUT_BOUNDARY_01",
        "line_number": 2,
        "mutation_type": "BOUNDARY_SWAP",
        "original_expr": "x >= 10",
        "mutated_expr": "x > 10",
        "status": "SURVIVED",
    }

    solver = NeuroSymbolicBoundarySolver()
    constraints = solver.extract_boundary_constraints(clean_code, [surviving_mutant])

    assert len(constraints) == 1
    c = constraints[0]
    assert c.function_name == "check_threshold"
    assert c.target_param == "x"
    assert c.threshold_value == 10
    assert c.probe_values == [9, 10, 11]

    synth_tests = solver.synthesize_boundary_tests(clean_code, [surviving_mutant])
    assert "check_threshold" in synth_tests
    assert "assert check_threshold(9) == 'low'" in synth_tests
    assert "assert check_threshold(10) == 'high'" in synth_tests
    assert "assert check_threshold(11) == 'high'" in synth_tests

    # Verify execution against clean code (100% Pass@1)
    runner = ParallelSandboxRunner(timeout_seconds=5)
    clean_res = runner.run_single(synth_tests, clean_code)
    assert clean_res.get("status") == "PASS", f"Failed on clean code: {clean_res.get('stdout')} {clean_res.get('stderr')}"

    # Verify execution against mutated code (Mutant KILLED!)
    mutant_res = runner.run_single(synth_tests, mutant_code)
    assert mutant_res.get("status") == "FAIL", "Mutant should be killed by boundary probe at x=10"


# ==============================================================================
# 2. Unit Test: String & Sequence Length Boundaries
# ==============================================================================

def test_extracts_string_and_length_boundaries():
    clean_code = (
        "def validate_batch(items: list) -> bool:\n"
        "    if len(items) <= 3:\n"
        "        return True\n"
        "    return False\n"
    )
    mutant_code = (
        "def validate_batch(items: list) -> bool:\n"
        "    if len(items) < 3:\n"
        "        return True\n"
        "    return False\n"
    )
    surviving_mutant = {
        "mutant_id": "MUT_LEN_01",
        "line_number": 2,
        "mutation_type": "BOUNDARY_SWAP",
        "original_expr": "len(items) <= 3",
        "mutated_expr": "len(items) < 3",
        "status": "SURVIVED",
    }

    solver = NeuroSymbolicBoundarySolver()
    constraints = solver.extract_boundary_constraints(clean_code, [surviving_mutant])

    assert len(constraints) == 1
    c = constraints[0]
    assert c.function_name == "validate_batch"
    assert c.target_param == "items"
    assert c.threshold_value == 3
    assert len(c.probe_values) == 3
    assert [len(p) for p in c.probe_values] == [2, 3, 4]

    synth_tests = solver.synthesize_boundary_tests(clean_code, [surviving_mutant])
    assert "validate_batch" in synth_tests

    # Verify execution against clean code
    runner = ParallelSandboxRunner(timeout_seconds=5)
    clean_res = runner.run_single(synth_tests, clean_code)
    assert clean_res.get("status") == "PASS"

    # Verify mutant killed
    mutant_res = runner.run_single(synth_tests, mutant_code)
    assert mutant_res.get("status") == "FAIL", "Mutant len(items) < 3 should be killed at len=3"


# ==============================================================================
# 3. Integration Test: Orchestrator Kills Boundary Survivors with Symbolic Solver
# ==============================================================================

def test_orchestrator_kills_boundary_survivors_with_symbolic_solver():
    pricing_target = (
        "def compute_tiered_rate(tier: int, volume: int) -> float:\n"
        "    if tier < 1:\n"
        "        raise ValueError('Invalid tier')\n"
        "    if volume >= 100:\n"
        "        return 0.15\n"
        "    elif volume >= 50:\n"
        "        return 0.10\n"
        "    elif volume >= 20:\n"
        "        return 0.05\n"
        "    return 0.0\n"
    )
    # Baseline test covering only volume=10 and volume=60 (leaving 20, 50, 100 boundaries surviving)
    initial_test = (
        "import pytest\n"
        "from target import compute_tiered_rate\n"
        "\n"
        "def test_rate_tier_valid():\n"
        "    assert compute_tiered_rate(1, 10) == 0.0\n"
        "    assert compute_tiered_rate(1, 60) == 0.10\n"
        "\n"
        "def test_rate_invalid_tier():\n"
        "    with pytest.raises(ValueError):\n"
        "        compute_tiered_rate(0, 50)\n"
    )

    with tempfile.TemporaryDirectory(prefix="testforge_symbolic_e2e_") as tmpdir:
        tmp_path = Path(tmpdir)
        target_file = tmp_path / "pricing.py"
        target_file.write_text(pricing_target, encoding="utf-8")

        orch = TestForgeOrchestrator(
            target_source_code=pricing_target,
            initial_test_code=initial_test,
            target_file_path=str(target_file),
            max_iterations=2,
            target_mutation_score=85.0,
            engine_mode="legacy",
        )

        final_state = orch.run()

        # DEF-022 Clean Integrity
        assert final_state.baseline_tests_failed == 0
        assert final_state.baseline_tests_passed >= 2

        # Verify that mutants were generated and killed
        mspace = orch.blackboard.get_mutant_space()
        assert mspace.mutants_generated > 0
        assert mspace.mutants_killed > 0

        # Verify that the test suite was hardened with boundary tests
        hardened_code = orch.state.current_test_code
        assert "compute_tiered_rate" in hardened_code

