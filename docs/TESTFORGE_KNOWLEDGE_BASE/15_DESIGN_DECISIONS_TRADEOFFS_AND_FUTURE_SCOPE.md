# TestForge — Architectural Design Decisions, Trade-offs & Future Scope

**Document Version:** 1.0.0  
**Last Verified:** November 2, 2026  
**Reference Codebase:** `testforge/`  

---

## 1. Deep Dive into Major Design Decisions

### 1. Why a Multi-Agent Architecture Instead of a Monolithic Script?
- **Problem Solved:** Automated software hardening requires diverse, conflicting cognitive tasks: static code analysis, creative assertion synthesis, adversarial fault detection, and execution sandboxing. Combining these into a single monolithic script creates unmaintainable, brittle code where a prompt change to improve boundary checks degrades security filtering.
- **Alternatives Considered:** Monolithic procedural script, chain-of-thought single LLM prompt, LangChain linear chain.
- **Selected Approach:** Specialized autonomous agents (`TargetManagerAgent`, `TestGeneratorAgent`, `AdversarialCriticAgent`, `TestForgeOrchestrator`).
- **Benefits:** Clean separation of concerns. The generator focuses entirely on maximizing coverage; the critic acts as an uncompromising adversary trying to break the generator's assertions.
- **Trade-offs:** Introduces coordination overhead and requires structured inter-agent state management.

---

### 2. Why a Blackboard Pattern Instead of Parameter Passing?
- **Problem Solved:** Passing large source files, AST signatures, hundreds of mutant records, test execution logs, and reflection notes as function arguments across multiple agent layers causes severe context bloat, type fragility, and debugging opacity.
- **Alternatives Considered:** Deep function parameter passing, shared global dictionary, Redis cache, distributed message broker (RabbitMQ/Kafka).
- **Selected Approach:** Thread-safe, in-process Blackboard (`testforge/blackboard.py`) with 5 typed Pydantic partitions (`TargetSpace`, `SuiteSpace`, `MutantSpace`, `CriticSpace`, `MetricsSpace`).
- **Benefits:**
  - Zero context serialization overhead between in-process agents.
  - Complete point-in-time snapshotting (`BlackboardSnapshot`) enabling time-travel rollbacks.
  - Independent read/write permissions per partition.
- **Trade-offs:** Requires strict concurrency locking (`threading.RLock`) to prevent race conditions during concurrent worker updates.

---

### 3. Why Mutation Testing as the Primary Hardening Metric?
- **Problem Solved:** Statement coverage only proves that code executed, not that faults were caught. A single test asserting `assert True` achieves 100% statement coverage on any function without detecting a single bug.
- **Alternatives Considered:** Branch coverage, cyclomatic complexity metrics, property-based testing (Hypothesis), fuzzing.
- **Selected Approach:** Native AST Mutation Testing (`testforge/mutator.py`).
- **Benefits:** Injects real syntactic faults (boundary shifts, arithmetic flips, boolean inversions) and measures the exact proportion killed by test assertions.
- **Trade-offs:** Computationally expensive; running 258 mutants requires 258 test subprocess executions. Mitigated by parallel batching, fast-fail execution, and conservative equivalent mutant exclusion.

---

### 4. Why Deterministic AST Synthesis Fallback (Tier 4)?
- **Problem Solved:** Relying exclusively on cloud LLMs (Gemini, OpenAI) introduces major liabilities: API rate limits, paid quota exhaustion, network outages, and non-deterministic test outputs that break automated regression suites.
- **Alternatives Considered:** Hard failure on API outage, retrying cloud requests indefinitely, mocking LLM responses with static string templates.
- **Selected Approach:** `IntelligentASTSynthesizer` with `ReferenceExecutor` (`testforge/intelligent_generator.py`).
- **Benefits:**
  - 100% offline capability.
  - Generates valid, boundary-rich Pytest suites in under 0.5 seconds with **zero API cost and zero tokens**.
  - Guarantees assertion truth by running pre-flight reference executions against clean target code before writing the test.
- **Trade-offs:** Cannot understand deep business domain semantics (e.g. knowing that a user named "admin" should have elevated permissions) as well as a multi-billion parameter LLM.

---

