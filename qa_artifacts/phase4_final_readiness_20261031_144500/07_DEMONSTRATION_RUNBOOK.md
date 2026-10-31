# TestForge Phase 4: 10–15 Minute Live Academic Demonstration Runbook

**Audience:** Academic Evaluators, Senior Software Architects, QA Automation Leads.  
**Demonstration Time:** 10–15 Minutes.  
**Target Host:** `http://127.0.0.1:8000/`  

---

## 1. Demonstration Narrative & Core Objective

The purpose of this demonstration is to showcase TestForge as an autonomous, multi-agent test hardening system that bridges code coverage and defect detection.

### Core Message for Evaluators:
> *"Code coverage only tells you which lines were executed; it tells you nothing about whether your tests actually check the results. A test suite with 100% line coverage can have a 0% mutation score if assertions are tautological (`assert res is not None`). TestForge uses Google ADK and CrewAI agents coordinated over a shared Blackboard to autonomously discover boundaries, synthesize value-aware assertions, and evaluate test suites against realistic AST mutations."*

---

## 2. Step-by-Step 12-Minute Demonstration Script

### Minute 00:00–02:00: Architecture Overview & Discovery
1. **Open Frontend:** Navigate to `http://127.0.0.1:8000/`.
   - *What to Point Out:* Hardware acceleration pill (Apple Silicon M-series), FastAPI single-port architecture, and zero-dependency offline mode.
2. **Demonstrate A2A Discovery:** Click **🤖 A2A Card** button.
   - *What to Point Out:* Conformance with official A2A protocol `v0.3.0`. Point out the three declared skills (`unit-test-generation`, `mutation-critique`, `hardening-workflow`).
   - *Action:* Click **"▶️ Test A2A Connection"** to show real-time JSON-RPC handshake verification.
3. **Demonstrate FastMCP Tools:** Click **🔌 MCP Tools ( 4 )** button.
   - *What to Point Out:* FastMCP integration (`v1.28.0`), four registered tools, and strict filesystem isolation confining access to `samples/`.

---

### Minute 02:00–05:00: Fast Nominal Run (`discount.py`)
1. **Load Target:** In **Mode A: Workspace & Upload**, select `discount.py` and click **"Load Sample"**.
   - *What to Point Out:* AST line counts (21 lines) and callable discovery token: `calculate_discount`.
2. **Inspect Blast Radius:** Switch to **💥 Blast Radius & Call Graph** tab.
   - *What to Point Out:* Static analysis tree showing risk score, callees, and dependency impact.
3. **Execute Autonomous Hardening:** Switch to **🔥 Hardening Lab & Results** tab and click **"⚡ Run Hardening Pipeline"**.
   - *What to Point Out:* Watch the progress bar transition through lifecycle stages:
     `INITIALIZING` $\to$ `GENERATING_TESTS` (Google ADK) $\to$ `VALIDATING` $\to$ `EXECUTING` (Parallel Sandbox) $\to$ `TARGET ACHIEVED`.
   - *Key Metrics on KPI Board:*
     - Generated Tests: **11**
     - Pass Rate: **11/11 (100% Pass@1)**
     - Statement Coverage: **100.0%**
     - Mutants: **19 generated, 17 killed, 2 survived**
     - Raw Mutation Score: **89.47%** (or **94.7%** under dynamic refinement)
     - Execution Duration: **~1.2 seconds**.

---

### Minute 05:00–09:00: Enterprise Multi-Callable Run (`uploaded_logistics_engine.py`)
1. **Ingest Custom Target:** In **Mode A**, select **"Upload Custom .py"** and upload `samples/uploaded_logistics_engine.py` (8.1 KB).
   - *What to Point Out:* Real-world complexity: 2 classes (`ShippingTier`, `WarehouseInventory`) and 6 module-level functions (10 total eligible callables).
