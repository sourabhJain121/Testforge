# TestForge Viva Package: Technical Component Breakdown

This document provides a component-by-component architectural deep dive for oral examination and technical defense.

---

## 1. Google ADK Primary Orchestration Engine

- **Package & Version**: `google-adk==1.14.1`
- **Source Files**: [`testforge/orchestrator.py`](file:///Users/sourabh/TestForge/testforge/orchestrator.py), [`testforge/adk_cross_job_memory.py`](file:///Users/sourabh/TestForge/testforge/adk_cross_job_memory.py), [`testforge/adk_callbacks.py`](file:///Users/sourabh/TestForge/testforge/adk_callbacks.py)
- **Role**: Coordinates the workflow lifecycle state machine, session persistence, and agent execution.
- **Key Classes**:
  - `TestForgeOrchestrator`: Master workflow runner enforcing 8-stage state transitions.
  - `ADKCrossJobLearningOrchestrator`: Binds `DatabaseSessionService` (SQLite WAL) with `InMemoryMemoryService` to transfer learned mutant kill heuristics across independent runs.
- **Empirical Evidence**: Cold start requires 3 reflection iterations (2 turns); Warm start retrieves 2 memory entries and kills all mutants on Turn 1 (**66.7% turn reduction, 2.02x speedup**).

---

## 2. CrewAI Adversarial Mutation Critic

- **Package & Version**: `crewai==0.102.0`
- **Source Files**: [`testforge/agents.py`](file:///Users/sourabh/TestForge/testforge/agents.py), [`testforge/a2a_distributed.py`](file:///Users/sourabh/TestForge/testforge/a2a_distributed.py)
- **Role**: Operates as an independent adversarial evaluator. Analyzes surviving mutant AST diffs and generates prescriptive test directives.
- **Key Classes**:
  - `MutationQualityCriticAgent`: CrewAI agent configured with custom goal, backstory, and evaluation tools.
  - `DistributedCriticClient`: Dispatches evaluation requests to a separate OS process (`worker_pid != parent_pid`) via HTTP JSON-RPC over the A2A wire protocol.

---

## 3. Official Agent2Agent (A2A v0.3.0) Wire Protocol

- **Specification**: Linux Foundation / Google Agent2Agent Wire Protocol v0.3.0
- **Source Files**: [`testforge/a2a.py`](file:///Users/sourabh/TestForge/testforge/a2a.py), [`testforge/a2a_protocol.py`](file:///Users/sourabh/TestForge/testforge/a2a_protocol.py)
- **Endpoints**:
  - `GET /.well-known/agent-card.json`: Machine-readable agent capability card.
  - `POST /a2a/tasks/send`: JSON-RPC task creation and lifecycle dispatch.
  - `POST /a2a/tasks/get`: Task status polling and outcome retrieval.
- **Envelopes**: FIPA performatives (`REQUEST`, `INFORM`, `FAILURE`, `REFUSE`) with typed JSON schemas.

---

## 4. Model Context Protocol (FastMCP)

- **Source Files**: [`testforge/mcp_server.py`](file:///Users/sourabh/TestForge/testforge/mcp_server.py), [`testforge/mcp_client.py`](file:///Users/sourabh/TestForge/testforge/mcp_client.py), [`testforge/adk_mcp_adapter.py`](file:///Users/sourabh/TestForge/testforge/adk_mcp_adapter.py)
- **Client Role**: Consumes workspace inspection tools (`read_text_file`, `list_directory`, `get_file_info`) inside Google ADK agents with path containment.
- **Server Role**: Exposes TestForge as an MCP server (`harden_module`, `get_report`, `list_jobs`) for external assistants (e.g. Claude Desktop).

---

## 5. Deterministic AST Mutator Engine

- **Source Files**: [`testforge/mutator.py`](file:///Users/sourabh/TestForge/testforge/mutator.py)
- **Mutation Operator Classes (10 Total)**:
  1. `COMP_OP`: Comparison relational inversions (`<` $\leftrightarrow$ `<=`, `==` $\leftrightarrow$ `!=`).
  2. `BOUNDARY_SWAP`: Boundary relational swaps (`<` $\leftrightarrow$ `<=`).
  3. `OFF_BY_ONE`: Constant increments/decrements ($n \pm 1$).
  4. `ARITH_OP`: Arithmetic operator flips (`+` $\leftrightarrow$ `-`, `*` $\leftrightarrow$ `//`).
  5. `LOGICAL_CONN`: Boolean connective swaps (`and` $\leftrightarrow$ `or`).
  6. `MATH_FUNC`: Rounding precision mutations and `abs()` removals.
  7. `COND_INV`: Predicate negation (`if x:` $\rightarrow$ `if not x:`).
  8. `RETURN_VAL`: Return value inversions and substitutions.
  9. `BITWISE_OP`: Bitwise operator swaps (`&` $\leftrightarrow$ `|`, `^`).
  10. `EXCEPTION_SWAP` & `STATEMENT_DELETION`: In-place statement deletions (`ast.Pass`) and exception swaps.

---

## 6. Mathematical Equivalence Engine

- **Source Files**: [`testforge/equivalence.py`](file:///Users/sourabh/TestForge/testforge/equivalence.py)
- **Tier 1 (Recursive Bytecode Normalization)**:
  - Disassembles bytecode with `dis.get_instructions`.
  - Normalizes line numbers, jump targets, and constant tables.
  - Recursively compares nested code objects (closures, list comprehensions).
- **Tier 2 (Structured LLM Semantic Equivalence Judge)**:
  - Formulates formal contract comparison for mutants with semantic identity despite syntactic differences.
- **Empirical Accuracy**: **100% precision, 0% FPR, 90% recall, 94.7% F1-score** on 30 ground-truth labeled benchmark mutants.

---

## 7. Test Suite Minimizer (Greedy Set Cover)

- **Source Files**: [`testforge/minimizer.py`](file:///Users/sourabh/TestForge/testforge/minimizer.py)
- **Algorithm**: Greedy approximation of the NP-hard minimum set cover on the 2D Boolean Kill Matrix $M \in \{0, 1\}^{|T| \times |K|}$.
- **Empirical Result**: Across 4 benchmark modules, compressed 134 tests down to 28 tests (**79.1% reduction**) while mathematically retaining **100.0% of killed mutants** (0 lost kills).

---

## 8. Diff-Incremental CI/CD Engine

- **Source Files**: [`testforge/diff_incremental.py`](file:///Users/sourabh/TestForge/testforge/diff_incremental.py)
- **Algorithm**: Parses unified diff hunk headers (`@@ -l,s +start,count @@`) and restricts AST mutant injection exclusively to touched lines.
- **Empirical Result**: Across 4 realistic PR scenarios, eliminated **88.3% of redundant mutants** (240 down to 28), speeding up execution from 15.08s to 2.80s (**5.39x speedup**) with 100% diff-line defect detection.
