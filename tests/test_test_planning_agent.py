"""
test_test_planning_agent.py - Comprehensive Verification for TestPlanningAgent.

Verifies:
  1. Instantiation with Google ADK constructs (LlmAgent, Runner, InMemorySessionService).
  2. Consumption of CodeIntelligencePayload and AST symbol extraction.
  3. Formulation of nominal, boundary, negative, and exception scenarios.
  4. McCabe cyclomatic complexity-based prioritization.
  5. Content fingerprinting and deduplication of test scenarios.
  6. Detection of mock dependencies for external imports.
  7. Strict output validation conforming to TestPlanPayload.
  8. Synchronization to Blackboard PlanSpace partition.
  9. In-process A2A communication protocol via A2ABroker.
  10. Graceful handling of empty or malformed code intelligence inputs.
"""

import time

import pytest

from testforge.a2a import (
    A2ABroker,
    A2AMessage,
    A2APerformative,
    CodeIntelligencePayload,
    TestPlanPayload,
)
from testforge.blackboard import Blackboard
from testforge.callbacks import CallbackRegistry, EventType
from testforge.planning_agent import PlanningModelBridge, TestPlanningAgent

SAMPLE_SOURCE = """
def calculate_discount(price: float, quantity: int, is_vip: bool) -> float:
    if price < 0 or quantity < 0:
        raise ValueError("Invalid negative values")
    if quantity == 0:
        return price
    rate = 0.20 if is_vip else 0.10
    if price > 500:
        rate += 0.05
    return price * (1 - rate)
"""


@pytest.fixture
def sample_code_intel():
    return CodeIntelligencePayload(
        task_id="job_planning_test_01",
        target_module="discount.py",
        functions=[
            {
                "name": "calculate_discount",
                "args": ["price", "quantity", "is_vip"],
                "complexity": 5,
                "has_docstring": False,
            }
        ],
        classes=[],
        branches=[
            {"location": "line 3", "condition": "price < 0 or quantity < 0", "complexity_weight": 2},
            {"location": "line 5", "condition": "quantity == 0", "complexity_weight": 1},
            {"location": "line 7", "condition": "is_vip", "complexity_weight": 1},
            {"location": "line 8", "condition": "price > 500", "complexity_weight": 1},
        ],
        exception_paths=[
            {"location": "line 4", "exception_type": "ValueError", "message": "Invalid negative values"}
        ],
        dependencies=["math", "os"],
        complexity_risk={"cyclomatic_complexity": 5, "risk_category": "MEDIUM"},
        suggested_testing_targets=["calculate_discount"],
    )


def test_planning_agent_instantiation():
    """Verify official Google ADK components and configuration."""
    agent = TestPlanningAgent()
    assert agent.agent_id == "agent:google-adk:test-planner"
    assert agent.adk_agent.name == "test_planning_agent"
    assert agent.adk_agent.output_schema == TestPlanPayload
    assert agent.session_service is not None
    assert agent.runner is not None


def test_planning_from_code_intelligence(sample_code_intel):
    """Verify scenario generation from structured CodeIntelligencePayload."""
    agent = TestPlanningAgent()
    plan = agent.plan_tests(
        code_intelligence=sample_code_intel,
        job_id="job_plan_001",
        allocated_test_budget=10,
    )

    assert isinstance(plan, TestPlanPayload)
    assert plan.task_id == "job_plan_001"
    assert plan.job_id == "job_plan_001"
    assert len(plan.scenarios) > 0

    # Ensure all scenario categories exist
    categories = {s["category"] for s in plan.scenarios}
    assert "nominal" in categories
    assert "boundary" in categories
    assert "negative" in categories
    assert "exception" in categories

    # Boundary and negative cases should be populated
    assert len(plan.boundary_targets) > 0
    assert len(plan.negative_cases) > 0


def test_scenario_prioritization(sample_code_intel):
    """Verify that scenarios are prioritized logically with high priority first."""
    agent = TestPlanningAgent()
    plan = agent.plan_tests(code_intelligence=sample_code_intel, job_id="job_plan_002")

    priorities = [s["priority"] for s in plan.scenarios]
    # Priority values must be within valid range [1, 5]
    for p in priorities:
        assert 1 <= p <= 5

    # High complexity functions should yield priority 1 or 2 scenarios
    assert any(p in (1, 2) for p in priorities)


