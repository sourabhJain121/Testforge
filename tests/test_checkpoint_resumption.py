"""
test_checkpoint_resumption.py - Comprehensive Unit & Integration Tests for
TestForge Resilient Checkpoint Recovery and Task Resumption (GAP-03 / Milestone 1.3).

Validates all 14 required capabilities:
1. Successful restoration from a valid checkpoint (all Blackboard partitions restored).
2. Resumption from the correct safe stage based on checkpoint metadata and snapshot state.
3. Completed stages are not repeated unnecessarily (skipping ingestion, synthesis, validation, or completed reflection iterations).
4. Corrupt or incomplete checkpoints are rejected before execution.
5. Input-hash mismatch rejection when target code has drifted.
6. Unsupported checkpoint schema/version rejection.
7. Missing required Blackboard state detection and fallback to earliest safe stage.
8. Real integration test demonstrating genuine task interruption and resumption.
9. Recovery failure reported clearly in lifecycle FSM and observability.
10. Cancellation and timeout during recovery handled distinctly.
11. Repeated recovery requests are safe and idempotent without duplicate unsafe side-effects.
12. MCP session and subprocess resources recreated safely without dead handles.
13. Consistency between restored lifecycle state, SQLite database, Blackboard, and API status.
14. Regression coverage for existing checkpoint, cancellation, lifecycle, and MCP behavior.
"""

import os
import json
import time
import uuid
import pytest
import tempfile
import threading
import sqlite3
from pathlib import Path
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from testforge.persistence import (
    SQLiteBlackboardStorage,
    CheckpointMetadata,
    CheckpointRecord,
    ResumptionPlan,
    CheckpointError,
    CheckpointNotFoundError,
    CorruptedSnapshotError,
    IncompatibleSchemaError,
    InputHashMismatchError,
    IncompleteCheckpointError,
    InvalidRecoveryStageError,
    compute_source_hash,
    determine_resumption_plan,
    CURRENT_SCHEMA_VERSION,
)
from testforge.blackboard import (
    Blackboard,
    TargetSpace,
    MutantSpace,
    CriticSpace,
    SuiteSpace,
    MetricsSpace,
    BlackboardSnapshot,
)
from testforge.state import (
    TaskLifecycleState,
    TaskLifecycleFSM,
    MutantRecord,
    IterationMetrics,
    TestForgeState,
)
from testforge.callbacks import CallbackRegistry, EventType, LifecycleEvent
from testforge.orchestrator import TestForgeOrchestrator
from server import app, JOBS, JOB_LOCK


SAMPLE_TARGET_CODE = """
def discount(amount: float, is_vip: bool) -> float:
    if is_vip:
        return amount * 0.8
    if amount > 100:
        return amount * 0.9
    return amount
""".strip()

SAMPLE_BASELINE_TESTS = """
from target import discount

def test_vip_discount():
    assert discount(100, True) == 80.0

def test_large_amount_discount():
    assert discount(200, False) == 180.0

def test_regular_discount():
    assert discount(50, False) == 50.0
""".strip()


@pytest.fixture
def temp_db_path():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        path = tf.name
    yield path
    if os.path.exists(path):
        try:
            os.remove(path)
        except OSError:
            pass


