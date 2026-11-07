# TestForge — Project Overview & Problem Statement

**Document Version:** 1.0.0  
**Last Verified:** November 2, 2026  
**Reference Codebase:** `testforge/`  

---

## 1. Project Title & Abstract

### Project Title
**TestForge — Autonomous Multi-Agent Unit Test Hardening via Mutation-Verified Reflection Loops**

### Abstract
Modern software engineering relies heavily on automated test suites to prevent functional regressions and ensure software reliability. However, industry and academic research consistently demonstrate that traditional test suites—even those reporting high statement or branch coverage—often fail to detect subtle boundary faults, off-by-one errors, and logical discrepancies. Test coverage measures only what code is *executed*, not whether the test assertions are capable of *detecting faults* when execution deviates from expected behavior.

**TestForge** is an enterprise-grade, autonomous multi-agent software testing platform that shifts the automated testing paradigm from superficial line coverage to **fault-revealing mutation test hardening**. Built around a blackboard architectural pattern, TestForge coordinates specialized autonomous agents (Target Ingestion, Test Generator, Adversarial Critic, and Orchestrator) to analyze Python target code via Abstract Syntax Tree (AST) inspection, generate boundary-focused candidate Pytest suites, execute them against syntactically valid mutants, analyze surviving mutants through an adversarial critic loop, and iteratively harden assertions until a target mutation kill threshold is reached. TestForge operates transparently across multi-tier LLM providers (Google Gemini, OpenRouter, local Ollama with CodeLlama and Qwen) and provides deterministic offline AST synthesis fallbacks, complete SQLite checkpoint persistence, FastMCP tool integration, and full OpenTelemetry/JSONL observability.

---

## 2. Problem Statement: The Coverage Illusion

### The Fundamental Flaw of Code Coverage
For decades, engineering teams have treated statement coverage ($\frac{\text{Executed Lines}}{\text{Total Lines}} \times 100$) as the gold standard of test quality. However, code coverage suffers from three fundamental weaknesses:
1. **Weak Assertions:** A test can execute 100% of the lines in a module without asserting anything meaningful (e.g., executing `calculate_discount(100, 5, True)` without checking the return value, or using trivial checks like `assert result is not None`).
2. **Missing Boundary Value Coverage:** A test may execute a conditional branch `if price <= 0:` using `price = -10`, but fail to test the boundary value `price = 0`, where off-by-one errors commonly lurk.
3. **Execution Without Fault Detection:** Line coverage guarantees that code was loaded into the CPU instruction cache; it does not guarantee that semantic faults will cause test failures.

### The Problem in Concrete Terms
Consider the following real-world example from `samples/discount_module.py`:

```python
def calculate_discount(price: float, quantity: int, is_member: bool) -> float:
    if price <= 0 or quantity <= 0:
        return 0.0
    discount = 0.0
    if quantity >= 10:
        discount += 0.10
    if is_member:
        discount += 0.05
    return round(price * (1.0 - discount), 2)
```

A conventional test suite might write:
```python
def test_discount():
    assert calculate_discount(100.0, 10, True) == 85.0
```
This single test achieves **100% statement coverage**! Every single line of `calculate_discount` is executed. Yet, if a developer introduces an off-by-one mutation:
```python
# Mutant: Changed >= to >
if quantity > 10:
    discount += 0.10
```
Or changes the boundary check:
```python
# Mutant: Changed <= to <
if price < 0 or quantity <= 0:
    return 0.0
```
The test suite will **PASS**, completely failing to detect the bug. This is the **Coverage Illusion**.

---

## 3. Motivation: Mutation Testing as the Ground Truth

### What is Mutation Testing?
Mutation testing evaluates test suite quality by injecting artificial syntactic faults (mutants) into the source code and verifying whether the test suite fails (kills the mutant). If the test suite passes on a mutant, the mutant **survives**, proving that the test suite has an assertion blind spot.

The **Mutation Score** represents the true fault-detection effectiveness of a test suite:
$$\text{Raw Mutation Score} = \left( \frac{\text{Mutants Killed}}{\text{Total Viable Mutants Generated}} \right) \times 100$$

