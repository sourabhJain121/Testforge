# TestForge Frontend Interactive Elements & Test Matrix

This document provides a comprehensive verification catalog of every interactive UI control, navigation trigger, input, and data-bound widget in the TestForge Frontend Dashboard Cockpit (`frontend/index.html` & `frontend/app.js`).

## System Architecture Summary
- **UI Stack:** Vanilla ES6+ JavaScript, Semantic HTML5, CSS3 Custom Properties (zero NPM runtime dependencies).
- **Backend Bridge:** FastAPI REST, WebSocket (`/ws/events`), Server-Sent Events, and JSON-RPC over stdio (FastMCP).
- **Automation Engine:** Playwright Headless Chromium (`playwright.sync_api`).

---

## 1. Tab Navigation & Pane Transitions

| Element ID / Selector | Expected Behavior | Verification Method | Status | Evidence / Log Excerpt |
|---|---|---|---|---|
| `#tab-btn-lab` (`[data-tab="tab-hardening"]`) | Activates Hardening Lab pane (`#tab-hardening`); applies `.active` class to button and pane | Playwright click event & class attribute assertion | PASS | Verified in `test_headless_cockpit_full_interactive_verification` |
| `#tab-btn-wiretap` (`[data-tab="tab-wiretap"]`) | Activates Multi-Agent Wiretap pane (`#tab-wiretap`); renders 8-agent topology grid | Playwright click event & `.agent-topo-card` count check (8 cards) | PASS | Verified in `test_headless_cockpit_full_interactive_verification` |
| `#tab-btn-benchmark` (`[data-tab="tab-benchmark"]`) | Activates Benchmarks & Ablation pane; triggers `loadMultiTargetBenchmark()` | Playwright click event & `#multi-target-benchmark-table-body` text check | PASS | Verified 4 targets and Arithmetic/Geometric mean rows |
| `#tab-btn-history` (`[data-tab="tab-checkpoints"]`) | Activates Checkpoint Timeline pane; queries `/api/checkpoint/list` | Playwright click event & `#tab-checkpoints` active class assertion | PASS | Verified in tab transition matrix |
| `#nav-mode-a` (`[data-tab="tab-mode-a"]`) | Activates Mode A (Workspace & Upload) panel; loads default sample | Playwright click event & `#tab-mode-a.active` | PASS | Verified in tab transition matrix |
| `#nav-mode-b` (`[data-tab="tab-mode-b"]`) | Activates Mode B (AI Synthesis) panel | Playwright click event & `#tab-mode-b.active` | PASS | Verified in tab transition matrix |
| `#nav-mode-c` (`[data-tab="tab-mode-c"]`) | Activates Mode C (GitHub Direct Import) panel | Playwright click event & `#tab-mode-c.active` | PASS | Verified in tab transition matrix |
| `#nav-blast` (`[data-tab="tab-blast"]`) | Activates Blast Radius & Call Graph panel; populates function select | Playwright click event & `#tab-blast.active` | PASS | Verified in tab transition matrix |
| `#nav-telemetry` (`[data-tab="tab-telemetry"]`) | Activates Observability Trace panel; queries `/api/telemetry/stats` | Playwright click event & `#tab-telemetry.active` | PASS | Verified in tab transition matrix |
| `#subtab-btn-file-url` | Switches Mode C to single file URL input view (`#subtab-pane-file-url`) | DOM class toggle click verification | PASS | Verified subtab switching |
| `#subtab-btn-repo-tree` | Switches Mode C to repository explorer tree view (`#subtab-pane-repo-tree`) | DOM class toggle click verification | PASS | Verified subtab switching |
| `#btn-subtab-detail` | Switches checkpoint inspector to Structured Detail view (`#view-cp-detail`) | Subtab click & visibility check | PASS | Verified in checkpoint inspector |
| `#btn-subtab-diff` | Switches checkpoint inspector to Deterministic Diff view (`#view-cp-diff`) | Subtab click & visibility check | PASS | Verified in checkpoint inspector |
| `#btn-subtab-json` | Switches checkpoint inspector to Raw Snapshot JSON view (`#view-cp-json`) | Subtab click & visibility check | PASS | Verified in checkpoint inspector |

