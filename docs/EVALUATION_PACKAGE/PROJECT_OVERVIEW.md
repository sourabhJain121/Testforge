# TestForge — Academic Project Overview

**Course:** CSE3101 - Agentic AI  
**Project:** TestForge — Autonomous AI-Powered Code-Hardening & Testing Platform  
**Authors:** Sourabh & Shreshth  
**Evaluation Candidate Date:** October 30, 2026  
**Status:** Implementation Finalized up to Phase 2B (Frozen for Academic Evaluation)  

---

## 1. Executive Summary & Problem Statement

Software testing in modern agile environments faces a dual bottleneck:
1. **The Assertion Fragility Problem:** Developers write unit tests that achieve high statement coverage while failing to test boundary conditions, edge cases, and arithmetic/comparison operator inversions. Traditional tests frequently pass even when critical business logic has defects.
2. **The Autonomous Agent Security Vulnerability:** When AI coding assistants ingest arbitrary public repositories or dependencies, they become vulnerable to indirect prompt injections embedded in source comments, function docstrings, README files, or AST mutation diffs, potentially causing credential leakage or arbitrary command execution.

**TestForge** solves both problems. It is an agentic, multi-agent AI code-hardening platform that automatically ingests Python source modules, parses their Abstract Syntax Tree (AST), orchestrates iterative test synthesis and adversarial mutation testing, executes generated suites in a secure subprocess sandbox, and enforces comprehensive indirect prompt-injection defenses.

---

## 2. Core Capabilities & What TestForge Does

1. **Source Ingestion & Static Analysis:**
   - Ingests Python modules from local files or public GitHub repositories.
   - Parses AST call graphs, extracts function signatures, calculates line counts, and tracks SHA-256 byte-level provenance.
2. **Deterministic AST Mutation Engine:**
   - Injects deterministic syntactic faults into target code:
     - Comparison operator replacements (`<` $\leftrightarrow$ `<=`, `==` $\leftrightarrow$ `!=`).
     - Arithmetic operator replacements (`+` $\leftrightarrow$ `-`, `*` $\leftrightarrow$ `/`).
     - Boolean logic flips (`and` $\leftrightarrow$ `or`).
     - Boundary and constant shifts (`0` $\leftrightarrow$ `1`, `True` $\leftrightarrow$ `False`).
     - Return value substitutions.
3. **Multi-Agent Test Hardening Loop:**
   - **Google ADK Generator Agent (`GoogleADKTestGenerator`)**: Employs Google's official Agent Development Kit (`google.adk`) to deliberate over surviving mutants and synthesize targeted boundary tests.
   - **CrewAI Adversarial Critic Agent (`CrewAICriticAgent`)**: Uses CrewAI tasks and agents to analyze surviving mutant AST diffs and produce diagnostic reflection directives.
   - **Hybrid LLM Client**: Bounded model abstraction supporting Gemini, Claude, OpenAI, and local Ollama, with offline deterministic test synthesis test doubles.
4. **Isolated Subprocess Sandbox:**
   - Executes candidate tests against original code and mutated variants in separate, bounded subprocesses.
   - Enforces strict execution timeouts (default 5.0s) and static AST pre-execution filters to prevent infinite loops, fork bombs, and system tampering.
5. **Mutation Score & Equivalent Mutant Filtering:**
   - Evaluates test suite strength by computing Mutation Score:
     $$\text{Mutation Score} = \frac{\text{Killed Mutants}}{\text{Total Non-Equivalent Mutants}} \times 100\%$$
   - Distinguishes genuine survivors from statically equivalent mutants.
6. **Multi-Channel Interfaces:**
   - **FastAPI Backend (`server.py`)**: RESTful API endpoints for jobs, checkpoints, metrics, telemetry, and A2A discovery.
   - **Real-time Web Dashboard (`/`)**: Interactive HTML5 / CSS3 / WebSocket dashboard streaming agent lifecycle events.
   - **Streamlit Web Application (`app.py`)**: Interactive interactive workbench for configuring models, running mutation campaigns, and visualizing diffs.
7. **End-to-End Security Architecture (Phase 2A, 2A.1, 2B)**:
   - SSRF protection on GitHub requests with strict hostname whitelisting.
   - Bounded streaming downloads with atomic disk persistence.
   - Indirect prompt-injection mitigation with `<untrusted_content>` envelopes and AST comment/docstring defusing.
   - Tool execution whitelists and path traversal defenses.

---

## 3. Major Technical Achievements

- **523 Automated Tests with 100% Pass Rate:** Complete test suite verifying every component from network security to multi-agent deliberation.
- **Genuine Agent Framework Integration:** Official `google.adk` (Google ADK) and `crewai` (CrewAI) integrated within an asynchronous, reflection-guided state machine.
- **Shared Context via Blackboard:** Thread-safe, Pydantic-validated state partition architecture (`TargetSpace`, `MutantSpace`, `CriticSpace`, `SuiteSpace`, `MetricsSpace`) with SQLite checkpoint persistence and rollback resumption.
- **Agent-to-Agent (A2A) Protocol:** Formal JSON-RPC typed messaging (`REQUEST`, `INFORM`, `REFUSE`, `FAILURE`) enabling decoupled agent negotiation.
- **Comprehensive Threat Remediation:** Verified resistance against SSRF, bounded memory exhaustion, prompt injection, and tool hijacking.

---

## 4. Expected Users & Target Audience

- **Security & Quality Engineers:** Requiring mathematical assurance of test suite resilience against subtle logic bugs.
- **DevSecOps Teams:** Needing automated security scanning and prompt-injection containment before deploying AI-generated tests.
- **Academic Evaluators & Researchers:** Demonstrating the state-of-the-art in autonomous multi-agent software engineering.

