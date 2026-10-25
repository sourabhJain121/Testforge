# TestForge — Phase 2: Typed Blackboard State Architecture

**Document**: `docs/PHASE2_BLACKBOARD.md`  
**Phase**: Phase 2 (Blackboard State Architecture)  
**Date**: October 2026  
**Status**: COMPLETED  
**Runtime Environment**: Python 3.13.17 (Isolated development environment)  

---

## 1. Executive Summary & Architecture

Phase 2 replaces the unstructured, linear procedural mutation of `TestForgeState` with a **strongly-typed, thread-safe, multi-partition Blackboard architecture (`testforge/blackboard.py`)**.

The Blackboard decouples state storage from procedural orchestration, introducing discrete typed knowledge partitions, fail-closed atomic validation, point-in-time consistent snapshots, defensive deep-copy isolation, safe provenance history, and priority-ordered observer subscriptions.

```mermaid
flowchart TD
    subgraph BB["TestForge Blackboard State Store (testforge/blackboard.py)"]
        direction TB
        subgraph Partitions["Typed State Partitions (Pydantic v2 Models)"]
            T["TargetSpace\n(Code, AST Symbols, Blast Risk, Call Graph)"]
            M["MutantSpace\n(AST Mutants, Killed/Survived, Diff Lists)"]
            C["CriticSpace\n(Adversarial Directives, Failure Mechanisms, Reflection Notes)"]
            S["SuiteSpace\n(Candidate Test Suite, Baseline Validation, Provider)"]
            K["MetricsSpace\n(Iteration Metrics, Line Coverage, Mutation Score, Status)"]
        end
        Lock["Re-entrant Lock (threading.RLock)\nThread-Safe Atomic Mutations"]
        History["Monotonic Revision Counter & Sanitized History Log"]
    end

    subgraph Controller["Blackboard Controller Operations"]
        Read["get_target_space() / get_mutant_space() / ...\n(Defensive Deep Copies)"]
        Update["update_partition(name, updates)\n(Atomic Pydantic Validation)"]
        Snap["get_snapshot()\n(Consistent Point-in-Time View)"]
        Sub["subscribe(handler, partitions, priority)\n(Deterministic Notification Order)"]
    end

    subgraph Pipeline["TestForge Pipeline & Observers"]
        Orchestrator["TestForgeOrchestrator"] -->|Update Partitions| Update
        Update --> Lock
        Update --> History
        Update -.->|Dispatch Events| Observers["Observer Handlers\n(Failure Isolated)"]
        Update -.->|Bridge State Changes| Callbacks["Phase 1 CallbackRegistry"]
        Controller -->|sync_to_state()| LegacyState["TestForgeState\n(100% Backward Compatible)"]
    end
```

---

## 2. Partition Models and Responsibilities

The Blackboard state is structured into 5 typed partitions conforming to Pydantic v2 schemas:

### 2.1 `TargetSpace`
- **Responsibilities**: Houses the target module under test, AST metadata, symbol signatures, call graphs, and blast radius risk scores.
- **Fields**:
  - `target_module_path: str = "target.py"`
  - `target_source_code: str = ""`
  - `target_file_path: Optional[str] = None`
  - `target_lines: Optional[List[int]] = None`
  - `functions: List[str] = Field(default_factory=list)`
  - `classes: List[str] = Field(default_factory=list)`
  - `blast_risk: str = "LOW"`
  - `source_sha: str = ""`
  - `line_count: int = 0`
  - `dependencies: List[str] = Field(default_factory=list)`

### 2.2 `MutantSpace`
- **Responsibilities**: Stores generated AST mutants, execution statuses (`KILLED`, `SURVIVED`, `TIMEOUT`, `ERROR`), and surviving unified diffs.
- **Fields**:
  - `mutants: List[MutantRecord] = Field(default_factory=list)`
  - `mutants_generated: int = 0`
  - `mutants_executed: int = 0`
  - `mutants_killed: int = 0`
  - `mutants_survived: int = 0`
  - `mutation_execution_errors: int = 0`
  - `current_mutation_score: float = 0.0`
  - `surviving_mutant_diffs: List[str] = Field(default_factory=list)`

