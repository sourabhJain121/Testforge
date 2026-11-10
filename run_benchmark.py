"""
run_benchmark.py - Ablation Study: Baseline vs Zero-Shot vs Mutation-Reflected TestForge.

System: Autonomous Multi-Agent Hardening Engine
Authors: Sourabh & Shreshth

Compares 3 distinct configurations:
  1. Baseline (Minimal/Weak handwritten tests)
  2. Single-Pass LLM Generation (Zero-shot test synthesis without reflection)
  3. TestForge Mutation-Reflected Suite (Iterative AST fault injection + Adversarial Critic)

Outputs:
  - Rich comparison table in terminal
  - Persisted results in benchmark_results.json
"""

import os
import sys
import json
import time
import argparse
from rich.console import Console
from rich.table import Table
from testforge.mutator import ASTMutator
from testforge.benchmarking import BenchmarkRunner, BenchmarkReport

console = Console()

TARGET_CONFIGS = {
    "samples/discount.py": {
        "desc": "E-Commerce Discount Rules",
        "baseline_tests": """
from target import *
def test_nominal_discount():
    assert calculate_discount(100.0, 2, False) == 100.0
"""
    },
    "samples/banking.py": {
        "desc": "Banking Transaction Rules",
        "baseline_tests": """
from target import *
def test_nominal():
    assert banking_transaction(100.0, 50.0, 5.0) is True
def test_neg_balance():
    assert banking_transaction(-10.0, 50.0, 5.0) is False
"""
    },
    "samples/inventory_pricing.py": {
        "desc": "Inventory Tier Pricing",
        "baseline_tests": """
from target import *
def test_basic_calc():
    assert compute_inventory_order(100.0, 10, "REGULAR", False) == 1000.0
"""
    },
    "samples/rate_limiter.py": {
        "desc": "Token Bucket Rate Limiter",
        "baseline_tests": """
from target import *
def test_nominal_limit():
    allowed, _ = evaluate_rate_limit(5.0, 10.0, 1.0, 1.0, 2)
    assert allowed is True
"""
    },
    "samples/state_machine.py": {
        "desc": "Order FSM with RBAC",
        "baseline_tests": """
from target import *
def test_start_order():
    ok, st = transition_order_state("CREATED", "PAYMENT_PENDING", "CUSTOMER", 50.0)
    assert ok is True and st == "PAYMENT_PENDING"
"""
    },
    "samples/currency_converter.py": {
        "desc": "Deterministic Currency Converter",
        "baseline_tests": """
from target import *
def test_nominal():
    assert convert_currency(100.0, "USD", "EUR") == 92.41
def test_same_curr():
    assert convert_currency(100.0, "USD", "USD") == 100.0
"""
    }
}


def evaluate_test_suite(test_code: str, target_code: str, sandbox):
    """Measures Line Coverage and Mutation Score for a test suite."""
    cov_pct, _ = sandbox.measure_coverage(test_code, target_code)
    mutants = ASTMutator.generate_mutants(target_code)
    evaluated = sandbox.evaluate_mutants_parallel(test_code, mutants)
    killed = sum(1 for m in evaluated if m.status in ("KILLED", "TIMEOUT"))
    total = len(evaluated)
    score = (killed / total * 100.0) if total > 0 else 0.0
    return cov_pct, score, killed, total


