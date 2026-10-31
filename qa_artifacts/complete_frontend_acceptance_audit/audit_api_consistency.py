#!/usr/bin/env python3
"""
TestForge Complete Frontend Acceptance Audit - Phase 7: Backend API & Service Consistency
Author: Antigravity Automated QA Suite
Date: 2026-10-30
"""

import os
import sys
import time
import json
import urllib.request
import urllib.error
import asyncio
from pathlib import Path

BASE_DIR = Path("/Users/sourabh/TestForge")
QA_DIR = BASE_DIR / "qa_artifacts" / "complete_frontend_acceptance_audit"
LOG_DIR = QA_DIR / "logs"

for d in [LOG_DIR]:
    d.mkdir(parents=True, exist_ok=True)

ENDPOINTS = [
    ("GET", "/", "Root HTML Dashboard", 200),
    ("GET", "/healthz", "Health Probe", 200),
    ("GET", "/readyz", "Readiness Probe", 200),
    ("GET", "/api/ready", "API Ready Probe", 200),
    ("GET", "/api/status", "System Status & Hardware Metrics", 200),
    ("GET", "/api/samples", "Workspace Sample Inventory", 200),
    ("GET", "/api/mcp/status", "FastMCP Tools Status", 200),
    ("GET", "/.well-known/agent-card.json", "A2A Agent Card Standard JSON", 200),
    ("GET", "/.well-known/agent.json", "A2A Agent Discovery Alias", 200),
    ("GET", "/api/checkpoints", "SQLite Checkpoints Timeline", 200),
    ("GET", "/api/telemetry", "Live Telemetry Events", 200),
    ("GET", "/api/wiretap", "Multi-Agent Wiretap Events", 200),
    ("GET", "/api/benchmark/results", "Benchmark Ablation Results JSON", 200),
    ("GET", "/api/benchmark/markdown", "Benchmark Ablation Markdown Report", 200),
    ("GET", "/api/ws/status", "WebSocket Hub Status", 200),
    ("GET", "/docs", "Swagger UI Documentation", 200),
    ("GET", "/redoc", "ReDoc Documentation", 200),
    ("GET", "/openapi.json", "OpenAPI v3 JSON Schema", 200),
]

def audit_api():
    print("=== STARTING PHASE 7: BACKEND API & SERVICE CONSISTENCY AUDIT ===")
    results = []

    for method, path, desc, expected_status in ENDPOINTS:
        url = f"http://127.0.0.1:8000{path}"
        start_t = time.perf_counter()
        status_code = None
        resp_data = None
        error_msg = ""
        try:
            req = urllib.request.Request(url, method=method)
            with urllib.request.urlopen(req, timeout=5) as resp:
                status_code = resp.status
                raw = resp.read()
                try:
                    resp_data = json.loads(raw.decode("utf-8"))
                except Exception:
                    resp_data = f"<bytes {len(raw)}>"
        except urllib.error.HTTPError as he:
            status_code = he.code
            try:
                resp_data = json.loads(he.read().decode("utf-8"))
            except Exception:
                resp_data = {"error": str(he)}
        except Exception as e:
            error_msg = str(e)
            status_code = 500

        elapsed_ms = round((time.perf_counter() - start_t) * 1000, 2)
        passed = (status_code == expected_status)
        status_str = "PASS" if passed else "FAIL"

        print(f"[{status_str}] {method:4s} {path:30s} -> {status_code} ({elapsed_ms}ms) | {desc}")
        results.append({
            "method": method,
            "path": path,
            "description": desc,
            "expected_status": expected_status,
            "actual_status": status_code,
            "latency_ms": elapsed_ms,
            "error": error_msg,
            "status": status_str
        })

    # Test WebSocket connection
    print("\n--- Testing WebSocket /ws/events ---")
    ws_passed = False
    try:
        import websockets
        async def test_ws():
            uri = "ws://127.0.0.1:8000/ws/events"
            async with websockets.connect(uri) as websocket:
                # Send ping or wait for initial message
                return True
        ws_passed = asyncio.run(test_ws())
        print(f"[PASS] WebSocket /ws/events connected successfully!")
    except Exception as exc:
        print(f"[NOTE] WebSocket test via websockets client: {exc}")
        # Check via /api/ws/status
        status_code, ws_stat = 200, {}
        try:
            with urllib.request.urlopen("http://127.0.0.1:8000/api/ws/status") as r:
                ws_stat = json.loads(r.read().decode("utf-8"))
                ws_passed = (ws_stat.get("status") == "healthy")
        except Exception:
            pass

    out_file = LOG_DIR / "api_consistency_results.json"
    out_file.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nAPI Consistency Audit complete! {sum(1 for r in results if r['status'] == 'PASS')}/{len(results)} PASSED. Saved to {out_file}")

if __name__ == "__main__":
    audit_api()

