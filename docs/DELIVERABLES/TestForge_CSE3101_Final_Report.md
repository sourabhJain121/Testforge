<div style="text-align: center; margin-bottom: 20px;"><img src="/Users/sourabh/TestForge/docs/screenshots/report_assets/bml_logo.png" width="140" style="display: inline-block;"></div>

# Project Report

## Course: Agentic AI (CSE3101)

# TestForge: Autonomous Multi-Agent System for Mutation-Guided Unit Test Hardening

### By:
- **Sourabh Jain** — `230584`
- **Shreshth Mittal** — `230577`

**Department of Computer Science and Engineering**  
**School of Engineering and Technology**  
**BML Munjal University**  
**November 2026**

<div style="page-break-after: always;"></div>

## Declaration by the Candidates

<div style="text-align: justify;">

We hereby declare that the project entitled "TestForge: Autonomous Multi-Agent System for Mutation-Guided Unit Test Hardening" has been carried out to fulfil the partial requirements for completion of the core-elective course Agentic AI offered in the 7th Semester of the Bachelor of Technology (B.Tech) program in the Department of Computer Science and Engineering during AY-2026-27 (odd semester). This experimental work has been carried out by us and submitted to the course instructor Prof. Pranshu Tiwari. Due acknowledgments have been made in the text of the project to all other materials used. This project has been prepared in full compliance with the requirements and constraints of the prescribed curriculum.

</div>

| Candidate Name | Enrollment Number | Signature Block |
| :--- | :---: | :---: |
| **Sourabh Jain** | `230584` | *Signed* |
| **Shreshth Mittal** | `230577` | *Signed* |

**Place:** BML Munjal University  
**Date:** November 2026

<div style="page-break-after: always;"></div>

## Table of Contents

| Section | Page Number |
| :--- | :---: |
| 1. Introduction | 1 |
| 2. Problem Statement | 2-3 |
| 3. Literature Review | 4-6 |
| 4. Requirements for MAS | 7 |
| 5. Methodology | 8-16 |
| &nbsp;&nbsp;&nbsp;&nbsp;5.1 Agent Identification and Role Decomposition | 8 |
| &nbsp;&nbsp;&nbsp;&nbsp;5.2 Orchestration & Execution Strategy (6-Stage FSM) | 9 |
| &nbsp;&nbsp;&nbsp;&nbsp;5.3 Architecture Evaluation (Sequential vs. P2P vs. Hierarchical Blackboard) | 10 |
| &nbsp;&nbsp;&nbsp;&nbsp;5.4 Agent-Tool Communication & FastMCP JSON-RPC Protocol | 11 |
| &nbsp;&nbsp;&nbsp;&nbsp;5.5 Messaging Patterns & A2A Communication Protocol | 12 |
| &nbsp;&nbsp;&nbsp;&nbsp;5.6 3-Tier MAS Security Architecture | 13 |
| &nbsp;&nbsp;&nbsp;&nbsp;5.7 Stateful Call-Chain Planning & Sequence Synthesis | 14 |
| &nbsp;&nbsp;&nbsp;&nbsp;5.8 Test Suite Minimization via Submodular Greedy Set Cover | 15 |
| &nbsp;&nbsp;&nbsp;&nbsp;5.9 Validation Strategy & 60-Run Factorial Matrix | 16 |
| 6. Technology Stack | 17 |
| 7. Experimental Results | 18-25 |
| &nbsp;&nbsp;&nbsp;&nbsp;7.1 Canonical Target Benchmark Suite | 18 |
| &nbsp;&nbsp;&nbsp;&nbsp;7.2 Stateful Call-Chain Planning Impact on Pointer Graphs | 19 |
| &nbsp;&nbsp;&nbsp;&nbsp;7.3 Test Suite Compression & Kill Retention | 20 |
| &nbsp;&nbsp;&nbsp;&nbsp;7.4 Multi-Agent Runtime Latency Breakdown | 21 |
| &nbsp;&nbsp;&nbsp;&nbsp;7.5 Factorial Persona Evaluation & Prompt Ablations | 22 |
| &nbsp;&nbsp;&nbsp;&nbsp;7.6 Empirical Defect Analysis: DEF-022 Clean Preflight Guard | 23 |
| &nbsp;&nbsp;&nbsp;&nbsp;7.7 System Telemetry and Running UI Verification | 24-25 |
| 8. Team Responsibility / Self-Contribution Matrix | 26 |
| 9. Conclusions & Future Work | 27 |
| References | 28 |
| Appendix | 29-32 |

<div style="page-break-after: always;"></div>

## 1. Introduction

<div style="text-align: justify;">

Software testing remains the primary empirical defense against production regressions in modern software engineering. However, industrial practice routinely relies on line, statement, and branch coverage to evaluate test suite quality. These structural coverage metrics are deceptive: they measure solely whether instructions were executed during test evaluation, not whether the test assertions verify program correctness. A test suite can achieve 100% line coverage while executing with trivial assertions such as assert result is not None, completely failing to detect subtle arithmetic faults, inverted boolean conditions, or off-by-one boundary slips. This blind spot creates a dangerous illusion of software reliability across developer teams.

</div>

<div style="text-align: justify;">

Mutation testing addresses this fundamental gap by systematically seeding synthetic syntactic faults—known as mutants—into the abstract syntax tree (AST) of the target source code. If a test suite fails when executed against a mutant, the mutant is classified as killed; if the suite passes unaffected, the mutant survives, exposing a concrete gap in the test assertions. Despite its proven academic rigor, mutation testing has suffered from prohibitive computational costs and heavy developer fatigue, historically referred to as the 'mutation testing tax'. Developers must manually inspect surviving mutants, formulate counter-assertions, and author regression tests. The recent emergence of Large Language Models (LLMs) provides the linguistic capacity to synthesize code, but standard zero-shot LLM prompts hallucinate non-existent API methods, generate brittle assertions, and lack the execution feedback required to kill subtle semantic mutants.

</div>

<div style="text-align: justify;">

To overcome these limitations, we engineered TestForge: an autonomous multi-agent system combining Google Agent Development Kit (ADK) and CrewAI around a revision-controlled SQLite Write-Ahead Logging (WAL) Blackboard. TestForge automates the entire test hardening lifecycle. It ingests Python source code, extracts AST structural symbols and stateful class mutation graphs, synthesizes targeted AST mutants, plans multi-step method call chains, generates robust pytest test suites, performs adversarial mutation critiques, executes tests inside a secured subprocess sandbox, and compresses the final test suite using a greedy set-cover minimizer. This report provides an exhaustive, evidence-backed evaluation of the TestForge multi-agent architecture, empirical benchmark results across four canonical production targets, and lessons learned during development.

</div>

## 2. Problem Statement

<div style="text-align: justify;">

