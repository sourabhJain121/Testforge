"""
test_blackboard_persistence.py - Comprehensive Unit & Integration Tests for Persistent SQLite Blackboard Checkpointing.

Covers all 18 requirements:
  1. Save and load a valid snapshot.
  2. Preserve every supported Blackboard partition (target, mutant, critic, suite, metrics).
  3. Restore typed state correctly.
  4. Save multiple sequential checkpoints.
  5. Select the appropriate checkpoint for a workflow/job.
  6. Restore after creating a fresh Blackboard instance.
  7. Recover safely from a missing database.
  8. Handle corrupted snapshot data.
  9. Handle schema-version mismatch.
  10. Handle database write failures without corrupting memory.
  11. Handle concurrent checkpoint operations (race-free multi-threading).
  12. Verify checkpoint transaction integrity (all-or-nothing rollback).
  13. Preserve cancellation and timeout terminal states.
  14. Ensure completed checkpoints survive a simulated application restart.
  15. Verify persistence-disabled mode behaves as before (in-memory only).
  16. Verify existing Blackboard APIs and workflows remain backward compatible.
  17. Verify secrets/API keys are NOT written to checkpoint data.
  18. Verify checkpoint events appear in existing observability mechanisms (callbacks/events).
  19. REST API test for /api/checkpoints, /api/checkpoints/{id}, /api/checkpoints/{id}/restore.
"""

import json
import os
import sqlite3
import tempfile
import threading
import time
from pathlib import Path
from typing import Any, Dict, List

import pytest

from testforge.blackboard import (
    Blackboard,
    BlackboardEvent,
    BlackboardSnapshot,
    CriticSpace,
    MetricsSpace,
    MutantSpace,
    SuiteSpace,
    TargetSpace,
)
from testforge.callbacks import CallbackRegistry, EventType, LifecycleEvent
from testforge.persistence import (
    CURRENT_SCHEMA_VERSION,
    CheckpointError,
    CheckpointMetadata,
    CheckpointNotFoundError,
    CheckpointRecord,
    CheckpointSummary,
    CorruptedSnapshotError,
    IncompatibleSchemaError,
    PersistenceWriteError,
    SQLiteBlackboardStorage,
)
from testforge.state import IterationMetrics, MutantRecord, TestForgeState

# ==============================================================================
# Fixtures
# ==============================================================================

@pytest.fixture
def temp_db(tmp_path):
    """Provides a temporary SQLite database file path."""
    db_file = tmp_path / "test_blackboard.db"
    yield db_file
    if db_file.exists():
        try:
            db_file.unlink()
        except Exception:
            pass


@pytest.fixture
def populated_blackboard():
    """Returns a Blackboard instance populated with rich multi-partition test data."""
    bb = Blackboard()
    bb.update_target_space(
        target_module_path="samples/discount.py",
        target_source_code="def calculate_discount(price, discount):\n    return price * (1 - discount)\n",
        functions=["calculate_discount"],
        blast_risk="LOW",
        source_sha="abc12345",
        line_count=2,
    )
    m1 = MutantRecord(
        mutant_id="MUT_001",
        mutation_type="ARITH_OP",
        line_number=2,
        original_code_snippet="return price * (1 - discount)",
        mutated_code_snippet="return price / (1 - discount)",
        unified_diff="--- target.py\n+++ target.py\n@@ -2,1 +2,1 @@\n- return price * (1 - discount)\n+ return price / (1 - discount)\n",
        status="KILLED",
        execution_time_ms=14.5,
    )
    m2 = MutantRecord(
        mutant_id="MUT_002",
        mutation_type="COMP_OP",
        line_number=2,
        original_code_snippet="1 - discount",
        mutated_code_snippet="1 + discount",
        unified_diff="--- target.py\n+++ target.py\n@@ -2,1 +2,1 @@\n- 1 - discount\n+ 1 + discount\n",
        status="SURVIVED",
        execution_time_ms=12.2,
    )
    bb.update_mutant_space(
        mutants=[m1, m2],
        mutants_generated=2,
        mutants_executed=2,
        mutants_killed=1,
        mutants_survived=1,
        current_mutation_score=50.0,
        surviving_mutant_diffs=[m2.unified_diff],
    )
    bb.update_critic_space(
        critic_directives=["Test edge case with discount=0", "Test negative prices"],
        latest_directive="Test edge case with discount=0",
        reflection_notes=["Boundary values survived MUT_002"],
    )
    bb.update_suite_space(
        test_module_path="test_discount.py",
        current_test_code="def test_discount():\n    assert calculate_discount(100, 0.2) == 80\n",
        baseline_test_code="def test_discount():\n    assert calculate_discount(100, 0.2) == 80\n",
        active_provider="Google GenAI Live",
        baseline_tests_generated=1,
        baseline_tests_executed=1,
        baseline_passed=True,
        baseline_tests_passed=1,
        baseline_tests_failed=0,
    )
    im = IterationMetrics(
        iteration=1,
        total_mutants=2,
        killed_mutants=1,
        survived_mutants=1,
        timed_out_mutants=0,
        mutation_score=50.0,
        line_coverage_pct=100.0,
        duration_seconds=1.2,
    )
    bb.update_metrics_space(
        current_iteration=1,
        max_iterations=3,
        target_mutation_score=85.0,
        baseline_line_coverage=100.0,
        lines_covered=2,
        num_statements=2,
        history=[im],
        final_mutation_score=50.0,
        reflection_iterations_performed=1,
        final_hardening_status="IN_PROGRESS",
    )
    return bb


