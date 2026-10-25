# TESTFORGE — KNOWN LIMITATIONS & OPERATIONAL BOUNDARIES

This document transparently records the known boundaries, trade-offs, and operational assumptions of the TestForge system.

---

## 1. Commercial LLM vs. Deterministic Local Evaluation

- **Design Decision:** In accordance with safety constraints and reproducibility requirements, the core benchmark test suite and browser audit use fast, deterministic, offline reflection and mutation engines rather than calling external commercial LLM APIs on every run.
- **Provider Support:** The backend fully supports live Google Gemini (`gemini-2.5-pro`, `gemini-2.0-flash`) and OpenRouter via configured environment variables (`GEMINI_API_KEY`, `OPENROUTER_API_KEY`). However, external network calls are intentionally gated by API key presence.
- **Reporting Separation:** In `benchmark_results_fast.json` and the frontend Benchmarking tab, simulated/offline runs are explicitly labeled with `is_simulation: true` or `mode: "Deterministic Offline"`, ensuring no simulated scores are ever falsely presented as empirical cloud measurements.

---

## 2. AST Equivalence Filtering

- **Theoretical Limit:** Determining whether a mutant is mathematically equivalent to the original program is undecidable in computer science (Rice's Theorem).
- **Practical Boundary:** TestForge implements rule-based pattern matching for common equivalent mutations (such as default argument substitutions, redundant identity operations, and equivalent logical invariants). Highly non-trivial semantic equivalence across complex loops remains a known residual risk.

---

## 3. Subprocess Sandboxing Scope

- **Current Implementation:** TestForge runs test suites in isolated OS subprocesses with strict CPU execution timeouts (`sandbox_timeout_secs`), process group termination (`SIGTERM` + `SIGKILL`), and memory/output limits.
- **Production Recommendation:** For multi-tenant cloud deployments, host subprocesses should be upgraded to ephemeral Docker containers, gVisor sandboxes, or Firecracker microVMs to guarantee kernel-level namespace isolation.

---

## 4. Clipboard API in Headless Browsers

- **Browser Behavior:** In automated headless browser runs, standard browser security policies may restrict unprompted access to the host OS clipboard (`navigator.clipboard.writeText`).
- **Mitigation:** The frontend provides fallback toast notifications ("Clipboard access denied" / visual alert) without throwing fatal JavaScript exceptions or disrupting user workflow.
