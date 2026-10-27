# TestForge — Metric Provenance & Calculation Audit

**Audit Date:** 2026-10-27 01:16:50 IST  
**Audit Directory:** `qa_artifacts/autonomous_e2e_acceptance_20261027_004800/`  

---

## 1. Metric Classification Taxonomy (MUST 3 Compliance)

In compliance with teacher requirements and Pydantic v2 schema definitions (`testforge/benchmarking.py`), all system metrics are strictly partitioned into four provenance categories:

```
MetricProvenance
├── Measured: Direct hardware or runtime observation
├── Calculated: Pure mathematical transformation of measured quantities
├── Estimated: Model-based or financial cost projection
└── Unavailable: Unmeasured or omitted metric
```

---

## 2. Quantitative Metric Audit Matrix

| Metric Name | Display Location | Calculation Formula / Source | Provenance Category | Precision Distinctions & Caveats |
|---|---|---|---|---|
| **Mutation Score (%)** | Hardening Lab, Benchmark Tab | `(mutants_killed / mutants_executed) * 100` | Calculated | Must distinguish between **Arithmetic Mean** of per-fixture percentages vs **Pooled Mutation Score** across all mutants. |
| **Line Coverage (%)** | Hardening Lab, Telemetry | `(lines_covered / total_executable_lines) * 100` | Calculated | Measured via `pytest-cov` / `coverage.py` on target module code during test execution. |
| **Defect Detection (%)** | Benchmark Tab | `(defects_detected / total_known_defects) * 100` | Calculated | Based on mutant kills mapping to AST error injections. |
| **Elapsed Runtime (s)** | Progress Bar, Telemetry, History | `time.time() - start_time` | Measured | Monotonic wall-clock time per stage and per entire job. |
| **Memory Peak (MB)** | Telemetry Trace | `resource.getrusage(RUSAGE_SELF).ru_maxrss` | Measured | Direct POSIX operating system syscall on macOS Apple Silicon. |
| **CPU Worker Count** | Hardware Badge | `max(1, os.cpu_count() - 2)` | Measured | Configured to 8 parallel worker subprocesses for sandboxed mutation. |
| **Token Usage** | Telemetry Trace | Prompt tokens + Completion tokens | Measured / Estimated | 0 tokens for deterministic local fallbacks; exact token count when live LLM is invoked. |
| **Estimated Cost ($)** | Telemetry Trace | `(tokens_in * rate_in) + (tokens_out * rate_out)` | Estimated | $0.00 for local execution; estimated pricing applies only to cloud API tiers. |

---

## 3. Discrepancy Avoidance Guarantees

1. **Zero-Token Local Execution:** All runs operating under deterministic mode or local synthesis are tagged with `cost_usd = 0.00` and `provenance = "deterministic_fallback"`. The UI never displays cloud API costs for offline runs.
2. **Deterministic Mutation Totals:** AST mutation counts are strictly reproducible given the same source AST and mutation operators.
3. **Equivalence Filtering:** Equivalent mutants (mutants that cannot alter semantics) are tracked distinctly in `MutantSpace` and not counted against the mutation kill denominator when adjusted scores are reported.
