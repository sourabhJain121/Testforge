# TESTFORGE — TEACHER DEMONSTRATION RUNBOOK

**Target Audience:** Professor / Project Evaluators / External Examiners  
**Presenter:** B.Tech Student / Software Engineer  
**Estimated Presentation Duration:** 15–20 minutes  
**Mode:** Live Browser Interactive Demonstration against Local Server  

---

## 1. Demonstration Setup & Pre-Flight Check

1. Open Terminal and start the backend:
   ```bash
   .venv-release/bin/python server.py
   ```
2. Open Google Chrome and navigate to:
   ```
   http://127.0.0.1:8000
   ```
3. Verify that the hardware status pill shows **Apple Silicon arm64 (NEON accelerated)** and the Gemini status indicator is green.

---

## 2. Step-by-Step Demonstration Sequence

| Step | Time | Screen / Control | Action to Perform | Teacher-Facing Explanation | Requirement Demonstrated |
|---|---|---|---|---|---|
| **1** | 1 min | Landing Page & Header | Point to header title, status pills, and architecture badge. | *"TestForge is an autonomous, multi-agent test hardening system that discovers edge-case bugs using AST mutation analysis and agentic reflection."* | Req 11 (Deployment & Health) |
| **2** | 1 min | Header: A2A Card Button | Click **🤖 A2A Agent Card**. Inspect rendered JSON. | *"TestForge implements the Agent-to-Agent (A2A) discovery standard at `/.well-known/agent-card.json`, allowing other autonomous agents to discover our capabilities."* | Req 6 (A2A Discovery) |
| **3** | 1 min | Header: MCP Tools Button | Click **🔌 FastMCP Tools**. Inspect tool list. | *"We integrate the Model Context Protocol (MCP) using genuine FastMCP tools: `validate_ast_syntax` and `run_isolated_pytest`."* | Req 2 (MCP Integration) |
| **4** | 2 min | Mode A: Workspace Target | Select `banking.py` from dropdown, click **Load Sample Module**. | *"Mode A loads local or built-in Python modules, computes an AST breakdown of classes and functions, and displays the source code preview."* | Req 3 (Structured AST Analysis) |
| **5** | 1 min | Mode A: Git Diff Toggle | Toggle **Git Diff-Aware Target**. | *"TestForge can isolate only modified functions from git diffs, saving compute by testing changed code paths first."* | Req 4 (Agentic Design Patterns) |
| **6** | 2 min | Blast Radius Tab | Click **Blast Radius & Call Graph**. Select `apply_interest`. | *"Before writing tests, our Blast Radius analyzer traverses the Abstract Syntax Tree to calculate reachability and risk metrics."* | Req 9 (Provenance & Lineage) |
| **7** | 3 min | Hardening Lab Tab | Switch sample to `discount.py` and click **🚀 Run Autonomous Hardening**. | *"Here the Orchestrator executes our multi-agent pipeline: Generator synthesizes tests, Critic reviews edge cases via CrewAI, Mutator generates AST mutants, and Sandbox isolates execution."* | Req 1, 4, 7 (Blackboard, Reflection, CrewAI) |
| **8** | 2 min | Hardening Lab: Results | Show KPI score (100%), click mutant row to show Unified Diff. | *"The unified diff viewer shows exactly what changed in the AST (e.g. relational operator mutation `<= -> <`), and confirms our test killed the mutant."* | Req 1, 3, 9 (Mutation Analysis, Structured Output) |
| **9** | 2 min | Multi-Agent Wiretap | Click **Multi-Agent Wiretap**. Show handoffs. | *"This provides full observability: you can see the exact handoffs between Orchestrator, ADK Generator, CrewAI Critic, and Sandbox via WebSocket streaming."* | Req 1, 5, 9 (Wiretap, Callbacks, Observability) |
| **10** | 1 min | Checkpoints Tab | Click **Blackboard Checkpoints**. Click a snapshot row. | *"Every state transition is persisted in SQLite with WAL journaling. We can inspect point-in-time state or restore previous stages without restarting."* | Req 1 (Persistent Blackboard) |
| **11** | 2 min | Benchmarking Tab | Click **Statistical Benchmarking**. Show table. | *"We empirically compared Baseline, Zero-Shot, and Agentic Reflection across a 5-fixture controlled defect corpus. Reflection achieves superior mutation scores."* | Req 4, 10 (Empirical Benchmarking) |
| **12** | 1 min | Test Suite Evidence | Show the terminal or report: 395 passed tests. | *"All 11 teacher rubric requirements are validated with 395 passing automated tests and zero failures."* | All 11 Requirements |

---

## 3. Failure Recovery Instructions

- If a port is occupied: Check running processes with `lsof -i :8000` and stop the older instance.
- If Chrome displays cached state: Press `Cmd+Shift+R` to force-reload the frontend.
- If database needs clean slate: Remove `testforge_blackboard.db` and restart `server.py` (it will auto-initialize cleanly).
