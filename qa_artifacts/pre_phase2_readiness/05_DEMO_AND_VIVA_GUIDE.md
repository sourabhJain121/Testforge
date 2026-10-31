# Stage 9: Live Demonstration Script & Viva Defense Guide

**Project:** TestForge — Agentic LLM-Driven Autonomous Mutation Testing System  
**Audience:** Academic Evaluators, Senior Quality Architects, Project Review Panel  
**Estimated Demo Time:** 5 to 7 Minutes  
**Target Environment:** Local macOS / Linux, FastAPI (`http://127.0.0.1:8000/`), Port 8501 disabled  

---

## Part 1: Step-by-Step 5–7 Minute Live Demonstration Script

### Setup Before Evaluators Arrive
1. Open terminal in workspace root `/Users/sourabh/TestForge`.
2. Start the FastAPI server:
   ```bash
   ./start_testforge.sh
   ```
   *(Or `.venv-release/bin/python -m uvicorn server:app --host 127.0.0.1 --port 8000`)*
3. Verify server responds:
   - Open browser at `http://127.0.0.1:8000/`.
   - Ensure header displays **"TestForge"**, status indicator shows **"System Ready"**, and port 8501 is NOT running.

---

### Step 1: System Overview & Architecture (1 Minute)
- **Action:** Point to the main dashboard at `http://127.0.0.1:8000/`.
- **What to Say:**
  > *"TestForge is an autonomous agentic test engineering platform. It uses a partitioned Blackboard architecture, FastMCP tool integration, and a multi-agent feedback loop (Target Manager, Test Generator, and CrewAI Critic) to automatically synthesize robust unit test suites, evaluate them with AST mutation testing, and iteratively harden code against subtle logic faults."*
- **Visual Evidence:** Highlight the 4 tabs: **Workspace & Pipeline**, **Mutations & Blast Radius**, **Blackboard & Agents**, and **Benchmarks & Quality**.

---

### Step 2: Ingestion & AST Analysis (1.5 Minutes)
- **Action:** 
  1. In the **Target Ingestion** panel, click **Select Sample Target** dropdown and choose `samples/discount.py` (or click **Choose File** and upload `qa_artifacts/complete_frontend_acceptance_audit/random_python_target/logistics_engine.py`).
  2. Click **Ingest & Parse Target**.
- **What to Say:**
  > *"Upon ingestion, TestForge parses the Python code into an Abstract Syntax Tree (AST). It extracts classes, functions, and docstrings, verifies syntax integrity, and determines the call graph and blast radius before any generation begins."*
- **Expected Output:**
  - Status banner turns green: `Ingested samples/discount.py (20 lines, 1 function)`.
  - Ingestion summary displays extracted callables (`calculate_discount`) and complexity metrics.

---

### Step 3: Blast Radius Call Graph & FastMCP Tools (1 Minute)
- **Action:**
  1. Switch to the **Mutations & Blast Radius** tab.
  2. Click **Calculate Blast Radius**.
  3. Click **Inspect MCP Tools** in the top-right tool bar.
- **What to Say:**
  > *"TestForge computes directional blast radius — identifying upstream callers and downstream callees to focus test generation on the highest-risk execution paths. Furthermore, our agents interact with files and repos via FastMCP protocol servers, protected by strict SSRF filters and bounded 5MB download guards."*
- **Expected Output:**
  - Interactive Graph visualization renders affected dependency nodes.
  - MCP modal displays 4 active tools across Filesystem and GitHub servers.

---

### Step 4: Autonomous Test Synthesis & Mutation Execution (2 Minutes)
- **Action:**
  1. Return to **Workspace & Pipeline**.
  2. Select Mode: **Autonomous Hardening Loop**.
  3. Click **Start Hardening Pipeline**.
- **What to Say:**
  > *"The Supervisor Agent dispatches the Test Generator. Notice our 4-tier fallback architecture: if external LLM APIs are offline or unconfigured, the system engages its deterministic AST rule synthesizer seamlessly without interrupting the evaluation. The test suite is executed inside an isolated subprocess sandbox, after which the AST Mutator introduces 9 distinct mutation operators (comparison swaps, condition inversions, boundary checks) to measure true test quality."*