### 2.3 `CriticSpace`
- **Responsibilities**: Stores adversarial failure directives from the critic agent, diagnosed failure mechanisms, and historical reflection notes.
- **Fields**:
  - `critic_directives: List[str] = Field(default_factory=list)`
  - `latest_directive: str = ""`
  - `reflection_notes: List[str] = Field(default_factory=list)`
  - `failure_mechanisms: Dict[str, str] = Field(default_factory=dict)`

### 2.4 `SuiteSpace`
- **Responsibilities**: Houses candidate test suites, pass@1 baseline validation results, and active LLM provider designations.
- **Fields**:
  - `test_module_path: str = "test_target.py"`
  - `current_test_code: str = ""`
  - `baseline_test_code: str = ""`
  - `hardened_test_code: str = ""`
  - `active_provider: str = "Google GenAI Live"`
  - `baseline_tests_generated: int = 0`
  - `baseline_tests_executed: int = 0`
  - `baseline_passed: bool = False`
  - `baseline_tests_passed: int = 0`
  - `baseline_tests_failed: int = 0`

### 2.5 `MetricsSpace`
- **Responsibilities**: Houses convergence benchmarks, line coverage percentages, statement counts, iteration history, and termination reasons.
- **Fields**:
  - `current_iteration: int = 0`
  - `max_iterations: int = 3`
  - `target_mutation_score: float = 85.0`
  - `baseline_line_coverage: float = 0.0`
  - `lines_covered: int = 0`
  - `num_statements: int = 0`
  - `history: List[IterationMetrics] = Field(default_factory=list)`
  - `final_mutation_score: float = 0.0`
  - `reflection_iterations_performed: int = 0`
  - `final_hardening_status: str = "INITIALIZING"`
  - `terminated: bool = False`
  - `termination_reason: str = ""`
  - `hardware_info: Dict[str, Any] = Field(default_factory=dict)`

---

## 3. Public Blackboard API

The `Blackboard` controller exposes explicit, typed operations:

### 3.1 Partition Accessors
- `get_target_space() -> TargetSpace`: Returns defensive deep copy of `TargetSpace`.
- `get_mutant_space() -> MutantSpace`: Returns defensive deep copy of `MutantSpace`.
- `get_critic_space() -> CriticSpace`: Returns defensive deep copy of `CriticSpace`.
- `get_suite_space() -> SuiteSpace`: Returns defensive deep copy of `SuiteSpace`.
- `get_metrics_space() -> MetricsSpace`: Returns defensive deep copy of `MetricsSpace`.
- `get_partition(partition_name: str) -> BaseModel`: Dynamic partition accessor.

### 3.2 Partition Updates
- `update_target_space(**kwargs) -> TargetSpace`
- `update_mutant_space(**kwargs) -> MutantSpace`
- `update_critic_space(**kwargs) -> CriticSpace`
- `update_suite_space(**kwargs) -> SuiteSpace`
- `update_metrics_space(**kwargs) -> MetricsSpace`
- `update_partition(partition_name: str, updates: Union[Dict, BaseModel], event_type: str = "UPDATE") -> BaseModel`: Atomically validates candidate update dictionary against target schema before committing. Raises `pydantic.ValidationError` on invalid schemas, leaving internal state completely unchanged.

### 3.3 Snapshots & History
- `get_snapshot() -> BlackboardSnapshot`: Produces a consistent, point-in-time snapshot containing the current revision and deep copies of all 5 partitions.
- `get_history() -> List[BlackboardEvent]`: Returns an immutable chronological list of state changes with monotonic revision numbers.

### 3.4 Subscriptions
- `subscribe(handler, partitions=None, priority=100, name=None) -> str`: Registers an observer handler with optional partition filtering. Returns unique `subscription_id`.
- `unsubscribe(subscription_id: str) -> bool`: Removes active subscription.
- `clear_subscriptions()`: Flushes all subscriptions.

### 3.5 Interoperability
- `to_testforge_state() -> TestForgeState`: Exports partition state into a `TestForgeState` instance.
- `from_testforge_state(state: TestForgeState, callback_registry=None) -> Blackboard`: Factory initializing Blackboard partitions from existing state.
- `sync_to_state(state: TestForgeState)`: In-place synchronization updating an existing `TestForgeState` instance.

---

## 4. Validation and Concurrency Guarantees

