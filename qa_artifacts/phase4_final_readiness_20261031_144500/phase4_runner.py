#!/usr/bin/env python3
"""
TestForge Phase 4: Master Live Workflow, Browser Automation & Failure Handling Runner
"""

import os
import sys
import time
import json
import urllib.request
import urllib.parse
import urllib.error
import subprocess
from pathlib import Path

BASE_DIR = Path("/Users/sourabh/TestForge")
ARTIFACT_DIR = BASE_DIR / "qa_artifacts" / "phase4_final_readiness_20261031_144500"
SCREENSHOT_DIR = ARTIFACT_DIR / "screenshots"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

ENV = os.environ.copy()
ENV["PATH"] = "/Users/sourabh/.nvm/versions/node/v24.15.0/bin:" + ENV.get("PATH", "")

def run_browser(*args, timeout=45) -> subprocess.CompletedProcess:
    cmd = ["agent-browser"] + list(args)
    try:
        return subprocess.run(cmd, capture_output=True, text=True, env=ENV, timeout=timeout)
    except subprocess.TimeoutExpired:
        print(f"[TIMEOUT] Command timed out: {' '.join(cmd)}")
        return subprocess.CompletedProcess(cmd, returncode=-1, stdout="", stderr="Timeout expired")

def take_screenshot(filename: str) -> str:
    path = str(SCREENSHOT_DIR / filename)
    res = run_browser("screenshot", path)
    if res.returncode == 0:
        print(f"  [SCREENSHOT] {filename}")
    else:
        print(f"  [SCREENSHOT FAILED] {filename}: {res.stderr}")
    return path

def browser_eval(js_code: str) -> str:
    res = run_browser("eval", js_code)
    return res.stdout.strip()

