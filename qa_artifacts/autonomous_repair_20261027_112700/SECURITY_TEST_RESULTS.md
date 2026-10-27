# Security Test Results: Guardrails, Isolation & Protocol Boundaries

**Audit Directory:** `qa_artifacts/autonomous_repair_20261027_112700/`  
**Repository:** `/Users/sourabh/TestForge`

---

## 1. Security Architecture & Threat Vectors

TestForge enforces defense-in-depth security across five critical attack surfaces:

1. **Subprocess Sandbox Isolation** (`testforge/sandbox.py`):
   - Restricts CPU execution time and virtual memory.
   - Executes untrusted LLM-generated test code in isolated subprocesses.
2. **AST Static Code Sanitizer** (`testforge/security.py`):
   - Inspects candidate code before execution.
   - Forbids dangerous modules (`os.system`, `subprocess`, `shutil.rmtree`, `sys.exit`, `eval`, `exec`).
3. **Pass@1 Clean Code Quarantine**:
   - Executes candidate tests against unmodified clean source code.
   - If a candidate test fails on clean code, it is immediately quarantined to prevent polluting the test suite.
4. **FastMCP Filesystem Confinement** (`server.py` & `testforge/mcp_server.py`):
   - Confines operations strictly to the authorized directory root (`samples`).
   - Rejects directory traversal (`..`), absolute paths, and sensitive credential files (`.env`, `.git`, `.key`, `id_rsa`).
   - Whitelists only read-only tools (`list_directory`, `get_file_info`).
5. **Agent2Agent Anti-SSRF Protection** (`server.py`):
   - Confines diagnostic agent discovery strictly to local loopback hosts (`127.0.0.1`, `localhost`).
   - Blocks external domain and cloud instance metadata attacks (`169.254.169.254`).

---

## 2. Automated Security Verification Results

| Test Case | Scenario / Vector | Expected Result | Actual Result | Status |
| :--- | :--- | :--- | :--- | :---: |
| `test_mcp_path_traversal_rejected` | Request `path="../server.py"` | HTTP 400 Bad Request ("directory traversal or absolute paths are strictly forbidden") | HTTP 400 Bad Request | **PASS** |
| `test_mcp_sensitive_file_rejected` | Request `path=".env"` | HTTP 400 Bad Request ("Access to sensitive credential files is strictly forbidden") | HTTP 400 Bad Request | **PASS** |
| `test_mcp_disallowed_tool_rejected` | Tool `execute_shell_command` | HTTP 422 Unprocessable Content (Schema validation failure) | HTTP 422 Unprocessable Content | **PASS** |
| `test_a2a_remote_ssrf_rejected` | Target `http://169.254.169.254/latest/meta-data` | HTTP 400 Bad Request ("A2A diagnostic actions are restricted strictly to local agent instances") | HTTP 400 Bad Request | **PASS** |
| `test_a2a_external_domain_rejected`| Target `http://evil.com/agent-card.json` | HTTP 400 Bad Request | HTTP 400 Bad Request | **PASS** |
| `test_sandbox_timeout_termination` | Infinite loop `while True: pass` in candidate test | Subprocess SIGKILL after timeout | Killed, reported TIMEOUT | **PASS** |
| `test_ast_sanitizer_dangerous_call` | Candidate test contains `import os; os.system('rm -rf /')` | Sanitizer flags security violation, quenches execution | Blocked | **PASS** |

---

## 3. In-Browser Verification Proof

During the headed browser session ([`run_autonomous_browser_verification.py`](file:///Users/sourabh/TestForge/qa_artifacts/autonomous_repair_20261027_112700/run_autonomous_browser_verification.py)):
- **Flow 7 (Unsafe MCP Traversal)**: Submitted `path="../server.py"`. Server returned `HTTP 400` with detail: `"Security Violation: Directory traversal or absolute paths are strictly forbidden."`
- **Flow 10 (A2A SSRF)**: Submitted `target_url="http://169.254.169.254/latest/meta-data"`. Server returned `HTTP 400` with detail: `"Security Violation: A2A diagnostic actions are restricted strictly to local agent instances."`

All security boundaries are active and non-bypassable.
