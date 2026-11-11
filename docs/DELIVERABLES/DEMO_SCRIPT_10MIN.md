# TestForge: 10-Minute Live Viva Demonstration Runbook

**Audience:** Academic Examination Panel, External Reviewers, Technical Auditors  
**Presenters:** Sourabh & Shreshth  
**Target Environment:** macOS arm64 (`.venv-release`), Python 3.13, FastAPI running on `http://127.0.0.1:8000`  
**Total Allocated Duration:** 10 Minutes + 5 Minutes Q&A  
**Emergency Fallback Directory:** `qa_artifacts/release_audit_20261022/` & `docs/AUDIT_EVIDENCE/`

---

## Pre-Flight Checklist (T-Minus 5 Minutes)
1. **Server Initialization:**
   ```bash
   cd /Users/sourabh/TestForge
   .venv-release/bin/uvicorn server:app --host 127.0.0.1 --port 8000 --reload
   ```
2. **Browser Window:** Open Chrome at `http://127.0.0.1:8000` in full-screen (1080p).
3. **Database Reset (Optional):** Ensure checkpoint database is present at `testforge_blackboard.db`.
4. **Offline Fallback Tab Ready:** Pre-load `qa_artifacts/MULTI_TARGET_BENCHMARK_RESULTS.json` in a background tab in case of live LLM API rate-limits.

---

## Detailed Demonstration Timeline

### [0:00 - 1:30] Part 1: System Overview & Cockpit Navigation
- **Presenter:** Sourabh
- **Action on Screen:**
  1. Open the TestForge Cockpit (`http://127.0.0.1:8000`).
  2. Point out the top header bar: Status badge (`READY`), Hardware Profile (`Apple Silicon M-Series | Workers: 8`), and the Theme Toggle.
  3. Toggle theme between **Dark Mode** and **Light Mode** to demonstrate native CSS custom property styling.
  4. Walk through the 7 primary cockpit navigation tabs:
     - `Mode A / Target Ingestion`: Source code intake, AST inspection, blast radius.
     - `Multi-Agent Wiretap`: Real-time WebSocket event streaming of agent handoffs.
     - `Mutant Diff Inspector`: Side-by-side visual AST code diffs and equivalence analysis.
     - `Benchmark Suite`: Multi-target comparative matrix and ablation viewer.
     - `Telemetry & Observability`: OpenTelemetry distributed trace spans and token usage.
     - `Checkpoints & Rollbacks`: SQLite WAL state timeline and atomic rollback.
     - `FastMCP Studio`: Interactive execution harness for the 4 MCP protocol tools.
- **Verbal Script:**
  > *"Good morning, examiners. We begin in the TestForge Cockpit, built entirely in pure Vanilla ES6 JavaScript and native CSS variables with zero external NPM packages. Notice our top status indicators showing 8 parallel CPU workers and real-time WebSocket connectivity. The interface provides 7 canonical operational views, allowing engineers to oversee the entire multi-agent hardening loop from initial ingestion to atomic checkpoint rollback."*

---

### [1:30 - 3:00] Part 2: Ingesting a Target (Mode A: `discount.py`)
- **Presenter:** Sourabh
- **Action on Screen:**
  1. In the **Mode A Ingestion** panel, click **"Load discount.py"**.
  2. Highlight the automatic execution of `CodeIntelligenceAgent`:
     - Discovered callables: `calculate_discount(price, customer_tier, has_coupon)`.
     - Cyclomatic complexity: 3.
     - Blast risk: `LOW`.
  3. Toggle the **"⚡ Git Diff-Aware Targeted Hardening"** switch and the **"🧠 Agentic RAG Knowledge Retrieval"** switch to showcase configurability.
- **Verbal Script:**
  > *"We ingest `discount.py`, a canonical business logic module with branch conditions and numeric boundary thresholds. Instantly, our Code Intelligence Agent performs static AST analysis without dynamic execution, identifying function signatures, parameters, and branch operators. With Agentic RAG enabled, our system automatically prepares targeted boundary retrieval queries to guide test scenario planning."*

---

### [3:00 - 5:30] Part 3: Live Hardening Run & Multi-Agent Wiretap
- **Presenter:** Shreshth
- **Action on Screen:**
  1. Click **"Run TestForge Autonomous Hardening"** (Target Score: 85%, Max Iterations: 2).
  2. Switch immediately to the **Multi-Agent Wiretap** tab.
  3. Observe live WebSocket events streaming down the timeline:
     - `Supervisor Agent` dispatches `CodeIntelligenceAgent`.
     - `TestPlanningAgent` formulates nominal, boundary, and negative scenarios and retrieves RAG heuristics.
     - `TestGeneratorAgent` synthesizes the initial candidate suite.
     - `TestExecutionAgent` executes the DEF-022 Pass@1 clean preflight check (100% clean pass verified).
     - `ASTMutator` injects 19 synthetic mutants.
     - `MutationQualityCritic` identifies surviving mutants and emits structured failure directives.
     - `ReflectionRepairAgent` executes iteration 2, killing surviving mutants and achieving 94.74% raw MS / 100% adjusted MS.
- **Verbal Script:**
  > *"As the hardening job begins, the Multi-Agent Wiretap captures every inter-agent handoff across the Agent2Agent protocol. Notice the DEF-022 preflight guard: before a single mutant is touched, the candidate suite is validated against clean reference code. In iteration 1, the critic agent diagnoses surviving condition-inversion mutants and provides concrete counterexamples. In iteration 2, the reflection repair agent kills the remaining mutants, reaching 100% adjusted mutation score with zero human intervention."*

