# TestForge Architecture: Persistent SQLite Blackboard Checkpointing

**Milestone:** 1.2 — Persistent SQLite Blackboard Checkpointing  
**Status:** Verified & Operational  
**Engine Environment:** Python 3.13.17 (`.venv-release`) on Darwin arm64  
**Date:** October 23, 2026  

---

## 1. Architectural Overview

TestForge uses a shared, typed, multi-agent **Blackboard** to coordinate state across autonomous agents (Target Ingestion, AST Fault Mutator, Subprocess Sandbox, Google ADK Generator, and CrewAI Adversarial Critic).

Prior to Milestone 1.2, Blackboard partitions existed strictly in-memory (`RLock`-synchronized Pydantic v2 models). While in-memory operation provided low latency (<15µs per partition mutation), long-running workflows or server restarts risked losing execution progress, surviving mutant records, and reflection history.

Milestone 1.2 introduces **persistent SQLite checkpointing** directly into the Blackboard architecture:
- **Zero-overhead In-Memory Default:** In-memory execution remains the default (`storage=None`). Tests and lightweight CLI invocations incur 0 database overhead.
- **Configurable Persistence Layer:** When enabled via `checkpoint_db_path` or `TESTFORGE_CHECKPOINT_DB`, the Blackboard captures all-or-nothing transactional snapshots at defined orchestration boundaries.
- **WAL Concurrency:** Uses SQLite Write-Ahead Logging (`PRAGMA journal_mode=WAL`) and `PRAGMA busy_timeout=5000` to support concurrent multi-reader and single-writer pipelines without database lock errors.
- **Fail-Safe Isolation:** Database I/O errors never crash the in-memory pipeline (unless `strict_persistence=True`), ensuring pipeline resilience.
- **Security by Design:** Full recursive scrubbing of credentials (API keys, tokens, passwords) prior to serialization.

```
+-----------------------------------------------------------------------------------------+
|                                    TestForge Blackboard                                 |
|                                                                                         |
|  +--------------------+  +--------------------+  +--------------------+  +------------+ |
|  |    TargetSpace     |  |    MutantSpace     |  |    CriticSpace     |  | SuiteSpace | |
|  |  (AST call graph)  |  |  (18-fault records)|  |  (Adversarial RAG) |  |  (Pytest)  | |
|  +--------------------+  +--------------------+  +--------------------+  +------------+ |
|  +------------------------------------------------------------------------------------+ |
|  |                         MetricsSpace (Iteration History & Telemetry)               | |
|  +------------------------------------------------------------------------------------+ |
|                                                                                         |
|      Threading RLock & Pydantic v2 Schema Validation (Fail-Closed, Monotonic Revs)      |
+-----------------------------------------------------------------------------------------+
                                    |
                    get_snapshot()  |  restore_from_snapshot()
                                    v
+-----------------------------------------------------------------------------------------+
|                    testforge.persistence.SQLiteBlackboardStorage                        |
|                                                                                         |
|  - Redaction Scrubbing (strips all API keys, credentials, tokens)                        |
|  - WAL Journal Mode (PRAGMA journal_mode=WAL; PRAGMA busy_timeout=5000)                |
|  - Parameterized SQLite Transactions (All-or-Nothing Commit/Rollback)                   |
+-----------------------------------------------------------------------------------------+
                                    |
                                    v
                       [ testforge_checkpoints.db ]
```

---

## 2. Database Schema & Storage Model

The database uses SQLite 3 with parameterized queries and explicit indexing:

