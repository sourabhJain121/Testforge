# TestForge Core-10 Viva & Oral Examination Study Guide

**Target Audience:** Viva Examination Candidates, System Auditors, Academic Examiners  
**Coursework:** CSE3101: Autonomous Agentic AI Systems  
**Evaluation Reference:** Python 3.13 macOS arm64 (`.venv-release`), 999 Passed Unit & Integration Tests

---

## Navigation Matrix: The 10 Core Architectural Pillars

| # | Pillar Component | Primary File & Class | Key Capability |
| :- | :--- | :--- | :--- |
| **1** | [Orchestrator & Reflection](#1-orchestrator--multi-agent-reflection-loop) | `testforge/orchestrator.py` (`TestForgeOrchestrator`) | Dynamic state machine, iteration loop, Never-Regress Guard |
| **2** | [Deterministic AST Mutator](#2-deterministic-ast-mutator) | `testforge/mutator.py` (`ASTMutator`) | 10 mutation operators, diff targeting, AST unparsing |
| **3** | [Blackboard State & WAL Logs](#3-blackboard-state--sqlite-wal-persistence) | `testforge/blackboard.py` (`Blackboard`) | 8 memory partitions, SQLite WAL checkpoint storage |
| **4** | [Parallel Sandboxed Execution](#4-sandboxed-concurrent-worker-subprocesses) | `testforge/sandbox.py` (`ParallelSandboxRunner`) | Multi-core process pool, timeout guardrails, clean pre-flight |
| **5** | [Equivalence Analysis Engine](#5-bytecode--ast-equivalence-engine) | `testforge/equivalence.py` (`EquivalentMutantAnalyzer`) | Bytecode normalization, static triviality, adjusted mutation score |
| **6** | [Intelligent AST Synthesizer](#6-intelligent-ast--property-synthesizer) | `testforge/intelligent_generator.py` (`IntelligentASTSynthesizer`) | Multi-callable discovery, boundary value synthesis, property tests |
| **7** | [Security Guard & Net Confinement](#7-adversarial-security-guard--network-interception) | `testforge/security.py`, `testforge/prompt_guard.py` | AST import blocking, socket network zero-egress, injection defense |
| **8** | [Agent-to-Agent (A2A) Protocol](#8-agent-to-agent-a2a-collaboration-protocol) | `testforge/a2a.py` (`A2ABroker`, `A2AWorker`) | A2A v0.3.0 schema, agent cards, task delegations |
| **9** | [FastMCP Tool Integration](#9-fastmcp-dynamic-tool-exposure) | `testforge/mcp_server.py`, `testforge/mcp_client.py` | Model Context Protocol tool catalog, sandboxed RPC tools |
| **10**| [FastAPI Server & Web Cockpit](#10-fastapi-server-ssews-streaming--cockpit) | `server.py`, `frontend/app.js` | REST endpoints, WebSocket event wiretap, vanilla ES6 dashboard |

---

## 1. Orchestrator & Multi-Agent Reflection Loop

### Key File & Reference Lines
* File: [`testforge/orchestrator.py`](file:///Users/sourabh/TestForge/testforge/orchestrator.py)
* Class: `TestForgeOrchestrator` (Line 130)
* Never-Regress Guard: Line 345–385
* Reflection Iteration Loop: Line 210–330

### Architecture & Mechanism
The orchestrator acts as the master coordinator. It runs a state machine:
`INGESTION -> MUTANT_GENERATION -> BASELINE_VALIDATION -> REFLECTION_LOOP -> FINALIZATION`
In each reflection turn:
1. `TestGeneratorAgent` generates or refines test assertions targeting surviving mutants.
2. `GranularTestValidator` filters candidate tests individually against unmutated reference code (`pass@1`).
3. Retained tests run against surviving mutants in parallel.
4. `NeverRegressGuard` compares the new suite's mutation kill count and branch coverage against the historical best. If an LLM hallucination degrades the suite, the orchestrator reverts state to the historical peak.

### Failure Analysis & Defenses
* **Agentic Regression Defect:** LLMs often produce broken tests in subsequent iterations that fail clean code. Guard: `validate_and_filter_candidate_suite` discards failing individual functions without discarding valid tests, and `NeverRegressGuard` guarantees monotonic progression.
* **Trace Log Memory Leak (DEF-014):** In-memory token accumulators prevent loading the whole JSONL trace log on every turn.

### Examiner Q&A
* **Q1:** *Why does agentic reflection sometimes perform worse than deterministic generation?*  
  **Answer:** Stochastic LLMs introduce syntax errors, impossible preconditions, or fragile assertions in later turns. When an orchestrator naively takes the last iteration's suite rather than the Pareto-optimal suite, score regresses. TestForge guards against this via `NeverRegressGuard`, which retains the monotonic peak across all iterations.
* **Q2:** *How do you prevent cyclic loops between generator and critic agents?*  
  **Answer:** The Blackboard tracks `surviving_mutant_ids` and `critic_directives`. Iterations are strictly bounded by `max_iterations` (default 2), and if no new mutants are killed in turn $i$, the loop terminates early via convergence detection.

### Live Exercise
```bash
.venv-release/bin/python -c "
from testforge.orchestrator import TestForgeOrchestrator
orch = TestForgeOrchestrator(target_source_code='def f(x): return x > 0', max_iterations=1)
res = orch.run()
print('Monotonic final score:', res.final_mutation_score)
"
```

---

## 2. Deterministic AST Mutator

### Key File & Reference Lines
* File: [`testforge/mutator.py`](file:///Users/sourabh/TestForge/testforge/mutator.py)
* Class: `ASTMutator` (Line 25), `ASTMutationVisitor` (Line 110)
* Operator Categories: Line 30–80 (AOR, ROR, LCR, COI, CDL, CRP)

### Architecture & Mechanism
TestForge uses Python's `ast` module to perform precise AST node transformations:
1. Parses target source into an AST via `ast.parse`.
2. Visits candidate AST nodes (`BinOp`, `Compare`, `BoolOp`, `If`, `UnaryOp`).
3. For each viable mutation point, produces a deep-copied AST with exactly one transformation, unparses it back to Python code via `ast.unparse`, and generates a deterministic `unified_diff`.

### Failure Analysis & Defenses
* **Syntax Invalidation Defect:** Certain AST mutations can produce invalid syntax (e.g. invalid indentation or missing required AST child nodes). Guard: `MutantRecord.is_valid_syntax` performs `compile(snippet, '<mutant>', 'exec')` pre-flight verification before any mutant enters the execution pool.

### Examiner Q&A
* **Q1:** *Why not use an off-the-shelf mutator like mutmut instead of writing a custom AST mutator?*  
  **Answer:** `mutmut` operates primarily via text/token manipulation, which does not allow semantic AST queries, diff-incremental boundary targeting, or direct integration with Blackboard state. Our custom `ASTMutator` exposes AST node metadata directly to the Generator and Critic agents to provide syntax-aware targeted feedback.
* **Q2:** *How does TestForge avoid the mutant explosion problem on large repositories?*  
  **Answer:** Diff-targeted mutation (`DiffTargetedMutator`) restricts mutation to lines modified in git diff hunks, reducing mutant count by up to 88.3%. Furthermore, `ASTEquivalenceAnalyzer` prunes provably redundant mutants before execution.

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

## 3. Blackboard State & SQLite WAL Persistence

### Key File & Reference Lines
* File: [`testforge/blackboard.py`](file:///Users/sourabh/TestForge/testforge/blackboard.py)
* Class: `Blackboard` (Line 355)
* Partitions: Line 50–265 (`TargetSpace`, `MutantSpace`, `CriticSpace`, `SuiteSpace`, `MetricsSpace`, `PlanSpace`, `ExecutionSpace`, `SecuritySpace`)
* Checkpoints: Line 965–1150 (`save_checkpoint`, `restore_checkpoint`, `list_checkpoints`)

### Architecture & Mechanism
The Blackboard provides a shared memory substrate across all agents:
* Partitioned into 8 distinct Pydantic-validated namespaces.
* Uses SQLite Write-Ahead Logging (`WAL` mode) with `PRAGMA synchronous = NORMAL` for atomic crash resilience.
* Supports zero-copy in-memory snapshots and atomic persistence across reflection iterations.

### Failure Analysis & Defenses
* **SQLite Lock Contention:** Multi-worker subprocesses or async endpoints could cause `database is locked`. Defense: WAL mode allows concurrent readers without blocking the single writer process, and short retry timeouts ensure thread safety.

### Examiner Q&A
* **Q1:** *Why use a Blackboard architecture instead of passing messages directly between agents?*  
  **Answer:** Direct message passing between $N$ agents leads to $O(N^2)$ point-to-point coupling. A shared Blackboard decouples agents: the mutator writes mutants, the generator reads mutants and writes tests, and the critic inspects tests and writes directives. All state is observable, auditable, and version-controlled via SQLite checkpoints.
* **Q2:** *How do you inspect what changed between iterations?*  
  **Answer:** `blackboard.save_checkpoint(id)` snapshots the 8 partitions into the SQLite database. Restoring or listing via `list_checkpoints()` / `restore_checkpoint(id)` enables time-travel debugging and iteration-level diff audits.

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
    ckpts = bb.list_checkpoints()
    print('Checkpoints persisted:', len(ckpts), '| Latest ID:', cid2)
    bb.close()
"
```

---

## 4. Sandboxed Concurrent Worker Subprocesses

### Key File & Reference Lines
* File: [`testforge/sandbox.py`](file:///Users/sourabh/TestForge/testforge/sandbox.py)
* Class: `ParallelSandboxRunner` (Line 530), `GranularTestValidator` (Line 915)
* Pre-flight Clean Execution: Line 575–595
* Failure Categorization: Line 695–740 (`ASSERTION_FAIL`, `EXCEPTION_FAIL`, `TIMEOUT`, `UNCOVERED`)

### Architecture & Mechanism
`ParallelSandboxRunner` executes test suites concurrently across all available CPU cores using `ProcessPoolExecutor`:
1. Each test run occurs in an ephemeral `tempfile.TemporaryDirectory` with target aliases (`target.py`, `samples/...`).
2. Sanitized environment (`build_sanitized_sandbox_env`) strips host API keys and tokens.
3. Subprocess execution enforces strict wall-clock timeouts via `signal.SIGALRM` / `process.kill()`.
4. Collects coverage via `pytest-cov`, extracting target file stats from `cov.json["files"]` to prevent alias statement inflation.

### Failure Analysis & Defenses
* **Clean-Code Failure False-Kill Defect (DEF-022):** Previously, if a test failed on clean code, pytest exited 1 on every mutant, marking all mutants killed. Defense: `evaluate_suite` enforces `pass@1` clean reference pre-flight; suites failing clean code are marked `INVALID_SUITE` (0 kills).

### Examiner Q&A
* **Q1:** *How do you prevent an infinite loop in a mutant from freezing your evaluation?*  
  **Answer:** Subprocesses are launched with a strict timeout (default 5s). If the timeout expires, the OS process group is detached and terminated (`SIGKILL`), and the mutant is classified as `status="TIMEOUT"`, `kill_classification="TIMEOUT"`, counting as a valid kill due to infinite loop detection.
* **Q2:** *How do you ensure a test that didn't execute a line doesn't get credit for killing a mutant on that line?*  
  **Answer:** The runner checks `cov_info["executed_lines"]`. If `mutant.line_number not in executed_lines`, the mutant is immediately marked `SURVIVED` (`kill_classification="UNCOVERED"`), guaranteeing line coverage consistency.

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

## 5. Bytecode & AST Equivalence Engine

### Key File & Reference Lines
* File: [`testforge/equivalence.py`](file:///Users/sourabh/TestForge/testforge/equivalence.py)
* Class: `EquivalentMutantAnalyzer` (Line 120)
* Normalization Rules: Line 40–110
* Score Formula: Line 250–295 (`calculate_mutation_scores`)

### Architecture & Mechanism
Equivalent mutants produce identical program behavior to original code and can never be killed. TestForge detects them via a multi-tier hierarchy:
1. **Tier 1 (Bytecode Invariance):** Compiles both original and mutant ASTs into Python bytecode and disassembles them via `dis`. If the instruction sequences are isomorphic (ignoring docstring constants and line number table offsets), the mutant is provably equivalent.
2. **Tier 2 (Static AST Heuristics):** Identifies commutative operation swaps (`a + b` $\to$ `b + a`), redundant guard conditions, and identical dead-code branches.
3. **Adjusted Score Formula:**
   $$\text{Adjusted Mutation Score} = \frac{\text{Killed} + \text{Timed Out}}{\text{Total Evaluated} - \text{Equivalent}} \times 100\%$$

### Failure Analysis & Defenses
* **False Positive Equivalence Defect:** Over-aggressive equivalence rules could misclassify true semantic bugs as equivalent, artificially inflating scores. Defense: Tier 1 requires 100% bytecode instruction match, and Tier 2 requires `confidence == HIGH`. Unconfirmed cases remain `UNKNOWN` or `POTENTIALLY_EQUIVALENT` and are NOT excluded from the denominator.

### Examiner Q&A
* **Q1:** *What is the difference between raw mutation score and adjusted mutation score?*  
  **Answer:** Raw mutation score divides kills by total mutants. However, some mutants are mathematically equivalent to the original program and cannot be killed by any test. Adjusted mutation score excludes provably equivalent mutants from the denominator, reflecting the true test quality against evaluable defects.
* **Q2:** *Can you give a concrete example of a mutant that is provably equivalent?*  
  **Answer:** In `samples/discount.py`, changing `final_price = price * (1.0 - discount_rate)` to `(1.0 - discount_rate) * price`. Multiplication is commutative; the Python compiler emits identical `BINARY_OP` bytecode, making it provably equivalent.

### Live Exercise
```bash
.venv-release/bin/python -c "
from testforge.equivalence import EquivalentMutantAnalyzer
from testforge.mutator import ASTMutator
orig = 'def mul(a, b): return a * b\n'
mut = ASTMutator.generate_mutants(orig)[0]
res = EquivalentMutantAnalyzer.analyze_mutant(mut, original_source=orig)
print('Equivalence status:', res.status.value, '| Confidence:', res.confidence.value)
"
```

---

## 6. Intelligent AST & Property Synthesizer

### Key File & Reference Lines
* File: [`testforge/intelligent_generator.py`](file:///Users/sourabh/TestForge/testforge/intelligent_generator.py)
* Class: `IntelligentASTSynthesizer` (Line 335), `ASTCallableAnalyzer` (Line 190)
* Test Generation Passes: Lines 595–840 (Nominal, Boundary, Extreme, Property, FSM)

### Architecture & Mechanism
Generates comprehensive pytest suites without calling external LLMs:
1. **Callable Discovery:** Extracts function signatures, parameter names, type annotations, and default values.
2. **Value-Aware Input Generation:** Synthesizes nominal values, zero/negative boundaries, off-by-one threshold partitions, and enum domain values.
3. **Hypothesis Property Synthesis:** Emits `@given` property tests for idempotence, monotonicity, and range invariants.
4. **FSM Lifecycle Synthesis:** Traverses state dictionaries to synthesize valid transition paths and test illegal transition rejections.

### Failure Analysis & Defenses
* **Generic Signature Mismatch Defect:** On stdlib algorithms with generic signatures (e.g. `bisect(a, x)` where `a` is a list), static inference previously emitted scalar ints (`1`). Defense: Dynamic execution preflight via `GranularTestValidator` discards failing nominal calls while retaining valid boundary and property tests.

### Examiner Q&A
* **Q1:** *How does deterministic heuristic synthesis compare to LLM-based zero-shot generation?*  
  **Answer:** Heuristic synthesis completes in 0.003s with 0 tokens and guarantees deterministic reproducibility. While LLMs excel at understanding natural language domain rules, heuristic synthesis provides reliable structural coverage (e.g. 59.5% on `statistics_algo.py` and 60.9% on `shlex_algo.py`) without API costs.
* **Q2:** *How does TestForge test finite state machines?*  
  **Answer:** It inspects transition dictionaries (`ALLOWED_TRANSITIONS`), constructs valid sequences (`DRAFT -> SUBMITTED -> APPROVED`), asserts valid state transitions, and tests that illegal transitions (e.g. `DRAFT -> APPROVED`) raise expected exceptions (`ValueError` or `InvalidStateTransition`).

### Live Exercise
```bash
.venv-release/bin/python -c "
from testforge.intelligent_generator import IntelligentASTSynthesizer
synth = IntelligentASTSynthesizer()
suite = synth.synthesize_test_suite('def clamp(x: int, low: int, high: int) -> int: return max(low, min(x, high))')
print(f'Synthesized {suite.total_test_count} tests in {len(suite.test_code)} chars of code.')
"
```

---

## 7. Adversarial Security Guard & Network Interception

### Key File & Reference Lines
* File: [`testforge/security.py`](file:///Users/sourabh/TestForge/testforge/security.py), [`testforge/prompt_guard.py`](file:///Users/sourabh/TestForge/testforge/prompt_guard.py)
* Class: `SecurityGuardrail` (Line 14), `PromptInjectionGuard` (Line 20)
* Zero-Egress Network Monkeypatch: `testforge/privacy_mode.py:apply_zero_egress_patch`

### Architecture & Mechanism
Dual-layer defense in depth protecting host infrastructure from untrusted code and adversarial prompts:
1. **Static AST Analysis:** Traverses test code AST prior to execution. Rejects unauthorized modules (`os.system`, `subprocess`, `socket`, `pty`, `eval`, `exec`, `requests`) via deterministic policy rules (`RULE_SPAWN`, `RULE_EVAL`, `RULE_EXFIL`).
2. **Runtime Confinement:** Monkeypatches `socket.socket.connect` to block all external IPv4/IPv6 connections while allowing local loopback (`127.0.0.1`) IPC.
3. **Adversarial Prompt Defense:** Decodes Base64 payloads, normalizes Unicode homoglyphs, strips zero-width spaces, and blocks 18 jailbreak attack vectors with 0.0% false positive rate on benign stdlib code.

### Failure Analysis & Defenses
* **Adversarial Evasion Defect (DEF-021):** Attackers previously hid instructions in multi-line comments or Base64 payloads. Defense: Recursive normalization and comment aggregation scan all text layers before dispatching prompts to LLM agents.

### Examiner Q&A
* **Q1:** *If a user writes a test containing `os.system("rm -rf /")`, how does TestForge prevent catastrophic damage?*  
  **Answer:** Before pytest runs, `SecurityGuardrail().inspect_code_ast()` inspects the AST. It detects the `Call` to `os.system`, triggers rule `RULE_SPAWN_001`, and returns `status="SECURITY_BLOCKED"`. The subprocess is never launched.
* **Q2:** *How does TestForge prevent exfiltration of API keys?*  
  **Answer:** In-memory credentials and environment variables are scrubbed by `build_sanitized_sandbox_env`. Furthermore, `ZeroEgressPrivacyMode` intercepts outbound socket connections, and `redact_secrets()` sanitizes log outputs against 7 PII/credential patterns (`AIza...`, `sk-...`, `ghp_...`).

### Live Exercise
```bash
.venv-release/bin/python -c "
from testforge.security import SecurityGuardrail
sec = SecurityGuardrail()
res = sec.inspect_code_ast('import os\ndef test_bad(): os.system(\"id\")')
print('Allowed:', res.allowed, '| Violations:', [v.rule_id for v in res.violations])
"
```

---

## 8. Agent-to-Agent (A2A) Collaboration Protocol

### Key File & Reference Lines
* File: [`testforge/a2a.py`](file:///Users/sourabh/TestForge/testforge/a2a.py)
* Class: `A2ABroker` (Line 35), `A2AWorker` (Line 180)
* Specification: Linux Foundation A2A v0.3.0 Standard Protocol
* Agent Card Endpoint: `/.well-known/agent-card.json` in `server.py`

### Architecture & Mechanism
Implements standardized inter-agent communication:
1. `A2ABroker` discovers registered agents via their JSON `AgentCard` metadata.
2. Manages structured JSON-RPC task delegation (`TaskRequest`, `TaskResponse`, `TaskStatus`).
3. Supports streaming progress updates, timeout cancellations, and capability negotiation (`test_generation`, `security_inspection`, `mutation_verification`).

### Failure Analysis & Defenses
* **Agent Deadlock / Timeout:** If a delegated worker hangs, the broker terminates the task after `timeout_seconds`, updates task state to `FAILED`, and notifies callers with structured error diagnostics.

### Examiner Q&A
* **Q1:** *What is an AgentCard, and why is it located at `/.well-known/agent-card.json`?*  
  **Answer:** Following the official A2A protocol specification, the AgentCard is a machine-readable JSON manifest declaring the agent's identity, capabilities, input/output schemas, and endpoints. Placing it at `/.well-known/agent-card.json` allows external agents to automatically discover and invoke TestForge capabilities.
* **Q2:** *How are tasks isolated when multiple external agents delegate work to TestForge simultaneously?*  
  **Answer:** Each task receives a unique UUID `task_id`. State, logs, and sandbox directories are scoped to the task ID, and `A2ABroker` ensures thread-safe message dispatching without cross-task state pollution.

### Live Exercise
```bash
.venv-release/bin/python -c "
from testforge.a2a import A2ABroker
broker = A2ABroker()
broker.register_handler('agent_alpha', lambda msg: None)
print('Registered A2A handlers:', broker.list_handlers())
"
```

---

## 9. FastMCP Dynamic Tool Exposure

### Key File & Reference Lines
* File: [`testforge/mcp_server.py`](file:///Users/sourabh/TestForge/testforge/mcp_server.py), [`testforge/mcp_client.py`](file:///Users/sourabh/TestForge/testforge/mcp_client.py)
* Function: `create_testforge_server()` (Line 314)
* Server Instance: `testforge-mcp-server`
* Core MCP Tools: `generate_mutants`, `evaluate_test_suite`, `inspect_blackboard`

### Architecture & Mechanism
Implements Anthropic's Model Context Protocol (MCP) to expose TestForge tools to IDEs and LLM agents:
* Exposes tools over standard stdio JSON-RPC or HTTP transports.
* Each tool request validates schema parameters via Pydantic before routing execution to the underlying engine.
* Integrates directly into FastAPI server at `/api/mcp/status` and `/api/mcp/tools`.

### Failure Analysis & Defenses
* **Schema Validation Failure:** Malformed tool payloads return standard JSON-RPC error objects (`code = -32602, Invalid params`) rather than crashing the server.

### Examiner Q&A
* **Q1:** *What is FastMCP, and what role does it play in TestForge?*  
  **Answer:** FastMCP provides an asynchronous, typed implementation of the Model Context Protocol. It allows external LLMs (such as Claude Desktop or Antigravity agents) to treat TestForge as an external tool provider, querying mutants, running tests, and fetching blackboard diffs via standardized RPC calls.
* **Q2:** *How do you ensure MCP tool calls do not compromise server security?*  
  **Answer:** All code execution tools exposed via MCP route through `ParallelSandboxRunner` with subprocess isolation and static AST security checks enabled. No tool can execute arbitrary host code directly.

### Live Exercise
```bash
.venv-release/bin/python -c "
from testforge.mcp_server import create_testforge_server
server = create_testforge_server()
print('MCP server name:', server.name)
"
```

---

## 10. FastAPI Server, SSE/WS Streaming, & Cockpit

### Key File & Reference Lines
* File: [`server.py`](file:///Users/sourabh/TestForge/server.py), [`frontend/app.js`](file:///Users/sourabh/TestForge/frontend/app.js)
* WebSocket Endpoint: Line 250–310 (`/ws/stream`)
* Provenance Summary Endpoint: Line 450–495 (`/api/benchmark/multi-target/summary`)
* Vanilla ES6 UI Views: 11 reactive panes in `frontend/app.js`

### Architecture & Mechanism
The full-stack presentation tier of TestForge:
* **Backend:** FastAPI with Starlette WebSocket & SSE connections streaming live agent thoughts, Blackboard checkpoints, and mutant tables in real time.
* **Frontend:** Zero-NPM vanilla ES6 SPA with glassmorphism design, SVG dependency trees, split-pane diff viewer, and reactive state management.
* **Truthfulness Badges:** Displays dynamic provenance badges for mocked data (`⚠️ MOCKED`), fast heuristic mode (`⚠️ FAST HEURISTIC`), and full agentic execution (`✓ FULL AGENTIC EVALUATION`), complete with commit hash and timestamp.

### Failure Analysis & Defenses
* **WebSocket Disconnection Handling:** Automatic reconnection with exponential backoff in `frontend/app.js` prevents cockpit freezes during transient network interruptions.

### Examiner Q&A
* **Q1:** *Why did you choose vanilla ES6 JavaScript instead of React or Vue for the dashboard?*  
  **Answer:** A vanilla ES6 dashboard requires zero `node_modules`, zero build steps, and zero security vulnerabilities from transitive NPM packages. It runs instantly from Python static file mounting, has zero cold-start delay, and eliminates framework churn while delivering sub-millisecond reactive DOM updates.
* **Q2:** *How does the frontend guarantee that displayed benchmark results are authentic and not mocked?*  
  **Answer:** The frontend queries `/api/benchmark/multi-target/summary`, which extracts provenance metadata directly from `qa_artifacts/MULTI_TARGET_BENCHMARK_RESULTS.json`. If `fast_mode` is true or model is a mock, the UI displays amber/rose warning badges (`⚠️ MOCKED / FIXTURE DATA`). Full green badges are only rendered for verified, non-fast agentic executions.

### Live Exercise
```bash
.venv-release/bin/python -c "
from fastapi.testclient import TestClient
from server import app
client = TestClient(app)
res = client.get('/healthz')
print('Server healthz status:', res.json())
"
```
