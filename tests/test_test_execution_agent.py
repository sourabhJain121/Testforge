"""
test_test_execution_agent.py - Comprehensive Verification for TestExecutionAgent.

Verifies:
  1. Instantiation with Google ADK constructs (LlmAgent, Runner, InMemorySessionService).
  2. Sandboxed test execution in subprocess isolation without in-process execution.
  3. Accurate parsing of passed, failed, skipped, and error tests.
  4. Failure diagnostic extraction with structured failure records.
  5. Timeout enforcement on infinite loops returning TIMEOUT.
  6. Non-hallucinated line coverage measurement.
  7. Blackboard ExecutionSpace and SuiteSpace synchronization.
  8. Cancellation handling without process hang.
  9. In-process A2A communication protocol via A2ABroker.
  10. Parallel mutant evaluation coordination.
"""

import threading
import time

import pytest

from testforge.a2a import (
    A2ABroker,
    A2AMessage,
    A2APerformative,
    TestExecutionPayload,
)
from testforge.blackboard import Blackboard
from testforge.callbacks import CallbackRegistry, EventType
from testforge.execution_agent import ExecutionModelBridge, TestExecutionAgent
from testforge.state import MutantRecord

SAMPLE_TARGET = """
def add(a: int, b: int) -> int:
    return a + b

def divide(a: int, b: int) -> float:
    if b == 0:
        raise ValueError("Division by zero")
    return a / b
"""

PASSING_TESTS = """
from target import add, divide
import pytest

def test_add_positive():
    assert add(2, 3) == 5

def test_divide_valid():
    assert divide(10, 2) == 5.0

def test_divide_zero():
    with pytest.raises(ValueError):
        divide(10, 0)
"""

FAILING_TESTS = """
from target import add

def test_add_fail():
    assert add(2, 3) == 999
"""

SYNTAX_ERROR_TESTS = """
def test_syntax_broken(
    assert True
"""

TIMEOUT_TESTS = """
import time

def test_infinite_loop():
    while True:
        time.sleep(0.01)
"""


def test_execution_agent_instantiation():
    """Verify official Google ADK components and configuration."""
    agent = TestExecutionAgent()
    assert agent.agent_id == "agent:google-adk:test-execution"
    assert agent.adk_agent.name == "test_execution_agent"
    assert agent.adk_agent.output_schema == TestExecutionPayload
    assert agent.session_service is not None
    assert agent.runner is not None


def test_clean_tests_execution():
    """Verify clean tests execute in sandbox and return PASSED status."""
    agent = TestExecutionAgent()
    res = agent.execute_tests(
        test_code=PASSING_TESTS,
        target_code=SAMPLE_TARGET,
        measure_coverage=True,
        job_id="job_exec_pass",
    )

    assert isinstance(res, TestExecutionPayload)
    assert res.status == "PASSED"
    assert res.total_tests == 3
    assert res.passed_tests == 3
    assert res.failed_tests == 0
    assert res.error_tests == 0
    assert res.line_coverage_pct > 0.0
    assert len(res.failures) == 0


def test_failing_assertion_execution():
    """Verify failing tests are accurately caught with failure diagnostics."""
    agent = TestExecutionAgent()
    res = agent.execute_tests(
        test_code=FAILING_TESTS,
        target_code=SAMPLE_TARGET,
        measure_coverage=False,
        job_id="job_exec_fail",
    )

    assert res.status == "FAILED"
    assert res.passed_tests == 0
    assert res.failed_tests == 1
    assert len(res.failures) >= 1
    assert "test_add_fail" in res.failures[0].get("test_id", "") or "assert add(2, 3) == 999" in res.failures[0].get("error_message", "")


def test_syntax_error_execution():
    """Verify syntax errors in test code produce ERROR status without crashing."""
    agent = TestExecutionAgent()
    res = agent.execute_tests(
        test_code=SYNTAX_ERROR_TESTS,
        target_code=SAMPLE_TARGET,
        measure_coverage=False,
        job_id="job_exec_syntax",
    )

    assert res.status == "ERROR"
    assert res.total_tests == 0
    assert res.passed_tests == 0
    assert len(res.stderr) > 0


