"""
tests/test_cancellation.py - Comprehensive Unit & Integration Tests for Hardening Cancellation & Graceful Timeout.

Covers:
  1. Cancellation of a queued job.
  2. Cancellation of a running job.
  3. Repeated cancellation requests (idempotency).
  4. Cancellation of an unknown job ID.
  5. Cancellation of an already completed job.
  6. Cancellation of an already failed job.
  7. Normal completion racing with cancellation.
  8. Timeout of a running job (TIMED_OUT status).
  9. Cancellation during a reflection loop.
  10. Cancellation during a long-running subprocess.
  11. Subprocess termination and cleanup.
  12. Preservation of partial results and diagnostics.
  13. Prevention of additional work after cancellation.
  14. Thread-safe state transitions.
  15. A new job starting successfully after a cancelled job.
  16. API status and error response behavior (bounds validation, sanitization).
  17. Frontend integration (cancellation elements, CSS, script bindings).
"""

from __future__ import annotations
import os
import sys
import time
import uuid
import threading
import concurrent.futures
from pathlib import Path
from typing import Dict, Any

import pytest
from fastapi.testclient import TestClient

from server import app, JOBS, JOB_LOCK
from testforge.orchestrator import (
    TestForgeOrchestrator,
    HardeningCancelledError,
    HardeningTimeoutError,
)
from testforge.sandbox import ParallelSandboxRunner
from testforge.mutator import ASTMutator
from testforge.blackboard import Blackboard


TARGET_CODE = """
def calculate_fee(amount: float, is_vip: bool) -> float:
    if amount <= 0:
        return 0.0
    fee_rate = 0.01 if is_vip else 0.03
    return amount * fee_rate
"""

INITIAL_TEST = """
from target import calculate_fee

def test_nominal():
    assert calculate_fee(100.0, True) == 1.0
    assert calculate_fee(100.0, False) == 3.0
    assert calculate_fee(-10.0, False) == 0.0
"""


@pytest.fixture
def client():
    return TestClient(app)


# -----------------------------------------------------------------------------
# 1. Cancellation of a queued job
# -----------------------------------------------------------------------------
def test_cancellation_of_queued_job(client):
    job_id = f"test_q_{uuid.uuid4().hex[:6]}"
    cancel_evt = threading.Event()
    with JOB_LOCK:
        JOBS[job_id] = {
            "job_id": job_id,
            "status": "QUEUED",
            "created_at": time.time(),
            "target_file_path": "samples/discount.py",
            "timeout_seconds": 300,
            "_cancel_event": cancel_evt,
            "_orchestrator": None,
        }

    res = client.post(f"/api/harden/cancel/{job_id}")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "cancelled"
    assert data["current_status"] == "CANCELLED"
    assert cancel_evt.is_set()

    with JOB_LOCK:
        assert JOBS[job_id]["status"] == "CANCELLED"


# -----------------------------------------------------------------------------
# 2. Cancellation of a running job
# -----------------------------------------------------------------------------
def test_cancellation_of_running_job(client):
    job_id = f"test_run_{uuid.uuid4().hex[:6]}"
    cancel_evt = threading.Event()
    with JOB_LOCK:
        JOBS[job_id] = {
            "job_id": job_id,
            "status": "RUNNING",
            "start_time": time.time(),
            "target_file_path": "samples/discount.py",
            "timeout_seconds": 300,
            "_cancel_event": cancel_evt,
            "_orchestrator": None,
        }

    res = client.post(f"/api/harden/cancel/{job_id}")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "cancelling"
    assert data["current_status"] == "CANCELLING"
    assert cancel_evt.is_set()

    with JOB_LOCK:
        assert JOBS[job_id]["status"] == "CANCELLING"


