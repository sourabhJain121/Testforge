# TestForge Defect Register & Resolution Log

**Date:** November 2, 2026  
**Auditor:** Senior Software Reliability & QA Engineer  
**Classification Standards:**
- **P0 — Critical:** Data corruption, security breach, application cannot start, or core pipeline dead.
- **P1 — High:** Core workflow failure, broken background worker, or critical API exception.
- **P2 — Medium:** Performance bottleneck, UI state inconsistency, or missing optimization.
- **P3 — Low:** Documentation ambiguity, minor UI Polish, or non-critical warning.

---

## 1. Defect Summary Table

| Defect ID | Severity | Subsystem | Description | Status |
| :---: | :---: | :--- | :--- | :---: |
| **`DEF-ENV-001`** | **P1 (High)** | Background Worker / TTY | Background hardening worker raised `[Errno 5] Input/output error` when writing to closed terminal. | **FIXED** |
| **`DEF-OBS-001`** | **P2 (Med)** | Observability / Telemetry | `GET /api/telemetry` took 4.69s due to dual redundant full scans of 238k JSONL lines. | **FIXED** |
| **`DEF-DOC-001`** | **P3 (Low)** | Performance Report | Apparent discrepancy between 89.47% automated adjusted and 94.44% domain-triaged score. | **RESOLVED** |
| **`DEF-DOC-002`** | **P3 (Low)** | Performance Architecture | Unclear attribution of deterministic AST test synthesis vs. live cloud LLM reasoning competition. | **RESOLVED** |

---

## 2. Detailed Defect Investigations & Remediation

### 2.1 DEF-ENV-001: Background Worker I/O Error on Closed TTY
- **Severity:** P1 (High)
- **File & Context:** `server.py` background worker invoking `TestForgeOrchestrator.run()`.
- **Symptom:** Asynchronous hardening jobs immediately failed with status `FAILED` and error `[Errno 5] Input/output error`.
- **Root Cause:** The uvicorn server process (PID 68707) had been spawned at 1:22 AM on `/dev/ttys003`. When that terminal tab was closed, file descriptors 0, 1, and 2 pointed to a dead terminal. When the orchestrator attempted to print Rich console progress tables to `sys.stdout`, the macOS kernel raised `OSError: [Errno 5] Input/output error`.
- **Reproduction:** Submitted `POST /api/harden/start`; job status transitioned to `FAILED`.
- **Resolution:** Terminated the orphaned process and launched TestForge via `./start_testforge.sh` as an independent background daemon. Retested: job completed successfully in 6.5s with status `COMPLETED` and mutation score `89.47%`.
- **Status:** **VERIFIED FIXED**

### 2.2 DEF-OBS-001: Redundant Telemetry Trace Parsing Latency
- **Severity:** P2 (Medium)
- **File & Context:** `testforge/logger.py:94` and `server.py:1571`.
- **Symptom:** `GET /api/telemetry` required 4.69 seconds to respond, causing read timeout exceptions on 5-second HTTP clients and noticeable UI lag.
- **Root Cause:** `testforge_trace.jsonl` contains 238,200+ lines. In `server.py`, `get_telemetry_trace()` called `logger_instance.read_traces()` (~1.75s), and then called `logger_instance.get_total_tokens()` which opened `testforge_trace.jsonl` and parsed all 238,000 lines from disk a second time (~2.94s).
- **Resolution:** Modified `testforge/logger.py` to allow `get_total_tokens(traces=traces)`. Updated `server.py` to pass the already-parsed in-memory `traces` list.
- **Verification:** Benchmarked endpoint before and after. Response time dropped from **4.69s to 1.74s (63% reduction)** with zero schema changes.
- **Status:** **VERIFIED FIXED**

### 2.3 DEF-DOC-001: Mutation Score Discrepancy Reconciliation
- **Severity:** P3 (Low)
- **Context:** Performance evaluation documentation in `docs/PERFORMANCE_EVALUATION/`.
- **Symptom:** Executive summaries cited 94.44% adjusted score, while automated raw JSON tables cited 89.47%.
- **Root Cause:** In the automated benchmark matrix, surviving mutants were classified as `UNKNOWN` equivalence by static AST heuristics, recording 0 equivalents ($\implies 17/19 = 89.47\%$). In deep domain triage, 1 mutant was proven equivalent, yielding $17/18 = 94.44\%$.
- **Resolution:** Documented both figures clearly: **89.47% automated adjusted** vs. **94.44% domain-triaged adjusted**.
- **Status:** **RESOLVED**

### 2.4 DEF-DOC-002: Deterministic AST Synthesis vs Live LLM Competition Disclosure
- **Severity:** P3 (Low)
- **Context:** Academic honesty in Criterion 10 presentation.
- **Symptom:** Risk of faculty interpreting Criterion 10 as proof that ReAct prompt architecture synthesized better tests than Few-Shot in live cloud LLMs.
- **Root Cause:** TestForge used the deterministic AST synthesizer for all 60 benchmark runs to ensure zero cost and offline reproducibility.
- **Resolution:** Explicitly documented that the benchmark evaluates configuration overhead, prompt serialization, token volume, and mutation testing latency, NOT live dynamic LLM reasoning loops.
- **Status:** **RESOLVED**

