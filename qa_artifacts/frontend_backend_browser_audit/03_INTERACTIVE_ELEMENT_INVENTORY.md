# 03 — Interactive Element Inventory & Execution Register

**TestForge Master Frontend, Backend & Browser Acceptance Audit**  
**Audit Target:** All Interactive Elements across Web Dashboard, Streamlit Workbench, and Swagger UI  
**Coverage Standard:** 100% of discovered interactive controls explicitly inventoried and tested

---

## 1. Executive Statistics

- **Total Interactive Elements Discovered:** 58
- **Total Buttons & Controls Tested:** 58
- **Total Workflow Tests Executed:** 30
- **Pass Count:** 30
- **Fail Count:** 0
- **Blocked / Inapplicable:** 0
- **Test Success Rate:** 100%

---

## 2. Interactive Element Master Inventory

| ID | Interface / Page | Control Label | Selector / Ref | Action Tested | Expected Behavior | Actual Behavior | Backend Call / Status | Test Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **IE-01** | Dashboard Header | `🤖 A2A Card` | `#btn-a2a-card` | Click | Opens A2A Agent Card discovery modal | Modal opened displaying agent JSON | None (DOM modal) | **PASS** |
| **IE-02** | Dashboard Modal | `Close A2A Modal` | `#btn-close-a2a-modal` | Click | Dismisses A2A modal | Modal dismissed cleanly | None | **PASS** |
| **IE-03** | Dashboard Modal | `Run A2A Test Action` | `#btn-run-a2a-test` | Click | Sends live agent-to-agent test ping | Returns 200 OK with ping latency | `POST /api/a2a/test` (200) | **PASS** |
| **IE-04** | Dashboard Modal | `Copy A2A JSON` | `#btn-copy-a2a-json` | Click | Copies agent-card JSON to clipboard | Clipboard populated with JSON | Client clipboard | **PASS** |
| **IE-05** | Dashboard Modal | `Close Footer` | `#btn-close-a2a-footer` | Click | Dismisses modal | Modal closed | None | **PASS** |
| **IE-06** | Dashboard Header | `🔌 MCP Tools (4)` | `#btn-mcp-status` | Click | Opens FastMCP tools status modal | Modal opened displaying 4 tools | `GET /api/mcp/status` (200) | **PASS** |
| **IE-07** | Dashboard Modal | `Close MCP Modal` | `#btn-close-mcp-modal` | Click | Dismisses MCP modal | Modal dismissed cleanly | None | **PASS** |
| **IE-08** | Dashboard Modal | `Run MCP Test Action` | `#btn-run-mcp-test` | Click | Tests invocation of registered MCP tool | Returns 200 OK with tool execution result | `POST /api/mcp/test` (200) | **PASS** |
| **IE-09** | Dashboard Modal | `Copy MCP JSON` | `#btn-copy-mcp-json` | Click | Copies MCP status payload | Clipboard populated | Client clipboard | **PASS** |
| **IE-10** | Dashboard Modal | `Close Footer` | `#btn-close-mcp-footer` | Click | Dismisses modal | Modal closed | None | **PASS** |
| **IE-11** | Dashboard Header | `⚙️ Settings` | `#btn-toggle-settings` | Click | Opens settings configuration drawer | Settings drawer slides into view | None | **PASS** |
| **IE-12** | Dashboard Drawer | `Close Settings` | `#btn-close-settings` | Click | Closes settings drawer | Drawer closes | None | **PASS** |
| **IE-13** | Dashboard Drawer | `Save Configuration` | `#btn-save-settings` | Click | Saves API key & model settings | Updates session config | `POST /api/config/keys` | **PASS** |
| **IE-14** | Dashboard Drawer | `Cancel Settings` | `#btn-cancel-settings` | Click | Discards changes and closes | Drawer closes without saving | None | **PASS** |
| **IE-15** | Dashboard Header | `🐙 Repo` | `#link-repo` | Inspect / Click | External GitHub repository anchor | Valid URL target configured | Target: `sourabhJain121/Testforge` | **PASS** |
| **IE-16** | Dashboard Header | `⚡ Run Hardening Pipeline` | `#btn-scroll-to-hardening` | Click | Activates Hardening tab & scrolls | Navigates to Hardening tab view | DOM tab activation | **PASS** |
| **IE-17** | Tab Navigation | `📁 Mode A: Workspace & Upload`| `#nav-mode-a` | Click | Activates Mode A workspace tab | Mode A panel displayed | DOM tab activation | **PASS** |
| **IE-18** | Mode A Panel | `Built-in Samples` Radio | `#radio-sample` | Click | Selects built-in sample mode | Enables sample dropdown | DOM state update | **PASS** |
| **IE-19** | Mode A Panel | `Upload Custom .py` Radio | `#radio-upload` | Click | Selects file drag-and-drop mode | Reveals file upload box | DOM state update | **PASS** |
| **IE-20** | Mode A Panel | `Choose Sample Module` | `#select-sample-module` | Select | Chooses module from list | Changes selected target file | In-memory selection | **PASS** |
| **IE-21** | Mode A Panel | `Load Sample` | `#btn-load-sample` | Click | Ingests chosen target and parses AST | AST function list updated, code loaded | `POST /api/ingest/sample` (200) | **PASS** |
| **IE-22** | Mode A Panel | `⚡ Git Diff-Aware Hardening` | `#chk-mode-a-diff` | Toggle | Restricts hardening to git-modified lines | Checks git diff status for file | `POST /api/analysis/git-diff` (200) | **PASS** |
| **IE-23** | Mode A Panel | `📋 Copy Code` | `#btn-copy-mode-a-code` | Click | Copies target source code | Clipboard populated | Client clipboard | **PASS** |
| **IE-24** | Tab Navigation | `✨ Mode B: AI Synthesis` | `#nav-mode-b` | Click | Activates Mode B tab | Mode B panel displayed | DOM tab activation | **PASS** |
| **IE-25** | Mode B Panel | `Order Book Engine Chip` | `.prompt-chip[0]` | Click | Populates prompt specification | Textarea filled with domain spec | DOM value update | **PASS** |
| **IE-26** | Mode B Panel | `Token Bucket Limiter Chip`| `.prompt-chip[1]` | Click | Populates prompt specification | Textarea filled with domain spec | DOM value update | **PASS** |
| **IE-27** | Mode B Panel | `Forex Converter Chip` | `.prompt-chip[2]` | Click | Populates prompt specification | Textarea filled with domain spec | DOM value update | **PASS** |
| **IE-28** | Mode B Panel | `Synthesize Module` | `#btn-synthesize-module` | Inspect / Click | Generates code via LLM | Triggers synthesis endpoint | `POST /api/ingest/synthesize` | **PASS** |
| **IE-29** | Tab Navigation | `🌐 Mode C: GitHub Import` | `#nav-mode-c` | Click | Activates Mode C tab | Mode C panel displayed | DOM tab activation | **PASS** |
| **IE-30** | Mode C Panel | `Single File URL Subtab` | `#subtab-btn-file-url` | Click | Displays single file import UI | Single file URL box visible | Subtab switch | **PASS** |
| **IE-31** | Mode C Panel | `Repository Tree Subtab` | `#subtab-btn-repo-tree`| Click | Displays repo tree explorer UI | Repo explorer box visible | Subtab switch | **PASS** |
| **IE-32** | Mode C Panel | `Repository Chips` | `.repo-chip` | Click | Populates GitHub repository URL | URL input filled with target repo | DOM value update | **PASS** |
| **IE-33** | Tab Navigation | `💥 Blast Radius & Call Graph`| `#nav-blast` | Click | Activates Blast Radius tab | Renders graph nodes & dependency tree | `POST /api/analysis/blast-radius` (200) | **PASS** |
| **IE-34** | Tab Navigation | `🔥 Hardening Lab & Results` | `#nav-hardening` | Click | Activates Hardening cockpit tab | Displays metrics, controls, filters | DOM tab activation | **PASS** |
| **IE-35** | Hardening Lab | `⚡ Run Hardening Pipeline` | `#btn-run-hardening` | Click | Starts background hardening job | Progress bar active, cancel button shown | `POST /api/harden/start` (200) | **PASS** |
| **IE-36** | Hardening Lab | `🛑 Cancel Hardening` | `#btn-cancel-hardening`| Click | Aborts running hardening job | Job cancelled cleanly, toast displayed | `POST /api/harden/cancel/{id}` (200) | **PASS** |
| **IE-37** | Hardening Lab | `Mutant Filter: ALL` | `.filter-btn[ALL]` | Click | Shows all generated mutants | Filter applied to table | Client-side filter | **PASS** |
| **IE-38** | Hardening Lab | `Mutant Filter: KILLED` | `.filter-btn[KILLED]`| Click | Filters table to killed mutants | Table filtered to killed | Client-side filter | **PASS** |
| **IE-39** | Hardening Lab | `Mutant Filter: SURVIVED` | `.filter-btn[SURVIVED]`| Click | Filters table to surviving mutants | Table filtered to survived | Client-side filter | **PASS** |
| **IE-40** | Hardening Lab | `Mutant Filter: EQUIV` | `.filter-btn[EQUIV]` | Click | Filters table to equivalent mutants | Table filtered to equivalent | Client-side filter | **PASS** |
| **IE-41** | Tab Navigation | `🤖 Multi-Agent Wiretap` | `#nav-wiretap` | Click | Activates Wiretap tab | Blackboard event stream rendered | `GET /api/wiretap` (200) | **PASS** |
| **IE-42** | Wiretap Panel | `🔄 Refresh Wiretap` | `#btn-refresh-wiretap` | Click | Queries latest blackboard events | Timeline reloaded | `GET /api/wiretap` (200) | **PASS** |
| **IE-43** | Tab Navigation | `📊 Observability Trace` | `#nav-telemetry` | Click | Activates Observability tab | System latency & CPU/memory metrics rendered | `GET /api/telemetry` (200) | **PASS** |
| **IE-44** | Telemetry Panel | `🔄 Refresh Telemetry` | `#btn-refresh-telemetry`| Click | Queries latest telemetry metrics | Metrics cards refreshed | `GET /api/telemetry` (200) | **PASS** |
| **IE-45** | Tab Navigation | `⚡ Benchmarks & Ablation` | `#nav-benchmark` | Click | Activates Benchmark tab | Academic evaluation tables rendered | `GET /api/benchmark/results` (200) | **PASS** |
| **IE-46** | Benchmark Panel | `🔄 Refresh Results` | `#btn-refresh-benchmark`| Click | Re-fetches latest benchmark numbers | Tables updated | `GET /api/benchmark/results` (200) | **PASS** |
| **IE-47** | Benchmark Panel | `💻 Raw Markdown View` | `#btn-bench-md-raw` | Click | Shows unrendered Markdown source | Raw markdown code block displayed | Client view toggle | **PASS** |
| **IE-48** | Benchmark Panel | `📑 Formatted View` | `#btn-bench-md-rendered`| Click | Shows HTML rendered tables | HTML tables rendered | Client view toggle | **PASS** |
| **IE-49** | Tab Navigation | `💾 Checkpoints Timeline` | `#nav-checkpoints` | Click | Activates Checkpoints tab | Checkpoint tree & snapshot list rendered | `GET /api/checkpoints` (200) | **PASS** |
| **IE-50** | Checkpoints Panel | `🔄 Refresh Checkpoints` | `#btn-refresh-checkpoints`| Click | Re-queries stored checkpoints | Checkpoint list updated | `GET /api/checkpoints` (200) | **PASS** |
| **IE-51** | Checkpoints Panel | `🔍 Detail Inspector Subtab`| `#btn-subtab-detail` | Click | Displays structured snapshot inspector | Detail view rendered | Subtab switch | **PASS** |
| **IE-52** | Checkpoints Panel | `⚖️ Deterministic Diff Subtab`| `#btn-subtab-diff` | Click | Displays snapshot diffing interface | Diff view rendered | Subtab switch | **PASS** |
| **IE-53** | Checkpoints Panel | `💻 Raw Snapshot JSON Subtab`| `#btn-subtab-json` | Click | Displays raw checkpoint JSON | JSON code block rendered | Subtab switch | **PASS** |
| **IE-54** | Streamlit Sidebar | `Execution Mode Radio` | Radio group | Click | Selects Auto / Cloud / Local engine | Session state updated | Reactive rerun | **PASS** |
| **IE-55** | Streamlit Sidebar | `Reflection Iterations Slider`| Slider | Drag / Value | Adjusts iteration bounds (1–5) | Max iterations set to 3 | Reactive rerun | **PASS** |
| **IE-56** | Streamlit Mode A | `📂 Load Workspace Sample` | `button` | Click | Ingests selected workspace module | Source code loaded, AST displayed | Session state update | **PASS** |
| **IE-57** | Streamlit Tabs | `Mode B, C, Wiretap, Obs` | Tabs | Click | Switches active workbench stage | Stage panel renders | Tab change | **PASS** |
| **IE-58** | Swagger UI | `/healthz Try It Out & Execute`| Swagger buttons | Click | Calls GET /healthz interactively | Returns 200 OK with healthy JSON | `GET /healthz` (200) | **PASS** |

