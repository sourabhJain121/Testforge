# TestForge Security Findings & Verification Log

**Audit Date:** November 5, 2026  
**Auditor:** Application Security Engineer & Systems Architect

---

## 1. Security Architecture Assessment

TestForge processes arbitrary Python code and generated tests. Security controls are multi-layered:

1. **Static AST Guardrails (`testforge/security.py`):**
   - Syntax validation via `ast.parse`.
   - AST Node Visitor (`SecurityGuardrail`) inspecting imports and function calls.
   - Refusal of prohibited primitives: `eval`, `exec`, `__import__`, `os.system`, `subprocess.Popen`, raw socket operations.
   - Regex-based indirect prompt injection and secret pattern matching.
2. **Deterministic Agent Precedence (`testforge/supervisor_agent.py`):**
   - The `SupervisorAgent` deterministic gate strictly enforces `STOP_SECURITY_REFUSAL` whenever `SecurityAgent` flags unallowed code. LLM deliberation cannot bypass this gate.
3. **Execution Sandbox (`testforge/sandbox.py`):**
   - Runs in isolated temporary directories created with `tempfile.TemporaryDirectory`.
   - Strips environment variables containing API keys and secrets.
   - Configures execution timeouts (`timeout=10s`) on subprocess calls.

---

## 2. Identified Vulnerabilities & Hardening Opportunities

| Finding ID | Severity | Target Area | Description | Status |
| :---: | :---: | :--- | :--- | :---: |
| **SEC-001** | High (P0) | Process Sandbox Isolation | Lack of OS-level resource limits (`setrlimit` CPU/Memory) at the subprocess boundary. | **RESOLVED & VERIFIED** |
| **SEC-002** | Medium (P1) | Environment Sanitization | Environment passed to pytest should explicitly whitelist only safe variables (`PYTHONPATH`, `PATH`, `SYSTEMROOT`) and scrub all caller variables. | **RESOLVED & VERIFIED** |
| **SEC-003** | Medium (P1) | Path Traversal Defense | Target and test file paths passed to CLI and REST API must be strictly confined to workspace roots or temporary directories. | **RESOLVED & VERIFIED** |