1. **Atomic Validation**:
   - Updates are merged into candidate dictionaries and validated against the partition's Pydantic schema **before** state assignment.
   - If validation fails, `ValidationError` is raised immediately; the partition is **not** partially modified, and the revision counter is **not** incremented.
2. **Thread Safety**:
   - All partition reads, mutations, snapshot generations, and subscription operations are guarded by a re-entrant lock (`threading.RLock`).
   - Multiple concurrent worker threads can update partitions without data races or inconsistent state reads.
3. **Deadlock Prevention**:
   - Observer notifications execute **outside** the `_lock`.
   - Matching subscribers are captured into a local list under lock, and then invoked sequentially after releasing the lock.
   - If an observer invokes Blackboard methods (`get_snapshot()`, `update_*`) inside its callback, no deadlock can occur.
4. **Defensive Isolation**:
   - Accessors and snapshots return deep copies (`model_copy(deep=True)`).
   - Callers mutating returned objects cannot alter internal Blackboard state.
5. **Sanitized History**:
   - History metadata records summaries (lengths, counts, statuses) rather than full source code strings or secret credentials. String values pass through `redact_sensitive_data()`.

---

## 5. Incremental Orchestrator Integration

Integration with `TestForgeOrchestrator` is incremental and preserves 100% backward compatibility:

1. **Initialization**:
   - `TestForgeOrchestrator.__init__` accepts an optional `blackboard: Optional[Blackboard] = None`.
   - If omitted, it automatically instantiates `self.blackboard = Blackboard.from_testforge_state(self.state, callback_registry=self.callbacks)`.
2. **Incremental State Routing**:
   - Extracted functions and blast risk are routed to `self.blackboard.update_target_space()`.
   - Candidate test code and baseline execution counts are routed to `self.blackboard.update_suite_space()`.
   - Baseline line coverage and statement metrics are routed to `self.blackboard.update_metrics_space()`.
   - Concurrently evaluated mutants and scores are routed to `self.blackboard.update_mutant_space()`.
   - Critic failure directives and reflection notes are routed to `self.blackboard.update_critic_space()`.
   - Final status, iteration metrics, and termination reasons are routed to `self.blackboard.update_metrics_space()`.
3. **In-Place Synchronization**:
   - After each major Blackboard mutation, `self.blackboard.sync_to_state(self.state)` updates `self.state` in-place.
   - Any external callers, UI components (`server.py`, `app.py`), or benchmark runners accessing `orchestrator.state` continue to work without modification.
4. **Lifecycle Callback Bridge**:
   - If a Phase 1 `CallbackRegistry` is connected to the Blackboard, partition mutations automatically dispatch `STATE_CHANGE` lifecycle events to the registry.

---

## 6. Verification and Test Results

All tests executed in the isolated Python 3.13 virtual environment (`venv_313`).

### 6.1 Focused Blackboard Suite (18 tests)
Command:
```bash
/Users/sourabh/.gemini/antigravity-ide/brain/05f0de02-c90e-40d7-bf92-0819372e0bac/scratch/venv_313/bin/pytest tests/test_blackboard.py -v
```
**Outcome: 18 passed in 1.60s (100% pass rate).**

```text
tests/test_blackboard.py::TestBlackboardCore::test_construction_with_default_partition_state PASSED [  5%]
tests/test_blackboard.py::TestBlackboardCore::test_valid_partition_updates PASSED [ 11%]
tests/test_blackboard.py::TestBlackboardCore::test_pydantic_validation_failures PASSED [ 16%]
tests/test_blackboard.py::TestBlackboardCore::test_invalid_updates_leave_existing_state_unchanged PASSED [ 22%]
tests/test_blackboard.py::TestBlackboardCore::test_partition_isolation PASSED [ 27%]
tests/test_blackboard.py::TestBlackboardCore::test_snapshot_consistency PASSED [ 33%]
tests/test_blackboard.py::TestBlackboardCore::test_history_ordering_and_revision_increments PASSED [ 38%]
tests/test_blackboard.py::TestBlackboardCore::test_defensive_copies_prevent_external_mutation PASSED [ 44%]
tests/test_blackboard.py::TestBlackboardCore::test_safe_metadata_sanitization PASSED [ 50%]
tests/test_blackboard.py::TestBlackboardSubscriptions::test_subscriber_registration_and_notification PASSED [ 55%]
tests/test_blackboard.py::TestBlackboardSubscriptions::test_subscriber_unregistration PASSED [ 61%]
tests/test_blackboard.py::TestBlackboardSubscriptions::test_filtering_subscriptions_by_partition PASSED [ 66%]
tests/test_blackboard.py::TestBlackboardSubscriptions::test_deterministic_subscriber_notification_order PASSED [ 72%]
tests/test_blackboard.py::TestBlackboardSubscriptions::test_subscriber_exception_isolation PASSED [ 77%]
tests/test_blackboard.py::TestBlackboardConcurrency::test_concurrent_updates_from_multiple_threads PASSED [ 83%]
tests/test_blackboard.py::TestBlackboardInterop::test_to_and_from_testforge_state PASSED [ 88%]
tests/test_blackboard.py::TestBlackboardInterop::test_sync_to_state PASSED [ 94%]
tests/test_blackboard.py::TestBlackboardInterop::test_orchestrator_integration PASSED [100%]
```