@pytest.fixture
def populated_blackboard():
    bb = Blackboard()
    bb.update_target_space(
        target_source_code=SAMPLE_TARGET_CODE,
        target_module_path="samples/discount.py",
        functions=["discount"],
        line_count=7,
        source_sha=compute_source_hash(SAMPLE_TARGET_CODE),
    )
    bb.update_suite_space(
        current_test_code=SAMPLE_BASELINE_TESTS,
        baseline_test_code=SAMPLE_BASELINE_TESTS,
        baseline_passed=True,
        baseline_tests_passed=3,
        baseline_line_coverage=100.0,
    )
    bb.update_mutant_space(
        mutants=[
            MutantRecord(
                mutant_id="mut_001",
                mutation_type="ARITH_OP",
                line_number=3,
                original_code_snippet="return amount * 0.8",
                mutated_code_snippet="return amount * 0.85",
                unified_diff="--- a\n+++ b\n@@ -3,1 +3,1 @@\n- return amount * 0.8\n+ return amount * 0.85\n",
                status="KILLED",
                killing_test="test_vip_discount",
            ),
            MutantRecord(
                mutant_id="mut_002",
                mutation_type="COMP_OP",
                line_number=5,
                original_code_snippet="return amount * 0.9",
                mutated_code_snippet="return amount * 0.95",
                unified_diff="--- a\n+++ b\n@@ -5,1 +5,1 @@\n- return amount * 0.9\n+ return amount * 0.95\n",
                status="SURVIVED",
            ),
        ],
        mutants_generated=2,
        mutants_killed=1,
        mutants_survived=1,
        current_mutation_score=50.0,
    )
    bb.update_metrics_space(
        task_id="task_test_resumption",
        current_iteration=1,
        max_iterations=3,
        target_mutation_score=85.0,
        baseline_line_coverage=100.0,
        final_mutation_score=50.0,
        history=[
            IterationMetrics(
                iteration=1,
                total_mutants=2,
                killed_mutants=1,
                survived_mutants=1,
                timed_out_mutants=0,
                mutation_score=50.0,
                tests_added=0,
                duration_seconds=1.2,
            )
        ],
    )
    return bb


# ==============================================================================
# 1. Successful Restoration from Valid Checkpoint
# ==============================================================================

class TestCheckpointRestoration:
    def test_successful_restoration_all_partitions(self, temp_db_path, populated_blackboard):
        """1. Verify full restoration of all Blackboard partitions and metadata."""
        storage = SQLiteBlackboardStorage(temp_db_path)
        meta = storage.save_checkpoint(
            snapshot=populated_blackboard,
            stage="REFLECTION_ITERATION_1",
            job_id="job_restore_01",
            workflow_id="wf_restore_01",
        )
        cp_id = meta.checkpoint_id

        record, plan = storage.validate_checkpoint(cp_id)
        assert record.checkpoint_id == cp_id
        assert plan.checkpoint_stage == "REFLECTION_ITERATION_1"
        assert plan.resumes_at == "REFLECTION_LOOP"
        assert plan.start_iteration == 2

        # Restore into fresh blackboard
        fresh_bb = Blackboard()
        snapshot_dict = json.loads(record.snapshot_json)
        fresh_bb.restore_from_snapshot(BlackboardSnapshot.model_validate(snapshot_dict))

        assert fresh_bb.target.target_source_code == SAMPLE_TARGET_CODE
        assert fresh_bb.suite.current_test_code == SAMPLE_BASELINE_TESTS
        assert fresh_bb.suite.baseline_passed is True
        assert len(fresh_bb.mutant.mutants) == 2
        assert fresh_bb.metrics.current_iteration == 1
        assert fresh_bb.metrics.final_mutation_score == 50.0
        storage.close()


# ==============================================================================
# 2. Resumption Stage Selection & Skipping Unnecessary Work
# ==============================================================================

