# TestForge — Security Test Results & Vulnerability Audit

**Audit Date:** 2026-10-27 01:18:30 IST  
**Artifact Directory:** `qa_artifacts/autonomous_e2e_acceptance_20261027_004800/`  

---

## 1. Security Architecture & Threat Model

TestForge operates on untrusted user code and synthetic test inputs. The threat model addresses:
1. **Arbitrary Code Execution (RCE):** Malicious inputs attempting to invoke system commands or spawn unauthorized shells.
2. **Filesystem Path Traversal:** Ingestion or MCP tool calls attempting to read secrets outside the project directory (`.env`, `~/.ssh/id_rsa`, `/etc/passwd`).
3. **Denial of Service / Unbounded Execution:** Infinite loops, fork bombs, or hanging processes exhausting memory or CPU.
4. **Secret Leaks in Traces & Logs:** Accidental exposure of API keys, tokens, or private environment variables in traces, HTTP responses, or logs.

---

## 2. Security Test Matrix

| Attack Vector / Test Scenario | Injected Payload / Method | Expected Defense | Observed Behavior | Test Verdict |
|---|---|---|---|:---:|
| **RCE via `os.system`** | `os.system('cat /etc/passwd')` in candidate code | AST Guardrail rejects before execution | Transitioned to `FAILED` with AST security rejection | **PASS** |
| **RCE via `subprocess.run`** | `subprocess.run(['rm', '-rf', '/tmp'])` | AST Guardrail blocks `subprocess` module | Blocked by `SecurityGuardrail` | **PASS** |
| **Dynamic Execution via `eval`** | `eval('__import__(\"sys\").exit(1)')` | AST Guardrail blocks `eval`, `exec`, `compile` | Node visitor detected prohibited call | **PASS** |
| **Path Traversal via MCP** | `read_text_file(path='../../../../etc/passwd')` | Bounded by `permitted_root` | `ValueError: Path outside permitted workspace root` | **PASS** |
| **Sensitive Secret Masking in MCP** | `list_directory()` containing `.env` or `.git` | Filter sensitive patterns | Sensitive files masked from response list | **PASS** |
| **Infinite Loop / Timeout** | `while True: pass` in mutant evaluation | Process timeout enforcement | Worker killed after configured timeout; marked `TIMEOUT` | **PASS** |
| **Secret Redaction in Logs** | `TraceLogger.log(f"Key: {sk_live_12345}")` | Regex pattern redactor | Logged as `Key: [REDACTED_API_KEY]` | **PASS** |
| **Empty / Malformed Ingestion** | Empty string or whitespace in `/api/harden/start` | HTTP 400 Bad Request | Returned `HTTP 400: Target source code and file path are required.` | **PASS** |

---

## 3. Residual Security Boundaries & Documentation

- **AST Boundary Scope:** AST inspection is a static pre-execution filter. It effectively prevents standard standard-library system calls and injection strings, but is not equivalent to a hardened kernel microVM (e.g. AWS Firecracker or gVisor).
- **Subprocess Isolation:** Worker sandboxes run as bounded subprocesses inside isolated temporary directories. Process limits and timeouts prevent resource exhaustion.