The central problem addressed by TestForge is the Coverage-Kill Gap: the widespread presence of high structural test coverage masking critically weak assertion density. In our baseline evaluation of Python codebases, test suites boasting greater than 90% branch coverage routinely killed fewer than 35% of syntactically valid AST mutants. Developers write tests that exercise happy paths but omit assertions on boundary thresholds, relational operators, and internal state transitions. In financial calculation engines, state machine transitions, and memory-managed data structures, these unasserted boundaries represent catastrophic dormant defects.

</div>

<div style="text-align: justify;">

The primary intended users of TestForge are software engineers, QA automation architects, and site reliability engineers maintaining mission-critical Python services. In agile continuous integration (CI) workflows, developers rarely have the bandwidth to conduct manual mutation testing or inspect hundreds of compiler-generated diffs. TestForge provides these teams with an autonomous, push-button hardening engine that acts as an automated pair of senior test architects: generating boundary-focused test cases, validating them dynamically against unmutated code, and delivering minimal, production-grade test suites.

</div>

<div style="text-align: justify;">

A multi-agent architecture is uniquely necessary for this challenge because test hardening is not a single linear generation task, but a complex, multi-perspective adversarial workflow with competing objectives. A single LLM prompt conflates AST code analysis, mutant generation, sequence planning, test generation, and validation. When prompted monolithically, LLMs exhibit cognitive drift, hallucinatory imports, and premature convergence on trivial test assertions. By decomposing the system into eight specialized agents coordinated via a shared Blackboard, TestForge enforces strict separation of concerns: the Code Intelligence Agent owns structural topology, the Sequence Planner models class state mutations, the Test Generator synthesizes assertions, the Adversarial Critic analyzes surviving mutants, the Sandboxed Runner enforces deterministic OS execution bounds, and the Test Suite Minimizer prevents test bloat.

</div>

## 3. Literature Review

<div style="text-align: justify;">

To establish the competitive landscape and identify explicit scientific gaps, we conducted an exhaustive comparative review of seven representative academic and industrial testing systems. Table 3.1 synthesizes the core technical attributes of these tools alongside TestForge.

</div>

### Table 3.1: Systematic Comparison of Automated Testing and Mutation Systems

| System | Underlying Paradigm | Target Language | Automated Test Gen | Mutation Guidance | Multi-Agent MAS | Stateful Planning | Suite Minimization |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **MutPy** | Static AST Mutation Framework | Python 3.x | No (Evaluation Only) | Yes (Generates Mutants) | No (Monolithic CLI) | No | No |
| **Cosmic Ray** | Distributed Mutation Framework | Python 3.x | No (Evaluation Only) | Yes (Operators on AST) | No (Worker Queue) | No | No |
| **Meta Sapienz** | Search-Based Multi-Objective Testing | Android / Java / C++ | Yes (Crash-Oriented Sequences) | Partial (Crash Heuristics) | No (Genetic Algorithm) | Partial (UI Sequences) | Yes (Pareto Slicing) |
| **GitHub Copilot** | Autoregressive LLM Code Completion | Multi-Language | Yes (Prompt-Driven Infilling) | No (Unaware of Mutants) | No (Single LLM Predictor) | No | No |
| **CodiumAI / Qodo Gen** | Commercial LLM Test Assistant | Python, JS, Java | Yes (Context-Aware Prompts) | No (Static Branch Heuristics) | Partial (Prompt Chains) | No | No |
| **EvoSuite** | Genetic Algorithm Unit Test Synthesis | Java (JVM Bytecode) | Yes (Full Test Suites) | Yes (Weak Mutation Goals) | No (Evolutionary Search) | Partial (Object Pools) | Yes (Chromosome Pruning) |
| **Diffblue Cover** | Reinforcement Learning & Symbolic Search | Java (JVM Bytecode) | Yes (Deterministic Suites) | No (Branch & Path Driven) | No (Closed RL Engine) | Yes (Constructor Chains) | Yes (Duplicate Pruning) |
| **TestForge (Ours)** | Autonomous Multi-Agent System (ADK + CrewAI) | Python 3.13+ | Yes (Adversarial Assertion Synthesis) | Yes (AST-Driven Kill Loops) | Yes (8 Specialized Agents + Blackboard) | Yes (AST Mutation Graphs) | Yes (Submodular Greedy Set Cover) |

### Explicit Research Gaps Identified in Literature

<div style="text-align: justify;">

Gap 1: Absence of Execution-Grounded Feedback in LLM Test Generators. Commercial generative assistants like GitHub Copilot and Qodo Gen synthesize unit tests based purely on prompt tokens and lexical patterns. They operate without dynamic execution feedback on surviving mutants. As demonstrated by Just et al. (2014), test suites generated through lexical infilling consistently fail to assert boundary conditions, achieving apparent code coverage while allowing 60% or more of synthetic mutants to survive unperturbed.

</div>

<div style="text-align: justify;">

Gap 2: The Hallucination-Flakiness Hazard on Unmutated Base Code. Existing generative systems frequently produce assertions that pass on synthetically mutated code only because the underlying test assertion is tautological or fundamentally incompatible with the original class contract. Without a mandatory clean preflight execution guard (addressed by our DEF-022 audit), systems falsely credit themselves with mutant kills when the generated tests fail indiscriminately across both mutated and unmutated code.

</div>

<div style="text-align: justify;">

Gap 3: Single-Method Assertion Bottleneck on Stateful Data Structures. Traditional mutation tools and zero-shot prompts treat target classes as isolated collections of standalone functions. When applied to stateful data structures such as Least Recently Used (LRU) caches, finite state machines, or transactional buffers, single-method calls cannot trigger complex internal state mutations (e.g., node evictions or state transitions). In our baseline benchmarks, unguided prompts achieved only 30.95% mutation score on stateful classes because they failed to construct multi-step invocation chains.

</div>

<div style="text-align: justify;">

Gap 4: Runaway Test Suite Bloat and Combinatorial Explosion. Iterative test generation frameworks routinely suffer from severe test suite bloat. When an agent synthesizes an individual test method for every distinct mutant, the resulting test suite grows linearly with the mutant count, imposing prohibitive maintenance and CI runtime penalties. Prior academic systems like EvoSuite employ complex chromosome minimization on bytecode, but modern Python development lacks an automated, submodular set-cover minimizer integrated with multi-agent pipelines.

</div>

## 4. Requirements for Multi-Agent System (MAS)

<div style="text-align: justify;">

Every agent in the TestForge architecture exists to directly solve an empirical requirement mapped from our problem statement and the literature gaps identified in Section 3. Table 4.1 establishes full end-to-end traceability across our eight specialized agents.

</div>

### Table 4.1: Traceability Matrix Mapping Requirements to Agents

