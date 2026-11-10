# TestForge: 10-Minute Live Demo Script & Examiner Walkthrough

> **Total Duration**: 10 Minutes  
> **Presenters**: Sourabh & Shreshth  
> **Course**: Autonomous Agentic AI (Phase-3 Submission)  
> **Live Cockpit**: `http://127.0.0.1:8000`  
> **Fallback Plan**: Zero-Egress Air-Gapped Local Ollama / Deterministic Offline Mode  

---

## Pre-Flight Checklist (T - 2 Minutes)
- [ ] Virtual environment activated: `source .venv-release/bin/activate`
- [ ] Server running: `python -m uvicorn server:app --host 127.0.0.1 --port 8000`
- [ ] Browser open to `http://127.0.0.1:8000`
- [ ] Ollama service active: `curl -s http://localhost:11434/api/tags` (optional, for local mode)

---

## Phase 1: Problem Statement & The Coverage-Kill Gap (Minutes 0:00 – 2:00)

### Visual / Action
1. Open dashboard to **Mode A: Workspace & Upload** tab.
2. Select `discount.py` from the sample dropdown.
3. Show the target module code in the viewer:
   - "Notice this tiered discount function has boundary logic (`quantity > 5`, `is_member == True`)."
4. Navigate to **Hardening Lab & Results** tab.
5. Click **"Run Hardening Pipeline"**.

### Presenter Script
> *"Good morning, examiners. In continuous integration, developers measure line coverage and assume 100% coverage means high-quality testing. But line coverage only measures code execution, not assertion depth. A test that calls a function with zero assertions achieves 100% line coverage but catches zero bugs.*  
> *TestForge solves this by transforming unit testing into an adversarial multi-agent game. Watch our live dashboard as the pipeline ingests `discount.py`, checks baseline tests, and injects 19 deterministic AST faults into the code."*

---

## Phase 2: Live Multi-Agent Execution & Wiretap (Minutes 2:00 – 4:00)

### Visual / Action
1. Click **Multi-Agent Wiretap** tab while job is running.
2. Show the **Canonical Eight-Agent Architecture Topology Grid**:
   - `SupervisorAgent` (Google ADK)
   - `TestPlanningAgent` (Google ADK)
   - `TestGeneratorAgent` (Google ADK)
   - `MutationQualityCriticAgent` (CrewAI via A2A wire protocol)
   - `ReflectionRepairAgent` (Google ADK)
3. Show the real-time timeline stream appending handoff events.

### Presenter Script
> *"Here on the Multi-Agent Wiretap, you are observing our dual-framework architecture in real time. Google ADK orchestrates the workflow lifecycle and enforces path containment. When mutants survive, the surviving AST diffs are dispatched over the official Agent2Agent (A2A v0.3.0) wire protocol to our CrewAI MutationQualityCritic agent running in a separate worker process.*  
> *The Critic analyzes the surviving diffs and formulates prescriptive directives for the ReflectionRepair agent."*

---

## Phase 3: Convergence & Checkpoint Timeline (Minutes 4:00 – 6:00)

### Visual / Action
1. Switch back to **Hardening Lab & Results**.
2. Point out the finalized metrics:
   - Line Coverage: 100.0%
   - Branch Coverage: 100.0%
   - Raw Mutation Score: 94.7% (18/19 killed)
   - Adjusted Mutation Score: **100.0%** (1 verified equivalent mutant excluded).
3. Switch to **Checkpoint Timeline & Diff** tab.
4. Click on Checkpoint 1 (Base) and Checkpoint 3 (Target), then click **"Deterministic Diff"**.

### Presenter Script
> *"Notice the score convergence: our system killed 18 of 19 mutants. The 19th mutant was mathematically proven equivalent using our recursive bytecode instruction normalizer, giving a true adjusted score of 100%.*  
> *Every single state transition is durably committed to an append-only SQLite database in WAL mode. Here on the Checkpoint Inspector, we can inspect semantic diffs across reflection iterations, demonstrating deterministic convergence without memory leaks."*

---

## Phase 4: Beyond the Handout Innovation Showcase (Minutes 6:00 – 8:00)

### Visual / Action
1. In the **Hardening Lab** tab, scroll down to the **Test Suite Minimizer** panel.
2. Click **"Load Benchmark Summary"** or **"Minimize Suite"**.
   - Show: 134 tests reduced to 28 tests (**79.1% reduction**) with **100% score retention**.
   - Show the 2D Kill Matrix heatmap sample.
3. Show the **Zero-Egress Privacy Mode** toggle in the navbar.
   - Click the privacy button: the badge switches to `🔒 Privacy Mode: ON`.
   - Show that external sockets are blocked and traffic routes to local Ollama.

### Presenter Script
> *"Beyond the coursework specification, we implemented three key optimizations:*  
> *First, our Test Suite Minimizer solves greedy set cover on the 2D Kill Matrix. It reduced 134 test cases across 4 targets down to 28 tests—a 79.1% reduction—while mathematically retaining 100% of mutation kills.*  
> *Second, our Zero-Egress Privacy Mode enforces air-gapped execution by intercepting low-level OS sockets, preventing cloud data exfiltration, and rerouting generation to local Ollama while scrubbing PII.*  
> *Third, our Human Approval Gate ensures no LLM-generated code touches the repository or PRs without operator sign-off."*

---

## Phase 5: Empirical Benchmarks & Examiner Q&A (Minutes 8:00 – 10:00)

### Visual / Action
1. Open the **Benchmarks & Ablation** tab.
2. Show the **Empirical Multi-Target Evaluation Suite (GAP-009)** table:
   - Point to `discount.py` (100% adj MS), `order_fsm.py` (100% adj MS), `lru_cache.py`, and `stats_calculator.py`.
   - Show the Arithmetic and Geometric mean rows in `tfoot`.
3. Open floor to examiner questions.

### Presenter Script
> *"In summary, across 4 diverse benchmark targets and 870+ automated regression tests, TestForge lifts mutation kill scores from 6.46% baseline to 67.02% raw and 70.17% adjusted, while cutting test suite bloat by 79%.*  
> *We are ready to take your questions."*

---

## Graceful Fallback & Contingency Plan

If an unexpected environmental issue arises during examination:
1. **Cloud API Outage / 429 Quota**:
   - Flip to local mode in Settings Modal (`Engine Mode: Local (Ollama)`).
   - Or run with `--privacy-mode` CLI flag:
     `python -m testforge.cli harden samples/discount.py --privacy-mode --engine-mode local`
2. **Deterministic Heuristic Offline Mode**:
   - If Ollama is not running, TestForge automatically shifts down to Tier 4 (Deterministic AST Synthesizer), guaranteeing 0 crashes and complete execution proof.
3. **Pre-computed Multi-Target Cache**:
   - If offline, the Benchmarks tab instantly loads pre-computed single-source-of-truth benchmarks from `qa_artifacts/MULTI_TARGET_BENCHMARK_RESULTS.json`.

