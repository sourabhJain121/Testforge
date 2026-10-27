# Milestone 5: Security Hardening & Audit Report

**Date:** 2026-10-26  
**Artifact Directory:** `qa_artifacts/phase2_finalization_20261026_141500/milestone5_security/`  
**Auditor:** TestForge Core Engineering  

---

## 1. Executive Summary

A comprehensive security audit of TestForge was performed across all six target areas:
1. Sandbox boundaries & process isolation
2. SSRF & network restrictions
3. Secret redaction & credential scrubbing
4. API validation & error handling
5. Prompt & tool safety (injection, override, exfiltration)
6. Dependencies & configuration

Every finding has been evaluated against live code, verified with regression tests, and classified by severity.

---

## 2. Findings Matrix

| Ref ID | Security Domain | Finding Description | Severity | Status | Code Evidence | Test Verification |
|---|---|---|---|:---:|---|---|
| **SEC-01** | Sandbox Boundaries | Subprocess test execution bounded by per-test timeouts (default 5s, configurable 1-30s), temporary directory cleanup, and non-blocking kill on expiration. Runaway infinite loops or malicious pauses cannot hang the host. | High | **VERIFIED PASS** | `testforge/sandbox.py:SubprocessSandbox.run_test_suite` | `tests/test_sandbox.py`, `tests/test_mutation_guided_repair.py` |
| **SEC-02** | Sandbox Boundaries | Python-level validation alone is not claimed as an OS kernel sandbox. Static AST inspection acts as an immediate pre-execution filter (`SEC_AST_*`), while subprocess execution handles execution faults. | Informational | **VERIFIED PASS** | `testforge/security.py:SecurityGuardrail.inspect_code_ast`, `testforge/sandbox.py:_run_single_test_task` | `tests/test_security.py:test_sandbox_runner_blocks_dangerous_execution_before_subprocess` |
| **SEC-03** | Network Restrictions & SSRF | Generated test code is statically inspected for socket instantiation (`socket.socket`) and remote HTTP calls (`urllib.request.urlopen`, `requests`). All such network calls are blocked with `SEC_AST_NETWORK_SOCKET`. Ingestion URL validation in Mode C restricts URLs to valid GitHub endpoints (`https://github.com/...`) with control character sanitization. | High | **VERIFIED PASS** | `testforge/security.py:270-295`, `testforge/ingestion.py:parse_and_normalize_github_url` | `tests/test_security.py:test_detection_of_network_socket_and_urlopen`, `tests/test_mode_c_ingestion.py` |
| **SEC-04** | Secret Redaction | Regex patterns scrub API keys (`sk-...`, `AIza...`, `ghp_...`), bearer tokens, passwords, and secrets across error messages, trace logs, and user-facing responses, replacing them with `[REDACTED_SECRET]`. | High | **VERIFIED PASS** | `testforge/security.py:redact_sensitive_data`, `testforge/logger.py:TraceLogger` | `tests/test_security.py:test_credential_redaction`, `tests/test_observability.py:test_credential_scrubbing_in_traces` |
| **SEC-05** | API Validation & Guardrails | FastAPI schemas validate all input parameters (`HardeningRunPayload`, `SampleIngestPayload`, `KeyConfigPayload`). Path traversal on sample names is prevented by checking existence within `SAMPLES_DIR` and stripping path components (`safe_name = os.path.basename(...)`). Malformed or empty inputs return 400/422 status codes without internal stack trace leakage. | Medium | **VERIFIED PASS** | `server.py:483-515, 814-850`, `testforge/ingestion.py` | `tests/test_cancellation.py`, `tests/test_a2a_card_ui_and_endpoint.py` |
| **SEC-06** | Prompt & Tool Safety | Input prompts are inspected for system prompt overrides (`INJ_SYSTEM_OVERRIDE`), role hijacking (`INJ_NEW_ROLE_PROMPT`), credential exfiltration (`INJ_SECRET_LEAK`), safety disabling (`INJ_SECURITY_DISABLE`), delimiter escaping (`INJ_SYSTEM_DELIMITER_ESCAPE`), and tool permission bypasses (`INJ_TOOL_BYPASS`). High/Critical risk triggers immediate security refusal before LLM invocation. | Critical | **VERIFIED PASS** | `testforge/security.py:SecurityGuardrail.inspect_prompt` | `tests/test_security.py:test_suspicious_prompt_injection_*`, `tests/test_observability.py:test_orchestrator_security_refusal_observability` |
| **SEC-07** | AST Policy Enforcement | Generated test suites undergo static AST policy enforcement before sandbox execution. Disallows `eval`, `exec`, `os.system`, `subprocess`, dynamic imports (`__import__`, `importlib`), and forbidden modules. Safely distinguishes harmless method names (`model.eval()`) from malicious invocations. | Critical | **VERIFIED PASS** | `testforge/security.py:_ASTSecurityVisitor` | `tests/test_security.py:test_detection_of_eval_and_exec`, `test_benign_eval_method_not_flagged` |
| **SEC-08** | Abuse & Toxicity Guardrails | Detects abusive, threatening, or harassing prompts (`INJ_TOXIC_ABUSIVE`) while correctly permitting legitimate technical terms (e.g., "kill runaway infinite loops", "kill surviving mutants"). | Medium | **VERIFIED PASS** | `testforge/security.py:150-156` | `tests/test_security.py:TestToxicityAndAbuseInspection` |
| **SEC-09** | MCP Tool Confinement | Filesystem MCP server restricts file operations strictly to the designated workspace root (`permitted_root=BASE_DIR / 'samples'`). Paths attempting `../` traversal or escaping the sandbox boundary are rejected. | High | **VERIFIED PASS** | `testforge/mcp_server.py:create_filesystem_server` | `tests/test_mcp.py` |
| **SEC-10** | Job Cancellation & Denial of Service | Cooperative cancellation (`threading.Event`) guarantees that background jobs can be halted gracefully via `/api/harden/cancel/{job_id}`, preventing resource exhaustion. Non-blocking polling ensures responsive API service. | Medium | **VERIFIED PASS** | `server.py:873-900`, `testforge/orchestrator.py` | `tests/test_cancellation.py` |

---

## 3. Residual Risks & Documented Mitigations

1. **Host-Level Isolation:** Test execution runs in a standard Python subprocess with resource timeouts rather than an unprivileged Docker container or gVisor sandbox. In production deployments, the backend should be run inside containerized environments (as provided by the Dockerfile) to enforce kernel-level cgroups and network namespace isolation.
2. **Local Ollama Access:** The local Ollama server runs over HTTP on `localhost:11434`. Access is constrained to the host loopback interface, preventing external SSRF exploitation.