- **Expected Output:**
  - Real-time event log streams agent state transitions via WebSocket.
  - Test execution card shows 100% test pass rate.
  - Mutation summary card displays mutants generated, killed count, and mutation score.

---

### Step 5: Checkpoints, Observability & A2A Discovery (1 Minute)
- **Action:**
  1. Switch to the **Blackboard & Agents** tab.
  2. View the partitioned state spaces: Target, Mutant, Critic, Suite, Metrics.
  3. In a separate browser tab, navigate to: `http://127.0.0.1:8000/.well-known/agent-card.json`.
- **What to Say:**
  > *"Every pipeline step updates a dedicated Blackboard partition protected by reentrant locks and persisted to SQLite checkpoints, enabling state diffing and recovery. Finally, TestForge exposes an A2A-compliant Agent Card, making it discoverable and interoperable with other agentic ecosystems."*
- **Expected Output:**
  - Blackboard shows live partition data with timestamped updates.
  - JSON Agent Card renders with name `testforge-agent-system` and protocol version `0.3.0`.

---

### Demo Fallback & Contingency Plan
| What could happen | Contingency Action |
|---|---|
| **External LLM rate limit or no API key** | No action required! The 4-tier fallback chain immediately routes to the deterministic AST rule synthesizer. Everything executes locally at zero cost. |
| **Port 8000 already occupied** | Run `kill $(lsof -t -i:8000)` and re-run `./start_testforge.sh`. |
| **Network disconnected** | System operates 100% offline; all dependencies and sandboxes are local. |

---

## Part 2: Comprehensive Viva Defense Q&A

### Q1: What makes TestForge an "Agentic" system rather than a simple script?
**Answer:**  
TestForge is agentic because it incorporates autonomous decision-making through decoupled, specialized agents:
1. **TargetManagerAgent** decomposes complex inputs, validates AST constraints, and computes blast radius.
2. **TestGeneratorAgent** plans and synthesizes targeted test strategies.
3. **CrewAICriticAgent** evaluates surviving mutants, reasons about test deficiencies, and formulates natural-language/structured directives to guide subsequent test synthesis iterations.
4. Agents coordinate asynchronously through a partitioned **Blackboard** (`testforge/blackboard.py`), avoiding hard-coded procedural calls.

---

### Q2: How does the Blackboard architecture work in TestForge?
**Answer:**  
Implemented in `testforge/blackboard.py`, the Blackboard is partitioned into five distinct state spaces:
- `TargetSpace`: Raw source, AST metadata, callables, line counts.
- `MutantSpace`: Generated AST mutants, status (`KILLED`, `SURVIVED`, `EQUIVALENT`).
- `CriticSpace`: Critic observations, surviving mutant guidance, recommendations.
- `SuiteSpace`: Current test suite code, past iterations, quarantined tests.
- `MetricsSpace`: Pass rates, mutation scores, execution latencies.
All updates are synchronized via thread locks (`threading.RLock`) and dispatch reactive callback notifications across agent boundaries.

---

### Q3: What is Mutation Testing and why is it superior to code coverage?
**Answer:**  
Standard line or branch coverage only measures whether code was *executed*, not whether the tests would *catch a bug* if the logic changed. Mutation testing introduces deliberate syntactic faults (mutants) into the AST (e.g. changing `>` to `>=`, `+` to `-`, or swapping booleans). If the test suite fails when run against the mutated code, the mutant is **killed**; if the suite passes, the mutant **survives**, indicating a test gap. The **Mutation Score** (`Killed / Total Mutants`) provides a true qualitative measure of test effectiveness.

---

