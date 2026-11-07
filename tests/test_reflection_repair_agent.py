"""
test_reflection_repair_agent.py - Unit and Contract Tests for Phase 6
Google ADK Reflection & Repair Agent.
"""

import hashlib
import pytest
from pydantic import ValidationError

from testforge.a2a import (
    A2AMessage,
    A2APerformative,
    RepairRequestPayload,
    RepairDirectivePayload,
    RepairResultPayload,
    ReflectionDecisionPayload,
    MutationQualityCriticPayload,
    A2ABroker,
)
from testforge.blackboard import Blackboard
from testforge.mutator import MutantRecord
from testforge.reflection_agent import (
    ReflectionRepairAgent,
    ReflectionModelBridge,
)


SAMPLE_TARGET = """
def calc_fee(amount: float, is_express: bool) -> float:
    if amount <= 0:
        return 0.0
    fee = 15.0 if is_express else 5.0
    return amount + fee
"""

INITIAL_TESTS = """
import pytest
from target import calc_fee

def test_nominal_fee():
    assert calc_fee(100.0, False) == 105.0

def test_zero_amount():
    assert calc_fee(0.0, False) == 0.0
"""


class TestReflectionRepairAgentUnit:
    """Unit tests for ReflectionRepairAgent deliberation, contracts, and non-regression."""

    def test_repair_directive_payload_contract_validation(self):
        """RepairDirectivePayload validates invariants and required fields."""
        directive = RepairDirectivePayload(
            task_id="task_contract_test",
            iteration=2,
            strategy="BOUNDARY_SYNTHESIS",
            targeted_mutants=["MUT_01", "MUT_02"],
            prescribed_assertions=[
                {"mutant_id": "MUT_01", "recommended_check": "assert calc_fee(-1, False) == 0.0"}
            ],
            rationale="Eliminate surviving relational operator mutant.",
        )
        assert directive.task_id == "task_contract_test"
        assert directive.iteration == 2
        assert len(directive.targeted_mutants) == 2
        assert directive.confidence == 1.0

        # Empty task_id must raise ValidationError
        with pytest.raises(ValidationError):
            RepairDirectivePayload(
                task_id="",
                job_id="",
                strategy="ASSERTION_HARDENING",
            )

    def test_repair_result_payload_contract_validation(self):
        """RepairResultPayload enforces score bounds and hash tracking."""
        res = RepairResultPayload(
            task_id="task_res_test",
            iteration=2,
            source_sha=hashlib.sha256(SAMPLE_TARGET.encode("utf-8")).hexdigest(),
            previous_test_sha="sha_prev_123",
            candidate_test_sha="sha_cand_456",
            accepted=True,
            previous_mutation_score=50.0,
            candidate_mutation_score=100.0,
            previous_test_count=2,
            candidate_test_count=4,
            retained_test_code=INITIAL_TESTS,
            mutants_killed=["MUT_01"],
            should_iterate=False,
            stop_reason="Target mutation score achieved.",
        )
        assert res.accepted is True
        assert res.candidate_mutation_score == 100.0
        assert res.should_iterate is False

    def test_reflection_model_bridge_mock_deliberation(self):
        """ReflectionModelBridge supports deterministic mock deliberation."""
        bridge = ReflectionModelBridge(use_live_llm=False)
        mock_directive = {
            "directive_id": "dir_mock_99",
            "task_id": "task_mock",
            "iteration": 2,
            "strategy": "BOUNDARY_SYNTHESIS",
            "targeted_mutants": ["MUT_BOUNDARY_01"],
            "missing_scenarios": ["Express shipping nominal fee"],
            "prescribed_assertions": [],
            "failing_tests_to_quarantine": [],
            "rationale": "Mock repair directive",
            "confidence": 1.0,
            "created_at": 1000.0,
        }
        bridge.set_mock_response(mock_directive)
        agent = ReflectionRepairAgent(model_bridge=bridge, use_live_llm=False)

        directive = agent.analyze_and_plan_repair(
            target_source_code=SAMPLE_TARGET,
            current_test_code=INITIAL_TESTS,
            surviving_mutants=[{"mutant_id": "MUT_BOUNDARY_01", "status": "SURVIVED"}],
            iteration=2,
            task_id="task_mock",
        )
        assert directive.directive_id == "dir_mock_99"
        assert directive.targeted_mutants == ["MUT_BOUNDARY_01"]
        assert directive.strategy == "BOUNDARY_SYNTHESIS"

    def test_reflection_repair_agent_identifies_surviving_mutants_and_prescribes_assertions(self):
        """ReflectionRepairAgent parses critic findings and forms actionable boundary directives."""
        agent = ReflectionRepairAgent(use_live_llm=False)
        critic_findings = MutationQualityCriticPayload(
            task_id="task_find_test",
            mutation_score=50.0,
            denominator=2,
            killed_mutants=["MUT_01"],
            survived_mutants=["MUT_02"],
            directives=["Assert express fee where is_express is True"],
            failure_mechanisms={"MUT_02": "Express branch unexercised"},
        )

        directive = agent.analyze_and_plan_repair(
            target_source_code=SAMPLE_TARGET,
            current_test_code=INITIAL_TESTS,
            surviving_mutants=[{"mutant_id": "MUT_02", "status": "SURVIVED"}],
            critic_findings=critic_findings,
            iteration=2,
            task_id="task_find_test",
        )
        assert directive.iteration == 2
        assert "MUT_02" in directive.targeted_mutants
        assert directive.strategy in ("ASSERTION_HARDENING", "BOUNDARY_SYNTHESIS")
        assert len(directive.prescribed_assertions) > 0

    def test_non_regression_rejection_when_score_regresses(self):
        """A candidate suite with a lower mutation score must be REJECTED to preserve the best suite."""
        agent = ReflectionRepairAgent(use_live_llm=False)
        mutants = [
            MutantRecord(
                mutant_id="MUT_01",
                original_code_snippet="return amount + fee",
                mutated_code_snippet="return amount - fee",
                unified_diff="--- a\n+++ b\n-return amount + fee\n+return amount - fee\n",
                status="KILLED",
                mutation_type="AOR",
                line_number=5,
            ),
            MutantRecord(
                mutant_id="MUT_02",
                original_code_snippet="if amount <= 0:",
                mutated_code_snippet="if amount < 0:",
                unified_diff="--- a\n+++ b\n-if amount <= 0:\n+if amount < 0:\n",
                status="SURVIVED",
                mutation_type="ROR",
                line_number=2,
            ),
        ]

        # Candidate test code that is deliberately worse / missing tests
        worse_candidate = (
            "import pytest\n"
            "from target import calc_fee\n\n"
            "def test_only_one():\n"
            "    assert calc_fee(100.0, False) == 105.0\n"
        )

        # Mock generator to return the worse candidate
        class MockGenerator:
            def generate_tests(self, **kwargs):
                from testforge.a2a import GeneratedTestPayload
                return GeneratedTestPayload(test_code=worse_candidate)

        agent.generator = MockGenerator()

        result = agent.coordinate_repair(
            target_source_code=SAMPLE_TARGET,
            current_test_code=INITIAL_TESTS,
            mutants=mutants,
            iteration=2,
            max_iterations=3,
            target_mutation_score=85.0,
            task_id="task_regr_test",
        )

        # Candidate must not replace better previous suite
        assert result.retained_test_code == INITIAL_TESTS
        assert result.rejection_reason is not None

    def test_rejection_when_candidate_fails_clean_target_validation(self):
        """A candidate test suite with broken syntax or assertions is rejected without corrupting existing suite."""
        agent = ReflectionRepairAgent(use_live_llm=False)
        broken_candidate = (
            "import pytest\n"
            "from target import calc_fee\n\n"
            "def test_broken_assertion():\n"
            "    assert calc_fee(100.0, False) == 999999.0\n"  # Wrong expectation, fails on clean code
        )

        class MockBrokenGenerator:
            def generate_tests(self, **kwargs):
                from testforge.a2a import GeneratedTestPayload
                return GeneratedTestPayload(test_code=broken_candidate)

        agent.generator = MockBrokenGenerator()

        mutants = [
            MutantRecord(
                mutant_id="MUT_01",
                original_code_snippet="return amount + fee",
                mutated_code_snippet="return amount - fee",
                unified_diff="--- a\n+++ b\n",
                status="SURVIVED",
                mutation_type="AOR",
                line_number=5,
            )
        ]

        result = agent.coordinate_repair(
            target_source_code=SAMPLE_TARGET,
            current_test_code=INITIAL_TESTS,
            mutants=mutants,
            iteration=2,
            max_iterations=3,
            target_mutation_score=85.0,
            task_id="task_broken_test",
        )

        assert result.accepted is False
        assert "clean-code validation" in result.rejection_reason or "quarantined" in result.rejection_reason
        assert result.retained_test_code == INITIAL_TESTS

    def test_iteration_limit_enforced_in_stop_reason(self):
        """When iteration reaches max_iterations, should_iterate is False and stop_reason is recorded."""
        agent = ReflectionRepairAgent(use_live_llm=False)
        mutants = [
            MutantRecord(
                mutant_id="MUT_01",
                original_code_snippet="if amount <= 0:",
                mutated_code_snippet="if amount < 0:",
                unified_diff="--- a\n+++ b\n-if amount <= 0:\n+if amount < 0:\n",
                status="SURVIVED",
                mutation_type="ROR",
                line_number=2,
            )
        ]

        result = agent.coordinate_repair(
            target_source_code=SAMPLE_TARGET,
            current_test_code=INITIAL_TESTS,
            mutants=mutants,
            iteration=3,
            max_iterations=3,
            target_mutation_score=95.0,
            task_id="task_limit_test",
        )

        assert result.should_iterate is False
        assert result.stop_reason is not None
        assert "iterations reached" in result.stop_reason.lower() or "target" in result.stop_reason.lower()

    def test_handle_a2a_plan_repair_and_repair_tests_actions(self):
        """A2A message handler supports 'plan_repair' and 'repair_tests'."""
        agent = ReflectionRepairAgent(use_live_llm=False)

        # 1. plan_repair
        plan_msg = A2AMessage(
            correlation_id="corr_plan_a2a",
            sender="agent:orchestrator",
            recipient="agent:google-adk:reflection-repair",
            performative=A2APerformative.REQUEST,
            action="plan_repair",
            payload={
                "target_source_code": SAMPLE_TARGET,
                "existing_test_code": INITIAL_TESTS,
                "surviving_mutants": [{"mutant_id": "M1", "status": "SURVIVED"}],
                "iteration": 2,
            }
        )
        plan_resp = agent.handle_a2a_message(plan_msg)
        assert plan_resp.performative == A2APerformative.INFORM
        assert plan_resp.action == "plan_repair_complete"
        assert "targeted_mutants" in plan_resp.payload

        # 2. Unsupported action
        bad_msg = A2AMessage(
            correlation_id="corr_bad",
            sender="agent:orchestrator",
            recipient="agent:google-adk:reflection-repair",
            performative=A2APerformative.REQUEST,
            action="unsupported_action",
            payload={}
        )
        bad_resp = agent.handle_a2a_message(bad_msg)
        assert bad_resp.performative == A2APerformative.REFUSE

    def test_blackboard_integration_records_repair_result(self):
        """Blackboard atomically records repair history and updates SuiteSpace when accepted."""
        bb = Blackboard()
        agent = ReflectionRepairAgent(blackboard=bb, use_live_llm=False)

        res = RepairResultPayload(
            task_id="task_bb_test",
            iteration=2,
            source_sha="src_sha_abc",
            previous_test_sha="prev_sha_123",
            candidate_test_sha="cand_sha_456",
            accepted=True,
            previous_mutation_score=50.0,
            candidate_mutation_score=90.0,
            retained_test_code=INITIAL_TESTS,
            should_iterate=False,
            stop_reason="Target reached",
        )
        agent._update_blackboard_and_dispatch(res)

        suite_space = bb.get_suite_space()
        assert suite_space.current_test_code == INITIAL_TESTS
        assert len(suite_space.repair_history) == 1
        assert suite_space.repair_history[0]["accepted"] is True
        assert suite_space.repair_history[0]["candidate_mutation_score"] == 90.0
