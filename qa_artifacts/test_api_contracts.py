"""
test_api_contracts.py - Comprehensive API contract and negative testing against http://127.0.0.1:8000
"""

import os
import json
import time
import requests

BASE_URL = "http://127.0.0.1:8000"
results = []

def test_endpoint(name, method, endpoint, expected_status, payload=None, files=None, params=None):
    start = time.time()
    url = f"{BASE_URL}{endpoint}"
    status = "FAIL"
    resp_data = None
    err_msg = ""
    status_code = None
    
    try:
        if method == "GET":
            r = requests.get(url, params=params, timeout=10)
        elif method == "POST":
            if files:
                r = requests.post(url, files=files, data=payload, timeout=15)
            elif isinstance(payload, str):
                r = requests.post(url, data=payload, headers={"Content-Type": "application/json"}, timeout=60)
            else:
                r = requests.post(url, json=payload, timeout=60)
        status_code = r.status_code
        elapsed = round((time.time() - start) * 1000, 2)
        content_type = r.headers.get("Content-Type", "")
        
        if status_code == expected_status:
            status = "PASS"
        else:
            status = "FAIL"
            err_msg = f"Expected HTTP {expected_status}, got {status_code}"
            
        try:
            resp_data = r.json()
        except Exception:
            resp_data = r.text[:200]
            
    except Exception as e:
        elapsed = round((time.time() - start) * 1000, 2)
        status = "FAIL"
        err_msg = str(e)
        content_type = "N/A"

    record = {
        "name": name,
        "method": method,
        "endpoint": endpoint,
        "expected_status": expected_status,
        "actual_status": status_code,
        "elapsed_ms": elapsed,
        "content_type": content_type,
        "status": status,
        "error": err_msg,
        "sample_response": resp_data if isinstance(resp_data, (dict, list)) else str(resp_data)[:150]
    }
    results.append(record)
    print(f"[{status}] {method:4} {endpoint:35} -> HTTP {status_code} ({elapsed}ms)")
    return record

# 1. Core Health, Discovery & Documentation
test_endpoint("Health Check (Liveness)", "GET", "/healthz", 200)
test_endpoint("Readiness Check (Subsystems)", "GET", "/readyz", 200)
test_endpoint("A2A Agent Card (well-known)", "GET", "/.well-known/agent-card.json", 200)
test_endpoint("A2A Agent Card (legacy alias)", "GET", "/.well-known/agent.json", 200)
test_endpoint("Swagger UI Documentation", "GET", "/docs", 200)
test_endpoint("OpenAPI Schema", "GET", "/openapi.json", 200)
test_endpoint("Root Web Application", "GET", "/", 200)

# 2. System Status & Configuration
test_endpoint("System Status & Hardware Info", "GET", "/api/status", 200)
test_endpoint("Update API Keys (Valid Payload)", "POST", "/api/config/keys", 200, payload={"gemini_api_key": None, "openrouter_api_key": None})
test_endpoint("Update API Keys (Negative: Invalid JSON)", "POST", "/api/config/keys", 422, payload="invalid_string_not_json")

# 3. Ingestion & Samples
test_endpoint("List Workspace Samples", "GET", "/api/samples", 200)
test_endpoint("Ingest Sample (Valid: banking.py)", "POST", "/api/ingest/sample", 200, payload={"filename": "banking.py"})
test_endpoint("Ingest Sample (Negative: Nonexistent File)", "POST", "/api/ingest/sample", 404, payload={"filename": "non_existent_file.py"})
test_endpoint("Ingest Sample (Negative: Missing filename field)", "POST", "/api/ingest/sample", 422, payload={})
test_endpoint("Ingest Sample (Security: Traversal attempt)", "POST", "/api/ingest/sample", 404, payload={"filename": "../../etc/passwd"})

# 4. Module Synthesis
test_endpoint("Synthesize Module (Valid)", "POST", "/api/ingest/synthesize", 200, payload={"prompt": "Create a simple math multiplier function with input type checks."})
test_endpoint("Synthesize Module (Negative: Missing prompt)", "POST", "/api/ingest/synthesize", 422, payload={})

# 5. GitHub Direct Import
test_endpoint("GitHub Ingestion (Valid Public Raw URL)", "POST", "/api/ingest/github", 200, payload={"url": "https://raw.githubusercontent.com/psf/requests/main/src/requests/status_codes.py"})
test_endpoint("GitHub Ingestion (Negative: Invalid Scheme)", "POST", "/api/ingest/github", 422, payload={"url": "ftp://malicious.com/file.py"})
test_endpoint("GitHub Ingestion (Negative: Non-Python File)", "POST", "/api/ingest/github", 422, payload={"url": "https://raw.githubusercontent.com/psf/requests/main/README.md"})
test_endpoint("GitHub Ingestion (Negative: Missing URL field)", "POST", "/api/ingest/github", 422, payload={})

# 6. Static AST Analysis
sample_code = "def deposit(account: dict, amount: float) -> float:\n    account['balance'] += amount\n    return account['balance']\n"
test_endpoint("Blast Radius Analysis (Valid)", "POST", "/api/analysis/blast-radius", 200, payload={"source_code": sample_code, "target_function": "deposit"})
test_endpoint("Blast Radius Analysis (Negative: Missing source_code)", "POST", "/api/analysis/blast-radius", 422, payload={})
test_endpoint("Git Diff-Aware Analysis (Valid)", "POST", "/api/analysis/git-diff", 200, payload={"target_file_path": "samples/banking.py"})
test_endpoint("Git Diff-Aware Analysis (Negative: Missing target_file_path)", "POST", "/api/analysis/git-diff", 422, payload={})

# 7. Hardening Pipeline
test_endpoint("Synchronous Hardening Run", "POST", "/api/harden/run", 200, payload={"target_file_path": "samples/banking.py", "target_source_code": sample_code, "max_iterations": 1, "target_mutation_score": 75.0})
test_endpoint("Start Async Hardening Job", "POST", "/api/harden/start", 200, payload={"target_file_path": "samples/banking.py", "target_source_code": sample_code, "max_iterations": 1, "target_mutation_score": 75.0})
test_endpoint("Hardening Run (Negative: Missing required fields)", "POST", "/api/harden/run", 422, payload={})
test_endpoint("Hardened Suite Retrieval", "GET", "/api/hardened-code", 200)

# 8. Observability, Wiretap & Telemetry
test_endpoint("Telemetry Trace Events", "GET", "/api/telemetry", 200)
test_endpoint("Wiretap Handoff Events", "GET", "/api/wiretap", 200)

# 9. Benchmarking
test_endpoint("Benchmark Results Retrieval", "GET", "/api/benchmark/results", 200)
test_endpoint("Benchmark Markdown Export", "GET", "/api/benchmark/markdown", 200)
test_endpoint("Benchmark Async Job Start (Valid)", "POST", "/api/benchmark/start", 200, payload={"target_file_path": "samples/banking.py", "scenarios": ["baseline"], "repetitions": 1})
test_endpoint("Benchmark Job Status Check (Nonexistent)", "GET", "/api/benchmark/job/non_existent_job_123", 404)

# Save API audit results
os.makedirs("qa_artifacts/browser_audit", exist_ok=True)
with open("qa_artifacts/browser_audit/api_contract_results.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)

passed = sum(1 for r in results if r["status"] == "PASS")
failed = sum(1 for r in results if r["status"] == "FAIL")
print(f"\n[API Contract Summary] Total: {len(results)}, Passed: {passed}, Failed: {failed}")
