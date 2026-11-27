# TestForge Report — Technical Terms Study Guide

This guide explains the technical terms used in the TestForge project report. The explanations use simple language and describe how each idea relates to TestForge.

Use the **Presentation answer** sentence when you need a short explanation during a presentation. The longer explanation is useful if a reviewer asks a follow-up question.

## 1. TestForge in one minute

**TestForge** is an automated Python test-hardening system. It reads source code, studies its structure, creates controlled faulty versions of that code, checks whether the existing tests detect those faults, and generates or improves tests for the gaps it finds. Several specialized AI agents share their work through a common state store. The final test suite is checked, minimized, and exported for review.

## 2. Core testing terms

### Software regression

A regression is a new failure introduced when code is changed.

**In TestForge:** The system strengthens tests so that future changes are more likely to be detected.

**Presentation answer:** “A regression is an old behavior that breaks after a later code change.”

### Test hardening

Test hardening means improving a test suite so that it detects more meaningful faults, especially boundary and logic errors.

**In TestForge:** Hardening is the complete workflow from source ingestion to mutation analysis, test generation, repair, validation, and minimization.

**Presentation answer:** “Test hardening improves the fault-detection power of tests, not just the number of lines they execute.”

### Assertion

An assertion is a check in a test that states what result or behavior is expected.

Example: `assert calculate_discount(100, 10) == 90`.

### Assertion density

Assertion density describes how many meaningful checks a test suite contains compared with the amount of code it executes.

High line coverage with very few meaningful assertions can still leave serious bugs undetected.

### Happy path

The happy path is the normal, successful input flow. It usually does not include invalid data, limits, failures, or unusual state transitions.

### Boundary condition

A boundary condition occurs at an edge of an allowed range, such as zero, one, a maximum value, or a threshold where behavior changes.

**In TestForge:** Boundary-focused tests are important because many surviving mutants change comparison operators or threshold logic.

### Line coverage

The percentage of source-code lines executed by tests.

### Statement coverage

The percentage of executable statements reached by tests. It is similar to line coverage, but the measurement is based on executable statements rather than physical lines.

### Branch coverage

The percentage of decision outcomes exercised by tests. For an `if` statement, good branch coverage normally requires testing both the true and false paths.

### Coverage-kill gap

The coverage-kill gap is the difference between how much code a test suite executes and how many realistic faults it actually detects.

**Why it matters:** A suite can report 100% line coverage while failing to detect a wrong operator or incorrect calculation.

**Presentation answer:** “Coverage tells us where tests went; mutation score tells us whether the tests noticed wrong behavior.”

## 3. Mutation testing terms

### Mutation testing

Mutation testing evaluates test quality by making small, controlled changes to the program and checking whether the tests fail.

### Mutant

A mutant is a deliberately modified copy of the original program. It represents a possible programming mistake.

Examples include changing `>` to `>=`, replacing `+` with `-`, or changing a Boolean condition.

### Mutant generation

Mutant generation is the process of creating these controlled faulty program variants.

**In TestForge:** Mutants are created from the Python abstract syntax tree rather than by unsafe text replacement.

### Killed mutant

A mutant is killed when the test suite fails against it. This indicates that the tests detected the injected fault.

### Surviving mutant

A mutant survives when the test suite still passes after the fault is inserted. This is evidence of a missing or weak assertion.

### Mutation score

Mutation score is the proportion of non-equivalent mutants killed by the tests.

Formula:

```text
mutation score = killed mutants / valid non-equivalent mutants × 100
```

The report’s example of 18 killed out of 19 generated mutants is approximately 94.74%.

### Equivalent mutant

An equivalent mutant is syntactically different but behaves the same as the original program for all relevant inputs. It should not reduce the quality score because no test can distinguish it from the original.

### AST mutation

AST mutation changes a node in the parsed structure of a program, such as a comparison operator, constant, Boolean expression, or arithmetic operator.

### AST — Abstract Syntax Tree

An Abstract Syntax Tree is a structured representation of source code. It represents functions, calls, operators, conditions, and values as nodes in a tree.

**Why TestForge uses it:** AST nodes give the system a safer and more precise place to inspect code and create mutants than raw text editing.

