# TESTFORGE — GPT PROJECT CONTEXT
## The Single-Document Master Technical Context for AI Language Models

**Project Name:** TestForge  
**Repository Directory:** `/Users/sourabh/TestForge`  
**Primary Architecture:** FastAPI Backend (Port 8000) + HTML5/CSS3/Vanilla JS Frontend  
**Runtime:** Python 3.13 (`.venv-release/bin/python`)  
**Core Domain:** Autonomous Agentic Mutation Testing & Self-Hardening Test Suites  

---

## 1. WHAT IS TESTFORGE?

TestForge is an autonomous multi-agent software testing framework designed to solve the **"High-Coverage, Zero-Assertion Illusion"** in software engineering. High statement coverage does not guarantee fault detection: a test suite can execute 100% of code without asserting any behavioral properties.

TestForge injects artificial syntactic defects (**First-Order AST Mutants**) into Python code and evaluates whether the test suite fails (killing the mutant). When mutants survive, an adversarial multi-agent system—coordinated over a typed, in-memory **Blackboard architecture**—diagnoses surviving mutant diffs, detects equivalent mutant suspects, synthesizes targeted unit test scenarios (`normal`, `boundary`, `negative`, `exception`), and demonstrates verified jumps in mutation score ($MS$).

---

## 2. THE MULTI-AGENT SUB-SYSTEM

The system coordinates five specialized agents:
1. **TargetAnalyzerAgent (`testforge/agents.py`):** Uses Python's `ast` module to decompose target code into callables, classes, method signatures, argument types, and defaults.
2. **MutantGeneratorAgent (`testforge/mutator.py`):** Subclasses `ast.NodeTransformer` to generate first-order mutants across comparison operators (`==` <-> `!=`), arithmetic (`+` <-> `-`), unary negatives (`-x` <-> `+x`), condition inversions (`and` <-> `or`), and numeric boundary modifications.
3. **CrewAICriticAgent (`testforge/crew_critic.py`):** Integrates the **CrewAI** framework to inspect surviving mutant diffs and emit a typed [`CriticDirectivePayload`](file:///Users/sourabh/TestForge/testforge/models.py).
4. **GoogleADKTestGenerator (`testforge/adk_generator.py`):** Implements **Google Agent Development Kit (ADK)** principles with a 4-tool registry (`inspect_target_ast`, `get_surviving_mutants`, `read_critic_guidance`, `synthesize_scenario_test`) to synthesize granular Pytest functions.
5. **EvaluatorAgent (`testforge/sandbox.py`):** Executes test suites against all mutants inside an isolated subprocess sandbox with wall-clock timeouts, computing baseline vs. hardened mutation scores.

---

## 3. SHARED STATE & PROTOCOLS

- **Typed Blackboard (`testforge/blackboard.py`):** In-memory shared state partitioned into 5 spaces: `TargetSpace` $\rightarrow$ `MutantSpace` $\rightarrow$ `CriticSpace` $\rightarrow$ `SuiteSpace` $\rightarrow$ `MetricsSpace`. Eliminates direct agent coupling.
- **Model Context Protocol (FastMCP):** Two genuine FastMCP servers (`testforge/mcp_servers.py`): `testforge-filesystem-samples` (with tools `list_directory`, `get_file_info`, `read_text_file`) and `testforge-github` (`get_repository_info`). Path traversal protection enforced.
- **Agent-to-Agent (A2A) Discovery:** Exposes a live Linux Foundation A2A v0.3.0 Agent Card at `http://127.0.0.1:8000/.well-known/agent-card.json`.
- **SQLite Checkpoints:** Snapshots serialized to `qa_artifacts/testforge_checkpoints.db` for multi-run comparison and resumption.

---

## 4. DEFENSE-IN-DEPTH SECURITY

- **Outbound Socket Interception (`testforge/network_security.py`):** Monkey-patches `socket.create_connection` during testing to block non-localhost network egress.
- **SSRF Defense:** Resolves hostnames and blocks private RFC-1918 subnets (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `127.0.0.0/8`).
- **Prompt Injection Defense (`testforge/prompt_guard.py`):** Wraps untrusted target code in `<untrusted_source_code>` XML tags with strict passive-data instructions.
- **Sandbox Bounds (`testforge/sandbox.py`):** Wall-clock timeouts (5.0s) and memory caps prevent infinite loop denial-of-service.

---

## 5. EMPIRICAL BENCHMARKS & REGRESSION RESULTS

- **Full Pytest Regression:** **523 / 523 tests passed (100%)** in 351.31s (Exit code 0).
- **Dedicated Security Suite:** **84 / 84 tests passed (100%)** in 18.98s.
- **Benchmark Mutation Scores:**
  - `samples/banking.py` (55 lines): **52.2%** (12/23 killed)
  - `samples/discount.py` (42 lines): **63.2%** (12/19 killed)
  - `samples/currency_converter.py` (48 lines): **64.0%** (16/25 killed)
  - `samples/inventory_pricing.py` (60 lines): **60.0%** (15/25 killed)
  - `samples/rate_limiter.py` (50 lines): **28.0%** (7/25 killed)
  - `samples/logistics_engine.py` (240 lines, 2 classes): **52.0%** (13/25 killed; jumped from 0.0% baseline)

---

## 6. HOW TO RUN THE APPLICATION

```bash
# Terminal: Activate environment and start FastAPI
cd /Users/sourabh/TestForge
.venv-release/bin/python -m uvicorn server:app --host 127.0.0.1 --port 8000
```
- **Web Interface:** `http://127.0.0.1:8000/`
- **Swagger Docs:** `http://127.0.0.1:8000/docs`
- **A2A Card:** `http://127.0.0.1:8000/.well-known/agent-card.json`
- **Health Check:** `http://127.0.0.1:8000/healthz`
- *(Legacy Streamlit port 8501 is permanently disabled).*