# -----------------------------------------------------------------------------
# 3. Repeated cancellation requests (idempotent)
# -----------------------------------------------------------------------------
def test_repeated_cancellation_idempotent(client):
    job_id = f"test_idemp_{uuid.uuid4().hex[:6]}"
    cancel_evt = threading.Event()
    with JOB_LOCK:
        JOBS[job_id] = {
            "job_id": job_id,
            "status": "RUNNING",
            "start_time": time.time(),
            "timeout_seconds": 300,
            "_cancel_event": cancel_evt,
            "_orchestrator": None,
        }

    # First cancel -> CANCELLING
    res1 = client.post(f"/api/harden/cancel/{job_id}")
    assert res1.status_code == 200
    assert res1.json()["status"] == "cancelling"

    # Second cancel -> already CANCELLING
    res2 = client.post(f"/api/harden/cancel/{job_id}")
    assert res2.status_code == 200
    assert res2.json()["status"] == "cancelling"

    # Worker marks CANCELLED
    with JOB_LOCK:
        JOBS[job_id]["status"] = "CANCELLED"

    # Third cancel -> already_terminal
    res3 = client.post(f"/api/harden/cancel/{job_id}")
    assert res3.status_code == 200
    data3 = res3.json()
    assert data3["status"] == "already_terminal"
    assert data3["current_status"] == "CANCELLED"


# -----------------------------------------------------------------------------
# 4. Cancellation of an unknown job ID
# -----------------------------------------------------------------------------
def test_cancellation_unknown_job_id(client):
    res = client.post("/api/harden/cancel/nonexistent_xyz_999")
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


# -----------------------------------------------------------------------------
# 5. Cancellation of an already completed job
# -----------------------------------------------------------------------------
def test_cancellation_already_completed_job(client):
    job_id = f"test_done_{uuid.uuid4().hex[:6]}"
    with JOB_LOCK:
        JOBS[job_id] = {
            "job_id": job_id,
            "status": "COMPLETED",
            "start_time": time.time() - 10,
            "end_time": time.time(),
            "_cancel_event": threading.Event(),
        }

    res = client.post(f"/api/harden/cancel/{job_id}")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "already_terminal"
    assert data["current_status"] == "COMPLETED"

    with JOB_LOCK:
        assert JOBS[job_id]["status"] == "COMPLETED"


# -----------------------------------------------------------------------------
# 6. Cancellation of an already failed job
# -----------------------------------------------------------------------------
def test_cancellation_already_failed_job(client):
    job_id = f"test_fail_{uuid.uuid4().hex[:6]}"
    with JOB_LOCK:
        JOBS[job_id] = {
            "job_id": job_id,
            "status": "FAILED",
            "error": "SyntaxError in synthesized tests",
            "end_time": time.time(),
            "_cancel_event": threading.Event(),
        }

    res = client.post(f"/api/harden/cancel/{job_id}")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "already_terminal"
    assert data["current_status"] == "FAILED"

    with JOB_LOCK:
        assert JOBS[job_id]["status"] == "FAILED"


# -----------------------------------------------------------------------------
# 7. Normal completion racing with cancellation
# -----------------------------------------------------------------------------
def test_completion_racing_with_cancellation(client):
    job_id = f"test_race_{uuid.uuid4().hex[:6]}"
    cancel_evt = threading.Event()
    with JOB_LOCK:
        JOBS[job_id] = {
            "job_id": job_id,
            "status": "RUNNING",
            "start_time": time.time(),
            "_cancel_event": cancel_evt,
        }

    def simulate_finish():
        with JOB_LOCK:
            JOBS[job_id]["status"] = "COMPLETED"
            JOBS[job_id]["end_time"] = time.time()

    def simulate_cancel():
        return client.post(f"/api/harden/cancel/{job_id}")

    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        f1 = executor.submit(simulate_finish)
        f2 = executor.submit(simulate_cancel)
        f1.result()
        res = f2.result()

    # Terminal state must be COMPLETED or CANCELLED, never corrupted or in CANCELLING
    with JOB_LOCK:
        final_st = JOBS[job_id]["status"]
        assert final_st in ("COMPLETED", "CANCELLED")


# -----------------------------------------------------------------------------
# 8. Timeout of a running job
# -----------------------------------------------------------------------------
def test_timeout_of_running_job():
    cancel_evt = threading.Event()
    orch = TestForgeOrchestrator(
        target_source_code=TARGET_CODE,
        initial_test_code=INITIAL_TEST,
        max_iterations=3,
        target_mutation_score=100.0,
        cancel_event=cancel_evt,
        timeout_seconds=0.001,  # immediate timeout bound
        job_id="test_timeout_001",
    )
    # Simulate past start time
    orch._start_time = time.perf_counter() - 5.0

    state = orch.run()
    assert state.final_hardening_status == "TIMED_OUT"
    assert "timeout" in state.termination_reason.lower()


