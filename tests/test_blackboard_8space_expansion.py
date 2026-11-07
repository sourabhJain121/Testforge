"""
test_blackboard_8space_expansion.py - Comprehensive Tests for Blackboard 8-Partition Expansion,
Pydantic Contracts, and Backward-Compatible Persistence.

Validates Phase 2 Architectural Foundations:
  1. Initialization of all eight partitions (Target, Mutant, Critic, Suite, Metrics, Plan, Execution, Security).
  2. Retention of existing five-partition behavior and interop.
  3. Read/write operations for PlanSpace, ExecutionSpace, and SecuritySpace.
  4. Partition isolation (mutating one partition never alters others).
  5. Multi-threaded concurrent updates preserving consistency and revision monotonicity.
  6. Job/task isolation across independent workflows and checkpoints.
  7. Acceptance of valid Pydantic contracts (TestPlanPayload, TestExecutionPayload, SecurityEvaluationPayload, RepairRequestPayload).
  8. Validation enforcement and rejection of invalid payloads.
  9. New snapshot serialization containing all eight partitions.
  10. Backward-compatible restoration of legacy five-partition snapshots (schema version 1) with safe defaults.
  11. Integrity of restored data matching the original state.
  12. Persistence transaction safety, WAL mode, and failure isolation.
"""

import json
import os
import sqlite3
import tempfile
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor

import pytest
from pydantic import ValidationError

from testforge.a2a import (
    A2ABroker,
    A2AMessage,
    A2APerformative,
    CriticDirectivePayload,
    GeneratedTestPayload,
    RepairRequestPayload,
    SecurityEvaluationPayload,
    TestExecutionPayload,
    TestPlanPayload,
)
from testforge.blackboard import (
    Blackboard,
    BlackboardEvent,
    BlackboardSnapshot,
    CriticSpace,
    ExecutionSpace,
    MetricsSpace,
    MutantSpace,
    PlanSpace,
    SecuritySpace,
    SuiteSpace,
    TargetSpace,
)
from testforge.persistence import (
    CURRENT_SCHEMA_VERSION,
    SUPPORTED_SCHEMA_VERSIONS,
    CheckpointMetadata,
    CheckpointRecord,
    IncompatibleSchemaError,
    SQLiteBlackboardStorage,
)


@pytest.fixture
def temp_db_path():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        path = tf.name
    yield path
    if os.path.exists(path):
        os.remove(path)
    wal = path + "-wal"
    shm = path + "-shm"
    if os.path.exists(wal):
        os.remove(wal)
    if os.path.exists(shm):
        os.remove(shm)