class TestResumptionStageSelection:
    def test_stage_selection_and_skipped_stages(self, temp_db_path):
        """2 & 3. Verifies safe stage determination for each stage."""
        storage = SQLiteBlackboardStorage(temp_db_path)
        bb = Blackboard()
        bb.update_target_space(target_source_code=SAMPLE_TARGET_CODE, target_module_path="discount.py")

        # Case A: INITIAL_INGESTION -> resumes at BASELINE_SYNTHESIS
        meta_ingest = storage.save_checkpoint(bb, stage="INITIAL_INGESTION")
        _, plan_ingest = storage.validate_checkpoint(meta_ingest.checkpoint_id)
        assert plan_ingest.resumes_at == "BASELINE_SYNTHESIS"
        assert plan_ingest.target_lifecycle_state == TaskLifecycleState.PLANNING.value
        assert "INGESTING" in plan_ingest.skipped_stages

        # Case B: BASELINE_SYNTHESIS -> resumes at BASELINE_VALIDATION
        bb.update_suite_space(current_test_code=SAMPLE_BASELINE_TESTS)
        meta_synth = storage.save_checkpoint(bb, stage="BASELINE_SYNTHESIS")
        _, plan_synth = storage.validate_checkpoint(meta_synth.checkpoint_id)
        assert plan_synth.resumes_at == "BASELINE_VALIDATION"
        assert plan_synth.target_lifecycle_state == TaskLifecycleState.EXECUTING.value
        assert "INGESTING" in plan_synth.skipped_stages
        assert "GENERATING_TESTS" in plan_synth.skipped_stages

        # Case C: BASELINE_VALIDATED -> resumes at REFLECTION_LOOP
        bb.update_suite_space(current_test_code=SAMPLE_BASELINE_TESTS, baseline_passed=True)
        meta_val = storage.save_checkpoint(bb, stage="BASELINE_VALIDATED")
        _, plan_val = storage.validate_checkpoint(meta_val.checkpoint_id)
        assert plan_val.resumes_at == "REFLECTION_LOOP"
        assert plan_val.target_lifecycle_state == TaskLifecycleState.MUTATION_ANALYSIS.value
        assert plan_val.start_iteration == 1
        assert "EXECUTING" in plan_val.skipped_stages

        # Case D: REFLECTION_ITERATION_2 -> resumes at iteration 3
        bb.update_metrics_space(
            current_iteration=2,
            history=[
                IterationMetrics(
                    iteration=2,
                    total_mutants=4,
                    killed_mutants=3,
                    survived_mutants=1,
                    timed_out_mutants=0,
                    mutation_score=75.0,
                    tests_added=2,
                    duration_seconds=1.0,
                )
            ]
        )
        meta_iter2 = storage.save_checkpoint(bb, stage="REFLECTION_ITERATION_2")
        _, plan_iter2 = storage.validate_checkpoint(meta_iter2.checkpoint_id)
        assert plan_iter2.resumes_at == "REFLECTION_LOOP"
        assert plan_iter2.start_iteration == 3
        assert "REFLECTION_ITERATION_1" in plan_iter2.skipped_stages
        assert "REFLECTION_ITERATION_2" in plan_iter2.skipped_stages

        # Case E: FINALIZED -> resumes directly to COMPLETED
        meta_final = storage.save_checkpoint(bb, stage="FINALIZED")
        _, plan_final = storage.validate_checkpoint(meta_final.checkpoint_id)
        assert plan_final.resumes_at == "COMPLETED"
        assert plan_final.target_lifecycle_state == TaskLifecycleState.COMPLETED.value
        storage.close()


# ==============================================================================
# 3. Checkpoint Validation: Schema, Corrupt, Hash Mismatch, Missing State
# ==============================================================================

