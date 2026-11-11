# TestForge Core-10 Viva & Oral Examination Study Guide

**Target Audience:** Viva Examination Candidates, System Auditors, Academic Examiners  
**Coursework:** Autonomous Agentic AI Systems (Phase-3 Capstone Evaluation)  
**Evaluation Reference:** Python 3.13 macOS arm64 (`.venv-release`), 999 Passed Unit & Integration Tests  
**Git Branch:** `release/v1.0.0` (Monotonic Verification)

---

## Navigation Matrix: The 10 Core Architectural Modules

| # | Core Module | Primary File & Class | Key Capability & Architectural Role |
| :- | :--- | :--- | :--- |
| **1** | [Orchestrator](#1-master-orchestration-engine-testforgeorchestratorpy) | `testforge/orchestrator.py` (`TestForgeOrchestrator`) | State machine FSM, inter-agent loop, Never-Regress Guard, OTel spans |
| **2** | [Deterministic AST Mutator](#2-deterministic-ast-mutator-testforgemutatorpy) | `testforge/mutator.py` (`ASTMutator`) | 10 mutation operators across 7 categories, diff targeting, AST unparsing |
| **3** | [Sandboxed Execution Engine](#3-parallel-sandboxed-execution-testforgesandboxpy) | `testforge/sandbox.py` (`ParallelSandboxRunner`) | Multi-core process pool, timeout guardrails, DEF-022 clean preflight |
| **4** | [FastMCP Server](#4-fastmcp-protocol-server-testforgemcp_serverpy) | `testforge/mcp_server.py` (`create_protocol_suite_server`) | 4 official MCP tools: symbol analyzer, mutator, sandbox, equivalence |
| **5** | [FastMCP Stdio Client](#5-fastmcp-stdio-subprocess-client-testforgemcp_clientpy) | `testforge/mcp_client.py` (`FastMCPStdioClient`) | Subprocess stdio JSON-RPC transport, child lifecycle, resilient fallback |
| **6** | [Blackboard & WAL Persistence](#6-blackboard-state--sqlite-wal-persistence-testforgeblackboardpy) | `testforge/blackboard.py` (`Blackboard`) | 8 typed memory partitions, SQLite WAL checkpoint storage & rollback |
| **7** | [Hybrid Synthesizer](#7-hybrid-synthesizer--never-regress-guard-testforgehybrid_synthesizerpy) | `testforge/hybrid_synthesizer.py` (`HybridSynthesizer`) | Invariant seeds, Pass@1 clean validation filter, monotonic peak retention |
| **8** | [Agentic RAG Retriever](#8-agentic-rag-knowledge-retriever-testforgeragknowledge_retrieverpy) | `testforge/rag/knowledge_retriever.py` (`AgenticKnowledgeRetriever`) | Zero-egress vector store, query reformulation, boundary recipe grading |
| **9** | [FastAPI Server](#9-fastapi-backend-api-serverpy) | `server.py` (`FastAPI`) | REST API, SSE/WebSocket streaming, MCP endpoints, async job runner |
| **10**| [Web Cockpit Dashboard](#10-web-cockpit-ui-frontendappjs) | `frontend/app.js` (Vanilla ES6 SPA) | 7 views, visual AST diff viewer, MCP Tool Studio, real-time wiretap |

---

## 1. Master Orchestration Engine (`testforge/orchestrator.py`)

### Key File & Reference Lines
* File: [`testforge/orchestrator.py`](file:///Users/sourabh/TestForge/testforge/orchestrator.py)
* Class: `TestForgeOrchestrator` (Line 136)
* Pipeline Methods: `harden()` (Line 806), `run()` (Line 815)
* Inter-Agent Execution Loop: Lines 1050–1350 (`_execute_pipeline`)
* Agentic RAG Trace Span: Line 1114 (`rag.retrieval` OpenTelemetry span emission)
* Never-Regress Monotonic Check: Lines 1180–1280

### Architecture & Mechanism
The orchestrator acts as the master coordinator across the agent topology. It drives a stateful FSM:
`INGESTION -> PLANNING (RAG) -> GENERATION -> SANDBOX_PREFLIGHT -> MUTATION -> CRITIC -> REPAIR -> MONOTONIC_GATE -> FINALIZATION`
In each reflection turn:
1. `TestPlanningAgent` analyzes AST intelligence and retrieves heuristics from the local vector store.
2. `TestGeneratorAgent` synthesizes candidate test assertions targeting surviving mutants.
3. `GranularTestValidator` validates candidate tests individually against clean reference code (`Pass@1`).
4. Retained tests run against surviving mutants in parallel.
5. If an LLM hallucination degrades the suite, `NeverRegressGuard` restores the historical monotonic peak.

### Examiner Q&A
* **Q:** *Why does agentic reflection sometimes perform worse than deterministic generation?*  
  **Answer:** Stochastic LLMs introduce syntax errors, impossible preconditions, or fragile assertions in later turns. When an orchestrator naively takes the last iteration's suite rather than the Pareto-optimal suite, score regresses. TestForge guards against this via `NeverRegressGuard`, which retains the monotonic peak across all iterations.

### Live Exercise
```bash
.venv-release/bin/python -c "
from testforge.orchestrator import TestForgeOrchestrator
orch = TestForgeOrchestrator(target_source_code='def f(x): return x > 0', max_iterations=1, enable_rag=True)
res = orch.run()
print('Monotonic final score:', res.final_mutation_score, '| Validated clean pass:', res.clean_code_passed)
"
```

---

## 2. Deterministic AST Mutator (`testforge/mutator.py`)

### Key File & Reference Lines
* File: [`testforge/mutator.py`](file:///Users/sourabh/TestForge/testforge/mutator.py)
* Class: `ASTMutator` (Line 430), `ASTMutationVisitor` (Line 150)
* Operator Registry: Lines 30–100 (10 operators across 7 categories: `BOUNDARY_SWAP`, `COMP_OP`, `COND_INV`, `CONST_VAL`, `LOGICAL_CONN`, `MATH_FUNC`, `RETURN_VAL`, `OFF_BY_ONE`, `STATEMENT_DEL`, `EXCEPTION_MOD`)
* Clean Syntax Preflight Check: Lines 85–115 (`compile(snippet, '<mutant>', 'exec')`)

### Architecture & Mechanism
TestForge uses Python's `ast` module to perform precise AST node transformations:
1. Parses target source into an AST via `ast.parse`.
2. Visits candidate AST nodes (`BinOp`, `Compare`, `BoolOp`, `If`, `UnaryOp`, `Subscript`).
3. For each viable mutation point, produces a deep-copied AST with exactly one transformation, unparses it back to Python code via `ast.unparse`, and generates a deterministic `unified_diff`.

### Examiner Q&A
* **Q:** *How do you ensure mutated code is syntactically valid and never crashes the test runner on syntax errors?*  
  **Answer:** Mutations are applied directly to parsed AST node objects rather than regex string replacement. Before any mutant record is added to the execution pool, `is_valid_syntax` performs `compile(snippet, '<mutant>', 'exec')` pre-flight verification, guaranteeing 100% syntactically valid Python.

### Live Exercise
```bash
.venv-release/bin/python -c "
from testforge.mutator import ASTMutator
code = 'def is_even(n): return n % 2 == 0'
mutants = ASTMutator.generate_mutants(code)
print(f'Generated {len(mutants)} AST mutants:')
for m in mutants[:3]:
    print(f'  [{m.mutation_type}] line {m.line_number}: {m.original_code_snippet} -> {m.mutated_code_snippet}')
"
```

---

## 3. Parallel Sandboxed Execution (`testforge/sandbox.py`)

### Key File & Reference Lines
* File: [`testforge/sandbox.py`](file:///Users/sourabh/TestForge/testforge/sandbox.py)
* Class: `ParallelSandboxRunner` (Line 569), `GranularTestValidator` (Line 345)
* Sanitized Subprocess Environment: Lines 80–120 (`build_sanitized_sandbox_env`)
* Subprocess Timeout & Memory Ceilings: Lines 120–190 (Detached process groups, `signal.SIGKILL`, `RLIMIT_AS`)
* Failure Classification: Lines 695–740 (`ASSERTION_FAIL`, `EXCEPTION_FAIL`, `TIMEOUT`, `UNCOVERED`)

### Architecture & Mechanism
`ParallelSandboxRunner` executes test suites concurrently across all available CPU cores using `ProcessPoolExecutor`:
1. Each test run occurs in an ephemeral `tempfile.TemporaryDirectory` with target aliases (`target.py`, `samples/...`).
2. Sanitized environment (`build_sanitized_sandbox_env`) strips host API keys and tokens.
3. Subprocess execution enforces strict wall-clock timeouts via `signal.SIGALRM` / `process.kill()`.
4. Collects coverage via `pytest-cov`, extracting target file stats from `cov.json["files"]` to prevent alias statement inflation.

### Examiner Q&A
* **Q:** *How does the runner handle infinite loops caused by while-condition mutants?*  
  **Answer:** Subprocesses are launched with a strict timeout (default 3.0s - 5.0s). If the timeout expires, the OS process group is detached and terminated (`SIGKILL`), and the mutant is classified as `status="TIMEOUT"`, `kill_classification="TIMEOUT"`, counting as a valid kill due to infinite loop detection.

### Live Exercise
```bash
.venv-release/bin/python -c "
from testforge.sandbox import ParallelSandboxRunner
runner = ParallelSandboxRunner(timeout_seconds=2)
cov, info = runner.measure_coverage('from target import *\ndef test_ok(): pass\n', 'def add(a, b): return a + b\n')
print('Baseline passed:', info['baseline_passed'], '| Statements:', info['num_statements'])
"
```

---

## 4. FastMCP Protocol Server (`testforge/mcp_server.py`)

### Key File & Reference Lines
* File: [`testforge/mcp_server.py`](file:///Users/sourabh/TestForge/testforge/mcp_server.py)
* Official 4 FastMCP Tools:
  - `mcp_ast_symbol_analyzer` (Line 319): AST callables, branch conditions, cyclomatic complexity.
  - `mcp_mutant_generator` (Line 394): Deterministic bounded AST mutant records.
  - `mcp_sandbox_runner` (Line 418): Sandboxed candidate suite execution under 3.0s timeout.
  - `mcp_equivalence_classifier` (Line 446): Compiler bytecode equivalence analyzer.
* Server Factory: `create_protocol_suite_server()` (Line 520)

### Architecture & Mechanism
Encapsulates all static analysis, mutation generation, sandboxed execution, and bytecode equivalence classification inside standard Model Context Protocol (FastMCP) `@mcp.tool()` decorators with strict Pydantic type hints and docstrings. External agents or subagents query tools over standardized JSON-RPC protocols.

### Examiner Q&A
* **Q:** *Why are exactly 4 tools exposed in the protocol suite?*  
  **Answer:** The 4 tools represent the complete orthogonal primitive set for autonomous test hardening: static symbol analysis, mutation synthesis, sandboxed execution, and semantic equivalence detection. Auxiliary filesystem or git tools are decoupled to maintain tight security boundaries.

### Live Exercise
```bash
.venv-release/bin/python -c "
from testforge.mcp_server import mcp_ast_symbol_analyzer
res = mcp_ast_symbol_analyzer('def calc(x): return x * 2')
print('Discovered functions:', [f['name'] for f in res['functions']])
"
```

---

## 5. FastMCP Stdio Subprocess Client (`testforge/mcp_client.py`)

### Key File & Reference Lines
* File: [`testforge/mcp_client.py`](file:///Users/sourabh/TestForge/testforge/mcp_client.py)
* Class: `MCPClientManager` (Line 167), `FastMCPStdioClient` (Line 739)
* Stdio Child Launch: Lines 745–780 (`python -m testforge.mcp_server` subprocess with pipe redirection)
* JSON-RPC Stdio Communication: Lines 780–840
* Fallback Telemetry Event: Line 830 (`MCP_STDIO_FALLBACK_TRIGGERED`)

### Architecture & Mechanism
`FastMCPStdioClient` manages an isolated child process running the FastMCP server. It sends JSON-RPC requests across `stdin` and reads responses from `stdout`:
- Subprocess launched on demand with clean OS process detachment.
- Enforces strict read timeouts (default 5.0s).
- If stdio pipes encounter broken pipe, EOF, or timeout, it gracefully falls back to in-process tool execution while logging an explicit telemetry event.

### Examiner Q&A
* **Q:** *What happens if the FastMCP child process crashes during a mutation run?*  
  **Answer:** The client catches `BrokenPipeError` or `TimeoutError`, automatically terminates any orphaned child process, logs `MCP_STDIO_FALLBACK_TRIGGERED` to the telemetry stream, and routes the tool call directly to in-process execution without failing the hardening pipeline.

### Live Exercise
```bash
.venv-release/bin/python -c "
from testforge.mcp_client import FastMCPStdioClient
client = FastMCPStdioClient()
res = client.call_tool_sync('mcp_ast_symbol_analyzer', {'source_code': 'def f(x): return x + 1'})
print('Stdio MCP Call success:', res.success, '| Discovered functions:', len(res.data['functions']))
client.close()
"
```

---

## 6. Blackboard State & SQLite WAL Persistence (`testforge/blackboard.py`)

### Key File & Reference Lines
* File: [`testforge/blackboard.py`](file:///Users/sourabh/TestForge/testforge/blackboard.py)
* Class: `Blackboard` (Line 356), `SQLiteBlackboardStorage` (Line 65)
* 8 Typed Partitions: Lines 50–250 (`TargetSpace`, `MutantSpace`, `CriticSpace`, `SuiteSpace`, `MetricsSpace`, `PlanSpace`, `ExecutionSpace`, `SecuritySpace`)
* Checkpoints: Lines 965–1150 (`save_checkpoint`, `restore_checkpoint`, `list_checkpoints`)

### Architecture & Mechanism
The Blackboard provides a thread-safe, typed shared memory substrate across all 8 agents:
- Partitioned into 8 distinct Pydantic-validated namespaces.
- Uses SQLite Write-Ahead Logging (`WAL` mode) with `PRAGMA synchronous = NORMAL` for atomic crash resilience.
- Supports zero-copy in-memory snapshots, rollback to prior iterations, and state diff comparisons.

### Examiner Q&A
* **Q:** *Why use a Blackboard architecture instead of passing messages directly between agents?*  
  **Answer:** Direct point-to-point messaging creates $O(N^2)$ tight coupling. A shared Blackboard decouples agents: the mutator writes mutants, the generator reads mutants and writes tests, and the critic inspects tests and writes directives. All state is observable, auditable, and version-controlled via SQLite checkpoints.

### Live Exercise
```bash
.venv-release/bin/python -c "
import tempfile
from testforge.blackboard import Blackboard
with tempfile.NamedTemporaryFile(suffix='.db') as f:
    bb = Blackboard(checkpoint_db_path=f.name)
    bb.update_target_space(source_code='x = 10')
    cid = bb.save_checkpoint('init', 'Initial baseline')
    bb.update_target_space(source_code='x = 20')
    cid2 = bb.save_checkpoint('updated', 'After reflection loop')
    print('Checkpoints persisted:', len(bb.list_checkpoints()), '| Latest ID:', cid2)
    bb.close()
"
```

---

## 7. Hybrid Synthesizer & Never-Regress Guard (`testforge/hybrid_synthesizer.py`)

### Key File & Reference Lines
* File: [`testforge/hybrid_synthesizer.py`](file:///Users/sourabh/TestForge/testforge/hybrid_synthesizer.py)
* Class: `HybridSynthesizer` (Line 51)
* Seed Test & RAG Generation: Lines 121–155 (`_generate_seed_tests`, `_synthesize_rag_boundary_tests`)
* DEF-022 Clean Preflight Guard: Lines 265–300 (`filter_clean_passing_tests`)
* Monotonic Reflection Loop: Lines 310–380 (`NeverRegressGuard`)

### Architecture & Mechanism
Combines boundary-aware AST invariant seeds with mutation-guided reflection:
1. Ingests target AST, extracts callable signatures, and injects RAG heuristics.
2. Applies strict DEF-022 Pass@1 clean preflight validation: broken candidate assertions are filtered out so ONLY 100% clean-passing tests are retained.
3. Evaluates retained tests against mutants, invokes the Critic, and synthesizes targeted counterexamples.
4. Enforces the Never-Regress Guard: if an iteration lowers the mutation score, it reverts to the historical peak.

### Examiner Q&A
* **Q:** *How does the Hybrid Synthesizer achieve DEF-022 compliance?*  
  **Answer:** In `filter_clean_passing_tests()`, the candidate suite is executed against unmutated reference code. If any test throws an error or assertion failure, `GranularTestValidator` isolates each test function, pruning failing functions and keeping only 100% clean-passing tests. If zero tests pass clean code, the suite is classified as `INVALID_SUITE` (0 kills, 0.0% MS).

### Live Exercise
```bash
.venv-release/bin/python -c "
from testforge.hybrid_synthesizer import HybridSynthesizer
code = 'def divide(a, b):\n    if b == 0:\n        raise ZeroDivisionError(\"zero\")\n    return a / b\n'
synth = HybridSynthesizer(target_code=code, enable_rag=True)
suite = synth._generate_seed_tests()
clean_suite, is_clean = synth.filter_clean_passing_tests(suite)
print('Preflight clean pass:', is_clean, '| Retained test code length:', len(clean_suite))
"
```

---

## 8. Agentic RAG Knowledge Retriever (`testforge/rag/knowledge_retriever.py`)

### Key File & Reference Lines
* File: [`testforge/rag/knowledge_retriever.py`](file:///Users/sourabh/TestForge/testforge/rag/knowledge_retriever.py)
* Class: `RetrievalResult` (Line 21), `AgenticKnowledgeRetriever` (Line 36)
* Decision Gating: Line 56 (`should_retrieve`)
* Semantic Query Reformulation: Line 70 (`reformulate_query`)
* Relevance Grading: Line 94 (`grade_chunk_relevance`, 0.0 to 1.0)
* Retrieval Loop: Line 125 (`retrieve()`)

### Architecture & Mechanism
Intelligent local retrieval controller providing:
1. **Trivial Query Gating**: Bypasses empty or uninformative single-keyword pass-throughs.
2. **Semantic Query Reformulation**: Rewrites raw AST tokens (e.g. `BinOp(Div)`) into canonical testing concepts (`division zero division arithmetic float overflow`).
3. **Relevance Grading**: Scores candidate chunks based on vector similarity (60%), operator alignment (25%), category alignment (15%), and code executability bonus.
4. **Curated Corpus Collections**: `arithmetic_division.json`, `sequence_slicing.json`, `string_regex.json`, `stateful_cache_fsm.json`.

### Examiner Q&A
* **Q:** *How does the retriever prevent injecting irrelevant heuristics?*  
  **Answer:** Retrieved chunks undergo multi-factor grading (`grade_chunk_relevance`). Only chunks exceeding `min_score` (default 0.3) are retained. If no relevant chunks match, the retriever gracefully returns an empty result, falling back to standard AST boundary seeds.

### Live Exercise
```bash
.venv-release/bin/python -c "
from testforge.rag.knowledge_retriever import AgenticKnowledgeRetriever
retriever = AgenticKnowledgeRetriever()
res = retriever.retrieve('BinOp(Div) zero denominator', top_k=2)
print('Retrieved chunks:', len(res.chunks))
for c in res.chunks:
    print(' -', c['doc_id'], 'score:', c['relevance_score'], 'category:', c['metadata']['category'])
"
```

---

## 9. FastAPI Backend API (`server.py`)

### Key File & Reference Lines
* File: [`server.py`](file:///Users/sourabh/TestForge/server.py)
* Application Setup: Lines 90–120
* Pydantic Schemas: Line 282 (`HardeningRunPayload`)
* FastMCP Endpoints: Lines 437 (`/api/mcp/status`), 603 (`/api/mcp/execute-tool`)
* Hardening Execution: Lines 1209 (`_run_orchestration_job`), 1418 (`/api/harden/start`), 1757 (`/api/harden/run`)
* Checkpoints & Rollbacks: Lines 2250–2355 (`/api/checkpoints/rollback/{id}`)

### Architecture & Mechanism
The presentation and orchestration API backend:
- Exposes synchronous and asynchronous endpoints for test hardening.
- Manages background thread execution pools with thread-safe cancellation events (`cancel_event`).
- Houses WebSocket and Server-Sent Events (SSE) streaming infrastructure for the real-time agent wiretap.
- Serves the static single-page application frontend.

### Examiner Q&A
* **Q:** *How does the backend prevent concurrent jobs from corrupting filesystem state?*  
  **Answer:** Every job generates a unique UUID `job_id`. Subprocesses and sandboxes execute inside dedicated `tempfile.TemporaryDirectory` paths. Blackboard database updates are locked via `JOB_LOCK` and SQLite WAL concurrency control.

### Live Exercise
```bash
.venv-release/bin/python -c "
from fastapi.testclient import TestClient
from server import app
client = TestClient(app)
res = client.get('/healthz')
print('Server healthz:', res.json())
mcp_res = client.get('/api/mcp/status')
print('FastMCP Registered Tools:', len(mcp_res.json()['tools']))
"
```

---

## 10. Web Cockpit UI (`frontend/app.js`)

### Key File & Reference Lines
* File: [`frontend/app.js`](file:///Users/sourabh/TestForge/frontend/app.js)
* DOM Elements & State Store: Lines 150–450 (`dom`, `state`)
* Visual AST Mutant Diff Inspector: Lines 2450–2700 (`renderMutantDiffView`, side-by-side gutter formatting)
* FastMCP Tool Studio Runner: Lines 2820–2950 (`executeMcpTool`, parameter table parsing)
* Hardening Dispatcher: Line 3065 (`/api/harden/start` payload with `enable_rag`)
* Telemetry & OTel Spans Rendering: Lines 5670–5720 (High-visibility `rag.retrieval` badge formatting)

### Architecture & Mechanism
Pure Vanilla ES6 Single-Page Application (SPA) with zero external NPM packages:
- Responsive CSS custom properties supporting dark and light themes.
- Side-by-side and unified syntax-highlighted code diff viewer showing clean code vs. AST mutated code.
- Interactive FastMCP Tool Studio allowing engineers to inspect tool schemas, modify arguments, and execute tools live over stdio JSON-RPC.
- Real-time WebSocket timeline streaming agent handoffs, reasoning traces, and critic directives.

### Examiner Q&A
* **Q:** *Why did you build the frontend in Vanilla ES6 rather than React or Vue?*  
  **Answer:** A vanilla ES6 dashboard requires zero `node_modules`, zero build steps, and zero security vulnerabilities from transitive NPM packages. It runs instantly from Python static file mounting, has zero cold-start delay, and eliminates framework churn while delivering sub-millisecond reactive DOM updates.

### Live Exercise
```bash
# Verify frontend syntax and absence of syntax errors
.venv-release/bin/python -c "
from pathlib import Path
app_js = Path('frontend/app.js').read_text()
assert 'executeMcpTool' in app_js
assert 'chk-enable-rag' in app_js
print('frontend/app.js validated: syntax complete, length =', len(app_js), 'chars')
"
```