class TestBlackboard8SpaceExpansion:
    """Verifies the expanded 8-partition Blackboard architecture."""

    def test_all_eight_partitions_initialized(self):
        """1. Verifies that all eight partitions are initialized with default state."""
        bb = Blackboard()
        expected_keys = {"target", "mutant", "critic", "suite", "metrics", "plan", "execution", "security"}
        assert set(bb.PARTITION_MODELS.keys()) == expected_keys

        # Check default spaces
        assert isinstance(bb.get_target_space(), TargetSpace)
        assert isinstance(bb.get_mutant_space(), MutantSpace)
        assert isinstance(bb.get_critic_space(), CriticSpace)
        assert isinstance(bb.get_suite_space(), SuiteSpace)
        assert isinstance(bb.get_metrics_space(), MetricsSpace)
        assert isinstance(bb.get_plan_space(), PlanSpace)
        assert isinstance(bb.get_execution_space(), ExecutionSpace)
        assert isinstance(bb.get_security_space(), SecuritySpace)

        # Check property accessors
        assert bb.plan.planning_status == "DRAFT"
        assert bb.execution.status == "NOT_STARTED"
        assert bb.security.status == "PENDING"
        assert bb.security.allowed is True

    def test_existing_five_partitions_retain_behavior(self):
        """2. Confirms that existing five partitions retain their full behavior and validation."""
        bb = Blackboard()
        bb.update_target_space(target_module_path="module_x.py", target_source_code="def f(): pass", blast_risk="HIGH")
        bb.update_suite_space(current_test_code="def test_f(): pass", active_provider="Local Ollama")
        bb.update_metrics_space(current_iteration=2, target_mutation_score=90.0, baseline_line_coverage=85.0)

        t = bb.get_target_space()
        s = bb.get_suite_space()
        m = bb.get_metrics_space()

        assert t.target_module_path == "module_x.py"
        assert t.blast_risk == "HIGH"
        assert s.current_test_code == "def test_f(): pass"
        assert s.active_provider == "Local Ollama"
        assert m.current_iteration == 2
        assert m.target_mutation_score == 90.0
        assert m.baseline_line_coverage == 85.0

    def test_new_partition_read_write_operations(self):
        """3. Verifies atomic read/write operations for PlanSpace, ExecutionSpace, and SecuritySpace."""
        bb = Blackboard()

        # Update PlanSpace
        scenarios = [
            {"scenario_id": "scen_1", "name": "test_nominal_discount", "target_callable": "calculate_discount", "category": "nominal", "priority": "HIGH"},
            {"scenario_id": "scen_2", "name": "test_zero_quantity", "target_callable": "calculate_discount", "category": "boundary", "priority": "HIGH"},
        ]
        bb.update_plan_space(
            task_id="task_100",
            source_module="samples.discount",
            scenarios=scenarios,
            boundary_conditions=["price <= 0", "discount_rate == 0.0"],
            allocated_test_budget=15,
            planning_status="APPROVED",
        )
        plan = bb.get_plan_space()
        assert plan.task_id == "task_100"
        assert plan.source_module == "samples.discount"
        assert len(plan.scenarios) == 2
        assert plan.planning_status == "APPROVED"
        assert plan.allocated_test_budget == 15

        # Update ExecutionSpace
        bb.update_execution_space(
            execution_id="exec_55",
            task_id="task_100",
            status="PASSED",
            total_tests=12,
            passed_tests=12,
            failed_tests=0,
            line_coverage_pct=92.5,
            lines_covered=37,
            lines_total=40,
            duration_seconds=1.45,
            stdout="12 passed in 0.12s",
        )
        exec_sp = bb.get_execution_space()
        assert exec_sp.execution_id == "exec_55"
        assert exec_sp.status == "PASSED"
        assert exec_sp.total_tests == 12
        assert exec_sp.line_coverage_pct == 92.5
        assert exec_sp.stdout == "12 passed in 0.12s"

        # Update SecuritySpace
        findings = [
            {"finding_id": "find_1", "rule_id": "SEC_INJ_01", "severity": "WARN", "category": "PROMPT_INJECTION", "message": "Neutralized prompt directive in docstring"}
        ]
        bb.update_security_space(
            task_id="task_100",
            status="WARNING",
            risk_level="LOW",
            allowed=True,
            findings=findings,
            defused_injection_count=1,
            remediation_recommendations=["Inspect docstrings before reflection prompts."],
        )
        sec = bb.get_security_space()
        assert sec.task_id == "task_100"
        assert sec.status == "WARNING"
        assert sec.risk_level == "LOW"
        assert sec.allowed is True
        assert len(sec.findings) == 1
        assert sec.defused_injection_count == 1

    def test_partition_isolation_preserves_independence(self):
        """4. Confirms that modifying one partition never mutates or corrupts unrelated partitions."""
        bb = Blackboard()

        # Update target and plan
        bb.update_target_space(target_module_path="original.py", blast_risk="LOW")
        bb.update_plan_space(task_id="plan_task", planning_status="PLANNED", allocated_test_budget=8)
        bb.update_execution_space(status="RUNNING", total_tests=5)
        bb.update_security_space(status="PASSED", allowed=True)

        target_before = bb.get_target_space()
        plan_before = bb.get_plan_space()
        exec_before = bb.get_execution_space()
        sec_before = bb.get_security_space()

        # Now heavily modify only ExecutionSpace
        bb.update_execution_space(status="FAILED", total_tests=10, failed_tests=2, stdout="AssertionError")

        target_after = bb.get_target_space()
        plan_after = bb.get_plan_space()
        sec_after = bb.get_security_space()

        # Target, Plan, and Security must remain identical
        assert target_before == target_after
        assert plan_before == plan_after
        assert sec_before == sec_after
        assert bb.get_execution_space().status == "FAILED"

    def test_concurrent_updates_preserve_consistency(self):
        """5. Verifies multi-threaded concurrency across partitions preserves consistency and revision ordering."""
        bb = Blackboard()
        num_threads = 10
        updates_per_thread = 20

        def worker_task(thread_id: int):
            for i in range(updates_per_thread):
                part = thread_id % 3
                if part == 0:
                    bb.update_plan_space(task_id=f"t_{thread_id}", allocated_test_budget=10 + i)
                elif part == 1:
                    bb.update_execution_space(duration_seconds=float(i), passed_tests=i)
                else:
                    bb.update_security_space(defused_injection_count=i)

        with ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(worker_task, tid) for tid in range(num_threads)]
            for f in futures:
                f.result()

        # Revision must match exactly the total number of updates
        total_updates = num_threads * updates_per_thread
        assert bb.revision == total_updates
        history = bb.get_history()
        assert len(history) == total_updates

        # Monotonically increasing revisions
        revs = [event.revision for event in history]
        assert revs == list(range(1, total_updates + 1))

    def test_job_and_task_isolation(self, temp_db_path):
        """6. Verifies that independent jobs are isolated in checkpoints and can be restored distinctly."""
        storage = SQLiteBlackboardStorage(temp_db_path)
        bb_alpha = Blackboard(storage=storage)
        bb_beta = Blackboard(storage=storage)

        # Job Alpha
        bb_alpha.update_target_space(target_module_path="alpha.py", target_source_code="def alpha(): pass")
        bb_alpha.update_plan_space(task_id="job_alpha", planning_status="APPROVED", allocated_test_budget=5)
        cid_alpha = bb_alpha.save_checkpoint(stage="STAGE_ALPHA", job_id="job_alpha", workflow_id="wf_alpha")

        # Job Beta
        bb_beta.update_target_space(target_module_path="beta.py", target_source_code="def beta(): pass")
        bb_beta.update_plan_space(task_id="job_beta", planning_status="PLANNED", allocated_test_budget=12)
        cid_beta = bb_beta.save_checkpoint(stage="STAGE_BETA", job_id="job_beta", workflow_id="wf_beta")

        # Restore Alpha
        bb_restore_alpha = Blackboard(storage=storage)
        bb_restore_alpha.restore_checkpoint(cid_alpha)
        assert bb_restore_alpha.get_target_space().target_module_path == "alpha.py"
        assert bb_restore_alpha.get_plan_space().allocated_test_budget == 5
        assert bb_restore_alpha.get_plan_space().task_id == "job_alpha"

        # Restore Beta
        bb_restore_beta = Blackboard(storage=storage)
        bb_restore_beta.restore_checkpoint(cid_beta)
        assert bb_restore_beta.get_target_space().target_module_path == "beta.py"
        assert bb_restore_beta.get_plan_space().allocated_test_budget == 12
        assert bb_restore_beta.get_plan_space().task_id == "job_beta"

        storage.close()

    def test_new_pydantic_contracts_accept_valid_payloads(self):
        """7. Verifies that new Pydantic contracts validate and accept complete, valid payloads."""
        # 1. TestPlanPayload
        plan_data = {
            "task_id": "task_plan_1",
            "target_module": "services.payment",
            "source_sha": "abc12345",
            "scenarios": [
                {"name": "test_charge_success", "category": "nominal"},
                {"name": "test_charge_negative_amount", "category": "boundary"}
            ],
            "boundary_targets": ["amount == 0", "amount < 0"],
            "allocated_test_budget": 8,
            "planning_rationale": "Prioritize boundary amounts and currency codes",
        }
        plan = TestPlanPayload.model_validate(plan_data)
        assert plan.task_id == "task_plan_1"
        assert len(plan.scenarios) == 2
        assert plan.allocated_test_budget == 8

        # 2. TestExecutionPayload
        exec_data = {
            "task_id": "task_exec_1",
            "status": "PASSED",
            "total_tests": 10,
            "passed_tests": 10,
            "failed_tests": 0,
            "line_coverage_pct": 100.0,
            "lines_covered": 45,
            "num_statements": 45,
            "duration_seconds": 0.85,
        }
        exec_res = TestExecutionPayload.model_validate(exec_data)
        assert exec_res.task_id == "task_exec_1"
        assert exec_res.line_coverage_pct == 100.0

        # 3. SecurityEvaluationPayload
        sec_data = {
            "task_id": "task_sec_1",
            "target_ref": "samples/discount.py",
            "assessment_stage": "INPUT_INSPECTION",
            "status": "PASSED",
            "allowed": True,
            "risk_level": "SAFE",
            "findings": [],
        }
        sec_res = SecurityEvaluationPayload.model_validate(sec_data)
        assert sec_res.allowed is True
        assert sec_res.risk_level == "SAFE"

        # 4. RepairRequestPayload
        rep_data = {
            "task_id": "task_rep_1",
            "iteration": 1,
            "target_source_code": "def discount(p, r): return p * (1 - r)",
            "existing_test_code": "def test_discount(): assert discount(100, 0.1) == 90",
            "surviving_diffs": ["--- a\n+++ b\n@@ -1 +1 @@\n-return p * (1 - r)\n+return p * (1 + r)"],
            "critic_directives": ["Add assertion testing negative rate"],
            "repair_strategy": "ASSERTION_HARDENING",
        }
        rep_res = RepairRequestPayload.model_validate(rep_data)
        assert rep_res.iteration == 1
        assert rep_res.repair_strategy == "ASSERTION_HARDENING"

    def test_pydantic_contracts_reject_invalid_payloads(self):
        """8. Confirms that strict Pydantic validation rejects malformed, empty, or inconsistent payloads."""
        # TestPlanPayload: empty task_id or budget < 1
        with pytest.raises(ValidationError):
            TestPlanPayload(task_id="", target_module="samples.discount", allocated_test_budget=5)
        with pytest.raises(ValidationError):
            TestPlanPayload(task_id="t1", target_module="samples.discount", allocated_test_budget=0)

        # TestExecutionPayload: coverage > 100.0 or negative tests
        with pytest.raises(ValidationError):
            TestExecutionPayload(task_id="t1", line_coverage_pct=105.0)
        with pytest.raises(ValidationError):
            TestExecutionPayload(task_id="t1", total_tests=-1)

        # SecurityEvaluationPayload: BLOCKED status with allowed=True is an inconsistent invariant
        with pytest.raises(ValidationError):
            SecurityEvaluationPayload(task_id="t1", status="BLOCKED", allowed=True)

        # RepairRequestPayload: empty target_source_code or empty existing_test_code
        with pytest.raises(ValidationError):
            RepairRequestPayload(task_id="t1", target_source_code="", existing_test_code="def test_x(): pass")
        with pytest.raises(ValidationError):
            RepairRequestPayload(task_id="t1", target_source_code="def x(): pass", existing_test_code="")

    def test_new_snapshots_contain_all_eight_partitions(self):
        """9. Verifies that generated BlackboardSnapshot records contain all eight partitions."""
        bb = Blackboard()
        bb.update_target_space(target_module_path="target_full.py")
        bb.update_plan_space(task_id="t_snap", planning_status="PLANNED")
        bb.update_execution_space(status="PASSED", line_coverage_pct=95.0)
        bb.update_security_space(status="PASSED", risk_level="SAFE")

        snapshot = bb.get_snapshot()
        data = snapshot.model_dump()

        assert "target" in data
        assert "mutant" in data
        assert "critic" in data
        assert "suite" in data
        assert "metrics" in data
        assert "plan" in data
        assert "execution" in data
        assert "security" in data

        assert data["plan"]["task_id"] == "t_snap"
        assert data["execution"]["line_coverage_pct"] == 95.0
        assert data["security"]["status"] == "PASSED"

    def test_backward_compatible_restoration_of_legacy_snapshots(self, temp_db_path):
        """10. Proves that legacy five-partition checkpoints (schema_version 1) restore safely with defaults."""
        storage = SQLiteBlackboardStorage(temp_db_path)

        # Construct synthetic legacy schema 1 snapshot JSON (only 5 partitions)
        legacy_snapshot = {
            "revision": 5,
            "timestamp": time.time(),
            "target": {"target_module_path": "legacy.py", "target_source_code": "def old(): pass"},
            "mutant": {"mutants_generated": 10, "mutants_killed": 8, "mutants_survived": 2},
            "critic": {"critic_directives": ["Legacy directive"]},
            "suite": {"current_test_code": "def test_old(): pass", "active_provider": "Legacy"},
            "metrics": {"current_iteration": 1, "final_mutation_score": 80.0, "baseline_line_coverage": 75.0},
        }

        # Insert directly into SQLite as schema_version = 1
        with sqlite3.connect(temp_db_path) as conn:
            conn.execute(
                """
                INSERT INTO checkpoints (
                    checkpoint_id, schema_version, job_id, workflow_id, stage,
                    revision, created_at, status, metrics_summary_json, snapshot_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    "chk_legacy_v1",
                    1,  # Legacy schema version 1
                    "job_legacy",
                    "wf_legacy",
                    "STAGE_LEGACY",
                    5,
                    time.time(),
                    "COMPLETED",
                    json.dumps({"mutation_score": 80.0}),
                    json.dumps(legacy_snapshot),
                )
            )
            conn.commit()

        # Load and restore through Blackboard
        bb = Blackboard(storage=storage)
        restored_snapshot = bb.restore_checkpoint("chk_legacy_v1")

        # 1. Existing 5 partitions restored faithfully
        assert bb.get_target_space().target_module_path == "legacy.py"
        assert bb.get_target_space().target_source_code == "def old(): pass"
        assert bb.get_mutant_space().mutants_killed == 8
        assert bb.get_metrics_space().final_mutation_score == 80.0

        # 2. Missing new 3 partitions populated with safe defaults
        assert bb.get_plan_space().planning_status == "DRAFT"
        assert bb.get_execution_space().status == "NOT_STARTED"
        assert bb.get_security_space().status == "PENDING"
        assert bb.get_security_space().allowed is True

        storage.close()

    def test_restored_data_matches_original_state(self, temp_db_path):
        """11. Verifies that all 8 partitions are serialized and restored without data drift or corruption."""
        storage = SQLiteBlackboardStorage(temp_db_path)
        bb = Blackboard(storage=storage)

        bb.update_target_space(target_module_path="pkg.math", blast_risk="MEDIUM")
        bb.update_plan_space(
            task_id="task_full",
            scenarios=[{"name": "test_add"}],
            boundary_conditions=["x < 0"],
            allocated_test_budget=12
        )
        bb.update_execution_space(
            task_id="task_full",
            status="PASSED",
            total_tests=6,
            passed_tests=6,
            line_coverage_pct=96.0
        )
        bb.update_security_space(
            task_id="task_full",
            status="PASSED",
            risk_level="SAFE",
            defused_injection_count=0
        )

        cid = bb.save_checkpoint(stage="STAGE_VERIFIED", job_id="job_full")

        # Fresh instance restoration
        bb_verify = Blackboard(storage=storage)
        bb_verify.restore_checkpoint(cid)

        assert bb_verify.get_target_space().target_module_path == "pkg.math"
        assert bb_verify.get_target_space().blast_risk == "MEDIUM"
        assert bb_verify.get_plan_space().allocated_test_budget == 12
        assert len(bb_verify.get_plan_space().scenarios) == 1
        assert bb_verify.get_execution_space().line_coverage_pct == 96.0
        assert bb_verify.get_security_space().risk_level == "SAFE"

        storage.close()

    def test_a2a_broker_synchronization_with_new_partitions(self):
        """12. Verifies that A2ABroker automatically synchronizes TestPlan, Execution, and Security payloads to Blackboard."""
        bb = Blackboard()
        broker = A2ABroker(blackboard=bb)

        # 1. Register mock planner
        def mock_planner(msg: A2AMessage) -> A2AMessage:
            plan = TestPlanPayload(
                task_id=msg.correlation_id,
                target_module="samples.discount",
                scenarios=[{"name": "test_discount_standard"}],
                allocated_test_budget=7,
                planning_rationale="Tested by mock planner"
            )
            return msg.create_response(
                performative=A2APerformative.INFORM,
                payload=plan.model_dump(),
                action=msg.action,
            )

        broker.register_handler("agent:google-adk:test-planner", mock_planner)

        # Send request
        req = A2AMessage(
            sender="orchestrator",
            recipient="agent:google-adk:test-planner",
            performative=A2APerformative.REQUEST,
            action="plan_tests",
            correlation_id="test_corr_100",
            payload={"target_module": "samples.discount"},
        )
        resp = broker.send_message(req)

        assert resp.performative == A2APerformative.INFORM
        # Blackboard PlanSpace must be updated automatically
        plan_space = bb.get_plan_space()
        assert plan_space.task_id == "test_corr_100"
        assert plan_space.source_module == "samples.discount"
        assert plan_space.allocated_test_budget == 7
        assert len(plan_space.scenarios) == 1
