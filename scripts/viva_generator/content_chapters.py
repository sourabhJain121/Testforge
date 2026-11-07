"""
content_chapters.py - Comprehensive technical chapters 1 through 23 for TestForge Viva Book.
Each chapter is fully grounded in the verified source code, architecture, and empirical evidence.
"""

import docx
from docx.shared import Inches, Pt, RGBColor
from .styles import (
    add_h1, add_h2, add_h3, add_p, add_bullet, add_callout,
    add_code_block, add_table, COLOR_PRIMARY_NAVY, COLOR_SECONDARY_BLUE
)


def add_table_of_contents(doc: docx.Document):
    """Adds the structured table of contents."""
    add_h1(doc, "Table of Contents")
    add_p(doc, "This comprehensive viva examination and architectural reference manual is organized into thirty-one primary chapters covering the complete theory, implementation, empirical evaluation, and oral defense of TestForge.")

    toc_items = [
        ("Chapter 1: Cover Page & Academic Metadata", "Page 1"),
        ("Chapter 2: Table of Contents & Executive Summary", "Page 2"),
        ("Chapter 3: Project Overview & Core Philosophy", "Page 4"),
        ("Chapter 4: Problem Statement & Engineering Objectives", "Page 7"),
        ("Chapter 5: Technology Stack & Architectural Dependencies", "Page 10"),
        ("Chapter 6: Complete System Architecture (Layers, State & Invariants)", "Page 13"),
        ("Chapter 7: Detailed Component & Module Directory", "Page 18"),
        ("Chapter 8: AI Model & Multi-Agent Architecture (Google ADK vs CrewAI)", "Page 23"),
        ("Chapter 9: Agent-to-Agent (A2A) Protocol & Interoperability", "Page 28"),
        ("Chapter 10: Blackboard Architecture & Partitioned Shared Context", "Page 33"),
        ("Chapter 11: Model Context Protocol (MCP) Server & Tool Integration", "Page 38"),
        ("Chapter 12: AST Analysis & Intelligent Test Generation", "Page 43"),
        ("Chapter 13: Boundary-Value Analysis & Assertion Synthesis", "Page 48"),
        ("Chapter 14: Mutation-Testing Engine & Operator Taxonomy", "Page 53"),
        ("Chapter 15: Mutation-Verified Reflection & Refinement Loops", "Page 58"),
        ("Chapter 16: Sandbox Execution & Multi-Core Process Isolation", "Page 63"),
        ("Chapter 17: Callbacks, Observability & Cryptographic Provenance", "Page 68"),
        ("Chapter 18: Persistence, SQLite WAL Storage & Checkpoint Recovery", "Page 73"),
        ("Chapter 19: FastAPI Backend Architecture & Vanilla JS Web Cockpit", "Page 78"),
        ("Chapter 20: Security Defenses, Prompt Guardrails & Deployment", "Page 83"),
        ("Chapter 21: Complete End-to-End Execution Walkthrough", "Page 88"),
        ("Chapter 22: Benchmarking Methodology & Statistical Modeling", "Page 93"),
        ("Chapter 23: Experimental Evaluation Results & Empirical Analysis", "Page 98"),
        ("Chapter 24: Comprehensive Answers to All 114 Viva Questions", "Page 104"),
        ("  • Part 1: AI Models and Agent Architecture (Q1–Q10)", "Page 105"),
        ("  • Part 2: A2A Communication and Interoperability (Q11–Q24)", "Page 114"),
        ("  • Part 3: Blackboard and Shared Context (Q25–Q36)", "Page 126"),
        ("  • Part 4: MCP Integration (Q37–Q46)", "Page 137"),
        ("  • Part 5: Intelligent Test Generation (Q47–Q59)", "Page 146"),
        ("  • Part 6: Mutation Testing and Reflection (Q60–Q75)", "Page 158"),
        ("  • Part 7: Callbacks, Logging, and Observability (Q76–Q85)", "Page 173"),
        ("  • Part 8: Persistence and Checkpoints (Q86–Q93)", "Page 182"),
        ("  • Part 9: API, Frontend, and Deployment (Q94–Q103)", "Page 190"),
        ("  • Part 10: Benchmarking and Evidence (Q104–Q114)", "Page 199"),
        ("Chapter 25: Additional High-Probability Examiner Defense Questions (Q115–Q135)", "Page 210"),
        ("Chapter 26: Practical Code Walkthrough & Source Code Reference", "Page 230"),
        ("Chapter 27: Academic Defense Strategy & Tricky Examiner Challenges", "Page 242"),
        ("Chapter 28: Acknowledged Limitations & Future Production Roadmap", "Page 249"),
        ("Chapter 29: Quick Revision Cheat Sheet & Essential Formulas", "Page 254"),
        ("Chapter 30: Glossary of Technical Terms & Standard Abbreviations", "Page 259"),
        ("Chapter 31: Evidence Verification Index & Trace Directory", "Page 264"),
    ]

    add_table(doc, ["Document Chapter / Section Title", "Reference Page"], toc_items, [Inches(5.0), Inches(1.5)])
    doc.add_page_break()


