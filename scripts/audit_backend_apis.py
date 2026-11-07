"""
Automated Backend API Contract and Reliability Audit Script for TestForge.
Tests all registered FastAPI endpoints with valid and invalid inputs.
"""

import json
import requests

BASE_URL = "http://127.0.0.1:8000"

def audit_apis():
    results = []

    tests = [
        # Health & System
        ("GET", "/healthz", None, 200),
        ("GET", "/readyz", None, 200),
        ("GET", "/api/ready", None, 200),
        ("GET", "/api/status", None, 200),
        ("GET", "/api/ws/status", None, 200),
        # MCP
        ("GET", "/api/mcp/status", None, 200),
        ("POST", "/api/mcp/test", {"tool_name": "list_directory", "path": "samples"}, 200),
        ("POST", "/api/mcp/test", {"tool_name": "invalid_tool", "path": "samples"}, 422),
        # A2A Agent Cards
        ("GET", "/.well-known/agent.json", None, 200),
        ("GET", "/.well-known/agent-card.json", None, 200),
        ("POST", "/api/a2a/test", {"action": "ping"}, 200),
        # Ingestion & Samples
        ("GET", "/api/samples", None, 200),
        ("POST", "/api/ingest/sample", {"filename": "discount.py"}, 200),
        ("POST", "/api/ingest/sample", {"filename": "non_existent.py"}, 404),
        # Blast Radius Analysis
        ("POST", "/api/analysis/blast-radius", {
            "source_code": "def foo(): pass\ndef bar(): foo()\n",
            "file_path": "test.py",
            "target_function": "foo"
        }, 200),
        # Hardening
        ("GET", "/api/hardened-code", None, 200),
        ("GET", "/api/harden/status/invalid_job_999", None, 404),
        ("POST", "/api/harden/cancel/invalid_job_999", None, 404),
        # Checkpoints
        ("GET", "/api/checkpoints", None, 200),
        ("GET", "/api/checkpoints/invalid_chk_999", None, 404),
        # Observability & Wiretap
        ("GET", "/api/telemetry", None, 200),
        ("GET", "/api/wiretap", None, 200),
        # Benchmark
        ("GET", "/api/benchmark/results", None, 200),
        ("GET", "/api/benchmark/markdown", None, 200),
    ]

    for method, path, body, expected_status in tests:
        url = f"{BASE_URL}{path}"
        try:
            if method == "GET":
                r = requests.get(url, timeout=5)
            elif method == "POST":
                r = requests.post(url, json=body, timeout=5)
            
            passed = (r.status_code == expected_status)
            entry = {
                "method": method,
                "path": path,
                "expected_status": expected_status,
                "actual_status": r.status_code,
                "passed": passed,
                "response_preview": r.text[:120] if r.text else ""
            }
            results.append(entry)
            status_symbol = "✔" if passed else "❌"
            print(f"{status_symbol} {method} {path} -> {r.status_code} (Expected {expected_status})")
        except Exception as exc:
            results.append({
                "method": method,
                "path": path,
                "expected_status": expected_status,
                "actual_status": "EXCEPTION",
                "passed": False,
                "error": str(exc)
            })
            print(f"❌ {method} {path} -> EXCEPTION: {exc}")

    with open("qa_artifacts/final_ui_audit/api_audit_results.json", "w") as f:
        json.dump(results, f, indent=2)

    total = len(results)
    passed_count = sum(1 for r in results if r["passed"])
    print(f"\nAPI Audit: {passed_count}/{total} endpoints passed contracts.")

if __name__ == "__main__":
    audit_apis()
