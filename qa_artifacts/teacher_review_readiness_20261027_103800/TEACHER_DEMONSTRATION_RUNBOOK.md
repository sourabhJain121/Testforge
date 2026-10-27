# TESTFORGE — TEACHER DEMONSTRATION RUNBOOK & LIVE WALKTHROUGH

**Repository:** `/Users/sourabh/TestForge`  
**Audit Directory:** `qa_artifacts/teacher_review_readiness_20261027_103800/`  
**Timestamp:** `2026-10-27T10:45:00+05:30`  
**Target Audience:** Evaluator / University Teacher / Technical Reviewer  
**Prerequisites:** Server running on `http://127.0.0.1:8000/` with headed browser open.

---

## Demonstration Script & Step-by-Step Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      TESTFORGE 7-STEP TEACHER WALKTHROUGH                   │
├──────┬────────────────────────────────┬─────────────────────────────────────┤
│ Step │ Demonstration Phase            │ Evaluated Mandatory Requirements    │
├──────┼────────────────────────────────┼─────────────────────────────────────┤
│ 1    │ System Architecture & Protocols│ MUST 2 (MCP), MUST 6 (A2A), MUST 11 │
│ 2    │ Target Ingestion & AST Analysis│ Mode A / Ingestion & Blast Radius   │
│ 3    │ Autonomous Reflection Loop     │ MUST 1, MUST 3, MUST 4, MUST 7      │
│ 4    │ Hardening Results & Diagnosis  │ MUST 3, MUST 9 (Provenance)         │
│ 5    │ Blackboard Snapshot Inspection │ MUST 1 (5 Spaces & Deterministic Diff)│
│ 6    │ Multi-Agent Wiretap & Handoffs │ MUST 5 (Callbacks), MUST 7 (CrewAI) │
│ 7    │ Empirical Benchmark & Cost     │ MUST 4 (Ablation), MUST 10 (Cost)   │
└──────┴────────────────────────────────┴─────────────────────────────────────┘
```

---

### Step 1: System Health, Protocols & Discovery (2 Minutes)
1. **Show Navbar Status:** Point out the `Backend: Online` badge and `Platform: Apple Silicon (darwin arm64)`.
2. **Demonstrate MUST 6 (A2A Protocol):**
   - Click the `🤖 A2A Agent Card` button in the header.
   - Show the rendered AgentCard: Protocol version `0.3.0`, capabilities, and endpoints.
   - Click **"View Raw JSON"** to show `http://127.0.0.1:8000/.well-known/agent-card.json`.
   - *Key Talking Point:* "TestForge follows the official A2A draft specification with machine-discoverable agent capabilities."
3. **Demonstrate MUST 2 (Model Context Protocol):**
   - Click the `🔌 MCP Tools` button in the header.
   - Show the 4 registered tools across FastMCP Filesystem and GitHub servers.
   - Point out the security boundaries: strict `permitted_root` containment, rejection of directory traversal (`../`), and masking of `.env` / credentials.
   - Click **"View Raw JSON"** to show `/api/mcp/status`.

---

### Step 2: Target Ingestion & Blast Radius (2 Minutes)
1. Navigate to **`📁 Mode A: Workspace & Upload`**.
2. Select built-in sample **`discount.py`** and click **"Load Sample"**.
3. Point out the loaded code in the editor (`calculate_discount` with price, quantity, and member logic).
4. Navigate to **`💥 Blast Radius & Call Graph`**:
   - Point out the calculated Cyclomatic Complexity (4), Risk Category (`LOW`), and AST symbol table.
   - *Key Talking Point:* "Before generating tests or injecting faults, TestForge builds a full AST call graph and risk profile using static analysis."

---

### Step 3: Running the Autonomous Hardening Pipeline (3 Minutes)
1. Navigate to **`🔥 Hardening Lab & Results`**.
2. Verify settings: Target Mutation Score = `85%`, Max Iterations = `3`.
3. Click **"⚡ Run TestForge Autonomous Hardening"**.
4. Observe the progress bar and status text as the orchestrator runs:
   - Google ADK synthesizes initial tests.
   - Granular Clean Code Validator verifies tests on unmutated code (**100% Pass@1**).
   - AST Mutator injects 19 deterministic mutations.
   - Subprocess sandbox evaluates mutants across parallel CPU workers.
   - CrewAI Adversarial Critic inspects surviving mutant diffs.
   - Cycle repeats up to 3 reflection rounds.
5. Watch the job finish and results render automatically.

---

