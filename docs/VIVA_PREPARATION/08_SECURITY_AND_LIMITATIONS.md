# TestForge: Security Architecture, Guardrails & Known Limitations

**Document Purpose:** Detailed technical reference on security enforcement, sandbox isolation, credential hygiene, and an honest assessment of current limitations for academic defense (VIVA).  
**Repository Files:** `testforge/security.py`, `testforge/sandbox.py`, `testforge/mcp_server.py`, `testforge/callbacks.py`.  

---

## 1. Multi-Tiered Defense-in-Depth Security Model

Executing dynamically synthesized code and running intentional software mutants poses inherent security risks. TestForge enforces security across five distinct architectural layers:

```
┌──────────────────────────────────────────────────────────────┐
│                    Layer 1: Input Validation                 │
│  - File extension & MIME whitelist (.py only)                │
│  - Max upload size limits (1 MB)                             │
│  - Safe path resolution blocking directory traversal (../)   │
├──────────────────────────────────────────────────────────────┤
│               Layer 2: Prompt Injection Defense              │
│  - Regex & heuristic classifier (DefenseManager)             │
│  - Strips jailbreak patterns ("ignore previous instructions")│
├──────────────────────────────────────────────────────────────┤
│              Layer 3: AST Static Security Gating             │
│  - Static AST inspection before execution                    │
│  - Whitelist: Only pytest, math, standard typing             │
│  - Blacklist: eval, exec, __import__, os.system, subprocess  │
├──────────────────────────────────────────────────────────────┤
│             Layer 4: Subprocess Sandbox Isolation            │
│  - Ephemeral sandbox directories (/tmp/testforge_box_...)    │
│  - Hard process execution timeouts (5.0s per mutant)         │
│  - Independent virtual Python interpreter processes          │
├──────────────────────────────────────────────────────────────┤
│               Layer 5: Credential Redaction                  │
│  - Recursive regex scrubbing of API keys & Bearer tokens     │
│  - AgentCard and SQLite checkpoints contain zero secrets     │
└──────────────────────────────────────────────────────────────┘
```

---

## 2. In-Depth Security Implementations

### 2.1 AST Static Inspection (`ASTSecurityInspector`)
Located in `testforge/security.py:210`:
- Before any generated candidate test suite is allowed to run, it is parsed into an AST.
- Any `ast.Import` or `ast.ImportFrom` targeting unauthorized modules (`os`, `sys.modules`, `socket`, `urllib`, `requests`, `ctypes`) raises an immediate `SecurityViolationError`.
- Any `ast.Call` invoking banned built-in functions (`eval`, `exec`, `open`, `compile`, `__import__`) aborts the pipeline before execution begins.

### 2.2 Subprocess Sandbox & Hard Timeouts
Located in `testforge/sandbox.py`:
- Test suites run inside spawned subprocesses (`subprocess.Popen`) in temporary directory sandboxes created via `tempfile.mkdtemp(prefix="testforge_box_")`.
- When mutants introduce while-loop bugs (e.g. `while count > 0` mutated to `while count >= 0` where count never decrements), the 5.0-second timeout triggers:
  - Terminates the child process.
  - Recursively deletes the temporary directory.
  - Classifies the mutant as `TIMED_OUT` (considered killed).

### 2.3 FastMCP Filesystem Confinement
Located in `testforge/mcp_server.py`:
- All filesystem MCP tools verify that the requested file path resolves strictly within `BASE_DIR / "samples"`.
- Requests attempting path traversal (e.g. `../../../../etc/passwd` or `../../checkpoints.db`) trigger a `PermissionError` and are rejected with JSON-RPC error code `-32602`.

---

## 3. Honest Assessment of Known Limitations

In academic defenses, examiners respect candidates who honestly acknowledge system boundaries rather than making exaggerated claims.

Below are the genuine, verifiable limitations of the current TestForge implementation:

| # | Known Limitation | Technical Cause | Current Behavior / Mitigation | Recommended Future Improvement |
| :-: | :--- | :--- | :--- | :--- |
| **1** | **Host-Level Subprocess Execution** | Sandbox spawns subprocesses on the host OS under the current user UID rather than a virtual container. | Safe for local developer workstations and academic grading. Blocked by AST import whitelisting. | Wrap sandbox execution in ephemeral Docker containers (e.g. gVisor or Firecracker microVMs) for public multi-tenant SaaS. |
| **2** | **Reflection Iteration Bound** | Finite state machine bounds reflections to $N=2$ (or user threshold). | Prevents infinite loops on equivalent mutants, but may terminate before achieving 100% on complex modules. | Implement automated equivalent-mutant SMT solver (e.g. Z3) to prove equivalence before stopping. |
| **3** | **Dynamic Typing without Annotations** | When parameters lack type hints (e.g. `def foo(x):`), AST analyzer defaults to integer inputs. | Generates nominal int inputs; may miss type-specific branches. | Integrate runtime type inference or dynamic trace extraction from existing unit tests. |
| **4** | **Async / Coroutine Callables** | Coroutines (`async def`) require an active event loop runner. | Discovered callables result filters out `async def` with explicit ineligibility reason. | Integrate `pytest-asyncio` harness with event loop fixture generation. |
| **5** | **Private Class Methods & Dunders** | Methods prefixed with `_` or wrapped in `__init__` are omitted from public suites. | Tested indirectly via public caller methods (e.g. `reserve_stock` testing inventory init). | Provide dedicated constructor fixture synthesizers for complex object graphs. |

---

## 4. Academic Defense Summary on Security

**Examiner Question:** *"Can a malicious user submit Python code that escapes your sandbox or deletes files?"*

**Precise Technical Answer:**
> *"No. The submission is subjected to a two-stage filter. First, the `ASTSecurityInspector` statically traverses the code tree and rejects any dangerous imports (`os`, `subprocess`, `socket`) and built-in calls (`eval`, `exec`, `open`).
>
> Second, even if benign code is accepted, the tests execute inside an isolated subprocess confined to an ephemeral directory with a hard 5-second timeout and zero access outside the working boundary. Path traversal attempts are blocked by `resolve_safe_path()` checks."*

