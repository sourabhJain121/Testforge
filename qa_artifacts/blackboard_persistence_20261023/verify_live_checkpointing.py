"""
verify_live_checkpointing.py - End-to-end live verification of SQLite Blackboard Checkpointing.
Validates stages, recovery in a fresh Blackboard, cancellation/timeout checkpoints, and REST endpoints.
"""

import os
import sys
import time
import json
import threading
from pathlib import Path

from testforge.orchestrator import TestForgeOrchestrator
from testforge.blackboard import Blackboard
from testforge.persistence import SQLiteBlackboardStorage
from testforge.state import TestForgeState

OUTPUT_DIR = Path("qa_artifacts/blackboard_persistence_20261023")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
LIVE_DB = OUTPUT_DIR / "live_hardening_checkpoints.db"
LOG_FILE = OUTPUT_DIR / "live_verification.log"
RESULTS_FILE = OUTPUT_DIR / "live_verification_results.json"

log_lines = []

def log(msg: str):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    log_lines.append(line)

def run_live_verification():
    report = {
        "timestamp": time.time(),
        "database": str(LIVE_DB),
        "stages_verified": [],
        "scenarios": {},
    }

    if LIVE_DB.exists():
        LIVE_DB.unlink()

    # --------------------------------------------------------------------------
    # Scenario 1: Full Hardening Pipeline with Automatic Checkpoint Stages
    # --------------------------------------------------------------------------
    log("=== Scenario 1: Live Hardening Pipeline with Checkpointing ===")
    sample_code = (
        "def compute_interest(principal: float, rate: float, time_years: int) -> float:\n"
        "    if principal < 0 or rate < 0 or time_years < 0:\n"
        "        return 0.0\n"
        "    return principal * rate * time_years\n"
    )
    initial_tests = (
        "import pytest\n"
        "from target import compute_interest\n\n"
        "def test_compute_interest_basic():\n"
        "    assert compute_interest(1000.0, 0.05, 2) == 100.0\n\n"
        "def test_compute_interest_negative():\n"
        "    assert compute_interest(-100.0, 0.05, 2) == 0.0\n"
        "    assert compute_interest(100.0, -0.05, 2) == 0.0\n"
        "    assert compute_interest(100.0, 0.05, -2) == 0.0\n"
    )

    t0 = time.time()
    orchestrator = TestForgeOrchestrator(
        target_source_code=sample_code,
        initial_test_code=initial_tests,
        max_iterations=2,
        target_mutation_score=80.0,
        job_id="job_live_001",
        checkpoint_db_path=str(LIVE_DB),
    )
    final_state = orchestrator.run()
    duration = time.time() - t0
    log(f"Pipeline executed in {duration:.2f}s with status '{final_state.final_hardening_status}'")

    # Inspect SQLite database for checkpoints
    storage = SQLiteBlackboardStorage(LIVE_DB)
    summaries = storage.list_checkpoints(job_id="job_live_001")
    stages_saved = [s.stage for s in summaries]
    log(f"Checkpoints created ({len(summaries)} total): {stages_saved}")
    assert len(summaries) >= 3, f"Expected at least 3 checkpoints, found {len(summaries)}"
    assert "INITIAL_INGESTION" in stages_saved
    assert "BASELINE_VALIDATED" in stages_saved
    assert "FINALIZED" in stages_saved

    report["scenarios"]["pipeline_checkpoints"] = {
        "job_id": "job_live_001",
        "checkpoint_count": len(summaries),
        "stages": stages_saved,
        "final_status": final_state.final_hardening_status,
        "final_mutation_score": final_state.final_mutation_score,
    }

    # --------------------------------------------------------------------------
    # Scenario 2: Recovery into a Fresh Blackboard Instance
    # --------------------------------------------------------------------------
    log("\n=== Scenario 2: Recovery in a Fresh Blackboard Instance ===")
    final_chk = storage.get_latest_checkpoint(job_id="job_live_001")
    assert final_chk is not None
    fresh_bb = Blackboard(checkpoint_db_path=LIVE_DB)
    fresh_bb.restore_checkpoint(final_chk.metadata.checkpoint_id)

    restored_target = fresh_bb.get_target_space()
    restored_metrics = fresh_bb.get_metrics_space()
    log(f"Restored target functions: {restored_target.functions}")
    log(f"Restored mutation score: {restored_metrics.final_mutation_score}%")
    log(f"Restored hardening status: {restored_metrics.final_hardening_status}")
    assert "compute_interest" in restored_target.functions
    assert restored_metrics.final_mutation_score == final_state.final_mutation_score
    fresh_bb.close()

    report["scenarios"]["fresh_blackboard_recovery"] = {
        "checkpoint_id": final_chk.metadata.checkpoint_id,
        "restored_functions": restored_target.functions,
        "restored_mutation_score": restored_metrics.final_mutation_score,
    }

    # --------------------------------------------------------------------------
    # Scenario 3: Checkpointing on Cooperative Cancellation
    # --------------------------------------------------------------------------
    log("\n=== Scenario 3: Checkpointing on Cooperative Cancellation ===")
    cancel_evt = threading.Event()
    cancel_evt.set()  # Pre-cancelled to trigger cancellation immediately
    orch_cancel = TestForgeOrchestrator(
        target_source_code=sample_code,
        initial_test_code=initial_tests,
        max_iterations=3,
        job_id="job_cancelled_002",
        checkpoint_db_path=str(LIVE_DB),
        cancel_event=cancel_evt,
    )
    res_cancel = orch_cancel.run()
    log(f"Cancellation run outcome: {res_cancel.final_hardening_status}")
    assert res_cancel.final_hardening_status == "CANCELLED"

    cancel_chk = storage.get_latest_checkpoint(job_id="job_cancelled_002")
    assert cancel_chk is not None
    assert cancel_chk.metadata.status == "CANCELLED"
    assert cancel_chk.metadata.stage == "CANCELLED"
    log(f"Confirmed CANCELLED checkpoint: {cancel_chk.metadata.checkpoint_id}")

    report["scenarios"]["cancellation_checkpoint"] = {
        "job_id": "job_cancelled_002",
        "checkpoint_id": cancel_chk.metadata.checkpoint_id,
        "status": cancel_chk.metadata.status,
    }

    # --------------------------------------------------------------------------
    # Scenario 4: Checkpointing on Timeout
    # --------------------------------------------------------------------------
    log("\n=== Scenario 4: Checkpointing on Bounded Timeout ===")
    orch_to = TestForgeOrchestrator(
        target_source_code=sample_code,
        initial_test_code=initial_tests,
        max_iterations=3,
        job_id="job_timeout_003",
        checkpoint_db_path=str(LIVE_DB),
        timeout_seconds=1,
    )
    orch_to._start_time = time.perf_counter() - 5.0  # Simulate 5s elapsed against 1s limit
    res_to = orch_to.run()
    log(f"Timeout run outcome: {res_to.final_hardening_status}")
    assert res_to.final_hardening_status == "TIMED_OUT"

    to_chk = storage.get_latest_checkpoint(job_id="job_timeout_003")
    assert to_chk is not None
    assert to_chk.metadata.status == "TIMED_OUT"
    assert to_chk.metadata.stage == "TIMED_OUT"
    log(f"Confirmed TIMED_OUT checkpoint: {to_chk.metadata.checkpoint_id}")

    report["scenarios"]["timeout_checkpoint"] = {
        "job_id": "job_timeout_003",
        "checkpoint_id": to_chk.metadata.checkpoint_id,
        "status": to_chk.metadata.status,
    }

    storage.close()

    # --------------------------------------------------------------------------
    # Scenario 5: REST Endpoints Verification
    # --------------------------------------------------------------------------
    log("\n=== Scenario 5: REST API Checkpoint Endpoints ===")
    from starlette.testclient import TestClient
    from server import app
    import server

    # Point server to live test database
    server.DEFAULT_CHECKPOINT_DB_PATH = str(LIVE_DB)

    with TestClient(app) as client:
        # GET /readyz (check sqlite_persistence)
        r_ready = client.get("/readyz")
        assert r_ready.status_code == 200
        assert r_ready.json()["subsystems"]["sqlite_persistence"] == "operational"
        log("GET /readyz: sqlite_persistence subsystem operational")

        # GET /api/checkpoints
        r_list = client.get("/api/checkpoints")
        assert r_list.status_code == 200
        chk_list_data = r_list.json()
        total_chks = chk_list_data["total_count"]
        log(f"GET /api/checkpoints returned {total_chks} checkpoints across jobs")
        assert total_chks >= 4

        # GET /api/checkpoints/{id}
        first_cid = chk_list_data["checkpoints"][0]["checkpoint_id"]
        r_detail = client.get(f"/api/checkpoints/{first_cid}")
        assert r_detail.status_code == 200
        detail_data = r_detail.json()
        assert detail_data["metadata"]["checkpoint_id"] == first_cid
        log(f"GET /api/checkpoints/{first_cid} returned structured details: stage='{detail_data['metadata']['stage']}'")

        # POST /api/checkpoints/{id}/restore
        r_restore = client.post(f"/api/checkpoints/{first_cid}/restore")
        assert r_restore.status_code == 200
        restore_data = r_restore.json()
        assert restore_data["status"] == "restored"
        assert restore_data["checkpoint_id"] == first_cid
        log(f"POST /api/checkpoints/{first_cid}/restore successful: restored revision {restore_data['revision']}")

    report["scenarios"]["rest_api"] = {
        "readyz_sqlite_persistence": "operational",
        "total_checkpoints_listed": total_chks,
        "sample_checkpoint_id": first_cid,
        "restored_revision": restore_data["revision"],
    }

    report["verdict"] = "PASS"
    log("\n>>> ALL LIVE CHECKPOINTING SCENARIOS PASSED WITH CODE 0! <<<")

    RESULTS_FILE.write_text(json.dumps(report, indent=2), encoding="utf-8")
    LOG_FILE.write_text("\n".join(log_lines), encoding="utf-8")
    log(f"Saved results to {RESULTS_FILE}")
    log(f"Saved log to {LOG_FILE}")
    return report

if __name__ == "__main__":
    run_live_verification()