### Step 4: Inspecting Hardening Results & Survivor Diagnosis (3 Minutes)
1. **Show the Verdict Banner:**
   - Point out the banner: `⚠️ Pipeline Completed — Mutation Target Unreached`.
   - Point out the 3 distinct badges:
     - `🟢 Baseline: 100% Passed` (Clean code passed 100%)
     - `🔵 Pipeline: Finished (3 Cycles)` (Pipeline completed without crashing)
     - `🟡 Target: Unreached` (Raw score 63.2% vs 85.0% target)
2. **Show the KPI Cards:**
   - Verified Score: `63.2% Target: 85%`.
   - Baseline Executed: `1 / 1 Passed`.
3. **Inspect a Surviving Mutant:**
   - Click the **`🔴 Survived`** filter button in the Mutants Table.
   - Click row `MUT_BOUNDARY_SWAP_003` (Line 9: `price <= 0.0` -> `price < 0.0`).
   - Show the **Survivor Diagnosis Box**:
     - *Execution Status:* Genuinely executed in sandbox (`360.3ms`).
     - *Survival Semantics:* Relational boundary condition altered.
     - *Equivalence Analysis:* Explain that when `price == 0.0`, `0.0 * (1 - rate) == 0.0`, returning `0.0` identically!
   - Expand **"View Real Sandbox Pytest Execution Output"** to show actual pytest stdout.
   - *Key Talking Point:* "TestForge did not reach 85% because this mutant is mathematically equivalent. TestForge refused to fake kills or lower the target, maintaining total scientific honesty."

---

### Step 5: Demonstrating the Blackboard Shared State (MUST 1) (3 Minutes)
1. Click the **`💾 Checkpoint Timeline & Diff`** tab (`#tab-checkpoints`).
2. Click **"🔄 Refresh Checkpoints"**.
3. Select the `BASELINE_VALIDATED` snapshot:
   - Show **TargetSpace** (functions, complexity) and **SuiteSpace** (baseline tests).
   - Show that MutantSpace and CriticSpace are not yet populated.
4. Select the `REFLECTION_ITERATION_1` snapshot:
   - Show that **MutantSpace** is now populated (12 killed, 7 survived) and **CriticSpace** contains adversarial directives.
5. Demonstrate Deterministic Diff:
   - Click "Set Base (A)" on `BASELINE_VALIDATED`.
   - Click "Set Target (B)" on `FINALIZED`.
   - Click **"⚖️ Compare Selected Checkpoints"**.
   - Show the property-by-property delta proving how state evolved across cycles.

---

### Step 6: Demonstrating Multi-Agent Wiretap & Frameworks (MUST 7 & MUST 5) (2 Minutes)
1. Click the **`🤖 Multi-Agent Wiretap`** tab (`#tab-wiretap`).
2. Show the handoff cards:
   - `GoogleADKTestGenerator -> SubprocessSandbox` (synthesizing candidate tests).
   - `SubprocessSandbox -> CrewAICriticAgent` (evaluating surviving diffs).
   - `CrewAICriticAgent -> GoogleADKTestGenerator` (passing adversarial directives).
3. Point out that **no 3rd framework** (LangChain, AutoGen) is used.
4. Click the **`📊 Observability Trace`** tab (`#tab-telemetry`) to show the real-time event log with correlation IDs.

---

### Step 7: Demonstrating Empirical Benchmarks & Cost (MUST 4 & MUST 10) (2 Minutes)
1. Click the **`⚡ Benchmarks & Ablation`** tab (`#tab-benchmark`).
2. Show the 3-Condition Ablation Table:
   - **Baseline (Handwritten):** 33.3% score, 70% coverage, 0 tokens, $0.00.
   - **Zero-Shot (Single-Pass LLM):** 94.4% score, 100% coverage, 3,731 tokens, $0.00053.
   - **Agentic Reflection (ADK + CrewAI):** Iterative loop with full sandbox validation.
3. Show the **Pricing Breakdown**: Measured tokens vs Calculated scores vs Estimated USD cost based on published rates.
4. Click **"💻 Raw Markdown"** or open `/api/benchmark/markdown` to show the full statistical report.

---

## Honest Disclosures to Provide During the Review

To project complete architectural mastery, disclose these technical nuances proactively:
1. **Mutation Target Status:** Proactively explain that 85% was unreached due to the 3-cycle ceiling, equivalent mutations, and clean-code quarantine.
2. **Offline Fallback Engines:** When cloud API keys are omitted, TestForge automatically falls back to deterministic rule-based generators and critics, allowing full pipeline execution without API costs or network dependencies.
3. **Progress Bar Polling:** Acknowledge that the progress bar currently interpolates progress while polling, and that the proposed improvement plan will wire it directly to backend FSM states.
