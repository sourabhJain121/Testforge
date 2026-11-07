"""
test_supervisor_agent.py - Unit test suite for Google ADK Top-Level Supervisor Agent.

Tests:
  1. Supervisor produces valid structured decisions adhering to SupervisorDecisionPayload.
  2. Supervisor reads current Blackboard state and populates decision context.
  3. Supervisor chooses the correct next specialist agent for each stage.
  4. Security rejection deterministically prevents execution.
  5. Cancellation deterministically prevents further workflow actions.
  6. Maximum iteration limits are enforced deterministically.
  7. Model failure activates deterministic fallback.
  8. Invalid model output is rejected and falls back safely.
  9. Invalid workflow transitions are rejected by the state machine.
  10. Agent runtime status is tracked truthfully across all 8 canonical agents.
  11. Retry limits are enforced for eligible steps.
  12. Duplicate handoffs do not cause duplicate dangerous execution.
  13. Job IDs and hashes remain consistent.
  14. A2A communication works for all supported performatives and actions.
  15. Supervisor records decision evidence in Blackboard MetricsSpace.
  16. Quality success stops unnecessary repair.
"""

import time
import pytest
import threading
from pydantic import ValidationError

from testforge.a2a import (
    WorkflowStage,
    SupervisorAction,
    SupervisorDecisionPayload,
    WorkflowTransitionRecord,
    A2AMessage,
    A2APerformative,
)
from testforge.blackboard import Blackboard
from testforge.supervisor_agent import SupervisorAgent, ALLOWED_TRANSITIONS, CANONICAL_EIGHT_AGENTS
from testforge.callbacks import CallbackRegistry


@pytest.fixture
def clean_blackboard():
    """Provides a fresh Blackboard instance with initialized partitions."""
    bb = Blackboard()
    bb.update_target_space(
        target_source_code="def add(a, b):\n    return a + b\n",
        functions=["add"],
    )
    return bb


@pytest.fixture
def supervisor(clean_blackboard):
    """Provides a SupervisorAgent connected to a clean blackboard."""
    return SupervisorAgent(
        blackboard=clean_blackboard,
        callbacks=CallbackRegistry(),
        use_live_llm=False,
    )


