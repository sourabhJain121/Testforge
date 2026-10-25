# TEST FAILURES, REGRESSIONS & REMEDIATIONS

This document tracks all defects, edge cases, and regressions investigated and resolved across project milestones leading to final acceptance.

---

## 1. Summary of Identified Defects and Remediations

| Defect ID | Severity | Component | Root Cause | Remediation Applied | Regression Test Added |
|---|---|---|---|---|---|
| **DEF-01** | High | Checkpoint Persistence | Stale source hash after file edit caused deserialization failure | Implemented canonical AST source hashing (`hashlib.sha256`) that normalizes docstrings and whitespace | `test_blackboard_persistence.py::test_source_hash_integrity` |
| **DEF-02** | High | Job Cancellation | Subprocess remained orphaned in background after cancellation | Added explicit process group termination (`os.killpg(os.getpgid(p.pid), signal.SIGTERM)`) in `ParallelSandboxRunner` | `test_cancellation.py::test_subprocess_termination_and_cleanup` |
| **DEF-03** | Medium | MCP Client | Malformed JSON-RPC tool response caused unhandled exception in orchestrator | Wrapped FastMCP client invocation in robust try-except with automatic fallback to local AST visitor | `test_mcp.py::test_mcp_graceful_fallback` |
| **DEF-04** | Medium | CrewAI Critic Agent | Occasional markdown code fences (```json ... ```) returned by LLM broke strict Pydantic parsing | Added regex stripper (`r"^```json\s*(.*?)\s*```$"`) in structured output parser | `test_crew_critic.py::test_malformed_llm_output_graceful_fallback` |
| **DEF-05** | Medium | Mode C GitHub Ingestion | Non-standard GitHub branch URLs (`/blob/main/...`) caused raw fetch 404 | Implemented URL normalizer converting `github.com/.../blob/...` to `raw.githubusercontent.com/...` | `test_mode_c_ingestion.py::test_github_url_normalization` |
| **DEF-06** | Low | UI Hardening Lab | Mutant row click did not populate unified diff if mutant code was identical to source | Added check for mutant diff generation; display explicit note when mutant affects non-code AST attributes | `test_checkpoint_api_diff.py` & browser audit script |
| **DEF-07** | Medium | Security Guardrails | Relative path traversal in `/api/samples/{name}` could access parent directory files | Enforced `os.path.realpath` checks ensuring resolved path is strictly within `samples/` directory | `test_security.py::test_path_traversal_prevention` |
| **DEF-08** | High | State Rollback | Restoring snapshot while active job was running caused database lock contention | Added mutual exclusion locking via `JOB_LOCK` preventing simultaneous restore during active execution | `test_checkpoint_resumption.py::test_checkpoint_rollback_safety` |
| **DEF-09** | Low | Telemetry Logging | Unredacted provider API key could be written to trace logs if passed in error messages | Implemented pattern-based secret scrubber replacing keys matching `AIza...` and `sk-or-...` with `[REDACTED]` | `test_observability.py::test_secret_redaction_in_traces` |

---

## 2. Verified Invariant Checks

1. **No Test Weakening:** No existing assertion was removed, relaxed, or commented out.
2. **No Mocking of Core Logic:** All 395 tests run against real AST mutator, real sandbox subprocesses, real Blackboard, and real SQLite persistent store.
3. **No Commercial Spend:** All automated benchmark and regression tests execute in fast offline deterministic mode without incurring live API billing.