### Q4: How do you identify and handle "Equivalent Mutants"?
**Answer:**  
An equivalent mutant is syntactically distinct but semantically identical to the original program (e.g. `for i in range(0, 10)` vs `for i in range(10)`), meaning no test can ever kill it. Counting them artificially depresses the mutation score.  
In `testforge/equivalence.py`, TestForge employs a multi-tiered classifier:
1. **AST Pattern Matching**: Identifies known algebraic/logical tautologies.
2. **Behavioral Equivalence Profiling**: Compares execution profiles and I/O states.
3. **Adjusted Mutation Score**: Computed as `Killed / (Total Mutants - Equivalent Mutants)`, providing an academically rigorous metric.

---

### Q5: How does the 4-tier Fallback Hierarchy prevent system failure?
**Answer:**  
In `testforge/llm.py` and `testforge/agents.py`, TestForge implements a graceful failover chain:
- **Tier 1:** Primary frontier model (Google Gemini `gemini-2.5-flash` via Google ADK / GenAI API).
- **Tier 2:** Secondary multi-provider API (OpenRouter).
- **Tier 3:** Local offline LLM (Ollama / local model inference).
- **Tier 4:** Deterministic AST Rule Synthesizer.  
If any tier times out, throws a 429 rate limit, or lacks credentials, the system automatically degrades to the next tier without throwing unhandled exceptions.

---

### Q6: How are tool calls handled and what is FastMCP's role?
**Answer:**  
TestForge uses the Model Context Protocol (FastMCP) in `testforge/mcp_server.py` and `testforge/mcp_client.py` to decouple agent tool execution. FastMCP exposes standardized tools (`read_file_tool`, `list_dir_tool`, `fetch_github_file_tool`). FastMCP standardizes tool schemas, input validation via Pydantic, and lifecycle management while allowing agents to run in sandboxed contexts.

---

### Q7: What security protections are implemented against SSRF and Prompt Injection?
**Answer:**  
Implemented in `testforge/network_security.py` and `testforge/prompt_guard.py`:
- **Core SSRF:** Strict IP validation rejects loopback (`127.0.0.1`), private RFC 1918 ranges, and cloud metadata endpoints (`169.254.169.254`). Hostnames are strictly checked against an approved GitHub allowlist.
- **Bounded Downloads:** Stream reader enforces a hard 5MB limit to prevent memory exhaustion attacks.
- **Indirect Prompt Injection:** The prompt guard scans untrusted source files and comments for malicious jailbreaks, markdown exfiltration, and directive overrides (`# IGNORE PREVIOUS INSTRUCTIONS`), defusing them before prompt synthesis.

---

### Q8: How does the Subprocess Sandbox ensure safety during test execution?
**Answer:**  
In `testforge/sandbox.py`, tests and mutants are never executed directly within the server process. Instead, each run:
1. Creates an isolated temporary directory in `/tmp/testforge_box_*`.
2. Writes isolated copies of the target code and test suite.
3. Spawns an isolated Python child process with hard execution timeouts (e.g. 5–10 seconds) to terminate infinite loops.
4. Collects structured test results via standard JSON/Pytest output and immediately unlinks the temporary environment.

---

### Q9: Why was Streamlit disabled in favor of FastAPI + Vanilla HTML/JS?
**Answer:**  
Streamlit re-runs the entire Python script on every user interaction, causing severe state thrashing, race conditions with background agent threads, and WebSocket instability. Migrating to FastAPI (`server.py`) and a lightweight vanilla JS frontend provides:
- Clean asynchronous event handling via native WebSockets (`/ws/events`).
- Decoupled REST endpoints for individual pipeline stages.
- Sub-10ms UI responsiveness with zero frontend framework overhead.
- True production-grade architecture deployable in standard containers.

---

### Q10: How does TestForge support reproducibility and evaluation benchmarking?
**Answer:**  
TestForge features two persistent persistence engines:
1. **SQLite State Checkpointing** (`testforge/persistence.py`): Stores complete snapshots of Blackboard spaces at every iteration with rollbacks and state diffing (`testforge/diff_inspector.py`).
2. **Trace Logging & Multi-Run Benchmarking** (`testforge/logger.py` & `testforge/benchmarking.py`): Logs JSONL telemetry with correlation IDs and saves multi-run scenario benchmarks to `benchmark_results.json`.

