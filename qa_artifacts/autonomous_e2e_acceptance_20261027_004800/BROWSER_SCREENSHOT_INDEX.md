# TestForge — Browser Screenshot Index

**Directory:** `qa_artifacts/autonomous_e2e_acceptance_20261027_004800/screenshots/`  
**Date:** 2026-10-27 01:15:00 IST  

---

## Visual Evidence Registry

| Index | Filename | View / Modal / Component | Key Observable Elements | Acceptance Criteria Linked |
|---|---|---|---|:---:|
| 01 | `01_initial_dashboard.png` | Main Dashboard Overview | Header pills (A2A, MCP, Settings), Mode tabs, Hero CTA, Status pill | Section 6.1 (Page Load) |
| 02 | `02_settings_modal.png` | Settings Configuration Drawer | LLM Model Tier radio buttons, Iteration limits slider, Timeout slider | Section 6.1 (Modals) |
| 03 | `03_a2a_agent_card_modal.png` | A2A AgentCard Modal | Official A2A v0.3.0 schema, capability discovery, JSON preview | MUST 6 (A2A Protocol) |
| 04 | `04_mcp_tools_modal.png` | MCP Tools Drawer | 4 FastMCP tools (read_text_file, list_dir, get_file_info, get_repo_info) | MUST 2 (MCP Integration) |
| 05 | `05_mode_a_workspace.png` | Mode A: Workspace & Upload | File dropzone, preset sample selector, Python syntax highlighting | Phase 4 (Workspace Ingest) |
| 06 | `06_mode_b_synthesis.png` | Mode B: AI Synthesis | Natural language prompt textarea, synthesis tier controls | Section 6.1 (Mode B) |
| 07 | `07_mode_c_github.png` | Mode C: GitHub Direct Import | GitHub repo input, branch selector, fetch CTA | Section 6.1 (Mode C) |
| 08 | `08_blast_radius.png` | Blast Radius & Call Graph | Interactive SVG topology graph, caller-callee links, risk score | MUST 1 / AST Graph |
| 09 | `09_hardening_lab_running.png` | Hardening Lab (Active) | Running state machine, cooperative cancel button, live terminal log | Section 6.2 (State Transitions) |
| 10 | `10_hardening_lab_complete.png`| Hardening Lab (Completed) | Mutation score gauge (63.2%), killed/survived mutant table, test suite | Section 6.2 (Completed State) |
| 11 | `11_wiretap_timeline.png` | Multi-Agent Wiretap | Structured communication handoffs: Google ADK <-> CrewAI Critic | MUST 7 (Wiretap) |
| 12 | `12_telemetry_trace.png` | Observability Trace | OpenTelemetry spans, step execution timings, hardware profile | MUST 10 (Observability) |
| 13 | `13_benchmarking_tab.png` | Benchmarks & Ablation | 3-way ablation study table (Handwritten vs Zero-shot vs Reflection) | MUST 9 & MUST 11 |
| 14 | `14_checkpoints_timeline.png` | Checkpoint History | SQLite Blackboard snapshot cards, monotonic revisions | MUST 1 (Checkpoints) |
| 15 | `15_checkpoint_diff_inspector.png` | Checkpoint Diff Inspector | Side-by-side AST code diff between revision snapshots | MUST 1 (Snapshot Diff) |
| 16 | `16_restore_confirmation_modal.png` | Checkpoint Restore Modal | State restoration warning, revision target confirmation | MUST 1 (State Restore) |
| 17 | `17_mobile_responsive_375x812.png` | Mobile Viewport (375x812) | Responsive stacked layout, collapsible drawer, horizontal overflow 0 | Section 6.3 (Accessibility) |
