# TestForge Architecture Gap Register

**Status Date:** November 5, 2026  
**Evaluation Standard:** Production-grade, autonomous 8-agent test hardening system.

---

## 1. Classification Methodology

Gaps are ranked according to standard mission priority tiers:
- **P0 (Critical / Blocker):** Security escapes, data loss, state corruption, falsified metrics, unrecoverable crashes.
- **P1 (High / Core Quality):** Broken agent coordination, incomplete contracts, brittle workflows, deficient test intelligence.
- **P2 (Medium / Enhancement):** Usability, UI consistency, performance bottlenecks, observability fidelity.
- **P3 (Low / Polish):** Code formatting, style cleanups, cosmetic UI tweaks.

---

## 2. Identified Architecture Gaps

### GAP-001 [P0]: Host Sandbox Subprocess Isolation Boundary [RESOLVED & VERIFIED]
- **Component:** `testforge/sandbox.py`
- **Issue:** The sandbox runner executes tests via `subprocess.Popen` in temporary directories with `PYTHONPATH` adjustments. While AST visitors detect known dangerous calls (`eval`, `exec`, `os.system`), if malicious code bypasses AST static checks (e.g. through dynamic attribute resolution or obfuscated imports), OS-level process isolation (CPU time limits, memory caps via `resource.setrlimit`, blocked networking) is not enforced at the subprocess boundary.
- **Impact:** Potential resource exhaustion (infinite loops, memory bombs) or host environment snooping during untrusted code execution.
- **Remediation Plan:** Implement preexec function in `subprocess.Popen` with `resource.setrlimit` (RLIMIT_CPU, RLIMIT_AS) on Unix/macOS platforms, and strict environment stripping.
- **Status:** **RESOLVED** via `build_sanitized_sandbox_env` & `get_sandbox_preexec_fn`; verified by `tests/test_sandbox_security_isolation.py`.

### GAP-002 [P1]: Concrete Boundary-Value & Invariant Property Generation [RESOLVED & VERIFIED]
- **Component:** `testforge/planning_agent.py` & `testforge/adk_generator.py`
- **Issue:** Test planning extracts scenario categories (nominal, boundary, negative), but generated assertions often default to simple equality checks rather than probing mathematical and edge-case invariants (e.g., negative zero, float epsilon, collection length conservation, idempotent transformations).
- **Impact:** Surviving mutants in arithmetic/comparison boundary operators can persist across reflection loops unless explicitly targeted.
- **Remediation Plan:** Enhance `TestPlanningAgent` and `GoogleADKTestGenerator` with a deterministic Boundary Partitioning Engine (zero, negatives, MAX_INT, boundary strings, empty/singleton collections) and algebraic invariant generation.
- **Status:** **RESOLVED** via `_generate_extreme_boundary_partitions` and `_generate_property_invariants`; verified by `tests/test_boundary_and_property_intelligence.py`.

### GAP-003 [P1]: Multi-Dimensional Test Quality Scoring (TQS) & Suite Minimization [RESOLVED & VERIFIED]
- **Component:** `testforge/crew_critic.py` & `testforge/reflection_agent.py`
- **Issue:** The critic checks basic weak asserts and survival diffs, but does not calculate an explicit, transparent, multi-dimensional Test Quality Score (TQS) combining assertion strength, branch coverage, mutation killing power, and test independence. Furthermore, no automated minimization exists to prune redundant tests.
- **Impact:** Generated suites can accumulate duplicate or weak tests across reflection loops without a clear metric distinguishing high-value tests from noise.
- **Remediation Plan:** Implement an explicit TQS model (Assertion Strength + Mutation Ratio + Edge Coverage + Independence) and a test deduplication / greedy suite minimization pass that preserves 100% of killed mutants.
- **Status:** **RESOLVED** via `TestQualityAnalyzer.calculate_test_quality_score` (5 dimensions) & `deduplicate_and_minimize_suite`; verified by `tests/test_quality_score_and_minimization.py`.

### GAP-004 [P1]: Concurrent Job State Isolation & Checkpoint Safety [RESOLVED & VERIFIED]
- **Component:** `testforge/orchestrator.py`, `testforge/blackboard.py`, `testforge/persistence.py`
- **Issue:** While single jobs run reliably, multi-job execution must be strictly isolated to prevent cross-job contamination in shared directory paths or SQLite lock contentions.
- **Impact:** Concurrent API calls in server mode could collide if job identifiers or temporary workdirs overlap.
- **Remediation Plan:** Audit SQLite WAL-mode concurrency, verify per-job directory isolation, and write rigorous concurrency integration tests.
- **Status:** **RESOLVED** via isolated job test exports (`test_hardened_{job_id}.py`) and multithreaded WAL checkpoint validation; verified by `tests/test_concurrency_and_reliability.py`.

### GAP-005 [P2]: Frontend Wiretap Dynamic Alignment with 8 Canonical Agents [RESOLVED & VERIFIED]
- **Component:** `frontend/app.js`, `frontend/index.html`, `server.py`
- **Issue:** The backend `/api/wiretap` now outputs dynamic `eight_agents_status`, but the frontend UI still displays legacy agent pill elements and hardcoded labels.
- **Impact:** Frontend does not dynamically light up the 8 canonical agents in real-time as they participate in the workflow.
- **Remediation Plan:** Update `frontend/app.js` and `frontend/index.html` to consume `eight_agents_status`, dynamically rendering active/participating states for all 8 agents.
- **Status:** **RESOLVED** via `wiretap-eight-agents-grid`, `CANONICAL_EIGHT_META`, and `SUPERVISOR_DECISION` card rendering; verified by `tests/test_wiretap_frontend_topology.py`.

