"""
cli.py - Enterprise Standalone CLI for TestForge.

Authors: Sourabh & Shreshth
Course: CSE3101 - Agentic AI
"""

import argparse
import json
import os
import sys
from typing import List, Optional, Tuple

from rich.console import Console
from rich.prompt import Prompt

from testforge.export import generate_junit_xml, generate_sarif_report
from testforge.ingestion import TargetManagerAgent
from testforge.orchestrator import TestForgeOrchestrator

console = Console()


def interactive_menu() -> Tuple[Optional[str], Optional[str]]:
    """Interactive CLI menu when no arguments are passed."""
    console.print("\n[bold cyan]==========================================================[/bold cyan]")
    console.print("[bold cyan]       TESTFORGE SUPERVISOR: TARGET SELECTION MENU        [/bold cyan]")
    console.print("[bold cyan]==========================================================[/bold cyan]")
    console.print("1. Ingest & Test an arbitrary Python file from disk")
    console.print("2. Synthesize a brand-new Python module via Natural-Language Prompt")
    console.print("3. Run built-in sample: samples/discount.py")
    console.print("4. Run built-in sample: samples/banking.py")
    console.print("[bold cyan]----------------------------------------------------------[/bold cyan]")

    choice = Prompt.ask("Select an option", choices=["1", "2", "3", "4"], default="3")

    if choice == "1":
        file_path = Prompt.ask("Enter the path to the Python file")
        return file_path.strip(), None
    elif choice == "2":
        prompt_text = Prompt.ask("Describe the module to synthesize")
        return None, prompt_text.strip()
    elif choice == "3":
        return "samples/discount.py", None
    else:
        return "samples/banking.py", None