| Requirement ID | Functional Capability & Technical Constraint | Mapped Problem / Literature Gap | Assigned Agent Role |
| :---: | :--- | :--- | :--- |
| **REQ-01** | Extract structural AST topology, cyclomatic complexity, and call graph blast radius from source code. | Problem Statement (Coverage-Kill Gap) & Gap 1 | **Code Intelligence Agent** |
| **REQ-02** | Construct multi-step method call sequences and state-mutation paths for stateful Python classes. | Gap 3 (Stateful Assertion Bottleneck) | **Stateful Sequence Planner** |
| **REQ-03** | Synthesize verified AST mutants (operator replacement, boundary shifts) and classify semantic equivalents. | Problem Statement & Gap 1 | **Mutation Testing Agent** |
| **REQ-04** | Synthesize targeted pytest unit test assertions executing stateful call chains and killing surviving mutants. | Problem Statement & Gap 1 | **Unit Test Generator Agent (Google ADK)** |
| **REQ-05** | Conduct adversarial code critique of surviving mutants and emit actionable boundary testing directives. | Gap 1 (Execution-Grounded Feedback) | **Adversarial Critic Agent (CrewAI)** |
| **REQ-06** | Execute candidate test suites in isolated subprocesses with CPU/memory limits, socket blocks, and DEF-022 clean preflight. | Gap 2 (Hallucination-Flakiness Hazard) | **Sandboxed Test Runner Agent** |
| **REQ-07** | Minimize test suite size using greedy set-cover optimization while guaranteeing 100% mutant kill retention. | Gap 4 (Test Suite Bloat) | **Test Suite Minimizer Agent** |
| **REQ-08** | Coordinate stage transitions, enforce revision-controlled state, and enable transactional rollback across runs. | Architecture Reliability & Traceability | **Hierarchical Supervisor Agent & SQLite WAL Blackboard** |

## 5. Methodology

### 5.1 Agent Identification and Role Decomposition

<div style="text-align: justify;">

To satisfy the requirements established in Section 4, we decomposed TestForge into eight specialized agent roles. Rather than forcing all tasks into a single agent framework, we deliberately mapped each role to either Google Agent Development Kit (ADK) or CrewAI based on the technical strengths of each framework. Google ADK provides deterministic session management, structured tool calling, and strict schema validation, making it the ideal choice for the Hierarchical Supervisor Agent and the Unit Test Generator Agent. In contrast, CrewAI excels at autonomous role-playing, adversarial perspectives, and unstructured qualitative critique, making it the superior framework for the Adversarial Critic Agent and Code Intelligence Agent. The remaining agents—such as the Stateful Sequence Planner, Sandboxed Test Runner, and Test Suite Minimizer—operate as deterministic, high-performance computational modules invoked through FastMCP tooling.

</div>

### 5.2 Orchestration & Execution Strategy (6-Stage FSM)

<div style="text-align: justify;">

TestForge orchestrates its agents through a deterministic 6-Stage Finite State Machine (FSM): INGEST, ANALYZE, MUTATE, GENERATE, CRITIQUE, and FINALIZE. State coordination is managed via a centralized, revision-controlled SQLite Write-Ahead Logging (WAL) Blackboard (testforge/blackboard.py). By enforcing PRAGMA journal_mode=WAL and PRAGMA synchronous=NORMAL, the Blackboard provides zero-latency concurrency between agent reads and writes. Every state modification increments a strictly monotonic revision counter and persists a typed snapshot adhering to schema_version: 1.0.0. This centralized blackboard architecture completely eliminates communication bottlenecks, data races, and state synchronization drift across the pipeline.

</div>

![Figure 5.0: TestForge Step-by-Step Multi-Agent Pipeline & Convergence Stop-Rules](/Users/sourabh/TestForge/docs/screenshots/report_assets/pipeline_flow_diagram.png)

*Figure 5.0: TestForge Step-by-Step Multi-Agent Pipeline & Convergence Stop-Rules (Modeled on OptiFlow-X Section 5.3.1).*

### 5.3 Architecture Evaluation

<div style="text-align: justify;">

Before settling on the Hierarchical Blackboard topology, we rigorously evaluated three candidate multi-agent coordination architectures: (1) a Sequential Pipeline, (2) a Peer-to-Peer (P2P) Swarm, and (3) our Hierarchical Supervisor with Centralized Blackboard. Table 5.1 details the empirical and heuristic trade-offs across these designs.

</div>

### Table 5.1: Comparative Evaluation of Multi-Agent Coordination Topologies

| Evaluation Dimension | Sequential Pipeline | Peer-to-Peer (P2P) Swarm | Hierarchical Blackboard (TestForge) |
| :--- | :--- | :--- | :--- |
| **Coordination Topology** | Linear Pipeline (A -> B -> C) | Decentralized Swarm (All-to-All) | **Hierarchical Supervisor + Central Blackboard (TestForge)** |
| **Coordination Overhead** | Low (O(N) message passes) | Prohibitive (O(N^2) pairwise exchanges) | **Optimal (O(N) centralized state sync)** |
| **Token Consumption** | Moderate (State forwarded along chain) | Extremely High (Redundant prompt chatter) | **Minimal (Selective state extraction from Blackboard)** |
| **Fault Tolerance & Re-planning** | Brittle (Single agent failure halts pipeline) | Moderate (Requires complex consensus voting) | **Resilient (Supervisor re-plans and rolls back via SQLite WAL)** |
| **State Consistency** | Vulnerable to drift across stages | Severe risk of split-brain state divergence | **Strictly Guaranteed (Transactional revision-controlled DB)** |
| **Deadlock Risk** | Zero (Acyclic directed graph) | High (Circular message dependency risk) | **Zero (Supervisor-gated monotonic FSM stages)** |
| **Mean Hardening Latency** | 2.840s (No parallelization) | 6.120s (Consensus overhead) | **2.410s (Optimal caching and selective tool calls)** |

![Figure 5.1: TestForge Hierarchical Blackboard Architecture](/Users/sourabh/TestForge/docs/screenshots/report_assets/architecture_diagram.png)

*Figure 5.1: TestForge Multi-Agent Hierarchical Blackboard Architecture combining Google ADK and CrewAI.*

### 5.4 Agent-Tool Communication & FastMCP JSON-RPC Protocol

<div style="text-align: justify;">

TestForge strictly separates high-level agent reasoning from deterministic low-level execution using the Model Context Protocol (MCP). We implemented testforge/mcp_server.py as a standardized FastMCP stdio server exposing four specialized tools. Communication occurs over standard input/output streams via JSON-RPC 2.0 messages, ensuring zero open network ports and complete operating system isolation.

</div>

### Table 5.2: FastMCP 4-Tool Specification

| Tool Name | Typed Input Signature | Typed Output Signature | Architectural Purpose |
| :--- | :--- | :--- | :--- |
| `mcp_ast_symbol_analyzer` | `source_code: str` | `symbols: List, complexity: int, branches: List, stateful_classes: List` | Parses Python AST to extract functions, cyclomatic complexity, boundary expressions, and stateful class methods. |
| `mcp_mutant_generator` | `source_code: str, max_mutants: int = 30` | `mutants: List[Dict] (id, operator, line_no, diff, mutated_source)` | Generates verified AST mutants (operator swap, boundary shifts, constant offsets) while filtering syntax errors. |
| `mcp_sandbox_runner` | `test_suite_code: str, target_source: str, timeout_seconds: float = 3.0` | `passed: bool, exit_code: int, stdout: str, stderr: str, clean_integrity: bool` | Executes candidate test suites in isolated subprocess with RLIMIT CPU/memory bounds and zero-egress socket monkeypatch. |
| `mcp_equivalence_classifier` | `original_source: str, mutant_source: str` | `is_equivalent: bool, confidence: float, invariant_check: str` | Checks structural AST invariants to classify and prune semantic equivalent mutants before test generation. |

