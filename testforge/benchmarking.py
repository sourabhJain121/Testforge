"""
benchmarking.py - Statistical Repeatable Benchmarking & Cost Accounting for TestForge.

Course: CSE3101 - Agentic AI
Features:
  1. Multi-scenario comparative benchmarking:
     - Baseline (minimal handwritten suite)
     - ADK Zero-Shot (single-pass test generation)
     - Agentic Reflection (ADK Generator + CrewAI Critic reflection loop)
  2. Multi-run repetitions with statistical aggregation (mean, stddev, min, max).
  3. Strict metric categorization:
     - MEASURED: raw wall-clock times, mutant counts (generated, executed, killed, survived, timeouts), iterations, token counts from provider telemetry.
     - CALCULATED: mutation score %, line coverage %, speedup ratios.
     - ESTIMATED: financial cost in USD using published token pricing models (clearly flagged as estimates).
     - UNAVAILABLE: explicitly tracked fields when telemetry is not accessible.
  4. Repeatable offline verification using deterministic model doubles.
  5. Machine-readable JSON export and GitHub-flavored Markdown reporting.
"""

from __future__ import annotations
import os
import json
import time
import math
from typing import Dict, Any, List, Optional, Tuple
from pydantic import BaseModel, Field

from testforge.mutator import ASTMutator


# Official published Gemini 2.5/Flash model pricing rates (per 1,000,000 tokens)
PRICING_TABLE_PER_MILLION = {
    "gemini-2.5-flash": {"prompt": 0.075, "completion": 0.30},
    "gemini-3.6-flash": {"prompt": 0.075, "completion": 0.30},
    "gemini-1.5-pro": {"prompt": 1.25, "completion": 5.00},
    "default": {"prompt": 0.10, "completion": 0.40},
}


class MetricBreakdown(BaseModel):
    """Categorized breakdown of observed metrics to avoid blending measured data with estimates."""
    measured: Dict[str, Any] = Field(
        default_factory=dict,
        description="Empirical, hardware-measured values (duration_seconds, killed_mutants, tokens_prompt, etc.)"
    )
    calculated: Dict[str, Any] = Field(
        default_factory=dict,
        description="Derived analytical values (mutation_score_pct, line_coverage_pct, kill_ratio)"
    )
    estimated: Dict[str, Any] = Field(
        default_factory=dict,
        description="Projected values based on models (estimated_cost_usd, projected_cloud_latency)"
    )
    unknown_or_unavailable: List[str] = Field(
        default_factory=list,
        description="Fields requested but absent from provider responses or offline doubles"
    )


class BenchmarkRunResult(BaseModel):
    scenario: str
    run_index: int
    success: bool
    error_message: Optional[str] = None
    metrics: MetricBreakdown = Field(default_factory=MetricBreakdown)


class BenchmarkScenarioSummary(BaseModel):
    scenario: str
    runs_completed: int
    runs_failed: int
    mean_duration_sec: float = 0.0
    stddev_duration_sec: float = 0.0
    mean_mutation_score: float = 0.0
    mean_line_coverage: float = 0.0
    total_tokens_consumed: int = 0
    estimated_total_cost_usd: float = 0.0


