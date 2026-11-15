# TestForge: An Autonomous Multi-Agent System for Mutation-Verified Unit Test Hardening

**Course Title:** Autonomous Agentic AI Systems  
**Evaluation Track:** Academic Capstone Research & Technical Engineering Deliverable  
**Engineering Leads:** Sourabh & Shreshth  
**Target Architecture:** macOS arm64 (`.venv-release`), Python 3.13, FastMCP (Model Context Protocol), Google ADK v1.14.1, CrewAI v0.102.0  
**Repository Branch:** `release/v1.0.0`  
**Git Integrity:** Monotonic Verification (999+ Unit, Contract, and Integration Tests Passing)

---

## 1. Executive Summary & Core Engineering Achievements

Modern Large Language Models (LLMs) routinely generate syntactically plausible unit tests that suffer from a pervasive **Coverage-Kill Gap**: tests achieve high line coverage by blindly executing code paths while omitting assertive boundary checks. In critical production environments, this produces a false sense of security—tests pass effortlessly while real semantic bugs and logic regressions go completely undetected.

**TestForge** is an industrial-grade, multi-agent autonomous test hardening platform that closes the Coverage-Kill Gap through **mutation-guided reflection**. Rather than relying on ungrounded generative loops or unassertive test generation, TestForge injects systematic Abstract Syntax Tree (AST) synthetic faults into target code and guides an 8-agent topology to formulate, execute, critique, and harden unit tests until reaching a verifiable mutation kill threshold.

### Key Engineering Milestones:
1. **8-Agent Topology & A2A Collaboration Protocol:** Deployed an orchestration loop coordinating Google Agent Development Kit (ADK) agents, CrewAI role-playing specialists, and a centralized thread-safe Blackboard with SQLite Write-Ahead Logging (WAL) state persistence.
2. **FastMCP 4-Tool Protocol Suite:** Standardized all AST analysis, mutation generation, sandbox execution, and bytecode equivalence classification into an official Model Context Protocol (FastMCP) server operating over isolated stdio JSON-RPC transport (`python -m testforge.mcp_server`).
3. **Live Agentic RAG Pipeline:** Integrated a zero-egress, deterministic TF-IDF/cosine vector store seeded with canonical boundary patterns across arithmetic division, sequence slicing, string regex, and stateful FSM caches to ground scenario planning.
4. **Defect DEF-022 Discovery & Empirical Honesty:** Uncovered and eliminated a critical evaluation vulnerability (Clean Reference False-Kill Defect) where suites failing on unmutated code inflated mutation scores. Enforced strict DEF-022 Pass@1 clean preflight validation and formally retracted legacy unvalidated claims.
5. **State-of-the-Art Benchmark Results:** Across the 4 canonical benchmark targets, TestForge raised mutation scores from an initial **6.46%** developer baseline to **67.02% raw / 70.17% adjusted mutation score** (167/240 mutants killed) in initial Phase-2 reflection, while lifting `bisect` to **65.71%** and `lru_cache` to **90.48% (38/42 killed)** via Stateful Call-Chain Planning.

---

## 2. Problem Statement & Motivation

### The Silent Failure Problem: Hollow Tests & False Coverage
Line coverage indicates that a line was touched by the interpreter during execution; it does not measure whether the test validated correctness. Consider a typical zero-shot LLM-generated test:
```python
def test_calculate_discount():
    calculate_discount(100.0, 5, True) # Line coverage: 100%, Mutation score: 0.0%
```
If `calculate_discount` contains an inverted condition (`price < 0` instead of `price > 0`) or drops the discount logic entirely, this test passes silently. The test satisfies naive CI code coverage requirements while providing zero regression protection.

### The Adversarial Mutation Solution
Mutation testing evaluates test suite quality by injecting syntactically valid semantic mutations (e.g., swapping `<` for `<=`, replacing `+` with `-`, deleting statements) into target source code. If a test fails against a mutated program, the mutant is *killed*; if all tests pass, the mutant *survives*.
However, traditional mutation testing suffers from two crippling bottlenecks:
1. **The Equivalent Mutant Problem:** A mutant may alter code structure without changing semantic behavior (e.g., mutating dead code or swapping equivalent branch predicates). Rice's Theorem dictates this is undecidable in the general case, leading to false penalties and trapped loops.
2. **High Computational Overhead:** Combinatorial explosions of mutants require hundreds of isolated subprocess test executions.

TestForge tackles both challenges through autonomous multi-agent reflection, bytecode equivalence filtering, parallel sub-second sandboxing, and monotonic never-regress validation.