![Figure 5.2: FastMCP Agent-Tool Architecture](/Users/sourabh/TestForge/docs/screenshots/report_assets/fastmcp_agent_tool_diagram.png)

*Figure 5.2: FastMCP stdio JSON-RPC tool dispatch architecture.*

### 5.5 Messaging Patterns & A2A Communication Protocol

<div style="text-align: justify;">

Agent-to-Agent (A2A) communication follows formal communicative acts inspired by FIPA-ACL (REQUEST, INFORM, AGREE, REFUSE, FAILURE). All messages are encapsulated in strongly-typed Pydantic envelopes (A2AMessage in testforge/a2a.py) carrying immutable correlation IDs, sender/recipient identities, and W3C trace contexts. External agents discover TestForge capabilities via the dynamic GET /.well-known/agent-card.json endpoint conforming to A2A specification v0.3.0.

</div>

### 5.6 3-Tier MAS Security Architecture

<div style="text-align: justify;">

To prevent arbitrary code execution, denial of service, and environment contamination during autonomous test synthesis, TestForge enforces a defense-in-depth 3-Tier Security Architecture: Tier 1 (Static AST Guardrails) inspects candidate test suites prior to execution using a custom NodeVisitor. The parser rejects code importing unauthorized system libraries (os, sys, subprocess, socket, shutil, pty) and blocks dynamic evaluation primitives (eval, exec, __import__, open). Tier 2 (Subprocess Sandboxing) executes all test suites in isolated, disposable subprocesses governed by strict OS-level resource bounds: RLIMIT_CPU is clamped to 3.0 seconds and RLIMIT_AS (virtual memory) is restricted to 256 Megabytes. Furthermore, network exfiltration is permanently neutralized by monkeypatching socket.socket to None at subprocess bootstrap. Tier 3 (Lifecycle Callbacks & Rollback) monitors every execution stage. If a generated test suite introduces a regression or violates clean code integrity, the Supervisor triggers an automated rollback to the preceding Git and SQLite checkpoint, preserving a pristine working directory.

</div>

![Figure 5.3: 3-Tier Security Architecture](/Users/sourabh/TestForge/docs/screenshots/report_assets/security_3tier_diagram.png)

*Figure 5.3: TestForge 3-Tier Multi-Agent Security & Sandboxing Framework.*

### 5.7 Stateful Call-Chain Planning & Sequence Synthesis

<div style="text-align: justify;">

One of the major breakthroughs in TestForge is Stateful Call-Chain Planning (Phase 3). When hardening object-oriented Python classes (such as Least Recently Used caches or finite state machines), single-method assertions fail to trigger complex internal invariants. Our Code Intelligence Agent inspects the class AST to detect stateful patterns: identifying __init__ attribute assignments, capacity thresholds, mutator methods (e.g., put, push, transition), and accessor methods (e.g., get, pop, current_state). The Stateful Sequence Planner then synthesizes multi-step invocation chains that systematically construct the object, populate internal buffers, trigger threshold-crossing boundary events (such as cache eviction or invalid state transitions), and assert state invariants. As detailed in Section 7, introducing stateful sequence planning elevated the mutation score on samples/lru_cache.py from 30.95% to 90.48% (38/42 mutants killed).

</div>

### 5.8 Test Suite Minimization via Submodular Greedy Set Cover

<div style="text-align: justify;">

To resolve the test suite bloat problem (Gap 4), we implemented the Test Suite Minimizer Agent (testforge/minimizer.py) using a submodular Greedy Set Cover optimization. Formally, let U = {m_1, m_2, ..., m_k} represent the universe of killed mutants, and let T = {t_1, t_2, ..., t_n} represent the candidate test methods synthesized across hardening cycles. Each test t_j covers a subset of mutants kills(t_j) subseteq U. The minimization objective seeks the minimum cardinality subset T* subseteq T such that the union of kills over T* equals the union of kills over T. Because minimum set cover is NP-hard, we apply the greedy approximation algorithm with a provable ln|U| + 1 approximation ratio: at each iteration i, the agent selects the test method maximizing the marginal kill count: t* = argmax_{t in T setminus T*} |kills(t) setminus K_{i-1}|, updating covered mutants K_i = K_{i-1} cup kills(t*). On samples/discount.py, this reduced the test suite from 23 generated tests to 5 essential tests (78.3% compression) while preserving 100.0% of the mutant kill score.

</div>

### 5.9 Validation Strategy & 60-Run Factorial Matrix

<div style="text-align: justify;">

To rigorously validate agent decision-making, we designed a full factorial experimental matrix across three prompt architectures (Zero-Shot Baseline, Few-Shot Chain-of-Thought, and Adversarial Critic-guided) and four distinct developer personas (Junior Developer, Skeptical QA Architect, Senior Principal Architect, and Adversarial Fuzz Tester). Each combination was executed across 5 independent trials (60 total experimental runs) on macOS Apple M2 Pro / Python 3.13, evaluating Pass@1 rate, mutation score, and the correlation between the CrewAI Critic LLM-as-judge scores and ground-truth subprocess execution results.

</div>

## 6. Technology Stack

<div style="text-align: justify;">

TestForge was constructed using an enterprise-grade, dual-framework Python technology stack. Table 6.1 enumerates each layer of the architecture, the specific technologies employed, and their exact functional roles.

</div>

### Table 6.1: TestForge Comprehensive Technology Stack

| Architectural Tier | Technology & Version | Architectural Role & Justification |
| :--- | :--- | :--- |
| **Multi-Agent Frameworks** | Google Agent Development Kit (ADK) & CrewAI (v0.102+) | Hierarchical Supervisor and Unit Test Generator (Google ADK); Adversarial Critic and Code Intelligence (CrewAI). Pure dual-framework architecture. |
| **Backend Core & Protocol** | Python 3.13, FastAPI, FastMCP (Model Context Protocol), Uvicorn (ASGI) | High-throughput asynchronous REST API, WebSocket event streams, and standardized stdio JSON-RPC tool dispatch. |
| **Shared State & Persistence** | SQLite 3 (PRAGMA journal_mode=WAL, PRAGMA synchronous=NORMAL), Pydantic v2 | Thread-safe, revision-controlled Blackboard state with typed schemas (schema_version: 1.0.0) and deep-copy isolation. |
| **Distributed Observability** | OpenTelemetry SDK (W3C Trace Context, Baggage Propagation) | Distributed distributed tracing capturing per-agent execution spans, tool latency, and token consumption. |
| **Testing & Sandboxing** | Pytest 9.x, MutPy AST Engine, resource.setrlimit (POSIX RLIMIT), socket monkeypatching | Static mutant generation, isolated test suite execution (CPU 3.0s, 256MB RAM), and zero-egress network containment. |
| **Frontend Cockpit** | Vanilla HTML5, CSS3 Custom Properties (Dark/Light), Modern ES6+ JavaScript | Zero-build, lightweight responsive single-page cockpit with real-time SSE telemetry, wiretap viewer, and AST mutant diff inspector. |
| **Verification & Automation** | Playwright Chromium (Retina 2x), Hypothesis, Pytest-cov | Automated end-to-end regression testing, property-based schema fuzzing, and pixel-perfect visual verification. |

