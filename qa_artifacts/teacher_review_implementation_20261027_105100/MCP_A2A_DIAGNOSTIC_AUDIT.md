# Audit Report: In-Browser FastMCP & A2A Diagnostic Testing (Improvements C & D)

**Audit Target:** Real interactive FastMCP and Agent2Agent diagnostic test runners in modals.  
**Repository:** `/Users/sourabh/TestForge`  
**Files Audited & Modified:**
- [`server.py`](file:///Users/sourabh/TestForge/server.py#L980-L1130)
- [`frontend/index.html`](file:///Users/sourabh/TestForge/frontend/index.html)
- [`frontend/app.js`](file:///Users/sourabh/TestForge/frontend/app.js)
- [`tests/test_teacher_review_improvements.py`](file:///Users/sourabh/TestForge/tests/test_teacher_review_improvements.py)

---

## 1. Problem Statement

Previously, both the **Model Context Protocol (FastMCP)** modal and the **Agent2Agent (A2A)** modal only fetched static metadata (`/api/mcp/status` and `/.well-known/agent-card.json`). Users could not verify:
- Whether the FastMCP server actually executes tools over stdio JSON-RPC 2.0.
- Whether tool responses return valid file inspection data with timing.
- Whether A2A AgentCard discovery complies with official schemas and protocol standards.
- Whether security boundaries prevent directory traversal, sensitive credential exposure, and SSRF attacks.

---

## 2. Technical Implementation & Security Controls

### A. FastMCP Diagnostic Execution (`POST /api/mcp/test`)
A new endpoint was added to `server.py` with strict Pydantic v2 input validation:
```python
class MCPTestRequest(BaseModel):
    tool_name: Literal["list_directory", "get_file_info"]
    path: str = "samples"
```

#### Security Guardrails:
1. **Strict Operation Whitelisting**: Only read-only operations (`list_directory`, `get_file_info`) are permitted. Modifying or executing tools are disallowed at schema level (HTTP 422).
2. **Path Traversal Defense**: The endpoint strictly checks:
   ```python
   if ".." in req.path or req.path.startswith("/") or "\\" in req.path:
       raise HTTPException(status_code=400, detail="Security Violation: Directory traversal or absolute paths are strictly forbidden.")
   ```
3. **Sensitive Credential Isolation**: File names containing `.env`, `.git`, `.key`, `id_rsa`, or `credentials` are blocked:
   ```python
   if any(f in req.path.lower() for f in [".env", ".git", ".key", "id_rsa", "credentials"]):
       raise HTTPException(status_code=400, detail="Security Violation: Access to sensitive credential files is strictly forbidden.")
   ```
4. **Execution Profiling**: Measures actual tool call execution duration via `time.perf_counter()` in milliseconds.

### B. A2A Diagnostic Verification (`POST /api/a2a/test`)
A new verification endpoint was implemented to test dynamic AgentCard discovery:
```python
class A2ATestRequest(BaseModel):
    target_url: str = "http://127.0.0.1:8000/"
```

#### Security Guardrails:
1. **Anti-SSRF Confinement**: External and non-loopback domains (e.g. AWS metadata `169.254.169.254` or external domains) are rejected:
   ```python
   if not (parsed.hostname in ("127.0.0.1", "localhost")):
       raise HTTPException(status_code=400, detail="Security Violation: A2A diagnostic actions are restricted strictly to local agent instances.")
   ```
2. **Protocol Schema Compliance**: Fetches `/.well-known/agent-card.json`, parses response into Pydantic v2 `AgentCard` structure, and validates declared skills:
   - `Unit Test Generation`
   - `Mutation Critique`
   - `Hardening Workflow`

---

## 3. Evidence of In-Browser & Automated Execution

### A. Headed Chrome In-Browser Verification
Executed during [`verify_all_four_improvements.py`](file:///Users/sourabh/TestForge/qa_artifacts/teacher_review_implementation_20261027_105100/verify_all_four_improvements.py):

1. **A2A In-Browser Test**:
   - Status: `✅ A2A Protocol v0.3.0 Verified (0.12ms) — Transport: JSONRPC`
   - Schema verified: `true`
   - Skills detected: `Unit Test Generation`, `Mutation Critique`, `Hardening Workflow`
   - Screenshot: [`02_a2a_test_action_verified.png`](file:///Users/sourabh/TestForge/qa_artifacts/teacher_review_implementation_20261027_105100/screenshots/02_a2a_test_action_verified.png)

2. **FastMCP In-Browser Test**:
   - Status: `✅ FastMCP stdio Execution Successful (403.57ms) — Tool: list_directory`
   - Target path: `samples`
   - Directory contents returned: `discount.py`, `banking.py`, `inventory_pricing.py`, `rate_limiter.py`, `state_machine.py`
   - Screenshot: [`03_mcp_test_action_verified.png`](file:///Users/sourabh/TestForge/qa_artifacts/teacher_review_implementation_20261027_105100/screenshots/03_mcp_test_action_verified.png)

### B. Automated Security & Negative Tests ([`tests/test_teacher_review_improvements.py`](file:///Users/sourabh/TestForge/tests/test_teacher_review_improvements.py))

| Test Case | Scenario | Expected Result | Actual Result | Status |
| :--- | :--- | :--- | :--- | :---: |
| `test_mcp_list_directory_success` | Valid `list_directory` | HTTP 200, valid file array, elapsed > 0 | HTTP 200, elapsed 424.7ms | **PASSED** |
| `test_mcp_get_file_info_success` | Valid `get_file_info` on `discount.py` | HTTP 200, sha256 + size_bytes | HTTP 200, size 545 bytes | **PASSED** |
| `test_mcp_path_traversal_rejected` | Target `../server.py` | HTTP 400 Bad Request | HTTP 400 Bad Request | **PASSED** |
| `test_mcp_sensitive_file_rejected`| Target `.env` | HTTP 400 Bad Request | HTTP 400 Bad Request | **PASSED** |
| `test_mcp_disallowed_tool_rejected`| Tool `unwhitelisted_tool` | HTTP 422 Unprocessable Content | HTTP 422 Unprocessable Content | **PASSED** |
| `test_a2a_local_verification_success`| Local target `http://127.0.0.1:8000/` | HTTP 200, v0.3.0, verified | HTTP 200, v0.3.0, verified | **PASSED** |
| `test_a2a_remote_ssrf_rejected` | Target AWS metadata IP | HTTP 400 Bad Request | HTTP 400 Bad Request | **PASSED** |
| `test_a2a_external_domain_rejected`| External malicious domain | HTTP 400 Bad Request | HTTP 400 Bad Request | **PASSED** |

---

## 4. Conclusion
Criteria C and D are fully achieved. Users and automated verification harnesses can now execute real FastMCP and A2A actions directly in the browser while maintaining uncompromised security.