def add_chapter_project_overview(doc: docx.Document):
    """Chapter 3: Project Overview & Core Philosophy."""
    add_h1(doc, "Chapter 3: Project Overview & Core Philosophy")

    add_h2(doc, "3.1 Project Definition")
    add_p(doc, "TestForge is an autonomous, multi-agent software test generation and hardening platform designed to bridge the fundamental gap between structural code reachability (statement/branch coverage) and behavioral fault detection (mutation score). Rather than relying on simple stochastic LLM prompts that produce vacuous assertions or unverified tests, TestForge combines static Abstract Syntax Tree (AST) analysis, dynamic reference execution, mutation testing, sandboxed execution, and an adversarial multi-agent reflection loop.")

    add_h2(doc, "3.2 The Core Dilemma: Coverage vs. Mutation Score")
    add_p(doc, "In modern software engineering, test suites are frequently evaluated by line or statement coverage: the percentage of executable code statements reached by tests. However, high coverage does not guarantee test quality. A test suite can achieve 100% line coverage with zero assertions by simply executing the functions without checking their return values. This phenomenon is known as the 'Assertion Blindness Problem'.")

    add_p(doc, "Consider the following illustrative example:")
    add_code_block(doc, 
"""# Target Source Code
def calculate_tax(income: float) -> float:
    if income > 50000.0:
        return income * 0.20  # Mutator inverts to: income / 0.20 or income * 0.10
    return 0.0

# Flaky / Vacuous Test Suite (100% Line Coverage, 0% Mutation Kill)
def test_calculate_tax_coverage_only():
    calculate_tax(60000.0)  # Executes line 3!
    calculate_tax(40000.0)  # Executes line 4!
    # PASSES! Line coverage is 100%, but no assertion exists!
    # If the logic is broken, the test suite never notices!

# Hardened Test Suite (100% Line Coverage, 100% Mutation Kill)
def test_calculate_tax_hardened():
    assert calculate_tax(60000.0) == 12000.0  # Fails if operator changes to / or rate changes!
    assert calculate_tax(50000.0) == 0.0      # Boundary check! Fails if > changes to >=!
    assert calculate_tax(50000.01) == 10000.002
""")

    add_p(doc, "Mutation testing injects artificial, single-token syntactic defects (mutants) into the program's AST—such as swapping '+' for '-', '>' for '>=', or 'True' for 'False'. A test suite kills a mutant if at least one test fails when executed against the mutated code. If all tests pass despite the bug, the mutant survives, exposing an assertion weakness.")

    add_callout(doc, 
        "Key Concept: Code Coverage measures whether code was executed (Reachability). "
        "Mutation Score measures whether the test suite can detect faults in that code (Assertion Effectiveness). "
        "TestForge's mission is to autonomously harden tests until the mutation score matches or exceeds industry standards.",
        title="Theoretical Foundation: Reachability vs. Verification",
        alert_type="note"
    )

    add_h2(doc, "3.3 Autonomous Multi-Agent Philosophy")
    add_p(doc, "Generating tests that kill mutants is computationally and logically difficult for a single monolithic prompt because single agents suffer from confirmation bias: an LLM generating code tends to rationalize its own assumptions rather than discovering edge-case loopholes. TestForge solves this by employing an adversarial separation of concerns:")
    add_bullet(doc, "Official Google ADK Test Generator Agent: Generates boundary-aware tests and edge-case inputs.", "Generator:")
    add_bullet(doc, "Official CrewAI Adversarial Critic Agent: Analyzes surviving mutant AST diffs to identify untested logic.", "Critic:")
    add_bullet(doc, "Shared Thread-Safe Blackboard: Decouples communication into partitioned data spaces.", "Blackboard:")
    add_bullet(doc, "Parallel Process Sandbox Runner: Executes tests against mutants under strict CPU/memory limits.", "Sandbox:")