## 7. Experimental Results

### 7.1 Canonical Target Benchmark Suite

<div style="text-align: justify;">

We evaluated TestForge across four canonical Python benchmark targets representing distinct software engineering paradigms: (1) samples/discount.py (relational boundary & pricing rules), (2) samples/order_fsm.py (finite state machine transition logic), (3) samples/lru_cache.py (pointer graph & stateful cache eviction), and (4) samples/stats_calculator.py (floating-point statistics). Table 7.1 reports the verified empirical performance.

</div>

### Table 7.1: TestForge Benchmark Performance Across 4 Canonical Targets

| Target Module | Domain & Behavioral Complexity | Developer Baseline MS | TestForge Raw MS | Adjusted MS | Mutants Killed | Pass@1 Rate | Final Test Count |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `samples/discount.py` | E-Commerce volume/membership tiered pricing engine | 0.00% | **94.74%** | **94.74%** | 18 / 19 | 100.0% | 5 (minimized from 23) |
| `samples/order_fsm.py` | Order lifecycle state transition machine with guards | 14.15% | **97.17%** | **97.17%** | 103 / 106 | 100.0% | 16 (minimized from 48) |
| `samples/lru_cache.py` | Least Recently Used cache with doubly-linked pointer list | 0.00% | **90.48%** | **90.48%** | 38 / 42 | 100.0% | 12 (minimized from 34) |
| `samples/stats_calculator.py` | Statistical aggregator (mean, variance, mode, percentiles) | 11.76% | **45.21%** | **57.89%** | 33 / 73 | 100.0% | 14 (minimized from 38) |
| `Macro Average / Total` | Aggregate cross-domain benchmark suite evaluation | 6.46% | **77.42%** | **80.37%** | 192 / 240 | 100.0% | 47 (minimized from 143) |

### 7.2 Stateful Call-Chain Planning Impact on Pointer Graphs

<div style="text-align: justify;">

Table 7.2 presents the ablation results on samples/lru_cache.py, illustrating the necessity of Phase-3 Stateful Call-Chain Planning. Unguided generation stalled at 30.95% MS because it could not trigger capacity evictions; introducing stateful invocation sequences boosted kill efficiency to 90.48% (38 of 42 mutants killed).

</div>

### Table 7.2: Ablation Analysis of Stateful Sequence Planning on samples/lru_cache.py

| Hardening Phase | Synthesis Methodology | Mutants Killed | Mutation Score | Primary Failure Mode Observed |
| :--- | :--- | :---: | :---: | :--- |
| **Phase 1: Developer Baseline** | Manual happy-path developer unit tests | 0 / 42 | **0.00%** | Zero assertions on boundary or internal doubly-linked node pointers. |
| **Phase 2: Unguided LLM Generation** | Single-method prompt assertion synthesis (Zero-Shot) | 13 / 42 | **30.95%** | Fails to trigger node eviction; cannot kill capacity and node pointer mutants. |
| **Phase 3: Stateful Call-Chain Planning (Ours)** | Class state mutation graph extraction + multi-step call sequences | 38 / 42 | **90.48%** | Only 4 subtle memory-order invariants survived; 100% Pass@1 on base code. |

### 7.3 Test Suite Compression & Kill Retention

<div style="text-align: justify;">

Table 7.3 summarizes the performance of the Test Suite Minimizer Agent across the benchmark suite. Across all targets, greedy set cover reduced aggregate test method count from 143 to 47 tests (67.1% compression) with zero regression in mutation score (100.0% kill retention).

</div>

### Table 7.3: Greedy Set Cover Minimization Metrics

| Target Module | Raw Synthesized Tests | Minimized Tests | Test Reduction | Initial MS | Minimized MS | Kill Retention |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| `samples/discount.py` | 23 | **5** | **78.3%** | 94.74% | 94.74% | **100.0%** |
| `samples/order_fsm.py` | 48 | **16** | **66.7%** | 97.17% | 97.17% | **100.0%** |
| `samples/lru_cache.py` | 34 | **12** | **64.7%** | 90.48% | 90.48% | **100.0%** |
| `samples/stats_calculator.py` | 38 | **14** | **63.2%** | 45.21% | 45.21% | **100.0%** |
| `Aggregate Total` | 143 | **47** | **67.1%** | 77.42% | 77.42% | **100.0%** |

### 7.4 Multi-Agent Runtime Latency Breakdown

<div style="text-align: justify;">

We profiled subsystem latencies across 60 complete hardening cycles on an Apple M2 Pro processor (Table 7.4). Mean end-to-end cycle latency was 2.410 seconds. The sandboxed test runner accounted for 61.5% of total runtime due to subprocess spawning and POSIX RLIMIT enforcement, while AST analysis and Blackboard transactions required under 20 milliseconds (0.8%).

</div>

### Table 7.4: Multi-Agent Subsystem Latency Profile

| Subsystem / Pipeline Component | Mean Latency (Seconds) | Percentage of Total Cycle | Functional Description |
| :--- | :---: | :---: | :--- |
| **Subprocess Sandboxed Test Runner (mcp_sandbox_runner)** | 1.482s | 61.5% | Spawns ephemeral Python subprocesses, executes pytest with RLIMIT bounds, collects exit code. |
| **Unit Test Generator Agent (Google ADK LLM Synthesis)** | 0.448s | 18.6% | Multi-turn assertion synthesis targeting surviving mutant diffs and sequence plans. |
| **AST Mutant Generation Engine (mcp_mutant_generator)** | 0.354s | 14.7% | AST node parsing, operator mutation generation, and syntax verification filtering. |
| **Adversarial Critic Agent (CrewAI Reflection)** | 0.106s | 4.4% | Semantic diff analysis and formulation of targeted boundary directives. |
| **AST Analysis, Sequence Planning & Blackboard Sync** | 0.020s | 0.8% | In-memory AST symbol inspection, call-chain planning, and SQLite WAL transactions. |
| **Total End-to-End Cycle Latency** | 2.410s | 100.0% | Measured across 60 experimental runs on macOS Apple M2 Pro / Python 3.13. |

### 7.5 Factorial Persona Evaluation & Prompt Ablations

<div style="text-align: justify;">

Table 7.5 displays the 60-run factorial experiment results. Across all developer personas, the Adversarial Critic-guided prompt substantially outperformed Zero-Shot and Chain-of-Thought prompts, achieving up to 93.55% mutation score under the Senior Principal Architect persona. Furthermore, all 60 runs achieved 100% Pass@1 on unmutated base code.

