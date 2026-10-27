# TestForge — Final Known Limitations & Environmental Boundaries

**Audit Date:** 2026-10-27 01:23:15 IST  
**Artifact Directory:** `qa_artifacts/autonomous_e2e_acceptance_20261027_004800/`  

---

## 1. Environmental & External Network Limitations

1. **Offline Sandbox Network Isolation:**
   - The evaluation environment is isolated from external outbound traffic.
   - Dynamic binary downloads (such as Playwright's browser manager fetching `playwright-1.57.0-mac-arm64.zip` from `azureedge.net`) return HTTP 404 / connection refusal.
   - *Impact:* Playwright browser automation is bypassed in favor of full HTTP/WebSocket client automation, DOM asset validation, and comprehensive pytest verification.
2. **Paid External LLM APIs:**
   - No external paid LLM API keys (OpenAI, Anthropic) were configured or billed during this autonomous audit.
   - *Impact:* The system operated in local synthesis and deterministic evaluation modes ($0.00 spend).

---

## 2. Architectural & Scope Limitations

1. **AST Sandbox vs MicroVM Boundary:**
   - The security guardrail operates via static AST syntax inspection (`ast.parse()`) and POSIX process timeouts in temporary directory sandboxes.
   - *Impact:* While effectively blocking standard system libraries (`os.system`, `subprocess`, `eval`, arbitrary file operations outside the permitted root), it does not provide hardware-isolated microVM containment (e.g. Firecracker).
2. **Preserved Working File (`test_hardened.py`):**
   - The pre-existing file `test_hardened.py` at the repository root contains an unstaged user working state importing `from samples.discount import discount` instead of `calculate_discount`.
   - *Impact:* Running `pytest test_hardened.py` yields an import collection error on this specific file. In accordance with Non-Negotiable Safety Rule 2.2, user working files were preserved without modification. The entire official test suite in `tests/` passes 428/428 tests.
3. **Equivalence & Mutation Scores:**
   - Depending on target function structure, semantic equivalent mutants can survive unless explicitly flagged by the user or equivalence heuristics.
   - *Impact:* Mutation kill scores vary from 21% to 100% across different fixture topologies.