def add_chapter_problem_statement(doc: docx.Document):
    """Chapter 4: Problem Statement & Engineering Objectives."""
    add_h1(doc, "Chapter 4: Problem Statement & Engineering Objectives")

    add_h2(doc, "4.1 Formal Problem Statement")
    add_p(doc, "Given an untrusted target Python source module S containing a set of callables C = {c_1, c_2, ..., c_n}, conventional automated test generators either produce weak assertions that fail to detect realistic programmer errors, or produce un-executable candidate tests that hallucinate non-existent APIs, cause infinite loops, or violate runtime type constraints.")

    add_p(doc, "The challenge is to autonomously synthesize a hardened test suite T* such that:")
    add_bullet(doc, "T* compiles and executes cleanly against clean source S with zero syntax errors, zero import errors, and 100% test pass rate.", "1. Syntactic & Semantic Correctness:")
    add_bullet(doc, "T* maximizes the mutation score MS(T*, M) across a suite of AST mutants M = {m_1, m_2, ..., m_k}.", "2. Fault Sensitivity:")
    add_bullet(doc, "T* identifies and accounts for mathematically equivalent mutants M_equiv without human intervention.", "3. Equivalent Mutant Triage:")
    add_bullet(doc, "The system isolates untrusted source execution and prevents infinite loops, recursive bombs, and prompt injections.", "4. Execution Safety:")

    add_h2(doc, "4.2 Measurable Academic Objectives")
    add_p(doc, "TestForge defined five quantitative evaluation criteria for project completion:")
    add_table(doc, 
        ["Criterion", "Target Metric", "Verified Achieved Metric", "Status"],
        [
            ["1. Unit Test Suite", "500+ passing tests", "598 passing tests, 0 failed", "Exceeded"],
            ["2. Discount Benchmark Mutation Score", ">= 80% raw mutation score", "89.47% raw (94.44% adjusted)", "Exceeded"],
            ["3. Enterprise Logistics Mutation Score", ">= 60% raw mutation score", "68.22% raw (75.21% adjusted)", "Exceeded"],
            ["4. Core Engine Code Coverage", ">= 80% engine coverage", "81.33% coverage verified", "Achieved"],
            ["5. Security & Isolation Fences", "Zero prompt leakage / AST jailbreaks", "120/120 security trials passed", "Achieved"],
        ],
        [Inches(2.2), Inches(1.5), Inches(1.8), Inches(1.0)]
    )


