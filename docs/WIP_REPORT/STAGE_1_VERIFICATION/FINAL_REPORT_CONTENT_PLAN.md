# TestForge Stage 1: Final Report Content Plan

**Document ID:** TF-WIP-PLAN-001  
**Inspection Date:** November 2, 2026  
**Target Document:** Academic Work in Progress (WIP) Report (DOCX & PDF, ~12–13 pages)  
**Style Reference:** Implementation-focused, rigorous academic style of NEXUS Progress Report PDF  

---

## 1. Document Architecture & Page Budget

To achieve a professional, non-bloated, and rigorous academic report, the document will adhere strictly to a ~12–13 page structural budget (excluding appendices):

- **Pages 1–2:** Chapter 1 (Project Summary) & Chapter 2 (Academic Requirements 2.1–2.6)
- **Pages 3–4:** Chapter 2 (Academic Requirements 2.7–2.12 & Table) & Chapter 3 (System Architecture, Figure 1 & Figure 2)
- **Pages 5–7:** Chapter 4 (Implementation Details & Repository References 4.1–4.17)
- **Pages 8–9:** Chapter 5 (Security & Execution Control) & Chapter 6 (Testing & Evaluation Methodology)
- **Pages 10–11:** Chapter 7 (Benchmark Results, Comparison Table & Graph) & Chapter 8 (Deployment & Screenshots)
- **Pages 12–13:** Chapter 9 (Development Progress & Future Work), Chapter 10 (Conclusion), and Academic References
- **Appendices:** Appendices A–D (API Endpoints, Provenance, Repository URLs, Extended Evidence)

---

## 2. Chapter-by-Chapter Content Specification

### Chapter 1: Project Summary
- **1.1 Project Overview:** Definition of TestForge as an autonomous multi-agent unit test hardening system targeting Python codebases.
- **1.2 Background and Motivation:** The illusion of statement coverage in modern software testing; why 100% line coverage often fails to catch simple off-by-one or condition bugs.
- **1.3 Problem Statement:** Traditional automated test generation tools optimize for line execution rather than defect verification, producing shallow assertions (`assert res is not None`).
- **1.4 Project Objectives:** Autonomous callable discovery, value-aware assertion synthesis, AST-guided mutation analysis, closed-loop agentic refinement, and verifiable provenance.
- **1.5 Proposed Solution:** Multi-agent collaboration (Google ADK Generator, CrewAI Critic, AST Mutator, Process Sandbox, Blackboard) governed by an iterative reflection loop.
- **1.6 Project Scope:** Python 3.13/3.14 target modules, offline deterministic evaluation, FastMCP tool integration, and local containerization.
- **1.7 Current Project Status:** Core engine complete, 542 regression tests passing, 89.47% / 68.22% raw mutation scores independently verified, and VIVA readiness achieved.

### Chapter 2: Implementation of Academic and Technical Requirements
- Detailed analysis of all 12 faculty rubric requirements:
  - **2.1 Blackboard Architecture and Shared State Management:** `Blackboard`, `RLock`, typed partition spaces (`TargetSpace`, `MutantSpace`, `SuiteSpace`, `MetricsSpace`), pub/sub subscriptions.
  - **2.2 MCP Tool Integration:** FastMCP integration, filesystem server (`read_text_file`, `list_directory`), GitHub repository server (`get_repository_info`), `MCPClientManager`.
  - **2.3 Pydantic-Based Structured Outputs:** Strict schema validation on inter-agent payloads (`GeneratedTestPayload`, `CriticDirectivePayload`, `ToolCallResult`).
  - **2.4 Agentic Design Patterns:** Triad pattern (Generator, Critic, Evaluator) connected via closed-loop feedback in `TestForgeOrchestrator`.
  - **2.5 Callback-Based Task Monitoring:** `CallbackRegistry`, 14 typed `EventType` signals, non-blocking telemetry dispatching.
  - **2.6 A2A Communication and Agent Discovery:** A2A Protocol v0.3.0, `A2ABroker`, JSON-LD `AgentCard` at `/.well-known/agent.json`.
  - **2.7 Google ADK Integration:** `ADKModelBridge` subclassing `BaseLlm`, `InMemorySessionService`, tool definitions.
  - **2.8 CrewAI Integration:** `CrewAICriticAgent` configuring "Senior Mutation Testing Specialist" role via `Crew` and `Task`.
  - **2.9 Security Guardrails:** AST security visitor, SSRF hostname whitelist, bounded stream reader, XML delimiter envelopes.
  - **2.10 Observability and Provenance:** SHA-256 cryptographic suite tracing across 4 lifecycle stages, JSONL trace log.
  - **2.11 Multi-Run Benchmarking:** `BenchmarkRunner` computing mean, median, IQR across repeated trials, ablation engine.
  - **2.12 Deployment Readiness:** Production multi-stage Dockerfile, docker-compose, and liveness/readiness probes.