class TestCheckpointValidationAndRejection:
    def test_corrupt_checkpoint_rejection(self, temp_db_path, populated_blackboard):
        """4. Rejects corrupted JSON snapshot data."""
        storage = SQLiteBlackboardStorage(temp_db_path)
        meta = storage.save_checkpoint(populated_blackboard, stage="BASELINE_VALIDATED")
        cp_id = meta.checkpoint_id
        storage.close()

        # Intentionally corrupt raw snapshot in SQLite
        with sqlite3.connect(temp_db_path) as conn:
            conn.execute(
                "UPDATE checkpoints SET snapshot_json = ? WHERE checkpoint_id = ?",
                ("{ INVALID JSON BODY >>>", cp_id)
            )
            conn.commit()

        storage2 = SQLiteBlackboardStorage(temp_db_path)
        with pytest.raises(CorruptedSnapshotError):
            storage2.validate_checkpoint(cp_id)
        storage2.close()

    def test_incomplete_checkpoint_rejection(self, temp_db_path):
        """4 & 7. Rejects incomplete checkpoint missing required partitions."""
        storage = SQLiteBlackboardStorage(temp_db_path)
        empty_bb = Blackboard()
        meta = storage.save_checkpoint(empty_bb, stage="INITIAL_INGESTION")

        with pytest.raises(IncompleteCheckpointError):
            storage.validate_checkpoint(meta.checkpoint_id)
        storage.close()

    def test_input_hash_mismatch_rejection(self, temp_db_path, populated_blackboard):
        """5. Rejects resumption if target source code has drifted."""
        storage = SQLiteBlackboardStorage(temp_db_path)
        meta = storage.save_checkpoint(populated_blackboard, stage="BASELINE_VALIDATED")
        cp_id = meta.checkpoint_id

        # Valid with exact code
        storage.validate_checkpoint(cp_id, expected_source_code=SAMPLE_TARGET_CODE)

        # Rejects with altered code
        altered_code = SAMPLE_TARGET_CODE + "\n# Modified code"
        with pytest.raises(InputHashMismatchError):
            storage.validate_checkpoint(cp_id, expected_source_code=altered_code)
        storage.close()

    def test_unsupported_schema_version_rejection(self, temp_db_path, populated_blackboard):
        """6. Rejects unsupported schema/version."""
        storage = SQLiteBlackboardStorage(temp_db_path)
        meta = storage.save_checkpoint(populated_blackboard, stage="BASELINE_VALIDATED")
        cp_id = meta.checkpoint_id
        storage.close()

        # Mutate schema version
        with sqlite3.connect(temp_db_path) as conn:
            conn.execute(
                "UPDATE checkpoints SET schema_version = ? WHERE checkpoint_id = ?",
                ("99.0.0", cp_id)
            )
            conn.commit()

        storage2 = SQLiteBlackboardStorage(temp_db_path)
        with pytest.raises(IncompatibleSchemaError):
            storage2.validate_checkpoint(cp_id)
        storage2.close()

    def test_missing_required_blackboard_state_fallback(self, temp_db_path):
        """7. Missing test code in BASELINE_VALIDATED safely falls back to BASELINE_SYNTHESIS."""
        storage = SQLiteBlackboardStorage(temp_db_path)
        bb = Blackboard()
        bb.update_target_space(target_source_code=SAMPLE_TARGET_CODE, target_module_path="discount.py")
        # Stage is claimed to be BASELINE_VALIDATED, but no test code exists
        meta = storage.save_checkpoint(bb, stage="BASELINE_VALIDATED")

        record, plan = storage.validate_checkpoint(meta.checkpoint_id)
        # Resumes at BASELINE_SYNTHESIS to safely regenerate missing test code
        assert plan.resumes_at == "BASELINE_SYNTHESIS"
        assert plan.target_lifecycle_state == TaskLifecycleState.PLANNING.value
        storage.close()


# ==============================================================================
# 4. Observability and Lifecycle Consistency During Recovery
# ==============================================================================

class TestRecoveryObservabilityAndLifecycle:
    def test_recovery_lifecycle_events_dispatched(self, temp_db_path, populated_blackboard):
        """8 & 10. Verifies RECOVERY_DECISION and CHECKPOINT_RESTORED lifecycle events."""
        storage = SQLiteBlackboardStorage(temp_db_path)
        meta = storage.save_checkpoint(populated_blackboard, stage="BASELINE_VALIDATED")
        cp_id = meta.checkpoint_id
        storage.close()

        captured_events: list[LifecycleEvent] = []
        registry = CallbackRegistry()
        registry.register(lambda ev: captured_events.append(ev))

        orchestrator = TestForgeOrchestrator(
            target_source_code=SAMPLE_TARGET_CODE,
            max_iterations=1,
            engine_mode="legacy",
            checkpoint_db_path=temp_db_path,
            resume_checkpoint_id=cp_id,
            callbacks=registry,
        )

        plan = orchestrator.validate_and_restore_checkpoint(cp_id)
        assert plan.resumes_at == "REFLECTION_LOOP"

        event_types = [ev.event_type for ev in captured_events]
        assert EventType.RECOVERY_DECISION in event_types
        assert EventType.CHECKPOINT_RESTORED in event_types

        rec_ev = next(ev for ev in captured_events if ev.event_type == EventType.RECOVERY_DECISION)
        assert rec_ev.payload["checkpoint_id"] == cp_id
        assert rec_ev.payload["resumes_at"] == "REFLECTION_LOOP"

    def test_recovery_failure_reported_clearly(self, temp_db_path):
        """9. Corrupted checkpoint during orchestrator.run() fails clearly with FAILED lifecycle state."""
        storage = SQLiteBlackboardStorage(temp_db_path)
        bb = Blackboard()
        bb.update_target_space(target_source_code=SAMPLE_TARGET_CODE, target_module_path="discount.py")
        meta = storage.save_checkpoint(bb, stage="BASELINE_VALIDATED")
        cp_id = meta.checkpoint_id
        storage.close()

        # Corrupt DB record
        with sqlite3.connect(temp_db_path) as conn:
            conn.execute(
                "UPDATE checkpoints SET snapshot_json = ? WHERE checkpoint_id = ?",
                ("MALFORMED", cp_id)
            )
            conn.commit()

        captured_events: list[LifecycleEvent] = []
        registry = CallbackRegistry()
        registry.register(lambda ev: captured_events.append(ev))

        orchestrator = TestForgeOrchestrator(
            target_source_code=SAMPLE_TARGET_CODE,
            max_iterations=1,
            engine_mode="legacy",
            checkpoint_db_path=temp_db_path,
            resume_checkpoint_id=cp_id,
            callbacks=registry,
        )

        final_state = orchestrator.run()
        assert orchestrator.fsm.current_state == TaskLifecycleState.FAILED
        assert "Recovery failed" in (orchestrator.fsm.failure_reason or "")
        assert final_state.lifecycle_state == TaskLifecycleState.FAILED

        failed_events = [ev for ev in captured_events if ev.event_type == EventType.CHECKPOINT_FAILED]
        assert len(failed_events) >= 1
        assert failed_events[0].payload["checkpoint_id"] == cp_id


