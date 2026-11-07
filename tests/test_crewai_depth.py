"""
tests/test_crewai_depth.py

Automated test suite verifying Handout Feature F3: CrewAI Depth.
Tests the 3-Agent Cooperative Critic Crew, custom tools, memory,
and the typed TestHardeningFlow state machine.
"""

import os
import pytest

# Ensure CrewAI interactive prompts and telemetry are disabled
os.environ["CREWAI_TELEMETRY_OPT_OUT"] = "true"
os.environ["OTEL_SDK_DISABLED"] = "true"
os.environ["CREWAI_TESTING"] = "true"
os.environ["CREWAI_TRACING_ENABLED"] = "false"

from testforge.crew_critic import (
    MutantAnalystAgent,
    TestQualityReviewerAgent,
    RepairStrategistAgent,
    CriticCrew,
    MutationQualityCriticAgent,
    CrewAILLMBridge,
    tool_inspect_mutant_diff,
    tool_inspect_unreached_arcs,
    tool_analyze_assertion_density,
    tool_audit_tautological_assertions,
    tool_synthesize_repair_directives,
)
from testforge.flows.hardening_flow import (
    HardeningFlowState,
    TestHardeningFlow,
)
from testforge.a2a import (
    A2AMessage,
    A2APerformative,
    CriticDirectivePayload,
    MutationQualityCriticPayload,
)


class TestCooperativeCriticCrew:
    def test_three_agents_initialization_and_tool_bindings(self):
        bridge = CrewAILLMBridge()

        analyst = MutantAnalystAgent(llm=bridge)
        assert analyst.role == "AST Mutation Vulnerability Analyst"
        assert len(analyst.agent.tools) == 2
        tool_names = [t.name for t in analyst.agent.tools]
        assert "inspect_mutant_diff" in tool_names
        assert "inspect_unreached_arcs" in tool_names

        reviewer = TestQualityReviewerAgent(llm=bridge)
        assert reviewer.role == "Senior Test Suite Auditor"
        assert len(reviewer.agent.tools) == 2
        tool_names_rev = [t.name for t in reviewer.agent.tools]
        assert "analyze_assertion_density" in tool_names_rev
        assert "audit_tautological_assertions" in tool_names_rev

        strategist = RepairStrategistAgent(llm=bridge)
        assert strategist.role == "Test Hardening Strategist"
        assert len(strategist.agent.tools) == 1
        assert strategist.agent.tools[0].name == "synthesize_repair_directives"

    def test_custom_tools_execution(self):
        diff_res = tool_inspect_mutant_diff.run(mutant_diff="- if x < 10:\n+ if x <= 10:")
        assert "Mutant Diff Audit" in diff_res

        arc_res = tool_inspect_unreached_arcs.run(target_code="def foo(x):\n    if x > 0:\n        return True\n    return False\n")
        assert "Control Flow Audit" in arc_res

        density_res = tool_analyze_assertion_density.run(test_code="def test_a():\n    assert 1 == 1\n    assert 2 == 2\n")
        assert "Assertion Density Audit" in density_res

        tautology_res = tool_audit_tautological_assertions.run(test_code="def test_clean():\n    assert foo() == 42\n")
        assert "Tautology Audit" in tautology_res

        synth_res = tool_synthesize_repair_directives.run(mutant_findings="boundary escape", quality_findings="low density")
        assert "Repair Directives Formulated" in synth_res

    def test_critic_crew_sequential_execution_and_directives(self):
        crew = CriticCrew(memory=True)
        surviving_mutants = [
            {
                "mutant_id": "MUT_01",
                "operator": "RELATIONAL_OPERATOR_REPLACEMENT",
                "diff": "- if val < 100:\n+ if val <= 100:",
                "line_number": 5,
            }
        ]

        directive = crew.diagnose_mutants(
            target_source_code="def check(val):\n    return val < 100\n",
            surviving_diffs=["- if val < 100:\n+ if val <= 100:"],
            surviving_mutants=surviving_mutants,
            current_test_code="def test_val():\n    assert check(50) is True\n",
            iteration=1,
        )

        assert isinstance(directive, CriticDirectivePayload)
        assert len(directive.target_mutants) > 0
        assert "MUT_01" in directive.target_mutants
        assert len(directive.directives) > 0
        assert "MUT_01" in directive.failure_mechanisms
        assert directive.analysis != ""


