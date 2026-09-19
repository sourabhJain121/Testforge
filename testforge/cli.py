"""
cli.py - Enhanced Multi-Mode CLI with Dynamic Ingestion & Autonomous Code Synthesis.

Authors: Sourabh & Shreshth
Course: CSE3101 - Agentic AI
"""

import os
import sys
import argparse
from rich.console import Console
from rich.prompt import Prompt

from testforge.orchestrator import TestForgeOrchestrator
from testforge.ingestion import TargetManagerAgent

console = Console()


def interactive_menu() -> tuple[str, Optional[str]]:
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


def main():
    parser = argparse.ArgumentParser(description="TestForge: Autonomous Test Hardening System")
    parser.add_argument("--target", "-t", default=None, help="Path to arbitrary Python target source file")
    parser.add_argument("--create", "-c", default=None, help="Synthesize a new Python module from a natural language prompt")
    parser.add_argument("--tests", "-s", default=None, help="Path to initial test file (optional)")
    parser.add_argument("--max-iter", "-i", type=int, default=3, help="Maximum reflection iterations")
    parser.add_argument("--target-score", "-score", type=float, default=85.0, help="Target mutation score (pct)")
    parser.add_argument("--model", "-m", default="gemini-3.6-flash", help="LLM foundation model name")
    parser.add_argument("--output", "-o", default="test_hardened.py", help="Output file for hardened tests")
    args = parser.parse_args()

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
        analysis = supervisor.ingest_file(target_path)
        if analysis.has_syntax_error:
            console.print(f"[bold red][!] Ingested file has syntax errors: {analysis.error_msg}[/bold red]")
            sys.exit(1)
        console.print(f"[green][✓] Target Validated. Module: [bold]{analysis.module_name}[/bold][/green]")
        console.print(f"    Functions found: {analysis.functions or 'None'}")
        console.print(f"    Classes found: {analysis.classes or 'None'}\n")
        source_code = analysis.source_code

    initial_tests = None
    if args.tests:
        with open(args.tests, "r", encoding="utf-8") as f:
            initial_tests = f.read()

    # Launch multi-agent hardening pipeline
    orchestrator = TestForgeOrchestrator(
        target_source_code=source_code,
        initial_test_code=initial_tests,
        max_iterations=args.max_iter,
        target_mutation_score=args.target_score,
        model_name=args.model,
        target_file_path=target_path
    )

    final_state = orchestrator.run()

    # Standalone export with dynamic import path resolution
    orchestrator.export_hardened_suite(output_path=args.output)

    console.print(f"\n[bold green][TestForge] Exported standalone hardened tests to: {args.output}[/bold green]")
    console.print(f"[dim]Run standalone verification anytime: pytest {args.output} -v[/dim]\n")


if __name__ == "__main__":
    main()