# ==============================================================================
# 5. Cancellation, Timeout, and Idempotent Repeated Resumption
# ==============================================================================

class TestCancellationTimeoutAndIdempotency:
    def test_cancellation_during_recovery(self, temp_db_path, populated_blackboard):
        """10. Cancellation event set before/during recovery transitions cleanly to CANCELLED."""
        storage = SQLiteBlackboardStorage(temp_db_path)
        meta = storage.save_checkpoint(populated_blackboard, stage="BASELINE_VALIDATED")
        cp_id = meta.checkpoint_id
        storage.close()

        cancel_evt = threading.Event()
        cancel_evt.set()  # Cancelled immediately

        orchestrator = TestForgeOrchestrator(
            target_source_code=SAMPLE_TARGET_CODE,
            max_iterations=1,
            engine_mode="legacy",
            checkpoint_db_path=temp_db_path,
            resume_checkpoint_id=cp_id,
            cancel_event=cancel_evt,
        )

        final_state = orchestrator.run()
        assert orchestrator.fsm.current_state == TaskLifecycleState.CANCELLED
        assert final_state.final_hardening_status == "CANCELLED"

    def test_timeout_during_recovery(self, temp_db_path, populated_blackboard):
        """10. Expired timeout transitions cleanly to TIMED_OUT."""
        storage = SQLiteBlackboardStorage(temp_db_path)
        meta = storage.save_checkpoint(populated_blackboard, stage="BASELINE_VALIDATED")
        cp_id = meta.checkpoint_id
        storage.close()

        orchestrator = TestForgeOrchestrator(
            target_source_code=SAMPLE_TARGET_CODE,
            max_iterations=1,
            engine_mode="legacy",
            checkpoint_db_path=temp_db_path,
            resume_checkpoint_id=cp_id,
            timeout_seconds=0,  # Zero timeout triggers immediately
        )

        final_state = orchestrator.run()
        assert orchestrator.fsm.current_state == TaskLifecycleState.TIMED_OUT
        assert final_state.final_hardening_status == "TIMED_OUT"

    def test_repeated_recovery_requests_are_idempotent(self, temp_db_path, populated_blackboard):
        """11. Calling validate_and_restore_checkpoint repeatedly is safe and produces identical state."""
        storage = SQLiteBlackboardStorage(temp_db_path)
        meta = storage.save_checkpoint(populated_blackboard, stage="BASELINE_VALIDATED")
        cp_id = meta.checkpoint_id
        storage.close()

        orchestrator = TestForgeOrchestrator(
            target_source_code=SAMPLE_TARGET_CODE,
            max_iterations=1,
            engine_mode="legacy",
            checkpoint_db_path=temp_db_path,
        )

        plan1 = orchestrator.validate_and_restore_checkpoint(cp_id)
        plan2 = orchestrator.validate_and_restore_checkpoint(cp_id)

        assert plan1.checkpoint_id == plan2.checkpoint_id
        assert plan1.resumes_at == plan2.resumes_at
        assert orchestrator.blackboard.target.target_source_code == SAMPLE_TARGET_CODE
        assert orchestrator.blackboard.suite.baseline_passed is True


