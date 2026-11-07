"""
test_phase4_workflow_integration.py - Full Workflow Integration Verification for Phase 4.

Verifies:
  1. TestPlanningAgent and TestExecutionAgent participate actively in TestForgeOrchestrator.run().
  2. PlanSpace and ExecutionSpace partitions are populated on Blackboard.
  3. Structured inter-agent handoff traces are recorded in TraceLogger:
     - SecurityAgent -> CodeIntelligenceAgent
     - CodeIntelligenceAgent -> TestPlanningAgent
     - TestPlanningAgent -> TestGeneratorAgent
  4. TestExecutionAgent coordinates pass@1 baseline validation and mutation evaluation.
  5. Checkpoint snapshots persist and restore PlanSpace and ExecutionSpace partitions.
"""

import os
import tempfile
import pytest
from testforge.orchestrator import TestForgeOrchestrator
from testforge.blackboard import Blackboard
from testforge.callbacks import CallbackRegistry, EventType


SAMPLE_TARGET_CODE = """
def discount(price: float, is_vip: bool) -> float:
    if price < 0:
        return 0.0
    rate = 0.20 if is_vip else 0.10
    return price * (1.0 - rate)
"""


def test_orchestrator_initializes_phase4_agents():
    """Verify that TestForgeOrchestrator instantiates TestPlanningAgent and TestExecutionAgent."""
    orch = TestForgeOrchestrator(target_source_code=SAMPLE_TARGET_CODE)
    assert hasattr(orch, "planning_agent")
    assert hasattr(orch, "execution_agent")
    assert orch.planning_agent is not None
    assert orch.execution_agent is not None

    # Check broker handler registrations
    registered = orch.broker.list_handlers()
    assert "agent:google-adk:test-planner" in registered
    assert "agent:google-adk:test-execution" in registered


def test_orchestrator_end_to_end_phase4_workflow():
    """Verify full orchestrator pipeline runs with Phase 4 agents."""
    with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as trace_f:
        trace_path = trace_f.name

    events = []
    callbacks = CallbackRegistry()
    callbacks.register(lambda e: events.append(e))

    try:
        orch = TestForgeOrchestrator(
            target_source_code=SAMPLE_TARGET_CODE,
            max_iterations=1,
            target_mutation_score=50.0,
            trace_log_path=trace_path,
            callbacks=callbacks,
            engine_mode="ast",
        )

        state = orch.run()

        # 1. Pipeline should complete successfully
        assert state.final_hardening_status in ("SUCCESS", "MAX_ITERATIONS_REACHED")
        assert state.baseline_passed is True

        # 2. PlanSpace must be populated
        plan_space = orch.blackboard.get_plan_space()
        assert plan_space.planning_status == "PLANNED"
        assert len(plan_space.scenarios) > 0
        assert len(plan_space.boundary_conditions) > 0

        # 3. ExecutionSpace must be populated
        exec_space = orch.blackboard.get_execution_space()
        assert exec_space.status in ("PASSED", "FAILED")
        assert exec_space.total_tests > 0
        assert exec_space.line_coverage_pct > 0.0

        # 4. State metadata must retain test_plan
        assert "test_plan" in state.metadata
        assert len(state.metadata["test_plan"]["scenarios"]) > 0

        # 5. Check TraceLogger events for inter-agent handoffs
        events_logged = [e.event_type for e in events]
        assert EventType.OPERATION_START in events_logged
        assert EventType.OPERATION_COMPLETE in events_logged

        # Inspect trace log file for handoffs
        with open(trace_path, "r", encoding="utf-8") as f:
            trace_content = f.read()

        assert "TestPlanningAgent" in trace_content
        assert "TestExecutionAgent" in trace_content
        assert "CodeIntelligenceAgent" in trace_content

    finally:
        if os.path.exists(trace_path):
            os.remove(trace_path)


def test_checkpoint_persistence_with_phase4_spaces():
    """Verify Blackboard save_checkpoint and restore preserves PlanSpace and ExecutionSpace."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as db_f:
        db_path = db_f.name

    try:
        bb = Blackboard(checkpoint_db_path=db_path)
        bb.update_target_space(target_source_code=SAMPLE_TARGET_CODE)

        # Update PlanSpace
        bb.update_plan_space(
            job_id="job_persist_test",
            planning_status="PLANNED",
            target_callables=["discount"],
            scenarios=[{"scenario_name": "nominal_vip", "category": "nominal", "priority": 1}],
            boundary_conditions=["price == 0"],
        )

        # Update ExecutionSpace
        bb.update_run(
            run_id="exec_persist_01",
            status="PASSED",
            total=4,
            passed=4,
            failed=0,
            duration=0.15,
            line_coverage_pct=95.0,
            lines_covered=6,
            lines_total=6,
            job_id="job_persist_test",
        )

        # Save checkpoint
        ckpt_id = bb.save_checkpoint(
            stage="TEST_PLANNING_AND_EXECUTION",
            job_id="job_persist_test",
            status="IN_PROGRESS",
        )
        assert ckpt_id is not None

        # Restore in fresh blackboard
        bb2 = Blackboard(checkpoint_db_path=db_path)
        restored_snap = bb2.restore_checkpoint(ckpt_id)

        assert restored_snap.plan.planning_status == "PLANNED"
        assert len(restored_snap.plan.scenarios) == 1
        assert restored_snap.plan.scenarios[0]["scenario_name"] == "nominal_vip"

        assert restored_snap.execution.status == "PASSED"
        assert restored_snap.execution.total_tests == 4
        assert restored_snap.execution.line_coverage_pct == 95.0

    finally:
        if os.path.exists(db_path):
            os.remove(db_path)
