# TestForge — Known Limitations and Risk Review

**Audit Date:** 2026-10-23  
**Status:** Documented & Transparently Classified  
**Policy:** No artificial suppression of compiler or test warnings; full engineering disclosure.

---

## 1. Classification Matrix of Known Issues

| Issue / Limitation | Root Cause | Severity / Category | Impact on System | Recommended Mitigation |
| :--- | :--- | :--- | :--- | :--- |
| **CrewAI Deprecation Warnings (208 count in pytest)** | Upstream CrewAI 0.102.0 using deprecated Pydantic v1 argument conventions (`function_calling_llm`, `allow_code_execution`) | **Future Compatibility Risk** | Zero impact on Python 3.13 / test suite (all 309 tests pass). Will require update when CrewAI releases v1.0. | Do not suppress globally. Plan upgrade when CrewAI reaches stable 1.0. |
| **Google Cloud Vertex AI Warning** | Upstream Google Cloud AI platform deprecation of legacy model garden imports | **Cosmetic / Informational** | Non-breaking warning printed once during client import in vertex environment. | Update import path when upgrading Google GenAI SDK. |
| **Fast Benchmark Mode is Offline Simulation** | Deterministic mock fixtures in `testforge/benchmark_fast_mode.py` | **Design Constraint / Simulation Disclosure** | Enables sub-second CI validation without API billing, but does not reflect real cloud LLM latency or non-deterministic variance. | Always disclose `--fast` as offline simulated mode in demonstrations and viva. |
| **Equivalent Mutant Undecidability** | Program equivalence is mathematically undecidable (Rice's Theorem / Halting Problem) | **Theoretical Limitation** | Static AST heuristic rules detect syntactic tautologies, but cannot detect semantic equivalence in arbitrary state machines. | Disclose heuristic bounds; use denominator adjustment in mutation score calculation. |
| **Apple Silicon MLX Backend Requirements** | MLX requires Apple Silicon hardware (M1/M2/M3/M4) and `mlx-lm` library | **Platform Dependency / Hardware Requirement** | If local MLX model fallback is requested on Linux x86 or Intel Macs, system gracefully falls back to Ollama or cloud LLM. | Tested cascade handles fallback; document hardware requirements for local neural inference. |
| **Subprocess Sandbox Multi-Tenancy** | `testforge/executor.py` uses OS-level child subprocesses with timeouts and directory isolation | **Security / Reliability Consideration** | Strong protection against accidental infinite loops on a developer workstation; insufficient for hostile untrusted multi-tenant SaaS hosting. | For cloud SaaS deployment, wrap executor in gVisor, WebAssembly, or Docker MicroVM containers. |

---

## 2. Detailed Technical Breakdown

### Issue 1: CrewAI Deprecation Warnings
* **Observation:** Running `.venv-release/bin/python -m pytest tests/ -q` produces `309 passed, 208 warnings`.
* **Warning Trace:**
  ```text
  UserWarning: The argument `function_calling_llm` is deprecated and will be removed in future releases.
  UserWarning: The argument `allow_code_execution` is deprecated in Agent and will be removed.
  ```
* **Analysis:**
  These warnings are emitted from the internal constructors of `crewai.Agent` within the vendor package `site-packages/crewai/`. TestForge code imports and initializes agents according to CrewAI 0.102.0 public API documentation.
* **Why We Refuse to Suppress:**
  Global warning filters (e.g. `python -W ignore`) hide genuine deprecation notices and can mask unexpected bugs introduced in other dependencies. In accordance with professional engineering ethics, these are disclosed as upstream library maintenance items.
* **Verdict:** Safe for evaluation and deployment on Python 3.13.

### Issue 2: Offline Fast Benchmark Disclosure
* **Observation:** `run_benchmark.py --fast -r 5` executes 5 iterations in 0.08 seconds.
* **Analysis:**
  The `--fast` flag switches the benchmark runner from making live external API requests (which take 5–15 seconds per call and cost money) to using local deterministic mock fixtures (`testforge/benchmark_fast_mode.py`).
* **Ethical Disclosure:**
  The fast benchmark is an integration and pipeline harness. It must never be presented to an evaluator as a real-time measurement of LLM inference latency. It verifies that the mutation score calculation, survival rate aggregation, and table generation work accurately under rapid conditions.

### Issue 3: Theoretical Limits of Mutation Testing
* **Observation:** Surviving mutants may include semantically equivalent programs that cannot be killed by any valid test case.
* **Example:**
  ```python
  # Original:
  if x >= 0: return abs(x)
  # Mutant:
  if x > -1: return abs(x) # (for integer domain)
  ```
* **Analysis:**
  Because proving equivalence between arbitrary algorithms is reducible to the Halting Problem, no static or dynamic tool can ever guarantee 100% equivalent mutant detection.
* **TestForge Mitigation:**
  `testforge/ast_engine.py` implements syntactic heuristic filters (`is_equivalent_mutant`) that catch trivial identity operations ($x \cdot 1$, $x + 0$, boolean tautologies). The mutation score formula explicitly subtracts detected equivalent mutants from the denominator.

### Issue 4: Local Sandboxing vs Multi-Tenant Cloud Isolation
* **Observation:** `testforge/executor.py` spawns `subprocess.run(["pytest", ...], timeout=...)` in an ephemeral temporary directory.
* **Analysis:**
  This architecture safely catches:
  - Infinite loops (aborted via timeout)
  - Memory exhaustion (bounded by OS limits)
  - Accidental relative path collisions (isolated to `tempfile.TemporaryDirectory()`)
* **Limitation:**
  A malicious user with arbitrary Python code execution could theoretically attempt OS-level privilege escalation or local network scanning if running on a shared server. For multi-tenant production hosting, containerized sandboxes (e.g. gVisor or Docker MicroVMs) would be required. For developer workstation usage (the project's target scope), the current sandbox is completely adequate.
