# TestForge — Complete End-to-End Practical Walkthrough

**Document Version:** 1.0.0  
**Last Verified:** November 2, 2026  
**Target Module:** `samples/discount_module.py`  
**Execution Mode:** Local Hybrid Reflection Hardening  

---

## 1. Sequence Diagram: Complete Lifecycle Trace

The diagram below traces every operation across all subsystems from user button click to final hardened suite visualization:

```mermaid
sequenceDiagram
    autonumber
    actor User as Developer / Web UI
    participant App as frontend/app.js
    participant Server as server.py (FastAPI)
    participant Orch as TestForgeOrchestrator
    participant BB as Blackboard
    participant TMA as TargetManagerAgent
    participant TGA as TestGeneratorAgent
    participant Sand as NativeSandbox
    participant Mut as ASTMutator
    participant Crit as AdversarialCriticAgent
    participant DB as SQLite CheckpointStorage
    participant Log as TraceLogger

    User->>App: Clicks "Harden Target Suite"
    App->>Server: POST /api/harden/start (target="discount_module.py")
    Server->>Orch: start_hardening_task(target, max_iter=3, target_score=85)
    Server-->>App: HTTP 200 OK (job_id="job_discount_01")
    
    Orch->>Log: log_event("LIFECYCLE_STATE_CHANGE", state="INGESTING")
    Orch->>BB: initialize_spaces()
    Orch->>TMA: ingest_source("samples/discount_module.py")
    TMA->>TMA: scan_for_injection_attempts() -> CLEAN
    TMA->>BB: write_target_space(source_code, callables)
    
    Note over Orch,TGA: --- ITERATION 0: BASELINE SYNTHESIS ---
    Orch->>Log: log_event("LIFECYCLE_STATE_CHANGE", state="GENERATING")
    Orch->>TGA: generate_initial_tests()
    TGA->>TGA: ASTCallableAnalyzer extracts calculate_discount signatures & boundaries
    TGA->>BB: write_suite_space(candidate_test_code)
    
    Orch->>Sand: execute_pytest(candidate_test_code, clean_target)
    Sand-->>Orch: Baseline Tests Passed (9/9 passed, 100% line coverage)
    Orch->>BB: update_metrics(baseline_passed=True, coverage=100.0)
    
    Orch->>Mut: generate_mutants(target_source_code)
    Mut-->>Orch: 19 Viable AST Mutants
    Orch->>Sand: execute_mutants_batch(candidate_test_code, 19 mutants)
    Sand-->>Orch: 15 Killed, 4 Survived (Raw Score: 78.95%)
    Orch->>BB: write_mutant_space(killed=15, survived=4, score=78.95)
    
    Orch->>Crit: diagnose_surviving_mutants(surviving_diffs)
    Crit-->>Orch: Directives: "Assert boundary quantity=9 vs 10, and quantity=4 vs 5"
    Orch->>BB: write_critic_space(directive, reflection_notes)
    Orch->>DB: save_checkpoint("chk_iter0", stage="BASELINE_VALIDATED")
    
    Note over Orch,TGA: --- ITERATION 1: ADVERSARIAL REFLECTION ---
    Orch->>Log: log_event("LIFECYCLE_STATE_CHANGE", state="REFLECTION_ITERATION_1")
    Orch->>TGA: refine_tests(critic_directive)
    TGA->>TGA: Appends boundary tests for quantity=9, 10, 4, 5 and price=0.0
    TGA->>BB: write_suite_space(hardened_candidate_code)
    
    Orch->>Sand: execute_mutants_batch(hardened_candidate_code, 19 mutants)
    Sand-->>Orch: 17 Killed, 2 Survived (Raw Score: 89.47%)
    Orch->>BB: write_mutant_space(killed=17, survived=2, raw_score=89.47, adj_score=94.44)
    Orch->>DB: save_checkpoint("chk_iter1", stage="FINALIZED")
    
    Note over Orch: Target Score 85.0% Exceeded (89.47% >= 85.0%)!
    Orch->>Log: log_event("LIFECYCLE_STATE_CHANGE", state="COMPLETED")
    
    App->>Server: GET /api/harden/status/job_discount_01 (Polling)
    Server-->>App: status="COMPLETED", raw_score=89.47%, adj_score=94.44%
    App->>User: Displays Hardened Code, Kill Badges & Enables AST Diff Modal
```

---

## 2. Step-by-Step Practical Trace

### Step 1: User Initiation in Web Dashboard
1. The user navigates to `http://127.0.0.1:8000/`.
2. Under the **Hardening Workbench** tab, the user selects `samples/discount_module.py` from the sample library dropdown.
3. The user configures:
   - Target Mutation Score: `85.0%`
   - Max Reflection Iterations: `3`
   - Prompt Strategy: `ReAct Deliberation Loop`
   - Persona: `QA Specialist`
4. The user clicks **"Start Hardening"**.

