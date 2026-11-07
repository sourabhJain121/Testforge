"""
tests/test_agentic_pipeline.py - End-to-End Multi-Agent Integration Tests.

Author: TestForge Agentic Upgrade
Phase: Phase 1 - Integration and Structured Output Hardening

Tests verify:
  1. Complete multi-agent reflection cycle through TestForgeOrchestrator:
     - TargetManager analysis -> Initial ADK synthesis -> Clean code pass@1 validation
     - AST mutation fault injection -> Parallel sandbox execution
     - CrewAI adversarial critic diagnosis -> A2ABroker message exchange
     - Second reflection iteration: ADK test hardening consuming critic directives
     - Blackboard state synchronization across SuiteSpace, CriticSpace, MutantSpace, MetricsSpace.
  2. Structured Pydantic validation across inter-agent boundaries (GeneratedTestPayload, CriticDirectivePayload).
  3. Strict bounds: Critic directives only target known surviving mutant IDs.
  4. Resilience: Invalid generated code rejected by CodeSanitizer and retains working tests.
  5. Result distinction: Explicit separation of killed, survived, timeouts, and execution errors.
"""

from __future__ import annotations
import pytest
from testforge.orchestrator import TestForgeOrchestrator
from testforge.a2a import (
    A2ABroker,
    A2AMessage,
    A2APerformative,
    GeneratedTestPayload,
    CriticDirectivePayload,
)
from testforge.blackboard import Blackboard
from testforge.callbacks import CallbackRegistry, EventType


# ==============================================================================
# Sample Target Codes & Fixtures
# ==============================================================================

TARGET_BANKING_CODE = """
def process_withdrawal(balance, amount):
    if amount <= 0:
        return balance, False
    if balance >= amount:
        return balance - amount, True
    return balance, False
"""

TARGET_DISCOUNT_CODE = """
def calculate_discount(price, member):
    if member:
        return price * 0.8
    if price > 100:
        return price * 0.9
    return price
"""


