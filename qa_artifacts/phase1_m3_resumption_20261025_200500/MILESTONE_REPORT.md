# TestForge Phase 1 Milestone 1.3: Resilient Checkpoint Recovery and Task Resumption (GAP-03)

## Executive Summary
This milestone report documents the implementation and verification of **GAP-03: Resilient Checkpoint Recovery and Task Resumption** for TestForge Phase 1. 

The implementation enables any interrupted, cancelled, or timed-out TestForge task to resume execution safely from its last valid persisted checkpoint. Resumption cleanly reconstructs Blackboard partitions, validates input hash provenance, restores lifecycle FSM states, skips completed pipeline stages, and cleans dead subprocess/MCP handles—without non-deterministic heuristics, redundant work, or silent corruption.

---

## 1. Checkpoint Stages & Resumption Policy

### 1.1 Persisted Checkpoint Stages
TestForge writes transactional SQLite checkpoints across the pipeline lifecycle:
| Checkpoint Stage | Persisted Partitions | Invariants | Resumes At | Skipped Stages |
|---|---|---|---|---|
| `INITIAL_INGESTION` | TargetSpace, MetricsSpace | Target source code and AST signatures extracted | `BASELINE_SYNTHESIS` | `VALIDATING`, `INGESTING` |
| `BASELINE_SYNTHESIS` | TargetSpace, SuiteSpace, MetricsSpace | Candidate test suite generated | `BASELINE_VALIDATION` | `VALIDATING`, `INGESTING`, `PLANNING`, `GENERATING_TESTS` |
| `BASELINE_VALIDATED` | TargetSpace, SuiteSpace, MetricsSpace | Candidate suite passed clean code pass@1 check; line coverage recorded | `REFLECTION_LOOP` | `VALIDATING`, `INGESTING`, `PLANNING`, `GENERATING_TESTS`, `EXECUTING` |
| `REFLECTION_ITERATION_{k}` | TargetSpace, SuiteSpace, MutantSpace, CriticSpace, MetricsSpace | Mutation score, mutant survival records, critic directives, hardened tests recorded | `REFLECTION_LOOP` (at iteration `k + 1`) | All stages up to and including iteration `k` |
| `CANCELLED` / `TIMED_OUT` | TargetSpace, SuiteSpace, MutantSpace, CriticSpace, MetricsSpace | Partial progress, reason, and cancellation metrics recorded | Evaluated based on furthest verified partition (`REFLECTION_LOOP`, `BASELINE_VALIDATION`, or `BASELINE_SYNTHESIS`) | Stages prior to furthest verified milestone |
| `FINALIZED` / `COMPLETED` | Complete snapshot | Terminal execution state reached | `COMPLETED` | All stages (`ALL`) |

### 1.2 Distinguishing Deserialization from Genuine Execution Resumption
- **Checkpoint Deserialization**: Rehydrates `BlackboardSnapshot` JSON into in-memory partition spaces (`target`, `mutant`, `critic`, `suite`, `metrics`).
- **Execution Resumption**: Re-establishes execution context, initializes the FSM in `TaskLifecycleState.RECOVERING` -> `RECOVERED` -> `MUTATION_ANALYSIS`, bypasses already-completed pipeline steps (`skip_ingestion=True`, `skip_baseline_synth=True`, `skip_baseline_validation=True`), re-initializes sandboxes, and resumes the reflection loop from the checkpoint iteration.

---

## 2. Integrity Verification & Invalidation Guards

Before any checkpoint state is applied to the live orchestrator, `SQLiteBlackboardStorage.validate_checkpoint` enforces strict validation rules:

1. **Schema Version Validation**: Checkpoints must match `CURRENT_SCHEMA_VERSION` (version 1). Checkpoints with differing schema versions raise `IncompatibleSchemaError` and are rejected.
2. **Task Identity Validation**: If an expected `task_id` or `workflow_id` is specified, the record must belong to that task; mismatches raise `TaskIdentityMismatchError`.
3. **Input Hash Integrity**: Target source code is normalized and hashed via SHA-256 (`compute_source_hash`). If the resumed task's source code differs from `snapshot.target.input_hash`, an `InputHashMismatchError` is raised immediately.
4. **Partition Completeness**: Checkpoint JSON must deserialize into a valid `BlackboardSnapshot`. Missing partitions or unparseable JSON raise `CheckpointCorruptedError` or `IncompleteCheckpointError`. If candidate test code is missing from a `BASELINE_VALIDATED` checkpoint, the policy falls back to `BASELINE_SYNTHESIS`.

---

## 3. Subprocess & Transport Resource Safety

1. **MCP Client Disconnection & Reinitialization**:
   If an MCP client manager is attached to the resumed orchestrator, `validate_and_restore_checkpoint()` invokes `mcp_client.disconnect_sync()`. This closes orphan stdio pipes and cleans dead subagent processes before opening fresh connections.
2. **Parallel Sandbox Pools**:
   Parallel mutant execution sandboxes (`ParallelSandboxRunner`) are instantiated afresh per orchestrator run, ensuring no defunct worker PIDs or broken IPC pipes persist across recovery.
3. **Idempotent Repeated Recovery**:
   Calling `validate_and_restore_checkpoint()` or `resume_from_checkpoint()` repeatedly on the same checkpoint produces identical, side-effect-free results without duplicate events or corrupted database records.

---

## 4. Lifecycle & Observability Integration

Resumption is fully observable across both the Event Stream and JSONL TraceLogger:
- **Lifecycle States**:
  - `CREATED` -> `RECOVERING` (validation & partition restoration in progress)
  - `RECOVERING` -> `RECOVERED` (validation succeeded, resumption plan ready)
  - `RECOVERED` -> Resume Stage (e.g., `MUTATION_ANALYSIS` for reflection loop)
  - On failure: `RECOVERING` -> `FAILED` (with explicit failure reason)
- **Lifecycle Events**:
  - `EventType.RECOVERY_DECISION`: Dispatched with complete `ResumptionPlan` payload (`checkpoint_id`, `resumes_at`, `target_lifecycle_state`, `skipped_stages`, `start_iteration`).
  - `EventType.CHECKPOINT_RESTORED`: Dispatched upon successful Blackboard restoration.
  - `EventType.CHECKPOINT_FAILED`: Dispatched with error code and reason upon any validation or recovery failure.
- **TraceLogger**:
  - `RECOVERY_DECISION` and `CHECKPOINT_RESTORED` events recorded with correlation IDs and token tracking.

---

## 5. REST API Endpoints & Server Integration

FastAPI server endpoints expose robust resumption control:
1. `POST /api/checkpoints/{checkpoint_id}/resume`:
   Validates checkpoint, computes `ResumptionPlan`, spawns background hardening job resumed from the checkpoint, and returns 200 with `resumption_plan` and `poll_url`.
2. `POST /api/harden/resume/{job_id}`:
   Resolves the latest resumable checkpoint for `job_id` from SQLite storage and queues background resumption.
3. `GET /api/harden/{job_id}/status`:
   Exposes `resumed_from_checkpoint` and `resumption_plan` fields in the job status payload for UI and monitoring clients.

---

## 6. Verification & Test Evidence

- **Unit & Integration Suite**: `tests/test_checkpoint_resumption.py` (17 tests, 100% pass rate).
  - Includes `test_genuine_interruption_and_successful_resumption`: genuine multi-stage run interrupted via cancellation event after baseline validation checkpoint, followed by genuine resumed run demonstrating skipped stages and successful completion.
- **Regression Suites**:
  - `tests/test_blackboard_persistence.py`
  - `tests/test_task_lifecycle.py`
  - `tests/test_orchestration_mcp.py`
  - All 55 tests passed with zero regressions.
- **Formatting & Style**:
  - `git diff --check` executed with clean exit code 0.