# ==============================================================================
# Unit & Integration Tests
# ==============================================================================

class TestBlackboardPersistenceCore:

    # 1. Save and load a valid snapshot
    def test_save_and_load_valid_snapshot(self, temp_db, populated_blackboard):
        storage = SQLiteBlackboardStorage(temp_db)
        snapshot = populated_blackboard.get_snapshot()

        meta = storage.save_checkpoint(
            snapshot=snapshot,
            stage="TEST_STAGE_1",
            job_id="job_abc",
            workflow_id="wf_123",
            status="IN_PROGRESS"
        )
        assert meta.checkpoint_id.startswith("chk_")
        assert meta.schema_version == CURRENT_SCHEMA_VERSION
        assert meta.job_id == "job_abc"
        assert meta.workflow_id == "wf_123"
        assert meta.stage == "TEST_STAGE_1"

        record = storage.load_checkpoint(meta.checkpoint_id)
        assert record.metadata.checkpoint_id == meta.checkpoint_id
        assert record.metadata.stage == "TEST_STAGE_1"

        restored_snapshot = BlackboardSnapshot.model_validate_json(record.snapshot_json)
        assert restored_snapshot.revision == snapshot.revision
        storage.close()

    # 2. Preserve every supported Blackboard partition
    def test_preserve_every_supported_partition(self, temp_db, populated_blackboard):
        storage = SQLiteBlackboardStorage(temp_db)
        snapshot = populated_blackboard.get_snapshot()
        meta = storage.save_checkpoint(snapshot=snapshot, stage="ALL_PARTITIONS")

        record = storage.load_checkpoint(meta.checkpoint_id)
        restored = BlackboardSnapshot.model_validate_json(record.snapshot_json)

        # Target partition
        assert restored.target.target_module_path == "samples/discount.py"
        assert restored.target.functions == ["calculate_discount"]
        assert restored.target.blast_risk == "LOW"

        # Mutant partition
        assert len(restored.mutant.mutants) == 2
        assert restored.mutant.mutants[0].mutant_id == "MUT_001"
        assert restored.mutant.mutants[0].status == "KILLED"
        assert restored.mutant.mutants_killed == 1
        assert restored.mutant.mutants_survived == 1

        # Critic partition
        assert len(restored.critic.critic_directives) == 2
        assert restored.critic.latest_directive == "Test edge case with discount=0"

        # Suite partition
        assert restored.suite.baseline_passed is True
        assert "assert calculate_discount" in restored.suite.current_test_code

        # Metrics partition
        assert restored.metrics.current_iteration == 1
        assert restored.metrics.final_mutation_score == 50.0
        assert len(restored.metrics.history) == 1
        assert restored.metrics.history[0].iteration == 1
        storage.close()

    # 3. Restore typed state correctly
    def test_restore_typed_state_correctly(self, temp_db, populated_blackboard):
        storage = SQLiteBlackboardStorage(temp_db)
        snapshot = populated_blackboard.get_snapshot()
        meta = storage.save_checkpoint(snapshot, stage="TYPED_RESTORE")

        fresh_bb = Blackboard()
        record = storage.load_checkpoint(meta.checkpoint_id)
        restored_snapshot = BlackboardSnapshot.model_validate_json(record.snapshot_json)
        fresh_bb.restore_from_snapshot(restored_snapshot)

        # Check types
        assert isinstance(fresh_bb.get_target_space(), TargetSpace)
        assert isinstance(fresh_bb.get_mutant_space(), MutantSpace)
        assert isinstance(fresh_bb.get_critic_space(), CriticSpace)
        assert isinstance(fresh_bb.get_suite_space(), SuiteSpace)
        assert isinstance(fresh_bb.get_metrics_space(), MetricsSpace)

        # Defensive copying check: mutating returned partition does not corrupt in-memory blackboard
        target = fresh_bb.get_target_space()
        target.target_source_code = "CORRUPTED"
        assert fresh_bb.get_target_space().target_source_code != "CORRUPTED"
        storage.close()

    # 4. Save multiple sequential checkpoints
    def test_save_multiple_sequential_checkpoints(self, temp_db, populated_blackboard):
        storage = SQLiteBlackboardStorage(temp_db)
        stages = ["INITIAL_INGESTION", "BASELINE_SYNTHESIS", "BASELINE_VALIDATED", "FINALIZED"]
        cids = []

        for stage in stages:
            snap = populated_blackboard.get_snapshot()
            meta = storage.save_checkpoint(snap, stage=stage, job_id="seq_job")
            cids.append(meta.checkpoint_id)
            time.sleep(0.01)

        summaries = storage.list_checkpoints(job_id="seq_job")
        assert len(summaries) == 4
        # Ordered by created_at DESC
        assert summaries[0].stage == "FINALIZED"
        assert summaries[-1].stage == "INITIAL_INGESTION"
        storage.close()

    # 5. Select the appropriate checkpoint for a workflow/job
    def test_select_appropriate_checkpoint_for_workflow(self, temp_db, populated_blackboard):
        storage = SQLiteBlackboardStorage(temp_db)
        snap = populated_blackboard.get_snapshot()

        storage.save_checkpoint(snap, stage="STAGE_A", job_id="job_1", workflow_id="wf_1")
        time.sleep(0.01)
        storage.save_checkpoint(snap, stage="STAGE_B", job_id="job_2", workflow_id="wf_2")
        time.sleep(0.01)
        storage.save_checkpoint(snap, stage="STAGE_C", job_id="job_1", workflow_id="wf_1")

        latest_job1 = storage.get_latest_checkpoint(job_id="job_1")
        assert latest_job1 is not None
        assert latest_job1.metadata.stage == "STAGE_C"

        latest_job2 = storage.get_latest_checkpoint(job_id="job_2")
        assert latest_job2 is not None
        assert latest_job2.metadata.stage == "STAGE_B"
        storage.close()

    # 6. Restore after creating a fresh Blackboard instance
    def test_restore_after_fresh_instance(self, temp_db, populated_blackboard):
        bb1 = Blackboard(checkpoint_db_path=temp_db)
        # Copy state from populated_blackboard
        bb1.restore_from_snapshot(populated_blackboard.get_snapshot())
        cid = bb1.save_checkpoint("STAGE_FRESH", job_id="fresh_job")
        assert cid is not None
        bb1.close()

        # Create brand new Blackboard on the same DB
        bb2 = Blackboard(checkpoint_db_path=temp_db)
        assert bb2.revision == 0
        restored_snap = bb2.restore_checkpoint(cid)

        assert bb2.revision > 0
        assert bb2.get_target_space().target_module_path == "samples/discount.py"
        assert len(bb2.get_mutant_space().mutants) == 2
        bb2.close()

    # 7. Recover safely from a missing database
    def test_recover_safely_from_missing_database(self, tmp_path):
        non_existent_db = tmp_path / "subdir" / "missing.db"
        # SQLite should safely create the directory and database on init
        storage = SQLiteBlackboardStorage(non_existent_db)
        assert non_existent_db.exists()
        assert storage.count_checkpoints() == 0
        storage.close()

        # Non-existent checkpoint load raises CheckpointNotFoundError
        storage2 = SQLiteBlackboardStorage(non_existent_db)
        with pytest.raises(CheckpointNotFoundError):
            storage2.load_checkpoint("non_existent_id")
        storage2.close()

    # 8. Handle corrupted snapshot data
    def test_handle_corrupted_snapshot_data(self, temp_db):
        storage = SQLiteBlackboardStorage(temp_db)
        # Directly insert a row with corrupted JSON
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO checkpoints (
                checkpoint_id, schema_version, job_id, workflow_id, stage,
                revision, created_at, status, metrics_summary_json, snapshot_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ("corrupt_chk", CURRENT_SCHEMA_VERSION, "j1", "wf1", "STAGE_ERR",
             1, time.time(), "FAILED", "{}", "NOT_VALID_JSON{{{")
        )
        conn.commit()
        conn.close()

        with pytest.raises(CorruptedSnapshotError):
            storage.load_checkpoint("corrupt_chk")
        storage.close()

    # 9. Handle schema-version mismatch
    def test_handle_schema_version_mismatch(self, temp_db):
        storage = SQLiteBlackboardStorage(temp_db)
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO checkpoints (
                checkpoint_id, schema_version, job_id, workflow_id, stage,
                revision, created_at, status, metrics_summary_json, snapshot_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            ("future_chk", 999, "j1", "wf1", "STAGE_FUTURE",
             1, time.time(), "COMPLETED", "{}", "{}")
        )
        conn.commit()
        conn.close()

        with pytest.raises(IncompatibleSchemaError) as exc_info:
            storage.load_checkpoint("future_chk")
        assert "schema version 999" in str(exc_info.value)
        storage.close()

    # 10. Handle database write failures without corrupting memory
    def test_database_write_failures_do_not_corrupt_memory(self, temp_db, populated_blackboard):
        bb = Blackboard(checkpoint_db_path=temp_db, strict_persistence=False)
        bb.restore_from_snapshot(populated_blackboard.get_snapshot())

        # Simulate closed/unwritable DB
        bb.storage.close()

        # Should log warning, return None, and NOT crash or corrupt in-memory Blackboard
        cid = bb.save_checkpoint("FAILED_STAGE")
        assert cid is None

        # Verify in-memory state is still 100% intact and operational
        assert bb.get_target_space().target_module_path == "samples/discount.py"
        bb.update_target_space(blast_risk="HIGH")
        assert bb.get_target_space().blast_risk == "HIGH"

    # 11. Handle concurrent checkpoint operations
    def test_concurrent_checkpoint_operations(self, temp_db, populated_blackboard):
        bb = Blackboard(checkpoint_db_path=temp_db)
        bb.restore_from_snapshot(populated_blackboard.get_snapshot())

        errors = []
        cids = []
        lock = threading.Lock()

        def worker(thread_idx: int):
            try:
                for i in range(10):
                    cid = bb.save_checkpoint(
                        stage=f"THREAD_{thread_idx}_STEP_{i}",
                        job_id=f"concurrent_job_{thread_idx}",
                    )
                    with lock:
                        cids.append(cid)
                    time.sleep(0.002)
            except Exception as e:
                with lock:
                    errors.append(e)

        threads = [threading.Thread(target=worker, args=(t,)) for t in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert len(errors) == 0, f"Concurrent checkpoint errors: {errors}"
        assert len(cids) == 50
        assert bb.storage.count_checkpoints() == 50
        bb.close()

    # 12. Verify checkpoint transaction integrity (all-or-nothing rollback)
    def test_checkpoint_transaction_integrity(self, temp_db, populated_blackboard):
        storage = SQLiteBlackboardStorage(temp_db, strict_mode=True)
        snap = populated_blackboard.get_snapshot()

        # Save an initial valid checkpoint
        storage.save_checkpoint(snap, stage="STAGE_INIT", checkpoint_id="chk_first")
        assert storage.count_checkpoints() == 1

        # Attempt to insert duplicate checkpoint_id with strict_mode=True
        with pytest.raises(PersistenceWriteError):
            storage.save_checkpoint(snap, stage="STAGE_DUP", checkpoint_id="chk_first")

        # Database should still have exactly 1 record and remain consistent
        assert storage.count_checkpoints() == 1
        storage.close()

    # 13. Preserve cancellation and timeout terminal states
    def test_preserve_cancellation_and_timeout_states(self, temp_db, populated_blackboard):
        bb = Blackboard(checkpoint_db_path=temp_db)
        bb.restore_from_snapshot(populated_blackboard.get_snapshot())

        # Test CANCELLED state checkpoint
        bb.update_metrics_space(
            terminated=True,
            termination_reason="Hardening job cancelled by user request.",
            final_hardening_status="CANCELLED"
        )
        cid_cancel = bb.save_checkpoint(
            stage="CANCELLED",
            job_id="job_cancelled_1",
            status="CANCELLED"
        )
        assert cid_cancel is not None

        rec_cancel = bb.storage.load_checkpoint(cid_cancel)
        assert rec_cancel.metadata.status == "CANCELLED"
        assert rec_cancel.metadata.stage == "CANCELLED"

        # Test TIMED_OUT state checkpoint
        bb.update_metrics_space(
            terminated=True,
            termination_reason="Hardening job exceeded timeout bound of 5s.",
            final_hardening_status="TIMED_OUT"
        )
        cid_to = bb.save_checkpoint(
            stage="TIMED_OUT",
            job_id="job_timeout_1",
            status="TIMED_OUT"
        )
        assert cid_to is not None

        rec_to = bb.storage.load_checkpoint(cid_to)
        assert rec_to.metadata.status == "TIMED_OUT"
        assert rec_to.metadata.stage == "TIMED_OUT"
        bb.close()

    # 14. Ensure completed checkpoints survive a simulated application restart
    def test_survives_application_restart(self, temp_db, populated_blackboard):
        # Session 1: Run and save checkpoint
        bb1 = Blackboard(checkpoint_db_path=temp_db)
        bb1.restore_from_snapshot(populated_blackboard.get_snapshot())
        cid = bb1.save_checkpoint("FINAL_SAVED", job_id="restart_job", status="SUCCESS")
        bb1.close()
        del bb1

        # Session 2: Fresh app startup, fresh Blackboard, fresh SQLite connection
        bb2 = Blackboard(checkpoint_db_path=temp_db)
        summaries = bb2.list_checkpoints(job_id="restart_job")
        assert len(summaries) == 1
        assert summaries[0].checkpoint_id == cid
        assert summaries[0].status == "SUCCESS"

        bb2.restore_checkpoint(cid)
        assert bb2.get_metrics_space().final_hardening_status == "IN_PROGRESS"
        assert bb2.get_target_space().target_module_path == "samples/discount.py"
        bb2.close()

    # 15. Verify persistence-disabled mode behaves as before (in-memory only)
    def test_persistence_disabled_mode(self, populated_blackboard):
        bb = Blackboard(checkpoint_db_path=None, storage=None)
        assert bb.has_persistence is False
        assert bb.storage is None

        # Calling save_checkpoint returns None with zero errors
        res = bb.save_checkpoint("NO_PERSIST")
        assert res is None

        # list_checkpoints returns empty list
        assert bb.list_checkpoints() == []

        # Standard Blackboard operations behave completely as before
        bb.update_metrics_space(current_iteration=3)
        assert bb.get_metrics_space().current_iteration == 3

    # 16. Verify existing Blackboard APIs and workflows remain backward compatible
    def test_existing_apis_backward_compatible(self, populated_blackboard):
        bb = Blackboard()
        # Testforge state bidirectional conversion
        state = populated_blackboard.to_testforge_state()
        assert isinstance(state, TestForgeState)
        assert state.target_module_path == "samples/discount.py"

        bb_reconstructed = Blackboard.from_testforge_state(state)
        assert bb_reconstructed.get_target_space().target_module_path == "samples/discount.py"
        assert len(bb_reconstructed.get_mutant_space().mutants) == 2

    # 17. Verify secrets/API keys are NOT written to checkpoint data
    def test_secrets_redacted_from_checkpoint(self, temp_db):
        storage = SQLiteBlackboardStorage(temp_db)
        bb = Blackboard()
        bb.update_target_space(
            target_source_code="def key_func(): return 'safe'\n",
        )
        bb.update_metrics_space(
            hardware_info={
                "cpu_count": 8,
                "api_key": "AIzaSySecretApiKey12345",
                "gemini_api_key": "secret_gemini_key",
                "nested": {
                    "openrouter_api_key": "sk-or-v1-secret",
                    "password": "SuperSecretPassword!"
                }
            }
        )
        snap = bb.get_snapshot()
        meta = storage.save_checkpoint(
            snap,
            stage="SECRET_TEST",
            extra_meta={"api_key": "secret_meta_key"}
        )

        record = storage.load_checkpoint(meta.checkpoint_id)
        raw_json = record.snapshot_json

        # Ensure no raw secrets exist anywhere in raw snapshot JSON
        assert "AIzaSySecretApiKey12345" not in raw_json
        assert "secret_gemini_key" not in raw_json
        assert "sk-or-v1-secret" not in raw_json
        assert "SuperSecretPassword!" not in raw_json
        assert "[REDACTED_SECRET]" in raw_json
        storage.close()

    # 18. Verify checkpoint events appear in existing observability mechanisms
    def test_checkpoint_events_in_observability(self, temp_db, populated_blackboard):
        events_received = []

        registry = CallbackRegistry()
        registry.register(
            lambda evt: events_received.append(evt),
            name="test_obs_listener"
        )

        bb = Blackboard(callback_registry=registry, checkpoint_db_path=temp_db)
        bb.restore_from_snapshot(populated_blackboard.get_snapshot())

        cid = bb.save_checkpoint("OBS_STAGE", job_id="job_obs_123")
        assert cid is not None

        # Verify CHECKPOINT_SAVED was dispatched
        saved_events = [e for e in events_received if e.event_type == EventType.CHECKPOINT_SAVED]
        assert len(saved_events) == 1
        assert saved_events[0].payload["checkpoint_id"] == cid
        # Clear previous events, then restore and verify CHECKPOINT_RESTORED was dispatched
        events_received.clear()
        bb.restore_checkpoint(cid)
        restored_events = [e for e in events_received if e.event_type == EventType.CHECKPOINT_RESTORED]
        assert len(restored_events) == 1
        assert restored_events[0].payload["status"] == "IN_PROGRESS"
        bb.close()


# ==============================================================================
# REST API Endpoint Tests
# ==============================================================================

class TestBlackboardPersistenceAPI:

    @pytest.fixture
    def test_client(self, tmp_path, monkeypatch):
        from starlette.testclient import TestClient

        from server import app

        api_db = tmp_path / "api_checkpoints.db"
        monkeypatch.setattr("server.DEFAULT_CHECKPOINT_DB_PATH", str(api_db))

        # Seed database with a checkpoint
        storage = SQLiteBlackboardStorage(api_db)
        bb = Blackboard()
        bb.update_target_space(
            target_module_path="samples/currency.py",
            target_source_code="def convert(c, rate): return c * rate\n",
            functions=["convert"]
        )
        bb.update_metrics_space(final_mutation_score=75.0, final_hardening_status="IN_PROGRESS")
        storage.save_checkpoint(bb.get_snapshot(), stage="API_SEED_STAGE", job_id="job_api_1")
        storage.close()

        with TestClient(app) as client:
            yield client

    def test_list_checkpoints_api(self, test_client):
        res = test_client.get("/api/checkpoints")
        assert res.status_code == 200
        data = res.json()
        assert "checkpoints" in data
        assert data["total_count"] >= 1
        assert data["checkpoints"][0]["stage"] == "API_SEED_STAGE"

    def test_get_checkpoint_details_api(self, test_client):
        res_list = test_client.get("/api/checkpoints")
        cid = res_list.json()["checkpoints"][0]["checkpoint_id"]

        res = test_client.get(f"/api/checkpoints/{cid}")
        assert res.status_code == 200
        data = res.json()
        assert data["metadata"]["checkpoint_id"] == cid
        assert data["target"]["target_module_path"] == "samples/currency.py"
        assert data["metrics"]["final_mutation_score"] == 75.0

    def test_get_nonexistent_checkpoint_404(self, test_client):
        res = test_client.get("/api/checkpoints/chk_nonexistent_999")
        assert res.status_code == 404
        assert "not found" in res.json()["detail"].lower()

    def test_restore_checkpoint_api(self, test_client):
        res_list = test_client.get("/api/checkpoints")
        cid = res_list.json()["checkpoints"][0]["checkpoint_id"]

        res = test_client.post(f"/api/checkpoints/{cid}/restore")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "restored"
        assert data["checkpoint_id"] == cid
        assert data["restored_state"]["target_module_path"] == "samples/currency.py"
