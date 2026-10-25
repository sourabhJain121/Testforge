# TestForge — Phase 2 Evaluator Walkthrough & Demo Runbook

**Target Evaluator Audience:** Academic viva examiners, enterprise architecture evaluators, and technical reviewers.  
**Platform / Pre-requisites:**
- macOS Apple Silicon / Linux (Python 3.13)
- Chrome / Chromium browser
- Local server running at `http://127.0.0.1:8000/`

---

## 1. Quick Launch & Health Verification

1. **Verify Backend Status:**
   ```bash
   curl -s http://127.0.0.1:8000/healthz | jq
   curl -s http://127.0.0.1:8000/readyz | jq
   ```
   *Expected Output:* Status `healthy` and `ready` across all subsystems (`ast_mutator`, `blackboard`, `sandbox_storage`, `sqlite_persistence`).

2. **Open Application in Google Chrome:**
   Navigate to `http://127.0.0.1:8000/`.
   - Observe the cyber-dark HUD header displaying the `TestForge` brand, hardware detection pill (`Apple Silicon (arm64)`), and status indicators.

---

## 2. Walkthrough Flow 1: MCP & A2A Interoperability Discovery

1. **Model Context Protocol (FastMCP) Tools:**
   - Click the **🔌 MCP Tools (4)** pill in the top navbar.
   - A modal opens displaying:
     - Protocol: Model Context Protocol (FastMCP / mcp-python v1.28.0)
     - Server 1: `testforge-filesystem` (3 tools: `read_text_file`, `list_directory`, `get_file_info`)
     - Server 2: `testforge-github` (1 tool: `get_repository_info`)
   - Click **📋 Copy JSON** — button updates to **✅ Copied!**.
   - Click **🌐 View Raw JSON** to see the machine-readable payload at `/api/mcp/status`.
   - Press **Escape** or click **Close** to dismiss.

2. **A2A Agent Card Discovery:**
   - Click the **🤖 A2A Card** button in the navbar.
   - Inspect the declared agent metadata:
     - Name: `testforge-agent-system`
     - Protocol: `A2A v0.3.0`
     - Capabilities: AST Mutator, Google ADK Synthesizer, CrewAI Critic, Parallel Sandbox.
   - Press **Escape** to dismiss.

---

## 3. Walkthrough Flow 2: Mode A — AST Parsing & Mutation Analysis

1. **Select Sample Target:**
   - Ensure the **Mode A (AST)** tab is selected.
   - From the dropdown `#sample-file-select`, choose `discount.py` (or `banking.py`).
   - Click **📂 Load Sample**.
   - Observe:
     - Hero card updates with module name, SHA-256 fingerprint, AST function count, and line count.
     - Code viewer renders the Python source with syntax highlighting.
     - AST callables list displays `calculate_discount`.

2. **Inspect Blast Radius:**
   - Click the **🎯 Blast Radius** tab.
   - Select `calculate_discount` from the dropdown.
   - Observe the static call tree rendering, risk category badge (`🟢 LOW`), and call graph canvas.

---

## 4. Walkthrough Flow 3: Autonomous Hardening Lab Execution

1. **Trigger Hardening:**
   - Navigate to the **🧪 Hardening Lab** tab.
   - Verify the target parameters:
     - Target: `samples.discount`
     - Model: `Auto (Ollama qwen2.5-coder -> Gemini fallback)`
     - Max Iterations: `3`
     - Target Mutation Score: `85%`
   - Click **⚡ Run Hardening**.

2. **Observe Real-Time Execution:**
   - The progress banner displays active reflection cycles.
   - Baseline integrity tests execute in isolated sandboxes.
   - Fault injection produces deterministic AST mutants.
   - Sandboxed test execution classifies mutants as `KILLED` or `SURVIVED`.
   - Surviving mutants trigger the Critic reflection agent to generate tighter boundary assertions.

3. **Inspect Convergence & AST Diffs:**
   - Once completed, inspect KPI counters:
     - Baseline Passed: `1`
     - Line Coverage: `100.0%`
     - Mutants Generated: `19`
     - Mutants Killed: `12`
   - Click the **Killed** filter button to filter the mutant table.
   - Click any mutant row (e.g., `MUT_COND_INV_001`) to inspect the unified AST diff viewer showing exact mutated lines.

4. **Export Hardened Suite:**
   - Scroll to the bottom of the Hardening Lab.
   - Click **📋 Copy Suite** to export the standalone pytest file.

---

## 5. Walkthrough Flow 4: Wiretap WebSocket Streaming & Polling Fallback

1. **Live Event Stream:**
   - Click the **⚡ Wiretap** tab.
   - Notice the status badge reads `⚡ Live Streaming` connected to `ws://127.0.0.1:8000/ws/events`.
   - Scroll through the chronological handoff timeline showing Critic and Generator messages.

2. **Simulate Network Degradation (Fallback):**
   - Open Chrome DevTools Console (`Cmd+Option+I`).
   - Run `window.__testforge.disconnectWebSocket()`.
   - Notice the badge immediately degrades to `🔄 Polling Fallback` and continues polling `/api/wiretap` every 2.5s without data loss.
   - Run `window.__testforge.initWebSocketEventStream()` to restore live WebSocket streaming.

---

## 6. Walkthrough Flow 5: Checkpoints, SQLite Rollback & Semantic Diff

1. **Inspect Historical Checkpoints:**
   - Click the **💾 Checkpoints** tab.
   - The timeline displays SQLite persistent snapshot cards with SHA hashes, revision numbers, and timestamps.
   - Click **Inspect** on any card to view the structured snapshot or formatted JSON.

2. **Compute Semantic Checkpoint Diff:**
   - On the first card, click **Set as Base (A)**.
   - On the second card, click **Set as Target (B)**.
   - Click **🔍 Compare Checkpoints**.
   - Inspect the unified semantic diff showing changes across code revisions and mutation scores.

3. **Safe Rollback Confirmation:**
   - Click **Restore** on any checkpoint card.
   - Notice the high-visibility safety confirmation dialog prompting the user to confirm or cancel.
   - Click **Cancel** to safely dismiss without modifying project state.
