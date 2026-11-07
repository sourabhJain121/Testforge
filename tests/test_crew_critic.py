"""
test_crew_critic.py - Unit and Integration Tests for Genuine CrewAI Adversarial Critic Agent.
"""

import json

import pytest
from crewai import Agent, Crew, Task

from testforge.a2a import (
    A2ABroker,
    A2AMessage,
    A2APerformative,
    CriticDirectivePayload,
)
from testforge.blackboard import Blackboard
from testforge.callbacks import CallbackRegistry, EventType
from testforge.crew_critic import CrewAICriticAgent, CrewAILLMBridge


class TestCrewAICriticAgent:
    def test_crewai_framework_classes_instantiated(self):
        critic = CrewAICriticAgent(verbose=False)
        assert isinstance(critic.crew_agent, Agent)
        assert "Senior Adversarial Mutation Testing Critic" in critic.crew_agent.role
        assert "AST mutants" in critic.crew_agent.goal
        assert isinstance(critic.llm_bridge, CrewAILLMBridge)

    def test_zero_surviving_mutants_fast_path(self):
        critic = CrewAICriticAgent(verbose=False)
        directive = critic.diagnose_mutants(
            target_source_code="def foo(): return 1",
            surviving_diffs=[],
            surviving_mutants=[],
            iteration=1,
        )
        assert isinstance(directive, CriticDirectivePayload)
        assert "All mutants killed" in directive.analysis
        assert len(directive.target_mutants) == 0
        assert len(directive.directives) == 0

    def test_genuine_crewai_crew_kickoff_execution(self):
        critic = CrewAICriticAgent(verbose=False)
        diff = "--- a/target.py\n+++ b/target.py\n@@ -1,2 +1,2 @@\n-    return a > b\n+    return a >= b"
        directive = critic.diagnose_mutants(
            target_source_code="def is_greater(a, b): return a > b",
            surviving_diffs=[diff],
            surviving_mutants=[{"mutant_id": "MUTANT_01"}],
            iteration=1,
        )
        assert isinstance(directive, CriticDirectivePayload)
        assert len(directive.target_mutants) >= 1
        assert "MUTANT_01" in directive.target_mutants
        assert len(directive.directives) >= 1
        assert "MUTANT_01" in directive.failure_mechanisms
        # Ensure directives address boundary conditions
        directive_text = " ".join(directive.directives).lower()
        assert "boundary" in directive_text or "equality" in directive_text

    def test_controlled_mock_llm_response(self):
        mock_payload = {
            "analysis": "Controlled mock analysis: operator swapped on line 12",
            "target_mutants": ["MUT_TEST_42"],
            "directives": ["Assert boundary at zero", "Assert strict equality with float epsilon"],
            "failure_mechanisms": {"MUT_TEST_42": "Inverted operator not reached by integer tests"},
        }
        bridge = CrewAILLMBridge(model="custom/test-mock", mock_response=mock_payload)
        critic = CrewAICriticAgent(llm_bridge=bridge, verbose=False)

        directive = critic.diagnose_mutants(
            target_source_code="def calc(x): return x * 10",
            surviving_diffs=["- return x * 10\n+ return x + 10"],
            surviving_mutants=[{"mutant_id": "MUT_TEST_42"}],
            iteration=2,
        )
        assert isinstance(directive, CriticDirectivePayload)
        assert directive.analysis == mock_payload["analysis"]
        assert directive.target_mutants == ["MUT_TEST_42"]
        assert directive.directives == mock_payload["directives"]
        assert directive.failure_mechanisms == mock_payload["failure_mechanisms"]

    def test_bounds_mutant_ids_to_known_survivors(self):
        # Mock LLM hallucinates an unknown mutant ID "MUT_HALLUCINATED_99"
        mock_payload = {
            "analysis": "Hallucinated mutant test",
            "target_mutants": ["MUT_HALLUCINATED_99", "MUT_VALID_01"],
            "directives": ["Strengthen assertions"],
            "failure_mechanisms": {"MUT_HALLUCINATED_99": "Bogus"},
        }
        bridge = CrewAILLMBridge(model="custom/test-mock", mock_response=mock_payload)
        critic = CrewAICriticAgent(llm_bridge=bridge, verbose=False)

        directive = critic.diagnose_mutants(
            target_source_code="def f(): pass",
            surviving_diffs=["diff"],
            surviving_mutants=[{"mutant_id": "MUT_VALID_01"}],
        )
        # Verify hallucinated mutant is filtered out
        assert directive.target_mutants == ["MUT_VALID_01"]

    def test_malformed_llm_output_graceful_fallback(self):
        # Return invalid non-JSON string
        bridge = CrewAILLMBridge(
            model="custom/test-mock",
            mock_response="This is raw text without JSON formatting.",
        )
        critic = CrewAICriticAgent(llm_bridge=bridge, verbose=False)

        directive = critic.diagnose_mutants(
            target_source_code="def f(): pass",
            surviving_diffs=["diff"],
            surviving_mutants=[{"mutant_id": "MUT_FALLBACK_01"}],
        )
        assert isinstance(directive, CriticDirectivePayload)
        assert len(directive.directives) > 0
        assert "MUT_FALLBACK_01" in directive.target_mutants

    def test_handle_a2a_message_success(self):
        critic = CrewAICriticAgent(verbose=False)
        req = A2AMessage(
            correlation_id="corr-a2a-crew",
            sender="agent:orchestrator",
            recipient="agent:crewai:critic",
            performative=A2APerformative.REQUEST,
            action="diagnose_mutants",
            payload={
                "target_source_code": "def sub(a, b): return a - b",
                "surviving_diffs": ["- return a - b\n+ return a + b"],
                "surviving_mutants": [{"mutant_id": "MUT_SUB_01"}],
                "iteration": 1,
            },
        )
        resp = critic.handle_a2a_message(req)
        assert resp.performative == A2APerformative.INFORM
        assert resp.correlation_id == "corr-a2a-crew"
        assert resp.action == "critique_complete"
        assert resp.sender == "agent:crewai:critic"
        assert resp.recipient == "agent:orchestrator"
        assert "analysis" in resp.payload
        assert "directives" in resp.payload

    def test_handle_a2a_message_unsupported_action(self):
        critic = CrewAICriticAgent(verbose=False)
        req = A2AMessage(
            correlation_id="corr-unsupported",
            sender="agent:orchestrator",
            recipient="agent:crewai:critic",
            performative=A2APerformative.REQUEST,
            action="generate_code",  # Critic only supports diagnose_mutants
        )
        resp = critic.handle_a2a_message(req)
        assert resp.performative == A2APerformative.REFUSE
        assert resp.payload.get("refusal_reason") == "UNSUPPORTED_ACTION"