---

## 2. Action & Execution Buttons

| Element ID / Selector | Expected Behavior | Verification Method | Status | Evidence / Log Excerpt |
|---|---|---|---|---|
| `#btn-start-hardening` | Initiates autonomous multi-agent hardening pipeline via `POST /api/harden/start` | Playwright click trigger; checks button disabled and label change | PASS | Verified in automated scenario B1 |
| `#btn-cancel-job` | Sends cancellation signal to `POST /api/harden/cancel/{job_id}`; transitions job to CANCELLED | Playwright click trigger while job is running | PASS | Verified in automated scenario B3 |
| `#btn-resume-interrupted-job` | Resumes interrupted job from checkpoint via `POST /api/harden/resume/{job_id}` | Playwright click trigger; verifies job resumed | PASS | Verified in automated scenario B3 |
| `#btn-a2a-card` | Opens A2A modal and fetches `/.well-known/agent-card.json` | Playwright click trigger; checks `#a2a-modal-backdrop` unhidden | PASS | Verified in A2A discovery test |
| `#btn-close-a2a-modal` / `#btn-close-a2a-footer` | Closes A2A Agent Card modal | Playwright click trigger; checks modal hidden | PASS | Verified modal close binding |
| `#btn-run-a2a-test` | Executes in-browser A2A protocol & schema test against `/api/a2a/diagnostic/verify` | Playwright click trigger; validates JSON response rendering | PASS | Verified diagnostic A2A execution |
| `#btn-view-raw-a2a` | Opens `/.well-known/agent-card.json` in new tab | Attribute verification (`href`, `target="_blank"`) | PASS | Verified URL target mapping |
| `#btn-copy-a2a-json` | Copies agent card JSON payload to clipboard | Event listener and clipboard API invocation | PASS | Verified clipboard write handler |
| `#btn-mcp-status` | Opens FastMCP tools modal and queries `/api/mcp/status` | Playwright click trigger; checks `#mcp-modal-backdrop` unhidden | PASS | Verified in MCP discovery test |
| `#btn-close-mcp-modal` / `#btn-close-mcp-footer` | Closes MCP tools modal | Playwright click trigger; checks modal hidden | PASS | Verified modal close binding |
| `#btn-run-mcp-test` | Executes FastMCP diagnostic tool invocation (`/api/mcp/diagnostic/invoke`) | Playwright click trigger; verifies result JSON displayed | PASS | Verified FastMCP tool test |
| `#btn-view-raw-mcp` | Opens `/api/mcp/status` in new tab | Attribute verification (`href`, `target="_blank"`) | PASS | Verified URL target mapping |
| `#btn-copy-mcp-json` | Copies MCP status payload to clipboard | Event listener and clipboard write handler | PASS | Verified clipboard write handler |
| `#btn-toggle-settings` | Opens system settings modal (`#settings-modal-backdrop`) | Playwright click trigger; checks modal visibility | PASS | Verified settings drawer toggle |
| `#btn-close-settings` / `#btn-cancel-settings` | Closes system settings modal without saving | Playwright click trigger; checks modal hidden | PASS | Verified modal close |
| `#btn-save-settings` | Persists model, iteration, and score settings to runtime state | Playwright click trigger; verifies state synchronization | PASS | Verified settings persistence |
| `#btn-scroll-to-hardening` | Smooth-scrolls to Hardening Lab and activates tab | Playwright click trigger; verifies `#tab-hardening.active` | PASS | Verified banner call-to-action |
| `#btn-load-sample` | Ingests selected sample module into active target state | Playwright click trigger; verifies AST summary and code display | PASS | Verified sample loading |
| `#btn-submit-upload` | Submits uploaded Python file via `POST /api/ingest/upload` | Form submission & AST parsing verification | PASS | Verified custom upload flow |
| `#btn-synthesize-module` | Invokes `POST /api/ingest/synthesize` to generate code from NL spec | Playwright click trigger; checks synthesized code rendered | PASS | Verified in Mode B test |
| `#btn-fetch-github` | Fetches and ingests remote GitHub module via `POST /api/ingest/github` | Playwright click trigger; checks AST metadata population | PASS | Verified in Mode C test |
| `#btn-discover-repo` | Discovers repository files via `POST /api/github/discover-repo` | Playwright click trigger; checks repo table rows rendered | PASS | Verified in Mode C explorer |
| `#btn-activate-mode-c` | Confirms ingested GitHub module as active target | Playwright click trigger; verifies target banner update | PASS | Verified target activation |
| `#btn-download-suite` | Downloads `test_hardened.py` directly from browser memory blob | Playwright download listener; validates Python syntax | PASS | Verified in scenario B4 |
| `#btn-download-junit` | Triggers browser download of JUnit XML report (`/api/export/junit/{job_id}`) | Playwright download listener; validates XML structure | PASS | Fixed via DEF-011; verified in scenario B4 |
| `#btn-download-sarif` | Triggers browser download of OASIS SARIF v2.1.0 report (`/api/export/sarif/{job_id}`) | Playwright download listener; validates SARIF 2.1.0 JSON | PASS | Fixed via DEF-011; verified in scenario B4 |
| `#btn-refresh-wiretap` | Queries `/api/wiretap/summary` to refresh agent statuses | Playwright click trigger; verifies status badges updated | PASS | Verified wiretap refresh |
| `#btn-refresh-telemetry` | Queries `/api/telemetry/stats` to refresh token counts | Playwright click trigger; verifies telemetry table updated | PASS | Verified telemetry refresh |
| `#btn-run-benchmark` | Runs comparative ablation benchmark via `/api/benchmark/run` | Playwright click trigger; verifies progress banner | PASS | Verified benchmark runner |
| `#btn-refresh-benchmark` | Refreshes benchmark summary table from `/api/benchmark/results` | Playwright click trigger; verifies table hydrated | PASS | Verified benchmark refresh |
| `#btn-run-multi-benchmark` | Runs 4-target cross-evaluation via `POST /api/benchmark/multi-target/run` | Playwright click trigger; verifies multi-target run | PASS | Verified multi-benchmark trigger |
| `#btn-refresh-multi-benchmark` | Queries `GET /api/benchmark/multi-target/summary` and updates 4-target table | Playwright click trigger; checks summary table and tfoot | PASS | Verified multi-benchmark refresh |
| `#btn-refresh-checkpoints` | Reloads SQLite checkpoints list from `/api/checkpoint/list` | Playwright click trigger; verifies stream cards rendered | PASS | Verified checkpoint stream refresh |
| `#btn-trigger-diff-modal` | Opens checkpoint diff viewer when base and target are selected | Click trigger & diff calculation check | PASS | Verified checkpoint diff view |
| `#btn-swap-diff-selection` | Swaps A and B checkpoint selections | Click trigger & label update assertion | PASS | Verified diff swap logic |
| `#btn-clear-diff-selection` | Clears active diff selections | Click trigger & label reset assertion | PASS | Verified diff clear logic |
| `#btn-confirm-restore` | Confirms checkpoint state restoration via `POST /api/checkpoint/restore` | Playwright click trigger; verifies isolated state restoration | PASS | Verified checkpoint restoration |
| `#btn-cancel-restore` | Cancels snapshot restoration modal | Click trigger & modal hidden check | PASS | Verified restore cancellation |
| Filter buttons (`[data-filter]`) | Filters AST mutation table (`ALL`, `KILLED`, `SURVIVED`, `EQUIVALENT`) | Playwright click on each filter; checks table row count updates | PASS | Verified filter toggles |

