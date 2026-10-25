# TestForge — Visual and Data-Correctness Audit Report
**Audit Timestamp:** October 23, 2026  
**Evidence Directory:** `/Users/sourabh/TestForge/qa_artifacts/full_e2e_audit_20261023_140930`  
**Target Environment:** macOS Darwin (Apple Silicon M2 Pro, 10 CPU cores, arm64), Google Chrome 141.0.7390.123  
**Verified Backend URL:** `http://127.0.0.1:8000`

---

## 1. Executive Summary

This visual audit evaluates every chart, diagram, KPI card, counter, badge, table, modal, and responsive viewport in TestForge. The audit was conducted via automated Chrome DevTools Protocol (CDP) and live visual browser sessions executing real workflows against the active FastAPI backend.

All visualizations were inspected for:
- Completeness of rendering (no layout breakage or horizontal overflow)
- Precision and honesty of underlying data (excluding invalid/errored mutants from scores)
- Accurate badge semantics (`🟢 KILLED`, `🔵 EQUIV`, `🟡 POTENTIAL`, `🟠 TIMEOUT`, `⚪ INVALID`, `🟣 ERROR`, `🔴 SURVIVED`)
- Responsive adaptation across 1440×900, 1280×800, and 390×844 viewports.

---

## 2. Visualization & View-by-View Audit

### 2.1 Navigation & Status Pills (`#system-status-pills`)
- **Visual Rendering:** Glassmorphic navigation header with ambient back-glow.
- **Hardware Pill (`#pill-hardware`):** Displays `Apple Silicon (arm64)` with pulsating green status indicator. Data matches backend `testforge.accel.hw_profile`.
- **Model Engine Pills (`#pill-ollama`, `#pill-gemini`, `#pill-openrouter`):**
  - Ollama Local Engine: Active indicator dot reflects real-time HTTP probe (`/api/status`).
  - Google Gemini: Displays cloud readiness.
  - OpenRouter: Fallback indicator.
- **Verdict:** **PASS** (Evidence: `01_initial_dashboard.png`).

---

### 2.2 Active Target Banner (`#active-target-card`)
- **Visual Elements:** Gradient hero card with active target chip (`Active Target: Mode A`).
- **Data Integrity:**
  - Target title: `samples.discount`
  - Tags: `📁 samples/discount.py`, `⚡ 1 Function`, `🏛️ 0 Classes`, `📄 24 Lines`
  - SHA-256 fingerprint: Dynamically calculated from ingested source AST.
- **Action Control:** `#btn-scroll-to-hardening` smoothly shifts focus to Hardening Lab.
- **Verdict:** **PASS** (Evidence: `01_initial_dashboard.png`, `02b_mode_a_workspace.png`).

---

### 2.3 AST Mutation Audit & Diff Inspector (`#mutant-audit-panel`)
- **Filter Buttons:**
  - `ALL`: Displayed 19 generated mutants. Count badge exactly matches 19 table rows.
  - `🟢 Killed`: Displayed 18 killed mutants (94.7% kill rate). Filtered rows: 18.
  - `🔴 Survived`: Displayed 1 surviving mutant. Filtered rows: 1.
  - `🔵 Equiv`: Displayed 0 verified equivalent mutants on `discount.py` (tier boundary mutations are non-equivalent). Filtered rows: 0 with clean empty state `No mutants matching filter (EQUIVALENT)`.
- **Data Row Inspector (`tr.clickable-row`):**
  - Displays Mutant ID (e.g. `MUT_COND_INV_001`), AST Operator (`COND_INV`, `ROR`, `AOR`), Line Number (`Line 9`), Outcome Badge (`🟢 KILLED BY ASSERTION`), and Execution Duration (`12ms`).
- **Unified AST Diff Viewer (`#diff-code-display`):**
  - Clicking any mutant table row dynamically renders the syntax-highlighted unified diff showing original versus mutated Python AST node.
  - Conservative Equivalence Analysis box clearly denotes whether the mutant is killed, verified equivalent, or surviving non-equivalent.
- **Verdict:** **PASS** (Evidence: `04a_mutants_table_all.png`, `04b_mutants_table_killed.png`, `04c_mutants_table_survived.png`, `04d_mutants_table_equiv.png`, `05_ast_diff_equivalence_inspector.png`).

---

### 2.4 Three-Row Structured Hardening Metrics Dashboard (`#hardening-metrics-board`)
- **Row 1: Baseline Test Suite Execution (Pass@1 Integrity):**
  - Baseline Generated: 3 tests
  - Baseline Executed: 3 tests
  - Baseline Passed: 3 tests (Green badge)
  - Baseline Failed: 0 tests
  - Clean Code Verdict: `🟢 PASSED` (Verifies unmutated code passes baseline assertions).
- **Row 2: Mutation Hardening & Line Coverage Analysis:**
  - Lines Covered: 24 / 24
  - Line Coverage: 100.0%
  - Mutants Generated: 19
  - Mutants Executed: 19
  - Mutants Killed: 18
  - Mutants Survived: 1
  - Execution Errors: 0
- **Row 3: Final Status & Reflection Cycles:**
  - Verified Mutation Score: 94.7% (Formula: `18 / (19 - 0 - 0) * 100 = 94.73%`).
  - Reflection Iterations: 1
  - Final Pipeline Status: `HARDENED` (Green luminous badge).