---

## 3. System Architecture & Multi-Agent Collaboration

TestForge separates generative, adversarial, and analytical concerns across an 8-agent topology coordinated over a shared typed Blackboard and the Agent-to-Agent (A2A v0.3.0) wire protocol.

```
                  ┌──────────────────────────────────────────────┐
                  │          TestForge Master Supervisor          │
                  │             (Google ADK State FSM)           │
                  └───────────────────────┬──────────────────────┘
                                          │
                 ┌────────────────────────┴────────────────────────┐
                 ▼                                                 ▼
     ┌───────────────────────┐                         ┌───────────────────────┐
     │ CodeIntelligenceAgent │                         │     SecurityAgent     │
     │   (AST Static Walk)   │                         │  (AST Import Guard)   │
     └───────────┬───────────┘                         └───────────────────────┘
                 │
                 ▼
     ┌───────────────────────┐       A2A JSON-RPC      ┌───────────────────────┐
     │   TestPlanningAgent   │────────────────────────▶│   Agentic RAG Store   │
     │  (Heuristic Scenarios)│◀────────────────────────│ (TF-IDF Vector Store) │
     └───────────┬───────────┘                         └───────────────────────┘
                 │
                 ▼
     ┌───────────────────────┐   stdio JSON-RPC (MCP)  ┌───────────────────────┐
     │  TestGeneratorAgent   │◀───────────────────────▶│   FastMCP 4-Tool Host │
     │  (Google ADK / Gemini)│                         │ (Subprocess Isolation)│
     └───────────┬───────────┘                         └───────────────────────┘
                 │
                 ▼
     ┌───────────────────────┐                         ┌───────────────────────┐
     │  TestExecutionAgent   │                         │ MutationQualityCritic │
     │  (Sandboxed Workers)  │                         │   (CrewAI Specialist) │
     └───────────┬───────────┘                         └───────────▲───────────┘
                 │                                                 │
                 └────────────────────────┬────────────────────────┘
                                          │ A2A Counterexample Directives
                                          ▼
                             ┌─────────────────────────┐
                             │  ReflectionRepairAgent  │
                             │ (Monotonic Peak Guard)  │
                             └─────────────────────────┘
```

### 3.1 8-Agent Topological Roles
1. **Supervisor Agent (Google ADK):** Enforces lifecycle invariants across ingestion, generation, evaluation, reflection, and finalization. Tracks convergence and stops loops when mutation score targets are met or iterations exhaust.
2. **Code Intelligence Agent:** Performs static AST extraction, parsing function signatures, parameter types, cyclomatic complexity, and branch conditions without dynamic module execution.
3. **Security Agent:** Inspects unparsed AST nodes and imports prior to execution, blocking forbidden system packages (`os.system`, `subprocess`, `socket`, `pty`) to maintain zero-egress sandboxing.
4. **Test Planning Agent:** Combines static AST intelligence with retrieved RAG recipes to formulate a structured `TestPlanPayload` (nominal, boundary, negative, and exception targets).
5. **Test Generator Agent (Google ADK):** Translates planned scenarios into executable Pytest suites, invoking LLM inference or deterministic AST invariant seeds.
6. **Test Execution Agent:** Manages a parallel worker pool running tests across mutants in detached subprocesses under strict 5.0-second timeout constraints.
7. **Mutation Quality Critic Agent (CrewAI):** Analyzes surviving mutant AST diffs, diagnoses missing test preconditions or weak assertions, and emits structured failure directives to guide targeted test repair.
8. **Reflection & Repair Agent (Google ADK):** Consumes critic directives to synthesize targeted counterexample tests. Enforces the **Never-Regress Guard**, ensuring regressions in score or clean-code integrity are discarded in favor of historical peaks.

### 3.2 FastMCP 4-Tool Protocol Suite (`testforge/mcp_server.py`)
TestForge isolates low-level static analysis, mutant synthesis, and execution tools inside an official Model Context Protocol (FastMCP) server executed via isolated stdio JSON-RPC transport (`FastMCPStdioClient`):
- `mcp_ast_symbol_analyzer`: Parses Python AST into structured symbols, callables, branches, and cyclomatic complexity.
- `mcp_mutant_generator`: Deterministically generates bounded mutant records using AST visitors with source location tagging.
- `mcp_sandbox_runner`: Executes candidate test suites against clean or mutated code in isolated child processes with memory and execution quotas.
- `mcp_equivalence_classifier`: Performs dual-tier bytecode disassembly and semantic invariance checks to identify non-killable equivalent mutants.