### Step 2: Frontend Dispatch & Background Job Creation
- In `frontend/app.js`, function `handleStartHardening()` intercepts the click event.
- Issues an asynchronous HTTP request:
  ```http
  POST /api/harden/start HTTP/1.1
  Content-Type: application/json

  {
    "mode": "sample",
    "target_file": "samples/discount_module.py",
    "target_score": 85.0,
    "max_iterations": 3,
    "prompt_strategy": "REACT",
    "persona": "QA_ENGINEER"
  }
  ```
- In `server.py`, the endpoint `start_hardening_task()` generates `job_id = "job_3f4e2d"` and `workflow_id = "wf_7a8b9c"`.
- Adds the orchestrator run task to FastAPI's `BackgroundTasks` pool and immediately returns HTTP 200 OK.
- `app.js` transitions the UI into the active running state, disabling the button and starting the status polling loop (`pollJobStatus()`) every 1,500ms.

### Step 3: Ingestion & Threat Validation
- The `TestForgeOrchestrator` starts execution on a background worker thread.
- Invokes `TargetManagerAgent.ingest()` (`testforge/ingestion.py`).
- Reads the file content from disk.
- Runs `scan_for_injection_attempts()` (`testforge/prompt_guard.py`): Checks for suspicious shell injection strings, docstring instructions, or dynamic imports. Status: **CLEAN**.
- Parses the Python Abstract Syntax Tree:
  - Discovers function `calculate_discount(price: float, quantity: int, is_member: bool)`.
- Writes clean source and callable signatures into `TargetSpace` on the blackboard.

### Step 4: Iteration 0 — Baseline Test Generation
- The orchestrator transitions the FSM state to `GENERATING`.
- Invokes `TestGeneratorAgent` (`testforge/agents.py`).
- `ASTCallableAnalyzer` inspects parameter types and condition operators (`<=`, `>=`, `<`).
- Generates 9 parameterized test cases covering nominal tiers, negative values, and zero boundaries.
- Writes candidate code into `SuiteSpace` (`suite.candidate_test_code`).

### Step 5: Clean Sandbox Pre-Flight Execution
- The orchestrator passes the candidate test code and clean target source to `NativeSandbox.run_pytest()` (`testforge/sandbox.py`).
- Spawns an isolated subprocess: `python -m pytest test_target.py`.
- **Result:** 9 passed in 0.24 seconds. 100% statement coverage achieved.
- Promotes `candidate_test_code` to `current_test_code` on the blackboard.

### Step 6: AST Mutant Generation & Sandbox Execution
- The orchestrator invokes `ASTMutator.mutate_module()` (`testforge/mutator.py`).
- Discovers 19 mutation sites across relational operators, arithmetic calculations, and boolean conditions.
- Generates 19 discrete AST mutants.
- Executes the candidate test suite against each mutant in the sandbox:
  - **Mutants Killed:** 15 mutants killed.
  - **Mutants Survived:** 4 mutants survived.
  - **Baseline Raw Mutation Score:** **78.95%** (below the 85.0% target).
- Writes scores and surviving unified diffs to `MutantSpace`.

### Step 7: Adversarial Critic Reflection Directive
- Because score (78.95%) < target (85.0%), the orchestrator transitions to `CRITIQUING`.
- Invokes `AdversarialCriticAgent` (`testforge/agents.py`).
- The critic compares the AST diffs of the 4 surviving mutants:
  - Detects that tests checked `quantity = 5` and `quantity = 10`, but missed transition boundaries `quantity = 4` and `quantity = 9`.
  - Detects that tests missed floating-point epsilon zero check `price = 0.0001`.
- Formulates a prescriptive `CriticDirectivePayload` and writes it to `CriticSpace`.
- Saves atomic snapshot `chk_iter0` to SQLite (`testforge_checkpoints.db`).

### Step 8: Iteration 1 — Targeted Refinement Loop
- Orchestrator increments iteration counter to 1.
- Invokes `TestGeneratorAgent.refine_suite()` with the critic's directive.
- The generator injects targeted boundary assertions:
  ```python
  assert calculate_discount(100.0, 9, False) == 95.0
  assert calculate_discount(100.0, 10, False) == 90.0
  assert calculate_discount(100.0, 4, False) == 100.0
  assert calculate_discount(100.0, 5, False) == 95.0
  ```
- Executes the refined suite against the 19 mutants in the sandbox:
  - **Mutants Killed:** 17 mutants killed (kills Mutant #1 and Mutant #2).
  - **Mutants Survived:** 2 mutants survived.
  - **Final Raw Mutation Score:** **89.47%** ($17/19 \times 100$).
  - **Adjusted Mutation Score:** **94.44%** (excluding 1 verified equivalent dead-code mutant).

### Step 9: Termination, Persistence & UI Presentation
- The orchestrator verifies that **89.47% >= 85.0% target threshold**.
- Transitions lifecycle state to `COMPLETED`.
- Saves final snapshot `chk_iter1` (`stage = "FINALIZED"`) to SQLite.
- Appends final telemetry event to `testforge_trace.jsonl`.
- `frontend/app.js` polls `/api/harden/status/job_discount_01`, detects `status = "COMPLETED"`, updates the dashboard with the hardened code editor, highlights the 89.47% score badge in glowing green, and activates the **"View AST Diff"** modal.

