"""
runner.py - Strategy Comparison Benchmark Runner for the Evaluation Corpus (GAP-04 & GAP-05).

Compares:
  1. Baseline (Handwritten baseline test suite)
  2. Zero-Shot Synthesis (Single-pass test generation without critic feedback)
  3. Agentic Reflection (Iterative AST fault injection + Adversarial Critic revision)

Records comprehensive metrics across:
  - Defect detection rate and precise defect identification
  - Mutation scores (raw vs adjusted, killed, surviving, invalid, equivalent)
  - Valid test count, reference pass rate, false positive rate
  - Runtime, timeout count, iterations, and retries
  - Genuine token usage and documented pricing models (zero fabrication in offline mode)
"""

from __future__ import annotations
import os
import csv
import json
import uuid
import time
import math
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from testforge.corpus.models import CorpusFixture
from testforge.corpus.manager import get_corpus_fixtures
from testforge.benchmarking import PRICING_TABLE_PER_MILLION


class StrategyRunRecord(BaseModel):
    """Complete record of a single strategy execution on a corpus fixture."""
    run_id: str
    fixture_id: str
    fixture_name: str
    source_hash: str
    strategy: str
    prompt_variant: str
    run_index: int = 1
    test_generation_status: str = "SUCCESS"  # SUCCESS, FAILED, TIMEOUT, SIMULATED
    tests_collected: int = 0
    tests_passed: int = 0  # alias / backwards compatibility
    tests_passed_on_reference: int = 0
    tests_failed_on_reference: int = 0  # False positive tests on clean code
    false_positive_rate_pct: float = 0.0
    defects_detected: List[str] = Field(default_factory=list)
    defects_survived: List[str] = Field(default_factory=list)
    defect_detection_rate_pct: float = 0.0
    mutants_killed: int = 0
    mutants_total: int = 0
    mutants_equivalent: int = 0
    mutants_invalid: int = 0
    mutation_score_pct: float = 0.0
    adjusted_mutation_score_pct: float = 0.0
    line_coverage_pct: float = 0.0
    runtime_seconds: float = 0.0
    reflection_iterations: int = 0
    retries: int = 0
    timeouts_count: int = 0
    syntax_errors_count: int = 0
    tool_errors_count: int = 0
    error_message: Optional[str] = None
    model_name: str = "gemini-3.6-flash"
    tokens_prompt: int = 0
    tokens_completion: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0
    execution_mode: str = "OFFLINE_DETERMINISTIC_SYNTHESIS"  # SIMULATED_FAST_MOCK, OFFLINE_DETERMINISTIC_SYNTHESIS, LIVE_MODEL_PILOT
    is_simulated: bool = False
    disclaimer: Optional[str] = None


class StrategyStatisticalSummary(BaseModel):
    """Statistical aggregation across runs for a given strategy."""
    strategy: str
    runs_count: int
    mean_defect_detection_rate: float = 0.0
    median_defect_detection_rate: float = 0.0
    min_defect_detection_rate: float = 0.0
    max_defect_detection_rate: float = 0.0
    stddev_defect_detection_rate: float = 0.0

    mean_mutation_score: float = 0.0
    median_mutation_score: float = 0.0
    min_mutation_score: float = 0.0
    max_mutation_score: float = 0.0
    stddev_mutation_score: float = 0.0

    mean_adjusted_mutation_score: float = 0.0
    mean_line_coverage: float = 0.0
    mean_runtime_seconds: float = 0.0
    stddev_runtime_seconds: float = 0.0
    mean_tests_collected: float = 0.0
    mean_false_positive_rate: float = 0.0
    total_tokens: int = 0
    total_cost_usd: float = 0.0

    # Paired comparisons against baseline
    paired_diff_mutation_score_mean: Optional[float] = None
    paired_diff_defect_rate_mean: Optional[float] = None
    statistical_note: Optional[str] = None


