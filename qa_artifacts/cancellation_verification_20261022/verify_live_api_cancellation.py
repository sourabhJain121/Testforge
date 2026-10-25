"""
qa_artifacts/cancellation_verification_20261022/verify_live_api_cancellation.py
Deterministic live API verification for TestForge background job cancellation and timeouts.
"""

import os
import sys
import time
import json
import requests
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"
RESULTS_DIR = Path("qa_artifacts/cancellation_verification_20261022")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = RESULTS_DIR / "live_api_verification.log"
JSON_FILE = RESULTS_DIR / "live_api_results.json"

log_lines = []

def log(msg: str):
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{ts}] {msg}"
    print(line)
    log_lines.append(line)

def run_checks():
    report = {
        "timestamp": time.time(),
        "base_url": BASE_URL,
        "scenarios": {},
    }
    
    # 1. Health & Readiness
    log("=== Scenario 1: Healthz & Readyz Probes ===")
    r_h = requests.get(f"{BASE_URL}/healthz", timeout=5)
    r_r = requests.get(f"{BASE_URL}/readyz", timeout=5)
    log(f"GET /healthz -> {r_h.status_code} {r_h.json()}")
    log(f"GET /readyz -> {r_r.status_code} {r_r.json()}")
    assert r_h.status_code == 200, f"Expected 200 from /healthz, got {r_h.status_code}"
    assert r_r.status_code == 200, f"Expected 200 from /readyz, got {r_r.status_code}"
    report["scenarios"]["health_and_readiness"] = {
        "healthz": {"status_code": r_h.status_code, "body": r_h.json()},
        "readyz": {"status_code": r_r.status_code, "body": r_r.json()}
    }

    # 2. Cancel non-existent job ID
    log("\n=== Scenario 2: Cancel Non-Existent Job ID (404 Diagnosis) ===")
    dummy_id = "test123"
    r_dummy = requests.post(f"{BASE_URL}/api/harden/cancel/{dummy_id}", timeout=5)
    log(f"POST /api/harden/cancel/{dummy_id} -> {r_dummy.status_code} {r_dummy.text}")
    assert r_dummy.status_code == 404, f"Expected 404 for unknown job, got {r_dummy.status_code}"
    report["scenarios"]["cancel_unknown_job"] = {
        "job_id": dummy_id,
        "status_code": r_dummy.status_code,
        "body": r_dummy.json()
    }

    # Read a sample for hardening
    sample_file = Path("samples/banking.py")
    if not sample_file.exists():
        sample_file = Path("samples/discount.py")
    sample_code = sample_file.read_text(encoding="utf-8")

    # 3. Start real job and cancel it while active
    log("\n=== Scenario 3: Real Hardening Job Creation and Cancellation Flow ===")
    payload = {
        "target_file_path": str(sample_file),
        "target_source_code": sample_code,
        "max_iterations": 3,
        "target_mutation_score": 85.0,
        "timeout_seconds": 300,
        "engine_mode": "auto"
    }
    t_start = time.time()
    r_start = requests.post(f"{BASE_URL}/api/harden/start", json=payload, timeout=5)
    log(f"POST /api/harden/start -> {r_start.status_code} {r_start.json()}")
    assert r_start.status_code == 200
    start_data = r_start.json()
    real_job_id = start_data["job_id"]
    log(f"Spawned real hardening job: {real_job_id}")

    # Brief delay to let worker start
    time.sleep(0.4)

    # Inspect intermediate status
    r_status = requests.get(f"{BASE_URL}/api/harden/status/{real_job_id}", timeout=5)
    log(f"Initial GET /api/harden/status/{real_job_id} -> {r_status.status_code} status='{r_status.json().get('status')}'")

    # Send cancellation
    t_cancel_req = time.time()
    r_cancel = requests.post(f"{BASE_URL}/api/harden/cancel/{real_job_id}", timeout=5)
    cancel_req_latency = round(time.time() - t_cancel_req, 4)
    log(f"POST /api/harden/cancel/{real_job_id} -> {r_cancel.status_code} {r_cancel.json()} (latency: {cancel_req_latency}s)")
    assert r_cancel.status_code == 200
    cancel_data = r_cancel.json()
    assert cancel_data["status"] in ("cancelling", "cancelled")

    # Poll status until terminal CANCELLED state
    terminal_reached = False
    final_status_data = None
    lifecycle_history = []
    for poll_idx in range(60):
        time.sleep(0.5)
        r_poll = requests.get(f"{BASE_URL}/api/harden/status/{real_job_id}", timeout=5)
        st = r_poll.json().get("status")
        lifecycle_history.append({"poll": poll_idx + 1, "time": round(time.time() - t_cancel_req, 2), "status": st})
        if (poll_idx + 1) % 4 == 0 or st == "CANCELLED":
            log(f"Poll #{poll_idx+1} ({round(time.time() - t_cancel_req, 1)}s): status='{st}'")
        if st == "CANCELLED":
            terminal_reached = True
            final_status_data = r_poll.json()
            break

    total_cancel_latency = round(time.time() - t_cancel_req, 3)
    log(f"Job {real_job_id} reached terminal state CANCELLED: {terminal_reached} (total cancel duration: {total_cancel_latency}s)")
    assert terminal_reached, f"Job did not reach CANCELLED state within poll timeout"
    report["scenarios"]["live_cancellation"] = {
        "job_id": real_job_id,
        "cancel_request_latency_s": cancel_req_latency,
        "total_cancellation_duration_s": total_cancel_latency,
        "lifecycle_history": lifecycle_history,
        "final_job_data": final_status_data
    }

    # 4. Idempotency test: Cancel the already CANCELLED job again
    log("\n=== Scenario 4: Cancellation Idempotency (Terminal Job) ===")
    r_repeat = requests.post(f"{BASE_URL}/api/harden/cancel/{real_job_id}", timeout=5)
    log(f"Repeated POST /api/harden/cancel/{real_job_id} -> {r_repeat.status_code} {r_repeat.json()}")
    assert r_repeat.status_code == 200
    repeat_data = r_repeat.json()
    assert repeat_data["status"] == "already_terminal"
    assert repeat_data["current_status"] == "CANCELLED"
    report["scenarios"]["cancellation_idempotency"] = {
        "job_id": real_job_id,
        "response": repeat_data
    }

    # 5. Timeout Handling Test
    log("\n=== Scenario 5: Timeout Handling (timeout_seconds = 5) ===")
    timeout_payload = {
        "target_file_path": str(sample_file),
        "target_source_code": sample_code,
        "max_iterations": 5,
        "target_mutation_score": 95.0,
        "timeout_seconds": 5,
        "engine_mode": "auto"
    }
    t_to_start = time.time()
    r_to_start = requests.post(f"{BASE_URL}/api/harden/start", json=timeout_payload, timeout=5)
    log(f"POST /api/harden/start (timeout=5s) -> {r_to_start.status_code} {r_to_start.json()}")
    assert r_to_start.status_code == 200
    to_job_id = r_to_start.json()["job_id"]

    to_terminal_reached = False
    to_final_data = None
    to_lifecycle = []
    for poll_idx in range(40):
        time.sleep(0.5)
        r_poll = requests.get(f"{BASE_URL}/api/harden/status/{to_job_id}", timeout=5)
        st = r_poll.json().get("status")
        to_lifecycle.append({"poll": poll_idx + 1, "time": round(time.time() - t_to_start, 2), "status": st})
        if (poll_idx + 1) % 4 == 0 or st == "TIMED_OUT":
            log(f"Timeout Poll #{poll_idx+1} ({round(time.time() - t_to_start, 1)}s): status='{st}'")
        if st == "TIMED_OUT":
            to_terminal_reached = True
            to_final_data = r_poll.json()
            break

    total_timeout_duration = round(time.time() - t_to_start, 2)
    log(f"Job {to_job_id} reached terminal state TIMED_OUT: {to_terminal_reached} in {total_timeout_duration}s")
    assert to_terminal_reached, f"Job {to_job_id} did not reach TIMED_OUT within poll limit"
    report["scenarios"]["timeout_verification"] = {
        "job_id": to_job_id,
        "configured_timeout_s": 5,
        "actual_duration_s": total_timeout_duration,
        "to_lifecycle": to_lifecycle,
        "final_job_data": to_final_data
    }

    # 6. Verify subsequent job execution works normally
    log("\n=== Scenario 6: Subsequent Job Execution Post-Cancellation ===")
    post_payload = {
        "target_file_path": "samples/simple_math.py",
        "target_source_code": "def add(a, b):\n    return a + b\n",
        "max_iterations": 1,
        "target_mutation_score": 50.0,
        "timeout_seconds": 60,
        "engine_mode": "auto"
    }
    r_post = requests.post(f"{BASE_URL}/api/harden/start", json=post_payload, timeout=5)
    log(f"POST /api/harden/start (post-cancellation job) -> {r_post.status_code} {r_post.json()}")
    assert r_post.status_code == 200
    post_job_id = r_post.json()["job_id"]
    time.sleep(0.5)
    r_post_st = requests.get(f"{BASE_URL}/api/harden/status/{post_job_id}", timeout=5)
    log(f"Subsequent job {post_job_id} status: {r_post_st.json().get('status')}")
    assert r_post_st.json().get("status") in ("QUEUED", "RUNNING", "COMPLETED")
    report["scenarios"]["post_cancellation_job"] = {
        "job_id": post_job_id,
        "status": r_post_st.json().get("status")
    }

    report["verdict"] = "PASS"
    log("\n>>> ALL LIVE API CANCELLATION & TIMEOUT SCENARIOS PASSED! <<<")

    # Save results
    JSON_FILE.write_text(json.dumps(report, indent=2), encoding="utf-8")
    LOG_FILE.write_text("\n".join(log_lines), encoding="utf-8")
    log(f"Saved machine-readable results to {JSON_FILE}")
    log(f"Saved full execution log to {LOG_FILE}")
    return report

if __name__ == "__main__":
    run_checks()
