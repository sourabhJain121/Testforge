# TestForge: Technical Defense Presentation (12-Slide Master Deck)

**Presentation Title:** Autonomous Test Hardening via Multi-Agent Reflection & Mutation Verification  
**Authors & Presenters:** Sourabh & Shreshth  
**Coursework:** Autonomous Agentic AI Systems (Phase-3 Capstone Evaluation)  
**Target Duration:** 15 Minutes (10-minute presentation + 5-minute Q&A)  
**System Status:** Release v1.0.0 (Passing 999+ Unit, Contract, and Integration Tests)

---

## Slide 1: Title & System Overview
- **Header:** TestForge: Autonomous Multi-Agent Unit Test Hardening
- **Subtitle:** Closing the LLM Coverage-Kill Gap via Mutation-Guided Reflection
- **Presenters:** Sourabh & Shreshth
- **Core Mission:** Transform unassertive, hallucinated LLM test suites into mathematically verified, high-kill test suites using AST mutation testing, sandboxed execution, and multi-agent reflection.
- **Architectural Highlights:**
  - 8-Agent Topology (Google ADK v1.14.1 + CrewAI v0.102.0).
  - FastMCP 4-Tool Protocol Suite over isolated stdio JSON-RPC.
  - Zero-egress local Agentic RAG vector store for invariant boundary patterns.
  - Immutable SQLite Blackboard state ledgers with atomic rollback.
- **Speaker Notes:**
  > *"Good morning, examiners. Today we present TestForge, a multi-agent platform designed to address a critical vulnerability in modern automated software engineering: the fact that LLMs generate tests that appear thorough but fail to catch real bugs. We will demonstrate how mutation verification and closed-loop multi-agent reflection bridge this gap."*

---

## Slide 2: The Core Problem: Why LLM-Generated Tests Are Weak
- **Header:** The "Coverage-Kill Gap" & Silent Test Tautologies
- **Key Visual:** Comparison between Line Coverage vs. Mutation Kill Score.
- **Problem Breakdown:**
  - **Hollow Execution:** Tests execute code lines without checking return values or state invariants (`calculate_discount(100, 5, True)` achieves 100% line coverage but 0% fault detection).
  - **The Silent Failure Trap:** Broken code passes tests; broken tests pass clean code.
  - **Empirical Baseline Evidence:**
    - Developer Starter Baselines: 30.75% Line Coverage $\rightarrow$ Only **6.46%** Raw Mutation Score.
    - Zero-Shot Foundation Models: 39.17% Line Coverage $\rightarrow$ Only **32.58%** Raw Mutation Score.
- **The Core Dilemma:** How can autonomous systems verify that a test suite is truly protecting against regressions without relying on human oracle authoring?
- **Speaker Notes:**
  > *"Our fundamental premise is that line coverage is a vanity metric. A test that touches every line without an assertion provides zero protection. In our empirical baselines across four diverse targets, starter tests had 30.75% line coverage but caught only 6.46% of injected faults. Zero-shot LLMs barely reached 32.58%. We needed an adversarial ground-truth."*

---

## Slide 3: The TestForge Solution: Mutation-Verified Autonomous Hardening
- **Header:** The Closed-Loop Mutation Reflection Engine
- **Core Principle:** Inject systematic synthetic bugs into Abstract Syntax Trees (ASTs). If tests pass on mutated code, the mutant *survives*; the test suite is inadequate.
- **The Closed Loop:**
  1. **Mutate:** Inject bounded semantic faults into the target AST.
  2. **Execute:** Run test suite against clean code (preflight) and mutants in isolated sandboxes.
  3. **Diagnose:** Analyze surviving mutants using an adversarial Critic Agent.
  4. **Synthesize:** Generate targeted counterexample assertions addressing the specific surviving diff.
  5. **Guard:** Commit only suites that strictly improve mutation score without breaking on clean code.
- **Speaker Notes:**
  > *"TestForge replaces open-loop generation with closed-loop mutation-guided reflection. By injecting concrete AST faults, our agents have an objective loss function: kill the surviving mutant. When a mutant survives, the critic agent diagnoses the exact surviving diff and guides the repair agent to synthesize assertions that target the specific boundary flaw."*

---