---

### [5:30 - 7:00] Part 4: Visual AST Mutant Diff Inspection & Minimization
- **Presenter:** Shreshth
- **Action on Screen:**
  1. Switch to the **Mutant Diff Inspector** tab.
  2. Click on a killed mutant (e.g., `MUTANT_004: BOUNDARY_SWAP`).
  3. Open the **Side-by-Side Diff Inspector Modal**:
     - Left pane: Original AST source (`price >= 100.0`).
     - Right pane: Mutated AST source (`price > 100.0` highlighted in red/green).
  4. Toggle the **"Unified / Side-by-Side"** button to showcase responsive diff layout.
  5. Demonstrate **Bytecode Semantic Equivalence**:
     - Show an equivalent mutant on dead-code or invariant syntax.
     - Explain how recursive bytecode disassembly proved equivalence with 0.0% false positives, adjusting the score to 100%.
  6. Click **"Run Suite Minimization"** to show how redundant tests are pruned while retaining 100% mutation kill fidelity.
- **Verbal Script:**
  > *"Here we see our interactive Visual AST Mutant Diff Viewer. Engineers can inspect the exact code mutation side-by-side with full syntax highlighting. Notice how our bytecode equivalence engine identified compiler-level equivalent mutants, excluding them from the denominator to calculate the true adjusted score. Furthermore, our suite minimizer prunes redundant test executions while preserving 100% kill coverage."*

---

### [7:00 - 8:30] Part 5: Checkpoint Rollback & SQLite Blackboard Recovery
- **Presenter:** Sourabh
- **Action on Screen:**
  1. Switch to the **Checkpoints & Rollbacks** tab.
  2. Inspect the immutable timeline of SQLite WAL checkpoints created across each turn:
     - `CP_001_INGESTION`
     - `CP_002_ITERATION_1`
     - `CP_003_ITERATION_2_FINAL`
  3. Click **"Inspect State Diff"** between Checkpoint 1 and Checkpoint 3 to view state evolution across Blackboard partitions.
  4. Click **"Rollback to Checkpoint 2"**:
     - Confirm dialog.
     - Cockpit updates instantaneously, restoring Blackboard state, test suite code, and mutation score to Iteration 1.
- **Verbal Script:**
  > *"Reliability in enterprise agentic systems requires crash tolerance and deterministic rollback. TestForge commits every state transition to an SQLite Write-Ahead Logging ledger across eight typed partitions. If an LLM hallucination degrades a test suite, our Never-Regress Guard or a developer can roll back to any prior checkpoint in milliseconds, restoring full pipeline state deterministically."*

---

### [8:30 - 9:30] Part 6: FastMCP 4-Tool Protocol Suite Verification
- **Presenter:** Shreshth
- **Action on Screen:**
  1. Switch to the **FastMCP Studio** tab or click the **"⚡ MCP: 4 Active Tools"** header button.
  2. Point to the diagnostic modal displaying the official 4-tool protocol suite:
     - `mcp_ast_symbol_analyzer`
     - `mcp_mutant_generator`
     - `mcp_sandbox_runner`
     - `mcp_equivalence_classifier`
  3. In the interactive runner, select `mcp_ast_symbol_analyzer`, input `def foo(x): return x + 1`, and click **"Execute Tool via Stdio MCP"**.
  4. Observe JSON-RPC response returned in sub-50ms with execution duration and status `SUCCESS`.
- **Verbal Script:**
  > *"Here is our FastMCP 4-Tool Protocol Suite running over standard stdio JSON-RPC transport. Rather than using ad-hoc REST calls, all analysis, mutation generation, sandboxed execution, and equivalence detection are encapsulated in standard FastMCP schemas. External clients like Claude Desktop or internal subagents can query these exact tools with process isolation and automatic fallback."*

---

### [9:30 - 10:00] Part 7: Summary & Q&A Wrap-Up
- **Presenters:** Sourabh & Shreshth
- **Action on Screen:**
  1. Return to the **Benchmark Suite** tab displaying the multi-target evaluation matrix.
  2. Highlight the audited macro results: **6.46% Baseline $\rightarrow$ 67.02% Raw / 70.17% Adjusted Mutation Score** (167/240 mutants killed across the 4 canonical targets).
  3. Close the presentation and invite examiner questions.
- **Verbal Script:**
  > *"To summarize: TestForge solves the silent failure problem of LLM unit testing through mutation-verified multi-agent reflection. By pairing FastMCP stdio tools, local Agentic RAG, and strict clean-reference validation, we deliver verified 10.37x improvements in software defect detection. We are now ready for your questions."*

---

## Pre-Computed Fallback Procedures (Network / API Outage)
If external Gemini API quotas are exhausted or local network fails during live defense:
1. **Fallback Command:** Switch engine mode to `local` or run pre-computed benchmark:
   ```bash
   .venv-release/bin/python scripts/run_t2_rescore.py
   ```
2. **Display Pre-Generated Audit Artifacts:**
   - Static Benchmark Results: `qa_artifacts/MULTI_TARGET_BENCHMARK_RESULTS.json`
   - Visual Evidence: `docs/AUDIT_EVIDENCE/T3/t3_evaluation_results.json`
   - Browser Screenshots: `docs/screenshots/`