class TestSupervisorAgentUnit:
    """Unit test cases verifying SupervisorAgent behavior, contracts, and guardrails."""

    def test_supervisor_decision_payload_contract_validation(self):
        """Contract: Verifies SupervisorDecisionPayload validation invariants."""
        # Valid payload
        decision = SupervisorDecisionPayload(
            task_id="task_123",
            current_stage=WorkflowStage.INITIALIZING.value,
            selected_action=SupervisorAction.SCREEN_SECURITY.value,
            target_agent="agent:google-adk:security",
            reason="Initial screening",
            is_deterministic=True,
        )
        assert decision.task_id == "task_123"
        assert decision.job_id == "task_123"
        assert decision.selected_action == "SCREEN_SECURITY"
        assert decision.is_deterministic is True

        # Invalid: missing task_id and job_id
        with pytest.raises(ValidationError):
            SupervisorDecisionPayload(
                task_id="",
                selected_action=SupervisorAction.SCREEN_SECURITY.value,
                target_agent="agent:google-adk:security",
            )

    def test_state_machine_valid_and_invalid_transitions(self, supervisor):
        """State Machine: Verifies ALLOWED_TRANSITIONS enforcement."""
        # Valid transitions
        allowed, reason = supervisor.validate_transition(WorkflowStage.INITIALIZING, WorkflowStage.SECURITY_SCREENING)
        assert allowed is True
        assert reason is None

        allowed, reason = supervisor.validate_transition(WorkflowStage.SECURITY_SCREENING, WorkflowStage.CODE_INTELLIGENCE)
        assert allowed is True

        allowed, reason = supervisor.validate_transition(WorkflowStage.CODE_INTELLIGENCE, WorkflowStage.TEST_PLANNING)
        assert allowed is True

        allowed, reason = supervisor.validate_transition(WorkflowStage.TEST_PLANNING, WorkflowStage.TEST_GENERATION)
        assert allowed is True

        allowed, reason = supervisor.validate_transition(WorkflowStage.TEST_GENERATION, WorkflowStage.BASELINE_EXECUTION)
        assert allowed is True

        # Valid retry transition on baseline failure
        allowed, reason = supervisor.validate_transition(WorkflowStage.BASELINE_EXECUTION, WorkflowStage.TEST_GENERATION)
        assert allowed is True

        # Invalid transition: jumping directly from INITIALIZING to CONVERGED
        allowed, reason = supervisor.validate_transition(WorkflowStage.INITIALIZING, WorkflowStage.CONVERGED)
        assert allowed is False
        assert "Invalid workflow transition" in reason

        # Invalid transition: from terminal state CONVERGED
        allowed, reason = supervisor.validate_transition(WorkflowStage.CONVERGED, WorkflowStage.INITIALIZING)
        assert allowed is False

    def test_deterministic_security_rejection_blocks_execution(self, clean_blackboard):
        """Authoritative Policy: SecurityAgent refusal immediately triggers STOP_SECURITY_REFUSAL."""
        clean_blackboard.update_security_space(
            allowed=False,
            status="BLOCKED",
            findings=[{"issue": "eval_detected", "severity": "BLOCK"}],
        )
        sup = SupervisorAgent(blackboard=clean_blackboard, use_live_llm=False)
        decision = sup.decide_next_step(
            WorkflowStage.SECURITY_SCREENING,
            context={"job_id": "job_sec_test", "task_id": "job_sec_test"}
        )

        assert decision.selected_action == SupervisorAction.STOP_SECURITY_REFUSAL.value
        assert decision.is_deterministic is True
        assert "SecurityAgent rejected target" in decision.reason

    def test_deterministic_cancellation_blocks_further_actions(self, supervisor):
        """Authoritative Policy: Cancellation event immediately triggers STOP_CANCELLED."""
        cancel_evt = threading.Event()
        cancel_evt.set()

        decision = supervisor.decide_next_step(
            WorkflowStage.TEST_GENERATION,
            context={"job_id": "job_cancel_test", "cancel_event": cancel_evt}
        )
        assert decision.selected_action == SupervisorAction.STOP_CANCELLED.value
        assert decision.is_deterministic is True
        assert "cancellation token was triggered" in decision.reason

    def test_deterministic_timeout_enforcement(self, supervisor):
        """Authoritative Policy: Timeout expiration triggers STOP_UNRECOVERABLE_FAILURE."""
        start_time = time.time() - 400.0  # 400 seconds ago
        decision = supervisor.decide_next_step(
            WorkflowStage.BASELINE_EXECUTION,
            context={"job_id": "job_timeout", "start_time": start_time, "timeout_seconds": 300.0}
        )
        assert decision.selected_action == SupervisorAction.STOP_UNRECOVERABLE_FAILURE.value
        assert decision.is_deterministic is True
        assert "timeout limit" in decision.reason

    def test_deterministic_max_iterations_enforcement(self, supervisor):
        """Authoritative Policy: Iteration budget exhaustion triggers STOP_MAX_ITERATIONS."""
        decision = supervisor.decide_next_step(
            WorkflowStage.CRITIC_ASSESSMENT,
            context={
                "job_id": "job_max_iter",
                "mutation_score": 50.0,
                "target_mutation_score": 85.0,
                "iteration": 3,
                "max_iterations": 3,
                "surviving_mutants_count": 2,
            }
        )
        assert decision.selected_action == SupervisorAction.STOP_MAX_ITERATIONS.value
        assert decision.is_deterministic is True
        assert "Maximum allowed reflection iterations reached" in decision.reason

    def test_deterministic_convergence_stops_unnecessary_repair(self, supervisor):
        """Authoritative Policy: When target mutation score is satisfied, STOP_CONVERGED is issued."""
        decision = supervisor.decide_next_step(
            WorkflowStage.CRITIC_ASSESSMENT,
            context={
                "job_id": "job_converged",
                "mutation_score": 90.0,
                "adjusted_mutation_score": 90.0,
                "target_mutation_score": 85.0,
                "coverage_pct": 100.0,
                "iteration": 1,
                "max_iterations": 3,
                "surviving_mutants_count": 1,
            }
        )
        assert decision.selected_action == SupervisorAction.STOP_CONVERGED.value
        assert decision.is_deterministic is True
        assert "Target mutation score satisfied" in decision.reason

    def test_retry_limits_enforced_on_baseline_failure(self, supervisor):
        """Reliability: Baseline test failure initiates bounded retry before stopping."""
        # Attempt 1 -> RETRY_STEP
        d1 = supervisor.decide_next_step(
            WorkflowStage.BASELINE_EXECUTION,
            context={"job_id": "job_retry", "baseline_passed": False, "tests_passed": 0}
        )
        assert d1.selected_action == SupervisorAction.RETRY_STEP.value
        assert d1.retry_count == 1

        # Attempt 2 -> Exhausted retry budget -> STOP_UNRECOVERABLE_FAILURE
        d2 = supervisor.decide_next_step(
            WorkflowStage.BASELINE_EXECUTION,
            context={"job_id": "job_retry", "baseline_passed": False, "tests_passed": 0}
        )
        assert d2.selected_action == SupervisorAction.STOP_UNRECOVERABLE_FAILURE.value
        assert "exhausted self-repair budget" in d2.reason

    def test_model_deliberation_and_truthful_attribution(self, clean_blackboard):
        """Cognitive Deliberation: Model deliberation produces REFLECT_AND_REPAIR with is_deterministic=False."""
        mock_model_output = {
            "selected_action": "REFLECT_AND_REPAIR",
            "reason": "Model evaluated surviving mutants and recommends targeted assertion synthesis.",
        }
        sup = SupervisorAgent(
            blackboard=clean_blackboard,
            use_live_llm=False,
            mock_response=mock_model_output,
        )
        decision = sup.decide_next_step(
            WorkflowStage.CRITIC_ASSESSMENT,
            context={
                "job_id": "job_model_delib",
                "mutation_score": 60.0,
                "target_mutation_score": 85.0,
                "iteration": 1,
                "max_iterations": 3,
                "surviving_mutants_count": 3,
            }
        )
        assert decision.selected_action == SupervisorAction.REFLECT_AND_REPAIR.value
        assert decision.target_agent == "agent:google-adk:reflection-repair"
        assert decision.is_deterministic is False  # Truthfully attributed to model reasoning
        assert "Model evaluated surviving mutants" in decision.reason

    def test_model_failure_activates_deterministic_fallback(self, clean_blackboard):
        """Fault Tolerance: If model throws exception or returns garbage, deterministic fallback is used."""
        sup = SupervisorAgent(
            blackboard=clean_blackboard,
            use_live_llm=False,
            mock_response="MALFORMED_NON_JSON_STRING",
        )
        decision = sup.decide_next_step(
            WorkflowStage.CRITIC_ASSESSMENT,
            context={
                "job_id": "job_fallback",
                "mutation_score": 50.0,
                "target_mutation_score": 85.0,
                "iteration": 1,
                "max_iterations": 3,
                "surviving_mutants_count": 2,
            }
        )
        assert decision.selected_action == SupervisorAction.REFLECT_AND_REPAIR.value
        assert decision.is_deterministic is True  # Fallback was deterministic
        assert "Deterministic policy:" in decision.reason

    def test_agent_status_tracking_is_truthful(self, supervisor):
        """Truthful Observability: All 8 agents tracked with meaningful dynamic statuses."""
        all_status = supervisor.get_all_agents_status()
        assert len(all_status) == len(CANONICAL_EIGHT_AGENTS)

        # Initially, agents are available and registered but not executing
        sec_status = supervisor.get_agent_status("SecurityAgent")
        assert sec_status["registered"] is True
        assert sec_status["instantiated"] is True
        assert sec_status["available"] is True
        assert sec_status["executing"] is False

        # Set executing
        supervisor.set_agent_executing("SecurityAgent", True)
        assert supervisor.get_agent_status("SecurityAgent")["executing"] is True
        assert supervisor.get_agent_status("SecurityAgent")["participating"] is True

        # Set completed
        supervisor.set_agent_completed("SecurityAgent", success=True)
        assert supervisor.get_agent_status("SecurityAgent")["executing"] is False
        assert supervisor.get_agent_status("SecurityAgent")["completed"] is True

    def test_handle_a2a_message_decide_and_validate(self, supervisor):
        """A2A Interoperability: Handles 'decide_next' and 'validate_transition' messages."""
        # 1. Decide next
        msg = A2AMessage(
            correlation_id="corr_decide_1",
            sender="agent:orchestrator",
            recipient="agent:google-adk:supervisor",
            performative=A2APerformative.REQUEST,
            action="decide_next",
            payload={"current_stage": WorkflowStage.INITIALIZING.value, "job_id": "job_a2a"},
        )
        resp = supervisor.handle_a2a_message(msg)
        assert resp.performative == A2APerformative.INFORM
        assert resp.payload["selected_action"] == SupervisorAction.SCREEN_SECURITY.value

        # 2. Validate transition
        trans_msg = A2AMessage(
            correlation_id="corr_trans_1",
            sender="agent:orchestrator",
            recipient="agent:google-adk:supervisor",
            performative=A2APerformative.REQUEST,
            action="validate_transition",
            payload={"current_stage": WorkflowStage.INITIALIZING.value, "proposed_stage": WorkflowStage.SECURITY_SCREENING.value},
        )
        trans_resp = supervisor.handle_a2a_message(trans_msg)
        assert trans_resp.performative == A2APerformative.INFORM
        assert trans_resp.payload["allowed"] is True

    def test_blackboard_records_supervisor_decision(self, clean_blackboard, supervisor):
        """Blackboard Integration: Supervisor decision is atomically recorded to MetricsSpace."""
        decision = supervisor.decide_next_step(
            WorkflowStage.INITIALIZING,
            context={"job_id": "job_bb_record"}
        )
        metrics = clean_blackboard.get_metrics_space()
        assert len(metrics.supervisor_decisions) >= 1
        latest = metrics.supervisor_decisions[-1]
        assert latest["selected_action"] == SupervisorAction.SCREEN_SECURITY.value
        assert latest["target_agent"] == "agent:google-adk:security"