2. **Run Hardening:** Switch to **🔥 Hardening Lab & Results** and click **"⚡ Run Hardening Pipeline"**.
   - *Explain the Reflection Loop:*
     - Iteration 1 generates initial baseline tests and executes 258 AST mutants across 8 CPU workers.
     - The Critic Agent (CrewAI) inspects surviving mutant diffs and sends targeted repair instructions back to the Blackboard.
     - The Generator Agent (Google ADK) synthesizes discriminating boundary inputs for customs duty thresholds (\$800, \$2,500) and SLA formulas.
   - *Key Metrics to Highlight:*
     - Discovered Callables Covered: **10/10 (100.0% callable coverage, 0 skipped)**.
     - Generated Tests: **64 tests**.
     - Mutants Killed: **176/258 killed**.
     - Raw Mutation Score: **68.22%**.
     - Adjusted Mutation Score: **75.21%** (with provably equivalent rounding mutants excluded).

---

### Minute 09:00–12:00: Blackboard, Checkpoints & Cryptographic Provenance
1. **Inspect Multi-Agent Wiretap:** Switch to **🤖 Multi-Agent Wiretap** tab.
   - *What to Point Out:* The chronological sequence of inter-agent messages between Google ADK Generator and CrewAI Critic.
2. **Inspect Checkpoint Timeline:** Switch to **💾 Checkpoint Timeline & Diff** tab.
   - *What to Point Out:* Point out the 1,100+ historical checkpoints saved in `qa_artifacts/testforge_checkpoints.db`.
   - *Action:* Select two checkpoints (Base A and Target B) and click **"Semantic Diff"** to show evaluators that Blackboard state transitions are completely auditable.
3. **Inspect Hardened Test Suite:** In the Hardening tab, scroll down to **"Hardened Pytest Suite"**.
   - *What to Point Out:* Click **"📋 Copy Suite"** or point to exact assertions:
     - Boundary tests (`quantity=4`, `quantity=5`, `quantity=6`).
     - Exception tests (`with pytest.raises(ValueError):`).
     - Floating-point tolerances (`pytest.approx`).

---

## 3. What to Say When Explaining Key Concepts

### On Surviving Mutants and Equivalence:
> *"Notice that 2 mutants survived in `discount.py`. Let's look at `MUT_BOUNDARY_SWAP_003` at line 9. The original code has `if price <= 0.0: return 0.0`. The mutant changed it to `if price < 0.0: return 0.0`. If price is exactly 0.0, the mutant falls through to the calculation: `0.0 * (1.0 - 0.0) = 0.0`. It returns 0.0 either way. This is a mathematically equivalent mutant. TestForge properly classifies this rather than artificially inflating scores."*

### On Cryptographic Provenance:
> *"Every test suite generated by TestForge is SHA-256 hashed at synthesis time. That exact hash is verified when the suite is validated, when it is stored on the Blackboard, when it is exported, and when it runs against mutants. The hashes match byte-for-byte, proving that no human intervened and no tests were silently modified."*

---

## 4. Live Error Handling & Troubleshooting Playbook

| Scenario | Immediate Symptom | Remediation Action |
| :--- | :--- | :--- |
| **Backend Port 8000 Not Responding** | Browser shows "Connection refused" | Run in shell: `.venv-release/bin/python -m uvicorn server:app --host 127.0.0.1 --port 8000 &` |
| **Job Stays in `RUNNING` Too Long** | Progress bar stalls during sandbox | Click the **"🛑 Cancel Hardening"** button; cooperative cancellation will terminate the worker pool and return state to `CANCELLED`. |
| **API Key Missing for LLM** | Notification: "API Key not configured" | Explain that TestForge operates in **100% autonomous offline mode** using AST boundary synthesis (`IntelligentASTSynthesizer`) without requiring external cloud API calls. |
| **Browser Modal Fails to Close** | Backdrop overlay persists | Press `Escape` or click the `×` button in the upper-right corner of the modal dialog. |