### Bytecode equivalence filter

Python bytecode is the lower-level instruction form executed by the Python interpreter. A bytecode equivalence filter compares the generated variant with the original and removes variants that compile to the same effective instructions.

**Purpose:** Reduce wasted test runs on mutants that do not create a meaningful behavioral change.

## 4. Python and program-analysis terms

### Symbol

A symbol is a named program element, such as a module, class, function, method, or variable.

### Symbol topology

Symbol topology is the structural relationship between symbols: which functions call which other functions, where classes are defined, and how modules are connected.

### Call graph

A call graph is a map of function or method calls. An edge from function A to function B means A can call B.

### Blast radius

Blast radius is the set of code and behaviors that may be affected by changing a particular function or symbol.

**In TestForge:** The call graph is used to show upstream callers, downstream callees, and risk around a target symbol.

### Stateful object

A stateful object stores information that changes over time. Its output may depend not only on the current input, but also on earlier method calls.

### State transition

A state transition is a change from one internal condition to another, such as moving from “empty” to “loaded” after a method call.

### Stateful call chain

A stateful call chain is an ordered sequence of method calls whose combined order affects the result.

**Example:** Creating a cache, inserting a value, evicting an older value, and then reading the cache.

### Pointer graph

A pointer graph represents relationships between objects or references in memory-oriented code. It helps reason about which objects point to or depend on other objects.

### Reflection-repair loop

Reflection is the step where the system examines test results, failures, and surviving mutants. Repair is the next attempt to improve the tests based on that evidence. The loop repeats until the target quality threshold is reached or the system stops safely.

## 5. AI and multi-agent terms

### Artificial Intelligence (AI)

AI refers to software that performs tasks normally associated with human reasoning, such as analysis, planning, or language-based generation.

### Agentic AI

Agentic AI describes an AI system that can pursue a task through several steps, use tools, inspect results, and make the next decision instead of producing one isolated answer.

### Large Language Model (LLM)

An LLM is a model trained on large collections of text and code. It predicts and generates language or code from a prompt and surrounding context.

### Hallucination

An LLM hallucination is a confident-looking but incorrect output, such as an import, API method, file path, or test assertion that does not exist.

**In TestForge:** Execution and validation are used to catch generated tests that are syntactically valid but incorrect or unusable.

### Multi-Agent System (MAS)

A Multi-Agent System is a group of specialized agents that cooperate on one larger task.

**In TestForge:** The agents divide code intelligence, sequence planning, test generation, adversarial criticism, sandboxed execution, and suite minimization.

### Agent role decomposition

Role decomposition means splitting a complex job into focused responsibilities. Each agent has a narrower task, clearer inputs, and clearer outputs.

### Cognitive drift

Cognitive drift is the loss of focus that can happen when one model is asked to perform too many unrelated tasks in one prompt.

### Prompt injection

Prompt injection is an attempt to place instructions in input data that manipulate an AI system into ignoring its intended rules or performing an unsafe action.

### Blackboard pattern

The Blackboard pattern uses a shared state space where specialists publish observations and read information produced by other specialists.

**In TestForge:** The shared Blackboard carries facts such as discovered symbols, generated mutants, test results, telemetry, and checkpoints.

### Orchestrator

An orchestrator controls the order of work, selects the next agent or tool, and manages the overall workflow.

### Finite-State Machine (FSM)

A Finite-State Machine models a process as a finite set of states and permitted transitions.

**In TestForge:** A hardening job moves through defined stages such as ingestion, analysis, synthesis, execution, repair, and finalization.

### Google ADK

Google Agent Development Kit is an agent-development framework used in the project’s hybrid orchestration design.

### CrewAI

CrewAI is a framework for coordinating role-based AI agents and their tasks.

### Hybrid orchestration

Hybrid orchestration means using more than one coordination framework or strategy. TestForge combines Google ADK and CrewAI around shared project state.

## 6. Protocols, APIs, and data formats

### API — Application Programming Interface

An API is a defined way for one software component to request data or an operation from another component.

### FastAPI

FastAPI is the Python web framework used for TestForge’s HTTP backend and API endpoints.