## Slide 4: 8-Agent Blackboard Architecture & Collaboration Flow
- **Header:** Heterogeneous Multi-Agent Topology & A2A Collaboration
- **Visual Diagram:** 8 Agents interacting via Blackboard and A2A Protocol.
  - **Supervisor Agent (Google ADK):** Master state machine FSM and convergence evaluator.
  - **Code Intelligence Agent:** Static AST symbol, branch, and complexity analyzer.
  - **Security Agent:** Zero-egress AST guardrail blocking dangerous system modules.
  - **Test Planning Agent:** Formulates scenario budgets, boundaries, and RAG heuristics.
  - **Test Generator Agent (Google ADK):** Generates candidate Pytest suites.
  - **Test Execution Agent:** Dispatches tests across isolated parallel subprocesses.
  - **Mutation Quality Critic (CrewAI):** Adversarial specialist diagnosing surviving mutants.
  - **Reflection & Repair Agent (Google ADK):** Synthesizes repairs with Never-Regress Guard.
- **Shared Memory:** Central Blackboard with SQLite Write-Ahead Logging (WAL) state persistence.
- **Speaker Notes:**
  > *"Rather than a monolithic prompt, TestForge delegates concerns across eight specialized agents. Google ADK provides stateful FSM coordination, while CrewAI provides adversarial role-playing for the critic. Communication occurs via the Agent-to-Agent wire protocol and a thread-safe, 8-partition Blackboard with SQLite WAL checkpointing."*

---

## Slide 5: FastMCP 4-Tool Protocol Suite
- **Header:** Standardizing Agent Tooling via Model Context Protocol (FastMCP)
- **Protocol Spec:** Subprocess stdio JSON-RPC transport (`python -m testforge.mcp_server`).
- **The 4 Official Tools:**
  1. `mcp_ast_symbol_analyzer`: Extracts AST functions, branches, complexity, and dependencies.
  2. `mcp_mutant_generator`: Deterministically generates bounded AST mutants with line tracking.
  3. `mcp_sandbox_runner`: Executes suites under memory limits and 3.0s timeout ceiling.
  4. `mcp_equivalence_classifier`: Classifies semantic equivalent mutants using dual-tier checks.
- **Resilience:** Automatic fallback to direct in-process execution with explicit telemetry event logging (`MCP_STDIO_FALLBACK_TRIGGERED`).
- **Interactive UI:** Web dashboard features an in-cockpit **FastMCP Tool Studio** for live tool execution and schema inspection.
- **Speaker Notes:**
  > *"To ensure modularity and external agent compatibility, our tools are exposed as an official FastMCP server running over isolated stdio JSON-RPC. Whether called by our internal agents or an external MCP client like Claude Desktop, the exact same 4-tool protocol suite powers analysis, mutation, sandboxed execution, and equivalence detection."*

---

## Slide 6: Defect DEF-022 Discovery & Empirical Honesty
- **Header:** DEF-022: The Clean Reference False-Kill Defect
- **Discovery:** In legacy mutation testing harnesses, test suites throwing compilation or type errors caused pytest to return non-zero exit codes. The harness erroneously scored these execution crashes as mutant kills!
- **Impact:** Suites that failed on *clean unmutated code* were falsely reported as achieving 90%+ mutation score.
- **The DEF-022 Architectural Cure:**
  - **Pass@1 Preflight Filter:** Candidate suites must pass against pristine clean code before mutant execution.
  - **Granular Pruning:** `GranularTestValidator` tests candidate functions individually, pruning broken tests and retaining only 100% clean-passing assertions.
  - **Invalid Suite Classification:** If no tests pass clean code, the suite is scored as `INVALID_SUITE` (0 kills, 0.0% MS).
- **Formal Retraction:** Legacy claims (CLM-028, CLM-032) claiming 90%+ local LLM scores were formally retracted in `docs/CLAIMS_REGISTER.md`.
- **Speaker Notes:**
  > *"A cornerstone of our engineering rigor was the discovery and correction of Defect DEF-022. We discovered that broken tests were causing non-zero exit codes that legacy scripts counted as mutant kills. We implemented strict Pass@1 preflight validation and granular pruning, and we formally retracted all unverified legacy numbers. What we present today are 100% empirically verified figures."*

---

