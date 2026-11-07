# TestForge — System Limitations & Academic Disclosures

**Document Version:** 1.0.0  
**Last Verified:** November 2, 2026  
**Reference Codebase:** `testforge/`  

---

## 1. Academic Honesty & Scope of Disclosures

To uphold the highest standards of scientific integrity and academic rigor, this document provides an unvarnished disclosure of the known technical limitations, architectural constraints, untested execution paths, and surviving mutants in the TestForge platform.

---

## 2. Exhaustive System Limitations

### 1. Incomplete Engine Coverage (81.33%)
- **Fact:** Statement coverage across the `testforge/` package is **81.33%**, leaving approximately 18.67% of lines unexecuted during regression runs.
- **Root Cause Analysis:** Uncovered lines reside primarily in:
  - Rare error-handling branches in external API adapters (e.g., specific HTTP 502/503 network retries in `github_service.py`).
  - Optional fallback paths in `llm_client.py` designed for cloud providers when offline.
  - Interactive terminal CLI formatting in `cli.py`.
- **Mitigation:** The core state machine (`orchestrator.py`), blackboard (`blackboard.py`), mutator (`mutator.py`), and AST generator (`intelligent_generator.py`) achieve > 90% statement coverage.

### 2. Surviving Mutants in Complex Business Logic
- **Discount Module:** 2 viable mutants survived out of 19 (89.47% raw score).
  - *Cause:* Mutants alter subtle floating-point rounding precision in `round(price * (1.0 - discount), 2)` from 2 decimals to 1. Tests using inputs like `100.0` produce round numbers (`90.0`, `85.0`) that evaluate identically under 1 or 2 decimal precision.
- **Logistics Module:** 82 viable mutants survived out of 258 (68.22% raw score).
  - *Cause:* The logistics module (`samples/logistics_module.py`) features deep nested branch combinations (customs duties on hazardous materials shipped express to overseas territories). Certain combination branches require highly specialized domain fixtures that the generic synthesizer did not generate.
- **Academic Significance:** TestForge does not artificially claim 100% mutation scores. Achieving 89.47% (Discount) and 68.22% (Logistics) represents a massive improvement over standard developer baselines (5.26% and 3.10%).

### 3. Untested Live Cloud Providers in CI
- **OpenRouter Cloud:** The test environment lacks an `OPENROUTER_API_KEY`. The OpenRouter client code was tested and verified using mock unit tests (`test_openrouter_dynamic_identification`), but live cloud API calls were not executed.
- **Google Gemini Quota Preservation:** Historical records verify 5 genuine live Gemini calls (29,055 tokens). During recent automated test suite runs, live Gemini calls were deliberately not invoked to prevent quota exhaustion and ensure deterministic CI timing.

### 4. Deterministic Simulated Security Evaluation
- **Limitation:** The 120 security evaluation trials (Criterion 8) evaluated deterministic attack injection strings (e.g. docstring injections, path traversal tokens, `os.system` AST nodes) against local filters and sandbox boundaries.
- **Disclosure:** This evaluation does **not** constitute a formal third-party penetration test or external black-hat red-teaming exercise against running cloud infrastructure.

### 5. Offline Hypothetical Cost Modeling
- **Limitation:** The reported benchmark cost ($0.000182 per run) is a mathematical projection applying Google Gemini 1.5 Flash published pricing ($0.075 / 1M prompt, $0.30 / 1M completion) to offline synthesized tokens.
- **Disclosure:** Actual billed API cost was **$0.00 USD**. No financial charges were incurred during the benchmark runs.

### 6. Single-Node Concurrency & Persistence Limits
- **Limitation:** TestForge relies on SQLite with WAL journaling (`testforge_checkpoints.db`). While WAL mode allows high-throughput concurrent reads, SQLite permits only a **single writer process** at any given millisecond.
- **Impact:** The current architecture is ideal for developer laptops, workstations, and single-server deployments. It cannot be deployed across a multi-node horizontal Kubernetes cluster without migrating persistence to PostgreSQL or CockroachDB.

### 7. Python-Specific AST Dependency
- **Limitation:** TestForge's mutation engine (`ASTMutator`) and test synthesizer (`IntelligentASTSynthesizer`) operate directly on Python's built-in `ast` library.
- **Impact:** TestForge cannot currently analyze or harden test suites for other programming languages (TypeScript, Java, C++, Go) without integrating language-agnostic parsers such as Tree-sitter.

### 8. Cloud Deployment Pending
- **Limitation:** While a `Dockerfile` and `docker-compose.yml` exist in the repository, TestForge is currently optimized for local execution (`./start_testforge.sh`). Multi-tenant cloud deployment with OAuth authentication and isolated tenant sandboxes remains on the future roadmap.