def add_chapter_technology_stack(doc: docx.Document):
    """Chapter 5: Technology Stack & Architectural Dependencies."""
    add_h1(doc, "Chapter 5: Technology Stack & Architectural Dependencies")
    add_p(doc, "TestForge is constructed using an enterprise-grade, asynchronous Python architecture running natively on Apple Silicon ARM64 hardware.")

    stack_data = [
        ["FastAPI 0.115+", "ASGI Web Framework", "Provides asynchronous REST endpoints, WebSocket streaming, and Pydantic validation.", "server.py"],
        ["Uvicorn 0.32+", "ASGI Web Server", "High-performance event loop hosting HTTP/1.1 and WebSockets on port 8000.", "start_testforge.sh"],
        ["Google ADK", "Agent Framework", "Orchestrates the TestGeneratorAgent with boundary analysis tools.", "testforge/adk_generator.py"],
        ["CrewAI 0.86+", "Agent Framework", "Orchestrates the AdversarialCriticAgent with mutant survival diagnosis.", "testforge/crew_critic.py"],
        ["Model Context Protocol (MCP)", "Tool Standard", "Provides structured tool discovery and execution for filesystem and git operations.", "testforge/mcp_server.py"],
        ["Python `ast` & `astor`", "Syntax Engine", "Parses source code into trees, inspects comparison nodes, and transforms mutants.", "testforge/mutator.py"],
        ["pytest 9.1+", "Test Runner", "Executes synthesized test suites in sandboxed subprocess environments.", "testforge/sandbox.py"],
        ["coverage.py 7.6+", "Coverage Engine", "Measures statement and branch execution reachability.", "testforge/coverage.py"],
        ["SQLite3 (WAL Mode)", "State Persistence", "Provides ACID persistence for Blackboard checkpoints and resumes.", "testforge/persistence.py"],
        ["HTML5 / CSS3 / Vanilla JS", "Frontend Cockpit", "Responsive SPA with live wiretap, blackboard partition strip, and charts.", "frontend/app.js"],
    ]

    add_table(doc, ["Technology", "Role / Layer", "Technical Justification", "Source Reference"], stack_data, [Inches(1.5), Inches(1.3), Inches(2.3), Inches(1.4)])


def add_chapter_complete_architecture(doc: docx.Document):
    """Chapter 6: Complete System Architecture."""
    add_h1(doc, "Chapter 6: Complete System Architecture")

    add_h2(doc, "6.1 Five-Tier Architectural Topology")
    add_p(doc, "TestForge is structured into five distinct, decoupled architectural tiers:")
    add_bullet(doc, "Browser-based Single Page Application (SPA) interacting via REST API and WebSockets.", "Tier 1: Presentation Layer:")
    add_bullet(doc, "FastAPI application managing job queues, background tasks, and MCP servers.", "Tier 2: Orchestration & Ingestion Layer:")
    add_bullet(doc, "Google ADK generator and CrewAI critic coordinating over A2A and Blackboard.", "Tier 3: Multi-Agent Intelligence Layer:")
    add_bullet(doc, "Parallel sandbox runner executing pytest against AST mutants under strict limits.", "Tier 4: Execution & Verification Sandbox:")
    add_bullet(doc, "SQLite database and JSONL wiretap trace ensuring full auditability and state recovery.", "Tier 5: Persistence & Observability Layer:")

    add_h2(doc, "6.2 Architectural Invariants")
    add_p(doc, "To guarantee stability and academic reproducibility, TestForge enforces five non-negotiable architectural invariants:")
    add_bullet(doc, "Candidate test suites generated by LLMs or AST synthesizers are strictly quarantined in memory. They are never written to disk as validated tests until they execute against the clean source code with a 100% pass rate in the sandbox.", "Invariant 1: Quarantine Before Validation:")
    add_bullet(doc, "Every write to any partition of the Blackboard increments the revision counter atomically under a re-entrant lock (RLock).", "Invariant 2: Atomic Blackboard Revisions:")
    add_bullet(doc, "Generated test suites are hashed via SHA-256 alongside the exact target code hash, mutation seeds, and agent IDs to guarantee cryptographic provenance.", "Invariant 3: Suite Cryptographic Provenance:")
    add_bullet(doc, "Every background thread checks `cancel_event.is_set()` before dispatching sandbox runs or agent calls. Subprocesses are forcibly terminated on cancellation.", "Invariant 4: Cooperative Cancellation:")
    add_bullet(doc, "Offline deterministic AST synthesis explicitly logs zero actual LLM tokens. Character-heuristic estimates are segregated and never conflated with billable API usage.", "Invariant 5: Strict Token Accounting Segregation:")