### 5. Why SQLite with WAL Mode Instead of PostgreSQL or In-Memory?
- **Problem Solved:** TestForge needed durable persistence for state checkpoints, audit logs, and time-travel rollbacks without forcing users to install, configure, and maintain an external database server like PostgreSQL or MySQL.
- **Alternatives Considered:** In-memory dictionary, serialized JSON files on disk, PostgreSQL, MongoDB.
- **Selected Approach:** Local SQLite database (`qa_artifacts/testforge_checkpoints.db`) with Write-Ahead Logging (`PRAGMA journal_mode=WAL;`).
- **Benefits:**
  - Zero configuration: Runs out-of-the-box on macOS and Linux.
  - High concurrency: WAL mode allows concurrent readers to query telemetry without blocking the orchestrator writer.
  - Durability: Survives server restarts and process crashes (1,310 checkpoints safely preserved).
- **Trade-offs:** Not suitable for multi-node horizontal clustering; perfectly optimized for single-host and developer workstation deployment.

---

### 6. Why Subprocess Sandboxing Instead of Per-Run Docker Containers?
- **Problem Solved:** Executing dynamically generated test code and AST mutants is inherently risky (infinite loops, memory bombs, system calls).
- **Alternatives Considered:** Docker container per mutant, WebAssembly sandbox (Wasmtime), Python `exec()` with restricted globals.
- **Selected Approach:** Native isolated Python subprocesses with resource limits and timeouts (`testforge/sandbox.py`).
- **Benefits:**
  - Spin-up latency is < 100 milliseconds (Docker container spin-up takes 1.5–3.0 seconds per mutant, which would make running 258 mutants take over 10 minutes).
  - Enforces strict process isolation, timeouts (10.0s), and directory boundaries.
- **Trade-offs:** Subprocess isolation does not provide the absolute kernel-level filesystem virtualization of a hardened Docker container against malicious root-level exploits.

---

### 7. Why Vanilla JavaScript Without React or Node.js?
- **Problem Solved:** Modern frontend frameworks (React, Vue, Next.js) introduce gigabytes of `node_modules`, complex build pipelines (Webpack, Vite), and breaking dependency churn.
- **Alternatives Considered:** React + TypeScript, Vue.js, Streamlit, HTMX.
- **Selected Approach:** Clean vanilla HTML5, CSS variables, and ES2022 JavaScript (`frontend/app.js`).
- **Benefits:**
  - Zero build step: Change a line of code, refresh the browser, and it runs immediately.
  - Ultra-fast load times (< 50ms) and zero external runtime dependencies.
  - Complete control over DOM updates, WebSocket streaming, and Server-Sent Events.
- **Trade-offs:** Requires manual DOM manipulation instead of declarative state-to-DOM binding.

---

### 8. Why Separate Actual vs Estimated Token Accounting?
- **Problem Solved:** Previous iterations of the dashboard lumped heuristic offline token counts together with genuine cloud API calls, misleading users into believing that 50,000 paid cloud tokens had been consumed when tests were generated offline.
- **Alternatives Considered:** Reporting only total tokens, reporting only cloud tokens.
- **Selected Approach:** Strict dual-accounting in `TraceLogger`:
  - `actual_llm_tokens`: Billed tokens reported directly by Gemini or Ollama.
  - `estimated_tokens`: Heuristic token counts computed offline for AST runs.
- **Benefits:** Absolute academic and financial transparency. Deterministic runs strictly report `actual_llm_tokens = 0`.
- **Trade-offs:** Requires maintaining dual aggregation logic across the logging and frontend layers.

---

## 2. Limitations & Future Research Roadmap

| Current Limitation | Technical Cause | Future Roadmap Solution |
| :--- | :--- | :--- |
| **Python-Only Target Support** | The mutator and callable analyzer operate directly on Python's native `ast` library. | Implement Tree-sitter multi-language grammar parser to support TypeScript, Go, and Java. |
| **Equivalent Mutant Manual Verification**| Conservative heuristics catch dead code, but subtle mathematical equivalences require human inspection. | Train a lightweight graph neural network (GNN) classifier to detect equivalent mutants automatically. |
| **Subprocess Execution Isolation**| Subprocesses run with user privileges on the host machine. | Implement lightweight microVM isolation (e.g. Firecracker or Docker-in-Docker) for untrusted enterprise deployments. |
| **Local Model Memory Footprint**| Running 7B models (`codellama:7b`) requires 16GB RAM and Apple Silicon Metal acceleration. | Integrate 4-bit AWQ / GGUF quantization (e.g. `qwen2.5-coder:1.5b-q4`) for low-spec 8GB developer laptops. |
| **Cloud Deployment Pending** | The application is optimized for local workstation execution; cloud deployment remains on the roadmap. | Containerize using Kubernetes Helm charts with decoupled Redis state and Postgres persistence. |

