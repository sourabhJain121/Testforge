# TestForge — Agentic Pipeline Verification

**Audit Date:** 2026-10-27 01:17:30 IST  
**Audit Directory:** `qa_artifacts/autonomous_e2e_acceptance_20261027_004800/`  

---

## 1. Multi-Stage Pipeline Architecture

TestForge executes an Evaluator-Optimizer / Reflection workflow coordinated across discrete, typed blackboard partitions:
```
Target Ingestion ──> AST Mutator ──> Clean Pass@1 Check ──> Parallel Sandbox
                          ▲                                       │
                          │                                       ▼
                  Targeted Synthesis <── Critic Diagnostic Directives
                  (Google ADK Agent)         (CrewAI Critic)
```

### Stage Transitions Verified (Finite State Machine)
- `TaskLifecycleState.CREATED`
- `TaskLifecycleState.VALIDATING`
- `TaskLifecycleState.INGESTING`
- `TaskLifecycleState.PLANNING`
- `TaskLifecycleState.GENERATING_TESTS`
- `TaskLifecycleState.EXECUTING`
- `TaskLifecycleState.MUTATION_ANALYSIS`
- `TaskLifecycleState.EVALUATING`
- `TaskLifecycleState.COMPLETED`

All 9 discrete transitions were captured with sub-millisecond precision in `stage_durations` and `stage_history` across all 5 evaluated jobs (`eaa31160`, `876c748c`, `ecae8d2b`, `55386150`, `cb4a25ab`).

---

## 2. Inter-Agent Context Sharing & Handoffs

1. **Google ADK Generator (`testforge/adk_generator.py`):**
   - Synthesizes candidate pytest assertion blocks for target functions.
   - Pushes `GeneratedTestPayload` to `SuiteSpace`.
   - Validates AST syntax before pushing to prevent syntax failures.
2. **Deterministic Mutation Evaluator (`testforge/sandbox.py`):**
   - Executes candidate tests against deterministic AST mutations in parallel sandbox workers.
   - Categorizes each mutant as `KILLED`, `SURVIVED`, `TIMEOUT`, or `ERROR`.
   - Emits surviving mutant code diffs to `MutantSpace`.
3. **CrewAI Adversarial Critic (`testforge/crew_critic.py`):**
   - Ingests surviving mutant unified diffs from `MutantSpace`.
   - Produces structured `CriticDirectivePayload` into `CriticSpace` with root-cause diagnoses, failure mechanisms, and actionable boundary test suggestions.
4. **Targeted Repair (Iteration 1..N):**
   - ADK Generator reads `CriticSpace` directives to synthesize targeted boundary assertions killing surviving mutants.
   - **Suite Preservation Invariant:** If candidate repair assertions fail the clean reference target, the previous working suite is preserved rather than dropped.