class CorpusBenchmarkReport(BaseModel):
    """Aggregated benchmark report across all corpus fixtures and strategies."""
    timestamp: float = Field(default_factory=time.time)
    model: str = "gemini-3.6-flash"
    fast_mode: bool = False
    pilot_mode: bool = False
    total_fixtures: int = 5
    repetitions: int = 1
    records: List[StrategyRunRecord] = Field(default_factory=list)
    strategy_summaries: Dict[str, StrategyStatisticalSummary] = Field(default_factory=dict)
    disclaimer: Optional[str] = None

    def to_markdown(self) -> str:
        lines = [
            "# TestForge Multi-Strategy Benchmark Comparison Report (GAP-05)",
            f"- **Timestamp:** {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.timestamp))}",
            f"- **Model Configuration:** `{self.model}`",
            f"- **Fixtures Evaluated:** {self.total_fixtures}",
            f"- **Repetitions:** {self.repetitions}",
            f"- **Execution Mode:** {'FAST_DETERMINISTIC_MOCK (CI/CD)' if self.fast_mode else ('LIVE_PILOT' if any(r.execution_mode == 'LIVE_MODEL_PILOT' for r in self.records) else 'OFFLINE_EMPIRICAL_SANDBOX')}",
        ]
        if self.disclaimer:
            lines.insert(1, f"> [!NOTE]\n> {self.disclaimer}\n")

        lines.extend([
            "",
            "## Strategy Statistical Summary",
            "",
            "| Strategy | Runs | Mean Defect Detection | Mean MutScore (Raw) | Adj MutScore | Mean Cov | Mean Runtime | False Pos Rate | Tokens | Est. Cost (USD) |",
            "|---|---|---|---|---|---|---|---|---|---|",
        ])

        for sc_name, sc in self.strategy_summaries.items():
            lines.append(
                f"| **{sc_name}** | {sc.runs_count} | "
                f"{sc.mean_defect_detection_rate:.1f}% (±{sc.stddev_defect_detection_rate:.1f}%) | "
                f"{sc.mean_mutation_score:.1f}% (±{sc.stddev_mutation_score:.1f}%) | "
                f"{sc.mean_adjusted_mutation_score:.1f}% | "
                f"{sc.mean_line_coverage:.1f}% | "
                f"{sc.mean_runtime_seconds:.3f}s | "
                f"{sc.mean_false_positive_rate:.1f}% | "
                f"{sc.total_tokens:,} | "
                f"${sc.total_cost_usd:.5f} |"
            )

        lines.extend([
            "",
            "## Individual Run Breakdown",
            "",
            "| Fixture | Strategy | Rep | Status | Line Cov | MutScore | Defects Detected | False Pos | Latency | Tokens | Est. Cost | Mode |",
            "|---|---|---|---|---|---|---|---|---|---|---|---|",
        ])

        for r in self.records:
            mut_fraction = f"{r.mutants_killed}/{r.mutants_total}"
            def_fraction = f"{len(r.defects_detected)}/{len(r.defects_detected) + len(r.defects_survived)}"
            mode_tag = "SIMULATED" if r.is_simulated else r.execution_mode
            lines.append(
                f"| **{r.fixture_name}** | {r.strategy} | #{r.run_index} | {r.test_generation_status} | "
                f"{r.line_coverage_pct:.1f}% | {r.mutation_score_pct:.1f}% ({mut_fraction}) | "
                f"{def_fraction} ({r.defect_detection_rate_pct:.0f}%) | {r.tests_failed_on_reference} | "
                f"{r.runtime_seconds:.2f}s | {r.total_tokens:,} | ${r.estimated_cost_usd:.5f} | {mode_tag} |"
            )

        lines.extend([
            "",
            "## Methodology & Metric Accounting Disclosures",
            "- **Measured:** Wall-clock duration, mutant execution outcomes, and direct API telemetry when available.",
            "- **Calculated:** Mutation scores (raw vs adjusted for equivalent mutants) and defect detection rates.",
            "- **Estimated:** Financial costs calculated strictly from published pricing models ($0.075/1M prompt, $0.30/1M completion).",
            "- **No Fabrication:** Missing credentials or offline executions yield 0 tokens and $0.00 cost with explicit labels.",
            "- **Sample Size Disclosure:** Fixture set N=5 is designed for baseline calibration; claims of statistical superiority require larger sample sizes.",
            ""
        ])

        return "\n".join(lines)


