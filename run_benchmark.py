"""
run_benchmark.py - Ablation Study: Baseline vs Zero-Shot vs Mutation-Reflected TestForge.

Course: CSE3101 - Agentic AI
Authors: Sourabh & Shreshth

Compares 3 distinct configurations:
  1. Baseline (Minimal/Weak handwritten tests)
  2. Single-Pass LLM Generation (Zero-shot test synthesis without reflection)
  3. TestForge Mutation-Reflected Suite (Iterative AST fault injection + Adversarial Critic)
"""

import os
import sys
import argparse
from rich.console import Console
from rich.table import Table

from testforge.orchestrator import TestForgeOrchestrator
from testforge.sandbox import ParallelSandboxRunner
from testforge.mutator import ASTMutator
from testforge.agents import TestGeneratorAgent
from testforge.logger import TraceLogger

console = Console()

TARGETS = {
    "banking": ("samples/banking.py", "Banking Transaction Rules"),
    "inventory": ("samples/inventory_pricing.py", "Inventory Tier Pricing"),
    "ratelimit": ("samples/rate_limiter.py", "Token Bucket Rate Limiter"),
    "statemachine": ("samples/state_machine.py", "Order FSM with RBAC")
}

BASELINE_TESTS = {
    "banking": """
from target import *
def test_nominal():
    assert banking_transaction(100.0, 50.0, 5.0) is True
def test_neg_balance():
    assert banking_transaction(-10.0, 50.0, 5.0) is False
""",
    "inventory": """
from target import *
def test_basic_calc():
    assert compute_inventory_order(100.0, 10, "REGULAR", False) == 1000.0
""",
    "ratelimit": """
from target import *
def test_nominal_limit():
    allowed, _ = evaluate_rate_limit(5.0, 10.0, 1.0, 1.0, 2)
    assert allowed is True
""",
    "statemachine": """
from target import *
def test_start_order():
    ok, st = transition_order_state("CREATED", "PAYMENT_PENDING", "CUSTOMER", 50.0)
    assert ok is True and st == "PAYMENT_PENDING"
"""
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
    parser.add_argument("--target", "-t", choices=list(TARGETS.keys()), default="banking")
    parser.add_argument("--model", "-m", default="gemini-2.5-flash")
    args = parser.parse_args()

    rel_path, desc = TARGETS[args.target]
    full_path = os.path.join(os.path.dirname(__file__), rel_path)

    with open(full_path, "r", encoding="utf-8") as f:
        target_code = f.read()

    console.print(f"[bold cyan]==========================================================[/bold cyan]")
    console.print(f"[bold cyan]      TESTFORGE ABLATION BENCHMARK: {args.target.upper()} [/bold cyan]")
    console.print(f"[dim]Target: {desc} ({rel_path})[/dim]")
    console.print(f"[bold cyan]==========================================================[/bold cyan]\n")

    sandbox = ParallelSandboxRunner(timeout_seconds=5)

    # 1. Config A: Baseline Handwritten Weak Suite
    console.print("[yellow]Evaluating Config A: Baseline Suite (Handwritten Minimal)...[/yellow]")
    baseline_code = BASELINE_TESTS[args.target]
    base_cov, base_score, base_k, base_tot = evaluate_test_suite(baseline_code, target_code, sandbox)

    # 2. Config B: Single-Pass Zero-Shot LLM
    console.print("[yellow]Evaluating Config B: Single-Pass LLM Generation (Zero-Shot No Reflection)...[/yellow]")
    zeroshot_logger = TraceLogger("trace_zeroshot.jsonl")
    generator = TestGeneratorAgent(model_name=args.model, logger=zeroshot_logger)
    zeroshot_code = generator.generate_tests(source_code=target_code, iteration=0)
    zs_cov, zs_score, zs_k, zs_tot = evaluate_test_suite(zeroshot_code, target_code, sandbox)
    zs_tokens = zeroshot_logger.get_total_tokens()

    # 3. Config C: TestForge Multi-Agent Reflection Loop
    console.print("[yellow]Evaluating Config C: TestForge Multi-Agent Reflection Loop...[/yellow]")
    tf_logger = TraceLogger("trace_reflected.jsonl")
    orchestrator = TestForgeOrchestrator(
        target_source_code=target_code,
        max_iterations=3,
        target_mutation_score=85.0,
        model_name=args.model,
        trace_log_path="trace_reflected.jsonl"
    )
    final_state = orchestrator.run()
    refl_cov, refl_score, refl_k, refl_tot = evaluate_test_suite(final_state.current_test_code, target_code, sandbox)
    refl_tokens = tf_logger.get_total_tokens()

    # Output Comparative Ablation Table
    table = Table(title=f"Ablation Benchmark Comparison: {args.target.upper()}", show_header=True)
    table.add_column("Configuration", style="bold cyan")
    table.add_column("Line Coverage", justify="center")
    table.add_column("Killed / Total", justify="center")
    table.add_column("Mutation Score", justify="center", style="bold")
    table.add_column("Total Tokens", justify="center", style="magenta")

    table.add_row("Config A: Baseline Minimal", f"{base_cov:.1f}%", f"{base_k}/{base_tot}", f"{base_score:.1f}%", "0")
    table.add_row("Config B: Zero-Shot LLM", f"{zs_cov:.1f}%", f"{zs_k}/{zs_tot}", f"{zs_score:.1f}%", f"{zs_tokens:,}")
    table.add_row("Config C: TestForge Reflected", f"{refl_cov:.1f}%", f"{refl_k}/{refl_tot}", f"[green]{refl_score:.1f}%[/green]", f"{refl_tokens:,}")

    console.print("\n")
    console.print(table)
    console.print("\n[bold green]Empirical Takeaway for CSE3101 Review:[/bold green]")
    console.print(f"• Baseline vs Reflected delta: [bold]+{refl_score - base_score:.1f}%[/bold] mutation kill rate.")
    console.print(f"• Zero-Shot vs Reflected delta: [bold]+{refl_score - zs_score:.1f}%[/bold] mutation kill rate.")
    console.print(f"• Deterministic reflection drives assertion hardening beyond simple line-coverage ceilings.\n")

if __name__ == "__main__":
    main()