### 6.2 Full Regression Suite (82 tests)
Command:
```bash
/Users/sourabh/.gemini/antigravity-ide/brain/05f0de02-c90e-40d7-bf92-0819372e0bac/scratch/venv_313/bin/pytest tests/ -v
```
**Outcome: 82 passed in 129.22s (2m 09s) (100% pass rate, 0 warnings).**
- Covers all 18 Blackboard tests, 40 Security & Callback tests, and 24 original baseline tests (mutator, sandbox, Apple Silicon MLX GPU neural classifier, blast radius analyzer, Mode C ingestion regression tests).

### 6.3 Standalone Hardened Suite (21 tests)
Command:
```bash
/Users/sourabh/.gemini/antigravity-ide/brain/05f0de02-c90e-40d7-bf92-0819372e0bac/scratch/venv_313/bin/pytest test_hardened.py -v
```
**Outcome: 21 passed in 0.02s (100% pass rate).**

---

## 7. Improvement Review Findings & Remediations

1. **Deadlock Prevention in Observer Callbacks**:
   - *Design review*: If notifications are dispatched while holding `_lock`, a subscriber that queries `bb.get_target_space()` or triggers an update could deadlock if a non-reentrant lock or inter-thread handoff is involved.
   - *Remediation*: Captured subscriber snapshots and dispatched all notifications **after** releasing the lock.
2. **Pytest Collection Warnings on State Classes**:
   - *Finding*: Pytest issued `PytestCollectionWarning` on `TestForgeState` and `TestForgeOrchestrator` because their class names start with `Test`.
   - *Remediation*: Added `__test__ = False` to both class definitions to cleanly suppress collection warnings without renaming symbols.
3. **Deep-Copy Isolation**:
   - *Design review*: Returning references to internal Pydantic models allowed callers to bypass validation and mutate internal lists directly.
   - *Remediation*: Enforced `.model_copy(deep=True)` across all partition getters, history queries, and snapshot generations.
4. **Safe Metadata for History Entries**:
   - *Design review*: Raw updates to `target_source_code` or `current_test_code` could inflate history memory and leak private source code.
   - *Remediation*: Implemented `_extract_safe_change_metadata()` to summarize large text fields by length and lists by count, while masking credentials with `redact_sensitive_data()`.

---

## 8. Rollback Strategy

If Blackboard state routing causes unexpected side effects in downstream tools:
- **Opt-in / Fallback**: `TestForgeOrchestrator` maintains full synchronization with `self.state`. If Blackboard routing needs to be disabled, the orchestrator can operate directly on `self.state` without breaking callers.
- **Git Reversion**: Phase 2 changes are isolated to `testforge/blackboard.py`, `tests/test_blackboard.py`, and clean routing calls in `testforge/orchestrator.py`.

---

## 9. Environment Preservation Evidence

- **Primary Virtual Environment (`/Users/sourabh/TestForge/.venv`)**:
  - Python Version: **Python 3.14.9** (Preserved, untouched).
  - Pip Check: `No broken requirements found.`
- **Project `requirements.txt`**:
  - Remained completely untouched and unmodified.
- **Isolated Development Environment (`scratch/venv_313`)**:
  - Python Version: **Python 3.13.17**.
  - All Phase 2 development and testing conducted exclusively within this isolated environment.
