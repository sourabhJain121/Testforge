# TestForge Viva Package: Examiner Q&A Defense

This document compiles anticipated technical examination questions, architectural trade-offs, and empirical defenses for the TestForge viva examination.

---

### Q1: Why did you choose a dual-framework architecture (Google ADK + CrewAI) instead of building exclusively in one?
**Defense:**
Different agentic frameworks are optimized for different concerns:
- **Google ADK** provides robust low-level orchestration, state machine transitions, native `Runner` constructs, `DatabaseSessionService` (SQLite WAL), and granular lifecycle callbacks (`before_tool_callback`, `after_model_callback`).
- **CrewAI** provides role-playing abstractions with backstories, goals, and adversarial reasoning ideal for the Critic specialist.
- Pairing them through the **Official Agent2Agent (A2A v0.3.0) Wire Protocol** satisfies the core curriculum mandate to demonstrate genuine interoperability across distinct agent ecosystems rather than relying on a proprietary in-process bus.

---

### Q2: What is the Coverage-Kill Gap, and why is line coverage an insufficient metric for software verification?
**Defense:**
Line coverage measures *execution*, not *assertion depth*. A single hollow test like:
```python
def test_discount():
    calculate_discount(100.0, 5, True)  # Executes 100% of lines without asserting state!
```
achieves 100% line coverage while killing **0% of mutants**.
In our empirical baseline evaluation across 4 targets (`qa_artifacts/MULTI_TARGET_BENCHMARK_RESULTS.json`):
- Baseline tests had **30.75% line coverage** but only **6.46% raw mutation score**.
- Zero-shot LLM tests reached **39.17% line coverage** but only **32.58% raw mutation score**.
- TestForge closed the gap, achieving **70.58% line coverage** and **67.02% raw mutation score (70.17% adjusted)**, killing 167/240 mutants.

---

### Q3: How does TestForge solve the Equivalent Mutant Problem?
**Defense:**
Equivalent mutants mutate syntax without altering semantics (e.g. replacing `x in (1, 2)` with `x in [1, 2]`, or mutating dead-code fallback branches). Standard systems treat these as surviving mutants, capping mutation scores and trapping reflection agents in infinite loops.
TestForge uses a 2-tier defense:
1. **Tier 1 (Recursive Bytecode Normalization)**: Normalizes bytecode via Python's `dis` module and compares instruction streams and code objects. Proves compiler-level equivalence with **0.0% false positive rate**.
2. **Tier 2 (LLM Equivalence Judge)**: Classifies behavioral invariants.
On `order_fsm.py`, identifying 3 verified dead-code equivalent mutants adjusted the score from 97.17% raw to **100.0% adjusted**, allowing the reflection loop to terminate cleanly.

---

### Q4: How do you guarantee safety when executing LLM-generated Python code?
**Defense:**
We enforce defense-in-depth across three layers:
1. **Static AST Guardrails**: Pre-execution AST walk blocks unauthorized network, socket, or process modules (`os.system`, `subprocess`, `socket`).
2. **Subprocess Isolation**: Every test run executes in a detached child process with resource limits (`RLIMIT_AS`) and a hard 5.0-second timeout ceiling to kill infinite loops.
3. **Kernel Container Isolation**: On systems with Docker, tests execute in `testforge:latest` with `--network none`, unprivileged user, and read-only filesystems.
4. **Human Approval Gate**: Writing hardened test suites to the repository or opening PRs requires explicit human sign-off via `/api/approval/*`.

---

### Q5: How did you validate your custom AST mutation engine against established industry benchmarks?
**Defense:**
We benchmarked TestForge's AST mutation engine against **`mutmut v3.8.1`** (the gold-standard LibCST mutation engine for Python) across canonical targets:
- `discount.py`: 90.9% mutmut vs 94.7% TestForge
- `lru_cache.py`: 31.8% mutmut vs 31.0% TestForge
- `order_fsm.py`: 90.7% mutmut vs 97.2% TestForge
- `stats_calculator.py`: 50.7% mutmut vs 49.3% TestForge
- Macro average: **66.02% mutmut vs 68.05% TestForge**.
- Pearson correlation coefficient: **$r = 0.9988$**, proving that TestForge's deterministic AST mutator mirrors established industry engines with near-perfect fidelity.

---

### Q6: What is the benefit of the Test Suite Minimizer, and what algorithm is used?
**Defense:**
Iterative multi-turn reflection naturally introduces redundant assertions as early partial tests remain in the suite alongside comprehensive later assertions.
TestForge computes the 2D Boolean Kill Matrix $M \in \{0, 1\}^{|T| \times |K|}$ and solves the NP-hard minimum set cover problem using a greedy approximation algorithm.
Across our 4 benchmark targets, the minimizer reduced test suite size from 134 tests down to 28 tests (**79.1% reduction**) while mathematically retaining **strictly 100.0% of killed mutants** (0 lost kills).

---

### Q7: What are the documented technical limitations of TestForge?
**Defense:**
Honest scientific disclosure is central to our work:
1. **Air-Gap Latency**: While Google Gemini Flash takes ~1.5s per iteration, running entirely air-gapped on local Ollama `qwen2.5-coder:7b` requires ~15s per iteration on Apple Silicon CPU/Metal.
2. **Equivalent Mutant Undecidability**: Rice's Theorem dictates that exact semantic equivalence in arbitrary programs is undecidable. While our bytecode normalization achieves 100% precision, semantic recall is bounded at ~90%.
3. **Complex Mocking**: TestForge currently hardens standalone algorithmic modules (50-150 LOC). Hardening distributed microservices with complex database fixtures or external mock injections requires additional integration harness generators.