class TestEndToEndBrokerCrewAICritic:
    def test_broker_crewai_critic_handoff_and_blackboard_sync(self):
        bb = Blackboard()
        cb = CallbackRegistry()
        events = []
        cb.register(lambda e: events.append(e))

        broker = A2ABroker(blackboard=bb, callback_registry=cb)
        critic = CrewAICriticAgent(verbose=False)
        broker.register_handler(
            agent_id="agent:crewai:critic",
            handler=critic.handle_a2a_message,
            allowed_actions=["diagnose_mutants"],
            allowed_senders=["agent:orchestrator"],
        )

        req = A2AMessage(
            correlation_id="cycle-e2e-101",
            sender="agent:orchestrator",
            recipient="agent:crewai:critic",
            performative=A2APerformative.REQUEST,
            action="diagnose_mutants",
            payload={
                "target_source_code": "def check(val): return val > 0",
                "surviving_diffs": ["- return val > 0\n+ return val >= 0"],
                "surviving_mutants": [{"mutant_id": "MUT_ZERO_01"}],
                "iteration": 1,
            },
        )

        resp = broker.send_message(req)
        assert resp.performative == A2APerformative.INFORM
        assert resp.correlation_id == "cycle-e2e-101"

        # Verify Blackboard CriticSpace was atomically updated
        critic_space = bb.get_critic_space()
        assert len(critic_space.critic_directives) >= 1
        assert "MUT_ZERO_01" in critic_space.failure_mechanisms
        assert len(critic_space.reflection_notes) >= 1
        assert "cycle-e2e-101" in critic_space.reflection_notes[-1]

        # Verify lifecycle callbacks were emitted
        event_types = [e.event_type for e in events]
        assert EventType.AGENT_HANDOFF in event_types
        assert EventType.OPERATION_COMPLETE in event_types

        # Verify broker history recorded scrubbed messages
        history = broker.get_history()
        assert len(history) == 2
        assert history[0].action == "diagnose_mutants"
        assert history[1].action == "critique_complete"
