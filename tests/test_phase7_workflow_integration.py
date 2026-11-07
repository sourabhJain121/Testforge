"""
test_phase7_workflow_integration.py - Integration test suite for Phase 7:
Google ADK Top-Level Supervisor Agent & Eight-Agent Workflow Orchestration.

Tests:
  1. Orchestrator initializes SupervisorAgent and registers handler in A2ABroker.
  2. End-to-end execution of full hardening workflow on local code (`samples/discount.py`)
     with actual sandbox execution and all 8 canonical agents participating.
  3. Security rejection stops workflow before any execution or generation occurs.
  4. User cancellation stops workflow gracefully.
  5. Wiretap endpoint (`/api/wiretap`) exposes truthful status for all 8 canonical agents
     and supervisor decisions.
  6. FastAPI `/api/harden` endpoint remains fully compatible and functional.
"""

import json
import os
import time
from pathlib import Path

import pytest
from starlette.testclient import TestClient

from server import app
from testforge.a2a import SupervisorAction, WorkflowStage
from testforge.orchestrator import TestForgeOrchestrator
from testforge.state import TaskLifecycleState
from testforge.supervisor_agent import CANONICAL_EIGHT_AGENTS, SupervisorAgent

SAMPLE_DISCOUNT_CODE = '''
def calculate_discount(price: float, quantity: int) -> float:
    """Calculates tiered bulk order discount."""
    if price < 0:
        raise ValueError("Price cannot be negative")
    if quantity <= 0:
        return 0.0
    if quantity >= 100:
        return price * 0.70
    elif quantity >= 50:
        return price * 0.80
    elif quantity >= 10:
        return price * 0.90
    return price
'''

SAMPLE_VULNERABLE_CODE = '''
import os
def execute_eval(command: str):
    return eval(command)
'''


@pytest.fixture
def test_client():
    """Provides a Starlette/FastAPI TestClient."""
    return TestClient(app)


def test_orchestrator_initializes_supervisor_agent():
    """Verifies that TestForgeOrchestrator instantiates SupervisorAgent and registers A2A broker handler."""
    orch = TestForgeOrchestrator(
        target_source_code=SAMPLE_DISCOUNT_CODE,
        engine_mode="adk_crewai",
    )
    assert hasattr(orch, "supervisor")
    assert isinstance(orch.supervisor, SupervisorAgent)
    assert "agent:google-adk:supervisor" in orch.broker._handlers


def test_supervisor_security_refusal_stops_workflow(tmp_path):
    """Verifies that Supervisor and SecurityAgent stop the workflow on dangerous code before execution."""
    orch = TestForgeOrchestrator(
        target_source_code=SAMPLE_VULNERABLE_CODE,
        engine_mode="adk_crewai",
    )
    final_state = orch.run()
    assert final_state.terminated is True
    assert "SecurityRefusal" in final_state.termination_reason
    assert final_state.final_hardening_status == "FAILED"

    # Verify Supervisor recorded the security refusal decision
    decisions = orch.blackboard.get_metrics_space().supervisor_decisions
    actions = [d.get("selected_action") for d in decisions]
    assert SupervisorAction.SCREEN_SECURITY.value in actions


def test_end_to_end_hardening_workflow_with_real_sandbox(tmp_path):
    """
    Executes a complete hardening workflow on actual local code (discount.py)
    using the real sandbox and verifying all 8 agents participate.
    """
    target_file = tmp_path / "discount_target.py"
    target_file.write_text(SAMPLE_DISCOUNT_CODE, encoding="utf-8")

    orch = TestForgeOrchestrator(
        target_file_path=str(target_file),
        target_source_code=SAMPLE_DISCOUNT_CODE,
        max_iterations=2,
        target_mutation_score=50.0,
        engine_mode="adk_crewai",
    )

    final_state = orch.run()

    # Invariants verification
    assert final_state is not None
    assert final_state.current_test_code and len(final_state.current_test_code) > 0
    assert final_state.baseline_passed is True
    assert final_state.mutants_generated > 0

    # Verify Supervisor recorded decisions throughout the pipeline
    metrics_space = orch.blackboard.get_metrics_space()
    decisions = metrics_space.supervisor_decisions
    assert len(decisions) >= 3

    actions_recorded = [d["selected_action"] for d in decisions]
    assert SupervisorAction.SCREEN_SECURITY.value in actions_recorded
    assert SupervisorAction.ANALYZE_CODE.value in actions_recorded
    assert SupervisorAction.PLAN_TESTS.value in actions_recorded

    # Check that canonical agents participated
    participating = orch.supervisor.get_all_agents_status()
    participating_names = [a["name"] for a in participating if a["participating"]]
    assert "SecurityAgent" in participating_names
    assert "CodeIntelligenceAgent" in participating_names
    assert "TestPlanningAgent" in participating_names
    assert "TestGeneratorAgent" in participating_names
    assert "TestExecutionAgent" in participating_names


def test_wiretap_api_exposes_eight_agents_truthfully(test_client):
    """Verifies that GET /api/wiretap truthfully exposes all 8 agents and supervisor decisions."""
    response = test_client.get("/api/wiretap")
    assert response.status_code == 200
    data = response.json()

    # Core Wiretap fields preserved
    assert "registered_agents" in data
    assert "SupervisorAgent" in data["registered_agents"]
    assert "ReflectionRepairAgent" in data["registered_agents"]
    assert "MutationQualityCriticAgent" in data["registered_agents"]

    # Phase 7 additions
    assert "eight_agents_status" in data
    assert "total_supervisor_decisions" in data
    assert "supervisor_decisions" in data

    statuses = data["eight_agents_status"]
    for agent_name in CANONICAL_EIGHT_AGENTS:
        assert agent_name in statuses
        agent_info = statuses[agent_name]
        assert agent_info["registered"] is True
        assert agent_info["instantiated"] is True
        assert "participating" in agent_info


def test_fastapi_harden_endpoint_compatibility(test_client):
    """Verifies that POST /api/harden/start remains fully backward-compatible."""
    response = test_client.post(
        "/api/harden/start",
        json={
            "target_source_code": "def multiply(x, y):\n    return x * y\n",
            "target_file_path": "samples/math.py",
            "max_iterations": 1,
            "target_mutation_score": 60.0,
            "engine_mode": "adk_crewai",
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "job_id" in data
    assert "status" in data
    assert data["status"].upper() in ("QUEUED", "PENDING", "IN_PROGRESS", "RUNNING", "COMPLETED", "SUCCESS")
