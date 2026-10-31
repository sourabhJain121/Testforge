# Phase 4: Complete End-to-End Evaluation Demonstration & Viva Guide

**Project:** TestForge — Autonomous Agentic Mutation Testing & Test Hardening System  
**Evaluation Scope:** Phase 2 Academic and Technical Defense  
**Estimated Demonstration Time:** 5 to 7 Minutes  
**Demonstration Target System:** `logistics_engine.py` (Realistic Warehouse Logistics & Freight Pricing Engine)  
**Target Path:** `qa_artifacts/complete_frontend_acceptance_audit/random_python_target/logistics_engine.py`  

---

## Part 1: Step-by-Step 5–7 Minute Live Demonstration Script

### Pre-Demonstration Environment Setup
1. Open terminal in workspace root `/Users/sourabh/TestForge`.
2. Launch the application:
   ```bash
   ./start_testforge.sh
   ```
   *(Server starts Uvicorn on `http://127.0.0.1:8000/`)*
3. Verify Port 8501 is NOT running (confirming permanent single-frontend architecture):
   ```bash
   lsof -nP -iTCP:8501 -sTCP:LISTEN
   # (Output is completely empty)
   ```
4. Open browser at `http://127.0.0.1:8000/`. Confirm the dark-themed UI loads with green "System Ready" status indicator.

---

### Step 1: System Architecture & Single-Frontend Paradigm (1 Minute)
- **Action:** Point out the header, status indicator, and tab navigation.
- **What to Say:**
  > *"TestForge is an autonomous agentic testing platform that combines Abstract Syntax Tree analysis, a typed partitioned Blackboard, FastMCP tool integration, and mutation testing to autonomously synthesize robust test suites. Notice our single-frontend architecture running purely on FastAPI and vanilla JavaScript with zero Streamlit overhead, communicating asynchronously via WebSockets and REST endpoints."*
- **Visuals:** Highlight the 4 primary view tabs: **Workspace & Pipeline**, **Mutations & Blast Radius**, **Blackboard & Agents**, and **Benchmarks & Quality**.

---

### Step 2: Target Ingestion & AST Analysis (1.5 Minutes)
- **Action:**
  1. In the **Target Ingestion** panel, click **Choose File** and select `qa_artifacts/complete_frontend_acceptance_audit/random_python_target/logistics_engine.py` (or choose `samples/discount.py`).
  2. Click **Ingest & Parse Target**.
- **What to Say:**
  > *"When code is ingested, TestForge uses Python's AST parser to inspect the codebase without executing it. It validates syntax integrity, identifies class structures (`ShippingTier`, `WarehouseInventory`), and extracts individual callable signatures (`calculate_item_discount`, `estimate_freight_cost`, `calculate_customs_duty`, `validate_tracking_number`, `compute_sla_deadline_hours`, `process_bulk_order`), calculating cyclomatic complexity and line counts."*
- **Observed Output:**
  - Status banner turns green: `Ingested uploaded_logistics_engine.py (240 lines, 2 classes, 6 functions, 11 callables)`.
  - Ingestion Summary displays full class and function inventories.

---

### Step 3: Blast Radius & FastMCP Tool Inspection (1 Minute)
- **Action:**
  1. Switch to the **Mutations & Blast Radius** tab.
  2. Select target function `estimate_freight_cost` and click **Calculate Blast Radius**.
  3. Click **Inspect MCP Tools** in the top navigation bar.
- **What to Say:**
  > *"Before synthesizing tests, TestForge determines static blast radius to prioritize risk paths. For `estimate_freight_cost`, it identifies 1 upstream caller (`process_bulk_order`) and 3 downstream callees across 30 dependency nodes. Furthermore, our agents operate using the Model Context Protocol (FastMCP) with 4 tools across Filesystem and GitHub servers, enforcing strict private IP blocking and 5MB streaming download limits."*
- **Observed Output:**
  - Interactive dependency graph renders affected caller and callee nodes.
  - MCP modal renders active registered tools (`read_text_file`, `list_directory`, `get_file_info`, `get_repository_info`).

---

### Step 4: Autonomous Test Generation & Mutation Testing (2 Minutes)
- **Action:**
  1. Return to the **Workspace & Pipeline** tab.
  2. Select Mode: **Autonomous Hardening Loop**.
  3. Click **Start Hardening Pipeline**.