---

## 3. Configuration & Form Inputs

| Element ID / Selector | Expected Behavior | Verification Method | Status | Evidence / Log Excerpt |
|---|---|---|---|---|
| `#target-select` | Selects built-in sample (`discount.py`, `banking.py`, `inventory_pricing.py`, `rate_limiter.py`, `state_machine.py`) | Value change & AST reload verification | PASS | Verified dropdown selection |
| `#radio-source-sample` / `#radio-source-upload` | Toggles between sample dropdown and custom upload dropzone in Mode A | Click trigger & container visibility checks | PASS | Verified radio toggle |
| `#file-upload-input` | Accepts `.py` file for custom ingestion | Simulated file upload event | PASS | Verified upload handler |
| `#toggle-git-diff` | Toggles Git diff-targeted mutation hardening mode | Change event & `/api/analysis/git-diff` call check | PASS | Verified diff detection toggle |
| `#synth-prompt-input` | Multiline specification input for Mode B synthesis | Textarea input & prompt length check | PASS | Verified in scenario B2 & Mode B |
| `#github-url-input` | Single file URL input for GitHub Mode C | Text input & regex validation | PASS | Verified in Mode C tests |
| `#github-repo-url-input` | Public repo URL input for Mode C repository explorer | Text input & repo explorer query | PASS | Verified in repo explorer |
| `#github-repo-ref-input` | Branch, tag, or commit SHA input for repository explorer | Text input & git tree query | PASS | Verified ref targeting |
| `#repo-filter-input` | Live client-side text filter for repository Python files table | Keyup event & DOM row filtering check | PASS | Verified client-side filtering |
| `#blast-func-select` | Selects function to inspect blast radius & dependency impact | Change event & call tree recalculation | PASS | Verified blast radius dropdown |
| `#engine-mode-select` | Sets execution engine (`auto`, `cloud`, `openrouter`, `local`) | Dropdown change & state synchronization | PASS | Verified provider mode selection |
| `#model-name-select` | Sets foundation model (`gemini-3.6-flash`, `gemini-3.1-pro-preview`, `qwen2.5-coder:7b`) | Dropdown change & payload verification | PASS | Verified model selection |
| `#max-iterations-input` | Slider configuring max reflection loops (range 1–10) | Slider change & label badge update | PASS | Verified slider range `[1, 10]` |
| `#target-score-input` | Slider configuring target mutation score (range 50–100%) | Slider change & label badge update | PASS | Verified slider range `[50, 100]` |
| `#input-gemini-key` | Password input for Google Gemini API key | Password input & masked attribute check | PASS | Verified secret protection |
| `#input-openrouter-key` | Password input for OpenRouter API key | Password input & masked attribute check | PASS | Verified secret protection |
| `#mcp-test-tool-select` | Selects tool for FastMCP diagnostic test (`list_directory`, `get_file_info`) | Change event & parameter binding | PASS | Verified tool selector |
| `#telem-scope-select` | Selects telemetry scope (`all`, `current`, `wf_*`) | Change event & `/api/telemetry/stats` scope query | PASS | Verified scope selector |
| `#bench-target-select` | Selects target module for benchmarking | Change event & benchmark payload mapping | PASS | Verified benchmark target selector |
| `#bench-repetitions` | Selects benchmark repetitions (1, 3, 5, 10) | Change event & repetition mapping | PASS | Verified repetition selector |
| `#bench-sc-baseline` / `#bench-sc-zeroshot` / `#bench-sc-refl` | Checkboxes selecting scenarios to evaluate in benchmark | Change events & scenario list mapping | PASS | Verified scenario checkboxes |
| `#cp-stage-filter` | Filters checkpoint snapshots by workflow stage | Change event & filter execution | PASS | Verified stage filtering |
| `#cp-status-filter` | Filters checkpoint snapshots by status | Change event & filter execution | PASS | Verified status filtering |
| `#cp-job-filter` | Filters checkpoint snapshots by job ID | Input event & substring filtering | PASS | Verified job ID filter |
| `#cp-sort-order` | Toggles sort order of checkpoints (newest vs oldest) | Change event & list reordering | PASS | Verified sort order |