# -----------------------------------------------------------------------------
# 9. Cancellation during a reflection loop
# -----------------------------------------------------------------------------
def test_cancellation_during_reflection_loop():
    cancel_evt = threading.Event()
    orch = TestForgeOrchestrator(
        target_source_code=TARGET_CODE,
        initial_test_code=INITIAL_TEST,
        max_iterations=5,
        target_mutation_score=100.0,
        cancel_event=cancel_evt,
        timeout_seconds=300,
        job_id="test_loop_cancel",
    )

    # Cancel before running
    cancel_evt.set()
    state = orch.run()

    assert state.final_hardening_status == "CANCELLED"
    assert state.current_iteration == 0
    assert "cancelled" in state.termination_reason.lower()


# -----------------------------------------------------------------------------
# 10. Cancellation during long-running subprocess
# -----------------------------------------------------------------------------
def test_cancellation_during_parallel_sandbox():
    cancel_evt = threading.Event()
    sandbox = ParallelSandboxRunner(timeout_seconds=3, max_workers=2, cancel_event=cancel_evt)

    # Pre-cancel
    cancel_evt.set()

    mutants = ASTMutator.generate_mutants(TARGET_CODE)
    evaluated = sandbox.evaluate_mutants_parallel(INITIAL_TEST, mutants)

    # Unexecuted mutants returned without evaluation
    assert len(evaluated) == len(mutants)
    assert all(m.status == "PENDING" for m in evaluated)


# -----------------------------------------------------------------------------
# 11. Subprocess termination and cleanup
# -----------------------------------------------------------------------------
def test_sandbox_single_run_respects_cancellation():
    cancel_evt = threading.Event()
    sandbox = ParallelSandboxRunner(timeout_seconds=3, cancel_event=cancel_evt)
    cancel_evt.set()

    res = sandbox.run_single(INITIAL_TEST, TARGET_CODE)
    assert res["status"] == "CANCELLED"
    assert res["cancelled"] is True


# -----------------------------------------------------------------------------
# 12. Preservation of partial results and diagnostics
# -----------------------------------------------------------------------------
def test_preservation_of_partial_results():
    cancel_evt = threading.Event()
    orch = TestForgeOrchestrator(
        target_source_code=TARGET_CODE,
        initial_test_code=INITIAL_TEST,
        max_iterations=3,
        cancel_event=cancel_evt,
        job_id="test_partial_preservation",
    )

    # Step 1: Synthesize initial tests
    orch.blackboard.update_suite_space(current_test_code=INITIAL_TEST)
    orch.state.current_test_code = INITIAL_TEST

    # Signal cancellation
    cancel_evt.set()
    state = orch.run()

    # Tests generated before cancel must still be in final_state
    assert state.current_test_code == INITIAL_TEST
    assert state.final_hardening_status == "CANCELLED"


# -----------------------------------------------------------------------------
# 13. Prevention of additional work after cancellation
# -----------------------------------------------------------------------------
def test_prevention_of_additional_work():
    cancel_evt = threading.Event()
    orch = TestForgeOrchestrator(
        target_source_code=TARGET_CODE,
        initial_test_code=INITIAL_TEST,
        cancel_event=cancel_evt,
        job_id="test_no_additional_work",
    )
    cancel_evt.set()

    with pytest.raises(HardeningCancelledError):
        orch.check_cancellation_or_timeout()