def main():
    parser = argparse.ArgumentParser(description="TestForge Ablation Benchmark")
    parser.add_argument(
        "--target", "-t",
        default="samples/discount.py",
        help="Path to Python target source file (default: samples/discount.py)"
    )
    parser.add_argument(
        "--corpus", "-c",
        action="store_true",
        help="Execute benchmark comparison across all 5 evaluation corpus fixtures"
    )
    parser.add_argument("--model", "-m", default="gemini-3.6-flash", help="Foundation model name")
    parser.add_argument("--output-json", "-j", default="benchmark_results.json", help="Path to save benchmark JSON")
    parser.add_argument(
        "--fast", "-f",
        action="store_true",
        help="Execute in fast deterministic offline mock mode (sub-second simulated AST analysis for CI/CD checks without invoking live LLMs or slow subprocesses)"
    )
    parser.add_argument(
        "--repetitions", "-r",
        type=int,
        default=1,
        help="Number of repetitions to run (default: 1)"
    )
    parser.add_argument(
        "--pilot",
        action="store_true",
        help="Execute in pilot mode with a subset of fixtures (default: 2 fixtures)"
    )
    parser.add_argument(
        "--max-cases",
        type=int,
        default=None,
        help="Limit execution to the first N fixtures (pilot subset)"
    )
    parser.add_argument(
        "--force-live",
        action="store_true",
        help="Authorize and execute against live foundation model API (requires GEMINI_API_KEY or OPENROUTER_API_KEY)"
    )
    parser.add_argument(
        "--export-dir",
        type=str,
        default=None,
        help="Directory to save STRATEGY_COMPARISON.csv and RAW_RUN_RESULTS.json"
    )
    args = parser.parse_args()

    if args.corpus:
        from testforge.corpus.runner import (
            CorpusBenchmarkRunner,
            export_strategy_comparison_csv,
            export_raw_run_results_json,
        )
        max_cases = args.max_cases if args.max_cases else (2 if args.pilot else None)
        console.print("[bold cyan]==========================================================[/bold cyan]")
        console.print("[bold cyan]       TESTFORGE EVALUATION CORPUS BENCHMARK (GAP-05)     [/bold cyan]")
        console.print(f"[dim]Fixtures: {max_cases or 5} modules | Fast Mock: {args.fast} | Pilot: {bool(max_cases)} | Reps: {args.repetitions} | Live: {args.force_live}[/dim]")
        console.print("[bold cyan]==========================================================[/bold cyan]\n")

        runner = CorpusBenchmarkRunner(model_name=args.model, fast_mode=args.fast)
        report = runner.run_benchmark(
            repetitions=args.repetitions,
            max_cases=max_cases,
            force_live=args.force_live
        )

        table = Table(title="Corpus Benchmark Individual Runs", show_header=True)
        table.add_column("Fixture", style="bold cyan")
        table.add_column("Strategy", justify="center")
        table.add_column("Rep", justify="center")
        table.add_column("Status", justify="center")
        table.add_column("Line Cov", justify="center")
        table.add_column("Mut Score (K/T)", justify="center", style="bold")
        table.add_column("Defects", justify="center")
        table.add_column("False Pos", justify="center")
        table.add_column("Latency", justify="center")
        table.add_column("Tokens", justify="center")
        table.add_column("Mode", justify="center")

        for r in report.records:
            score_styled = f"[green]{r.mutation_score_pct}%[/green]" if r.mutation_score_pct >= 80.0 else f"{r.mutation_score_pct}%"
            mut_fraction = f"{r.mutants_killed}/{r.mutants_total}"
            def_fraction = f"{len(r.defects_detected)}/{len(r.defects_detected) + len(r.defects_survived)}"
            mode_tag = "SIMULATED" if r.is_simulated else r.execution_mode[:12]
            table.add_row(
                r.fixture_name,
                r.strategy,
                f"#{r.run_index}",
                r.test_generation_status,
                f"{r.line_coverage_pct}%",
                f"{score_styled} ({mut_fraction})",
                f"{def_fraction} ({r.defect_detection_rate_pct:.0f}%)",
                str(r.tests_failed_on_reference),
                f"{r.runtime_seconds:.2f}s",
                f"{r.total_tokens:,}",
                mode_tag
            )

        console.print(table)

        # Strategy Statistical Summary Table
        if report.strategy_summaries:
            sum_table = Table(title="\nStrategy Statistical Aggregation Summary", show_header=True)
            sum_table.add_column("Strategy", style="bold green")
            sum_table.add_column("Runs", justify="center")
            sum_table.add_column("Defect Rate (Mean±SD)", justify="center")
            sum_table.add_column("MutScore Raw", justify="center", style="bold")
            sum_table.add_column("MutScore Adj", justify="center")
            sum_table.add_column("Line Cov", justify="center")
            sum_table.add_column("Latency (Mean)", justify="center")
            sum_table.add_column("False Pos Rate", justify="center")
            sum_table.add_column("Total Tokens", justify="center")
            sum_table.add_column("Total Cost (USD)", justify="center")

            for strat, s in report.strategy_summaries.items():
                sum_table.add_row(
                    strat,
                    str(s.runs_count),
                    f"{s.mean_defect_detection_rate:.1f}% ±{s.stddev_defect_detection_rate:.1f}%",
                    f"{s.mean_mutation_score:.1f}% ±{s.stddev_mutation_score:.1f}%",
                    f"{s.mean_adjusted_mutation_score:.1f}%",
                    f"{s.mean_line_coverage:.1f}%",
                    f"{s.mean_runtime_seconds:.3f}s",
                    f"{s.mean_false_positive_rate:.1f}%",
                    f"{s.total_tokens:,}",
                    f"${s.total_cost_usd:.5f}"
                )
            console.print(sum_table)

        with open(args.output_json, "w", encoding="utf-8") as jf:
            json.dump(report.model_dump(), jf, indent=2)

        md_path = os.path.splitext(args.output_json)[0] + ".md"
        with open(md_path, "w", encoding="utf-8") as mf:
            mf.write(report.to_markdown())

        if args.export_dir:
            csv_path = os.path.join(args.export_dir, "STRATEGY_COMPARISON.csv")
            json_path = os.path.join(args.export_dir, "RAW_RUN_RESULTS.json")
            export_strategy_comparison_csv(csv_path, report)
            export_raw_run_results_json(json_path, report)
            console.print(f"[green][✓] Exported CSV to: {csv_path}[/green]")
            console.print(f"[green][✓] Exported Raw JSON to: {json_path}[/green]")

        console.print(f"\n[green][✓] Corpus benchmark saved to: {args.output_json}[/green]")
        console.print(f"[green][✓] Markdown report saved to: {md_path}[/green]\n")
        return

    norm_target = os.path.normpath(args.target)
    if not os.path.exists(norm_target):
        console.print(f"[bold red]Error: Target file '{norm_target}' not found.[/bold red]")
        sys.exit(1)

    with open(norm_target, "r", encoding="utf-8") as f:
        target_code = f.read()

    config_info = TARGET_CONFIGS.get(norm_target, {
        "desc": "Custom Python Module",
        "baseline_tests": "from target import *\ndef test_dummy(): pass\n"
    })

    console.print(f"[bold cyan]==========================================================[/bold cyan]")
    console.print(f"[bold cyan]             TESTFORGE ABLATION BENCHMARK                 [/bold cyan]")
    console.print(f"[dim]Target: {norm_target} ({config_info['desc']})[/dim]")
    if args.fast:
        console.print("[bold yellow]Mode: FAST DETERMINISTIC OFFLINE MOCK (CI/CD)[/bold yellow]")
    console.print(f"[bold cyan]==========================================================[/bold cyan]\n")

    if args.fast:
        if args.output_json == "benchmark_results.json":
            args.output_json = "benchmark_results_fast.json"

        console.print("[bold yellow]⚡ FAST DETERMINISTIC BENCHMARK MODE ACTIVE[/bold yellow]")
        console.print("[dim]Simulating repeatable AST mutation and reflection loops for rapid offline CI validation...[/dim]\n")

        runner = BenchmarkRunner(
            target_code=target_code,
            target_file_path=norm_target,
            baseline_tests=config_info.get("baseline_tests"),
            model_name=args.model,
            fast_mode=True
        )
        report = runner.run_benchmark(repetitions=args.repetitions)

        results = {
            "target_file": norm_target,
            "model": args.model,
            "mode": "fast-mock",
            "simulated": True,
            "disclaimer": "SIMULATED OFFLINE BENCHMARK: Results are deterministic fixtures for CI/CD checks and do NOT represent real foundation model synthesis quality or live API latency.",
            "timestamp": time.time(),
            "repetitions": args.repetitions,
            "runs": []
        }
        for r in report.runs:
            results["runs"].append({
                "run_type": f"{r.scenario} (rep {r.run_index})" if args.repetitions > 1 else r.scenario,
                "line_coverage_pct": r.metrics.calculated.get("line_coverage_pct", 0.0),
                "mutation_score_pct": r.metrics.calculated.get("mutation_score_pct", 0.0),
                "killed_mutants": r.metrics.measured.get("killed_mutants", 0),
                "total_mutants": r.metrics.measured.get("total_mutants", 0),
                "iterations": r.metrics.measured.get("iterations", 0),
                "latency_seconds": r.metrics.measured.get("duration_seconds", 0.0),
                "tokens_used": r.metrics.measured.get("total_tokens", 0),
                "simulated": True,
            })
    else:
        from testforge.sandbox import ParallelSandboxRunner
        from testforge.logger import TraceLogger
        from testforge.agents import TestGeneratorAgent
        from testforge.orchestrator import TestForgeOrchestrator
        sandbox = ParallelSandboxRunner(timeout_seconds=5)
        results = {
            "target_file": norm_target,
            "model": args.model,
            "timestamp": time.time(),
            "runs": []
        }

        # 1. Condition A: Baseline (Existing / minimal handwritten tests)
        console.print("[yellow]▶ [Condition A] Evaluating Baseline Suite...[/yellow]")
        start_a = time.perf_counter()
        baseline_code = config_info["baseline_tests"]
        base_cov, base_score, base_k, base_tot = evaluate_test_suite(baseline_code, target_code, sandbox)
        latency_a = time.perf_counter() - start_a

        results["runs"].append({
            "run_type": "Condition A (Baseline Minimal)",
            "line_coverage_pct": round(base_cov, 1),
            "mutation_score_pct": round(base_score, 1),
            "killed_mutants": base_k,
            "total_mutants": base_tot,
            "iterations": 0,
            "latency_seconds": round(latency_a, 2),
            "tokens_used": 0
        })

        # 2. Condition B: Single-Pass Zero-Shot LLM Generation
        console.print("[yellow]▶ [Condition B] Evaluating Zero-Shot Single-Pass (No Reflection)...[/yellow]")
        zs_trace_file = "trace_zeroshot.jsonl"
        if os.path.exists(zs_trace_file):
            os.remove(zs_trace_file)
        zeroshot_logger = TraceLogger(zs_trace_file)

        start_b = time.perf_counter()
        generator = TestGeneratorAgent(model_name=args.model, logger=zeroshot_logger)
        zeroshot_code = generator.generate_tests(source_code=target_code, iteration=0)
        zs_cov, zs_score, zs_k, zs_tot = evaluate_test_suite(zeroshot_code, target_code, sandbox)
        latency_b = time.perf_counter() - start_b
        zs_tokens = zeroshot_logger.get_total_tokens()

        results["runs"].append({
            "run_type": "Condition B (Zero-Shot Single-Pass)",
            "line_coverage_pct": round(zs_cov, 1),
            "mutation_score_pct": round(zs_score, 1),
            "killed_mutants": zs_k,
            "total_mutants": zs_tot,
            "iterations": 1,
            "latency_seconds": round(latency_b, 2),
            "tokens_used": zs_tokens
        })

        # 3. Condition C: TestForge Full Reflection Loop
        console.print("[yellow]▶ [Condition C] Evaluating TestForge Full Mutation-Reflection Loop...[/yellow]")
        refl_trace_file = "trace_reflected.jsonl"
        if os.path.exists(refl_trace_file):
            os.remove(refl_trace_file)

        start_c = time.perf_counter()
        orchestrator = TestForgeOrchestrator(
            target_source_code=target_code,
            max_iterations=3,
            target_mutation_score=85.0,
            model_name=args.model,
            trace_log_path=refl_trace_file,
            target_file_path=norm_target
        )
        final_state = orchestrator.run()
        refl_cov, refl_score, refl_k, refl_tot = evaluate_test_suite(final_state.current_test_code, target_code, sandbox)
        latency_c = time.perf_counter() - start_c
        refl_tokens = orchestrator.logger.get_total_tokens()

        # Export hardened tests
        orchestrator.export_hardened_suite(output_path="test_hardened.py")

        results["runs"].append({
            "run_type": "Condition C (TestForge Full Reflection)",
            "line_coverage_pct": round(refl_cov, 1),
            "mutation_score_pct": round(refl_score, 1),
            "killed_mutants": refl_k,
            "total_mutants": refl_tot,
            "iterations": final_state.current_iteration,
            "latency_seconds": round(latency_c, 2),
            "tokens_used": refl_tokens
        })

    # Render Terminal Comparison Table
    table = Table(title=f"Ablation Benchmark Summary: {norm_target}", show_header=True)
    table.add_column("Run Type", style="bold cyan")
    table.add_column("Line Coverage", justify="center")
    table.add_column("Mutation Score", justify="center", style="bold")
    table.add_column("Iterations", justify="center")
    table.add_column("Latency (s)", justify="center")
    table.add_column("Tokens Used", justify="center", style="magenta")

    for run in results["runs"]:
        score_styled = f"[green]{run['mutation_score_pct']}%[/green]" if run["mutation_score_pct"] >= 85.0 else f"{run['mutation_score_pct']}%"
        table.add_row(
            run["run_type"],
            f"{run['line_coverage_pct']}%",
            score_styled,
            str(run["iterations"]),
            f"{run['latency_seconds']:.2f}s",
            f"{run['tokens_used']:,}"
        )

    console.print("\n")
    console.print(table)

    # Save to benchmark_results.json
    with open(args.output_json, "w", encoding="utf-8") as jf:
        json.dump(results, jf, indent=2)

    md_path = os.path.splitext(args.output_json)[0] + ".md"
    md_lines = [
        f"# TestForge Ablation Benchmark Report: {norm_target}",
        f"- **Target File:** `{norm_target}`",
        f"- **Description:** {config_info.get('desc', 'Python Module')}",
        f"- **Model:** `{args.model}`",
        f"- **Timestamp:** {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(results['timestamp']))}",
        "",
        "## Ablation Performance Comparison",
        "",
        "| Run Condition | Line Coverage | Mutation Score | Iterations | Latency (s) | Tokens Used |",
        "|---|---|---|---|---|---|",
    ]
    for r in results["runs"]:
        md_lines.append(
            f"| **{r['run_type']}** | {r['line_coverage_pct']}% | {r['mutation_score_pct']}% | {r['iterations']} | {r['latency_seconds']:.2f}s | {r['tokens_used']:,} |"
        )
    md_lines.extend([
        "",
        "## Metrics Integrity Disclosure",
        "- **Measured:** Wall-clock latency, mutant kill counts, and exact token counts are captured directly from execution and telemetry.",
        "- **Calculated:** Mutation scores and coverage percentages are computed deterministically via AST analysis.",
        "- **Estimated:** Model cost estimates are computed from published Gemini token pricing ($0.075/1M prompt, $0.30/1M completion).",
        ""
    ])
    with open(md_path, "w", encoding="utf-8") as mf:
        mf.write("\n".join(md_lines))

    console.print(f"\n[green][✓] Benchmark results saved to: {args.output_json}[/green]")
    console.print(f"[green][✓] Benchmark Markdown report saved to: {md_path}[/green]")
    console.print(f"[green][✓] Hardened suite exported to: test_hardened.py[/green]")
    console.print("[dim]Run standalone verification with: pytest test_hardened.py -v[/dim]\n")


if __name__ == "__main__":
    main()