### Uvicorn

Uvicorn is an ASGI server that runs the FastAPI application and accepts web requests.

### ASGI

ASGI, or Asynchronous Server Gateway Interface, is the Python interface between asynchronous web servers and web applications.

### FastMCP

FastMCP is the project’s Model Context Protocol tool-server layer. It exposes approved tools and schemas that agents can call.

### MCP — Model Context Protocol

MCP is a protocol for connecting AI models or agents to tools and structured context in a consistent way.

### JSON-RPC

JSON-RPC is a request-and-response protocol that encodes method calls and parameters as JSON objects.

### A2A — Agent2Agent

A2A is a protocol for describing and communicating with agents. An A2A Agent Card advertises an agent’s identity, capabilities, and skills.

### Agent Card

An Agent Card is a machine-readable description of an agent. It normally tells a client what the agent can do and how to communicate with it.

### Schema

A schema defines the expected shape, names, and types of data. Tool schemas help prevent agents from sending malformed arguments.

### JUnit XML

JUnit XML is a common XML format for reporting test results to continuous-integration systems, even when the tests themselves are written in Python.

### SARIF

SARIF, or Static Analysis Results Interchange Format, is a standard JSON-based format for reporting code-analysis findings in developer tools and code-hosting platforms.

## 7. Security and execution terms

### Guardrail

A guardrail is a rule or control that limits unsafe, invalid, or out-of-scope behavior.

### Input sanitization

Input sanitization checks and cleans incoming values before they are used. It reduces the chance that malformed or dangerous input reaches sensitive operations.

### Subprocess sandbox

A subprocess sandbox runs generated or analyzed code in a separate operating-system process with restrictions such as time, resource, and access limits.

**In TestForge:** It isolates test execution from the main server and makes execution failures easier to contain.

### Deterministic execution

Deterministic execution produces the same result when the same inputs, code, and configuration are used.

### Resource bound

A resource bound limits something such as execution time, memory, output size, or number of generated items.

### Human-in-the-loop

Human-in-the-loop means that a person remains responsible for an important approval or decision instead of allowing the system to perform it automatically.

**In TestForge:** Repository write actions require an approval gate.

### Repository write approval

This is the explicit permission step before generated tests or patches are written back to a project repository.

## 8. Storage, reliability, and deployment terms

### SQLite

SQLite is a small embedded relational database stored in a file. TestForge uses it for local checkpoint and snapshot data.

### WAL — Write-Ahead Logging

Write-Ahead Logging records a change in a log before applying it to the main database state. It improves recovery and allows safer concurrent reading and writing.

### Checkpoint

A checkpoint is a saved version of job state at a particular point in time. It allows inspection, comparison, or controlled restoration.

### Snapshot

A snapshot is a stored capture of the application or job state. A timeline of snapshots makes state changes auditable.

### Deterministic diff

A deterministic diff compares two saved states using a repeatable method, so the same inputs produce the same reported differences.

### Idempotency

An operation is idempotent when repeating it produces the same final state as performing it once.

### Deployment

Deployment is the process of making the application available in a runtime environment.

### Container

A container packages an application and its dependencies so it can run consistently across environments.

### Docker

Docker is a platform and toolset for building and running containers.

### Microsoft Azure Container Apps

Azure Container Apps is a managed Azure service for running containerized applications without managing the underlying server infrastructure directly.

### Render

Render is a cloud deployment platform that can build and run web services and containers.

### TokenHarbor

TokenHarbor is the configured remote model provider in TestForge. The report identifies the model as `deepseek-v4.1-flash:free`.

### Ollama

Ollama is the local model runtime used for local inference. The configured model in the report is `codellama:7b`.

### Provider hot-swapping

Provider hot-swapping means changing the configured model provider or model without redesigning the rest of the application.

## 9. Metrics, experiments, and evaluation

### Pass@1

Pass@1 measures whether the first generated candidate passes validation. A higher value means the system succeeds more often without needing another attempt.

### Telemetry

Telemetry is collected information about system behavior, such as job counts, durations, errors, and agent activity.

### KPI — Key Performance Indicator

