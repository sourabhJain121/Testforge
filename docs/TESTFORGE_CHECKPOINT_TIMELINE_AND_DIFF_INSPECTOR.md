# TestForge — Checkpoint Timeline, Deterministic Diff Inspector & Recovery UI
**Milestone 1.3 Technical Documentation & Operational Guide**  
*Project: TestForge — Autonomous Agentic Unit-Test Hardening System*  
*Authors: Sourabh & Shreshth | Autonomous Agentic AI*  
*Environment: Python 3.13 (`.venv-release`) | macOS Apple Silicon (arm64)*  
*Verified Release Gate: October 2026*

---

## 1. Executive Summary & Objective

Milestone 1.3 delivers the user-facing inspection, comparison, and recovery interface for the persistent SQLite Blackboard checkpointing engine implemented in Milestone 1.2. 

Prior to Milestone 1.3, Blackboard snapshots were automatically persisted at every significant pipeline boundary (`INITIAL_INGESTION`, `BASELINE_SYNTHESIS`, `BASELINE_VALIDATED`, `REFLECTION_ITERATION_{n}`, `FINALIZED`, `CANCELLED`, `TIMED_OUT`), but users lacked:
1. An interactive, chronological timeline to inspect historical state transitions.
2. A deterministic semantic diff engine capable of comparing any two point-in-time Blackboard snapshots across all five typed partitions (`TargetSpace`, `SuiteSpace`, `MutantSpace`, `MetricsSpace`, `CriticSpace`).
3. A safe, non-destructive recovery workflow allowing state replay and verification without corrupting active pipelines or overwriting historical database records.

Milestone 1.3 completes this capability with zero external frontend dependencies (pure Vanilla ES6+ JavaScript, semantic HTML5, and responsive CSS3), automated end-to-end Chrome CDP verification, and exhaustive unit and integration tests.

---

## 2. Architecture & Design Principles

```mermaid
graph TD
    UI[Frontend Dashboard: Checkpoint Tab] -->|GET /api/checkpoints| S_LIST[server.py: list_checkpoints]
    UI -->|GET /api/checkpoints/{id}| S_DET[server.py: get_checkpoint_details]
    UI -->|GET /api/checkpoints/diff| S_DIFF[server.py: diff_checkpoints_endpoint]
    UI -->|POST /api/checkpoints/{id}/restore| S_RESTORE[server.py: restore_checkpoint_endpoint]

    S_LIST --> DB[(SQLite testforge_checkpoints.db WAL)]
    S_DET --> DB
    S_DIFF --> DIFF_ENG[testforge/diff_inspector.py: DeterministicDiffInspector]
    DIFF_ENG --> DB
    S_RESTORE --> ISO_BB[Isolated Blackboard Instance]
    ISO_BB --> DB
```

### 2.1 Core Architectural Guarantees
1. **Zero State Mutation on Read**: Viewing, inspecting, filtering, or comparing checkpoints is strictly read-only and never modifies in-memory state or SQLite records.
2. **Deterministic Comparison Engine**:
   - Dictionary keys are sorted at all traversal levels to ensure byte-for-byte and semantic determinism regardless of Python dict insertion order or JSON serialization variances.
   - Deep recursive comparison across nested objects, arrays, and primitive leaf values.
   - Explicit discrimination between missing fields, explicit `null` (`None`), empty collections (`{}`, `[]`), and zero/false values.
3. **Specialized Mutant Lifecycle Tracking**:
   - Compares AST mutants using deterministic `mutant_id` indexing rather than brittle array indexing.
   - Computes explicit transitions: `newly_generated`, `newly_killed` (transitions from `SURVIVED` ➔ `KILLED`), `newly_survived`, and status flips.
4. **Isolated State Recovery & Non-Destructive Replay**:
   - Restoring a checkpoint deserializes the snapshot into an **isolated, fresh Blackboard instance**.
   - Verifies all Pydantic v2 partition invariants upon load.
   - Confirms that restoration does **not** resume or mutate active concurrent workflows unless explicitly commanded by orchestration.
5. **Defense-in-Depth UI Security**:
   - Untrusted inputs (such as generated test code, mutant diffs, and error strings) are rendered exclusively via safe DOM manipulation APIs (`document.createElement`, `textContent`, `setAttribute`).
   - No `innerHTML` interpolation of user-controlled or model-generated payloads, eliminating Cross-Site Scripting (XSS) vectors.

---

## 3. Implemented API Contracts

### 3.1 `GET /api/checkpoints`
Lists saved Blackboard checkpoints with metadata, stages, and pagination.

