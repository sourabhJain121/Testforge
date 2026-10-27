# TESTFORGE — PRIORITIZED IMPLEMENTATION PLAN FOR TEACHER REVIEW

**Repository:** `/Users/sourabh/TestForge`  
**Audit Directory:** `qa_artifacts/teacher_review_readiness_20261027_103800/`  
**Timestamp:** `2026-10-27T10:44:00+05:30`  
**Auditor Role:** Senior Software Architect & QA Lead  

---

## Priority Framework
- **P0:** Correctness, security, or materially misleading results.
- **P1:** Necessary for demonstrating a mandatory requirement with maximum clarity.
- **P2:** Significant usability, reliability, or demo-flow improvement.
- **P3:** Optional visual polish.

---

## 1. Ranked List of Proposed Targeted Improvements

### Item 1: Real-Time Lifecycle FSM Progress Display (Priority: P0 / P1)
- **1. Specific Problem:** In `frontend/app.js:1772-1786`, during a hardening job, the progress bar uses a simulated increment timer (`progressSim = Math.min(progressSim + 12, 90)` every 1.2s). The backend already returns real FSM lifecycle states (`job.lifecycle_state`) and stage durations, but the frontend ignores them while polling.
- **2. Evidence & Affected Files:**
  - `frontend/app.js` (lines 1772-1786)
  - `server.py` (lines 873-877: `job["lifecycle_state"] = orch.fsm.current_state.value`)
- **3. Why it Matters for Teacher Review:** A teacher may ask: "Does that percentage bar reflect the actual agent execution state or is it just a timer?" Answering that it is a timer undermines the agentic demonstration. Connecting it to the real FSM proves genuine multi-agent orchestration.
- **4. Smallest Proposed Solution:**
  - In `app.js:pollHardeningJob`, read `job.lifecycle_state`.
  - Calculate progress based on real FSM stages:
    - `SUBMITTED` / `PLANNING` -> 15% ("Ingesting target & planning reflection strategy...")
    - `GENERATING_TESTS` -> 35% ("Google ADK: Synthesizing candidate test assertions...")
    - `VALIDATING_CLEAN_CODE` -> 50% ("Clean Code Validator: Verifying Pass@1 soundness on unmutated code...")
    - `MUTATION_ANALYSIS` / `EXECUTING` -> 70% ("AST Mutator: Inverting operators & executing parallel worker sandboxes...")
    - `EVALUATING` / `CHECKPOINTING` -> 85% ("CrewAI Critic: Diagnosing surviving mutants & checkpointing Blackboard...")
    - `COMPLETED` -> 100% ("Hardening finished.")
- **5. Estimated Implementation Effort:** ~25 lines of JavaScript in `app.js`. (No backend changes required).
- **6. Regression Risks:** Minimal; purely frontend display logic within existing poll interval.
- **7. Tests & Verification:** Run a visible browser run on `discount.py` and verify status text updates smoothly through all FSM states.
- **8. Classification:** **Essential for Review Honesty.**

---

### Item 2: Live Blackboard Mini-Drawer in Hardening Lab (Priority: P1)
- **1. Specific Problem:** The 5 Blackboard spaces (`TargetSpace`, `SuiteSpace`, `MutantSpace`, `CriticSpace`, `MetricsSpace`) are currently rendered in the `💾 Checkpoint Timeline & Diff` tab. While running in `🔥 Hardening Lab`, the student only sees the progress bar and final results.
- **2. Evidence & Affected Files:**
  - `frontend/index.html` (lines 580-610)
  - `frontend/app.js` (`pollHardeningJob`, `renderHardeningResults`)
- **3. Why it Matters for Teacher Review:** MUST 1 requires demonstrating shared context and state between agents. In a live presentation, switching tabs interrupts the narrative. Showing a compact 5-space strip in the primary demo tab makes the Blackboard immediately obvious.
- **4. Smallest Proposed Solution:**
  - In `frontend/index.html` under `#hardening-progress-box`, add a compact 5-card status bar:
    ```html
    <div id="live-blackboard-strip" class="blackboard-mini-strip">
      <div class="bb-pill" id="bb-pill-target">📁 TargetSpace</div>
      <div class="bb-pill" id="bb-pill-suite">🧪 SuiteSpace</div>
      <div class="bb-pill" id="bb-pill-mutant">🧬 MutantSpace</div>
      <div class="bb-pill" id="bb-pill-critic">🧐 CriticSpace</div>
      <div class="bb-pill" id="bb-pill-metrics">📊 MetricsSpace</div>
    </div>
    ```
  - As FSM stages transition, add an `.active-pulse` class to the corresponding pill.
  - On completion, clicking any pill switches active tab to `#tab-checkpoints` focused on that space.