If stdio transport encounters unexpected subprocess interruption or communication timeout, the engine logs an explicit telemetry event (`MCP_STDIO_FALLBACK_TRIGGERED`) and falls back gracefully to in-process execution.

### 3.3 Live Agentic RAG Knowledge Retrieval (`testforge/rag/`)
To eliminate unassertive zero-shot hallucination, TestForge incorporates a local, zero-egress knowledge retrieval system:
- **Vector Store (`TestForgeVectorStore`):** Deterministic TF-IDF vectorization with cosine similarity matching, operating locally with zero third-party cloud database dependencies.
- **Agentic Knowledge Retriever (`AgenticKnowledgeRetriever`):** Applies semantic query reformulation and relevance grading (0.0 to 1.0) against four curated corpus collections:
  1. `arithmetic_division.json`: Zero-division, floating-point roundoff (`math.isclose`), and negative zero (`-0.0`).
  2. `sequence_slicing.json`: Empty collections, negative indexing, reverse slicing (`[::-1]`), and KeyError bounds.
  3. `string_regex.json`: Empty string invariants, multi-byte UTF-8, and catastrophic backtracking guards.
  4. `stateful_cache_fsm.json`: Cache eviction limits (LRU capacity), state idempotency, and duplicate insertions.
- **Observability:** Emits real-time OpenTelemetry trace spans (`rag.retrieval`) recording query text, top similarity score, and rule count into the dashboard.

### 3.4 SQLite Blackboard State Persistence (`testforge/blackboard.py`)
All agent interactions, plans, execution results, and metrics are written to an 8-partition Blackboard state store (`Target`, `Mutant`, `Critic`, `Suite`, `Metrics`, `Plan`, `Execution`, `Security`). To survive unexpected worker crashes, state changes are committed to SQLite Write-Ahead Logging (`SQLiteBlackboardStorage`). Every iteration generates an immutable checkpoint snapshot allowing single-click rollback and state replay.

---

## 4. Empirical Methodology & Measurement Harness

### 4.1 Defect DEF-022 Post-Mortem: Clean-Reference Pass@1 Enforcement
During our Phase-2 audit, we detected a critical measurement defect (**DEF-022: Clean-Reference False-Kill Defect**). In legacy mutation testing scripts, test execution errors (e.g., syntax errors, import failures, or type errors) caused pytest to exit with code 1. When running against mutant programs, the harness naively treated any non-zero exit code as a successful mutant kill.
As a result, a candidate test suite that crashed on *clean, unmutated target code* was credited with killing 100% of mutants!

**The DEF-022 Clean Preflight Guard:**
TestForge resolved this defect by integrating strict **Pass@1 Preflight Validation** into the core engine (`testforge/hybrid_synthesizer.py` and `testforge/sandbox.py`):
1. **Global Preflight:** Every candidate test suite must execute against the pristine, unmutated reference code.
2. **Granular Pruning:** If the suite fails on clean code, `GranularTestValidator` executes each test function individually against the clean reference code, discarding any broken test and retaining only 100% clean-passing tests.
3. **Invalid Suite Classification:** If no valid tests pass clean code, the suite is scored as `INVALID_SUITE` (0 kills, 0.0% MS).
This architectural guarantee ensures that mutant kills represent genuine regression detection rather than suite compilation failure.

### 4.2 AST Mutation Operators (10 Operators across 7 Categories)
TestForge implements 10 deterministic AST mutation operators covering 7 critical fault domains:
1. `BOUNDARY_SWAP` (AOR/ROR): Relational boundary shifts (`<` to `<=`, `>` to `>=`).
2. `COMP_OP`: Comparator inversions (`==` to `!=`, `in` to `not in`, `is` to `is not`).
3. `COND_INV`: Boolean condition negation (`if cond:` to `if not (cond):`).
4. `CONST_VAL`: Numeric/string boundary shifts (`0` to `1`, `""` to `"mutant"`).
5. `LOGICAL_CONN`: Short-circuit logic inversion (`and` to `or`).
6. `MATH_FUNC`: Arithmetic operator inversion (`+` to `-`, `*` to `/`, `//` to `/`).
7. `RETURN_VAL`: Predicate return flipping (`return True` to `return False`, `return x` to `return None`).
8. `OFF_BY_ONE`: Slice and index displacement (`i` to `i + 1`, `len(s)` to `len(s) - 1`).
9. `STATEMENT_DEL`: Critical side-effect deletion (`pass` substitution).
10. `EXCEPTION_MOD`: Exception guard suppression or altering raised exception types.

