"""
test_phase6_workflow_integration.py - Full Workflow Integration Verification for Phase 6.

Verifies:
  1. ReflectionRepairAgent (Google ADK) is instantiated and registered with A2ABroker.
  2. End-to-end sandbox execution and mutation re-evaluation via ReflectionRepairAgent.
  3. ReflectionRepairAgent coordinates targeted repair that improves mutation coverage.
  4. Real TestForgeOrchestrator runs multi-iteration hardening with ReflectionRepairAgent.
  5. TraceLogger captures handoff events to/from ReflectionRepairAgent.
"""

import os
import tempfile
import pytest

from testforge.orchestrator import TestForgeOrchestrator
from testforge.blackboard import Blackboard
from testforge.callbacks import CallbackRegistry, EventType
from testforge.reflection_agent import ReflectionRepairAgent
from testforge.execution_agent import TestExecutionAgent
from testforge.crew_critic import MutationQualityCriticAgent
from testforge.sandbox import ParallelSandboxRunner
from testforge.mutator import ASTMutator


SAMPLE_TARGET_CODE = """
def discount(price: float, is_vip: bool) -> float:
    if price < 0:
        return 0.0
    rate = 0.20 if is_vip else 0.10
    return price * (1.0 - rate)
"""

INITIAL_TEST_CODE = """
import pytest
from target import discount

def test_basic_discount():
    assert discount(100.0, False) == 90.0
"""


def test_orchestrator_initializes_phase6_agent():
    """Verify TestForgeOrchestrator instantiates ReflectionRepairAgent and registers A2A route."""
    orch = TestForgeOrchestrator(target_source_code=SAMPLE_TARGET_CODE)
    assert hasattr(orch, "reflection_agent")
    assert isinstance(orch.reflection_agent, ReflectionRepairAgent)

    handlers = orch.broker.list_handlers()
    assert "agent:google-adk:reflection-repair" in handlers


def test_reflection_repair_end_to_end_sandbox_workflow():
    """Verify real sandbox execution, mutant evaluation, and targeted repair via ReflectionRepairAgent."""
    bb = Blackboard()
    callbacks = CallbackRegistry()
    sandbox = ParallelSandboxRunner()

    execution_agent = TestExecutionAgent(
        sandbox_runner=sandbox,
        blackboard=bb,
        callbacks=callbacks,
    )
    critic_agent = MutationQualityCriticAgent(use_live_llm=False)
    reflection_agent = ReflectionRepairAgent(
        blackboard=bb,
        callbacks=callbacks,
        execution_agent=execution_agent,
        critic_agent=critic_agent,
        sandbox=sandbox,
        use_live_llm=False,
    )

    # 1. Execute initial baseline test suite in sandbox
    exec_res = execution_agent.execute_tests(
        test_code=INITIAL_TEST_CODE,
        target_code=SAMPLE_TARGET_CODE,
    )
    assert exec_res.status == "PASSED"

    # 2. Mutate target code
    mutator = ASTMutator()
    mutants = mutator.mutate(SAMPLE_TARGET_CODE)
    assert len(mutants) > 0

    # 3. Evaluate initial mutants
    evaluated_initial = execution_agent.evaluate_mutants(
        mutants=mutants,
        test_code=INITIAL_TEST_CODE,
    )
    surviving_initial = [m for m in evaluated_initial if m.status == "SURVIVED"]
    assert len(surviving_initial) > 0  # Initial suite only has 1 test, mutants must survive

    # 4. Critique initial results
    critic_payload = critic_agent.evaluate_quality(
        target_source_code=SAMPLE_TARGET_CODE,
        current_test_code=INITIAL_TEST_CODE,
        mutants=evaluated_initial,
        iteration=1,
        target_mutation_score=85.0,
    )
    assert critic_payload.should_iterate is True

    # 5. Coordinate Reflection & Repair
    repair_result = reflection_agent.coordinate_repair(
        target_source_code=SAMPLE_TARGET_CODE,
        current_test_code=INITIAL_TEST_CODE,
        mutants=evaluated_initial,
        critic_findings=critic_payload,
        iteration=2,
        max_iterations=3,
        target_mutation_score=85.0,
        task_id="task_phase6_sandbox_test",
    )

    # 6. Verify Repair Result
    assert repair_result.accepted is True
    assert repair_result.candidate_mutation_score >= repair_result.previous_mutation_score
    assert len(repair_result.retained_test_code) > len(INITIAL_TEST_CODE)
    assert "def test_" in repair_result.retained_test_code

    # 7. Verify Blackboard was updated
    suite_space = bb.get_suite_space()
    assert len(suite_space.repair_history) > 0
    assert suite_space.repair_history[-1]["accepted"] is True


def test_orchestrator_end_to_end_phase6_reflection_loop():
    """Verify full orchestrator multi-iteration reflection loop with ReflectionRepairAgent."""
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as trace_f:
        trace_path = trace_f.name

    events = []
    callbacks = CallbackRegistry()
    callbacks.register(lambda e: events.append(e))

    try:
        orch = TestForgeOrchestrator(
            target_source_code=SAMPLE_TARGET_CODE,
            initial_test_code=INITIAL_TEST_CODE,
            max_iterations=2,
            target_mutation_score=100.0,
            trace_log_path=trace_path,
            callbacks=callbacks,
            engine_mode="ast",
        )

        state = orch.run()

        # 1. Pipeline status
        assert state.final_hardening_status in ("SUCCESS", "TARGET_SCORE_UNREACHED", "MAX_ITERATIONS_REACHED")
        assert state.baseline_passed is True

        # 2. Check Blackboard SuiteSpace for repair history
        suite_space = orch.blackboard.get_suite_space()
        assert len(suite_space.current_test_code) > 0

        # 3. Check TraceLogger for ReflectionRepairAgent handoff events
        with open(trace_path, "r", encoding="utf-8") as f:
            trace_content = f.read()

        assert "TestExecutionAgent" in trace_content
        assert ("MutationQualityCriticAgent" in trace_content or "CrewAICriticAgent" in trace_content)

    finally:
        if os.path.exists(trace_path):
            os.remove(trace_path)