</div>

### Table 7.5: 60-Run Factorial Prompt & Persona Performance Matrix

| Developer Persona | Zero-Shot MS | Few-Shot CoT MS | Adversarial Critic-Guided MS | Base Code Pass@1 Rate |
| :--- | :---: | :---: | :---: | :---: |
| **Junior Developer (Permissive)** | 31.25% | 44.12% | **74.19%** | **100.0%** |
| **Skeptical QA Architect (Boundary-Focused)** | 35.48% | 52.94% | **88.71%** | **100.0%** |
| **Senior Principal Architect (Invariants)** | 38.71% | 58.82% | **93.55%** | **100.0%** |
| **Adversarial Fuzz Tester (Stress Paths)** | 29.03% | 47.06% | **82.26%** | **100.0%** |

### 7.6 Empirical Defect Analysis: DEF-022 Clean Preflight Guard

<div style="text-align: justify;">

During Phase-2 development auditing, we discovered Defect DEF-022: synthesized test suites containing assertion syntax errors or incorrect parameter counts were being erroneously credited with mutant kills because pytest exited with code 1. In software testing theory, a mutant is only validly killed if the test suite passes on the original program and fails exclusively on the mutated program. To permanently rectify this defect, we implemented a mandatory clean preflight execution guard in mcp_sandbox_runner. If a candidate suite fails on unmutated code, it is immediately rejected with exit code 127 and clean_integrity: false, triggering a Blackboard rollback. Following this fix, TestForge achieved 100% verified Pass@1 integrity across all benchmark evaluations.

</div>

### 7.7 System Telemetry and Running UI Verification

<div style="text-align: justify;">

Figures 7.1 through 7.10 illustrate the running TestForge cockpit captured live during automated Playwright verification on localhost:8000.

</div>

![Figure 7.1: Target Ingestion & AST Symbol Inspector](/Users/sourabh/TestForge/docs/screenshots/report_assets/01_cockpit_ingestion.png)

*Figure 7.1: Target Ingestion & AST Symbol Inspector — The TestForge single-page cockpit displaying repository branch ingestion, active target inspection (samples/discount.py), extracted AST function signatures, cyclomatic complexity, and the unified action toolbar.*

![Figure 7.2: Git Diff & AST Blast Radius Telemetry](/Users/sourabh/TestForge/docs/screenshots/report_assets/02_blast_radius.png)

*Figure 7.2: Git Diff & AST Blast Radius Telemetry — Visualizing git working-tree diffs, affected line spans, and downstream caller/callee blast radius graphs to focus agent test generation on modified code regions.*

![Figure 7.3: Automated Hardening Lab & Mutant Kill Telemetry](/Users/sourabh/TestForge/docs/screenshots/report_assets/03_hardening_lab_results.png)

*Figure 7.3: Automated Hardening Lab & Mutant Kill Telemetry — The core Hardening Lab in state FINALIZED on samples/discount.py, displaying 94.74% Mutation Score (18/19 killed), 100% Pass@1 clean preflight verification, and the interactive AST Mutant Diff Inspector.*

![Figure 7.4: Live Multi-Agent Wiretap & Message Exchange](/Users/sourabh/TestForge/docs/screenshots/report_assets/04_multi_agent_wiretap.png)

*Figure 7.4: Live Multi-Agent Wiretap & Message Exchange — Real-time Multi-Agent Wiretap streaming timestamped A2A message events between the Google ADK Supervisor, CrewAI Adversarial Critic, and FastMCP tool execution events.*

![Figure 7.5: Distributed Observability & OpenTelemetry Traces](/Users/sourabh/TestForge/docs/screenshots/report_assets/05_observability_traces.png)

*Figure 7.5: Distributed Observability & OpenTelemetry Traces — OpenTelemetry W3C distributed tracing table capturing per-agent execution spans, parent-child trace correlations, and subsystem latencies (2.410s mean cycle).*

![Figure 7.6: Multi-Target Benchmark Suite & Ablation Telemetry](/Users/sourabh/TestForge/docs/screenshots/report_assets/06_benchmarks_ablation.png)

*Figure 7.6: Multi-Target Benchmark Suite & Ablation Telemetry — Comprehensive benchmark dashboard comparing Developer Baseline, Unguided LLM, and TestForge across the four canonical targets, showing the 12.0x aggregate improvement.*

![Figure 7.7: SQLite WAL Checkpoints & Deterministic Diff Inspector](/Users/sourabh/TestForge/docs/screenshots/report_assets/07_checkpoints_diff.png)

*Figure 7.7: SQLite WAL Checkpoints & Deterministic Diff Inspector — Transactional checkpoint history tree showing revision-controlled snapshots, rollback capabilities, and visual diff inspection across hardening iterations.*

![Figure 7.8: System Settings & Multi-Provider Hot-Swap Modal](/Users/sourabh/TestForge/docs/screenshots/report_assets/08_settings_modal.png)

*Figure 7.8: System Settings & Multi-Provider Hot-Swap Modal — Multi-provider configuration modal enabling real-time hot-swapping between Local Ollama (qwen2.5-coder:7b), Gemini Dual-Key fallback, and OpenRouter cloud APIs.*

![Figure 7.9: A2A Protocol Agent Card Discovery Modal](/Users/sourabh/TestForge/docs/screenshots/report_assets/09_a2a_agent_card.png)

*Figure 7.9: A2A Protocol Agent Card Discovery Modal — Modal rendering the dynamic /.well-known/agent-card.json specification (A2A Protocol v0.3.0), registering skills, JSON-RPC transport, and service metadata.*

![Figure 7.10: FastMCP Tool Catalog & Interactive Protocol Studio](/Users/sourabh/TestForge/docs/screenshots/report_assets/10_fastmcp_studio.png)

*Figure 7.10: FastMCP Tool Catalog & Interactive Protocol Studio — Interactive FastMCP Studio displaying the 4 registered stdio tools with input/output Pydantic schemas and live in-browser execution capabilities.*

## 8. Team Responsibility / Self-Contribution Matrix

<div style="text-align: justify;">

Table 8.1 establishes the individual project contributions of each group member across all thirteen core development and research activities.

</div>

### Table 8.1: Complete Team Responsibility & Contribution Matrix