## Slide 7: AST Mutation Engine & Bytecode Semantic Equivalence
- **Header:** Generating Faults & Solving the Equivalent Mutant Problem
- **AST Mutation Engine:**
  - 10 operators across 7 categories (Boundary Swaps, Comparators, Condition Inversion, Constant Shifts, Logical Connectives, Math Operators, Return Predicates).
  - Validated against gold-standard `mutmut v3.8.1`: achieves **$r = 0.9988$** ordinal correlation.
- **The Equivalent Mutant Challenge:**
  - Rice's Theorem: Program semantic equivalence is undecidable in the general case.
  - Equivalent mutants mutate syntax without altering behavior (e.g. dead code), creating artificial score ceilings.
- **Dual-Tier Detection:**
  - **Tier 1 (Compiler-Level Bytecode Normalization):** Compares Python bytecode instruction streams via `dis`. Proves equivalence with **0.0% false positive rate (100% precision)**.
  - **Tier 2 (Semantic AST Classification):** Eliminates equivalent mutants to calculate true Adjusted Mutation Score.
- **Speaker Notes:**
  > *"Our mutation engine injects 10 categories of AST faults. To address the equivalent mutant problem, we introduced a compiler-level bytecode normalization engine. By comparing normalized bytecode instruction streams, we mathematically prove compiler equivalence with zero false positives, eliminating artificial ceilings on complex stateful targets like order_fsm."*

---

## Slide 8: Benchmark Results: 4 Canonical Targets
- **Header:** Quantitative Evaluation: Baseline vs. Zero-Shot vs. TestForge
- **Empirical Table (Post-Rescore Audited Figures):**

| Benchmark Target | Complexity Domain | Baseline MS | Zero-Shot MS | TestForge Raw MS | TestForge Adj MS | Killed Mutants |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| `discount.py` | Arithmetic & Boundaries | 5.26% | 63.16% | **94.74%** | **100.0%** | 18 / 19 |
| `order_fsm.py` | Stateful E-Commerce FSM | 6.60% | 13.21% | **97.17%** | **100.0%** | 103 / 106 |
| `lru_cache.py` | Doubly-Linked Nodes | 7.14% | 23.81% | **30.95%** | **34.21%** | 13 / 42 |
| `stats_calculator.py`| Numerical & Float Stats | 6.85% | 30.14% | **45.21%** | **46.48%** | 33 / 73 |
| **Macro Average** | **Diverse Algorithmic Set** | **6.46%** | **32.58%** | **67.02%** | **70.17%** | **167 / 240** |

- **Key Takeaway:** TestForge achieves a **10.37x lift over developer baselines** and **doubles the fault detection rate of zero-shot LLMs**, proving the power of closed-loop reflection.
- **Speaker Notes:**
  > *"Across the four canonical benchmarks, developer starter tests killed only 6.46% of mutants. Zero-shot LLM prompts reached 32.58%. TestForge closed the gap, achieving 67.02% raw mutation score and 70.17% adjusted mutation score, killing 167 out of 240 injected mutants across all targets."*

---

## Slide 9: Extension: Hybrid Synthesizer & Agentic RAG
- **Header:** Scaling to Complex Production & Sealed Algorithms
- **Hybrid Synthesizer:** Pairs fast deterministic AST invariant seeds with mutation-guided reflection and the **Never-Regress Guard**.
- **Live Agentic RAG Vector Store:**
  - Zero-egress local vector store seeded with 4 specialized testing pattern corpora (division, slicing, regex, stateful cache).
  - Automatically retrieves boundary heuristics matching target AST constructs (e.g. injecting `sys.maxsize`, `math.isclose`, and `ZeroDivisionError` recipes).
- **Production & Sealed Target Performance:**
  - `jwt_validator.py` (Auth tokens): 48.98% baseline $\rightarrow$ **54.42%** (+5.44% lift).
  - `rate_limiter.py` (Concurrency): 21.77% baseline $\rightarrow$ **59.18%** (+37.41% lift).
  - `bisect_algo.py` (Adapted CPython Stdlib): 0.0% baseline $\rightarrow$ **65.71%** (46/70 killed).
  - `lru_cache.py` (Extended Sequence): 7.14% baseline $\rightarrow$ **54.76%** (23/42 killed).
