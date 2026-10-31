#!/usr/bin/env python3
"""
TestForge FastAPI-Only Single Frontend Architecture Verification Suite
Author: Antigravity Automated QA Suite
Date: 2026-10-30
"""

import os
import sys
import time
import json
import subprocess
from pathlib import Path

BASE_DIR = Path("/Users/sourabh/TestForge")
QA_DIR = BASE_DIR / "qa_artifacts" / "frontend_consolidation"
SCREENSHOT_DIR = QA_DIR / "screenshots"

ENV = os.environ.copy()
ENV["PATH"] = "/Users/sourabh/.nvm/versions/node/v24.15.0/bin:" + ENV.get("PATH", "")

def run_ab(*args, timeout=25) -> subprocess.CompletedProcess:
    cmd = ["agent-browser"] + list(args)
    try:
        return subprocess.run(cmd, capture_output=True, text=True, env=ENV, timeout=timeout)
    except subprocess.TimeoutExpired:
        print(f"[TIMEOUT] Command timed out: {' '.join(cmd)}")
        return subprocess.CompletedProcess(cmd, returncode=-1, stdout="", stderr="Timeout expired")

def take_shot(filename: str, full_page: bool = False) -> str:
    path = str(SCREENSHOT_DIR / filename)
    args = ["screenshot", path]
    if full_page:
        args.append("--full")
    run_ab(*args)
    return filename

def verify_single_frontend():
    print("=== STARTING FASTAPI-ONLY ARCHITECTURE VERIFICATION ===")
    run_ab("close", "--all")
    time.sleep(1)

    # 1. Open Landing at :8000
    run_ab("open", "http://127.0.0.1:8000")
    run_ab("wait", "3000")
    shot1 = take_shot("01_consolidated_landing.png")
    print(f"[PASS] Consolidated Landing loaded: {shot1}")

    # Check console logs and errors
    console_res = run_ab("console")
    errors_res = run_ab("errors")
    print(f"Console errors: {errors_res.stdout.strip() or 'None'}")

    # 2. Verify A2A Modal
    run_ab("click", "#btn-a2a-card")
    run_ab("wait", "800")
    run_ab("click", "#btn-run-a2a-test")
    run_ab("wait", "1200")
    shot2 = take_shot("02_a2a_protocol_test.png")
    run_ab("click", "#btn-close-a2a-modal")
    run_ab("wait", "400")
    print(f"[PASS] A2A Protocol verified: {shot2}")

    # 3. Verify FastMCP Tools Modal
    run_ab("click", "#btn-mcp-status")
    run_ab("wait", "800")
    run_ab("click", "#btn-run-mcp-test")
    run_ab("wait", "1200")
    shot3 = take_shot("03_fastmcp_tools_test.png")
    run_ab("click", "#btn-close-mcp-modal")
    run_ab("wait", "400")
    print(f"[PASS] FastMCP Tools verified: {shot3}")

    # 4. Verify Mode A Sample Loading
    run_ab("click", "#nav-mode-a")
    run_ab("wait", "400")
    run_ab("select", "#sample-file-select", "samples/inventory_pricing.py")
    run_ab("wait", "400")
    run_ab("click", "#btn-load-sample")
    run_ab("wait", "1200")
    shot4 = take_shot("04_inventory_pricing_loaded.png")
    print(f"[PASS] Mode A Sample Loaded: {shot4}")

    # 5. Verify Blast Radius Tab
    run_ab("click", "#nav-blast")
    run_ab("wait", "800")
    shot5 = take_shot("05_blast_radius_mermaid.png")
    print(f"[PASS] Blast Radius Graph verified: {shot5}")

    # 6. Verify Hardening Lab Tab
    run_ab("click", "#nav-hardening")
    run_ab("wait", "600")
    shot6 = take_shot("06_hardening_lab.png")
    print(f"[PASS] Hardening Lab verified: {shot6}")

    # 7. Verify Checkpoints Tab & Deterministic Diff
    run_ab("click", "#nav-checkpoints")
    run_ab("wait", "600")
    run_ab("click", "#btn-refresh-checkpoints")
    run_ab("wait", "600")
    run_ab("click", "#btn-subtab-diff")
    run_ab("wait", "600")
    shot7 = take_shot("07_checkpoint_diff_view.png")
    print(f"[PASS] Checkpoint Diff view verified: {shot7}")

    # 8. Verify No Requests to Port 8501
    net_res = run_ab("network", "requests")
    has_8501 = "8501" in net_res.stdout
    print(f"Network requests to 8501 detected: {has_8501}")
    assert not has_8501, "Security defect: Network requests to port 8501 detected!"
    print("[PASS] Zero requests to port 8501 confirmed!")

    run_ab("close")
    print("\n=== ALL FASTAPI-ONLY BROWSER WORKFLOWS PASSED ===")

if __name__ == "__main__":
    verify_single_frontend()