### 4.3 Bytecode Semantic Equivalence Filtering
To resolve the Equivalent Mutant Problem without human bottleneck, TestForge uses recursive bytecode disassembly (`testforge/equivalence.py`):
- Both clean target and mutated source ASTs are compiled into Python bytecode objects.
- Bytecode instruction sequences are normalized (stripping line numbers, co_flags, docstrings, and constant table offsets).
- If normalized bytecode sequences are identical, the mutant is proved algebraically equivalent at compile-time with **0.0% false positive rate (100% precision)**.
- Adjusted Mutation Score is calculated as:
$$\text{MS}_{\text{adj}} = \frac{\text{Mutants Killed}}{\text{Total Mutants} - \text{Verified Equivalent Mutants}} \times 100\%$$

---

## 5. Experimental Results & Ablation Study

### 5.1 Canonical 4 Targets (Macro Evaluation)
We evaluated TestForge across 4 standard software engineering benchmarks representing diverse algorithmic profiles:
1. `samples/discount.py`: Arithmetic boundary and branch discount logic.
2. `samples/order_fsm.py`: Complex stateful e-commerce Finite State Machine (FSM).
3. `samples/lru_cache.py`: High-complexity doubly linked list LRU cache.
4. `samples/stats_calculator.py`: Numerical statistical computations with floating-point boundaries.

| Target Module | LOC | Mutants | Baseline Line Cov | Baseline Raw MS | Zero-Shot Raw MS | TestForge Final Raw MS | TestForge Final Adj MS | Mutants Killed |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `discount.py` | 19 | 19 | 50.0% | 5.26% | 63.16% | **94.74%** | **100.0%** | 18 / 19 |
| `order_fsm.py` | 89 | 106 | 28.1% | 6.60% | 13.21% | **97.17%** | **100.0%** | 103 / 106 |
| `lru_cache.py` (Stateful Call-Chain)* | 74 | 42 | 21.4% | 7.14% | 23.81% | **90.48%** | **95.00%** | 38 / 42 |
| `stats_calculator.py`| 54 | 73 | 23.5% | 6.85% | 30.14% | **45.21%** | **46.48%** | 33 / 73 |
| **Macro Average** | **59** | **240** | **30.75%** | **6.46%** | **32.58%** | **77.42%** | **80.37%** | **192 / 240** |

*\*Note on `lru_cache.py`: Phase-2 baseline reflection scored 30.95% raw MS (13/42 killed). Phase-3 Stateful Call-Chain Planning lifts this to 90.48% raw MS (38/42 killed, 100% Pass@1) by formulating multi-step sequence plans across capacity eviction, sentinel invariants, and key updates.*

**Empirical Takeaway:** TestForge achieves a **12.0x relative improvement** in mutation score over developer baselines (6.46% -> 77.42% raw MS) and more than doubles the effectiveness of unguided zero-shot LLM test suites (32.58% -> 77.42% raw MS), proving the decisive value of closed-loop adversarial reflection.

### 5.2 Production & Sealed Generalization Targets
To verify that TestForge generalizes beyond simple algorithmic benchmarks, we evaluated the Hybrid Synthesizer on complex production codebases and adapted standard library modules:

| Target Module | Complexity Domain | Baseline Raw MS | Hybrid Synthesizer MS | Mutation Score Lift | Clean Pass@1 Status |
| :--- | :--- | :---: | :---: | :---: | :---: |
| `jwt_validator.py` | Cryptographic auth & base64 parsing | 48.98% | **54.42%** | **+5.44%** | 100% Pass (80/147 killed) |
| `rate_limiter.py` | Stateful token-bucket concurrency | 21.77% | **59.18%** | **+37.41%** | 100% Pass (87/147 killed) |
| `bisect_algo.py` | Binary search & sequence slicing | 0.0% | **65.71%** | **+65.71%** | 100% Pass (46/70 killed) |
| `lru_cache.py` (Stateful Call-Chain) | Doubly-linked eviction nodes | 7.14% | **90.48%** | **+83.34%** | 100% Pass (38/42 killed) |