- **Requirement Summary Table:** Comprehensive verification status scorecard with test counts.

### Chapter 3: System Architecture
- **3.1 Overall System Architecture:** High-level overview of UI, Backend, Orchestration, and Sandboxing tiers.
- **3.2 Frontend and Backend Architecture:** FastAPI async REST/WebSocket engine paired with vanilla ES6 single-page cockpit.
- **3.3 Multi-Agent Architecture:** Cognitive roles and boundaries between Generator, Critic, and Sandbox Evaluator.
- **3.4 Agent Communication and Coordination:** Asynchronous dispatching via Blackboard events and A2A Broker.
- **3.5 Blackboard and Shared State Flow:** State transitions from revision 0 through reflection iterations.
- **3.6 Technology Stack:** Python 3.13, FastAPI, FastMCP, Google ADK, CrewAI, Pytest, Mutmut-compatible AST transformer, SQLite WAL.
- **3.7 End-to-End Execution Workflow:** Step-by-step sequence from file ingestion to hardened test suite export.
- **Figure 1 (System Architecture):** Strict black-and-white vector diagram detailing all subsystem relationships.
- **Figure 2 (Execution Workflow):** Strict black-and-white sequence diagram detailing inter-agent data flow.

### Chapter 4: Implementation Details and Repository References
- Standard subsection format across all 17 components:
  - *Purpose*, *Implementation*, *Execution Flow*, *Repository Reference* (file, class, function, line range), *Verification* (tests, artifacts).
- **4.1 Development Environment and Project Structure**
- **4.2 Source Code Ingestion (`testforge/ingestion.py:TargetManagerAgent`)**
- **4.3 AST Analysis and Callable Discovery (`testforge/intelligent_generator.py:ASTCallableAnalyzer`)**
- **4.4 Intelligent Test Case Generation (`testforge/intelligent_generator.py:IntelligentASTSynthesizer`)**
- **4.5 Test Execution and Sandboxing (`testforge/sandbox.py:ParallelSandboxRunner`)**
- **4.6 Mutation Testing Engine (`testforge/mutator.py:ASTMutator`)**
- **4.7 Mutation-Guided Refinement (`testforge/orchestrator.py:TestForgeOrchestrator`)**
- **4.8 Blackboard and Persistent Shared State (`testforge/blackboard.py:Blackboard`)**
- **4.9 MCP Tool Execution (`testforge/mcp_server.py`, `testforge/mcp_client.py`)**
- **4.10 A2A Communication (`testforge/a2a.py`, `testforge/a2a_protocol.py`)**
- **4.11 Google ADK Generator (`testforge/adk_generator.py:ADKModelBridge`)**
- **4.12 CrewAI Critic (`testforge/crew_critic.py:CrewAICriticAgent`)**
- **4.13 Pydantic Data Models (`testforge/a2a.py`, `testforge/state.py`)**
- **4.14 Callback and Logging Mechanisms (`testforge/callbacks.py`, `testforge/logger.py`)**
- **4.15 FastAPI Backend (`server.py`)**
- **4.16 Frontend Integration (`frontend/app.js`)**
- **4.17 Checkpointing and SQLite Persistence (`testforge/persistence.py:SQLiteBlackboardStorage`)**

### Chapter 5: Security and Execution Control
- **5.1 Source Code Validation:** AST syntax verification prior to compilation.
- **5.2 Sandboxed Test Execution:** Isolated scratch directory per mutant, subprocess timeout enforcement.
- **5.3 AST-Based Security Inspection:** `_ASTSecurityVisitor` node filtering.
- **5.4 Restricted Imports and Operations:** Blocking dangerous syscalls (`os`, `sys`, `subprocess`, `socket`).
- **5.5 Input Validation & Bounded Streaming:** 500 KB limit, XML delimiter isolation.
- **5.6 Filesystem & Network Restrictions:** Path confinement under sandbox root, SSRF IP blocking.
- **5.7 Execution Timeouts and Cancellation:** Cooperative job cancellation token check in orchestrator.
- **5.8 Credential Redaction:** Regex pattern scrubbing for tokens/passwords in logs and checkpoints.
- **5.9 Clean-Code Integrity Verification:** `GranularTestValidator` ensuring tests pass on clean target before mutant evaluation.

