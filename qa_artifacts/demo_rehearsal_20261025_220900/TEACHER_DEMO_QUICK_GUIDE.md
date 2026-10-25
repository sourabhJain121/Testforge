# TESTFORGE — TEACHER DEMONSTRATION QUICK GUIDE

**Presenter Cheat Sheet**  
**Estimated Presentation Time:** 12–15 minutes  
**Server URL:** `http://127.0.0.1:8000/`  

---

### Step 1: System Status & Hardware Architecture
- **Click:** Look at the top-left header.
- **Say:** *"Professor, TestForge is an autonomous test hardening engine. It detects Apple Silicon arm64 hardware with NEON vectorization and verifies our background services are online."*
- **Screen:** Header shows `Darwin arm64 (10 cores, 16GB)` pill and a green `Gemini Engine` indicator.
- **Fallback:** If offline, start server with `.venv-release/bin/python server.py`.

### Step 2: Agent-to-Agent (A2A) Discovery Protocol
- **Click:** **🤖 A2A Agent Card** button in the header.
- **Say:** *"TestForge implements the A2A Discovery Standard draft at `/.well-known/agent-card.json`. Other agents can query our card to discover our capabilities, endpoints, and authentication schema."*
- **Screen:** Modal opens displaying formatted JSON agent card.
- **Click:** Close modal (×).

### Step 3: Model Context Protocol (FastMCP) Tools
- **Click:** **🔌 FastMCP Tools** button in the header.
- **Say:** *"We use the Model Context Protocol (MCP) to decouple tools. We expose two genuine FastMCP tools: `validate_ast_syntax` for AST safety and `run_isolated_pytest` for sandboxing."*
- **Screen:** Modal opens showing FastMCP operational status and tools.
- **Click:** Close modal (×).

### Step 4: System Hyperparameters & Settings
- **Click:** **⚙️ Settings** button in the header.
- **Say:** *"Here developers can configure the reflection iteration limit, target mutation threshold, and switch between foundation models or local offline execution."*
- **Screen:** Settings drawer slides in with sliders and engine selects.
- **Click:** Cancel / Close Settings.

### Step 5: Mode A Workspace Ingestion
- **Click:** **Mode A: Workspace & Upload** tab. Select `banking.py` from dropdown and click **Load Sample**.
- **Say:** *"In Mode A, we ingest local Python files. Our AST parser extracts exported functions, classes, and methods, and renders an interactive code display."*
- **Screen:** Active target hero updates to `samples.banking`, listing `banking_transaction`.

### Step 6: Git Diff-Aware Targeting
- **Click:** **Git Diff-Aware Target** toggle.
- **Say:** *"For large legacy repositories, TestForge isolates modified lines from `git diff`, allowing the multi-agent loop to focus test synthesis strictly on recent changes."*
- **Screen:** Blue callout box displays working tree status.

### Step 7: Mode B AI Module Synthesis
- **Click:** **Mode B: AI Synthesis** tab.
- **Click:** Quick template chip: **Token Bucket Rate Limiter**. Click **🚀 Synthesize Module**.
- **Say:** *"Mode B synthesizes Python modules directly from natural language specifications using our TargetManagerAgent, with full type hints and boundary conditions."*
- **Screen:** Callout shows synthesis progress, then displays the generated Python code container.

### Step 8: Mode C Direct GitHub Ingestion
- **Click:** **Mode C: GitHub Direct Import** tab.
- **Click:** Prompt chip: `requests/status_codes.py`. Click **⬇️ Fetch & Ingest**.
- **Say:** *"Mode C ingests public GitHub files. It normalizes GitHub URLs, fetches raw source, audits imports, and calculates AST line counts."*
- **Screen:** Displays 128 lines, class chips, and activates target. Click **🎯 Target Confirmed for Hardening**.

### Step 9: Blast Radius Call Graph Analysis
- **Click:** **💥 Blast Radius & Call Graph** tab.
- **Say:** *"Before synthesizing tests, our AST crawler computes call graph depth, reachability, and a blast radius risk score to prioritize high-risk functions."*
- **Screen:** Hierarchical call tree renders with a risk badge (`🟢 LOW` / `🟡 MEDIUM`).

### Step 10: Autonomous Hardening Lab Execution
- **Click:** **🔥 Hardening Lab & Results** tab. (Switch back to `discount.py` for standard run). Click **⚡ Run TestForge Autonomous Hardening**.
- **Say:** *"Now the core orchestration runs: Google ADK synthesizes tests, CrewAI evaluates boundary edge cases, AST Mutator injects faults, and our parallel sandbox tests mutants."*
- **Screen:** Animated progress bar shows stages, finishing with KPI cards (Mutation Score, Killed Mutants, Total Mutants).
- **Click:** Click any row in the **AST Mutation Audit** table.
- **Say:** *"Clicking a mutant displays the exact unified AST diff showing what operator was mutated (e.g. `<= -> <`), and confirms our test killed the defect."*
- **Screen:** Unified AST diff viewer shows colored diff lines.

### Step 11: Multi-Agent Wiretap Timeline
- **Click:** **🤖 Multi-Agent Wiretap** tab. Click **🔄 Refresh Wiretap**.
- **Say:** *"The Wiretap provides complete visibility into inter-agent handoffs between Orchestrator, Generator, Critic, Mutator, and Sandbox."*
- **Screen:** Interactive timeline cards show the exact chronological handoff chain.

### Step 12: Observability Trace & Provenance
- **Click:** **📊 Observability Trace** tab. Click **🔄 Refresh Telemetry**.
- **Say:** *"Every agent decision and execution timestamp is logged into `testforge_trace.jsonl` with API keys automatically redacted."*
- **Screen:** Telemetry table renders with timestamps, latency, and event types.

### Step 13: Statistical Benchmarking & Ablation
- **Click:** **⚡ Benchmarks & Ablation** tab. Click **🔄 Refresh Results**.
- **Say:** *"We empirically compared Baseline, Zero-Shot, and Agentic Reflection. Reflection consistently achieves superior mutation scores by actively closing coverage holes."*
- **Screen:** Table renders all 3 conditions with mutation scores, token costs, and markdown preview.

### Step 14: Blackboard Checkpointing & Recovery
- **Click:** **💾 Checkpoint Timeline & Diff** tab. Click **🔄 Refresh Checkpoints**.
- **Say:** *"All Blackboard states are persisted in SQLite with WAL journaling. We can inspect any revision's raw JSON snapshot or restore point-in-time state."*
- **Screen:** 100 versioned checkpoint cards render. Click a card, then click **Raw Snapshot JSON** to show serialized state.

### Step 15: Concluding Verification
- **Say:** *"All 11 teacher rubric requirements are supported by 395 passing automated tests and zero defects. TestForge is fully functional, secure, and ready for deployment."*
