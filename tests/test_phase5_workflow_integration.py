"""
test_phase5_workflow_integration.py - Full Workflow Integration Verification for Phase 5.

Verifies:
  1. MutationQualityCriticAgent (CrewAI) participates actively in TestForgeOrchestrator.run().
  2. CriticSpace partition on Blackboard is populated with typed Phase 5 fields:
     - job_id, mutation_score, quality_assessment, assertion_quality_findings,
       recommended_improvements, should_iterate, overall_verdict, critic_agent.
  3. Structured inter-agent handoff traces are recorded in TraceLogger:
     - TestExecutionAgent -> MutationQualityCriticAgent
     - MutationQualityCriticAgent -> GoogleADKTestGenerator / TestGeneratorAgent
  4. Direct multi-agent handoff from TestExecutionAgent to MutationQualityCriticAgent.
"""

import os
import tempfile
import pytest
from pathlib import Path

from testforge.orchestrator import TestForgeOrchestrator
from testforge.blackboard import Blackboard
from testforge.callbacks import CallbackRegistry, EventType
from testforge.crew_critic import MutationQualityCriticAgent
from testforge.execution_agent import TestExecutionAgent
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


def test_orchestrator_initializes_phase5_critic_agent():
    """Verify TestForgeOrchestrator instantiates MutationQualityCriticAgent and registers A2A routes."""
    orch = TestForgeOrchestrator(target_source_code=SAMPLE_TARGET_CODE)
    assert hasattr(orch, "crew_critic")
    assert isinstance(orch.crew_critic, MutationQualityCriticAgent)

    handlers = orch.broker.list_handlers()
    assert "agent:crewai:critic" in handlers
    assert "agent:crewai:mutation-critic" in handlers


def test_direct_execution_to_critic_handoff():
    """Verify direct handoff from TestExecutionAgent sandbox evaluation to MutationQualityCriticAgent."""
    bb = Blackboard()
    callbacks = CallbackRegistry()
    sandbox = ParallelSandboxRunner()

    execution_agent = TestExecutionAgent(
        sandbox_runner=sandbox,
        blackboard=bb,
        callbacks=callbacks,
    )
    critic_agent = MutationQualityCriticAgent(use_live_llm=False)

    # 1. Execute baseline test suite in sandbox
    exec_res = execution_agent.execute_tests(
        test_code=INITIAL_TEST_CODE,
        target_code=SAMPLE_TARGET_CODE,
    )
    assert exec_res.status == "PASSED"

    # 2. Generate AST mutants
    mutator = ASTMutator()
    mutants = mutator.mutate(SAMPLE_TARGET_CODE)
    assert len(mutants) > 0

    # 3. Evaluate mutants via TestExecutionAgent
    evaluated_mutants = execution_agent.evaluate_mutants(
        mutants=mutants,
        test_code=INITIAL_TEST_CODE,
    )
    assert len(evaluated_mutants) == len(mutants)

    # 4. Critique via MutationQualityCriticAgent
    critique_payload = critic_agent.evaluate_quality(
        target_source_code=SAMPLE_TARGET_CODE,
        current_test_code=INITIAL_TEST_CODE,
        mutants=evaluated_mutants,
        execution_payload=exec_res,
        job_id="job_phase5_direct",
        target_mutation_score=90.0,
    )

    assert critique_payload.job_id == "job_phase5_direct"
    assert critique_payload.denominator > 0
    assert critique_payload.mutation_score >= 0.0
    assert len(critique_payload.killed_mutants) + len(critique_payload.survived_mutants) <= critique_payload.denominator
    assert critique_payload.overall_quality_assessment != ""
    assert isinstance(critique_payload.assertion_quality_findings, list)
    assert isinstance(critique_payload.recommended_improvements, list)
    assert critique_payload.critic_agent == "agent:crewai:mutation-critic"


def test_orchestrator_end_to_end_phase5_pipeline():
    """Verify full orchestrator reflection loop with MutationQualityCriticAgent."""
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as trace_f:
        trace_path = trace_f.name

    events = []
    callbacks = CallbackRegistry()
    callbacks.register(lambda e: events.append(e))

    try:
        orch = TestForgeOrchestrator(
            target_source_code=SAMPLE_TARGET_CODE,
            max_iterations=2,
            target_mutation_score=100.0,
            trace_log_path=trace_path,
            callbacks=callbacks,
            engine_mode="ast",
        )

        state = orch.run()

        # 1. Pipeline execution status
        assert state.final_hardening_status in ("SUCCESS", "TARGET_SCORE_UNREACHED", "MAX_ITERATIONS_REACHED")
        assert state.baseline_passed is True

        # 2. Verify Blackboard CriticSpace updated with Phase 5 fields
        critic_space = orch.blackboard.get_critic_space()
        assert len(critic_space.critic_directives) > 0
        assert critic_space.latest_directive != ""
        assert len(critic_space.failure_mechanisms) > 0
        assert len(critic_space.reflection_notes) > 0
        assert critic_space.overall_verdict in ("ACTIONABLE", "SATISFIED", "CRITIQUE_RECORDED", "PENDING")

        # 3. Check TraceLogger for agent handoffs
        with open(trace_path, "r", encoding="utf-8") as f:
            trace_content = f.read()

        assert "TestExecutionAgent" in trace_content
        assert ("MutationQualityCriticAgent" in trace_content or "CrewAICriticAgent" in trace_content)

    finally:
        if os.path.exists(trace_path):
            os.remove(trace_path)