### Chapter 6: Testing and Evaluation Methodology
- **6.1 Testing Strategy:** Multi-tiered verification pyramid (Unit $\rightarrow$ Subsystem $\rightarrow$ E2E $\rightarrow$ Regression).
- **6.2 Unit Testing:** 542 automated unit tests across 48 test modules.
- **6.3 Integration Testing:** MCP tool client-server tests, A2A broker round-trips.
- **6.4 Regression Testing:** Continuous regression gate preventing defect reintroduction.
- **6.5 End-to-End Browser Testing:** 16-step headless/visible browser automation via Playwright/agent-browser.
- **6.6 Mutation Testing Methodology:** 9 operator families generating 19 and 258 mutants.
- **6.7 Statement Coverage Measurement:** `coverage.py` integration inside test sandbox.
- **6.8 Independent Validation:** Scratch directory reproduction with isolated databases.
- **6.9 Failure Scenario Testing:** Adversarial defect injection, timeout handling, and cancellation recovery.

### Chapter 7: Benchmark Results and Performance Analysis
- **7.1 Initial Mutation Testing Baseline:** 5.26% on `discount.py`, 3.10% on `uploaded_logistics_engine.py`.
- **7.2 Improvements in Intelligent Test Generation:** Value-aware assertions, boundary synthesis, negative exception testing.
- **7.3 Discount Benchmark:** 11 tests, 100% pass, 100% coverage, 89.47% raw (94.44% adjusted).
- **7.4 Logistics Benchmark:** 64 tests, 100% pass, 90.15% coverage, 68.22% raw (75.21% adjusted), 10/10 callables.
- **7.5 Test Coverage Analysis:** Line coverage vs. mutation score correlation.
- **7.6 Mutation Score Analysis:** Surviving mutant breakdown across operator families.
- **7.7 Initial Versus Current Performance:** Side-by-side metric comparison table.
- **7.8 Result Interpretation:** Empirical proof of mutation score gains (17x–22x improvement).
- **Benchmark Graph:** High-contrast bar chart comparing Baseline vs. Hardened Raw vs. Hardened Adjusted scores.

### Chapter 8: Deployment and Demonstration Status
- **8.1 FastAPI Application Execution:** Port 8000 startup, uvicorn async server.
- **8.2 Frontend Availability:** Single-page dashboard, real-time WebSocket telemetry.
- **8.3 API Health Verification:** `/healthz` and `/readyz` probe responses.
- **8.4 A2A Agent Discovery Endpoint:** Live AgentCard JSON-LD verification.
- **8.5 Docker and Container Readiness:** Multi-stage image build, docker-compose orchestration.
- **8.6 Demonstration Workflow:** Minute-by-minute live hardening walkthrough.
- **8.7 Current Demonstration Readiness:** Verification scorecard of live interactive capabilities.
- **Application Screenshots (Figures 3, 4, 5, 6):** Real browser captures from Phase 4 verification.

### Chapter 9: Development Progress and Future Work
- **9.1 Development Phases Completed:** Phases 1–5 review (Baselines, AST bugfix, Multi-Callable, Independent Validation, VIVA Package).
- **9.2 Major Implementation Milestones:** Timeline of completed engineering achievements.
- **9.3 Current Implementation Status:** Working prototype status.
- **9.4 Remaining Work:** Cloud CI/CD pipeline integration, additional mutation operators (e.g. statement deletion).
- **9.5 Future Improvements:** Dynamic symbolic execution (concolic testing), multi-file inter-module call graph analysis.
- **9.6 Expected Final Project Outcome:** Fully autonomous self-hardening CI/CD bot for enterprise software testing.

### Chapter 10: Conclusion
- **10.1 Summary of Work Completed:** Recap of architectural and empirical accomplishments.
- **10.2 Achievement of Project Objectives:** Assessment against original thesis objectives.
- **10.3 Overall WIP Status:** Exemplary academic project readiness.

### References & Appendices
- **Academic References:** Peer-reviewed literature on mutation testing (Jia & Harman), agentic frameworks (CrewAI, ADK), and testing standards.
- **Appendix A:** Comprehensive REST & WebSocket API Endpoint Catalog.
- **Appendix B:** Full Discovered Callables & Mutation Operator Distribution.
- **Appendix C:** Project Setup, Virtual Environment, and Execution Instructions.
- **Appendix D:** Complete Pytest Suite Inventory & Execution Evidence.

---

## 3. Visual Figures Specification

