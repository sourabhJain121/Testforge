"""
test_mutation_quality_critic_agent.py - Unit and Contract Tests for Phase 5
CrewAI Mutation & Quality Critic Agent.
"""

import time
import pytest
from pydantic import ValidationError

from testforge.a2a import (
    A2AMessage,
    A2APerformative,
    MutationQualityCriticPayload,
    CriticDirectivePayload,
    A2ABroker,
)
from testforge.blackboard import Blackboard
from testforge.mutator import MutantRecord
from testforge.crew_critic import (
    MutationQualityCriticAgent,
    CrewAICriticAgent,
    CrewAILLMBridge,
    TestQualityAnalyzer,
)


class TestMutationQualityCriticUnit:
    """Tests for MutationQualityCriticAgent and TestQualityAnalyzer."""

    def test_alias_backward_compatibility(self):
        """CrewAICriticAgent must be an alias for MutationQualityCriticAgent."""
        assert CrewAICriticAgent is MutationQualityCriticAgent

    def test_quality_analyzer_detects_weak_and_tautological_assertions(self):
        """TestQualityAnalyzer flags assert True, assert x == x, assert is not None, and assert bool."""
        bad_test_code = (
            "import pytest\n\n"
            "def test_tautology_and_weak():\n"
            "    x = 10\n"
            "    assert True\n"
            "    assert not False\n"
            "    assert x == x\n"
            "    assert x is not None\n"
            "    assert bool(x)\n"
            "    assert len([1, 2]) >= 0\n"
        )
        findings = TestQualityAnalyzer.analyze(bad_test_code)
        categories = {f["category"] for f in findings}
        assert "TAUTOLOGY" in categories
        assert "WEAK_ASSERTION" in categories

        tautologies = [f for f in findings if f["category"] == "TAUTOLOGY"]
        assert len(tautologies) >= 3  # True, not False, x == x

        weak = [f for f in findings if f["category"] == "WEAK_ASSERTION"]
        assert len(weak) >= 3  # is not None, bool(x), len >= 0

    def test_quality_analyzer_detects_missing_assertions(self):
        """Test function with no assert statements or pytest.raises is flagged."""
        empty_test = (
            "def test_no_assertions():\n"
            "    x = 5 + 5\n"
        )
        findings = TestQualityAnalyzer.analyze(empty_test)
        categories = [f["category"] for f in findings]
        assert "MISSING_ASSERTION" in categories
        assert findings[0]["severity"] == "HIGH"

    def test_quality_analyzer_detects_broad_exceptions(self):
        """Using pytest.raises(Exception) is flagged as overly broad."""
        broad_test = (
            "import pytest\n\n"
            "def test_broad():\n"
            "    with pytest.raises(Exception):\n"
            "        raise ValueError('boom')\n"
        )
        findings = TestQualityAnalyzer.analyze(broad_test)
        categories = [f["category"] for f in findings]
        assert "BROAD_EXCEPTION" in categories

    def test_quality_analyzer_handles_syntax_error(self):
        """Malformed test code produces a SYNTAX_ERROR finding without raising."""
        malformed = "def test_broken(:\n    assert True"
        findings = TestQualityAnalyzer.analyze(malformed)
        assert len(findings) == 1
        assert findings[0]["category"] == "SYNTAX_ERROR"

    def test_mutation_score_calculation_no_fabrication(self):
        """Score is calculated strictly from executed MutantRecords without fabrication."""
        critic = MutationQualityCriticAgent(use_live_llm=False)
        target_source = "def add(a, b): return a + b\n"
        test_code = "def test_add(): assert add(1, 2) == 3\n"

        mutants = [
            MutantRecord(
                mutant_id="MUT_01",
                original_code_snippet="return a + b",
                mutated_code_snippet="return a - b",
                unified_diff="--- original\n+++ mutated\n@@ -1 +1 @@\n-return a + b\n+return a - b\n",
                status="KILLED",
                mutation_type="AOR",
                line_number=1,
            ),
            MutantRecord(
                mutant_id="MUT_02",
                original_code_snippet="return a + b",
                mutated_code_snippet="return a * b",
                unified_diff="--- original\n+++ mutated\n@@ -1 +1 @@\n-return a + b\n+return a * b\n",
                status="SURVIVED",
                mutation_type="AOR",
                line_number=1,
            ),
            MutantRecord(
                mutant_id="MUT_03",
                original_code_snippet="return a + b",
                mutated_code_snippet="return a + 0",
                unified_diff="--- original\n+++ mutated\n@@ -1 +1 @@\n-return a + b\n+return a + 0\n",
                status="POTENTIALLY_EQUIVALENT",
                mutation_type="EQUIV",
                line_number=1,
            ),
        ]

        payload = critic.evaluate_quality(
            target_source_code=target_source,
            current_test_code=test_code,
            mutants=mutants,
            target_mutation_score=85.0,
        )

        assert isinstance(payload, MutationQualityCriticPayload)
        assert payload.killed_mutants == ["MUT_01"]
        assert payload.survived_mutants == ["MUT_02"]
        assert payload.equivalent_mutants == ["MUT_03"]
        # Denominator = killed (1) + survived (1) = 2. Score = 50.0%
        assert payload.denominator == 2
        assert payload.mutation_score == 50.0
        assert payload.should_iterate is True  # 50.0% < 85.0%

    def test_full_kill_cleans_reflection_decision(self):
        """When 100% of mutants are killed and assertions are clean, should_iterate is False."""
        critic = MutationQualityCriticAgent(use_live_llm=False)
        target_source = "def is_positive(x): return x > 0\n"
        clean_test = (
            "def test_positive():\n"
            "    assert is_positive(1) is True\n"
            "    assert is_positive(-1) is False\n"
            "    assert is_positive(0) is False\n"
        )
        mutants = [
            MutantRecord(
                mutant_id="MUT_01",
                original_code_snippet="x > 0",
                mutated_code_snippet="x >= 0",
                unified_diff="--- orig\n+++ mut\n@@ -1 +1 @@\n-x > 0\n+x >= 0\n",
                status="KILLED",
                mutation_type="ROR",
                line_number=1,
            )
        ]

        payload = critic.evaluate_quality(
            target_source_code=target_source,
            current_test_code=clean_test,
            mutants=mutants,
            target_mutation_score=85.0,
        )
        assert payload.mutation_score == 100.0
        assert payload.survived_mutants == []
        assert payload.should_iterate is False

    def test_payload_contract_validation(self):
        """MutationQualityCriticPayload enforces valid ranges and required fields."""
        with pytest.raises(ValidationError):
            # Invalid score > 100.0
            MutationQualityCriticPayload(
                task_id="task_123",
                mutation_score=150.0,
            )

        with pytest.raises(ValidationError):
            # Empty task_id / job_id
            MutationQualityCriticPayload(
                task_id="",
                job_id="",
                mutation_score=50.0,
            )

    def test_to_directive_payload_conversion(self):
        """Payload converts cleanly to backward-compatible CriticDirectivePayload."""
        payload = MutationQualityCriticPayload(
            task_id="task_conv",
            mutation_score=60.0,
            denominator=5,
            killed_mutants=["M1", "M2", "M3"],
            survived_mutants=["M4", "M5"],
            directives=["Assert boundary 0", "Assert boundary negative"],
            failure_mechanisms={"M4": "Off-by-one comparison", "M5": "Missing zero check"},
            overall_quality_assessment="Need more boundary tests",
        )
        directive = payload.to_directive_payload()
        assert isinstance(directive, CriticDirectivePayload)
        assert directive.target_mutants == ["M4", "M5"]
        assert len(directive.directives) >= 2
        assert "M4" in directive.failure_mechanisms

    def test_handle_a2a_evaluate_quality_action(self):
        """MutationQualityCriticAgent processes A2AMessage with action='evaluate_quality'."""
        critic = MutationQualityCriticAgent(use_live_llm=False)
        msg = A2AMessage(
            correlation_id="corr_eval_1",
            sender="agent:orchestrator",
            recipient="agent:crewai:mutation-critic",
            performative=A2APerformative.REQUEST,
            action="evaluate_quality",
            payload={
                "target_source_code": "def double(x): return x * 2\n",
                "current_test_code": "def test_double(): assert double(2) == 4\n",
                "mutants": [
                    {
                        "mutant_id": "M1",
                        "status": "SURVIVED",
                        "diff": "--- orig\n+++ mut\n-return x * 2\n+return x + 2\n",
                        "line_number": 1,
                    }
                ],
                "iteration": 1,
                "job_id": "job_a2a_test",
            }
        )

        resp = critic.handle_a2a_message(msg)
        assert resp.performative == A2APerformative.INFORM
        assert resp.action == "quality_evaluation_complete"
        assert resp.payload["mutation_score"] == 0.0
        assert resp.payload["survived_mutants"] == ["M1"]
        assert resp.payload["should_iterate"] is True

    def test_blackboard_sync_via_broker(self):
        """Broker synchronizes MutationQualityCriticPayload into Blackboard CriticSpace."""
        bb = Blackboard()
        broker = A2ABroker(blackboard=bb)
        critic = MutationQualityCriticAgent(use_live_llm=False)

        broker.register_handler(
            "agent:crewai:mutation-critic",
            critic.handle_a2a_message,
        )

        msg = A2AMessage(
            correlation_id="corr_sync_bb",
            sender="agent:orchestrator",
            recipient="agent:crewai:mutation-critic",
            performative=A2APerformative.REQUEST,
            action="evaluate_quality",
            payload={
                "target_source_code": "def mult(a, b): return a * b\n",
                "current_test_code": "def test_mult(): assert mult(2, 3) == 6\n",
                "mutants": [
                    {"mutant_id": "M1", "status": "KILLED", "line_number": 1},
                    {"mutant_id": "M2", "status": "SURVIVED", "line_number": 1},
                ],
                "iteration": 1,
                "job_id": "job_sync_test",
            }
        )

        resp = broker.send_message(msg)
        assert resp.performative == A2APerformative.INFORM

        # Verify Blackboard CriticSpace was atomically updated
        cs = bb.get_critic_space()
        assert cs.job_id == "job_sync_test"
        assert cs.mutation_score == 50.0
        assert cs.should_iterate is True
        assert cs.overall_verdict == "ACTIONABLE"
        assert len(cs.critic_directives) > 0
        assert cs.critic_agent == "agent:crewai:mutation-critic"
        assert cs.evaluated_at is not None