# -----------------------------------------------------------------------------
# 14. Thread-safe state transitions
# -----------------------------------------------------------------------------
def test_thread_safe_state_transitions(client):
    job_id = f"test_threads_{uuid.uuid4().hex[:6]}"
    cancel_evt = threading.Event()
    with JOB_LOCK:
        JOBS[job_id] = {
            "job_id": job_id,
            "status": "RUNNING",
            "start_time": time.time(),
            "_cancel_event": cancel_evt,
        }

    errors = []

    def poller():
        for _ in range(20):
            res = client.get(f"/api/harden/status/{job_id}")
            if res.status_code != 200:
                errors.append(f"Poller received {res.status_code}")
            time.sleep(0.005)

    def canceller():
        time.sleep(0.02)
        res = client.post(f"/api/harden/cancel/{job_id}")
        if res.status_code != 200:
            errors.append(f"Canceller received {res.status_code}")

    threads = [
        threading.Thread(target=poller),
        threading.Thread(target=poller),
        threading.Thread(target=canceller),
    ]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0
    with JOB_LOCK:
        assert JOBS[job_id]["status"] in ("CANCELLING", "CANCELLED")


# -----------------------------------------------------------------------------
# 15. A new job starting successfully after a cancelled job
# -----------------------------------------------------------------------------
def test_new_job_after_cancelled_job(client):
    # Job 1: Cancelled
    payload1 = {
        "target_file_path": "samples/discount.py",
        "target_source_code": TARGET_CODE,
        "max_iterations": 1,
        "timeout_seconds": 60,
    }
    res1 = client.post("/api/harden/start", json=payload1)
    assert res1.status_code == 200
    job1_id = res1.json()["job_id"]

    cancel_res = client.post(f"/api/harden/cancel/{job1_id}")
    assert cancel_res.status_code == 200

    # Job 2: Fresh job starts cleanly
    payload2 = {
        "target_file_path": "samples/discount.py",
        "target_source_code": TARGET_CODE,
        "max_iterations": 1,
        "timeout_seconds": 60,
    }
    res2 = client.post("/api/harden/start", json=payload2)
    assert res2.status_code == 200
    job2_id = res2.json()["job_id"]
    assert job2_id != job1_id

    status2 = client.get(f"/api/harden/status/{job2_id}")
    assert status2.status_code == 200
    assert status2.json()["status"] in ("QUEUED", "RUNNING", "COMPLETED")


# -----------------------------------------------------------------------------
# 16. API status and error response behavior
# -----------------------------------------------------------------------------
def test_api_status_and_payload_validation(client):
    # Missing source code -> 400
    bad_res1 = client.post("/api/harden/start", json={
        "target_file_path": "foo.py",
        "target_source_code": "   "
    })
    assert bad_res1.status_code == 400

    # Invalid timeout: timeout_seconds < 5 -> 422
    bad_res2 = client.post("/api/harden/start", json={
        "target_file_path": "foo.py",
        "target_source_code": "def foo(): pass",
        "timeout_seconds": 2
    })
    assert bad_res2.status_code == 422

    # Status response does not leak internal keys (_cancel_event, etc.)
    job_id = f"test_sanitize_{uuid.uuid4().hex[:6]}"
    with JOB_LOCK:
        JOBS[job_id] = {
            "job_id": job_id,
            "status": "QUEUED",
            "_cancel_event": threading.Event(),
            "_orchestrator": None,
            "created_at": time.time(),
        }

    status_res = client.get(f"/api/harden/status/{job_id}")
    assert status_res.status_code == 200
    data = status_res.json()
    assert "_cancel_event" not in data
    assert "_orchestrator" not in data
    assert "job_id" in data


# -----------------------------------------------------------------------------
# 17. Frontend integration (cancellation elements, CSS, script bindings)
# -----------------------------------------------------------------------------
def test_frontend_cancellation_integration(client):
    # Verify index.html contains #btn-cancel-hardening
    res_index = client.get("/")
    assert res_index.status_code == 200
    assert "btn-cancel-hardening" in res_index.text

    # Verify style.css contains .btn-danger and .verdict-banner.cancelled
    res_css = client.get("/static/style.css")
    assert res_css.status_code == 200
    assert ".btn-danger" in res_css.text
    assert ".verdict-banner.cancelled" in res_css.text

    # Verify app.js contains cancelHardeningJob and event listener
    res_js = client.get("/static/app.js")
    assert res_js.status_code == 200
    assert "cancelHardeningJob" in res_js.text
    assert "/api/harden/cancel/" in res_js.text
