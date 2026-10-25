# TestForge — Complete Visualization & Metric Audit

**Audit Date:** 2026-10-23
**Platform:** macOS Apple Silicon M2 Pro
**TestForge Server:** `http://127.0.0.1:8000/`

---

## 1. Executive Summary

Every chart, KPI counter, data table, status badge, and visualization in TestForge was audited against genuine backend API responses.
All visual components were inspected for:
1. Source data validity and accuracy vs backend API
2. Rendering completeness without clipping, overflow, or NaN/undefined values
3. Axes, units, labels, and formatting rules
4. Missing, empty, loading, and recovery states
5. Dynamic DOM updates following real lifecycle events

---

## 2. Comprehensive Visualization Inventory

| # | Visualization Component | Selector / ID | Source Endpoint | Observed Value / Rendering | Audit Status | Notes |
|---|---|---|---|---|---|---|
| 1 | **Hardware Status Pill** | `#label-hardware` | `GET /api/status` | `Apple Silicon (arm64)` | **PASS** | Detects ARM64 architecture |
| 2 | **Local Ollama Pill** | `#label-ollama` | `GET /api/status` | `Local Ollama` | **PASS** | Gray when offline; active when connected |
| 3 | **Cloud Gemini Pill** | `#label-gemini` | `GET /api/status` | `Gemini Live` | **PASS** | Status indicator with green/amber dot |
| 4 | **Target Module Hero Card** | `#target-module-title` | `POST /api/ingest/sample` | `samples.discount` | **PASS** | Updates immediately on sample change |
| 5 | **Source SHA Badge** | `#tag-sha` | `POST /api/ingest/sample` | `SHA: c9b7...` | **PASS** | 64-character SHA-256 hash |
| 6 | **Source Functions Tag** | `#tag-funcs` | `POST /api/ingest/sample` | `1 Function` | **PASS** | Accurately extracts AST defs |
| 7 | **Source Line Count Tag** | `#tag-lines` | `POST /api/ingest/sample` | `24 Lines` | **PASS** | Accurate LoC count |
| 8 | **AST Functions Summary** | `#mode-a-funcs-list` | `POST /api/ingest/sample` | `calculate_discount` | **PASS** | Lists AST callable signatures |
| 9 | **Syntax Code Viewer** | `#mode-a-code-display` | `POST /api/ingest/sample` | Formatted Python code | **PASS** | JetBrains Mono font, line numbering |
| 10 | **Blast Risk Badge** | `#blast-risk-badge` | `POST /api/analysis/blast-radius` | `🟢 LOW` | **PASS** | Color-coded risk tier |
| 11 | **Blast Impact Ratio** | `#blast-impact-ratio` | `POST /api/analysis/blast-radius` | `0.0%` | **PASS** | Ratio of affected callables |
| 12 | **ASCII Call Tree** | `#blast-tree-display` | `POST /api/analysis/blast-radius` | Formatted ASCII tree | **PASS** | Visual tree indentation |
| 13 | **Call Graph Canvas** | `#call-graph-canvas` | `POST /api/analysis/blast-radius` | Interactive nodes & edges | **PASS** | High-DPI canvas rendering |
| 14 | **Baseline Executed KPI** | `#kpi-base-exec` | `GET /api/harden/status/{id}` | Integer counter (1) | **PASS** | Tests executed count |
| 15 | **Baseline Passed KPI** | `#kpi-base-pass` | `GET /api/harden/status/{id}` | Integer counter (1, green) | **PASS** | Pass@1 integrity check |
| 16 | **Line Coverage KPI** | `#kpi-cov-pct` | `GET /api/harden/status/{id}` | Percentage (`45.0%` - `100.0%`) | **PASS** | Calculated by ParallelSandboxRunner |
| 17 | **Mutants Generated KPI** | `#kpi-mut-gen` | `GET /api/harden/status/{id}` | Integer counter (4 - 20) | **PASS** | From ASTMutator |
| 18 | **Mutants Killed KPI** | `#kpi-mut-kill` | `GET /api/harden/status/{id}` | Integer counter (green) | **PASS** | Validated mutant kills |
| 19 | **Mutants Survived KPI** | `#kpi-mut-surv` | `GET /api/harden/status/{id}` | Integer counter (red) | **PASS** | Non-equivalent surviving mutants |
| 20 | **Mutation Score KPI** | `#kpi-mut-score` | `GET /api/harden/status/{id}` | Percentage (`85.0%` - `100.0%`) | **PASS** | Formula: (Killed / Total * 100) |
| 21 | **Reflection Cycles Done** | `#kpi-cycles-done` | `GET /api/harden/status/{id}` | Integer counter (1 - 3) | **PASS** | Multi-agent loop iterations |
| 22 | **Hardening Progress Bar** | `#hardening-progress-bar` | `GET /api/harden/status/{id}` | `0%` -> `100%` width | **PASS** | Smooth CSS animated transitions |
| 23 | **Iteration History Table** | `#history-table` | `GET /api/harden/status/{id}` | Iteration breakdown rows | **PASS** | Tracks delta between loops |
| 24 | **Mutant Filter Chips** | `.filter-btn` | DOM / State | `All (4), Killed (4), Equiv (0)` | **PASS** | Dynamic counting & table filtering |
| 25 | **Unified AST Diff Viewer** | `#diff-code-display` | Selected Mutant AST Diff | Unified Git-style diff | **PASS** | Red deletion / Green insertion lines |
| 26 | **Hardened Suite Preview** | `#hardened-suite-code` | `GET /api/hardened-code` | Executable pytest code | **PASS** | Syntax-highlighted Python block |
| 27 | **Wiretap WS Badge** | `#wiretap-ws-status-badge` | `/ws/events` connection state | `● Streaming (Live)` / `● Polling` | **PASS** | Live streaming badge |
| 28 | **Wiretap Handoffs KPI** | `#wiretap-kpi-handoffs` | `GET /api/wiretap` | Integer count | **PASS** | Increments on every agent handoff |
| 29 | **Wiretap Timeline Cards** | `#wiretap-timeline-container`| `/ws/events` or `/api/wiretap`| Sequential handoff cards | **PASS** | Micro-animated step cards |
| 30 | **Telemetry Events KPI** | `#telem-kpi-events` | `GET /api/telemetry` | Integer count | **PASS** | Tracks events in trace log |
| 31 | **Telemetry Total Tokens** | `#telem-kpi-tokens` | `GET /api/telemetry` | Number with formatting | **PASS** | Exact provider token sums |
| 32 | **Telemetry Data Table** | `#telemetry-table` | `GET /api/telemetry` | Latency, prompt, completion | **PASS** | Structured row rendering |
| 33 | **Benchmark Summary Table**| `#benchmark-summary-table`| `GET /api/benchmark/results` | Baseline vs ZeroShot vs Refl | **PASS** | Aggregated statistical means |
| 34 | **Benchmark Markdown View**| `#bench-rendered-markdown-view`| `GET /api/benchmark/markdown`| Formatted HTML report | **PASS** | Renders tables and disclaimers |
| 35 | **Checkpoint Snapshot Cards**| `#checkpoint-cards-stream` | `GET /api/checkpoints` | Persistent snapshot cards | **PASS** | Stage badge, revision, time |
| 36 | **Checkpoint Inspector** | `#cp-detail-content` | `GET /api/checkpoints/{id}` | Structured partition view | **PASS** | Inspects state, tests, mutants |
| 37 | **Checkpoint Diff View** | `#cp-diff-content` | `GET /api/checkpoints/diff` | Semantic delta comparison | **PASS** | Color-coded added/removed items |
| 38 | **A2A Agent Card Modal** | `#a2a-card-content` | `/.well-known/agent-card.json`| Rendered card metadata | **PASS** | Name, description, capabilities |

---

## 3. Visual Defect Analysis
- **Overflow & Clipping:** 0 horizontal overflow issues across 1440px, 1280px, and 768px viewports.
- **NaN / Undefined Values:** 0 instances of `NaN`, `undefined`, or `[object Object]` observed.
- **Stale Data:** All counters dynamically update upon corresponding user actions or event broadcasts.