* **Query Parameters**:
  * `job_id` (optional string): Filter by specific hardening job identifier.
  * `workflow_id` (optional string): Filter by workflow instance.
  * `limit` (integer, default 50): Number of records per page.
  * `offset` (integer, default 0): Record offset.
* **Response Status**: `200 OK`
* **Response Payload Schema**:
```json
{
  "checkpoints": [
    {
      "checkpoint_id": "chk_c7288ba79d39",
      "schema_version": 1,
      "job_id": "job_0c88ae57",
      "workflow_id": null,
      "stage": "FINALIZED",
      "revision": 13,
      "created_at": 1792683900.12,
      "status": "SUCCESS",
      "metrics_summary": {
        "final_mutation_score": 88.5,
        "lines_covered": 22,
        "current_iteration": 2
      },
      "snapshot_bytes": 22371
    }
  ],
  "total_count": 30,
  "limit": 50,
  "offset": 0
}
```

---

### 3.2 `GET /api/checkpoints/{checkpoint_id}`
Retrieves full metadata and structured partition info for a specific checkpoint.

* **Path Parameters**:
  * `checkpoint_id` (string, required): e.g. `chk_c7288ba79d39`
* **Response Status**: `200 OK` (or `404 Not Found`)
* **Response Payload Schema**:
```json
{
  "metadata": {
    "checkpoint_id": "chk_c7288ba79d39",
    "schema_version": 1,
    "job_id": "job_0c88ae57",
    "workflow_id": null,
    "stage": "FINALIZED",
    "revision": 13,
    "created_at": 1792683900.12,
    "status": "SUCCESS",
    "metrics_summary": { "final_mutation_score": 88.5 }
  },
  "target": {
    "target_module_path": "samples.discount",
    "target_file_path": "samples/discount.py",
    "functions": ["calculate_discount"],
    "classes": []
  },
  "suite": {
    "test_module_path": "test_target.py",
    "active_provider": "gemini-3.6-flash",
    "current_test_code": "def test_vip_discount():\n    assert calculate_discount(100, 'VIP') == 80\n"
  },
  "mutant": {
    "mutants_generated": 10,
    "mutants_killed": 9,
    "mutants_survived": 1,
    "mutants": [
      {
        "mutant_id": "MUT_ARITH_OP_001",
        "mutation_type": "ARITH_OP",
        "line_number": 14,
        "status": "KILLED",
        "unified_diff": "- discount = total * 0.2\n+ discount = total / 0.2"
      }
    ]
  },
  "metrics": {
    "current_iteration": 2,
    "max_iterations": 3,
    "target_mutation_score": 85.0,
    "final_mutation_score": 88.5,
    "lines_covered": 22,
    "final_hardening_status": "CONVERGED_SUCCESS"
  },
  "critic": {
    "critic_directives": ["Target boundary conditions for volume thresholds > 1000"],
    "notes": "Adversarial evaluation confirmed coverage of tiered discount edge cases."
  },
  "snapshot": { "...": "Complete raw BlackboardSnapshot object" }
}
```

---

### 3.3 `GET /api/checkpoints/diff`
Computes a deterministic, partition-aware semantic diff between any two checkpoints.

* **Route Precedence**: Explicitly defined *before* `@app.get("/api/checkpoints/{checkpoint_id}")` to prevent FastAPI parameter shadowing.
* **Query Parameters**:
  * `base_id` (string, required): e.g. `chk_06dc3d53a61d` (Base A)
  * `target_id` (string, required): e.g. `chk_c7288ba79d39` (Target B)
  * `include_unchanged` (boolean, optional, default `false`): When true, includes identical fields marked as `UNCHANGED`.
* **Response Status**: `200 OK` (or `404 Not Found`, `422 Unprocessable Entity`)
* **Response Payload Schema**:
```json
{
  "base_checkpoint_id": "chk_06dc3d53a61d",
  "target_checkpoint_id": "chk_c7288ba79d39",
  "base_stage": "INITIAL_INGESTION",
  "target_stage": "FINALIZED",
  "summary": {
    "total_differences": 7,
    "added_count": 2,
    "removed_count": 0,
    "changed_count": 5,
    "missing_vs_null_count": 0,
    "unchanged_count": 14
  },
  "partition_summaries": {
    "target": { "total": 0, "added": 0, "removed": 0, "changed": 0, "missing_vs_null": 0, "unchanged": 4 },
    "suite": { "total": 2, "added": 1, "removed": 0, "changed": 1, "missing_vs_null": 0, "unchanged": 2 },
    "mutant": { "total": 3, "added": 1, "removed": 0, "changed": 2, "missing_vs_null": 0, "unchanged": 0 },
    "metrics": { "total": 2, "added": 0, "removed": 0, "changed": 2, "missing_vs_null": 0, "unchanged": 5 }
  },
  "differences": [
    {
      "path": "metrics.final_mutation_score",
      "partition": "metrics",
      "change_type": "CHANGED",
      "base_value": 0.0,
      "target_value": 88.5,
      "description": "Value changed from 0.0 to 88.5"
    },
    {
      "path": "suite.current_test_code",
      "partition": "suite",
      "change_type": "CHANGED",
      "base_value": "",
      "target_value": "def test_vip_discount(): ...",
      "description": "Synthesized hardened test assertions added"
    }
  ],
  "mutant_delta": {
    "newly_generated": [],
    "newly_killed": [
      {
        "mutant_id": "MUT_ARITH_OP_001",
        "operator": "ARITH_OP",
        "line_number": 14,
        "diff": "- discount = total * 0.2\n+ discount = total / 0.2"
      }
    ],
    "newly_survived": [],
    "status_changes": [
      {
        "mutant_id": "MUT_ARITH_OP_001",
        "from_status": "SURVIVED",
        "to_status": "KILLED"
      }
    ]
  }
}
```

