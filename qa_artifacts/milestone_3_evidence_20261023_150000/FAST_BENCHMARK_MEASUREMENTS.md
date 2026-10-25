# Milestone 3 Evidence: Fast Deterministic Benchmark Mode

**Date:** 2026-10-23
**Platform:** macOS Darwin 27.0.1 (Apple Silicon M2 Pro)
**Python Environment:** `.venv-release` (Python 3.13.17)
**Files Modified/Created:**
- `testforge/benchmarking.py` (added `fast_mode` support to `BenchmarkRunner` & `BenchmarkReport`)
- `run_benchmark.py` (added `--fast` and `--repetitions` CLI flags, non-destructive output redirect)
- `tests/test_fast_benchmarking.py` (3 test suites)

---

## 1. Fast Benchmark Architecture

- **Deterministic Fixtures**: Emulates `baseline`, `zeroshot`, and `agentic_reflection` scenarios with repeatable, fixed metric trajectories derived from offline AST mutator analysis.
- **Offline / Cost-Free**: Requires 0 network requests, consumes 0 LLM API credits, and executes entirely in-process.
- **Clear Disclaimers**: Every generated run, summary table, and output JSON/Markdown file explicitly flags:
  - `"simulated": true`
  - `"mode": "fast-mock"`
  - Prominent banner: *"SIMULATED OFFLINE BENCHMARK: Results are deterministic fixtures for CI/CD checks and do NOT represent real foundation model synthesis quality or live API latency."*
- **Preservation of Historical Data**: When running `--fast`, default output redirects to `benchmark_results_fast.json` and `benchmark_results_fast.md`, never overwriting production `benchmark_results.json`.

---

## 2. Empirical Execution Durations

### Five Repetitions Measurement (In-Process)
Executing 5 repetitions $\times$ 3 scenarios = 15 scenario evaluations:

```text
tests/test_fast_benchmarking.py::test_fast_benchmark_runner_five_repetitions_duration 
[MEASURED DURATION] 5 repetitions (15 scenario runs) elapsed: 0.0063s
PASSED
```

| Metric | Measured Duration | Target Bound | Margin |
| :--- | :--- | :--- | :--- |
| **5 Repetitions (15 runs)** | **0.0063 seconds** (6.3 ms) | < 5.0 seconds | **793x faster than target** |
| **Average per Repetition** | **1.26 ms** | < 1.0 s | **793x faster than target** |

### CLI Subprocess Invocation (`run_benchmark.py --fast`)
```text
tests/test_fast_benchmarking.py::test_run_benchmark_cli_fast_mode 
[MEASURED CLI DURATION] run_benchmark.py --fast elapsed: 0.1507s
PASSED
```

| Metric | Measured Duration | Target Bound |
| :--- | :--- | :--- |
| **CLI Cold Start + Execution** | **0.1507 seconds** | < 5.0 seconds |

---

## 3. Schema & Label Verification

`tests/test_fast_benchmarking.py::test_fast_benchmark_schema_and_simulated_flags` passed:
- Verified `report.fast_mode == True`
- Verified `run.metrics.measured["simulated"] == True`
- Verified `run.metrics.measured["execution_mode"] == "SIMULATED_DETERMINISTIC"`
- Verified JSON serialization contains `"simulated": True`
- Verified Markdown serialization contains simulated warning callout box.
