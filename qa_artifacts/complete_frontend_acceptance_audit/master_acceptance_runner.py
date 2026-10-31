#!/usr/bin/env python3
"""
TestForge Master Complete Frontend Acceptance Audit Runner
Author: Antigravity Automated QA Suite
Date: 2026-10-30
"""

import os
import sys
import time
import json
import shutil
import urllib.request
import urllib.error
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional

BASE_DIR = Path("/Users/sourabh/TestForge")
QA_DIR = BASE_DIR / "qa_artifacts" / "complete_frontend_acceptance_audit"
SCREENSHOT_DIR = QA_DIR / "screenshots"
RESPONSIVE_DIR = SCREENSHOT_DIR / "responsive"
LOG_DIR = QA_DIR / "logs"
EDGE_DIR = QA_DIR / "edge_cases"
RANDOM_TARGET_DIR = QA_DIR / "random_python_target"

for d in [SCREENSHOT_DIR, RESPONSIVE_DIR, LOG_DIR, EDGE_DIR, RANDOM_TARGET_DIR]:
    d.mkdir(parents=True, exist_ok=True)

ENV = os.environ.copy()
ENV["PATH"] = "/Users/sourabh/.nvm/versions/node/v24.15.0/bin:" + ENV.get("PATH", "")

def run_ab(*args, timeout=30) -> subprocess.CompletedProcess:
    cmd = ["agent-browser"] + list(args)
    try:
        res = subprocess.run(cmd, capture_output=True, text=True, env=ENV, timeout=timeout)
        return res
    except subprocess.TimeoutExpired:
        print(f"[TIMEOUT] Command timed out: {' '.join(cmd)}")
        return subprocess.CompletedProcess(cmd, returncode=-1, stdout="", stderr="Timeout expired")

def take_screenshot(filename: str, full_page: bool = True) -> str:
    path = str(SCREENSHOT_DIR / filename)
    args = ["screenshot", path]
    if full_page:
        args.append("--full")
    run_ab(*args)
    return path

def take_responsive_screenshot(filename: str, full_page: bool = True) -> str:
    path = str(RESPONSIVE_DIR / filename)
    args = ["screenshot", path]
    if full_page:
        args.append("--full")
    run_ab(*args)
    return path

audit_results = {
    "metadata": {
        "timestamp": time.time(),
        "date": "2026-10-30",
        "target_fastapi": "http://127.0.0.1:8000",
        "target_streamlit": "http://127.0.0.1:8501",
    },
    "controls": [],
    "interactions": [],
    "responsive": [],
    "random_target_test": {},
    "edge_cases": [],
    "workflows": {},
    "api_consistency": [],
    "summary": {
        "total_controls_tested": 0,
        "controls_passed": 0,
        "controls_defects": 0,
        "workflows_passed": 0,
        "edge_cases_passed": 0
    }
}

def record_interaction(control_id, name, selector, control_type, initial_state, action, result_state, backend_req, console_err, status, screenshot):
    item = {
        "control_id": control_id,
        "name": name,
        "selector": selector,
        "control_type": control_type,
        "initial_state": initial_state,
        "action": action,
        "result_state": result_state,
        "backend_request": backend_req,
        "console_errors": console_err,
        "status": status,
        "screenshot": screenshot
    }
    audit_results["interactions"].append(item)
    audit_results["summary"]["total_controls_tested"] += 1
    if status == "PASS":
        audit_results["summary"]["controls_passed"] += 1
    else:
        audit_results["summary"]["controls_defects"] += 1
    print(f"[{status}] {control_id} | {name} ({selector}) -> {result_state[:50]}")

print("Master acceptance runner initialized.")

