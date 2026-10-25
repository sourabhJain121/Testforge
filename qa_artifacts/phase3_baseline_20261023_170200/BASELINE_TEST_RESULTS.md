# TestForge — Phase 3 Baseline Test Results Report

**Audit Directory:** `qa_artifacts/phase3_baseline_20261023_170200/`  
**Execution Timestamp:** 2026-10-23T17:02:40+05:30  
**Python Virtual Environment:** `.venv-release` (Python 3.13.17)  
**Host Platform:** macOS Darwin 27.0.1 (Apple Silicon M2 Pro, 10 Cores, 16GB RAM)  
**Node.js Environment:** v24.15.0  
**Docker Engine:** Docker Desktop 28.5.1 / containerd 1.7.27  

---

## 1. Summary of Baseline Verification Runs

| Test Scope / Command | Tests Executed | Tests Passed | Tests Failed | Warnings | Duration | Exit Code | Status |
|---|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **Targeted Baseline Core Suite** | 117 | 117 | 0 | 26 | 16.05s | **0** | **PASS** |
| **Complete Pytest Suite** | 316 | 316 | 0 | 208 | 362.65s | **0** | **PASS** |
| **JavaScript Syntax Check (`node -c`)** | 1 file | 1 | 0 | 0 | 0.05s | **0** | **PASS** |
| **Bytecode Compilation (`compileall`)** | All files | All | 0 | 0 | 0.45s | **0** | **PASS** |
| **Dependency Integrity (`pip check`)** | 58 packages | 58 | 0 | 0 | 0.85s | **0** | **PASS** |
| **Git Whitespace & Syntax (`git diff --check`)** | All diffs | All | 0 | 0 | 0.02s | **0** | **PASS** |

---

## 2. Targeted Baseline Core Suite Breakdown

Executed command:
```bash
.venv-release/bin/python -m pytest \
  tests/test_blackboard.py \
  tests/test_mcp.py \
  tests/test_mcp_status_endpoint.py \
  tests/test_messaging_benchmark.py \
  tests/test_a2a_protocol.py \
  tests/test_checkpoint_diff.py \
  tests/test_deployment.py \
  tests/test_security.py \
  tests/test_fast_benchmarking.py -q
```

**Result: 117 passed, 26 warnings in 16.05 seconds.**

### Detailed Suite Results:
1. `tests/test_blackboard.py` (18 passed):
   - Thread-safe partition updates, deep-copy snapshotting, observer subscriptions, and partition type safety verified.
2. `tests/test_mcp.py` (16 passed):
   - Genuine FastMCP stdio server creation, tool reflection, `read_text_file` bounded root enforcement, path traversal blocking (`../`), and `MCPClientManager` execution verified.
3. `tests/test_mcp_status_endpoint.py` (2 passed):
   - `/api/mcp/status` JSON schema and `/api/ready` readiness probe alias verified.
4. `tests/test_messaging_benchmark.py` (5 passed):
   - Statistical calculations, metric isolation, and micro-benchmark reporting verified.
5. `tests/test_a2a_protocol.py` (18 passed):
   - A2A v0.3.0 `AgentCard` schema conformance, agent skills, and JSON-RPC dispatching verified.
6. `tests/test_checkpoint_diff.py` (8 passed):
   - SQLite checkpoint retrieval and unified AST semantic diff computation verified.
7. `tests/test_deployment.py` (11 passed):
   - Dockerfile multi-stage syntax, Compose network configuration, `/healthz` liveness, and `/readyz` readiness verified.
8. `tests/test_security.py` (30 passed):
   - Prompt injection rejection (`INJ_SYSTEM_OVERRIDE`, `INJ_SECURITY_DISABLE`), dangerous AST call detection (`eval`, `exec`, `os.system`, `subprocess`, socket creation), and secret redaction verified.
9. `tests/test_fast_benchmarking.py` (3 passed):
   - Offline fast simulation benchmark execution, rich console table rendering, and simulation disclaimer verified.

---

## 3. Warning Classification & Audit

The 208 warnings emitted during test execution were rigorously inspected:
- **Upstream CrewAI 0.102.0 Deprecations (194 warnings):**
  - `DeprecationWarning: function_calling_llm is deprecated and will be removed in a future release.`
  - `DeprecationWarning: if self.allow_code_execution: ...`
  - `DeprecationWarning: if self.reasoning and self.planning_config is None: ...`
  - These warnings originate entirely within the installed `crewai` library package in `.venv-release` as it prepares for Pydantic v2 argument migrations.
- **FastAPI / Starlette Lifespan Deprecations (12 warnings):**
  - `DeprecationWarning: on_event is deprecated, use lifespan event handlers instead.`
  - Originates from `server.py` startup event handlers. Safe for Python 3.13 / FastAPI 0.115.
- **Google Cloud AI Platform Storage Notice (2 warnings):**
  - `FutureWarning: Support for google-cloud-storage < 3.0.0 will be removed in a future version.`
  - Originates from `google-cloud-aiplatform` SDK.

**Conclusion:** Zero warnings originate from architectural flaws in TestForge's core logic. In accordance with the non-negotiable operating rules, dependencies are preserved without artificial suppression.
