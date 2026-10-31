#!/usr/bin/env python3
"""
TestForge Complete Frontend Acceptance Audit - Phase 5: 10 Edge-Case Python Inputs
Author: Antigravity Automated QA Suite
Date: 2026-10-30
"""

import os
import sys
import time
import json
import subprocess
import urllib.request
import urllib.error
from pathlib import Path

BASE_DIR = Path("/Users/sourabh/TestForge")
QA_DIR = BASE_DIR / "qa_artifacts" / "complete_frontend_acceptance_audit"
EDGE_DIR = QA_DIR / "edge_cases"
LOG_DIR = QA_DIR / "logs"

for d in [LOG_DIR]:
    d.mkdir(parents=True, exist_ok=True)

EDGE_FILES = [
    ("EC-01", "01_empty.py", "Empty file (0 bytes)", False),
    ("EC-02", "02_comments_only.py", "File with only comments and docstrings", False),
    ("EC-03", "03_single_simple_function.py", "Single simple function (square)", False),
    ("EC-04", "04_multiple_functions.py", "Multiple independent arithmetic functions", False),
    ("EC-05", "05_class_methods.py", "Class with methods, properties, inheritance", False),
    ("EC-06", "06_complex_typing.py", "Complex type hints (Dict, List, Union, Callable)", False),
    ("EC-07", "07_nested_closures.py", "Deeply nested functions & closures", False),
    ("EC-08", "08_syntax_error.py", "Deliberate syntax error (unclosed parens/colons)", True),
    ("EC-09", "09_exception_raising.py", "Functions raising specific domain exceptions", False),
    ("EC-10", "10_heavy_branching.py", "High cyclomatic complexity / heavy branching", False)
]

def check_server_health() -> bool:
    try:
        with urllib.request.urlopen("http://127.0.0.1:8000/healthz", timeout=3) as resp:
            return resp.status == 200
    except Exception:
        return False

def audit_edge_cases():
    print("=== STARTING PHASE 5: 10 EDGE-CASE PYTHON INPUTS AUDIT ===")
    results = []

    for ec_id, filename, desc, expect_error in EDGE_FILES:
        filepath = EDGE_DIR / filename
        source_code = filepath.read_text(encoding="utf-8")
        print(f"\n--- Testing {ec_id}: {filename} ({desc}) ---")

        # Ingest using multipart curl
        upload_cmd = ["curl", "-s", "-w", "\n%{http_code}", "-F", f"file=@{filepath}", "http://127.0.0.1:8000/api/ingest/upload"]
        res = subprocess.run(upload_cmd, capture_output=True, text=True)
        lines = res.stdout.strip().split("\n")
        status_code = int(lines[-1]) if lines[-1].isdigit() else 500
        raw_body = "\n".join(lines[:-1])
        try:
            resp_json = json.loads(raw_body)
        except Exception:
            resp_json = {"raw": raw_body}

        # Check server health after test
        is_healthy = check_server_health()

        # Evaluate correctness
        passed = False
        outcome_detail = ""
        if expect_error:
            if status_code in (400, 422) or resp_json.get("status") == "syntax_error" or resp_json.get("has_syntax_error") or "error" in resp_json:
                passed = True
                outcome_detail = f"Correctly caught syntax error with HTTP {status_code}: {resp_json.get('error') or resp_json.get('detail')}"
            else:
                outcome_detail = f"Expected error but got HTTP {status_code}"
        else:
            if status_code == 200 and resp_json.get("status") in ("success", "loaded", "ok"):
                passed = True
                funcs = resp_json.get("functions", [])
                classes = resp_json.get("classes", [])
                outcome_detail = f"Ingested cleanly (HTTP 200). Extracted {len(funcs)} functions, {len(classes)} classes."
            elif filename == "01_empty.py" and (status_code == 200 or status_code == 400):
                # Empty file may cleanly return 0 functions or 400 bad request
                passed = True
                outcome_detail = f"Safely handled empty file with HTTP {status_code} without server crash."
            elif filename == "02_comments_only.py" and status_code == 200:
                passed = True
                outcome_detail = f"Safely handled comments-only file with HTTP 200 (0 executable functions)."
            else:
                outcome_detail = f"Unexpected response: HTTP {status_code}, response: {resp_json}"

        status_str = "PASS" if passed and is_healthy else "FAIL"
        print(f"[{status_str}] {ec_id} | HTTP {status_code} | Server Healthy: {is_healthy} -> {outcome_detail}")

        results.append({
            "id": ec_id,
            "filename": filename,
            "description": desc,
            "expect_error": expect_error,
            "http_status": status_code,
            "response": resp_json,
            "server_healthy": is_healthy,
            "outcome_detail": outcome_detail,
            "status": status_str
        })

    out_file = LOG_DIR / "edge_case_results.json"
    out_file.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nPhase 5 Edge Case Audit complete. {sum(1 for r in results if r['status'] == 'PASS')}/10 PASSED. Saved to {out_file}")

if __name__ == "__main__":
    audit_edge_cases()