def test_scenario_deduplication(sample_code_intel):
    """Verify content fingerprinting eliminates duplicate scenario formulations."""
    agent = TestPlanningAgent()
    plan = agent.plan_tests(code_intelligence=sample_code_intel, job_id="job_plan_003")

    fingerprints = [s.get("fingerprint") for s in plan.scenarios]
    # Check that every scenario has a valid fingerprint
    assert all(fp and len(fp) == 16 for fp in fingerprints)
    # Check uniqueness
    assert len(fingerprints) == len(set(fingerprints))


def test_mock_dependency_detection():
    """Verify external library imports are tagged as mock dependencies."""
    intel = CodeIntelligencePayload(
        task_id="job_mock_test",
        target_module="network_client.py",
        functions=[{"name": "fetch_data", "args": ["url"], "complexity": 2}],
        dependencies=["requests", "urllib3", "redis", "sys"],
    )
    agent = TestPlanningAgent()
    plan = agent.plan_tests(code_intelligence=intel, job_id="job_mock_test")

    assert "requests" in plan.mock_dependencies
    assert "urllib3" in plan.mock_dependencies
    assert "redis" in plan.mock_dependencies
    assert "sys" not in plan.mock_dependencies


def test_blackboard_planspace_sync(sample_code_intel):
    """Verify planning results correctly update Blackboard PlanSpace partition."""
    bb = Blackboard()
    agent = TestPlanningAgent(blackboard=bb)

    plan = agent.plan_tests(code_intelligence=sample_code_intel, job_id="job_bb_sync")
    plan_space = bb.get_plan_space()

    assert plan_space.planning_status == "PLANNED"
    assert plan_space.job_id == "job_bb_sync"
    assert len(plan_space.scenarios) == len(plan.scenarios)
    assert len(plan_space.boundary_conditions) == len(plan.boundary_targets)
    assert len(plan_space.negative_cases) == len(plan.negative_cases)


def test_a2a_communication_handler(sample_code_intel):
    """Verify A2ABroker message routing and response formatting."""
    broker = A2ABroker()
    agent = TestPlanningAgent()
    broker.register_handler(agent.agent_id, agent.handle_a2a_message)

    msg = A2AMessage(
        correlation_id="corr_plan_a2a_01",
        sender="agent:supervisor",
        recipient=agent.agent_id,
        performative=A2APerformative.REQUEST,
        action="plan_tests",
        payload={
            "job_id": "job_a2a_plan",
            "code_intelligence": sample_code_intel.model_dump(),
            "allocated_test_budget": 8,
        }
    )

    resp = broker.send_message(msg)
    assert resp.performative == A2APerformative.INFORM
    assert resp.recipient == "agent:supervisor"
    assert "scenarios" in resp.payload
    assert resp.payload["job_id"] == "job_a2a_plan"


def test_empty_or_malformed_input_handling():
    """Verify agent gracefully handles empty or syntax-invalid source intelligence."""
    agent = TestPlanningAgent()

    # Empty payload dict
    plan = agent.plan_tests(code_intelligence={}, job_id="job_empty")
    assert isinstance(plan, TestPlanPayload)
    assert plan.status in ("PLANNED", "PARTIAL", "FAILED")

    # Raw string input
    plan_str = agent.plan_tests(code_intelligence="def foo(): pass", job_id="job_str")
    assert isinstance(plan_str, TestPlanPayload)
    assert len(plan_str.scenarios) > 0


def test_lifecycle_events_dispatched(sample_code_intel):
    """Verify OPERATION_START and OPERATION_COMPLETE lifecycle events are fired."""
    registry = CallbackRegistry()
    events = []
    registry.register(lambda e: events.append(e))

    agent = TestPlanningAgent(callbacks=registry)
    agent.plan_tests(code_intelligence=sample_code_intel, job_id="job_events")

    event_types = [e.event_type for e in events]
    assert EventType.OPERATION_START in event_types
    assert EventType.OPERATION_COMPLETE in event_types
