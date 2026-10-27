# BLACKBOARD DATA FLOW & SHARED STATE ARCHITECTURE TRACE

**Repository:** `/Users/sourabh/TestForge`  
**Audit Directory:** `qa_artifacts/must_requirements_audit_20261027_102500/`  
**Date:** October 27, 2026  
**Auditor Role:** Senior Software Architect & QA Auditor  

---

## 1. Architectural Foundations of the TestForge Blackboard

The TestForge `Blackboard` (`testforge/blackboard.py`) is a thread-safe, revision-controlled shared-memory state coordinator partitioned into five strongly-typed spaces.

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                             TESTFORGE BLACKBOARD                                 │
├─────────────────┬─────────────────┬─────────────────┬──────────────┬─────────────┤
│  TargetSpace    │   SuiteSpace    │   MutantSpace   │ CriticSpace  │MetricsSpace │
├─────────────────┼─────────────────┼─────────────────┼──────────────┼─────────────┤
│ • target_source │ • current_tests │ • mutants list  │ • directives │ • score %   │
│ • module_path   │ • baseline_tests│ • killed/surv   │ • mechanisms │ • coverage %│
│ • functions/cls │ • pass@1 status │ • AST diffs     │ • guidance   │ • history   │
│ • blast_risk    │ • active_prov   │ • equiv_status  │ • notes      │ • status    │
└─────────────────┴─────────────────┴─────────────────┴──────────────┴─────────────┘
         ▲                 ▲                 ▲               ▲              ▲
         │ (write)         │ (write/read)    │ (write/read)  │ (write/read) │ (write)
┌────────┴──────┐ ┌────────┴──────┐ ┌────────┴──────┐ ┌──────┴──────┐ ┌─────┴───────┐
│ Ingestion     │ │ Google ADK    │ │ AST Mutator & │ │ CrewAI      │ │ Metrics     │
│ Manager       │ │ Generator     │ │ Sandbox       │ │ Critic      │ │ Aggregator  │
└───────────────┘ └───────────────┘ └───────────────┘ └─────────────┘ └─────────────┘
                                         │
                                         ▼ (All-or-nothing transactional snapshots)
                          ┌─────────────────────────────┐
                          │ SQLite Persistence Storage  │
                          │ (testforge_checkpoints.db)  │
                          └─────────────────────────────┘