---

### 3.4 `POST /api/checkpoints/{checkpoint_id}/restore`
Safely deserializes and restores a checkpoint into an isolated Blackboard instance for diagnostic inspection and state verification.

* **Path Parameters**:
  * `checkpoint_id` (string, required): e.g. `chk_c7288ba79d39`
* **Response Status**: `200 OK` (or `404 Not Found`)
* **Response Payload Schema**:
```json
{
  "status": "restored",
  "checkpoint_id": "chk_c7288ba79d39",
  "revision": 13,
  "stage": "FINALIZED",
  "restored_state": {
    "target_module_path": "samples.discount",
    "test_module_path": "test_target.py",
    "current_test_code": "def test_vip_discount(): ...",
    "current_iteration": 2,
    "max_iterations": 3,
    "target_mutation_score": 85.0
  }
}
```

---

## 4. Deterministic Diff Engine Specification

The comparison engine resides in `testforge/diff_inspector.py`.

### 4.1 Diff Classification Rules
For any field path `P` between Base object `B` and Target object `T`:

| Condition | Change Type | Semantic Meaning |
|---|---|---|
| `P in T and P not in B` (and `T[P] is not None`) | `ADDED` | Field newly introduced in target checkpoint |
| `P in B and P not in T` (and `B[P] is not None`) | `REMOVED` | Field removed or pruned in target checkpoint |
| `P in B and P in T and B[P] != T[P]` | `CHANGED` | Value modified (scalars, strings, numbers, booleans) |
| `(P not in B and T[P] is None) or (B[P] is None and P not in T)` | `MISSING_VS_NULL` | Distinguishes absence of key from explicit null value |
| `P in B and P in T and B[P] == T[P]` | `UNCHANGED` | Value strictly identical in both snapshots |

### 4.2 Handling of Edge Cases
1. **Dictionary Key Ordering Invariance**:
   Dict keys are sorted using `sorted(set(B.keys()) | set(T.keys()))`. Dictionaries `{"a": 1, "b": 2}` and `{"b": 2, "a": 1}` produce 0 differences.
2. **Empty Collections vs Missing Keys**:
   An empty dict `{}` or list `[]` is treated as a concrete collection value. A transition from missing (`_SENTINEL_MISSING`) to `{}` is flagged as `ADDED` with value `{}`.
3. **AST Mutant Lists**:
   Mutant lists are indexed by `mutant_id` (e.g. `MUT_ARITH_OP_001`). If a mutant is moved to a different array position due to filtering, the diff engine matches it by its unique ID and only flags genuine mutations or kill status changes.

---

## 5. UI Components & Frontend Architecture

The user interface is integrated into `frontend/index.html` and managed by `frontend/app.js`:

### 5.1 Timeline Stream (`#checkpoint-cards-stream`)
* Chronological listing of checkpoint cards.
* Filter controls for:
  * **Workflow Stage**: All, `INITIAL_INGESTION`, `BASELINE_SYNTHESIS`, `BASELINE_VALIDATED`, `REFLECTION_ITERATION`, `FINALIZED`, `CANCELLED`, `TIMED_OUT`.
  * **Status**: All, `SUCCESS`, `IN_PROGRESS`, `CANCELLED`, `TIMED_OUT`, `FAILED`.
  * **Job ID**: Real-time substring filter.
  * **Sort Order**: Newest First / Oldest First.
* Interactive card actions:
  * `🔍 Inspect`: Selects card and populates the Structured Inspector.
  * `Set Base (A)`: Sets this checkpoint as Base for diff comparison.
  * `Set Target (B)`: Sets this checkpoint as Target for diff comparison.
  * `↩ Restore...`: Opens safe modal for confirmed state restoration.

