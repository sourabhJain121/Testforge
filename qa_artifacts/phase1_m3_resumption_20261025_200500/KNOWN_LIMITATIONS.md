# TestForge Phase 1 Milestone 1.3: Known Limitations & Operational Boundaries

## Scope & Target Milestone
This document establishes the operational boundaries, non-resumable edge cases, and architectural limitations of the Resilient Checkpoint Recovery and Task Resumption mechanism (GAP-03 / Milestone 1.3).

---

## 1. Safe Boundaries & Rerun Justification for Unsafe Stages

### 1.1 In-Flight Stage Midpoint Interruption
- **Boundary**: TestForge checkpoints are persisted transactionally upon the successful exit of distinct pipeline stages (`INITIAL_INGESTION`, `BASELINE_SYNTHESIS`, `BASELINE_VALIDATED`, `REFLECTION_ITERATION_{k}`, `FINALIZED`, `CANCELLED`).
- **Policy**: If execution is interrupted mid-stage (e.g., process killed during parallel mutant sandbox execution before `REFLECTION_ITERATION_{k}` is committed), recovery falls back to the last fully verified checkpoint.
- **Justification**: Partial sandbox runs may have executed only a subset of mutants. Resuming from partial in-memory execution without an atomic snapshot risks mutant score skew and inconsistent mutant state. Repeating the interrupted iteration ensures sound mutation analysis.

### 1.2 Baseline Candidate Test Synthesis Without Test Code
- **Boundary**: If a checkpoint is recorded at `BASELINE_SYNTHESIS` or `BASELINE_VALIDATED` but the snapshot lacks candidate test code (e.g. partition corruption or empty test suite generation failure), recovery automatically demotes the stage to `BASELINE_SYNTHESIS`.
- **Policy**: Rerun baseline test synthesis rather than attempting to validate an empty or absent suite.
- **Justification**: Sandbox pass@1 validation requires concrete test code. Rerunning synthesis restores test suite invariants cleanly.

---

## 2. Invalidation & Security Rejection Policies

### 2.1 Input Code Drift (`InputHashMismatchError`)
- **Boundary**: When resuming with an explicitly provided `target_source_code`, TestForge computes the SHA-256 hash of the normalized source and cross-references it against `input_hash` stored in the checkpoint snapshot.
- **Policy**: Any discrepancy causes immediate rejection with `InputHashMismatchError`.
- **Justification**: Checkpoint test suites and AST mutation positions are strictly coupled to the exact syntax and line numbers of the original target file. Permitting resumption against modified source code would execute invalid assertions or mutated AST nodes at incorrect line numbers.

### 2.2 Incompatible Schema Version (`IncompatibleSchemaError`)
- **Boundary**: Checkpoints must have `schema_version == CURRENT_SCHEMA_VERSION` (version 1).
- **Policy**: Checkpoints created with older or unmigrated schemas fail validation and are rejected.
- **Justification**: Backward-incompatible modifications to partition structures (e.g. `BlackboardSnapshot`) cannot be safely deserialized without explicit migration scripts.

### 2.3 Task Identity Separation (`TaskIdentityMismatchError`)
- **Boundary**: When resuming via an existing job identifier (`job_id` or `workflow_id`), the checkpoint metadata must belong to that job.
- **Policy**: Cross-job resumption requires explicit administrative checkpoint ID selection; mismatched job IDs are rejected.
- **Justification**: Prevents state pollution across disparate orchestration runs.

---

## 3. Subprocess & Transport Resource Boundaries

### 3.1 Dead Process Handles & Subprocess Sandboxes
- **Boundary**: Subprocess workers and MCP servers spawned in a prior execution cycle cannot be reattached across process crashes or daemon restarts.
- **Policy**: Upon restoring from a checkpoint, TestForge discards stale child process IDs, closes or resets any attached MCP client sessions (`mcp_client.disconnect_sync()`), and instantiates fresh worker pools.
- **Justification**: OS process handles and stdio pipes do not survive process restarts. Re-establishing fresh transport handles guarantees deadlock-free operation.

### 3.2 In-Flight LLM Stream / Network Calls
- **Boundary**: In-flight LLM calls to Google Gemini or OpenRouter aborted during network outages or task cancellation cannot be resumed at partial token generation.
- **Policy**: Aborted generation requests are re-invoked cleanly with full context upon recovery.
- **Justification**: LLM provider streaming protocols do not support mid-stream token continuation.

---

## 4. Phase 2 Boundary Explicit Statement
- **Boundary**: Milestone 1.3 does NOT include multi-repository benchmark corpus evaluation or automated quality degradation suites across external repositories (Phase 2 / GAP-04).
- **Status**: Milestone 1.3 delivers complete, robust, and verified checkpoint recovery within the TestForge orchestration and server architecture.