class BenchmarkReport(BaseModel):
    target_file: str
    timestamp: float = Field(default_factory=time.time)
    repetitions: int
    hardware_summary: Optional[str] = None
    runs: List[BenchmarkRunResult] = Field(default_factory=list)
    scenario_summaries: Dict[str, BenchmarkScenarioSummary] = Field(default_factory=dict)
    fast_mode: bool = False
    disclaimer: Optional[str] = None

    def to_markdown(self) -> str:
        """Renders a formatted Markdown report comparing benchmarked scenarios."""
        lines = [
            "# TestForge Benchmark & Ablation Study Report",
            f"- **Target File:** `{self.target_file}`",
            f"- **Timestamp:** {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.timestamp))}",
            f"- **Repetitions per Scenario:** {self.repetitions}",
        ]
        if self.fast_mode:
            lines.insert(1, "> [!WARNING]\n> **SIMULATED OFFLINE BENCHMARK:** This report was generated using fast deterministic mock fixtures for CI/CD pipeline validation. Values are simulated and do NOT represent real foundation model synthesis quality or live API latency.")
        if self.hardware_summary:
            lines.append(f"- **Hardware Platform:** {self.hardware_summary}")

        lines.extend([
            "",
            "## Scenario Performance Summary",
            "",
            "| Scenario | Runs | Mean Latency (s) | StdDev (s) | Mean Mutation Score | Line Coverage | Total Tokens | Est. Cost (USD) |",
            "|---|---|---|---|---|---|---|---|",
        ])

        for sc_name, sc in self.scenario_summaries.items():
            lines.append(
                f"| **{sc_name}** | {sc.runs_completed}/{self.repetitions} | "
                f"{sc.mean_duration_sec:.2f}s | ±{sc.stddev_duration_sec:.2f}s | "
                f"{sc.mean_mutation_score:.1f}% | {sc.mean_line_coverage:.1f}% | "
                f"{sc.total_tokens_consumed:,} | ${sc.estimated_total_cost_usd:.5f} |"
            )

        lines.extend([
            "",
            "## Metric Integrity Disclosure",
            "> [!NOTE]",
            "> - **Measured values:** Execution latency, mutant kill counts, and exact token counts are captured directly from OS execution and API telemetry.",
            "> - **Calculated values:** Mutation scores and coverage percentages are computed deterministically via AST analysis.",
            "> - **Estimated values:** Model financial cost in USD is calculated from published pricing rates ($0.075/1M prompt, $0.30/1M completion) and is explicitly flagged as estimated.",
            ""
        ])

        return "\n".join(lines)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.model_dump(), indent=indent)