- **Speaker Notes:**
  > *"To generalize beyond simple benchmarks, we introduced the Hybrid Synthesizer and local Agentic RAG. By retrieving deterministic boundary recipes from our local vector store and inferring sequence parameters, we lifted real-world production targets like JWT Validator and Token-Bucket Rate Limiter by up to 37.41%, and achieved 65.71% on CPython's bisect."*

---

## Slide 10: Negative Results & Architectural Limitations
- **Header:** Engineering Honesty: Failure Modes & Boundary Limits
- **Documented Limitations:**
  1. **Untyped Dynamic Sequence Indexing:**
     - Pure static analysis cannot guess whether `s[0]` expects integers, strings, or custom dataclasses without type annotations.
     - Early iterations generated invalid sequence calls, requiring AST sequence inference to resolve.
  2. **Complex Stateful Object Inter-Call Dependencies:**
     - Killing subtle cache eviction or node-relinking mutants requires synthesizing exact multi-step call sequences (`put -> put -> get -> put`).
     - While single-method assertions reach 54.76%, killing 100% of LRU mutants requires deep state-machine sequence synthesis.
  3. **Computational & Token Overhead:**
     - Parallel sandboxing consumes CPU workers during combinatorial mutation runs.
     - Mitigated via Diff-Incremental testing and sub-second subprocess pools.
- **Speaker Notes:**
  > *"Academic rigor requires transparently presenting limitations. TestForge struggles with untyped dynamic sequences where type annotations are absent, and single-method assertions cannot easily kill deep stateful call-chain mutants like pointer swaps in an LRU doubly linked list. Identifying these boundaries guided our sequence inference enhancements."*

---

## Slide 11: Production Cockpit & Developer Experience
- **Header:** Full-Stack Cockpit: FastAPI, Vanilla ES6 & Observability
- **Architecture:** Zero NPM dependencies, pure Vanilla ES6 JavaScript, HTML5, CSS3 variables.
- **Key Cockpit Capabilities:**
  - **7 Canonical Views:** Target Ingestion, Multi-Agent Wiretap, Mutant Diff Inspector, Benchmark Suite, Telemetry, Checkpoints, FastMCP Studio.
  - **Visual AST Mutant Diff Inspector:** Side-by-side syntax-highlighted code viewer rendering original source vs. mutated AST diff.
  - **Real-Time Agent Wiretap:** WebSocket stream showing agent handoffs, reasoning traces, and critic directives.
  - **State Rollback & Replay:** Single-click rollback across SQLite WAL checkpoints.
  - **FastMCP Tool Studio:** Live execution, input modification, and schema inspection for all 4 MCP tools.
- **Speaker Notes:**
  > *"To ensure seamless developer adoption, we engineered a production cockpit using FastAPI and Vanilla ES6 with zero external frontend dependencies. Developers can observe agent handoffs in real-time, inspect AST mutant diffs side-by-side, test MCP tools interactively, and roll back state across SQLite checkpoints."*

---

## Slide 12: Conclusion & Contribution Summary
- **Header:** Summary of Core Contributions
- **Summary of Achievements:**
  1. **Solved the LLM Coverage-Kill Gap:** Proved that mutation-guided reflection lifts test effectiveness from 6.46% to 70.17% adjusted MS.
  2. **FastMCP Stdio Tool Architecture:** Deployed an isolated 4-tool protocol suite over stdio JSON-RPC.
  3. **Empirical Integrity (DEF-022):** Enforced Pass@1 clean preflight validation and maintained public retraction register.
  4. **Multi-Agent Interoperability:** Harmonized Google ADK and CrewAI over the official A2A protocol and SQLite Blackboard.
- **Division of Labor:**
  - **Sourabh:** Ingestion, Static Analysis, Orchestration, Hybrid Synthesizer, Agentic RAG, UI Cockpit.
  - **Shreshth:** AST Mutation Engine, Subprocess Sandbox, Bytecode Equivalence Classifier, FastMCP Server.
- **Thank You! Questions & Live Defense.**
- **Speaker Notes:**
  > *"In conclusion, TestForge demonstrates that autonomous multi-agent systems can achieve rigorous software engineering standards when grounded in adversarial mutation testing. We thank you for your time and welcome your questions."*