def add_chapter_blackboard(doc: docx.Document):
    """Chapter 10: Blackboard Architecture."""
    add_h1(doc, "Chapter 10: Blackboard Architecture & Partitioned Shared Context")

    add_h2(doc, "10.1 The Blackboard Pattern")
    add_p(doc, "The Blackboard architectural pattern is a classical AI coordination strategy where diverse, autonomous knowledge sources (agents) collaborate by reading from and writing to a shared problem-solving space. Unlike direct message passing where agents must maintain point-to-point connections, the Blackboard decouples agents in time and space: the Generator agent writes tests without knowing when the Sandbox will execute them, and the Mutator writes mutants without knowing how the Critic will diagnose survivors.")

    add_h2(doc, "10.2 Partitioned Spaces in `testforge/blackboard.py`")
    add_p(doc, "The TestForge Blackboard is partitioned into five distinct domain spaces, each implemented as an explicit Pydantic model:")

    spaces = [
        ["TargetSpace", "Holds target module path, raw source code, AST function signatures, and static blast radius.", "testforge/blackboard.py:TargetSpace"],
        ["SuiteSpace", "Stores current test code, baseline test code, hardened test code, and SHA-256 provenance hashes.", "testforge/blackboard.py:SuiteSpace"],
        ["MutantSpace", "Records generated mutants, AST operator diffs, killed mutants, survived mutants, and mutant statuses.", "testforge/blackboard.py:MutantSpace"],
        ["CriticSpace", "Stores adversarial critique text, targeting directives, identified boundary gaps, and iteration count.", "testforge/blackboard.py:CriticSpace"],
        ["MetricsSpace", "Contains statement coverage, raw mutation score, equivalent-adjusted score, and wall-clock execution time.", "testforge/blackboard.py:MetricsSpace"],
    ]
    add_table(doc, ["Blackboard Partition", "Stored Data & Responsibility", "Source Implementation"], spaces, [Inches(1.8), Inches(3.2), Inches(1.5)])

    add_h2(doc, "10.3 Thread Safety via `threading.RLock()`")
    add_p(doc, "Because FastAPI handles concurrent HTTP requests and background worker threads simultaneously, state corruption is prevented using a re-entrant lock (`threading.RLock`). Every mutation method (`update_target`, `update_suite`, `record_mutant_run`, `add_critic_feedback`) acquires this lock before modifying state and incrementing `self.revision`.")


def add_chapter_mcp(doc: docx.Document):
    """Chapter 11: Model Context Protocol (MCP)."""
    add_h1(doc, "Chapter 11: Model Context Protocol (MCP) Server & Tool Integration")

    add_h2(doc, "11.1 What is MCP?")
    add_p(doc, "The Model Context Protocol (MCP) is an open standard created by Anthropic that standardizes how AI applications provide context and tools to foundation models. Instead of writing proprietary, one-off tool wrappers for every LLM SDK, MCP provides a uniform JSON-RPC protocol over standard I/O (stdio) or HTTP/SSE.")

    add_h2(doc, "11.2 MCP Servers in TestForge (`testforge/mcp_server.py`)")
    add_p(doc, "TestForge implements two official FastMCP servers running within the application:")
    add_bullet(doc, "Exposes sandboxed local file operations. Registered tools: `read_text_file`, `list_directory`, `get_file_info`.", "1. Filesystem MCP Server:")
    add_bullet(doc, "Exposes read-only GitHub repository ingestion. Registered tools: `get_repository_info`, `get_file_contents`, `search_repositories`.", "2. GitHub MCP Server:")

    add_h2(doc, "11.3 Security: Path Traversal Prevention")
    add_p(doc, "All filesystem MCP tools execute `_is_path_safe(requested_path, allowed_dir)` before performing file I/O. This function resolves symlinks via `os.path.realpath()` and verifies that the canonical path starts with the allowed root directory, preventing directory traversal attacks (`../../etc/passwd`).")