- **What to Say:**
  > *"The Orchestrator dispatches the Test Generator Agent. Notice our multi-tier fallback architecture: when operating in local evaluation mode without paid API keys, the system seamlessly engages its deterministic AST rule synthesizer. Notice the quality of the tests: rather than monolithic functions or hollow assertions, TestForge generates discrete scenario tests targeting normal inputs, boundary conditions (such as the 5, 20, 50 item discount breaks and modulo-7 tracking checks), and exception handling (`ValueError` on invalid tiers). The test suite is executed in an isolated subprocess sandbox, after which the AST mutator introduces 9 distinct fault operators to measure true defect detection."*
- **Observed Output:**
  - Real-time WebSocket terminal streams agent lifecycle transitions (`AGENT_START`, `MUTATION_EVALUATION`).
  - Unit test card displays **18 / 18 tests passed** (100% pass rate).
  - Mutation summary card reports 258 mutants generated and a strong initial mutation kill rate.

---

### Step 5: Blackboard State Sharing & A2A Discovery (1 Minute)
- **Action:**
  1. Switch to the **Blackboard & Agents** tab.
  2. Open a separate browser tab to `http://127.0.0.1:8000/.well-known/agent-card.json`.
- **What to Say:**
  > *"Every pipeline step updates a dedicated Blackboard partition protected by reentrant locks and saved to SQLite checkpoints, allowing rollbacks and diff inspection. Finally, TestForge exposes an Agent-to-Agent (A2A) protocol Agent Card, making the entire system discoverable by external multi-agent networks."*
- **Observed Output:**
  - Blackboard shows live partition data across `TargetSpace`, `MutantSpace`, `CriticSpace`, `SuiteSpace`, and `MetricsSpace`.
  - JSON Agent Card renders compliant schema with name `testforge-agent-system` and protocol version `0.3.0`.

---

## Part 2: Safe Failure Demonstration (Task 4.3)

- **Demonstration:**
  1. In **Target Ingestion**, upload `samples/uploaded_08_syntax_error.py`.
  2. Click **Ingest & Parse Target**.
- **Evaluator Observation:**
  - The UI cleanly catches the error: `SyntaxError on line 1: invalid syntax`.
  - Server status remains 100% stable (HTTP 200 with `has_syntax_error=True`); zero server crashes or unhandled 500 exceptions occur.
  - TestForge refuses to generate tests on broken syntax, preventing wasted compute.

---

## Part 3: Offline Contingency & Fallback Strategy (Task 4.4)

| Scenario | System Fallback Behavior |
|---|---|
| **No Internet Connection** | 100% of the demonstration operates offline. All dependencies, AST mutators, and subprocess sandboxes run on the local machine. |
| **No External LLM API Keys** | The 4-tier LLM fallback hierarchy automatically routes test synthesis and critic tasks to the deterministic AST rule synthesizer and structured critic generator at **$0.00 cost**. |
| **Port 8000 in Use** | Kill stale process via `kill $(lsof -t -i:8000)` and re-run `./start_testforge.sh`. |

---

## Part 4: Comprehensive Viva Defense Q&A (Task 4.5)

### 1. Why did you build TestForge?
**Answer:**  
Standard testing relies on human developers writing manual unit tests, which frequently miss boundary conditions, inverted logic, and edge cases. TestForge automates this process using an agentic feedback loop: it parses Python AST, synthesizes targeted test suites, evaluates them against artificial faults (mutants), and iteratively hardens assertions until logic gaps are closed.

### 2. How is TestForge different from standard pytest?
**Answer:**  
`pytest` is a test *runner* and assertion framework; it only executes tests written by developers. TestForge is an autonomous *test engineering system* that writes the tests, discovers system call graphs, introduces AST mutants to stress-test those tests, and coordinates multiple AI agents to iteratively improve test quality.

### 3. Why use multiple agents instead of a single script or LLM call?
**Answer:**  
A single prompt cannot reliably handle code parsing, call graph analysis, test synthesis, execution sandbox management, and adversarial defect reasoning without hallucination. TestForge uses specialized agents: `TargetManagerAgent` handles AST decomposition, `TestGeneratorAgent` focuses on assertion design, and `CrewAICriticAgent` focuses exclusively on diagnosing why surviving mutants escaped.

### 4. How does the Blackboard architecture work?
**Answer:**  
In `testforge/blackboard.py`, the Blackboard decouples agents by providing five strongly-typed state spaces: `TargetSpace`, `MutantSpace`, `CriticSpace`, `SuiteSpace`, and `MetricsSpace`. Agents never invoke each other directly; they read from and write to their designated spaces under thread-safe reentrant locks (`threading.RLock()`), with updates triggering reactive subscriber callbacks.

### 5. How do agents share intermediate outputs?
**Answer:**  
When `ASTMutator` finishes, it writes surviving mutant diffs to `MutantSpace`. `CrewAICriticAgent` reads those diffs, analyzes the failure mechanisms, and writes structured directives to `CriticSpace`. `TestGeneratorAgent` then consumes `CriticSpace` directives to write hardened tests into `SuiteSpace`.