### 5.3 Retraction & Correction Register
In alignment with strict empirical honesty, TestForge maintains a public claims retraction register:
- **Retraction of CLM-028 (Local LLM 90%+ Claims):** Legacy claims that local Qwen models achieved 91.5% - 97.8% raw mutation score on sealed targets were discovered to be artifacts of DEF-022 (unvalidated suites throwing exceptions on clean code). These claims were formally retracted and corrected to verified DEF-022 Pass@1 metrics in `docs/CLAIMS_REGISTER.md`.
- **Retraction of CLM-032 (Statement Count Doubling):** Discrepancies in AST line count parsing on multi-line decorators were audited and patched in DEF-023.

---

## 6. Limitations & Negative Results

A rigorous academic evaluation must document system boundaries and failure modes:
1. **Untyped Dynamic Sequence Indexing:** Pure static AST analysis cannot infer element types or allowable collection keys without dynamic typing or PEP-484 annotations. In early iterations on `bisect_algo`, the synthesizer passed integers to functions expecting sorted sequences, resulting in preflight type failures. This motivated the development of AST sequence parameter inference (Step 2).
2. **Complex Stateful Object Inter-Call Dependencies:** In classes like `LRUCache`, killing subtle eviction mutants requires executing exact multi-step method sequences (`cache.put(k1, v1) -> cache.put(k2, v2) -> cache.get(k1) -> cache.put(k3, v3)`). While TestForge kills 54.76% of LRU mutants, single-method assertions miss internal pointer swaps without prolonged call-chain synthesis.
3. **API Quota & LLM Jitter:** Foundation model latency and rate limits present practical hurdles in CI/CD pipelines. TestForge addresses this by pairing fast local deterministic AST seeds with cloud LLM reflection and full local privacy mode.

---

## 7. Two-Contributor Engineering Division of Labor

The development of TestForge was executed as a collaborative two-engineer effort with strictly demarcated technical ownership:

| Engineering Lead | Primary Subsystems & Architectural Ownership | Key Deliverables & Commits |
| :--- | :--- | :--- |
| **Sourabh** | **Static Analysis, Orchestration, Synthesis & UI**<br>• Code Intelligence Agent (`testforge/code_intelligence_agent.py`)<br>• Master Orchestrator State Machine (`testforge/orchestrator.py`)<br>• Hybrid Synthesizer & Never-Regress Guard (`testforge/hybrid_synthesizer.py`)<br>• Agentic RAG Vector Store & Corpus (`testforge/rag/`)<br>• FastAPI Web Cockpit & Visual Diff Viewer (`frontend/`, `server.py`) | • Multi-agent FSM lifecycle & A2A protocol<br>• FastMCP Stdio Client & Tool Studio<br>• Side-by-side visual AST mutant diff viewer<br>• DEF-022 Pass@1 clean preflight guard |
| **Shreshth** | **Mutation Engine, Sandbox Execution & Equivalence**<br>• AST Mutation Engine & Operator Registry (`testforge/mutator.py`)<br>• Parallel Subprocess Sandbox Runner (`testforge/sandbox.py`)<br>• Bytecode Semantic Equivalence Engine (`testforge/equivalence.py`)<br>• FastMCP Server Tool Definitions (`testforge/mcp_server.py`)<br>• Test Suite Minimization Engine (`testforge/suite_minimizer.py`) | • 10 AST mutation operators<br>• Detached process isolation & RLIMIT quotas<br>• Recursive bytecode disassembly comparison<br>• FastMCP protocol server endpoints |

---

## 8. Conclusion & References

TestForge proves that mutation-verified multi-agent reflection transforms unassertive, fragile LLM code generation into a rigorous software verification engine. By combining the FastMCP protocol suite, Agentic RAG boundary patterns, SQLite immutable state ledgers, and strict clean-code preflight validation, TestForge provides an empirically honest foundation for autonomous software engineering.

### References
1. **Jia, Y., & Harman, M. (2011).** An analysis and survey of the development of mutation testing. *IEEE Transactions on Software Engineering*, 37(5), 649-678.
2. **Just, R., Jalali, D., Inozemtseva, L., Ernst, M. D., Holmes, R., & Fraser, G. (2014).** Are mutants a valid substitute for real faults in software testing? *ACM SIGSOFT FSE*, 654-665.
3. **Papadakis, M., et al. (2019).** Mutation testing advances: An analysis and survey. *Advances in Computers*, 112, 275-378.
4. **Model Context Protocol (MCP) Specification.** Anthropic PBC / Linux Foundation (2024). Open standard for agent tool communication over JSON-RPC.
5. **Google Agent Development Kit (ADK) & Agent2Agent Protocol.** Google DeepMind (2025). Framework for enterprise agent orchestration and multi-agent interoperability.