def add_chapter_ast_and_generation(doc: docx.Document):
    """Chapter 12: AST Analysis & Intelligent Test Generation."""
    add_h1(doc, "Chapter 12: AST Analysis & Intelligent Test Generation")

    add_h2(doc, "12.1 Abstract Syntax Tree (AST) Extraction")
    add_p(doc, "TestForge parses Python source code into an Abstract Syntax Tree using Python's native `ast.parse()`. In [`testforge/intelligent_generator.py`](file:///Users/sourabh/TestForge/testforge/intelligent_generator.py), the `ASTCallableAnalyzer` traverses the tree using an `ast.NodeVisitor` to catalog all callable functions, methods, class hierarchies, and comparison boundaries.")

    add_h2(doc, "12.2 Ground Truth Establishment via `ReferenceExecutor`")
    add_p(doc, "A critical innovation in TestForge is `ReferenceExecutor`. When generating unit tests, LLMs often hallucinate incorrect expected return values (e.g., claiming 15% discount on $100 is $80). `ReferenceExecutor` dynamically imports the clean target module in an isolated in-memory environment, executes candidate inputs against the real function, and records the ground-truth return values and types.")

    add_callout(doc,
        "Ground Truth Invariant: TestForge never guesses or hallucinates function return values. "
        "ReferenceExecutor executes the clean code with nominal arguments to determine the true return value, "
        "guaranteeing that generated tests initially pass 100% on clean code.",
        title="Zero-Hallucination Assertion Principle",
        alert_type="note"
    )


def add_chapter_mutation_testing(doc: docx.Document):
    """Chapter 14: Mutation-Testing Engine & Operator Taxonomy."""
    add_h1(doc, "Chapter 14: Mutation-Testing Engine & Operator Taxonomy")

    add_h2(doc, "14.1 Nine AST Mutation Operators in `testforge/mutator.py`")
    add_p(doc, "TestForge implements nine fine-grained AST mutation operators via `MutationTransformer(ast.NodeTransformer)`:")

    operators = [
        ["1. AOR (Arithmetic Operator Replacement)", "Swaps arithmetic operators (+ to -, * to /, % to *)", "a + b  -->  a - b"],
        ["2. ROR (Relational Operator Replacement)", "Swaps comparison operators (> to >=, == to !=, < to <=)", "x > 10  -->  x >= 10"],
        ["3. COR (Conditional Operator Replacement)", "Swaps logical connectors (and to or, or to and)", "a and b  -->  a or b"],
        ["4. CRP (Constant Replacement)", "Perturbs numeric literals (0 to 1, 1 to 0, 10 to 11)", "100  -->  101"],
        ["5. LCR (Logical Connector Replacement)", "Inverts boolean truth values and flags", "is_vip = True  -->  False"],
        ["6. SVR (Scalar Variable Replacement)", "Swaps compatible variable names within scope", "return a  -->  return b"],
        ["7. UOI (Unary Operator Insertion)", "Inserts or removes negation operators", "return x  -->  return -x"],
        ["8. BCR (Break/Continue Replacement)", "Swaps loop control statements (break to continue)", "break  -->  continue"],
        ["9. EXS (Exception Swapping)", "Replaces raised exception types", "raise ValueError  -->  TypeError"],
    ]
    add_table(doc, ["Operator Category", "Mutation Description", "Code Transformation Example"], operators, [Inches(2.2), Inches(2.5), Inches(1.8)])

    add_h2(doc, "14.2 Mutant Outcome Classification")
    add_p(doc, "When a mutant is executed against the test suite in the sandbox runner, it is classified into one of four states:")
    add_bullet(doc, "At least one test failed, raised an unexpected exception, or asserted false. The synthetic bug was successfully caught.", "1. Killed Mutant:")
    add_bullet(doc, "All tests passed. The test suite failed to detect the injected bug, exposing a quality gap.", "2. Survived Mutant:")
    add_bullet(doc, "A mutant that produces identical observable behavior for all possible valid inputs. Cannot be killed by any test.", "3. Equivalent Mutant:")
    add_bullet(doc, "The mutant is in dead code or an unreached callable that the test suite never executed.", "4. Unreached Mutant:")

    add_h2(doc, "14.3 Mathematical Mutation Formulas")
    add_p(doc, "TestForge computes both Raw and Equivalent-Adjusted Mutation Scores:")
    add_code_block(doc,
"""Raw Mutation Score (RMS):
RMS = (Killed Mutants / Total Generated Mutants) * 100%

Equivalent-Adjusted Mutation Score (AMS):
AMS = (Killed Mutants / (Total Generated Mutants - Equivalent Mutants)) * 100%
""")