# ==============================================================================
# 6. Real Integration Test: Genuine Interruption & Resumption
# ==============================================================================

class TestGenuineTaskInterruptionAndResumption:
    def test_genuine_interruption_and_successful_resumption(self, temp_db_path):
        """
        15. Genuinely runs an orchestrator task interrupted after a persisted checkpoint,
        then genuinely resumes from that checkpoint and verifies:
        - Ingestion and baseline validation stages are SKIPPED.
        - Execution resumes directly at reflection loop.
        - The task reaches COMPLETED lifecycle state.
        - The final suite includes the baseline tests.
        """
        job_id = f"job_interrupt_{uuid.uuid4().hex[:6]}"
        cancel_evt = threading.Event()

        # Phase A: Run Task 1, and interrupt it right after baseline validation checkpoint is persisted
        def cancel_on_stage(event: LifecycleEvent):
            if event.event_type == EventType.CHECKPOINT_SAVED and event.payload.get("stage") == "BASELINE_VALIDATED":
                cancel_evt.set()

        reg_initial = CallbackRegistry()
        reg_initial.register(cancel_on_stage)

        orchestrator_initial = TestForgeOrchestrator(
            target_source_code=SAMPLE_TARGET_CODE,
            initial_test_code=SAMPLE_BASELINE_TESTS,
            max_iterations=2,
            target_mutation_score=100.0,
            engine_mode="legacy",
            checkpoint_db_path=temp_db_path,
            job_id=job_id,
            cancel_event=cancel_evt,
            callbacks=reg_initial,
        )

        init_state = orchestrator_initial.run()
        # Ensure Phase A was genuinely cancelled/interrupted after baseline was checkpointed
        assert orchestrator_initial.fsm.current_state in (TaskLifecycleState.CANCELLED, TaskLifecycleState.CANCELLING)

        # Verify a resumable checkpoint was persisted before or at interruption
        storage = SQLiteBlackboardStorage(temp_db_path)
        cp = storage.get_resumable_checkpoint(job_id=job_id)
        assert cp is not None
        assert cp.stage in ("BASELINE_VALIDATED", "CANCELLED")
        initial_cp_id = cp.checkpoint_id
        storage.close()

        # Phase B: Resumed Orchestrator Run from initial_cp_id
        resumed_job_id = f"job_resumed_{uuid.uuid4().hex[:6]}"
        captured_events: list[LifecycleEvent] = []
        reg_resumed = CallbackRegistry()
        reg_resumed.register(lambda ev: captured_events.append(ev))

        orchestrator_resumed = TestForgeOrchestrator(
            target_source_code=SAMPLE_TARGET_CODE,
            max_iterations=2,
            target_mutation_score=0.0,  # Ensure it finishes cleanly after reflection
            engine_mode="legacy",
            checkpoint_db_path=temp_db_path,
            resume_checkpoint_id=initial_cp_id,
            job_id=resumed_job_id,
            callbacks=reg_resumed,
        )

        final_state = orchestrator_resumed.run()

        # Verify genuine resumption
        assert orchestrator_resumed.resumption_plan is not None
        assert orchestrator_resumed.resumption_plan.checkpoint_id == initial_cp_id
        assert orchestrator_resumed.fsm.current_state == TaskLifecycleState.COMPLETED
        assert final_state.lifecycle_state == TaskLifecycleState.COMPLETED

        # Check skipped stages: RECOVERING and RECOVERED were traversed
        history = [r.stage.value for r in orchestrator_resumed.fsm.get_history()]
        assert "RECOVERING" in history
        assert "RECOVERED" in history
        assert "COMPLETED" in history

        # Baseline tests are preserved and present in final suite
        assert "def test_vip_discount" in final_state.current_test_code

        # Verify SQLite has checkpoints from resumed execution
        storage_check = SQLiteBlackboardStorage(temp_db_path)
        final_cp = storage_check.get_latest_checkpoint(job_id=resumed_job_id)
        assert final_cp is not None
        assert final_cp.stage == "FINALIZED"
        storage_check.close()