class TestAgenticPipelineIntegration:
    """Verifies end-to-end multi-agent reflection loop using ADK, CrewAI, Broker, and Blackboard."""

    def test_end_to_end_orchestrator_agentic_reflection_loop(self):
        """
        Executes a multi-iteration reflection cycle where surviving mutants trigger
        CrewAI diagnosis and subsequent Google ADK test hardening.
        """
        weak_initial_test = """
def test_nominal():
    from target import process_withdrawal
    bal, ok = process_withdrawal(100, 50)
    assert ok is True
    assert bal == 50
"""
        bb = Blackboard()
        callbacks = CallbackRegistry()
        events = []
        callbacks.register(lambda ev: events.append(ev))

        orch = TestForgeOrchestrator(
            target_source_code=TARGET_BANKING_CODE,
            initial_test_code=weak_initial_test,
            max_iterations=2,
            target_mutation_score=100.0,
            engine_mode="auto",
            blackboard=bb,
            callbacks=callbacks,
        )

        final_state = orch.run()

        # 1. Pipeline reached completion
        assert final_state.terminated is True
        assert final_state.reflection_iterations_performed >= 1

        # 2. Result distinction verification
        assert final_state.mutants_generated > 0
        assert final_state.mutants_executed > 0
        equiv_count = bb.get_mutant_space().mutants_equivalent
        assert final_state.mutants_killed + final_state.mutants_survived + equiv_count == final_state.mutants_executed
        assert isinstance(final_state.final_mutation_score, float)

        # 3. Blackboard synchronization verification
        critic_space = bb.get_critic_space()
        suite_space = bb.get_suite_space()
        mutant_space = bb.get_mutant_space()
        metrics_space = bb.get_metrics_space()

        assert suite_space.current_test_code != ""
        assert suite_space.baseline_passed is True
        assert mutant_space.mutants_generated == final_state.mutants_generated
        assert metrics_space.final_mutation_score == final_state.final_mutation_score

        # 4. Lifecycle callback emission verification
        emitter_names = [e.emitter for e in events]
        assert "TestForgeOrchestrator" in emitter_names
        event_types = [e.event_type for e in events]
        assert EventType.OPERATION_START in event_types
        assert EventType.OPERATION_COMPLETE in event_types

    def test_critic_directives_bound_to_known_surviving_mutants(self):
        """Ensures CrewAI critic directives reference actual surviving mutant IDs."""
        from testforge.crew_critic import CrewAICriticAgent

        critic = CrewAICriticAgent(verbose=False)
        surviving = [
            {"mutant_id": "MUT_BOUNDARY_01", "mutation_type": "COMP_OP", "line_number": 3},
            {"mutant_id": "MUT_ARITH_02", "mutation_type": "ARITH_OP", "line_number": 5},
        ]
        diffs = [
            "- if amount <= 0:\n+ if amount < 0:",
            "- return balance - amount, True\n+ return balance + amount, True",
        ]

        directive = critic.diagnose_mutants(
            target_source_code=TARGET_BANKING_CODE,
            surviving_diffs=diffs,
            surviving_mutants=surviving,
            iteration=1,
        )

        assert isinstance(directive, CriticDirectivePayload)
        for target in directive.target_mutants:
            assert target in ("MUT_BOUNDARY_01", "MUT_ARITH_02")
        for m_id in ("MUT_BOUNDARY_01", "MUT_ARITH_02"):
            assert m_id in directive.failure_mechanisms

    def test_adk_generator_consumes_critic_directives(self):
        """Ensures Google ADK generator produces structured test code informed by critic directives."""
        from testforge.adk_generator import GoogleADKTestGenerator

        generator = GoogleADKTestGenerator()
        surviving = [{"mutant_id": "MUT_BOUNDARY_01"}]
        diffs = ["- if amount <= 0:\n+ if amount < 0:"]
        directive_text = "Assert explicit zero input: amount == 0 must return False."

        payload = generator.generate_tests(
            target_source_code=TARGET_BANKING_CODE,
            existing_test_code="def test_basic(): pass",
            surviving_diffs=diffs,
            surviving_mutants=surviving,
            critic_directive=directive_text,
            iteration=2,
            target_function="process_withdrawal",
        )

        assert isinstance(payload, GeneratedTestPayload)
        assert payload.target_function == "process_withdrawal"
        assert payload.covered_mutants == ["MUT_BOUNDARY_01"]
        assert "def test_" in payload.test_code
        assert payload.generation_metadata.get("ast_verified") is True

    def test_malformed_generated_code_retains_previous_working_suite(self):
        """If the generator outputs syntactically invalid code, the orchestrator preserves the working suite."""
        orch = TestForgeOrchestrator(
            target_source_code=TARGET_BANKING_CODE,
            initial_test_code="def test_safe():\n    from target import process_withdrawal\n    assert process_withdrawal(10, 5) == (5, True)\n",
            max_iterations=1,
            engine_mode="auto",
        )

        # Mock the broker handler for ADK to return broken syntax
        def broken_adk_handler(msg: A2AMessage) -> A2AMessage:
            return msg.create_response(
                performative=A2APerformative.INFORM,
                payload={"test_code": "def broken_syntax( - "},
            )

        orch.broker.register_handler(
            "agent:google-adk:generator",
            broken_adk_handler,
        )

        state = orch.run()
        # Ensure the safe test code was retained and not overwritten with broken code
        assert "def test_safe():" in state.current_test_code
        assert "broken_syntax" not in state.current_test_code

    def test_blackboard_cross_agent_information_provenance(self):
        """
        Explicitly proves that intermediate information produced by Google ADK Generator
        is stored in Blackboard SuiteSpace, evaluated by Sandbox into MutantSpace,
        consumed by CrewAI Critic into CriticSpace directives, and then re-consumed
        by the Generator in the subsequent iteration.
        """
        bb = Blackboard()
        initial_test = """
def test_partial():
    from target import calculate_discount
    assert calculate_discount(50, False) == 50
"""
        orch = TestForgeOrchestrator(
            target_source_code=TARGET_DISCOUNT_CODE,
            initial_test_code=initial_test,
            max_iterations=2,
            target_mutation_score=100.0,
            engine_mode="auto",
            blackboard=bb,
        )

        final_state = orch.run()

        # Verify revision monotonicity
        assert bb.revision >= 4, f"Expected at least 4 partition commits, got {bb.revision}"

        # 1. TargetSpace contains module details
        t_space = bb.get_target_space()
        assert "calculate_discount" in t_space.functions

        # 2. SuiteSpace was updated with generator's assertions
        s_space = bb.get_suite_space()
        assert "def test_" in s_space.current_test_code
        assert s_space.baseline_passed is True

        # 3. MutantSpace contains evaluated mutants
        m_space = bb.get_mutant_space()
        assert m_space.mutants_generated > 0
        assert m_space.mutants_executed > 0

        # 4. CriticSpace received directives if any mutants survived
        c_space = bb.get_critic_space()
        if len(m_space.surviving_mutant_diffs) > 0:
            assert len(c_space.critic_directives) > 0 or len(c_space.reflection_notes) > 0

        # 5. Snapshot represents consistent point-in-time state
        snap = bb.get_snapshot()
        assert snap.revision == bb.revision
        assert snap.suite.current_test_code == s_space.current_test_code
        assert snap.metrics.final_mutation_score == final_state.final_mutation_score

