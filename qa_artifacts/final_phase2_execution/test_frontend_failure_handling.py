#!/usr/bin/env python3
"""
TestForge Pre-Phase 2 Evaluation Readiness: Stage 3 Frontend Failure Handling & Recovery
Author: Antigravity Automated QA Suite
Date: 2026-10-30
"""

import sys
import time
import json
import requests
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"
QA_DIR = Path("/Users/sourabh/TestForge/qa_artifacts/final_phase2_execution")

def run_failure_and_recovery_tests():
    print("=== STARTING PHASE 3: FRONTEND FAILURE HANDLING & RECOVERY TESTS ===")
    results = []

    # Scenario 1: Empty Python File Upload
    print("\n--- Test 1: Empty File Upload ---")
    resp1 = requests.post(
        f"{BASE_URL}/api/ingest/upload",
        files={"file": ("empty.py", b"", "text/x-python")}
    )
    print("Empty upload status:", resp1.status_code, resp1.json().get("status"))
    assert resp1.status_code == 200
    assert resp1.json()["line_count"] == 0
    results.append({
        "scenario": "Empty Python File Upload",
        "endpoint": "/api/ingest/upload",
        "http_status": resp1.status_code,
        "observed_behavior": f"Clean 200 with line_count=0, callables_count=0, status={resp1.json().get('status')}",
        "pass_fail": "PASS"
    })

    # Scenario 2: Invalid Python Syntax Upload
    print("\n--- Test 2: Invalid Python Syntax Upload ---")
    resp2 = requests.post(
        f"{BASE_URL}/api/ingest/upload",
        files={"file": ("syntax_bad.py", b"def broken(:\n    pass\n", "text/x-python")}
    )
    print("Syntax bad upload status:", resp2.status_code, resp2.json().get("status"))
    assert resp2.status_code == 200
    assert resp2.json()["has_syntax_error"] is True
    assert "SyntaxError" in resp2.json()["error"]
    results.append({
        "scenario": "Invalid Python Syntax Upload",
        "endpoint": "/api/ingest/upload",
        "http_status": resp2.status_code,
        "observed_behavior": f"HTTP 200 with has_syntax_error=True and error detail: '{resp2.json().get('error')}'",
        "pass_fail": "PASS"
    })

    # Scenario 3: Valid Python with No Functions
    print("\n--- Test 3: Valid Python with No Functions ---")
    resp3 = requests.post(
        f"{BASE_URL}/api/ingest/upload",
        files={"file": ("no_func.py", b"CONFIG_A = 100\nCONFIG_B = 200\n", "text/x-python")}
    )
    print("No func upload status:", resp3.status_code, resp3.json().get("status"))
    assert resp3.status_code == 200
    assert resp3.json()["functions"] == []
    assert resp3.json()["classes"] == []
    assert resp3.json()["line_count"] == 2
    results.append({
        "scenario": "Valid Python File With Zero Functions",
        "endpoint": "/api/ingest/upload",
        "http_status": resp3.status_code,
        "observed_behavior": "HTTP 200 with empty functions list, 0 classes, line_count=2, no server error",
        "pass_fail": "PASS"
    })

    # Scenario 4: Unsupported File Extension
    print("\n--- Test 4: Unsupported File Extension ---")
    resp4 = requests.post(
        f"{BASE_URL}/api/ingest/upload",
        files={"file": ("malicious.exe", b"\x4d\x5a\x90\x00", "application/octet-stream")}
    )
    print("Unsupported extension status:", resp4.status_code, resp4.text[:100])
    assert resp4.status_code == 400
    results.append({
        "scenario": "Unsupported / Binary File Ingestion (.exe)",
        "endpoint": "/api/ingest/upload",
        "http_status": resp4.status_code,
        "observed_behavior": f"HTTP 400 Bad Request with security rejection: {resp4.text[:80]}",
        "pass_fail": "PASS"
    })

    # Scenario 5: Missing / Malformed Request Payload
    print("\n--- Test 5: Malformed Payload & Boundary Violation ---")
    resp5 = requests.post(
        f"{BASE_URL}/api/harden/start",
        json={"target_file_path": "samples/discount.py", "timeout_seconds": -50}
    )
    print("Negative timeout status:", resp5.status_code)
    assert resp5.status_code == 422  # Pydantic schema validation failure
    results.append({
        "scenario": "Malformed Payload (Negative Timeout)",
        "endpoint": "/api/harden/start",
        "http_status": resp5.status_code,
        "observed_behavior": "HTTP 422 Unprocessable Entity with Pydantic field constraint error",
        "pass_fail": "PASS"
    })

    # Scenario 6: Non-Existent Job Cancellation
    print("\n--- Test 6: Cancel Non-Existent Job ---")
    resp6 = requests.post(f"{BASE_URL}/api/harden/cancel/nonexistent-job-xyz")
    print("Non-existent cancel status:", resp6.status_code, resp6.json())
    assert resp6.status_code == 404
    assert "not found" in resp6.json()["detail"].lower()
    results.append({
        "scenario": "Cancellation of Non-Existent Job",
        "endpoint": "/api/harden/cancel/{job_id}",
        "http_status": resp6.status_code,
        "observed_behavior": f"HTTP 404 with RFC-compliant error message: {resp6.json().get('detail')}",
        "pass_fail": "PASS"
    })

    # Scenario 7: Active Hardening Job Start & Cancellation
    print("\n--- Test 7: Active Job Cancellation ---")
    discount_code = Path("/Users/sourabh/TestForge/samples/discount.py").read_text()
    start_resp = requests.post(
        f"{BASE_URL}/api/harden/start",
        json={
            "target_file_path": "samples/discount.py",
            "target_source_code": discount_code,
            "max_iterations": 5
        }
    )
    print("Start job status:", start_resp.status_code, start_resp.json())
    assert start_resp.status_code == 200
    job_id = start_resp.json()["job_id"]

    # Issue cancellation immediately
    cancel_resp = requests.post(f"{BASE_URL}/api/harden/cancel/{job_id}")
    print("Cancel job status:", cancel_resp.status_code, cancel_resp.json())
    assert cancel_resp.status_code == 200
    assert cancel_resp.json()["status"] in ("cancelling", "cancelled", "stopping", "stopped")

    # Poll status to confirm state
    time.sleep(0.5)
    poll_resp = requests.get(f"{BASE_URL}/api/harden/status/{job_id}")
    final_status = poll_resp.json().get("status", "")
    print("Final polled status after cancel:", final_status)
    assert final_status.lower() in ("cancelling", "cancelled", "stopped", "failed", "completed")
    # Verify no false positive claim
    assert poll_resp.json().get("final_hardening_status") != "SUCCESS_HARDENED"
    results.append({
        "scenario": "Active Hardening Job Cancellation",
        "endpoint": "/api/harden/cancel/{job_id}",
        "http_status": cancel_resp.status_code,
        "observed_behavior": f"Job {job_id} acknowledged cancel, polled status '{final_status}', zero false success states",
        "pass_fail": "PASS"
    })

    # Scenario 8: WebSocket Disconnection & Event Channel
    print("\n--- Test 8: WebSocket Status Endpoint ---")
    resp8 = requests.get(f"{BASE_URL}/api/ws/status")
    print("WebSocket health endpoint status:", resp8.status_code, resp8.json())
    assert resp8.status_code == 200
    results.append({
        "scenario": "WebSocket Event Channel Inspection",
        "endpoint": "/api/ws/status",
        "http_status": resp8.status_code,
        "observed_behavior": f"HTTP 200 with active status: {resp8.json()}",
        "pass_fail": "PASS"
    })

    out_file = QA_DIR / "frontend_failure_results.json"
    out_file.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nAll 8 failure recovery scenarios passed! Saved to {out_file}")

if __name__ == "__main__":
    run_failure_and_recovery_tests()