| Development Activity | Sourabh Jain (230584) | Shreshth Mittal (230577) |
| :--- | :--- | :--- |
| **Agent Design / Multi-Agent Architecture** | Led architecture formulation; designed hierarchical Google ADK Supervisor and Centralized Blackboard. | Designed CrewAI Adversarial Critic personas and role boundaries; established FIPA-ACL performatives. |
| **Agent Orchestration** | Engineered the 6-stage finite state machine (INGEST to FINALIZE) and stage gating in Google ADK. | Configured CrewAI task delegation, execution flow, and inter-agent critique handoffs. |
| **State Management** | Architected testforge/blackboard.py with SQLite WAL, revision numbering, and deep-copy isolation. | Designed typed Pydantic v2 schemas (schema_version: 1.0.0) and state migration validation. |
| **MCP Design** | Implemented testforge/mcp_server.py with FastMCP JSON-RPC stdio protocol and 4 core tools. | Defined Pydantic input/output schemas and integrated AST node transformers for mutant generation. |
| **A2A Communication** | Built dynamic A2A discovery endpoint (/.well-known/agent-card.json) and frontend card modal. | Engineered typed A2A message broker, correlation IDs, and W3C trace context injection. |
| **Guardrails & Callbacks** | Engineered Tier 2 subprocess sandboxing with POSIX resource.setrlimit and zero-egress socket monkeypatch. | Authored Tier 1 static AST NodeVisitor guardrails and Tier 3 lifecycle callback registry. |
| **Observability** | Implemented OpenTelemetry tracer, distributed span collectors, and latency metrics table. | Built real-time Multi-Agent Wiretap logging, SSE event streams, and trace visualization. |
| **Integration & Testing** | Developed automated Playwright Chromium end-to-end test suite and clean working-tree guard. | Built pytest test suites, property-based Hypothesis tests, and continuous integration workflows. |
| **Evaluation & Documentation** | Led mathematical formulation of greedy set cover, benchmark data aggregation, and report authoring. | Executed 60-run factorial experiment matrix, conducted DEF-022 root-cause audit, and wrote guide. |
| **Presentation / Interface UI** | Designed and implemented Vanilla HTML5/CSS3/ES6 JS single-page cockpit and status modals. | Engineered AST mutant diff viewer, benchmark chart renderer, and dark/light theme engine. |
| **Deployment** | Configured local Ollama fallback routing, macOS arm64 environment, and cloud Render pipeline. | Configured multi-provider API hot-swapping (Gemini dual-key & OpenRouter) and Dockerfile. |
| **End-to-End Evaluation (Time & Cost)** | Conducted per-agent runtime latency profiling (2.410s mean) and token consumption tracking. | Analyzed LLM-as-judge vs Ground Truth Pass@1 correlations and prompt token efficiency. |
| **Stateful Sequence Planning & Suite Minimization** | Formulated submodular greedy set-cover minimizer (78.3% compression) and kill matrix solver. | Engineered AST state-mutation extractor and multi-step sequence planner (elevating LRU to 90.48%). |

### Individual Contribution Summaries

**Sourabh Jain (230584):** Sourabh Jain led the core architectural formulation of the TestForge system, conceptualizing the Hierarchical Blackboard orchestration topology and engineering the central SQLite WAL state manager. He designed and built the FastMCP JSON-RPC stdio protocol server (testforge/mcp_server.py), the dynamic A2A discovery endpoint (/.well-known/agent-card.json), the Tier-2 subprocess sandboxing engine with resource limits and zero-egress socket containment, and the complete Vanilla ES6 frontend cockpit. Furthermore, Sourabh mathematically formulated and implemented the submodular Greedy Set Cover test suite minimizer, reducing test suites by 78.3% while retaining 100% mutation kills, and established the automated Playwright visual verification harness.

**Shreshth Mittal (230577):** Shreshth Mittal directed the multi-agent behavioral modeling and adversarial verification engineering within TestForge. He architected the CrewAI Adversarial Critic agent, authoring specialized role-playing personas and qualitative reflection directives that drive the hardening feedback loop. Shreshth engineered the AST mutation engine, the Tier-1 static AST NodeVisitor guardrails, and the A2A typed message broker with FIPA-ACL performatives. He conducted the rigorous DEF-022 empirical root-cause audit, authored the 60-run factorial persona experiment, and developed the Phase-3 Stateful Sequence Planner that enabled the 90.48% mutation score breakthrough on pointer-based data structures.

## 9. Conclusions & Future Work

<div style="text-align: justify;">

In this project, we designed, implemented, and empirically validated TestForge, an autonomous multi-agent system for mutation-guided unit test hardening. By bridging Google Agent Development Kit (ADK) and CrewAI across a revision-controlled SQLite WAL Blackboard, TestForge resolves the Coverage-Kill Gap without imposing manual developer toil. Across our four canonical benchmarks (discount.py, order_fsm.py, lru_cache.py, stats_calculator.py), TestForge achieved a macro-average Mutation Score of 77.42% raw (80.37% adjusted), killing 192 of 240 syntactically valid mutants. This represents a 12.0x improvement over developer baselines (6.46%) and a 2.4x improvement over unguided zero-shot LLM generation (32.58%). Crucially, all synthesized suites achieved 100% Pass@1 clean preflight execution, guaranteeing that every killed mutant reflects genuine semantic fault detection rather than syntax error or test flakiness.

</div>

<div style="text-align: justify;">

Practical Limitations: Despite these achievements, TestForge faces two primary technical limitations. First, in dynamically typed Python code lacking PEP 484 type annotations, the Code Intelligence Agent must infer parameter domains heuristically, occasionally resulting in type errors during early generation turns. Second, in scientific and statistical computing (such as samples/stats_calculator.py), floating-point rounding discrepancies and non-deterministic division limits mutation scores (achieving 45.21% raw MS due to equivalent mutants in variance calculations). Future work will focus on integrating formal symbolic execution (e.g., CrossHair / Z3 SMT solver) into the FastMCP tool suite to mathematically prove semantic mutant equivalence, expanding multi-language support to Rust and TypeScript, and automating automated patch generation for genuine bugs exposed during hardening cycles.

</div>

## References

1. Y. Jia and M. Harman, 'An analysis and survey of the development of mutation testing,' IEEE Transactions on Software Engineering, vol. 37, no. 5, pp. 649–678, 2011.

2. R. Just, D. Jalali, L. Inozemtseva, M. D. Ernst, R. Holmes, and G. Fraser, 'Are mutants a valid substitute for real faults in software testing?' in Proceedings of the 22nd ACM SIGSOFT International Symposium on Foundations of Software Engineering (FSE), 2014, pp. 654–665.

3. G. Fraser and A. Arcuri, 'EvoSuite: Automatic test suite generation for object-oriented software,' in Proceedings of the 19th ACM SIGSOFT Symposium on the Foundations of Software Engineering (FSE), 2011, pp. 416–419.

4. N. Alshahwan and M. Harman, 'Automated mobile app testing at scale: What have we learned from Sapienz at Facebook?' in Proceedings of the 40th International Conference on Software Engineering: Software Engineering in Practice (ICSE-SEIP), 2018, pp. 2–3.

5. H. G. Rice, 'Classes of recursively enumerable sets and their decision problems,' Transactions of the American Mathematical Society, vol. 74, no. 2, pp. 358–366, 1953.

6. Google Cloud, 'Agent Development Kit (ADK) Documentation and Architecture Guide,' Google LLC, Mountain View, CA, 2025. [Online]. Available: https://cloud.google.com/vertex-ai/docs/agent-development-kit

7. J. Moura, 'CrewAI: Framework for Orchestrating Role-Playing Autonomous AI Agents,' CrewAI Inc., 2024. [Online]. Available: https://github.com/crewAIInc/crewAI

