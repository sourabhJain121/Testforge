"""
run_benchmark.py - Ablation Study: Baseline vs Zero-Shot vs Mutation-Reflected TestForge.

Course: CSE3101 - Agentic AI
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

from testforge.orchestrator import TestForgeOrchestrator
from testforge.sandbox import ParallelSandboxRunner
from testforge.mutator import ASTMutator
from testforge.agents import TestGeneratorAgent
from testforge.logger import TraceLogger

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
    }
}


def evaluate_test_suite(test_code: str, target_code: str, sandbox: ParallelSandboxRunner):
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
    parser.add_argument("--model", "-m", default="gemini-3.6-flash", help="Foundation model name")
    parser.add_argument("--output-json", "-j", default="benchmark_results.json", help="Path to save benchmark JSON")
    args = parser.parse_args()

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
    console.print(f"[bold cyan]==========================================================[/bold cyan]\n")

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

    console.print(f"\n[green][✓] Benchmark results saved to: {args.output_json}[/green]")
    console.print(f"[green][✓] Hardened suite exported to: test_hardened.py[/green]")
    console.print("[dim]Run standalone verification with: pytest test_hardened.py -v[/dim]\n")


if __name__ == "__main__":
    main()