```

---

## 2. End-to-End Execution Trace: Step-by-Step Data Flow

Tracing a live execution of `samples/discount.py` (Job `5f996812` / fresh live run):

### Step 1: Instantiation & Shared State Creation
- **Where Created:** In `server.py:725-742`, when `POST /api/harden/start` is invoked, a worker thread calls `TestForgeOrchestrator(checkpoint_db_path=DEFAULT_CHECKPOINT_DB_PATH)`.
- **Initialization:** In `testforge/orchestrator.py:192-205`, `TestForgeOrchestrator.__init__` instantiates:
  ```python
  self.blackboard = Blackboard(
      checkpoint_db_path=self.checkpoint_db_path,
      callback_registry=self.callbacks
  )
  ```
- **Initial State:** All five spaces are initialized as empty typed Pydantic models. Monotonic revision counter begins at `0`.

---

### Step 2: Target Ingestion (`INITIAL_INGESTION`)
- **Agent / Component:** `IngestionManager` & `BlastRadiusAnalyzer`.
- **Writers:** Orchestrator calls `self.blackboard.update_target_space(...)`.
- **Intermediate Output Published to Blackboard:**
  - `target_module_path`: `"samples/discount.py"`
  - `target_source_code`: Complete source text of `calculate_discount`.
  - `functions`: `["calculate_discount"]`
  - `classes`: `[]`
  - `blast_risk`: `"LOW"` (complexity = 4).
- **Persistence:** `self.blackboard.save_checkpoint(stage="INITIAL_INGESTION", job_id=job_id)`.
  - Serialized all-or-nothing JSON committed to `qa_artifacts/testforge_checkpoints.db`.
  - Revision increments to `1`.

---

### Step 3: Baseline Test Synthesis (`BASELINE_SYNTHESIS` & `BASELINE_VALIDATED`)
- **Agent / Component:** `GoogleADKTestGenerator` (`testforge/adk_generator.py`).
- **Readers:** Reads `TargetSpace.target_source_code` and `TargetSpace.functions`.
- **Execution & Validation:**
  - Synthesizes initial test suite (`test_discount_basic`).
  - Orchestrator validates the candidate test in an isolated `SubprocessSandbox` on the unmutated code.
  - Confirms **100% Pass@1** (clean code passes without assertion errors).
- **Writers:** Orchestrator calls `self.blackboard.update_suite_space(...)`.
- **Intermediate Output Published to Blackboard:**
  - `current_test_code`: Code of `test_discount_basic`.
  - `baseline_test_code`: Identical copy preserved for regression reference.
  - `active_provider`: `"Google ADK Generator"`.
  - `baseline_passed`: `True` (1 passed, 0 failed).
- **Persistence:** `save_checkpoint(stage="BASELINE_VALIDATED")`.
  - Revision increments to `2`.

---

### Step 4: Deterministic AST Mutation & Parallel Sandbox Evaluation
- **Agent / Component:** `ASTMutator` (`testforge/mutator.py`) & `SubprocessSandbox` (`testforge/sandbox.py`).
- **Readers:** Reads `TargetSpace.target_source_code` and `SuiteSpace.current_test_code`.
- **Execution:**
  - Injects 19 deterministic AST mutations (`COMP_OP`, `BOUNDARY_SWAP`, `OFF_BY_ONE`, `MATH_FUNC`).
  - Evaluates all 19 mutants across CPU multiprocessing sandbox workers against `current_test_code`.
  - Categorizes mutant outcomes: 12 Killed, 7 Survived, 0 Timed Out, 0 Invalid.
  - Computes Raw Score: `63.16%`.
- **Writers:** Orchestrator calls `self.blackboard.update_mutant_space(...)` and `update_metrics_space(...)`.
- **Intermediate Output Published to Blackboard:**
  - `mutants`: List of 19 `MutantRecord` objects with full stdout, diffs, execution timing, and status.
  - `surviving_mutant_diffs`: Unified diffs for the 7 surviving mutants.
  - `raw_mutation_score`: `63.16`.
  - `history`: Appends `IterationMetrics(iteration=1, score=63.16%, killed=12, survived=7)`.
- **Persistence:** `save_checkpoint(stage="REFLECTION_ITERATION_1")`.
  - Revision increments to `15`.

---

### Step 5: Adversarial Critique & Semantic Guidance
- **Agent / Component:** `CrewAICriticAgent` (`testforge/crew_critic.py`) via A2A message broker.
- **Readers:** Reads `MutantSpace.surviving_mutant_diffs` and `TargetSpace.target_source_code`.
- **Execution:**
  - Diagnoses why mutants survived (e.g., lack of equality boundary assertions on `quantity == 5`, floating-point hundredths precision omitted).
  - Emits structured Pydantic `CriticDirectiveModel`.
- **Writers:** Orchestrator calls `self.blackboard.update_critic_space(...)`.
- **Intermediate Output Published to Blackboard:**
  - `latest_directive`: Adversarial guidance targeting boundary values.
  - `critic_directives`: Cumulative list of directives.
  - `failure_mechanisms`: Map of `{mutant_id: explanation}`.
- **Persistence:** Checkpoint state updated. Revision increments.

---

### Step 6: Downstream Reflection Loop Consumption
- **Downstream Reader:** `GoogleADKTestGenerator` in Iteration 2 reads:
  - `CriticSpace.latest_directive`
  - `MutantSpace.surviving_mutant_diffs`
  - `TargetSpace.target_source_code`
- **Execution & Clean-Code Quarantine:**
  - Synthesizes candidate tests incorporating boundary conditions.
  - Granular Clean Code Validator runs candidate tests against clean code.
  - Any candidate test asserting an incorrect expected output (which would cause false failures on valid code) is quarantined.
  - Working test suite from Iteration 1 is safely retained to protect 100% Pass@1 integrity.
- **Writers:** Checkpoint saved for `REFLECTION_ITERATION_2` and `REFLECTION_ITERATION_3`.
- **Finalization:** At iteration 3, stopping ceiling is reached. Orchestrator calls `self.blackboard.sync_to_state()` and `save_checkpoint(stage="FINALIZED", status="TARGET_SCORE_UNREACHED")`.
  - Final revision reached: `76`.

---

## 3. Frontend Consumption & UI Visibility Analysis

### How the Frontend Reads Blackboard State
The frontend communicates with Blackboard state through two primary channels:

1. **Active Job Polling:**
   - Frontend polls `GET /api/harden/status/{job_id}` every 1200ms.
   - When complete, returns `job.final_state`, which contains the synced Blackboard snapshot dictionary (`mutants`, `history`, `surviving_mutant_diffs`, `metrics`).
2. **Persistent Checkpoint APIs:**
   - `GET /api/checkpoints?job_id=...`: Lists all checkpoint records from SQLite.
   - `GET /api/checkpoints/{checkpoint_id}`: Retrieves the exact 5-partition snapshot JSON.
   - `GET /api/checkpoints/diff?base_id=...&target_id=...`: Computes structured semantic diff between any two snapshots.
3. **Real-time Event Stream:**
   - `GET /api/telemetry` & `GET /api/wiretap`: Streams individual lifecycle events emitted synchronously during Blackboard mutations.

### What the UI Displays: Live vs Final

| UI Tab | Live During Run? | Display Content |
| :--- | :---: | :--- |
| **Hardening Lab & Results** | **Partial** | Shows live progress bar simulation and status text (`Running reflection loop...`), but the full 5 partition cards only render upon job completion. |
| **Checkpoint Timeline & Diff** | **Yes (on refresh)** | Displays the persistent SQLite snapshot stream (`INITIAL_INGESTION`, `BASELINE_VALIDATED`, `REFLECTION_ITERATION_1..3`, `FINALIZED`). Clicking any card renders all 5 partition cards. |
| **Multi-Agent Wiretap** | **Live** | Streams agent-to-agent message exchange cards as they occur. |
| **Observability Trace** | **Live** | Displays structured event telemetry stream. |

---

## 4. How a Reviewer Can Visibly Demonstrate This Data Flow

A reviewer or teacher can verify the Blackboard shared state in 4 clear steps:

1. **Step 1: Open Checkpoint Timeline**
   - Click the `💾 Checkpoint Timeline & Diff` tab in the navigation bar.
   - Click "🔄 Refresh Checkpoints".
2. **Step 2: Inspect Ingestion Baseline**
   - Select the `BASELINE_VALIDATED` snapshot card.
   - Observe **Target Space** (functions, complexity) and **Suite Space** (initial baseline test code). Observe that Mutant Space and Critic Space are still empty.
3. **Step 3: Inspect Reflection Iteration 1**
   - Select the `REFLECTION_ITERATION_1` snapshot card.
   - Observe that **Mutant Space** is now populated with 19 mutants (12 killed, 7 survived) and **Metrics Space** shows `63.2%`.
   - Observe **Critic Space** containing adversarial directives targeting the surviving mutants.
4. **Step 4: Execute Deterministic Checkpoint Diff**
   - Click "Set Base (A)" on `BASELINE_VALIDATED`.
   - Click "Set Target (B)" on `FINALIZED`.
   - Click "⚖️ Compare Selected Checkpoints".
   - Review the modal diff highlighting exact additions to the test suite, mutant state transitions, and metric progression.

---

## 5. Architectural Recommendation for Enhanced Live Visibility

While the Blackboard is fully implemented in the backend and visible post-hoc in the Checkpoint Timeline tab, live visualization during an active run could be made even more immediate:

### Smallest Practical Addition: "Live Blackboard Drawer" (Recommendation Only — Not Implemented)
- **Concept:** Add a collapsible side drawer or 5-card mini-strip to the `Hardening Lab` tab.
- **Behavior:** As `pollHardeningJob` polls `/api/harden/status/{job_id}`, if the orchestrator attaches the latest lightweight partition summary, the 5 mini-cards (`Target`, `Suite`, `Mutants`, `Critic`, `Metrics`) illuminate dynamically.
- **Estimated Effort:** ~60 lines of HTML/JS without changing backend logic.
- **Priority:** Low/Polish — the existing `💾 Checkpoint Timeline & Diff` tab already satisfies all core requirements for shared state inspection.