### 5.2 Structured Detail Inspector (`#view-cp-detail`)
* Partitions displayed in structured, syntax-highlighted cards:
  * **Target Space**: module, file path, functions list, classes list.
  * **Suite Space**: active provider, test module path, syntax-highlighted candidate test code.
  * **Mutant Space**: generated/killed/survived metric pills, mutant table with operators and lines.
  * **Metrics Space**: mutation score %, covered lines, statements, hardening status badge.
  * **Critic Space**: adversarial feedback directives, reflection suggestions, approval status.

### 5.3 Deterministic Diff Viewer (`#view-cp-diff`)
* Comparison header displaying `Base (A)` ➔ `Target (B)` and total difference count badge.
* Color-coded summary tags:
  * `+ N Added` (Emerald)
  * `- N Removed` (Rose)
  * `~ N Changed` (Amber)
  * `∅ N Missing vs Null` (Purple)
* Mutant State Transitions container highlighting newly killed, generated, or survived mutants.
* Path-indexed semantic diff list showing side-by-side Base vs Target value boxes.

### 5.4 Safe Recovery Modal (`#restore-modal`)
* Explains the exact target checkpoint ID, stage, revision, and creation timestamp.
* Highlights safety notices:
  * "Restores the point-in-time Blackboard partition state into an isolated Blackboard instance for diagnostic inspection, replay verification, and state comparison."
  * "Historical database records remain immutable."
* Requires explicit user click on **"Confirm & Restore Snapshot"** before making network request.
* Displays success alert and updates UI state upon backend verification.

---

## 6. Automated Verification Evidence

### 6.1 Unit Tests (`tests/test_checkpoint_diff.py`)
11 dedicated unit test cases verifying all diff engine edge cases:
* `test_added_field`: Added scalar in nested target partition.
* `test_removed_field`: Removed field from base partition.
* `test_changed_scalar_value`: Scalar value modification.
* `test_nested_dictionary_changes`: Multi-level nested dictionary traversal.
* `test_missing_vs_null_discrimination`: Missing in base vs null in target, and vice-versa.
* `test_empty_object_vs_missing_object`: `{}` vs missing key.
* `test_dictionary_key_ordering_invariance`: Permuted dictionary keys produce identical diff outputs.
* `test_list_changes_positional`: List element mutations and insertions.
* `test_mutant_list_diff_and_transitions`: Tracks newly killed, generated, and survived mutants.
* `test_malformed_data_handling`: Heterogeneous types and non-dict primitives.
* `test_partition_categorization`: Grouping across metadata, target, suite, mutant, metrics, critic, and other.

*Result*: **11 passed in 0.07s**.

### 6.2 API Integration Tests (`tests/test_checkpoint_api_diff.py`)
5 integration tests testing FastAPI endpoints with live SQLite fixture:
* `test_get_checkpoint_details_enhanced`: Verifies metadata, suite, mutant, metrics, and raw snapshot retrieval.
* `test_checkpoint_diff_api_success`: Full diff execution between two real checkpoints.
* `test_checkpoint_diff_api_unknown_base`: Returns HTTP 404 for nonexistent base checkpoint ID.
* `test_checkpoint_diff_api_missing_param`: Returns HTTP 422 for missing query parameters.
* `test_restore_endpoint_success`: Validates isolated Blackboard restoration and restored state structure.

*Result*: **5 passed in 3.26s**.

### 6.3 Browser E2E CDP Verification (`qa_artifacts/checkpoint_ui_browser_audit.py`)
Exercised inside headless Chrome (version 131+) via Chrome DevTools Protocol over WebSockets:
1. `01_testforge_dashboard_loaded.png`: Dashboard loaded at `http://127.0.0.1:8000`.
2. `02_checkpoint_tab_active.png`: Switched to `💾 Checkpoint Timeline & Diff` tab.
3. `03_checkpoint_cards_stream.png`: Rendered 30 persistent checkpoint cards from SQLite database.
4. `04_checkpoint_detail_inspected.png`: Inspected `chk_c7288ba79d39`, rendered structured partition cards.
5. `05_checkpoint_diff_results.png`: Compared Base `chk_06dc3d53a61d` vs Target `chk_c7288ba79d39`, rendered 7 semantic diff items.
6. `06_restore_confirmation_modal.png`: Opened restore confirmation modal with safety notice.
7. `07_restore_success_alert.png`: Confirmed restoration, verified alert `✓ Successfully restored checkpoint chk_c7288ba79d39 (Stage: FINALIZED, Revision: 13)`.

*Artifacts saved to*: `qa_artifacts/technical_report_20261023_132239/screenshots/`.