def test_timeout_enforcement():
    """Verify infinite loop tests are terminated by timeout guardrail."""
    agent = TestExecutionAgent(timeout_seconds=2.0)
    t0 = time.perf_counter()
    res = agent.execute_tests(
        test_code=TIMEOUT_TESTS,
        target_code=SAMPLE_TARGET,
        measure_coverage=False,
        timeout_seconds=2.0,
        job_id="job_exec_timeout",
    )
    elapsed = time.perf_counter() - t0

    assert res.status == "TIMEOUT"
    assert res.passed_tests == 0
    assert elapsed < 5.0  # Must enforce strict timeout


def test_blackboard_execution_space_sync():
    """Verify execution metrics and failures update Blackboard ExecutionSpace."""
    bb = Blackboard()
    agent = TestExecutionAgent(blackboard=bb)

    res = agent.execute_tests(
        test_code=PASSING_TESTS,
        target_code=SAMPLE_TARGET,
        measure_coverage=True,
        job_id="job_bb_exec",
    )

    exec_space = bb.get_execution_space()
    assert exec_space.status == "PASSED"
    assert exec_space.total_tests == 3
    assert exec_space.passed_tests == 3
    assert exec_space.line_coverage_pct == res.line_coverage_pct
    assert exec_space.branch_coverage == res.branch_coverage
    assert exec_space.total_branches == res.total_branches
    assert exec_space.covered_branches == res.covered_branches
    assert bb.get_metrics_space().branch_coverage == res.branch_coverage

    # Also check SuiteSpace sync
    suite_space = bb.get_suite_space()
    assert suite_space.baseline_passed is True
    assert suite_space.baseline_tests_executed == 3
    assert suite_space.baseline_tests_passed == 3


def test_cancellation_handling():
    """Verify pre-set cancellation event aborts execution immediately."""
    cancel_evt = threading.Event()
    cancel_evt.set()

    agent = TestExecutionAgent()
    res = agent.execute_tests(
        test_code=PASSING_TESTS,
        target_code=SAMPLE_TARGET,
        cancel_event=cancel_evt,
        job_id="job_cancelled",
    )

    assert res.status == "ERROR"
    assert "cancelled" in res.stderr.lower() or res.sandbox_metadata.get("status") == "CANCELLED"


def test_a2a_communication_handler():
    """Verify A2ABroker message routing for execute_tests."""
    broker = A2ABroker()
    agent = TestExecutionAgent()
    broker.register_handler(agent.agent_id, agent.handle_a2a_message)

    msg = A2AMessage(
        correlation_id="corr_exec_a2a_01",
        sender="agent:supervisor",
        recipient=agent.agent_id,
        performative=A2APerformative.REQUEST,
        action="execute_tests",
        payload={
            "job_id": "job_a2a_exec",
            "test_code": PASSING_TESTS,
            "target_code": SAMPLE_TARGET,
            "measure_coverage": True,
        }
    )

    resp = broker.send_message(msg)
    assert resp.performative == A2APerformative.INFORM
    assert resp.recipient == "agent:supervisor"
    assert resp.payload["status"] == "PASSED"
    assert resp.payload["total_tests"] == 3


def test_evaluate_mutants_coordination():
    """Verify evaluate_mutants coordinates parallel sandbox execution."""
    agent = TestExecutionAgent()

    mutated_code = """
def add(a: int, b: int) -> int:
    return a - b

def divide(a: int, b: int) -> float:
    if b == 0:
        raise ValueError("Division by zero")
    return a / b
"""

    mutant1 = MutantRecord(
        mutant_id="mut_001",
        mutation_type="AOR",
        line_number=3,
        original_code_snippet="return a + b",
        mutated_code_snippet=mutated_code,
        unified_diff="--- a\n+++ b\n@@ -3 +3 @@\n-return a + b\n+return a - b",
        original_source=SAMPLE_TARGET,
        mutated_source=mutated_code,
    )

    evaluated = agent.evaluate_mutants(
        test_code=PASSING_TESTS,
        mutants=[mutant1],
        baseline_passed=True,
        job_id="job_mut_eval",
    )

    assert len(evaluated) == 1
    # Mutant 1 changes add(2,3) from 5 to -1, which FAILS the test, thus mutant is KILLED!
    assert evaluated[0].status == "KILLED"