- **Verdict:** **PASS** (Evidence: `03_hardening_completed.png`).

---

### 2.5 Architectural Call Graph & Blast Radius Visualizer (`#tab-blast`)
- **Visual Elements:** Interactive SVG/HTML call graph container (`#call-graph-canvas`).
- **Data Correctness:**
  - Function Selector: Populated with module callables (`calculate_discount`).
  - Risk Category: `🟢 LOW`
  - Affected Functions: `0 / 1` (isolated leaf calculation function).
  - Impact Ratio: `0.0%`
  - Direct Callees: `0`
  - ASCII Dependency Call Tree: Renders hierarchical caller-callee structure.
- **Verdict:** **PASS** (Evidence: `09_blast_call_graph.png`, `02e_blast_radius_call_graph.png`).

---

### 2.6 Blackboard Checkpoint Timeline & Split Inspector (`#tab-checkpoints`)
- **Timeline Stream (`#checkpoint-cards-stream`):**
  - Loaded 100 persistent SQLite snapshots from `testforge_checkpoints.db`.
  - Filter Controls: Stage Filter (`ALL`, `INITIAL_INGESTION`, `BASELINE_VALIDATED`, `REFLECTION_ITERATION`, `FINALIZED`), Status Filter (`ALL`, `SUCCESS`), Search Input, Sort Order (`Newest First`, `Oldest First`).
  - Card Details: Displays Checkpoint ID (`chk_...`), Workflow Stage badge, timestamp, metrics chips.
- **Structured Inspector Subtab (`#btn-subtab-detail`):**
  - Injects structured partition cards: Target Space, Suite Space, Mutant Space, Metrics, and Critic Directives.
  - XSS Protection: All arbitrary user code and error messages rendered safely via `textContent` rather than `innerHTML`.
- **Raw Snapshot JSON Subtab (`#btn-subtab-json`):**
  - Displays full JSON payload with `📋 Copy JSON` functionality.
- **Deterministic Diff Comparator (`#btn-subtab-diff` & `#btn-trigger-diff-modal`):**
  - Side-by-side selection: Base (A) (`chk_dcdcc3da1a21`) and Target (B) (`chk_464af8e6717e`).
  - Computes partition transitions: Added fields, modified fields, mutant classification deltas.
- **Verdict:** **PASS** (Evidence: `06_checkpoint_timeline_detail.png`, `07_checkpoint_diff_viewer.png`).

---

### 2.7 State Recovery Confirmation Modal (`#restore-modal`)
- **Visual Elements:** Warning modal with prominent yellow exclamation icon and clear safety disclaimer.
- **Data Display:** Shows target Checkpoint ID, Workflow Stage, Revision, and Creation Timestamp.
- **Safety Safeguard:**
  - Clicking `Cancel` closes the dialog with zero side-effects.
  - Clicking `Confirm & Restore` triggers isolated non-destructive deserialization into an isolated Blackboard instance.
- **Verdict:** **PASS** (Evidence: `08_restore_confirmation_modal.png`).

---

### 2.8 Multi-Agent Wiretap & Observability Trace (`#tab-wiretap`, `#tab-telemetry`)
- **Wiretap Stream:** Sequential handoff cards displaying inter-agent deliberation contracts between TargetManagerAgent, TestArchitectAgent, MutationSpecialistAgent, and CriticAgent.
- **Telemetry Table:** Real-time log from `testforge_trace.jsonl` detailing provider latency, prompt tokens, completion tokens, and AST validation verdicts.
- **Verdict:** **PASS** (Evidence: `09a_multi_agent_wiretap.png`, `09b_observability_telemetry.png`).

---

### 2.9 Statistical Benchmarking & Ablation View (`#tab-benchmark`)
- **Comparative Ablation Table:** Renders comparative rows for Baseline vs Zero-Shot vs Agentic Reflection across Wall-Clock Latency, Mutation Score, Line Coverage, and Estimated Token Cost.
- **Metric Categorization Callouts:**
  - 📏 Measured Metrics (runtimes, raw mutant counts, token usage).
  - 🧮 Calculated Metrics (mutation score formulas, speedup ratios).
  - 💲 Estimated Metrics (Gemini pricing conversions).
- **Report Toggle:** Formatted rendered Markdown view and raw Markdown code view.
- **Verdict:** **PASS** (Evidence: `09c_statistical_benchmarks.png`).

---

## 3. Responsive Layout Audit

| Viewport | Dimensions | Orientation | Layout Findings | Result | Screenshot Evidence |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Desktop** | 1440 × 900 | Landscape | Full 2-column grid, side-by-side diff inspector, unclipped timeline cards | **PASS** | `10a_desktop_1440x900.png` |
| **Laptop** | 1280 × 800 | Landscape | Proper scaling, metrics cards wrap cleanly in flex grid, zero horizontal overflow | **PASS** | `10b_laptop_1280x800.png` |
| **Mobile** | 390 × 844 | Portrait | Stacks to 1-column layout, horizontal scroll preserved on wide tables, navigation tab bar scrolls horizontally without clipping buttons | **PASS** | `10c_narrow_390x844.png` |

---

## 4. Overall Visual Audit Verdict: PASS
All charts, tables, diff inspectors, modals, and responsive views render faithfully, accurately represent the underlying state, and provide clear user feedback.
