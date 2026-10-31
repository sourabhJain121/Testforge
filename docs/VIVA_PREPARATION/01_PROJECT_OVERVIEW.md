# TestForge: Project Overview & Executive Summary

**Project Title:** TestForge — Autonomous Agentic Mutation Testing and Test Hardening System  
**Academic Target:** Final Year Computer Science / Software Engineering Evaluation & Oral Defense (VIVA)  
**Author:** Sourabh Jain  
**Repository:** `/Users/sourabh/TestForge`  
**Production Runtime:** FastAPI on Python 3.13 (`http://127.0.0.1:8000`)  
**Active Database:** SQLite Checkpoints (`qa_artifacts/testforge_checkpoints.db`, 195 MB, 1,104 snapshots)  

---

## 1. Executive Summary

Modern software engineering relies heavily on automated test suites and statement coverage metrics (e.g. `pytest --cov`). However, high statement coverage provides a **dangerous false sense of security**: a test suite can execute 100% of the lines in a program without asserting a single meaningful property (e.g. testing with `assert result is not None` or having no assertions at all).

**TestForge** solves this fundamental defect by building an autonomous multi-agent software testing pipeline that evaluates and hardens unit tests against **mutation analysis**. Rather than merely checking whether code was executed, TestForge systematically injects synthetic faults into the program AST (Abstract Syntax Tree)—altering arithmetic operators, inverting conditional branches, and swapping boundary thresholds. It then coordinates specialized AI agents (powered by Google Agent Development Kit and CrewAI) over a thread-safe shared **Blackboard** to synthesize value-aware, boundary-driven unit tests specifically designed to kill surviving mutants.

---

## 2. The Core Problem: The Code Coverage Illusion

In traditional software development:
- **Code Coverage (Statement Coverage):** Measures *execution reachability*. Did the CPU program counter visit line $N$?
- **The Defect:** If a function `calculate_discount(price, quantity, is_member)` is invoked in a test as `calculate_discount(100, 5, True)` without asserting that the returned price is exactly `$80.00`, the coverage tool records 100% line coverage. If a bug is later introduced (e.g. changing discount rate from 20% to 0%), the test suite still passes!

```
┌────────────────────────────────────────────────────────┐
│ The False Sense of Security in Standard Testing        │
├──────────────────────────┬─────────────────────────────┤
│ Metric                   │ What it Actually Measures   │
├──────────────────────────┼─────────────────────────────┤
│ 100% Line Coverage       │ 100% of lines executed.     │
│ 0% Mutation Score        │ 0% of injected bugs caught. │
│ Result                   │ Broken tests, silent bugs.  │
└──────────────────────────┴─────────────────────────────┘
```

**Mutation testing** is the gold standard for assessing test suite quality:
- A "mutant" is a copy of the target program with a deliberate single-token fault injected (e.g. changing `price <= 0` to `price < 0`, or `+` to `-`).
- If the test suite **fails** when run against the mutant, the mutant is **killed** (defect caught).
- If the test suite **passes** against the mutant, the mutant has **survived** (test suite blind spot).

TestForge automates the discovery, critique, and repair of these blind spots.

---

## 3. High-Level Solution Architecture

TestForge replaces passive test generation with an **agentic generator-critic-reflection loop** coordinated across five architectural layers:

```
┌────────────────────────────────────────────────────────────────────────┐
│                        FastAPI Web Frontend & UI                       │
│     (Mode A: Upload, Mode B: Synthesis, Mode C: GitHub Ingestion,      │
│      Blast Radius, Hardening Lab, Wiretap, Checkpoints Diff)           │
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ HTTP / WebSocket JSON-RPC
┌───────────────────────────────────▼────────────────────────────────────┐
│                  TestForge Central Orchestrator                        │
│                 (State Machine & Lifecycle Gating)                     │
└─────────┬─────────────────────────┬──────────────────────────┬─────────┘
          │                         │                          │
┌─────────▼─────────────┐ ┌─────────▼────────────┐ ┌───────────▼─────────┐
│   Google ADK Bridge   │ │  CrewAI Adversarial  │ │   Parallel Mutator  │
│    Test Generator     │ │        Critic        │ │       Sandbox       │
│  (Value-Aware / BVA)  │ │   (Fault Analysis)   │ │  (Isolated Runners) │
└─────────┬─────────────┘ └─────────┬────────────┘ └───────────┬─────────┘
          │                         │                          │
          └─────────────────────────┼──────────────────────────┘
                                    │ State Updates
┌───────────────────────────────────▼────────────────────────────────────┐
│                    Synchronized Blackboard State                       │
│    [Target Space] [Suite Space] [Mutant Space] [Critic Space] [Metrics]│
└───────────────────────────────────┬────────────────────────────────────┘
                                    │ Point-in-time Snapshots
┌───────────────────────────────────▼────────────────────────────────────┐
│            SQLite Checkpoint Persistence & Audit Trail                 │
│               (qa_artifacts/testforge_checkpoints.db)                  │
└────────────────────────────────────────────────────────────────────────┘
```

1. **AST Ingestion & Blast Radius Analysis:** Analyzes the target Python module, extracts all public functions, classes, instance methods, and static methods, and derives a call dependency graph.
2. **Safe Pre-Flight Reference Execution:** Evaluates candidate test inputs against clean reference code inside an isolated memory namespace to establish deterministic expected values without LLM hallucinations.
3. **Google ADK Generator Agent:** Synthesizes boundary-value, nominal, and negative exception test cases directly targeting discovered AST comparison operators.
4. **Subprocess Isolation Sandbox:** Validates candidate test suites in isolated operating system processes with hard timeouts (5.0s) and static import whitelisting.
5. **Parallel Mutation Engine:** Generates deterministic AST mutants across 9 fault classes (`ARITH_OP`, `COMP_OP`, `BOUNDARY_SWAP`, `COND_INV`, `LOGICAL_CONN`, `CONST_VAL`, `MATH_FUNC`, `OFF_BY_ONE`, `RETURN_VAL`) and runs tests across multi-core CPU workers.
6. **CrewAI Adversarial Critic:** Inspects surviving mutant diffs, detects unasserted logic paths, and formulates targeted repair directives for the generator.
7. **Typed Blackboard & SQLite Checkpoint Store:** Manages synchronized state partitions and commits immutable, auditable checkpoints.

---

## 4. Key Quantitative Results

Across empirical evaluations verified in Phases 2, 3, and 4:

| Benchmark Fixture | Discovered Callables | Statement Coverage | Mutants Evaluated | Killed Mutants | Raw Mutation Score | Adjusted Mutation Score | Pytest Regression |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **`discount.py`** | 1 / 1 (100%) | 100.0% (10/10) | 19 | 17 | **89.47%** | **94.44%** | 11/11 Passed |
| **`uploaded_logistics_engine.py`** | 10 / 10 (100%) | 90.15% (119/132) | 258 | 176 | **68.22%** | **75.21%** | 64/64 Passed |
| **Full Regression Suite** | 44 test modules | N/A | N/A | N/A | N/A | N/A | **542 passed, 0 failed** |

---

## 5. Technology Stack Summary

- **Programming Language:** Python 3.13.18 (Apple Silicon ARM64 optimized).
- **Backend Framework:** FastAPI 0.115+, Uvicorn ASGI server.
- **Agent Frameworks:** Google Agent Development Kit (ADK) integration contracts, CrewAI 0.100+ multi-agent framework.
- **Interoperability Standards:** Model Context Protocol (FastMCP Python SDK v1.28.0), Agent-to-Agent (A2A) protocol specification v0.3.0.
- **Testing & Mutation:** Pytest 9.1+, Coverage.py, AST-based deterministic mutation injector.
- **Database & Storage:** SQLite3 with WAL mode, JSON serialization, SHA-256 cryptographic provenance hashing.
- **Frontend Architecture:** Vanilla modern HTML5 / ES6 JavaScript / CSS3 (zero heavy npm frontend dependencies, single-port deployment).