```sql
-- Schema Version Tracking
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY,
    applied_at REAL NOT NULL
);

-- Checkpoint Snapshot Records
CREATE TABLE IF NOT EXISTS checkpoints (
    checkpoint_id TEXT PRIMARY KEY,
    schema_version INTEGER NOT NULL,
    job_id TEXT,
    workflow_id TEXT,
    stage TEXT NOT NULL,
    revision INTEGER NOT NULL,
    created_at REAL NOT NULL,
    status TEXT NOT NULL,
    metrics_summary_json TEXT NOT NULL,
    snapshot_json TEXT NOT NULL
);

-- Performance Indexes
CREATE INDEX IF NOT EXISTS idx_checkpoints_job_created 
    ON checkpoints(job_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_checkpoints_workflow_created 
    ON checkpoints(workflow_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_checkpoints_created 
    ON checkpoints(created_at DESC);
```

### Partition Payload Mapping
- **`checkpoint_id`**: Structured UUID (`chk_...`).
- **`schema_version`**: Integer format (currently `1`). Incompatible versions reject deserialization safely.
- **`stage`**: The orchestration lifecycle checkpoint boundary (`INITIAL_INGESTION`, `BASELINE_SYNTHESIS`, `BASELINE_VALIDATED`, `REFLECTION_ITERATION_{n}`, `FINALIZED`, `CANCELLED`, `TIMED_OUT`).
- **`metrics_summary_json`**: Denormalized lightweight summary containing iteration, mutation score, line coverage, and mutant counts for rapid listing without full JSON deserialization.
- **`snapshot_json`**: Full serialized Pydantic v2 `BlackboardSnapshot` containing all 5 partitions: `TargetSpace`, `MutantSpace`, `CriticSpace`, `SuiteSpace`, and `MetricsSpace`.

---

## 3. Configuration & Integration

### Configuration Mechanisms
1. **Environment Variable:**
   ```bash
   export TESTFORGE_CHECKPOINT_DB="qa_artifacts/testforge_checkpoints.db"
   ```
2. **Programmatic Orchestrator Initialization:**
   ```python
   orchestrator = TestForgeOrchestrator(
       target_source_code=code,
       checkpoint_db_path="path/to/checkpoints.db",
       job_id="job_123"
   )
   ```
3. **Direct Blackboard Initialization:**
   ```python
   bb = Blackboard(checkpoint_db_path="path/to/checkpoints.db")
   # or in-memory default:
   bb = Blackboard()  # zero DB overhead
   ```

### Checkpoint Creation Boundaries
Checkpoints are saved at deterministic lifecycle milestones:
1. `INITIAL_INGESTION`: Post-Step 0, after extracting AST symbol signatures, call graph, and blast radius risk categorization.
2. `BASELINE_SYNTHESIS`: Post-Step 1, after synthesizing the initial candidate test suite via Google ADK or fallback generator.
3. `BASELINE_VALIDATED`: Post-Step 2 & 3, after clean pass@1 target execution and baseline line coverage analysis.
4. `REFLECTION_ITERATION_{n}`: Post-Step 4, at the completion of each multi-agent reflection and mutation evaluation cycle.
5. `FINALIZED`: Upon pipeline completion with terminal verdict (`SUCCESS`, `TARGET_SCORE_UNREACHED`, `ZERO_COVERAGE_WARNING`).
6. `CANCELLED`: Upon cooperative cancellation by user request (preserves all partial mutants and test suites).
7. `TIMED_OUT`: Upon exceeding bounded timeout limit (preserves all partial metrics gathered prior to cutoff).

---

## 4. Recovery Semantics & Explicit Limitations

### Safe Restoration Policy
When restoring a checkpoint via `bb.restore_checkpoint(checkpoint_id)` or `bb.restore_from_snapshot(snapshot)`:
- **Atomic Swap:** Partitions are validated through Pydantic v2 schemas and deep-copied into state under `RLock`.
- **Monotonic Revision Advance:** `self._revision = max(current_revision, snapshot.revision) + 1`.
- **Event Provenance:** A `RESTORE` event is appended to the Blackboard change history.
- **Lifecycle Notification:** Dispatches `EventType.CHECKPOINT_RESTORED` to attached observers and the `TraceLogger`.