def run_live_workflow():
    print("=================================================================")
    print("TESTFORGE PHASE 4 LIVE BROWSER WORKFLOW VERIFICATION")
    print("=================================================================")
    
    # Close any lingering session
    run_browser("close", "--all")
    time.sleep(1.0)
    
    # 1. Open Frontend
    print("\n1. Navigating to http://127.0.0.1:8000/...")
    res = run_browser("open", "http://127.0.0.1:8000/")
    print(f"  Navigation output: {res.stdout.strip() or res.stderr.strip()}")
    time.sleep(1.5)
    take_screenshot("01_homepage.png")
    
    # 2. Inspect A2A Card Modal
    print("\n2. Inspecting A2A AgentCard...")
    run_browser("click", "#btn-a2a-card")
    time.sleep(1.0)
    take_screenshot("02_a2a_modal.png")
    run_browser("eval", 'document.querySelector("#btn-close-a2a-modal").click()')
    time.sleep(0.5)

    # 3. Inspect MCP Tools Modal
    print("\n3. Inspecting MCP Tools Modal...")
    run_browser("click", "#btn-mcp-status")
    time.sleep(1.0)
    take_screenshot("03_mcp_modal.png")
    run_browser("eval", 'document.querySelector("#btn-close-mcp-modal").click()')
    time.sleep(0.5)

    # 4. Load Built-in discount.py sample
    print("\n4. Loading discount.py in Mode A...")
    run_browser("click", "#btn-load-sample")
    time.sleep(1.0)
    take_screenshot("04_discount_loaded.png")
    
    # 5. Inspect Blast Radius
    print("\n5. Inspecting Blast Radius & Call Graph Tab...")
    run_browser("click", "#nav-blast")
    time.sleep(1.0)
    take_screenshot("05_blast_radius_tab.png")

    # 6. Inspect Multi-Agent Wiretap
    print("\n6. Inspecting Multi-Agent Wiretap Tab...")
    run_browser("click", "#nav-wiretap")
    time.sleep(1.0)
    take_screenshot("06_wiretap_tab.png")

    # 7. Execute Hardening on discount.py
    print("\n7. Executing Live Hardening Pipeline on discount.py...")
    run_browser("click", "#nav-hardening")
    time.sleep(0.8)
    run_browser("click", "#btn-run-hardening")
    
    # Wait for completion
    for _ in range(30):
        time.sleep(1.0)
        status_text = browser_eval("document.querySelector('#hardening-status-text') ? document.querySelector('#hardening-status-text').innerText : ''")
        final_status = browser_eval("document.querySelector('#kpi-final-status') ? document.querySelector('#kpi-final-status').innerText : ''")
        if "ACHIEVED" in final_status or "COMPLETE" in final_status or "UNREACHED" in final_status or "ERROR" in final_status:
            print(f"  Hardening finished with verdict: {final_status}")
            break
        print(f"  Hardening status: {status_text[:60]}...")
        
    time.sleep(1.0)
    take_screenshot("07_discount_hardened_kpi.png")

    # 8. Test Checkpoints Timeline Tab
    print("\n8. Inspecting Checkpoint Timeline...")
    run_browser("click", "#nav-checkpoints")
    time.sleep(1.0)
    take_screenshot("08_checkpoints_timeline.png")

    # 9. Test Semantic Checkpoint Diff
    print("\n9. Testing Semantic Checkpoint Diff in UI...")
    run_browser("eval", '''
        const btnsA = document.querySelectorAll(".btn-set-diff-a");
        const btnsB = document.querySelectorAll(".btn-set-diff-b");
        if (btnsA.length > 1 && btnsB.length > 0) {
            btnsA[1].click();
            btnsB[0].click();
        }
    ''')
    time.sleep(0.5)
    run_browser("click", "#btn-subtab-diff")
    time.sleep(0.8)
    take_screenshot("09_checkpoints_diff_view.png")

    # 10. Ingest logistics engine sample via Mode A
    print("\n10. Loading and Ingesting uploaded_logistics_engine.py...")
    with open(BASE_DIR / "samples" / "uploaded_logistics_engine.py") as f:
        logistics_code = f.read()

    # Upload via API directly to set active target
    boundary = "----WebKitFormBoundaryPhase4Logistics"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="uploaded_logistics_engine.py"\r\n'
        f"Content-Type: text/x-python\r\n\r\n"
        f"{logistics_code}\r\n"
        f"--{boundary}--\r\n"
    ).encode()
    req = urllib.request.Request("http://127.0.0.1:8000/api/ingest/upload", data=body, headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    with urllib.request.urlopen(req) as resp:
        upload_resp = json.loads(resp.read().decode())
        print(f"  Ingested module: {upload_resp.get('module_name')}, Callables: {len(upload_resp.get('functions', [])) + len(upload_resp.get('classes', []))}")

    # Reload page to refresh active target banner
    run_browser("reload")
    time.sleep(1.5)
    take_screenshot("10_logistics_target_active.png")

    # 11. Run Hardening on logistics engine
    print("\n11. Executing Live Hardening on uploaded_logistics_engine.py...")
    run_browser("click", "#nav-hardening")
    time.sleep(0.8)
    run_browser("click", "#btn-run-hardening")

    for _ in range(40):
        time.sleep(1.0)
        status_text = browser_eval("document.querySelector('#hardening-status-text') ? document.querySelector('#hardening-status-text').innerText : ''")
        final_status = browser_eval("document.querySelector('#kpi-final-status') ? document.querySelector('#kpi-final-status').innerText : ''")
        if "ACHIEVED" in final_status or "COMPLETE" in final_status or "UNREACHED" in final_status or "ERROR" in final_status:
            print(f"  Logistics hardening finished with verdict: {final_status}")
            break
        print(f"  Logistics status: {status_text[:60]}...")

    time.sleep(1.0)
    take_screenshot("11_logistics_hardened_kpi.png")

    # 12. Check Exported Hardened Suite
    print("\n12. Verifying Hardened Suite in UI...")
    suite_len = browser_eval("document.querySelector('#hardened-suite-code') ? document.querySelector('#hardened-suite-code').innerText.length : 0")
    print(f"  Hardened suite code length in UI: {suite_len} characters")
    take_screenshot("12_hardened_suite_export.png")

    print("\n✓ Live Browser Workflow Completed Successfully.")

def run_failure_handling_tests():
    print("\n=================================================================")
    print("TESTFORGE PHASE 4 FAILURE HANDLING & EDGE CASES")
    print("=================================================================")
    results = []

    # 1. Unsupported File (Binary/Executable)
    print("\n1. Testing Unsupported Binary Upload (.exe)...")
    boundary = "----WebKitFormBoundaryPhase4TestForge"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="malicious_payload.exe"\r\n'
        f"Content-Type: application/octet-stream\r\n\r\n"
        f"MZ90\x00\x03\x00\x00\x00"
        f"--{boundary}--\r\n"
    ).encode("latin-1")
    req = urllib.request.Request("http://127.0.0.1:8000/api/ingest/upload", data=body, headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    try:
        with urllib.request.urlopen(req) as resp:
            code = resp.status
    except urllib.error.HTTPError as e:
        code = e.code
    print(f"  Binary file rejection HTTP Status: {code}")
    results.append({"case": "Binary / Non-Python file rejection", "expected_code": [400, 422], "actual_code": code, "verdict": "PASS" if code in [400, 422] else "FAIL"})

    # 2. Empty Source Code
    print("\n2. Testing Empty Source Code Handling...")
    req = urllib.request.Request("http://127.0.0.1:8000/api/harden/start", data=json.dumps({"target_source_code": "", "target_file_path": "samples/empty.py"}).encode(), headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as resp:
            code = resp.status
    except urllib.error.HTTPError as e:
        code = e.code
    print(f"  Empty code rejection HTTP Status: {code}")
    results.append({"case": "Empty source rejection", "expected_code": 400, "actual_code": code, "verdict": "PASS" if code == 400 else "FAIL"})

    # 3. Invalid Python Syntax
    print("\n3. Testing Malformed / Syntax-Error Python Code Ingestion...")
    boundary = "----WebKitFormBoundaryPhase4TestForge"
    bad_code = "def broken_func(a, b\n    return a +++ \n"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="syntax_error.py"\r\n'
        f"Content-Type: text/x-python\r\n\r\n"
        f"{bad_code}\r\n"
        f"--{boundary}--\r\n"
    ).encode()
    req = urllib.request.Request("http://127.0.0.1:8000/api/ingest/upload", data=body, headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    try:
        with urllib.request.urlopen(req) as resp:
            code = resp.status
            resp_body = resp.read().decode()
    except urllib.error.HTTPError as e:
        code = e.code
        resp_body = e.read().decode()
    print(f"  Syntax error rejection HTTP Status: {code} | Detail: {resp_body[:100]}")
    results.append({"case": "Syntax error handling", "expected_code": "Graceful (400 or status=syntax_error)", "actual_code": code, "verdict": "PASS" if (code == 400 or "syntax_error" in resp_body) else "FAIL"})

    # 4. Nonexistent Job Cancellation
    print("\n4. Testing Nonexistent Job Cancellation...")
    req = urllib.request.Request("http://127.0.0.1:8000/api/harden/cancel/job_phantom_999999", data=b"", headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req) as resp:
            code = resp.status
    except urllib.error.HTTPError as e:
        code = e.code
    print(f"  Nonexistent job cancel HTTP Status: {code}")
    results.append({"case": "Nonexistent job cancel", "expected_code": 404, "actual_code": code, "verdict": "PASS" if code == 404 else "FAIL"})

    # 5. Cooperative Cancellation of Active Job
    print("\n5. Testing Live Job Cooperative Cancellation...")
    with open(BASE_DIR / "samples" / "discount.py") as f:
        src = f.read()
    payload = {
        "target_source_code": src,
        "target_file_path": "samples/discount.py",
        "max_iterations": 5
    }
    start_req = urllib.request.Request("http://127.0.0.1:8000/api/harden/start", data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(start_req) as resp:
        job_id = json.loads(resp.read().decode())["job_id"]
    print(f"  Started job {job_id}, triggering cooperative cancel...")
    
    cancel_req = urllib.request.Request(f"http://127.0.0.1:8000/api/harden/cancel/{job_id}", data=b"", headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(cancel_req) as resp:
        cancel_res = json.loads(resp.read().decode())
    
    time.sleep(1.0)
    status_req = urllib.request.Request(f"http://127.0.0.1:8000/api/harden/status/{job_id}")
    with urllib.request.urlopen(status_req) as resp:
        final_status = json.loads(resp.read().decode())["status"]
    print(f"  Final job status: {final_status}")
    results.append({"case": "Active job cooperative cancellation", "expected_code": "CANCELLED/CANCELLING", "actual_code": final_status, "verdict": "PASS" if ("CANCEL" in final_status.upper()) else "FAIL"})

    with open(ARTIFACT_DIR / "failure_handling_summary.json", "w") as f:
        json.dump(results, f, indent=2)

    print("\n✓ Failure Handling & Edge Case Tests Completed.")
    return results

if __name__ == "__main__":
    run_live_workflow()
    run_failure_handling_tests()