def export_job_report(job_id: str, report_format: str, output_path: Optional[str] = None, db_path: Optional[str] = None) -> str:
    """Exports JUnit XML or SARIF v2.1.0 report directly from SQLite checkpoints."""
    from testforge.persistence import SQLiteBlackboardStorage
    db_file = db_path or os.environ.get("TESTFORGE_CHECKPOINT_DB", "qa_artifacts/testforge_checkpoints.db")

    if not os.path.exists(db_file):
        raise FileNotFoundError(f"Checkpoint database not found at: {db_file}")

    storage = SQLiteBlackboardStorage(db_file)
    try:
        rec = storage.get_latest_checkpoint(job_id=job_id)
        if not rec:
            raise ValueError(f"No checkpoint found for job_id '{job_id}' in {db_file}")

        snap = json.loads(rec.snapshot_json) if isinstance(rec.snapshot_json, str) else rec.snapshot_json
        target_mod = (
            snap.get("target", {}).get("target_module_path")
            or snap.get("target_space", {}).get("target_file_path")
            or "target.py"
        )
        mutants = snap.get("mutant", {}).get("mutants") or snap.get("mutants", [])
        suite_space = snap.get("suite", {})
        sec_space = snap.get("security", {}) or snap.get("security_space", {})

        job_record = {
            "job_id": job_id,
            "target_file_path": target_mod,
            "final_state": {
                "target_module_path": target_mod,
                "mutants": mutants,
                "baseline_run": {
                    "tests_executed": suite_space.get("baseline_tests_executed", 1),
                    "tests_passed": suite_space.get("baseline_tests_passed", 1),
                    "tests_failed": suite_space.get("baseline_tests_failed", 0),
                },
                "security_space": sec_space,
            }
        }
    finally:
        storage.close()

    fmt_lower = report_format.lower()
    if fmt_lower == "junit":
        content = generate_junit_xml(job_id, job_record)
        ext = "xml"
    elif fmt_lower == "sarif":
        sarif_data = generate_sarif_report(job_id, job_record)
        content = json.dumps(sarif_data, indent=2)
        ext = "sarif"
    else:
        raise ValueError(f"Unsupported report format: {report_format}. Choose 'junit' or 'sarif'.")

    if not output_path:
        os.makedirs("qa_artifacts", exist_ok=True)
        output_path = f"qa_artifacts/testforge-{fmt_lower}-{job_id}.{ext}"

    out_dir = os.path.dirname(output_path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(content)

    return output_path


def cmd_harden(args: argparse.Namespace) -> int:
    """Executes headless test hardening via CLI."""
    target_path = args.target_path
    console.print("\n[bold cyan]⚡ TestForge Autonomous Hardener[/bold cyan]")
    console.print(f"  Target: [bold]{target_path}[/bold]")
    console.print(f"  Target Score: [bold]{args.target_score}%[/bold] | Max Iterations: [bold]{args.max_iterations}[/bold]")

    supervisor = TargetManagerAgent(model_name=args.model)
    try:
        analysis = supervisor.ingest_file(target_path)
    except FileNotFoundError:
        console.print(f"\n[bold red][!] FileNotFoundError: Target file not found at:[/bold red] '{target_path}'")
        return 1

    if analysis.has_syntax_error:
        console.print(f"[bold red][!] Target file has syntax errors: {analysis.error_msg}[/bold red]")
        return 1

    console.print(f"[green][✓] Target validated: module '{analysis.module_name}' ({len(analysis.functions)} functions, {len(analysis.classes)} classes)[/green]")

    initial_tests = None
    if getattr(args, "tests", None) and os.path.exists(args.tests):
        with open(args.tests, "r", encoding="utf-8") as f:
            initial_tests = f.read()

    if getattr(args, "privacy_mode", False):
        from testforge.privacy_mode import PrivacyModeManager
        PrivacyModeManager.get_instance().enable()
        console.print("[bold green][🔒 Privacy Mode Active][/bold green] Zero-egress air-gap enforced. Local models only.")

    orchestrator = TestForgeOrchestrator(
        target_source_code=analysis.source_code,
        initial_test_code=initial_tests,
        max_iterations=args.max_iterations,
        target_mutation_score=args.target_score,
        model_name=args.model,
        target_file_path=target_path,
        engine_mode=args.engine_mode,
        privacy_mode=getattr(args, "privacy_mode", False),
    )

    console.print("[dim]Executing multi-agent hardening pipeline...[/dim]")
    final_state = orchestrator.run()

    # Extract coverage and mutation metrics from orchestrator state and blackboard spaces
    try:
        metrics_space = orchestrator.blackboard.get_metrics_space()
    except Exception:
        metrics_space = None

    try:
        exec_space = orchestrator.blackboard.get_execution_space()
    except Exception:
        exec_space = None

    # Line Coverage
    line_cov = getattr(orchestrator.state, "line_coverage", None) or (metrics_space.statement_coverage if metrics_space else None)
    if not line_cov and final_state:
        line_cov = getattr(final_state, "line_coverage", None) or getattr(final_state, "baseline_line_coverage", None) or getattr(final_state, "baseline_line_coverage_pct", None)
    if (not line_cov or float(line_cov) == 0.0) and exec_space:
        line_cov = getattr(exec_space, "line_coverage_pct", 0.0)
    line_cov = float(line_cov or 0.0)

    # Branch Coverage
    branch_cov = getattr(orchestrator.state, "branch_coverage", None) or (metrics_space.branch_coverage if metrics_space else None)
    if not branch_cov and final_state:
        branch_cov = getattr(final_state, "branch_coverage", None) or getattr(final_state, "baseline_branch_coverage", None) or getattr(final_state, "baseline_branch_coverage_pct", None)
    if (not branch_cov or float(branch_cov) == 0.0) and exec_space:
        branch_cov = getattr(exec_space, "branch_coverage_pct", None) or getattr(exec_space, "branch_coverage", 0.0)
    branch_cov = float(branch_cov or 0.0)

    # Mutation Scores (Raw & Adjusted)
    raw_mut = getattr(final_state, "final_mutation_score", None)
    if raw_mut is None:
        raw_mut = getattr(final_state, "raw_mutation_score", None)
    if raw_mut is None and metrics_space:
        raw_mut = getattr(metrics_space, "final_mutation_score", None) or getattr(metrics_space, "raw_mutation_score", 0.0)
    raw_mut = float(raw_mut or 0.0)

    adj_score = metrics_space.adjusted_mutation_score if metrics_space else None
    if adj_score is None and final_state:
        adj_score = getattr(final_state, "adjusted_mutation_score", None)
    if adj_score is None:
        adj_score = raw_mut
    adj_score = float(adj_score or 0.0)

    console.print(
        f"\n[bold green][✓] Hardening Complete: Line Cov: {line_cov:.1f}% | "
        f"Branch Cov: {branch_cov:.1f}% | "
        f"Mutation Score: {raw_mut:.1f}% (Adj: {adj_score:.1f}%)[/bold green]"
    )

    # Determine export destination
    if args.output:
        out_path = args.output
    else:
        out_dir = args.output_dir or "./qa_artifacts"
        os.makedirs(out_dir, exist_ok=True)
        mod_clean = os.path.splitext(os.path.basename(target_path))[0]
        out_path = os.path.join(out_dir, f"test_hardened_{mod_clean}.py")

    orchestrator.export_hardened_suite(output_path=out_path)
    console.print(f"[bold green][TestForge] Exported test suite to: {out_path}[/bold green]\n")
    return 0


# Canonical aliases
handle_harden_command = cmd_harden


def handle_benchmark_command(args: argparse.Namespace) -> int:
    """Executes multi-target empirical benchmark suite."""
    from testforge.benchmarking import MultiTargetBenchmarkRunner

    targets_raw = [t.strip() for t in args.targets.split(",") if t.strip()]
    resolved_targets: List[str] = []
    for t in targets_raw:
        if os.path.exists(t):
            resolved_targets.append(t)
        elif os.path.exists(f"samples/{t}.py"):
            resolved_targets.append(f"samples/{t}.py")
        elif os.path.exists(f"samples/{t}"):
            resolved_targets.append(f"samples/{t}")
        else:
            resolved_targets.append(t)

    scenarios = [s.strip() for s in args.scenarios.split(",") if s.strip()]
    out_dir = os.path.dirname(args.output) or "qa_artifacts"
    os.makedirs(out_dir, exist_ok=True)

    console.print("\n[bold cyan]⚡ TestForge Empirical Benchmark Runner[/bold cyan]")
    console.print(f"  Targets: {resolved_targets}")
    console.print(f"  Scenarios: {scenarios}")
    console.print(f"  Fast Heuristic Mode: {args.fast}")

    runner = MultiTargetBenchmarkRunner(
        target_modules=resolved_targets,
        scenarios=scenarios,
        output_dir=out_dir,
        fast_mode=args.fast,
        engine_mode=args.engine_mode,
        model_name=args.model,
    )

    results = runner.run()

    saved_json = results.get("saved_json_path", os.path.join(out_dir, "MULTI_TARGET_BENCHMARK_RESULTS.json"))
    # If args.output specifies a specific file path different from default runner path, write it
    if args.output and os.path.abspath(args.output) != os.path.abspath(saved_json):
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
        saved_json = args.output

    console.print(f"\n[bold green][✓] Benchmark run complete! Results written to: {saved_json}[/bold green]")
    return 0


def handle_export_command(args: argparse.Namespace) -> int:
    """Exports JUnit XML or SARIF from SQLite checkpoints without web server."""
    console.print("\n[bold cyan]⚡ TestForge Report Exporter[/bold cyan]")
    console.print(f"  Job ID: [bold]{args.job_id}[/bold] | Format: [bold]{args.format.upper()}[/bold]")

    try:
        out_file = export_job_report(
            job_id=args.job_id,
            report_format=args.format,
            output_path=args.output,
            db_path=args.db_path,
        )
        console.print(f"[bold green][✓] Exported {args.format.upper()} report to: {out_file}[/bold green]\n")
        return 0
    except Exception as exc:
        console.print(f"[bold red][!] Export failed: {exc}[/bold red]\n")
        return 1


def main():
    parser = argparse.ArgumentParser(description="TestForge: Enterprise Autonomous Test Hardening CLI")

    # Top-level legacy arguments
    parser.add_argument("--target", "-t", default=None, help="Path to arbitrary Python target source file")
    parser.add_argument("--create", "-c", default=None, help="Synthesize a new Python module from a natural language prompt")
    parser.add_argument("--tests", "-s", default=None, help="Path to initial test file (optional)")
    parser.add_argument("--max-iter", "-i", type=int, default=3, help="Maximum reflection iterations")
    parser.add_argument("--target-score", "-score", type=float, default=85.0, help="Target mutation score (pct)")
    parser.add_argument("--model", "-m", default="gemini-3.6-flash", help="LLM foundation model name")
    parser.add_argument("--engine-mode", "-e", choices=["auto", "cloud", "openrouter", "local"], default="auto", help="Engine execution mode (auto, cloud, openrouter, local)")
    parser.add_argument("--output", "-o", default=None, help="Output file for hardened tests")
    parser.add_argument("--privacy-mode", action="store_true", help="Enforce zero-egress air-gap isolation and PII scrubbing")

    subparsers = parser.add_subparsers(dest="subcommand", help="Available subcommands")

    # Subcommand: harden
    harden_p = subparsers.add_parser("harden", help="Autonomously harden test suite for a target module")
    harden_p.add_argument("target_path", help="Path to Python target source file to harden")
    harden_p.add_argument("--target-score", type=float, default=85.0, help="Target mutation score (default: 85.0)")
    harden_p.add_argument("--max-iterations", "-i", type=int, default=3, help="Maximum reflection iterations (default: 3)")
    harden_p.add_argument("--output-dir", default="./qa_artifacts", help="Directory to save hardened test artifacts (default: ./qa_artifacts)")
    harden_p.add_argument("--output", "-o", default=None, help="Specific output filename for hardened test suite")
    harden_p.add_argument("--model", "-m", default="gemini-3.6-flash", help="LLM foundation model name")
    harden_p.add_argument("--engine-mode", "-e", choices=["auto", "cloud", "openrouter", "local"], default="auto", help="Engine execution mode")
    harden_p.add_argument("--tests", "-s", default=None, help="Path to initial test file (optional)")
    harden_p.add_argument("--privacy-mode", action="store_true", help="Enforce zero-egress air-gap isolation and PII scrubbing")

    # Subcommand: benchmark
    bench_p = subparsers.add_parser("benchmark", help="Execute multi-target empirical benchmark suite")
    bench_p.add_argument("--targets", default="discount,lru_cache,order_fsm,stats_calculator", help="Comma-separated target module names or paths")
    bench_p.add_argument("--output", "-o", default="qa_artifacts/MULTI_TARGET_BENCHMARK_RESULTS.json", help="Path to write JSON benchmark results")
    bench_p.add_argument("--fast", action="store_true", help="Run benchmark in fast heuristic mode without LLM calls")
    bench_p.add_argument("--scenarios", default="baseline,zeroshot,agentic_reflection", help="Comma-separated benchmark scenarios")
    bench_p.add_argument("--model", default="gemini-3.6-flash", help="LLM model name for synthesis")
    bench_p.add_argument("--engine-mode", default="auto", choices=["auto", "cloud", "openrouter", "local"], help="Engine execution mode")

    # Subcommand: export
    export_p = subparsers.add_parser("export", help="Export CI/CD reports (JUnit XML or OASIS SARIF)")
    export_p.add_argument("--job-id", required=True, help="Job identifier to export")
    export_p.add_argument("--format", choices=["junit", "sarif"], default="junit", help="Report format (junit or sarif)")
    export_p.add_argument("--output", "-o", default=None, help="Output file path (default: qa_artifacts/testforge-<format>-<job_id>.<ext>)")
    export_p.add_argument("--db-path", default=None, help="Path to SQLite checkpoints database")

    args = parser.parse_args()

    # Route based on subcommand
    if args.subcommand == "harden":
        sys.exit(handle_harden_command(args))
    elif args.subcommand == "benchmark":
        sys.exit(handle_benchmark_command(args))
    elif args.subcommand == "export":
        sys.exit(handle_export_command(args))

    # Fallback to legacy behavior
    target_path = args.target
    prompt_create = args.create

    # If no flags passed, trigger interactive supervisor menu
    if not target_path and not prompt_create:
        target_path, prompt_create = interactive_menu()

    supervisor = TargetManagerAgent(model_name=args.model)

    # Mode B: Autonomous Code Synthesis
    if prompt_create:
        console.print(f"\n[bold yellow]▶ [Mode B: Synthesis] Synthesizing module from prompt:[/bold yellow] '{prompt_create}'...")
        target_path, source_code = supervisor.synthesize_module(prompt_create)
        console.print(f"[bold green][✓] Successfully synthesized module at: {target_path}[/bold green]\n")
    else:
        # Mode A: Arbitrary File Ingestion
        console.print(f"\n[bold yellow]▶ [Mode A: Ingestion] Ingesting & analyzing target:[/bold yellow] {target_path}...")
        try:
            analysis = supervisor.ingest_file(target_path)
        except FileNotFoundError:
            console.print(f"\n[bold red][!] FileNotFoundError: Target file not found at:[/bold red] '{target_path}'")
            console.print("[yellow]Hint: Provide a path to a real Python file that exists on your system, for example:[/yellow]")
            console.print("  • Built-in sample: [cyan]python -m testforge.cli --target samples/discount.py[/cyan]")
            console.print("  • Built-in sample: [cyan]python -m testforge.cli --target samples/banking.py[/cyan]")
            console.print("  • Or generate one: [cyan]python -m testforge.cli --create \"Currency converter with exchange fees\"[/cyan]\n")
            sys.exit(1)

        if analysis.has_syntax_error:
            console.print(f"[bold red][!] Ingested file has syntax errors: {analysis.error_msg}[/bold red]")
            sys.exit(1)
        console.print(f"[green][✓] Target Validated. Module: [bold]{analysis.module_name}[/bold][/green]")
        console.print(f"    Functions found: {analysis.functions or 'None'}")
        console.print(f"    Classes found: {analysis.classes or 'None'}\n")
        source_code = analysis.source_code

    initial_tests = None
    if args.tests:
        if os.path.exists(args.tests):
            with open(args.tests, "r", encoding="utf-8") as f:
                initial_tests = f.read()
        else:
            console.print(f"[yellow][!] Tests file '{args.tests}' not found. TestForge will synthesize tests autonomously.[/yellow]")

    if getattr(args, "privacy_mode", False):
        from testforge.privacy_mode import PrivacyModeManager
        PrivacyModeManager.get_instance().enable()
        console.print("[bold green][🔒 Privacy Mode Active][/bold green] Zero-egress air-gap enforced. Local models only.")

    # Launch multi-agent hardening pipeline
    orchestrator = TestForgeOrchestrator(
        target_source_code=source_code,
        initial_test_code=initial_tests,
        max_iterations=args.max_iter,
        target_mutation_score=args.target_score,
        model_name=args.model,
        target_file_path=target_path,
        engine_mode=args.engine_mode,
        privacy_mode=getattr(args, "privacy_mode", False)
    )

    final_state = orchestrator.run()

    out_file = args.output or "test_hardened.py"
    orchestrator.export_hardened_suite(output_path=out_file)

    console.print(f"\n[bold green][TestForge] Exported standalone hardened tests to: {out_file}[/bold green]")
    console.print(f"[dim]Run standalone verification anytime: pytest {out_file} -v[/dim]\n")


if __name__ == "__main__":
    main()