- **5. Estimated Implementation Effort:** ~30 lines of CSS, ~15 lines of HTML, ~20 lines in `app.js`.
- **6. Regression Risks:** Zero backend risk; strictly additive presentation in frontend.
- **7. Tests & Verification:** Headed Chrome inspection confirming pills illuminate as stages progress.
- **8. Classification:** **Highly Recommended for MUST 1 Demonstration.**

---

### Item 3: 1-Click Interactive A2A Test Ping in A2A Modal (Priority: P2)
- **1. Specific Problem:** The `🤖 A2A Agent Card` modal displays discoverable AgentCard metadata, but demonstrating live task execution requires curl or terminal commands.
- **2. Evidence & Affected Files:**
  - `frontend/index.html` (lines 140-165)
  - `frontend/app.js` (`renderA2ACard`)
  - `server.py` (`POST /a2a/tasks`)
- **3. Why it Matters for Teacher Review:** Proves that the A2A endpoint is a functioning JSON-RPC wire protocol, not just a static `.json` file.
- **4. Smallest Proposed Solution:**
  - Add a button `⚡ Send Test A2A Ping` inside `#a2a-modal`.
  - On click, issues `POST /a2a/tasks` with `{"jsonrpc": "2.0", "method": "ping", "id": 1}` and renders the response inline.
- **5. Estimated Implementation Effort:** ~15 lines in `app.js`.
- **6. Regression Risks:** Zero; invokes existing read-only endpoint.
- **7. Tests & Verification:** Pytest `test_a2a_protocol.py` + browser modal click.
- **8. Classification:** **Recommended for MUST 6 Live Demo.**

---

### Item 4: 1-Click FastMCP Tool Query in MCP Modal (Priority: P2)
- **1. Specific Problem:** The `🔌 MCP Tools` modal lists FastMCP servers and tool schemas, but running a tool requires autonomous agent invocation.
- **2. Evidence & Affected Files:**
  - `frontend/index.html` (lines 180-205)
  - `frontend/app.js` (`renderMcpStatus`)
  - `server.py` (`GET /api/mcp/status`)
- **3. Why it Matters for Teacher Review:** Gives immediate tangible proof that the FastMCP stdio transport is alive and executing real tools.
- **4. Smallest Proposed Solution:**
  - Add a `▶️ Test Tool Execution` button next to `read_text_file` or `list_directory` in `#mcp-modal`.
  - On click, invokes the tool on `samples/` and renders the real FastMCP JSON-RPC response.
- **5. Estimated Implementation Effort:** ~20 lines in `app.js`.
- **6. Regression Risks:** Zero.
- **7. Tests & Verification:** Pytest `test_mcp.py` + browser click.
- **8. Classification:** **Recommended for MUST 2 Live Demo.**

---

## 2. Summary Table of Proposed Improvements

| Priority | Proposed Improvement | Affected Files | Estimated Lines | Risk Level | Necessity for Review |
| :---: | :--- | :--- | :---: | :---: | :---: |
| **P0 / P1** | Real-Time FSM Lifecycle Progress | `frontend/app.js` | ~25 lines | Low | **Essential (Eliminates simulated timer)** |
| **P1** | Live Blackboard Partition Strip | `frontend/index.html`, `app.js` | ~65 lines | Low | **Essential (Makes MUST 1 obvious in primary tab)** |
| **P2** | In-Browser A2A Test Ping | `frontend/index.html`, `app.js` | ~20 lines | None | Optional Polish (Avoids terminal for MUST 6) |
| **P2** | In-Browser FastMCP Tool Test | `frontend/index.html`, `app.js` | ~25 lines | None | Optional Polish (Avoids terminal for MUST 2) |

---

## 3. Strict Safety Statement

Per the user's instructions:
**None of these changes have been implemented.**
All existing code, tests, and configuration remain 100% untouched. Implementation will only begin after the user explicitly reviews and approves this plan.