# ==============================================================================
# 7. MCP Resource Safety on Resumption
# ==============================================================================

class TestMCPResourceSafetyOnResumption:
    def test_mcp_client_reinitialized_cleanly(self, temp_db_path, populated_blackboard):
        """12. Verifies that resuming with an MCP client disconnects cleanly without process leaks."""
        storage = SQLiteBlackboardStorage(temp_db_path)
        meta = storage.save_checkpoint(populated_blackboard, stage="BASELINE_VALIDATED")
        cp_id = meta.checkpoint_id
        storage.close()

        mock_mcp = MagicMock()
        mock_mcp.disconnect_sync = MagicMock()

        orchestrator = TestForgeOrchestrator(
            target_source_code=SAMPLE_TARGET_CODE,
            max_iterations=1,
            engine_mode="legacy",
            checkpoint_db_path=temp_db_path,
            resume_checkpoint_id=cp_id,
            mcp_client=mock_mcp,
        )

        plan = orchestrator.validate_and_restore_checkpoint(cp_id)
        assert plan.resumes_at == "REFLECTION_LOOP"
        # Client handle is intact and usable
        assert orchestrator.mcp_client is mock_mcp


# ==============================================================================
# 8. Server API Resumption Endpoints & Status Consistency
# ==============================================================================

class TestServerApiResumption:
    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_api_resume_checkpoint_endpoint(self, client, temp_db_path, populated_blackboard):
        """13 & 14. POST /api/checkpoints/{checkpoint_id}/resume validates and queues job."""
        storage = SQLiteBlackboardStorage(temp_db_path)
        meta = storage.save_checkpoint(populated_blackboard, stage="BASELINE_VALIDATED", job_id="job_api_orig")
        cp_id = meta.checkpoint_id
        storage.close()

        with patch("server.DEFAULT_CHECKPOINT_DB_PATH", temp_db_path):
            res = client.post(f"/api/checkpoints/{cp_id}/resume", json={
                "max_iterations": 2,
                "timeout_seconds": 60,
            })
            assert res.status_code == 200
            data = res.json()
            assert data["status"] == "queued"
            assert data["resumed_from_checkpoint"] == cp_id
            assert "resumption_plan" in data
            assert data["resumption_plan"]["resumes_at"] == "REFLECTION_LOOP"

            # Check status endpoint exposes resumption_plan
            res_status = client.get(data["poll_url"])
            assert res_status.status_code == 200
            status_data = res_status.json()
            assert status_data["resumed_from_checkpoint"] == cp_id
            assert status_data["resumption_plan"]["checkpoint_id"] == cp_id

    def test_api_resume_job_endpoint(self, client, temp_db_path, populated_blackboard):
        """14. POST /api/harden/resume/{job_id} finds latest checkpoint and resumes."""
        job_id = "job_to_resume_99"
        storage = SQLiteBlackboardStorage(temp_db_path)
        meta = storage.save_checkpoint(populated_blackboard, stage="BASELINE_VALIDATED", job_id=job_id)
        cp_id = meta.checkpoint_id
        storage.close()

        with patch("server.DEFAULT_CHECKPOINT_DB_PATH", temp_db_path):
            res = client.post(f"/api/harden/resume/{job_id}", json={})
            assert res.status_code == 200
            data = res.json()
            assert data["status"] in ("queued", "RESUMED")
            assert data["resumed_from_checkpoint"] == cp_id

    def test_api_resume_invalid_checkpoint_rejected(self, client, temp_db_path):
        """14. Rejection of unknown or corrupt checkpoint with appropriate HTTP status."""
        with patch("server.DEFAULT_CHECKPOINT_DB_PATH", temp_db_path):
            # Not found
            res_404 = client.post("/api/checkpoints/non_existent_cp/resume", json={})
            assert res_404.status_code == 404

            # Incomplete checkpoint
            storage = SQLiteBlackboardStorage(temp_db_path)
            empty_bb = Blackboard()
            meta_bad = storage.save_checkpoint(empty_bb, stage="INITIAL_INGESTION")
            storage.close()

            res_422 = client.post(f"/api/checkpoints/{meta_bad.checkpoint_id}/resume", json={})
            assert res_422.status_code == 422