A KPI is a selected measurement used to judge system performance or progress.

### OTel — OpenTelemetry

OpenTelemetry is a standard ecosystem for collecting traces, metrics, and logs from software systems.

### Trace

A trace records the path of one request or job across multiple components.

### Span

A span is one timed operation inside a trace, such as an agent call, tool call, or database operation.

### Latency

Latency is the time taken for an operation to complete. A latency breakdown shows which stages consume that time.

### Ablation study

An ablation study removes or disables one component at a time and measures how the result changes. It helps show whether that component is useful.

### Factorial matrix

A factorial matrix evaluates combinations of multiple factors, such as target programs, personas, or configuration choices, instead of changing only one factor in isolation.

### Benchmark

A benchmark is a repeatable workload or target used to compare systems or configurations.

### Canonical target

A canonical target is a fixed, representative example used consistently for testing and comparison.

### Empirical result

An empirical result is based on an actual measurement or experiment rather than only a theoretical argument.

### Greedy set cover

Set cover chooses a small collection of tests that together cover a desired collection of mutants or behaviors. The greedy method repeatedly chooses the test that covers the largest number of currently uncovered items.

### Submodular objective

A submodular objective has diminishing returns: the benefit of adding an item becomes smaller as more items have already been selected. Greedy set cover is useful because it provides a practical approximation for this type of problem.

### Test suite minimization

Test suite minimization removes redundant tests while retaining required coverage or mutant-kill behavior.

### Kill matrix

A kill matrix records which tests kill which mutants. It makes overlap and redundancy visible.

## 10. Report and engineering terms

### Literature review

A literature review compares earlier research and tools to identify what is already known and what gap the project addresses.

### Research gap

A research gap is an important problem that existing approaches do not fully solve.

### Requirements traceability

Requirements traceability links a requirement to its implementation, test, and evidence. It helps show that a claimed feature has been verified.

### Technical debt

Technical debt is the future maintenance cost created by a quick, incomplete, or overly complex implementation choice.

### Proof of concept

A proof of concept demonstrates that an approach can work. It may not yet include every production-level feature or operational guarantee.

### Reproducibility

Reproducibility means another person can repeat an experiment using the documented code, inputs, and configuration and obtain comparable results.

## 11. Short presentation answers

### Why is mutation testing needed if coverage is 100%?

“Coverage only proves that execution reached code. Mutation testing changes the code and checks whether the tests detect the changed behavior, so it measures test strength more directly.”

### Why use multiple agents?

“The workflow has different kinds of reasoning: code structure, stateful planning, test generation, criticism, execution, and minimization. Separate agents give each responsibility a clear boundary and make the process easier to inspect.”

### Why use a Blackboard?

“The Blackboard gives every specialist a shared, auditable state without forcing every agent to know the internal details of every other agent.”

### Why is sandboxing necessary?

“TestForge executes generated or mutated code. A subprocess sandbox limits the impact of failures and keeps generated execution separate from the main application.”

### Why minimize the test suite?

“A smaller suite is faster and easier to maintain. TestForge keeps tests that preserve mutant-kill coverage and removes tests that add no useful coverage.”

### What does a surviving mutant tell us?

“It is evidence that the current tests did not distinguish the original behavior from a specific injected fault. That points to a missing assertion or missing input case.”

### What is the main limitation to acknowledge?

“The quality of generated tests depends on the target code, available execution environment, model behavior, and the quality of the validation checks. The human approval gate remains important before repository writes.”

## 12. Terms worth memorizing first

If presentation time is limited, learn these first:

1. Mutation testing, mutant, killed mutant, surviving mutant, and mutation score.
2. AST, call graph, blast radius, and stateful call chain.
3. Multi-Agent System, Blackboard pattern, orchestrator, and FSM.
4. FastMCP, MCP, JSON-RPC, A2A, and Agent Card.
5. Sandbox, guardrail, human-in-the-loop, and repository write approval.
6. SQLite WAL, checkpoint, snapshot, and deterministic diff.
7. Greedy set cover, test-suite minimization, kill matrix, and ablation study.
8. Pass@1, telemetry, OpenTelemetry, trace, span, and latency.