### Figure 1: Overall TestForge System Architecture
- **Design:** Pure black-and-white vector diagram.
- **Format:** High-resolution SVG / 300 DPI PNG with pure white background (`#FFFFFF`), solid black borders (`#000000`), crisp rectangular boxes, clean directional arrows, and readable typography (sans-serif / JetBrains Mono).
- **Components Shown:**
  1. User Interface (Unified Web Cockpit, Browser DOM).
  2. FastAPI Backend & WebSocket Hub (`server.py`).
  3. Master Hardening Orchestrator (`TestForgeOrchestrator`).
  4. Cognitive Agents Tier:
     - Target Manager Agent (`Ingestion`).
     - Intelligent AST Synthesizer (`intelligent_generator.py`).
     - Google ADK Generator (`adk_generator.py`).
     - CrewAI Adversarial Critic (`crew_critic.py`).
  5. Communication & Tooling Layer:
     - Agent-to-Agent Broker (`A2ABroker`, A2A v0.3.0).
     - FastMCP Servers (Filesystem & GitHub Tools).
     - Callback Event Registry (`CallbackRegistry`).
  6. Shared Memory & Storage Tier:
     - Thread-Safe In-Memory Blackboard (`Blackboard`, 5 Partitions).
     - SQLite WAL-Mode Checkpoint Storage (`SQLiteBlackboardStorage`).
  7. Verification Sandbox:
     - Parallel Process Test Runner (`ParallelSandboxRunner`).
     - AST Mutation Engine (`ASTMutator`, 9 Operators).
     - Granular Assertion Validator (`GranularTestValidator`).

### Figure 2: Multi-Agent Execution Workflow
- **Design:** Pure black-and-white sequence / flow diagram.
- **Components & Interactions:**
  1. Ingestion Phase: User $\rightarrow$ Backend $\rightarrow$ AST Parser $\rightarrow$ Blackboard (`target_space`).
  2. Callable Discovery: AST Analyzer extracts 10 callables $\rightarrow$ Blackboard.
  3. Baseline Synthesis: Generator crafts nominal, boundary, and negative tests $\rightarrow$ Sandbox executes tests $\rightarrow$ Blackboard (`suite_space`).
  4. Mutation Injection: AST Mutator generates 258 mutants $\rightarrow$ Parallel Sandbox runs test suite across all mutants $\rightarrow$ Blackboard (`mutant_space`).
  5. Adversarial Critique: CrewAI Critic identifies surviving mutant diffs $\rightarrow$ Issues structured reflection directives $\rightarrow$ Blackboard (`critic_space`).
  6. Refinement Loop: Generator synthesizes targeted boundary assertions $\rightarrow$ Sandbox re-evaluates surviving mutants $\rightarrow$ Iteration counter increments.
  7. Finalization: Terminal condition met ($\ge 85\%$ or max iterations) $\rightarrow$ Atomic checkpoint saved in SQLite $\rightarrow$ Final hardened test suite exported.

### Screenshots Selection (Figures 3, 4, 5, 6)
- **Figure 3:** `qa_artifacts/phase4_final_readiness_20261031_144500/screenshots/01_homepage.png`  
  *Caption:* Figure 3: TestForge Unified Application Dashboard and System Health Overview.
- **Figure 4:** `qa_artifacts/phase4_final_readiness_20261031_144500/screenshots/07_discount_hardened_kpi.png`  
  *Caption:* Figure 4: Automated Test Generation and Mutation Testing Terminal KPI Results for `discount.py` (89.47% Mutation Score, 100% Statement Coverage).
- **Figure 5:** `qa_artifacts/phase4_final_readiness_20261031_144500/screenshots/11_logistics_hardened_kpi.png`  
  *Caption:* Figure 5: Enterprise Multi-Callable Hardening Terminal Results for `uploaded_logistics_engine.py` (64 Tests, 176 Mutants Killed, 68.22% Mutation Score).
- **Figure 6:** `qa_artifacts/phase4_final_readiness_20261031_144500/screenshots/08_checkpoints_timeline.png`  
  *Caption:* Figure 6: Persistent Blackboard Checkpoint Timeline in SQLite showing Atomic Revisions and Semantic Diff Controls.

### Figure 7: Benchmark Performance Graph
- **Design:** Clean, publication-quality bar chart comparing Baseline Raw vs. Hardened Raw vs. Hardened Adjusted mutation scores for both benchmark suites (`discount.py` and `uploaded_logistics_engine.py`).
- **Data Points:**
  - `discount.py`: Baseline 5.26% $\rightarrow$ Hardened Raw 89.47% $\rightarrow$ Hardened Adjusted 94.44% (Live UI 94.7%).
  - `uploaded_logistics_engine.py`: Baseline 3.10% $\rightarrow$ Hardened Raw 68.22% $\rightarrow$ Hardened Adjusted 75.21%.