### Why Has Mutation Testing Not Been Widely Adopted?
1. **Computational Cost:** Running hundreds of mutants requires repeatedly executing the test suite in isolated subprocesses.
2. **Manual Test Authoring Bottleneck:** When a mutant survives, a human engineer must manually inspect the unified diff, diagnose why the existing assertions missed it, and write targeted test cases to kill it.
3. **Equivalent Mutants:** Syntactic changes that do not alter program semantics (e.g., changing `x = x + 0` or mutating dead code) cannot be killed by any test, distorting the score.

TestForge solves these problems by combining **autonomous multi-agent deliberation**, **AST-based mutant generation**, **conservative equivalent mutant analysis**, and **reflection loops** to automate both the diagnosis and generation of mutant-killing tests.

---

## 4. Primary Research Objectives

TestForge was developed to fulfill 11 rigorous academic and faculty criteria:

| Objective / Criterion | Target Requirement | Implemented Reality in TestForge |
| :--- | :--- | :--- |
| **Criterion 1: Project Plan & Scope** | Multi-agent autonomous testing scope definition. | Structured in `docs/PROJECT_PLAN/` and verified across 11 modules. |
| **Criterion 2: System Architecture** | Distributed blackboard and multi-agent topology. | Blackboard state manager with 5 partitions and thread-safe RLock. |
| **Criterion 3: Tool Integration** | Standardized tool access layer. | Native FastMCP Filesystem and GitHub servers over stdio/JSON-RPC. |
| **Criterion 4: Agent Orchestration** | Autonomous reflection and handoffs. | FSM-driven reflection loop (Generate $\rightarrow$ Execute $\rightarrow$ Mutate $\rightarrow$ Critique $\rightarrow$ Refine). |
| **Criterion 5: Agent-to-Agent Protocol** | Standardized inter-agent messaging. | FIPA-ACL communicative acts (`REQUEST`, `INFORM`, `PROPOSE`, `REFUSE`). |
| **Criterion 6: Resumption & Persistence**| Durable state and time-travel rollback. | SQLite checkpoint persistence (1,310 verified records) with schema validation. |
| **Criterion 7: Evaluation Framework** | Comprehensive automated test validation. | 611 automated tests passing, 81.33% statement coverage. |
| **Criterion 8: Security Guardrails** | Multi-layer sandbox and prompt defense. | AST scope extraction, FastMCP allowlists, 120 deterministic security trials. |
| **Criterion 9: Observability & Telemetry**| Transparent token, latency, and agent tracking.| `TraceLogger` JSONL store (305k events) with dynamic engine resolution. |
| **Criterion 10: Performance Evaluation** | Empirical benchmarking of architectures/personas.| Authoritative 60-run benchmark matrix with statistical latency & cost formulas. |
| **Criterion 11: Deployment & Release** | Production containerization and web interface. | FastAPI backend, responsive SPA frontend, SSE live wiretap, Docker Compose. |

---

## 5. Scope & Boundary Conditions

### In-Scope Capabilities
- **Target Language:** Pure Python 3.10–3.13 source code (functions, standalone classes, instance methods, classmethods, staticmethods).
- **Test Framework:** Pytest format with deterministic assertions, parameterization, and boundary fixtures.
- **Mutation Engine:** Native AST-level mutation operators (Arithmetic, Relational, Logical, Boundary, Return Value, Bitwise).
- **Execution Sandboxing:** Subprocess isolation with timeouts, memory constraints, and directory restrictions.
- **Multi-Tier LLM Support:** Google Gemini (Cloud), OpenRouter (Cloud), Ollama CodeLlama / Qwen (Local), and Deterministic AST Synthesizer (Offline).

### Out-of-Scope / Excluded Gaps
- Compilers for compiled languages (C++, Rust, Go) — TestForge targets Python ASTs exclusively.
- Active cloud penetration testing — Security evaluation uses deterministic simulated attack strings against local filters.
- Paid API quota burning — Automated CI regression runs utilize the offline deterministic AST synthesizer to preserve cost and guarantee reproducibility.