### Explicit Limitations (Important)
1. **Inspection and Diagnostic Replay:** Recovery in Milestone 1.2 is designed for **diagnostic inspection, status review, state comparison, and fresh workflow seeding**.
2. **No Mid-Instruction Resumption:** Restoring an in-flight checkpoint does **NOT** automatically re-invoke external LLM calls or resume interrupted sandbox subprocesses mid-instruction.
3. **Terminal State Preservation:** A checkpoint for a job that was `CANCELLED`, `TIMED_OUT`, or `FAILED` retains that terminal status; restoring it does not automatically re-run or revert the job to `RUNNING`.

---

## 5. Concurrency, Locking, & Failure Handling

- **SQLite WAL Mode:** Multiple read queries (`GET /api/checkpoints`) can execute concurrently without blocking writing transactions from active worker pipelines.
- **Busy Timeout:** `PRAGMA busy_timeout = 5000` waits up to 5 seconds before returning a lock error.
- **Fail-Safe Memory Isolation:** In default mode (`strict_persistence=False`), any filesystem or SQLite write failure logs an error, dispatches `EventType.CHECKPOINT_FAILED`, and leaves the in-memory Blackboard state 100% operational and uncorrupted.

---

## 6. Performance Benchmarks

Measured on Apple Silicon Darwin arm64 with a representative 50-mutant, 3-iteration Blackboard snapshot:

| Metric | Measured Result | Evaluation |
|---|---|---|
| **Representative Snapshot Size** | **24.02 KB** (24,595 bytes) | Compact, manageable footprint |
| **Save Latency (Mean)** | **0.964 ms** | Sub-millisecond write |
| **Save Latency (P95)** | **1.044 ms** | Predictable transaction time |
| **Load Latency (Mean)** | **0.097 ms** (97 µs) | Near-instantaneous retrieval |
| **Load Latency (P95)** | **0.135 ms** | Sub-millisecond deserialization |
| **In-Memory Update Overhead** | **0.0152 ms** (15 µs) | Zero database overhead when disabled |
| **Update + Checkpoint Overhead** | **0.109 ms** | Negligible impact on pipeline iterations |

---

## 7. REST API Endpoints

The FastAPI backend exposes the following read-only inspection and recovery endpoints:

### `GET /api/checkpoints`
Lists available checkpoints with pagination.
- **Query Params:** `job_id` (optional), `workflow_id` (optional), `limit` (default 50), `offset` (default 0).
- **Response:**
  ```json
  {
    "checkpoints": [
      {
        "checkpoint_id": "chk_601ed8436888",
        "schema_version": 1,
        "job_id": "job_cancelled_002",
        "stage": "CANCELLED",
        "revision": 3,
        "created_at": 1792740983.1,
        "status": "CANCELLED",
        "metrics_summary": {"iteration": 0, "mutation_score": 0.0},
        "snapshot_bytes": 18240
      }
    ],
    "total_count": 7,
    "limit": 50,
    "offset": 0
  }
  ```

### `GET /api/checkpoints/{checkpoint_id}`
Returns full structured metadata, target space, metrics, and mutant summaries without leaking credentials.

### `POST /api/checkpoints/{checkpoint_id}/restore`
Restores the checkpoint into an isolated Blackboard instance and returns the verified restored state dictionary.

---

## 8. Verification Results

- **Unit & Integration Suite (`tests/test_blackboard_persistence.py`):** **22 passed, 0 failed in 3.51s**
- **Existing Blackboard & Cancellation Suites:** **35 passed, 0 failed in 6.68s**
- **Full Regression Suite (`tests/`):** **245 passed, 0 failed in 187.36s (0:03:07)**
- **Static Compilation & Formatting:**
  - `node -c frontend/app.js` -> Exit Code 0
  - `python -m py_compile server.py testforge/blackboard.py testforge/orchestrator.py testforge/persistence.py` -> Exit Code 0
  - `python -m pip check` -> "No broken requirements found."
  - `git diff --check` -> Clean, Exit Code 0