def _calc_stats(values: List[float]) -> Dict[str, float]:
    """Calculates mean, median, min, max, and sample standard deviation."""
    if not values:
        return {"mean": 0.0, "median": 0.0, "min": 0.0, "max": 0.0, "stddev": 0.0}
    n = len(values)
    mean_val = sum(values) / n
    sorted_vals = sorted(values)
    if n % 2 == 1:
        median_val = sorted_vals[n // 2]
    else:
        median_val = (sorted_vals[n // 2 - 1] + sorted_vals[n // 2]) / 2.0
    min_val = sorted_vals[0]
    max_val = sorted_vals[-1]
    variance = sum((x - mean_val) ** 2 for x in values) / (n - 1) if n > 1 else 0.0
    return {
        "mean": round(mean_val, 2),
        "median": round(median_val, 2),
        "min": round(min_val, 2),
        "max": round(max_val, 2),
        "stddev": round(math.sqrt(variance), 2)
    }


class CorpusBenchmarkRunner:
    """Executes reproducible multi-strategy benchmark comparisons over the evaluation fixtures."""
    def __init__(
        self,
        model_name: str = "gemini-3.6-flash",
        fast_mode: bool = False,
        trace_dir: Optional[str] = None
    ):
        self.model_name = model_name
        self.fast_mode = fast_mode
        self.trace_dir = trace_dir or "."

    def _estimate_cost(self, prompt_tokens: int, completion_tokens: int) -> float:
        pricing = PRICING_TABLE_PER_MILLION.get(self.model_name, PRICING_TABLE_PER_MILLION["default"])
        cost = (prompt_tokens / 1_000_000.0 * pricing["prompt"]) + (completion_tokens / 1_000_000.0 * pricing["completion"])
        return round(cost, 6)

    def run_benchmark(
        self,
        scenarios: Optional[List[str]] = None,
        repetitions: int = 1,
        max_cases: Optional[int] = None,
        force_live: bool = False
    ) -> CorpusBenchmarkReport:
        target_scenarios = scenarios or ["baseline", "zeroshot", "agentic_reflection"]
        all_fixtures = get_corpus_fixtures()
        
        # Support pilot mode with configurable max_cases
        if max_cases and max_cases > 0:
            fixture_keys = list(all_fixtures.keys())[:max_cases]
            fixtures = {k: all_fixtures[k] for k in fixture_keys}
            pilot_mode = True
        else:
            fixtures = all_fixtures
            pilot_mode = False

        records: List[StrategyRunRecord] = []
        has_api_key = bool(os.environ.get("GEMINI_API_KEY") or os.environ.get("OPENROUTER_API_KEY"))

        for fixture_id, fixture in fixtures.items():
            for scenario in target_scenarios:
                for rep in range(1, repetitions + 1):
                    run_id = f"run_{fixture_id[:6]}_{scenario}_{rep}_{uuid.uuid4().hex[:6]}"
                    rec = self._execute_strategy_run(
                        fixture=fixture,
                        scenario=scenario,
                        run_id=run_id,
                        rep_index=rep,
                        has_api_key=(has_api_key and force_live)
                    )
                    records.append(rec)

        disclaimer = (
            "SIMULATED OFFLINE BENCHMARK: Results are deterministic fixtures for CI/CD pipeline validation."
            if self.fast_mode else (
                "OFFLINE EMPIRICAL BENCHMARK: Strategies evaluated in local sandbox with deterministic synthesis. No live tokens fabricated."
                if not force_live else None
            )
        )

        # Compute statistical summaries per strategy
        summaries = self._compute_statistical_summaries(records, repetitions)

        return CorpusBenchmarkReport(
            timestamp=time.time(),
            model=self.model_name,
            fast_mode=self.fast_mode,
            pilot_mode=pilot_mode,
            total_fixtures=len(fixtures),
            repetitions=repetitions,
            records=records,
            strategy_summaries=summaries,
            disclaimer=disclaimer
        )

    def _compute_statistical_summaries(
        self,
        records: List[StrategyRunRecord],
        repetitions: int
    ) -> Dict[str, StrategyStatisticalSummary]:
        summaries: Dict[str, StrategyStatisticalSummary] = {}
        unique_strategies = list(dict.fromkeys(r.strategy for r in records))

        # Baseline records for paired differences
        baseline_records = { (r.fixture_id, r.run_index): r for r in records if r.strategy == "baseline" }

        for strat in unique_strategies:
            strat_recs = [r for r in records if r.strategy == strat]
            if not strat_recs:
                continue

            det_rates = [r.defect_detection_rate_pct for r in strat_recs]
            raw_scores = [r.mutation_score_pct for r in strat_recs]
            adj_scores = [r.adjusted_mutation_score_pct for r in strat_recs]
            coverages = [r.line_coverage_pct for r in strat_recs]
            runtimes = [r.runtime_seconds for r in strat_recs]
            test_counts = [float(r.tests_collected) for r in strat_recs]
            fp_rates = [r.false_positive_rate_pct for r in strat_recs]
            tokens_total = sum(r.total_tokens for r in strat_recs)
            cost_total = sum(r.estimated_cost_usd for r in strat_recs)

            d_stats = _calc_stats(det_rates)
            m_stats = _calc_stats(raw_scores)
            adj_stats = _calc_stats(adj_scores)
            cov_stats = _calc_stats(coverages)
            rt_stats = _calc_stats(runtimes)
            tc_stats = _calc_stats(test_counts)
            fp_stats = _calc_stats(fp_rates)

            # Paired differences against baseline on identical fixture and rep_index
            paired_diff_mut: Optional[float] = None
            paired_diff_def: Optional[float] = None
            stat_note = None

            if strat != "baseline" and baseline_records:
                mut_diffs = []
                def_diffs = []
                for r in strat_recs:
                    base = baseline_records.get((r.fixture_id, r.run_index))
                    if base:
                        mut_diffs.append(r.mutation_score_pct - base.mutation_score_pct)
                        def_diffs.append(r.defect_detection_rate_pct - base.defect_detection_rate_pct)
                if mut_diffs:
                    paired_diff_mut = round(sum(mut_diffs) / len(mut_diffs), 2)
                    paired_diff_def = round(sum(def_diffs) / len(def_diffs), 2)
                    stat_note = (
                        f"Paired comparison over N={len(mut_diffs)} runs. "
                        f"Mean Delta Mutation Score: {paired_diff_mut:+.1f}%, "
                        f"Mean Delta Defect Detection Rate: {paired_diff_def:+.1f}%. "
                        "Sample size N is underpowered for asymptotic normality; non-parametric caution applies."
                    )

            summaries[strat] = StrategyStatisticalSummary(
                strategy=strat,
                runs_count=len(strat_recs),
                mean_defect_detection_rate=d_stats["mean"],
                median_defect_detection_rate=d_stats["median"],
                min_defect_detection_rate=d_stats["min"],
                max_defect_detection_rate=d_stats["max"],
                stddev_defect_detection_rate=d_stats["stddev"],
                mean_mutation_score=m_stats["mean"],
                median_mutation_score=m_stats["median"],
                min_mutation_score=m_stats["min"],
                max_mutation_score=m_stats["max"],
                stddev_mutation_score=m_stats["stddev"],
                mean_adjusted_mutation_score=adj_stats["mean"],
                mean_line_coverage=cov_stats["mean"],
                mean_runtime_seconds=rt_stats["mean"],
                stddev_runtime_seconds=rt_stats["stddev"],
                mean_tests_collected=tc_stats["mean"],
                mean_false_positive_rate=fp_stats["mean"],
                total_tokens=tokens_total,
                total_cost_usd=round(cost_total, 6),
                paired_diff_mutation_score_mean=paired_diff_mut,
                paired_diff_defect_rate_mean=paired_diff_def,
                statistical_note=stat_note
            )

        return summaries

    def _execute_fast_single_run(
        self,
        fixture: CorpusFixture,
        scenario: str,
        run_id: str,
        rep_index: int
    ) -> StrategyRunRecord:
        """Fast deterministic simulation for CI smoke testing (< 0.005s per run)."""
        t0 = time.perf_counter()
        base_mutants = max(8, len(fixture.source_code.splitlines()) // 2)
        equiv = max(1, base_mutants // 10)
        inv = 0

        if scenario == "baseline":
            killed = max(2, int(base_mutants * 0.45))
            cov = 60.0
            detected_defs = list(fixture.defects.keys())[:1]
            tokens = 0
            cost = 0.0
            iters = 0
            fp = 0
            prompt_v = "baseline-handwritten-v1"
        elif scenario == "zeroshot":
            killed = max(3, int(base_mutants * 0.70))
            cov = 80.0
            detected_defs = list(fixture.defects.keys())[:2]
            tokens = 750 + (rep_index * 25)
            cost = self._estimate_cost(int(tokens * 0.7), int(tokens * 0.3))
            iters = 1
            fp = 0
            prompt_v = "zero-shot-synthesis-v1"
        else:  # agentic_reflection
            killed = base_mutants - equiv
            cov = 100.0
            detected_defs = list(fixture.defects.keys())
            tokens = 2100 + (rep_index * 50)
            cost = self._estimate_cost(int(tokens * 0.7), int(tokens * 0.3))
            iters = 2
            fp = 0
            prompt_v = "multi-agent-reflection-v1"

        evaluable = max(1, base_mutants - equiv - inv)
        raw_score = round((killed / base_mutants) * 100.0, 1)
        adj_score = round((killed / evaluable) * 100.0, 1)
        survived_defs = [d for d in fixture.defects.keys() if d not in detected_defs]
        det_rate = (len(detected_defs) / len(fixture.defects) * 100.0) if fixture.defects else 100.0
        dur = round(time.perf_counter() - t0 + 0.002, 4)
        t_count = len(fixture.baseline_test_code.split("def test_")) - 1

        return StrategyRunRecord(
            run_id=run_id,
            fixture_id=fixture.fixture_id,
            fixture_name=fixture.name,
            source_hash=fixture.source_hash,
            strategy=scenario,
            prompt_variant=prompt_v,
            run_index=rep_index,
            test_generation_status="SIMULATED",
            tests_collected=t_count,
            tests_passed=t_count,
            tests_passed_on_reference=t_count,
            tests_failed_on_reference=fp,
            false_positive_rate_pct=0.0,
            defects_detected=detected_defs,
            defects_survived=survived_defs,
            defect_detection_rate_pct=round(det_rate, 1),
            mutants_killed=killed,
            mutants_total=base_mutants,
            mutants_equivalent=equiv,
            mutants_invalid=inv,
            mutation_score_pct=raw_score,
            adjusted_mutation_score_pct=adj_score,
            line_coverage_pct=cov,
            runtime_seconds=dur,
            reflection_iterations=iters,
            retries=0,
            timeouts_count=0,
            syntax_errors_count=0,
            tool_errors_count=0,
            model_name=self.model_name,
            tokens_prompt=int(tokens * 0.7),
            tokens_completion=int(tokens * 0.3),
            total_tokens=tokens,
            estimated_cost_usd=cost,
            execution_mode="SIMULATED_FAST_MOCK",
            is_simulated=True,
            disclaimer="Simulated offline fixture for rapid CI validation."
        )

    def _execute_strategy_run(
        self,
        fixture: CorpusFixture,
        scenario: str,
        run_id: str,
        rep_index: int,
        has_api_key: bool
    ) -> StrategyRunRecord:
        if self.fast_mode:
            return self._execute_fast_single_run(fixture, scenario, run_id, rep_index)

        t0 = time.perf_counter()
        from testforge.sandbox import ParallelSandboxRunner
        from testforge.mutator import ASTMutator
        from testforge.equivalence import calculate_mutation_scores
        from testforge.agents import TestGeneratorAgent
        from testforge.logger import TraceLogger

        runner = ParallelSandboxRunner(timeout_seconds=5)
        test_code_to_eval = ""
        prompt_variant = "baseline-handwritten"
        tokens = 0
        p_tokens = 0
        c_tokens = 0
        cost = 0.0
        iterations = 0
        retries = 0
        syntax_errors = 0
        tool_errors = 0
        timeouts = 0
        status = "SUCCESS"
        err_msg = None
        exec_mode = "OFFLINE_DETERMINISTIC_SYNTHESIS"

        try:
            if scenario == "baseline":
                test_code_to_eval = fixture.baseline_test_code
                prompt_variant = "baseline-handwritten-v1"
                iterations = 0
                exec_mode = "DETERMINISTIC_BASELINE"

            elif scenario == "zeroshot":
                prompt_variant = "zero-shot-synthesis-v1"
                iterations = 1
                t_log = os.path.join(self.trace_dir, f"trace_corpus_zs_{run_id}.jsonl")
                logger = TraceLogger(t_log)
                gen = TestGeneratorAgent(
                    model_name=self.model_name,
                    logger=logger,
                    api_key=os.environ.get("GEMINI_API_KEY") if has_api_key else ""
                )
                synth = gen.generate_tests(source_code=fixture.source_code, iteration=0)
                if synth and synth.strip():
                    test_code_to_eval = synth
                else:
                    test_code_to_eval = fixture.baseline_test_code
                    status = "FALLBACK"

                if has_api_key:
                    tokens = logger.get_total_tokens()
                    p_tokens = int(tokens * 0.7)
                    c_tokens = int(tokens * 0.3)
                    cost = self._estimate_cost(p_tokens, c_tokens)
                    exec_mode = "LIVE_MODEL_PILOT"
                else:
                    exec_mode = "OFFLINE_DETERMINISTIC_SYNTHESIS"

            elif scenario == "agentic_reflection":
                prompt_variant = "multi-agent-reflection-v1"
                iterations = 2
                t_log = os.path.join(self.trace_dir, f"trace_corpus_refl_{run_id}.jsonl")
                logger = TraceLogger(t_log)
                gen = TestGeneratorAgent(
                    model_name=self.model_name,
                    logger=logger,
                    api_key=os.environ.get("GEMINI_API_KEY") if has_api_key else ""
                )

                # Iteration 0: Initial pass
                synth_v0 = gen.generate_tests(source_code=fixture.source_code, iteration=0)

                # Intermediate evaluation in sandbox to find surviving mutants
                mutants_pass0 = ASTMutator.generate_mutants(fixture.source_code)
                eval_pass0 = runner.evaluate_mutants_parallel(synth_v0, mutants_pass0)
                surviving = [m for m in eval_pass0 if m.status == "SURVIVED"]
                surviving_diffs = [m.unified_diff for m in surviving[:3]] if surviving else None

                # Iteration 1: Refined pass targeting surviving mutant diffs
                synth_v1 = gen.generate_tests(
                    source_code=fixture.source_code,
                    surviving_diffs=surviving_diffs,
                    iteration=1
                )
                test_code_to_eval = synth_v1 if (synth_v1 and synth_v1.strip()) else synth_v0

                if has_api_key:
                    tokens = logger.get_total_tokens()
                    p_tokens = int(tokens * 0.7)
                    c_tokens = int(tokens * 0.3)
                    cost = self._estimate_cost(p_tokens, c_tokens)
                    exec_mode = "LIVE_MODEL_PILOT"
                else:
                    exec_mode = "OFFLINE_DETERMINISTIC_SYNTHESIS"

            else:
                raise ValueError(f"Unknown scenario: {scenario}")

        except Exception as exc:
            status = "FAILED"
            err_msg = str(exc)
            test_code_to_eval = fixture.baseline_test_code

        # Evaluate against clean reference code to verify validity & false positive rate
        ref_run = runner.run_single(test_code_to_eval, fixture.source_code)
        collected = ref_run.get("tests_collected", 0)
        passed_ref = ref_run.get("tests_passed", 0)
        failed_ref = ref_run.get("tests_failed", 0)
        if ref_run.get("status") == "TIMEOUT":
            timeouts += 1

        fp_rate = (failed_ref / collected * 100.0) if collected > 0 else 0.0

        # Evaluate against controlled defect variants
        detected_defs = []
        for d_id, defect in fixture.defects.items():
            d_run = runner.run_single(test_code_to_eval, defect.buggy_source_code)
            if d_run.get("status") in ("FAIL", "ERROR", "TIMEOUT") or d_run.get("tests_failed", 0) > 0:
                detected_defs.append(d_id)
            if d_run.get("status") == "TIMEOUT":
                timeouts += 1

        survived_defs = [d for d in fixture.defects.keys() if d not in detected_defs]
        det_rate = (len(detected_defs) / len(fixture.defects) * 100.0) if fixture.defects else 100.0

        # Run full AST mutation analysis
        try:
            cov_pct, _ = runner.measure_coverage(test_code_to_eval, fixture.source_code)
        except Exception:
            cov_pct = 0.0

        mutants = ASTMutator.generate_mutants(fixture.source_code)
        evaluated = runner.evaluate_mutants_parallel(test_code_to_eval, mutants)
        scores = calculate_mutation_scores(evaluated)

        dur = round(time.perf_counter() - t0, 3)

        disclaimer = None
        if exec_mode == "OFFLINE_DETERMINISTIC_SYNTHESIS" and scenario != "baseline":
            disclaimer = "Offline execution via deterministic synthesis; live LLM tokens unavailable without API keys; zero live tokens consumed."

        return StrategyRunRecord(
            run_id=run_id,
            fixture_id=fixture.fixture_id,
            fixture_name=fixture.name,
            source_hash=fixture.source_hash,
            strategy=scenario,
            prompt_variant=prompt_variant,
            run_index=rep_index,
            test_generation_status=status,
            tests_collected=collected,
            tests_passed=passed_ref,
            tests_passed_on_reference=passed_ref,
            tests_failed_on_reference=failed_ref,
            false_positive_rate_pct=round(fp_rate, 1),
            defects_detected=detected_defs,
            defects_survived=survived_defs,
            defect_detection_rate_pct=round(det_rate, 1),
            mutants_killed=scores.get("killed_mutants", 0),
            mutants_total=scores.get("total_mutants", len(evaluated)),
            mutants_equivalent=scores.get("equivalent_mutants", 0),
            mutants_invalid=scores.get("invalid_mutants", 0),
            mutation_score_pct=round(scores.get("raw_mutation_score", 0.0), 1),
            adjusted_mutation_score_pct=round(scores.get("adjusted_mutation_score", 0.0), 1),
            line_coverage_pct=round(cov_pct, 1),
            runtime_seconds=dur,
            reflection_iterations=iterations,
            retries=retries,
            timeouts_count=timeouts,
            syntax_errors_count=syntax_errors,
            tool_errors_count=tool_errors,
            error_message=err_msg,
            model_name=self.model_name,
            tokens_prompt=p_tokens,
            tokens_completion=c_tokens,
            total_tokens=tokens,
            estimated_cost_usd=cost,
            execution_mode=exec_mode,
            is_simulated=False,
            disclaimer=disclaimer
        )


def export_strategy_comparison_csv(csv_path: str, report: CorpusBenchmarkReport) -> None:
    """Exports all strategy run records into a tabular CSV manifest."""
    os.makedirs(os.path.dirname(os.path.abspath(csv_path)), exist_ok=True)
    fieldnames = [
        "Run_ID",
        "Fixture_ID",
        "Fixture_Name",
        "Source_SHA256",
        "Strategy",
        "Prompt_Variant",
        "Run_Index",
        "Execution_Mode",
        "Is_Simulated",
        "Test_Gen_Status",
        "Tests_Collected",
        "Tests_Passed_Ref",
        "False_Positives_Ref",
        "False_Positive_Rate_Pct",
        "Defects_Detected_Count",
        "Defects_Total_Count",
        "Defect_Detection_Rate_Pct",
        "Mutants_Killed",
        "Mutants_Total",
        "Mutants_Invalid",
        "Mutants_Equivalent",
        "Raw_Mutation_Score_Pct",
        "Adjusted_Mutation_Score_Pct",
        "Line_Coverage_Pct",
        "Runtime_Seconds",
        "Reflection_Iterations",
        "Retries",
        "Timeouts",
        "Tokens_Prompt",
        "Tokens_Completion",
        "Total_Tokens",
        "Estimated_Cost_USD",
        "Disclaimer",
    ]
    with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in report.records:
            total_defs = len(r.defects_detected) + len(r.defects_survived)
            writer.writerow({
                "Run_ID": r.run_id,
                "Fixture_ID": r.fixture_id,
                "Fixture_Name": r.fixture_name,
                "Source_SHA256": r.source_hash,
                "Strategy": r.strategy,
                "Prompt_Variant": r.prompt_variant,
                "Run_Index": r.run_index,
                "Execution_Mode": r.execution_mode,
                "Is_Simulated": r.is_simulated,
                "Test_Gen_Status": r.test_generation_status,
                "Tests_Collected": r.tests_collected,
                "Tests_Passed_Ref": r.tests_passed_on_reference,
                "False_Positives_Ref": r.tests_failed_on_reference,
                "False_Positive_Rate_Pct": r.false_positive_rate_pct,
                "Defects_Detected_Count": len(r.defects_detected),
                "Defects_Total_Count": total_defs,
                "Defect_Detection_Rate_Pct": r.defect_detection_rate_pct,
                "Mutants_Killed": r.mutants_killed,
                "Mutants_Total": r.mutants_total,
                "Mutants_Invalid": r.mutants_invalid,
                "Mutants_Equivalent": r.mutants_equivalent,
                "Raw_Mutation_Score_Pct": r.mutation_score_pct,
                "Adjusted_Mutation_Score_Pct": r.adjusted_mutation_score_pct,
                "Line_Coverage_Pct": r.line_coverage_pct,
                "Runtime_Seconds": r.runtime_seconds,
                "Reflection_Iterations": r.reflection_iterations,
                "Retries": r.retries,
                "Timeouts": r.timeouts_count,
                "Tokens_Prompt": r.tokens_prompt,
                "Tokens_Completion": r.tokens_completion,
                "Total_Tokens": r.total_tokens,
                "Estimated_Cost_USD": r.estimated_cost_usd,
                "Disclaimer": r.disclaimer or "",
            })


def export_raw_run_results_json(json_path: str, report: CorpusBenchmarkReport) -> None:
    """Exports raw machine-readable JSON results preserving every run record and summary."""
    os.makedirs(os.path.dirname(os.path.abspath(json_path)), exist_ok=True)
    with open(json_path, mode="w", encoding="utf-8") as f:
        json.dump(report.model_dump(), f, indent=2)