### 6. What is MCP (Model Context Protocol)?
**Answer:**  
MCP is an open standard created by Anthropic that allows AI agents to securely connect to external tools and data sources. In TestForge (`testforge/mcp_server.py`), FastMCP exposes standardized file system and GitHub inspection tools with validated Pydantic schemas.

### 7. What is A2A (Agent-to-Agent Protocol)?
**Answer:**  
A2A is an interoperability protocol for autonomous agent discovery. Implemented in `testforge/a2a_protocol.py` and served at `/.well-known/agent-card.json`, it publishes TestForge's skills (`unit-test-generation`, `mutation-critique`), communication protocols, and capabilities so external agent swarms can discover and delegate tasks to it.

### 8. How are MCP and A2A different?
**Answer:**  
MCP standardizes how an *agent talks to tools and resources* (client-to-tool boundary). A2A standardizes how *agents talk to other agents* (agent-to-agent discovery and delegation boundary). TestForge implements both.

### 9. Why use Pydantic for structured outputs?
**Answer:**  
LLMs often produce free-form text or invalid markdown. By enforcing Pydantic models (`MutantRecord`, `CriticDirectivePayload`, `GeneratedTestPayload`), TestForge validates schemas at runtime, rejecting malformed data before it can corrupt state.

### 10. How do callbacks work in TestForge?
**Answer:**  
Implemented in `testforge/callbacks.py`, the `CallbackRegistry` tracks 20 distinct `EventType` states (e.g. `AGENT_START`, `MUTATION_EVALUATION`, `CHECKPOINT_SAVED`). Handlers register with specific priorities and safe error modes (`raise_on_error=False`), streaming events to WebSockets and the JSONL trace log.

### 11. Why use mutation testing instead of line coverage?
**Answer:**  
Line coverage only proves that a line of code was executed, not that a bug would be detected. Mutation testing modifies the AST (e.g. swapping `>` to `>=`, changing arithmetic operators, or altering constants). If tests fail on the mutant, it is **killed**; if tests pass, the mutant **survives**, proving the test suite has a semantic blind spot.

### 12. How do you measure test quality?
**Answer:**  
Through the **Mutation Score**:
$$\text{Mutation Score} = \frac{\text{Killed Mutants}}{\text{Total Mutants}} \times 100\%$$
In addition, we compute the **Adjusted Mutation Score** by classifying and removing *equivalent mutants* (mutants that are syntactically different but semantically identical) from the denominator.

### 13. How do SSRF protections work in TestForge?
**Answer:**  
In `testforge/network_security.py` and `testforge/mcp_server.py`, all external URL requests pass through a custom opener that resolves DNS hostnames and verifies they do not map to loopbacks (`127.0.0.1`), private RFC 1918 networks (`10.0.0.0/8`, `192.168.0.0/16`), or cloud metadata services (`169.254.169.254`). Only approved GitHub hostnames are allowed, and downloads are strictly bounded to 5MB.

### 14. How do you defend against indirect prompt injection?
**Answer:**  
In `testforge/prompt_guard.py`, untrusted code files and comments are scanned for injection patterns (`IGNORE PREVIOUS INSTRUCTIONS`, shell command escapes). Detected payloads are defused, and all untrusted data is encapsulated in explicit `<untrusted_content>` tags before prompt construction, instructing the LLM to treat them strictly as passive data.

### 15. What happens when an agent fails or times out?
**Answer:**  
TestForge employs multi-tiered containment:
1. `SubprocessSandbox` enforces a 5–10 second timeout on test execution.
2. The 4-tier LLM fallback hierarchy automatically fails over from Gemini to OpenRouter to Ollama to the AST deterministic synthesizer.
3. Errors are caught, logged to `testforge_trace.jsonl`, and displayed in the UI without crashing the server.

### 16. What are the limitations of the current system?
**Answer:**  
1. **Local Evaluation Boundary:** Multi-stage Docker containers are configured and tested, but the evaluation is conducted locally rather than on a public cloud URL.
2. **Offline Fallback Scope:** While the offline deterministic synthesizer handles mathematical, boundary, and domain-modeled scenarios cleanly, novel arbitrary business logic requires live LLM tiers for full semantic depth.

### 17. What would you improve after Phase 2?
**Answer:**  
1. Implement Phase 2C: Automated GitHub Pull Request creation and CI/CD bot actions.
2. Expand the equivalent mutant classifier using formal Z3 SMT solver theorem proving.
3. Add support for multi-file repository projects beyond single modules.