---

## 4. Data-Bound Reactive Widgets

| Element ID / Selector | Expected Behavior | Verification Method | Status | Evidence / Log Excerpt |
|---|---|---|---|---|
| `#hardening-progress-box` / `#hardening-status-text` / `#hardening-percent-text` | Reflects live pipeline phase (`IDLE` -> `PARSING` -> `MUTATING` -> `EVALUATING` -> `COMPLETED`) | Polling callback & DOM text assertion | PASS | Verified in scenario B1 |
| `#hardening-blackboard-strip` / `#bb-strip-stage` / `#bb-strip-revision` | Displays real-time partition states (TargetSpace, SuiteSpace, MutantSpace, CriticSpace, MetricsSpace) | DOM content updates during polling | PASS | Verified in scenario B1 |
| `#kpi-base-gen` / `#kpi-base-exec` / `#kpi-base-pass` / `#kpi-base-fail` / `#kpi-base-verdict` | Displays Baseline Pass@1 test suite execution integrity | Numerical value & text assertion | PASS | Verified baseline metrics |
| `#kpi-lines-cov` / `#kpi-cov-pct` | Displays line coverage and ratio | Number format & percentage assertion | PASS | Verified coverage metrics |
| `#kpi-branch-pct` / `#kpi-branch-sub` / `#kpi-missing-branches-dropdown` | Displays branch coverage; click toggles missing branch dropdown | Click toggle & dropdown visibility check | PASS | Verified in interactive drill-down test |
| `#kpi-mut-gen` / `#kpi-mut-exec` / `#kpi-mut-kill` / `#kpi-mut-surv` / `#kpi-mut-err` | Displays AST mutation counts across lifecycle | Non-zero value assertions on completed run | PASS | Verified in scenario B1 |
| `#kpi-mut-score` | Displays verified mutation score percentage | Text content check (`> 0.0%`) | PASS | Verified in scenario B1 |
| `#kpi-tqs-score` / `#kpi-tqs-sub` / `#tqs-breakdown-tooltip` | Displays 5-dimension calibrated TQS quality; hover reveals dimension tooltip | Hover trigger & tooltip visibility check | PASS | Verified in interactive drill-down test |
| `#wiretap-eight-agents-grid` | Renders dynamic cards for all 8 canonical agents with URIs and status pills | DOM query for 8 agent cards & URI attributes | PASS | Verified 8 canonical agents present |
| `#wiretap-timeline-container` | Appends sequential inter-agent handoff cards in real time | Child element count check | PASS | Verified handoff trajectory display |
| `#telem-kpi-events` / `#telem-kpi-actual-tokens` / `#telem-kpi-est-tokens` / `#telem-kpi-engine` | Displays token consumption and execution engine accounting | Numerical value assertions | PASS | Verified token telemetry |
| `#telemetry-table-body` | Renders row-by-row LLM and synthesis inference telemetries | Table row count assertion | PASS | Verified telemetry log table |
| `#multi-target-benchmark-table-body` | Renders 4 canonical modules (`discount.py`, `lru_cache.py`, `order_fsm.py`, `stats_calculator.py`) | Table row text checks | PASS | Verified all 4 target rows rendered |
| `#multi-target-benchmark-table-foot` | Renders Arithmetic Mean and Geometric Mean summary rows | `tfoot` content check | PASS | Verified Arithmetic & Geometric mean rows |
| `#mutants-table-body` | Renders list of generated AST mutants with type, line, and outcome | Row count & click listener verification | PASS | Verified mutant audit table |
| `#diff-code-display` | Renders unified AST diff of the selected mutant | Inner text syntax check | PASS | Verified diff inspector |
| `#hardened-suite-code` | Displays final executable hardened test suite | Python syntax check | PASS | Verified hardened suite display |
| `#wiretap-ws-status-badge` | Shows WebSocket connection state (`Connecting...` -> `Live Streaming` or `Disconnected`) | Badge text & CSS class assertion | PASS | Verified in scenario B5 |

---

## 5. Verification Conclusion
Every interactive control, navigation transition, button trigger, form input, and data-bound widget has been audited against `frontend/index.html` and `frontend/app.js`. Zero dangling DOM references exist, all API endpoints are mapped, and automated Playwright headless browser test suites (B1–B5) confirm reactive compliance.

