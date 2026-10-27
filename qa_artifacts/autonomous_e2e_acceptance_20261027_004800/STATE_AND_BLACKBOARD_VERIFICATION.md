# TestForge — State & Blackboard Verification

**Audit Date:** 2026-10-27 01:17:50 IST  
**Artifact Directory:** `qa_artifacts/autonomous_e2e_acceptance_20261027_004800/`  

---

## 1. Blackboard Partition Spaces (MUST 1 Verification)

The TestForge Blackboard (`testforge/blackboard.py`) manages shared state across five strongly typed partitions:

| Partition Space | Type Model | Stored Information | Invariant Enforced |
|---|---|---|---|
| **`TargetSpace`** | `TargetMetadata` | Source code, AST function signatures, module name, source SHA-256 | Immutable after ingestion |
| **`MutantSpace`** | `List[MutantRecord]` | Injected AST faults, status (`KILLED`/`SURVIVED`), execution times, diffs | Deterministic IDs |
| **`CriticSpace`** | `CriticDirectivePayload` | Adversarial diagnoses, targeted mutant IDs, test design directives | Bounded to surviving mutants |
| **`SuiteSpace`** | `GeneratedTestPayload` | Candidate test functions, pass@1 validation status, test code | Syntactically valid AST |
| **`MetricsSpace`** | `HardeningMetrics` | Iteration count, line coverage %, mutation scores %, duration | Monotonically increasing revs |

---

## 2. Invariant Guarantees Verified

1. **Atomic Rollback:** If an agent attempts to write an invalid payload that fails Pydantic schema validation, the entire transaction is rolled back and the revision counter is not incremented.
2. **Monotonic Revisions:** Each valid partition update increments the global monotonic revision counter. Verified across runs (revisions reached 57 in job `eaa31160`).
3. **Point-in-Time Snapshot Isolation:** Calling `get_snapshot()` returns a frozen, immutable `BlackboardSnapshot`. Reading from this snapshot is safe across concurrent threads and processes.
4. **SQLite Checkpoint Persistence:** Every major workflow stage (`INITIAL_INGESTION`, `BASELINE_SYNTHESIS`, `BASELINE_VALIDATED`, `REFLECTION_ITERATION_*`, `FINALIZED`) automatically commits a complete snapshot to `qa_artifacts/testforge_checkpoints.db`.
5. **State Restoration & Replay:** Checkpoints can be re-instantiated into an isolated Blackboard memory instance for verification and side-by-side diffing without modifying historical records.