class TestMutationQualityCriticIntegration:
    def test_critic_agent_delegates_to_cooperative_crew(self):
        critic = MutationQualityCriticAgent(use_cooperative_crew=True)
        assert critic.use_cooperative_crew is True
        assert isinstance(critic.cooperative_crew, CriticCrew)

        directive = critic.diagnose_mutants(
            target_source_code="def add(a, b): return a + b",
            surviving_diffs=["- return a + b\n+ return a - b"],
            surviving_mutants=[{"mutant_id": "MUT_ADD", "operator": "ARITHMETIC_OP"}],
            iteration=1,
        )

        assert isinstance(directive, CriticDirectivePayload)
        assert "MUT_ADD" in directive.target_mutants
        assert len(directive.directives) > 0

    def test_evaluate_quality_returns_tqs_and_dimensions(self):
        critic = MutationQualityCriticAgent()
        target_code = "def is_positive(x): return x > 0"
        test_code = "def test_pos(): assert is_positive(5) is True"
        mutants = [
            {"mutant_id": "M1", "status": "KILLED", "operator": "REL_OP"},
            {"mutant_id": "M2", "status": "SURVIVED", "operator": "REL_OP", "diff": "- return x > 0\n+ return x >= 0"},
        ]

        payload: MutationQualityCriticPayload = critic.evaluate_quality(
            target_source_code=target_code,
            current_test_code=test_code,
            mutants=mutants,
            iteration=1,
        )

        assert isinstance(payload, MutationQualityCriticPayload)
        assert payload.mutation_score == 50.0
        assert "M1" in payload.killed_mutants
        assert "M2" in payload.survived_mutants
        assert payload.test_quality_score is not None
        assert "assertion_strength" in payload.quality_dimensions
        assert "mutation_effectiveness" in payload.quality_dimensions

    def test_a2a_broker_dispatch(self):
        critic = MutationQualityCriticAgent()
        msg = A2AMessage(
            correlation_id="corr_test_01",
            sender="agent:orchestrator",
            recipient="agent:crewai:mutation-critic",
            performative=A2APerformative.REQUEST,
            action="evaluate_quality",
            payload={
                "target_source_code": "def target(x): return x * 2",
                "current_test_code": "def test_t(): assert target(2) == 4",
                "mutants": [{"mutant_id": "M1", "status": "KILLED"}],
            },
        )

        resp = critic.handle_a2a_message(msg)
        assert resp.performative == A2APerformative.INFORM
        assert resp.payload["mutation_score"] == 100.0


class TestCrewAIFlowArchitecture:
    def test_hardening_flow_state_model(self):
        state = HardeningFlowState(
            task_id="flow_test_01",
            target_code="def fn(): pass",
            mutation_score=75.0,
            target_score=85.0,
            max_iterations=3,
        )
        assert state.task_id == "flow_test_01"
        assert state.mutation_score == 75.0
        assert state.target_score == 85.0
        assert state.iteration_count == 0
        assert state.converged is False
        assert state.status == "INITIALIZED"

    def test_flow_router_branches_to_finalize_when_score_meets_target(self):
        flow = TestHardeningFlow()
        flow.state.mutation_score = 90.0
        flow.state.target_score = 85.0
        flow.state.surviving_mutants = []

        res = flow.kickoff()
        assert isinstance(res, dict)
        assert res["converged"] is True
        assert flow.state.status == "COMPLETED"
        assert flow.state.converged is True

    def test_flow_router_branches_to_repair_when_score_below_target(self):
        flow = TestHardeningFlow()
        flow.state.mutation_score = 40.0
        flow.state.target_score = 85.0
        flow.state.iteration_count = 0
        flow.state.max_iterations = 3
        flow.state.surviving_mutants = [{"mutant_id": "M1", "operator": "OP"}]

        res = flow.kickoff()
        assert res == "repair_step_complete"
        assert flow.state.status == "REPAIR_SYNTHESIZED"
        assert flow.state.mutation_score > 40.0

    def test_flow_router_branches_to_finalize_on_max_iterations(self):
        flow = TestHardeningFlow()
        flow.state.mutation_score = 50.0
        flow.state.target_score = 85.0
        # Start at max_iterations - 1 so run_critic_crew pushes it to max_iterations
        flow.state.iteration_count = 2
        flow.state.max_iterations = 3

        res = flow.kickoff()
        assert isinstance(res, dict)
        assert flow.state.status == "COMPLETED"
        assert flow.state.iteration_count == 3

    def test_flow_run_to_convergence(self):
        flow = TestHardeningFlow()
        flow.state.mutation_score = 30.0
        flow.state.target_score = 85.0
        flow.state.max_iterations = 4
        flow.state.surviving_mutants = [
            {"mutant_id": "M1", "operator": "OP1"},
            {"mutant_id": "M2", "operator": "OP2"},
            {"mutant_id": "M3", "operator": "OP3"},
        ]

        final_state = flow.run_to_convergence()
        assert final_state.converged is True
        assert final_state.mutation_score >= 85.0
        assert final_state.status == "COMPLETED"
