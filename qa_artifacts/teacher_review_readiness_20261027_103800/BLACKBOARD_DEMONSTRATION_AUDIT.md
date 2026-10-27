# TESTFORGE — BLACKBOARD DEMONSTRATION AUDIT & STATE FLOW TRACE

**Repository:** `/Users/sourabh/TestForge`  
**Audit Directory:** `qa_artifacts/teacher_review_readiness_20261027_103800/`  
**Timestamp:** `2026-10-27T10:41:00+05:30`  
**Auditor Role:** Senior Software Architect & Agentic Systems Specialist  

---

## 1. Architectural Integrity of the Blackboard

The TestForge Blackboard (`testforge/blackboard.py`) is a thread-safe, revision-controlled shared state coordinator. It is not an informal global dictionary; it is partitioned into five strongly typed spaces governed by Pydantic models:

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│                            TESTFORGE SHARED BLACKBOARD                           │
├─────────────────┬─────────────────┬─────────────────┬──────────────┬─────────────┤
│   TargetSpace   │   SuiteSpace    │   MutantSpace   │ CriticSpace  │MetricsSpace │
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

## 2. End-to-End Real State Flow & Agent Interactivity

| Step | Lifecycle Stage | Active Agent / Component | Blackboard Space Written | Blackboard Space Read | Intermediate Output Published | Persisted Checkpoint |
| :---: | :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | Instantiation | Orchestrator | All (initialized empty) | None | Revision 0 initialized | None |
| **2** | Ingestion | `IngestionManager`, `BlastRadiusAnalyzer` | `TargetSpace` | None | Target source code, AST symbols, complexity, blast risk profile | `INITIAL_INGESTION` (Rev 1) |
| **3** | Baseline Synthesis | `GoogleADKTestGenerator` | `SuiteSpace` | `TargetSpace` | Initial test suite, Pass@1 validation status | `BASELINE_VALIDATED` (Rev 2) |
| **4** | Fault Injection & Evaluation | `ASTMutator`, `SubprocessSandbox` | `MutantSpace`, `MetricsSpace` | `TargetSpace`, `SuiteSpace` | 19 AST mutants, killed/survived statuses, raw score (63.2%), iteration metric | `REFLECTION_ITERATION_1` (Rev 15) |
| **5** | Adversarial Diagnosis | `CrewAICriticAgent` | `CriticSpace` | `TargetSpace`, `MutantSpace` | Root-cause analysis, failure mechanisms, boundary directives | Checkpoint state updated |
| **6** | Reflection Iteration 2 | `GoogleADKTestGenerator` | `SuiteSpace` | `CriticSpace`, `TargetSpace` | Candidate tests targeting boundary conditions, clean-code quarantine | `REFLECTION_ITERATION_2` |
| **7** | Reflection Iteration 3 | `GoogleADKTestGenerator`, `Critic` | `SuiteSpace`, `CriticSpace` | `MutantSpace`, `CriticSpace` | Final candidate assertions, clean code validation | `REFLECTION_ITERATION_3` |
| **8** | Finalization | Orchestrator | `MetricsSpace` | All | Final score (63.2%), terminal status `TARGET_SCORE_UNREACHED`, stopping reason | `FINALIZED` (Rev 76) |

---

## 3. Critical Findings on UI Presentation: Real Events vs Simulated Timers

### A. The Reality of the Hardening Lab Progress Bar
- **Inspection of `frontend/app.js` (lines 1772-1786):**
  ```javascript
  let progressSim = 15;
  state.hardening.pollTimer = setInterval(async () => {
    ...
    if (job.status === 'RUNNING') {
      progressSim = Math.min(progressSim + 12, 90);
      dom.hardeningProgressBar.style.width = `${progressSim}%`;
      dom.hardeningPercentText.textContent = `${progressSim}%`;
      dom.hardeningStatusText.textContent = `Autonomous Multi-Agent reflection loop running (Core Sandbox: ${progressSim}%)...`;
    }
  ```
- **Finding:** The percentage progress bar in the Hardening Lab is **driven by a simulated JavaScript timer**, incrementing by 12% every 1.2s until capping at 90%.
- **The Backend Disconnect:** The backend orchestrator already provides real lifecycle states in `job["lifecycle_state"]` (`PLANNING`, `GENERATING_TESTS`, `VALIDATING_CLEAN_CODE`, `MUTATION_ANALYSIS`, `EXECUTING`, `EVALUATING`, `CHECKPOINTING`), but the frontend currently ignores this rich field and shows the simulated percentage.

### B. State Visibility: Live vs Post-Hoc
- **In Hardening Lab:** Blackboard spaces are not displayed live while the job is running. The full results only render after `job.status === 'COMPLETED'`.
- **In Checkpoint Timeline:** All 5 Blackboard spaces are fully visible post-hoc. Every stage has a dedicated card displaying its full partition data, and the diff modal proves state transitions across cycles.

---

## 4. Evaluation of Existing Checkpoint Timeline & Diff View

### Is the existing Checkpoint Timeline & Diff view sufficient for a teacher's review?
**YES, it is technically sufficient, but requires navigation.**
- The `💾 Checkpoint Timeline & Diff` tab is a fully functioning Blackboard inspector.
- A teacher can click on `BASELINE_VALIDATED` and see `TargetSpace` and `SuiteSpace`.
- The teacher can click on `REFLECTION_ITERATION_1` and see `MutantSpace`, `CriticSpace`, and `MetricsSpace`.
- The teacher can click "Compare Selected Checkpoints" and view exact partition deltas.

### Would adding a compact live Blackboard view to the Hardening Lab materially improve the demonstration?
**YES, SUBSTANTIALLY.**
- **Why it matters:** In a live demonstration, the teacher's attention is focused on the `🔥 Hardening Lab & Results` tab where the student clicks "⚡ Run TestForge Autonomous Hardening".
- If the student can point to a live 5-space strip right below the progress bar that lights up as each agent writes to the Blackboard:
  `[Target Space: Ingested] -> [Suite Space: Synthesized] -> [Mutant Space: 19 Mutants] -> [Critic Space: Directive Emitted]`
  the teacher immediately sees the Blackboard in action without needing an explanation about switching tabs.

---

## 5. Recommended Minimal Changes (Planning Only)

1. **Replace Simulated Timer with Real FSM Lifecycle (P0/P1):**
   - Update `app.js:pollHardeningJob` to read `job.lifecycle_state`.
   - Map states to meaningful descriptive text:
     - `GENERATING_TESTS`: "Google ADK: Synthesizing candidate test assertions..."
     - `VALIDATING_CLEAN_CODE`: "Granular Validator: Verifying tests on clean unmutated code (Pass@1)..."
     - `MUTATION_ANALYSIS`: "AST Mutator: Injecting faults and executing parallel sandboxes..."
     - `PLANNING` / `EVALUATING`: "CrewAI Critic: Diagnosing surviving mutant diffs and formulating directives..."
2. **Add a Compact Live Blackboard Partition Strip in Hardening Lab (P1):**
   - In `frontend/index.html` below the progress bar, add a 5-card mini-strip:
     `Target | Suite | Mutants | Critic | Metrics`.
   - As the job progresses through FSM states, pulse the active partition card.
   - On completion, clicking any card links directly to that partition in the Checkpoint Timeline tab.
