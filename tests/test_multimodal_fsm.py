"""
tests/test_multimodal_fsm.py

Automated Test Suite for Multimodal (Image/Diagram) Requirement Derivation for State Machines (Sub-Task 4.2).
"""

import ast
import os
import pytest

from testforge.multimodal_fsm import (
    FSMExtractionResult,
    MultimodalFSMDeriver,
    generate_fsm_diagram,
)
from testforge.mutator import ASTMutator
from testforge.sandbox import ParallelSandboxRunner


@pytest.fixture(scope="module")
def diagram_path(tmp_path_factory):
    """Generates a diagram fixture if not already present."""
    default_path = "tests/fixtures/fsm_diagram.png"
    if os.path.exists(default_path):
        return default_path
    return generate_fsm_diagram(default_path)


def test_generate_fsm_diagram_output(diagram_path):
    assert os.path.exists(diagram_path)
    assert os.path.getsize(diagram_path) > 10000  # Valid non-empty PNG


def test_multimodal_deriver_extraction(diagram_path):
    deriver = MultimodalFSMDeriver()
    spec = deriver.extract_from_image(diagram_path)

    assert isinstance(spec, FSMExtractionResult)
    assert len(spec.states) >= 8
    assert "CREATED" in spec.states
    assert "COMPLETED" in spec.states
    assert "CANCELLED" in spec.states

    assert len(spec.transitions) >= 10
    assert "COMPLETED" in spec.terminal_states
    assert "CANCELLED" in spec.terminal_states
    assert "REFUNDED" in spec.terminal_states


def test_synthesized_test_suite_syntax(diagram_path):
    deriver = MultimodalFSMDeriver()
    spec = deriver.extract_from_image(diagram_path)
    test_code = deriver.synthesize_test_suite(spec)

    # Validate AST parses cleanly
    parsed = ast.parse(test_code)
    func_names = [n.name for n in ast.walk(parsed) if isinstance(n, ast.FunctionDef)]

    assert len(func_names) >= 6
    assert "test_nominal_order_forward_lifecycle" in func_names
    assert "test_terminal_states_cannot_transition" in func_names
    assert "test_admin_only_guards" in func_names
    assert "test_amount_threshold_guard" in func_names


def test_synthesized_tests_pass_clean_target(diagram_path):
    deriver = MultimodalFSMDeriver()
    spec = deriver.extract_from_image(diagram_path)
    test_code = deriver.synthesize_test_suite(spec)

    with open("samples/order_fsm.py", "r", encoding="utf-8") as f:
        clean_target = f.read()

    sandbox = ParallelSandboxRunner(target_file_path="samples/order_fsm.py")
    res = sandbox.validate_and_filter_candidate_suite(test_code, clean_target)
    assert res.overall_status in ("ALL_VALID", "PASS", "PARTIAL_PASS")
    assert res.retained_count >= 5


def test_synthesized_tests_kill_mutants(diagram_path):
    deriver = MultimodalFSMDeriver()
    spec = deriver.extract_from_image(diagram_path)
    test_code = deriver.synthesize_test_suite(spec)

    with open("samples/order_fsm.py", "r", encoding="utf-8") as f:
        clean_target = f.read()

    mutator = ASTMutator()
    mutants = mutator.mutate(clean_target)
    assert len(mutants) >= 50

    sandbox = ParallelSandboxRunner(target_file_path="samples/order_fsm.py")
    results = sandbox.evaluate_mutants_parallel(test_code, mutants, clean_target)

    killed = sum(1 for m in results if m.status == "KILLED")
    kill_rate = (killed / len(mutants)) * 100.0

    # Visually-derived test suite must kill at least 65% of mutants out-of-the-box
    assert kill_rate >= 65.0, f"Expected >= 65% kill rate, got {kill_rate:.1f}% ({killed}/{len(mutants)})"