def add_chapter_reflection_loop(doc: docx.Document):
    """Chapter 15: Reflection and Refinement Loop."""
    add_h1(doc, "Chapter 15: Mutation-Verified Reflection & Refinement Loops")

    add_h2(doc, "15.1 The Closed-Loop Iteration Cycle")
    add_p(doc, "The multi-agent reflection loop coordinates four automated phases per hardening cycle:")
    add_bullet(doc, "Google ADK generator analyzes AST callable signatures and synthesizes an initial boundary test suite.", "Phase 1: Initial Synthesis:")
    add_bullet(doc, "Parallel sandbox compiles the AST, injects mutants, and evaluates the suite against all mutants.", "Phase 2: Mutation Evaluation:")
    add_bullet(doc, "CrewAI Adversarial Critic inspects the surviving mutant AST diffs and generates targeted critique directives.", "Phase 3: Adversarial Diagnosis:")
    add_bullet(doc, "ADK generator ingests the critic directive and synthesizes specialized boundary/edge tests to kill surviving mutants.", "Phase 4: Targeted Refinement:")

    add_h2(doc, "15.2 Convergence Guards & Stopping Criteria")
    add_p(doc, "The loop terminates automatically under any of four conditions:")
    add_bullet(doc, "Mutation score reaches 100% (or target score e.g. 85%).", "1. Target Threshold Achieved:")
    add_bullet(doc, "Maximum configured hardening cycles reached (default: 3 iterations).", "2. Max Iterations Exceeded:")
    add_bullet(doc, "Mutation score did not improve over two consecutive cycles.", "3. Convergence Plateaus:")
    add_bullet(doc, "User clicks 'Stop Hardening' via frontend WebSocket cancel button.", "4. Cooperative Cancellation:")


def add_chapter_benchmarking_and_results(doc: docx.Document):
    """Chapter 22 & 23: Benchmarking Methodology and Results."""
    add_h1(doc, "Chapter 22 & 23: Benchmarking Methodology & Experimental Results")

    add_h2(doc, "22.1 Verified Empirical Benchmarks")
    add_p(doc, "TestForge was evaluated against two benchmark programs representing different complexity profiles:")

    bench_results = [
        ["samples/discount.py", "19", "1", "5.26%", "5.56%", "17", "89.47%", "94.44%", "1"],
        ["samples/uploaded_logistics_engine.py", "258", "8", "3.10%", "3.42%", "176", "68.22%", "75.21%", "24"],
    ]
    add_table(doc, 
        ["Target Module", "Total Mutants", "Baseline Killed", "Baseline Raw", "Baseline Adj", "Hardened Killed", "Hardened Raw", "Hardened Adj", "Equiv Mutants"],
        bench_results,
        [Inches(1.8), Inches(0.6), Inches(0.6), Inches(0.6), Inches(0.6), Inches(0.6), Inches(0.6), Inches(0.6), Inches(0.5)]
    )

    add_h2(doc, "23.1 Analysis of Results")
    add_p(doc, "On `discount.py`, TestForge achieved an **89.47% raw mutation score (94.44% adjusted)**, representing a **17x improvement** over the initial baseline. The 1 surviving mutant represents a quantity boundary threshold condition (`quantity >= 5` to `quantity > 5`) that evaluates identically under volume step tiers.")

    add_p(doc, "On enterprise `uploaded_logistics_engine.py` (258 mutants across 10 complex multi-package routing callables), TestForge raised the mutation score from **3.10% to 68.22% raw (75.21% adjusted)**, an increase of **+65.12% (22x improvement)**. In the baseline, 9 out of 10 callables were unreached (80.6% unreached callable gap). Hardened test generation achieved **100% callable reachability**.")