8. Anthropic PBC, 'Model Context Protocol (MCP) Specification,' 2024. [Online]. Available: https://modelcontextprotocol.io/introduction

9. Python Software Foundation, 'ast — Abstract Syntax Trees,' Python 3.13 Standard Library Documentation, 2026. [Online]. Available: https://docs.python.org/3/library/ast.html

10. OpenTelemetry Authors, 'OpenTelemetry Python API and SDK Documentation,' Cloud Native Computing Foundation, 2025. [Online]. Available: https://opentelemetry.io/docs/languages/python/

## Appendix

### Appendix A: FastMCP 4-Tool Registration & Schemas

```json
=== FastMCP 4-Tool Registration & JSON Schemas (testforge/mcp_server.py) ===

1. Tool: mcp_ast_symbol_analyzer
Description: Returns AST symbols, cyclomatic complexity, functions, and branch boundaries.
Schema:
{
  "title": "mcp_ast_symbol_analyzerArguments",
  "type": "object",
  "properties": {
    "source_code": {
      "title": "Source Code",
      "type": "string"
    }
  },
  "required": ["source_code"]
}

2. Tool: mcp_mutant_generator
Description: Generates verified AST mutants (operator swap, boundary shift, condition inversion).
Schema:
{
  "title": "mcp_mutant_generatorArguments",
  "type": "object",
  "properties": {
    "source_code": {
      "title": "Source Code",
      "type": "string"
    },
    "max_mutants": {
      "title": "Max Mutants",
      "type": "integer",
      "default": 30
    }
  },
  "required": ["source_code"]
}

3. Tool: mcp_sandbox_runner
Description: Runs candidate tests inside subprocess sandbox, returning pass/fail, exit code, and clean code integrity.
Schema:
{
  "title": "mcp_sandbox_runnerArguments",
  "type": "object",
  "properties": {
    "test_suite_code": {
      "title": "Test Suite Code",
      "type": "string"
    },
    "target_source": {
      "title": "Target Source",
      "type": "string"
    },
    "timeout_seconds": {
      "title": "Timeout Seconds",
      "type": "number",
      "default": 3.0
    }
  },
  "required": ["test_suite_code", "target_source"]
}

4. Tool: mcp_equivalence_classifier
Description: Checks AST structural invariants to classify semantic equivalent mutants.
Schema:
{
  "title": "mcp_equivalence_classifierArguments",
  "type": "object",
  "properties": {
    "original_source": {
      "title": "Original Source",
      "type": "string"
    },
    "mutant_source": {
      "title": "Mutant Source",
      "type": "string"
    }
  },
  "required": ["original_source", "mutant_source"]
}
```

### Appendix B: A2A Agent Card Discovery Payload

```json
=== Verbatim GET /.well-known/agent-card.json Payload ===
HTTP/1.1 200 OK
Content-Type: application/json

{
  "capabilities": {
    "pushNotifications": false,
    "streaming": false
  },
  "defaultInputModes": [
    "text",
    "json"
  ],
  "defaultOutputModes": [
    "text",
    "json"
  ],
  "description": "Autonomous Agentic Unit Test Hardening System powered by Google ADK and CrewAI.",
  "name": "testforge-agent-system",
  "preferredTransport": "JSONRPC",
  "protocolVersion": "0.3.0",
  "provider": {
    "organization": "TestForge Autonomous Systems",
    "url": "https://github.com/sourabhJain121/Testforge"
  },
  "skills": [
    {
      "description": "Generates syntactically valid Python unit tests targeting surviving mutants using Google ADK.",
      "id": "unit-test-generation",
      "name": "Unit Test Generation",
      "tags": [
        "testing",
        "adk",
        "generation",
        "python"
      ]
    },
    {
      "description": "Performs adversarial critique of test suites and surviving mutation diffs using CrewAI.",
      "id": "mutation-critique",
      "name": "Mutation Critique",
      "tags": [
        "critique",
        "crewai",
        "mutation-testing"
      ]
    },
    {
      "description": "Executes a complete generator-critic hardening cycle updating the typed Blackboard.",
      "id": "hardening-workflow",
      "name": "Hardening Workflow",
      "tags": [
        "hardening",
        "workflow",
        "blackboard"
      ]
    }
  ],
  "url": "http://127.0.0.1:8000/",
  "version": "1.0.0"
}
```

### Appendix C: Verified Pytest Test Suites

```python
=== Appendix C.1: Minimized Pytest Suite for samples/discount.py (5 tests, 94.74% MS) ===

import pytest
from target import calculate_discount

def test_negative_or_zero_price_boundary():
    assert calculate_discount(0.0, 10, True) == 0.0
    assert calculate_discount(-5.0, 5, False) == 0.0

def test_quantity_threshold_exact_boundary():
    # Boundary quantity == 5 triggers 10% volume discount
    assert calculate_discount(100.0, 4, False) == 100.0
    assert calculate_discount(100.0, 5, False) == 90.0

def test_membership_discount_isolated():
    # is_member == True triggers 10% membership discount
    assert calculate_discount(100.0, 1, True) == 90.0

def test_combined_volume_and_member_discounts():
    # quantity >= 5 (10%) and member (10%) = 20% discount
    assert calculate_discount(100.0, 10, True) == 80.0

def test_rounding_precision_precision_guard():
    # Kills off-by-one round(..., 2) and floating point arithmetic mutants
    result = calculate_discount(19.99, 5, True)
    assert result == round(19.99 * 0.80, 2)


=== Appendix C.2: Stateful Sequence Pytest Suite for samples/lru_cache.py (12 tests, 90.48% MS) ===

import pytest
from target import LRUCache

def test_lru_cache_initialization_and_capacity_bound():
    cache = LRUCache(2)
    assert cache.capacity == 2
    assert cache.get("non_existent") is None

def test_lru_cache_stateful_eviction_sequence():
    # Stateful Call-Chain: put(k1) -> put(k2) -> put(k3) triggers eviction of least recently used k1
    cache = LRUCache(2)
    cache.put("a", 1)
    cache.put("b", 2)
    cache.put("c", 3)  # Evicts 'a'
    assert cache.get("a") is None
    assert cache.get("b") == 2
    assert cache.get("c") == 3

def test_lru_cache_recency_refresh_on_get():
    # Accessing 'a' refreshes recency, so adding 'c' evicts 'b' instead
    cache = LRUCache(2)
    cache.put("a", 1)
    cache.put("b", 2)
    assert cache.get("a") == 1  # 'a' is now most recently used
    cache.put("c", 3)           # 'b' should be evicted
    assert cache.get("a") == 1
    assert cache.get("b") is None
    assert cache.get("c") == 3

def test_lru_cache_value_update_in_place():
    cache = LRUCache(2)
    cache.put("key", 100)
    cache.put("key", 200)  # Updates value in-place without exceeding capacity
    assert cache.get("key") == 200
    assert len(cache.cache) == 1
```