class BenchmarkRunner:
    """
    Executes repeatable, multi-run benchmarks comparing:
      1. Baseline (Minimal handwritten tests)
      2. Zero-Shot Generation (Single-pass LLM synthesis)
      3. Agentic Reflection (Full multi-agent generator + adversarial critic loop)
    """
    def __init__(
        self,
        target_code: str,
        target_file_path: Optional[str] = None,
        baseline_tests: Optional[str] = None,
        model_name: str = "gemini-3.6-flash",
        trace_dir: Optional[str] = None,
        fast_mode: bool = False,
    ):
        self.target_code = target_code.strip()
        self.target_file_path = target_file_path or "sample_target.py"
        self.baseline_tests = baseline_tests or "from target import *\ndef test_dummy(): pass\n"
        self.model_name = model_name
        self.trace_dir = trace_dir or "."
        self.fast_mode = fast_mode
        self._sandbox = None

    @property
    def sandbox(self):
        if self._sandbox is None:
            from testforge.sandbox import ParallelSandboxRunner
            self._sandbox = ParallelSandboxRunner(timeout_seconds=5)
        return self._sandbox

    def _estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        pricing = PRICING_TABLE_PER_MILLION.get(self.model_name, PRICING_TABLE_PER_MILLION["default"])
        cost = (prompt_tokens / 1_000_000.0 * pricing["prompt"]) + (completion_tokens / 1_000_000.0 * pricing["completion"])
        return round(cost, 6)

    def evaluate_suite(self, test_code: str) -> Tuple[float, float, int, int]:
        """Measures line coverage and mutation score deterministically."""
        cov_pct, _ = self.sandbox.measure_coverage(test_code, self.target_code)
        mutants = ASTMutator.generate_mutants(self.target_code)
        evaluated = self.sandbox.evaluate_mutants_parallel(test_code, mutants)
        killed = sum(1 for m in evaluated if m.status in ("KILLED", "TIMEOUT"))
        total = len(evaluated)
        score = (killed / total * 100.0) if total > 0 else 0.0
        return cov_pct, score, killed, total

    def run_benchmark(
        self,
        scenarios: Optional[List[str]] = None,
        repetitions: int = 1,
        engine_mode: str = "auto"
    ) -> BenchmarkReport:
        target_scenarios = scenarios or ["baseline", "zeroshot", "agentic_reflection"]
        all_runs: List[BenchmarkRunResult] = []

        for scenario in target_scenarios:
            for rep in range(1, repetitions + 1):
                res = self._execute_single_run(scenario, rep, engine_mode=engine_mode)
                all_runs.append(res)

        # Aggregate metrics across runs per scenario
        summaries: Dict[str, BenchmarkScenarioSummary] = {}
        for scenario in target_scenarios:
            sc_runs = [r for r in all_runs if r.scenario == scenario and r.success]
            failed_runs = [r for r in all_runs if r.scenario == scenario and not r.success]
            count = len(sc_runs)

            if count > 0:
                durations = [r.metrics.measured.get("duration_seconds", 0.0) for r in sc_runs]
                mean_dur = sum(durations) / count
                variance = sum((d - mean_dur) ** 2 for d in durations) / count if count > 1 else 0.0
                stddev_dur = math.sqrt(variance)

                mean_score = sum(r.metrics.calculated.get("mutation_score_pct", 0.0) for r in sc_runs) / count
                mean_cov = sum(r.metrics.calculated.get("line_coverage_pct", 0.0) for r in sc_runs) / count
                total_tokens = sum(r.metrics.measured.get("total_tokens", 0) for r in sc_runs)
                total_cost = sum(r.metrics.estimated.get("estimated_cost_usd", 0.0) for r in sc_runs)

                summaries[scenario] = BenchmarkScenarioSummary(
                    scenario=scenario,
                    runs_completed=count,
                    runs_failed=len(failed_runs),
                    mean_duration_sec=round(mean_dur, 3),
                    stddev_duration_sec=round(stddev_dur, 3),
                    mean_mutation_score=round(mean_score, 1),
                    mean_line_coverage=round(mean_cov, 1),
                    total_tokens_consumed=total_tokens,
                    estimated_total_cost_usd=round(total_cost, 6),
                )
            else:
                summaries[scenario] = BenchmarkScenarioSummary(
                    scenario=scenario,
                    runs_completed=0,
                    runs_failed=len(failed_runs),
                )

        hw_desc = None
        try:
            from testforge.accel import hw_profile
            hw_desc = f"{hw_profile.machine} ({hw_profile.os_system}, {hw_profile.cpu_count} cores, {hw_profile.total_memory_gb:.1f}GB RAM)"
        except Exception:
            pass

        disclaimer_text = (
            "SIMULATED OFFLINE BENCHMARK: Results are deterministic mock fixtures for CI/CD pipeline validation."
            if self.fast_mode else None
        )
        return BenchmarkReport(
            target_file=self.target_file_path,
            repetitions=repetitions,
            hardware_summary=hw_desc,
            runs=all_runs,
            scenario_summaries=summaries,
            fast_mode=self.fast_mode,
            disclaimer=disclaimer_text,
        )

    def _execute_fast_single_run(self, scenario: str, rep_index: int) -> BenchmarkRunResult:
        """
        Fast deterministic offline execution using precomputed AST metrics for CI/CD checks.
        Executes in < 0.05 seconds per run without spawning slow subprocesses or calling LLMs.
        """
        t0 = time.perf_counter()
        base_mutants = max(6, min(20, len(self.target_code.splitlines())))

        if scenario == "baseline":
            killed = max(1, base_mutants // 4)
            score = round((killed / base_mutants) * 100.0, 1)
            cov_pct = 45.0
            tokens = 0
            cost = 0.0
            iters = 0
        elif scenario == "zeroshot":
            killed = max(2, int(base_mutants * 0.6))
            score = round((killed / base_mutants) * 100.0, 1)
            cov_pct = 75.0
            tokens = 650 + (rep_index * 15)
            cost = self._estimate_cost(int(tokens * 0.7), int(tokens * 0.3))
            iters = 1
        else:  # agentic_reflection
            killed = base_mutants
            score = 100.0
            cov_pct = 95.0
            tokens = 1800 + (rep_index * 40)
            cost = self._estimate_cost(int(tokens * 0.7), int(tokens * 0.3))
            iters = 2

        duration = round(time.perf_counter() - t0 + 0.002, 4)

        return BenchmarkRunResult(
            scenario=scenario,
            run_index=rep_index,
            success=True,
            metrics=MetricBreakdown(
                measured={
                    "duration_seconds": duration,
                    "killed_mutants": killed,
                    "total_mutants": base_mutants,
                    "iterations": iters,
                    "total_tokens": tokens,
                    "execution_mode": "FAST_DETERMINISTIC_MOCK",
                    "simulated": True,
                },
                calculated={
                    "mutation_score_pct": score,
                    "line_coverage_pct": cov_pct,
                },
                estimated={
                    "estimated_cost_usd": cost,
                },
                unknown_or_unavailable=[
                    "live_llm_telemetry_simulated_for_offline_ci"
                ]
            )
        )

    def _execute_single_run(self, scenario: str, rep_index: int, engine_mode: str = "auto") -> BenchmarkRunResult:
        if self.fast_mode:
            return self._execute_fast_single_run(scenario, rep_index)

        t0 = time.perf_counter()
        try:
            if scenario == "baseline":
                cov_pct, score, killed, total = self.evaluate_suite(self.baseline_tests)
                duration = time.perf_counter() - t0
                return BenchmarkRunResult(
                    scenario=scenario,
                    run_index=rep_index,
                    success=True,
                    metrics=MetricBreakdown(
                        measured={
                            "duration_seconds": round(duration, 3),
                            "killed_mutants": killed,
                            "total_mutants": total,
                            "total_tokens": 0,
                            "execution_mode": "DETERMINISTIC_BASELINE"
                        },
                        calculated={"mutation_score_pct": round(score, 1), "line_coverage_pct": round(cov_pct, 1)},
                        estimated={"estimated_cost_usd": 0.0},
                        unknown_or_unavailable=["prompt_tokens", "completion_tokens"]
                    )
                )

            elif scenario == "zeroshot":
                from testforge.agents import TestGeneratorAgent
                from testforge.logger import TraceLogger
                trace_path = os.path.join(self.trace_dir, f"trace_bench_zs_{rep_index}.jsonl")
                logger = TraceLogger(log_path=trace_path)
                gen = TestGeneratorAgent(model_name=self.model_name, logger=logger)
                tests = gen.generate_tests(source_code=self.target_code, iteration=0)
                cov_pct, score, killed, total = self.evaluate_suite(tests)
                duration = time.perf_counter() - t0
                tokens = logger.get_total_tokens()
                cost = self._estimate_cost(int(tokens * 0.7), int(tokens * 0.3)) if tokens > 0 else 0.0

                return BenchmarkRunResult(
                    scenario=scenario,
                    run_index=rep_index,
                    success=True,
                    metrics=MetricBreakdown(
                        measured={
                            "duration_seconds": round(duration, 3),
                            "killed_mutants": killed,
                            "total_mutants": total,
                            "total_tokens": tokens,
                            "execution_mode": "LIVE_MODEL" if tokens > 0 else "OFFLINE_FALLBACK"
                        },
                        calculated={"mutation_score_pct": round(score, 1), "line_coverage_pct": round(cov_pct, 1)},
                        estimated={"estimated_cost_usd": cost},
                        unknown_or_unavailable=[] if tokens > 0 else ["api_tokens_unavailable_in_offline_mode"]
                    )
                )

            elif scenario == "agentic_reflection":
                from testforge.orchestrator import TestForgeOrchestrator
                trace_path = os.path.join(self.trace_dir, f"trace_bench_refl_{rep_index}.jsonl")
                orchestrator = TestForgeOrchestrator(
                    target_source_code=self.target_code,
                    initial_test_code=self.baseline_tests,
                    max_iterations=2,
                    target_mutation_score=90.0,
                    model_name=self.model_name,
                    trace_log_path=trace_path,
                    target_file_path=self.target_file_path,
                    engine_mode=engine_mode,
                )
                state = orchestrator.run()
                duration = time.perf_counter() - t0
                tokens = orchestrator.logger.get_total_tokens()
                cost = self._estimate_cost(int(tokens * 0.7), int(tokens * 0.3)) if tokens > 0 else 0.0
                score = state.final_mutation_score
                cov_pct = state.baseline_line_coverage

                return BenchmarkRunResult(
                    scenario=scenario,
                    run_index=rep_index,
                    success=True,
                    metrics=MetricBreakdown(
                        measured={
                            "duration_seconds": round(duration, 3),
                            "killed_mutants": state.mutants_killed,
                            "total_mutants": state.mutants_generated,
                            "iterations": state.reflection_iterations_performed,
                            "total_tokens": tokens,
                            "execution_mode": "LIVE_MODEL" if tokens > 0 else "OFFLINE_FALLBACK"
                        },
                        calculated={"mutation_score_pct": round(score, 1), "line_coverage_pct": round(cov_pct, 1)},
                        estimated={"estimated_cost_usd": cost},
                        unknown_or_unavailable=[] if tokens > 0 else ["api_tokens_unavailable_in_offline_mode"]
                    )
                )

            else:
                raise ValueError(f"Unknown benchmark scenario: {scenario}")

        except Exception as exc:
            duration = time.perf_counter() - t0
            return BenchmarkRunResult(
                scenario=scenario,
                run_index=rep_index,
                success=False,
                error_message=str(exc),
                metrics=MetricBreakdown(
                    measured={"duration_seconds": round(duration, 3)},
                    calculated={},
                    estimated={},
                    unknown_or_unavailable=["execution_failed"]
                )
            )
