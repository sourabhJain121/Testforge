"""
orchestrator.py - Multi-Agent State Graph Orchestration & Reflection Loop.

Author: Sourabh (Module 1 & 3)
Course: CSE3101 - Agentic AI

Agent State Graph:
  1. Sandbox baseline validation (pass@1 check on clean code)
  2. TestGeneratorAgent: synthesizes initial candidate assertions via live Gemini API
  3. Sandbox candidate validation on clean target code
  4. AST Mutator: injects deterministic faults (comparison, arith, cond, return)
  5. Parallel Sandbox Runner: evaluates mutants across CPU cores concurrently
  6. Termination check: Mutation Score >= target_score or iteration >= max_iterations
  7. AdversarialCriticAgent: reasons why mutants survived and produces reflection directives
  8. Loop back to TestGeneratorAgent with surviving unified diffs and critic directives
"""

from __future__ import annotations
import os
import re
import time
from typing import Optional, List
from rich.console import Console
from rich.table import Table

from testforge.state import TestForgeState, IterationMetrics
from testforge.accel import hw_profile
from testforge.mutator import ASTMutator
from testforge.sandbox import ParallelSandboxRunner
from testforge.logger import TraceLogger
from testforge.agents import TestGeneratorAgent, AdversarialCriticAgent

console = Console()


def format_standalone_test_suite(test_code: str, target_file_path: Optional[str] = None) -> str:
    """
    Transforms internal sandbox test code (`from target import *`, `import target`)
    into a production-ready, standalone executable Pytest file.
    Inserts a dynamic path hook and resolves the target module's import.
    """
    code = test_code.strip()

    # Determine module name if target path provided
    module_import_name = "target"
    if target_file_path:
        norm = os.path.normpath(target_file_path)
        if norm.endswith(".py"):
            norm = norm[:-3]
        module_import_name = norm.replace(os.sep, ".").replace("/", ".").lstrip(".")

    # Replace `from target import ...` with module import
    if module_import_name != "target":
        code = re.sub(r"from\s+target\s+import\s+", f"from {module_import_name} import ", code)
        code = re.sub(r"import\s+target\s+", f"import {module_import_name} as target ", code)

    # Dynamic sys.path hook to ensure pytest runs from root or any directory
    path_hook = (
        "import os\n"
        "import sys\n"
        "sys.path.insert(0, os.path.abspath('.'))\n"
        "sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))\n"
    )

    if "sys.path.insert" not in code:
        code = path_hook + "\n" + code

    return code


class TestForgeOrchestrator:
    """
    Coordinates the live multi-agent reflection loop across iterations until termination.
    """
    def __init__(
        self,
        target_source_code: str,
        initial_test_code: Optional[str] = None,
        max_iterations: int = 3,
        target_mutation_score: float = 85.0,
        model_name: str = "gemini-3.6-flash",
        trace_log_path: str = "testforge_trace.jsonl",
        api_key: Optional[str] = None,
        target_file_path: Optional[str] = None
    ):
        self.target_file_path = target_file_path
        self.state = TestForgeState(
            target_source_code=target_source_code.strip(),
            current_test_code=(initial_test_code or "").strip(),
            max_iterations=max_iterations,
            target_mutation_score=target_mutation_score,
            hardware_info=hw_profile.summary()
        )
        self.logger = TraceLogger(log_path=trace_log_path)
        self.sandbox = ParallelSandboxRunner(timeout_seconds=5)
        self.generator = TestGeneratorAgent(
            model_name=model_name,
            logger=self.logger,
            api_key=api_key
        )
        self.critic = AdversarialCriticAgent(
            model_name=model_name,
            logger=self.logger,
            api_key=api_key
        )

    def export_hardened_suite(self, output_path: str = "test_hardened.py") -> str:
        """
        Exports the final test suite formatted for standalone pytest execution.
        """
        formatted = format_standalone_test_suite(
            self.state.current_test_code,
            self.target_file_path
        )
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(formatted)
        return formatted

    def run(self) -> TestForgeState:
        console.print("[bold cyan]==========================================================[/bold cyan]")
        console.print("[bold cyan]       TESTFORGE: AUTONOMOUS TEST HARDENING ENGINE        [/bold cyan]")
        console.print(f"[dim]Hardware: Apple Silicon M-Series | Cores: {hw_profile.cpu_count} | Workers: {hw_profile.recommended_workers}[/dim]")
        console.print(f"[bold green]Foundation Model: Google GenAI Live ({self.generator.model_name})[/bold green]")
        console.print("[bold cyan]==========================================================[/bold cyan]\n")

        self.logger.log_event("PIPELINE_START", {
            "max_iterations": self.state.max_iterations,
            "target_score": self.state.target_mutation_score,
            "hardware": self.state.hardware_info,
            "model_name": self.generator.model_name,
            "target_file": self.target_file_path
        })

        # Step 1: Synthesize initial candidate tests if none provided
        if not self.state.current_test_code:
            console.print("[yellow][Step 1/6] TestGeneratorAgent synthesizing initial candidate test suite...[/yellow]")
            initial_tests = self.generator.generate_tests(
                source_code=self.state.target_source_code,
                iteration=0
            )
            self.state.current_test_code = initial_tests
            self.state.active_provider = self.generator.active_provider

        # Step 2: Validate baseline tests on clean target code (pass@1 check)
        console.print("[yellow][Step 2/6] Sandbox validating test suite against clean target (pass@1 check)...[/yellow]")
        baseline_exec = self.sandbox.run_single(self.state.current_test_code, self.state.target_source_code)
        
        if baseline_exec["status"] != "PASS":
            console.print(f"[red][!] Initial generated tests failed against clean code:[/red]\n{baseline_exec['stderr']}")
            self.logger.log_event("BASELINE_FAILURE", baseline_exec)
            # Re-attempt single self-repair
            console.print("[yellow][Self-Repair] Re-prompting TestGeneratorAgent to fix syntax/runtime error...[/yellow]")
            repair_prompt = f"The following tests failed against clean code:\n{baseline_exec['stderr']}\nPlease produce corrected, working Pytest tests."
            self.state.current_test_code = self.generator.generate_tests(
                source_code=self.state.target_source_code,
                critic_feedback=repair_prompt,
                iteration=0
            )
        else:
            console.print("[green][✓] Candidate test suite passed on clean code.[/green]")

        # Step 3: Measure Baseline Line Coverage
        cov_pct, _ = self.sandbox.measure_coverage(self.state.current_test_code, self.state.target_source_code)
        self.state.baseline_line_coverage = cov_pct
        console.print(f"[green][✓] Baseline Line Coverage: {cov_pct:.1f}%[/green]\n")

        # Step 4: Iterative Reflection & Hardening Loop
        critic_directive: Optional[str] = None

        for iteration in range(1, self.state.max_iterations + 1):
            iter_start = time.perf_counter()
            self.state.current_iteration = iteration
            console.print(f"[bold magenta]▶ Iteration {iteration} of {self.state.max_iterations} (Target Score: {self.state.target_mutation_score}%)[/bold magenta]")

            # A. If we have reflection feedback from previous iteration, regenerate/harden tests first
            if critic_directive and self.state.surviving_mutant_diffs:
                console.print(f"  [cyan]• TestGeneratorAgent hardening assertions based on Critic reasoning...[/cyan]")
                hardened_tests = self.generator.generate_tests(
                    source_code=self.state.target_source_code,
                    surviving_diffs=self.state.surviving_mutant_diffs,
                    critic_feedback=critic_directive,
                    iteration=iteration
                )
                # Verify hardened tests still pass on clean target
                clean_check = self.sandbox.run_single(hardened_tests, self.state.target_source_code)
                if clean_check["status"] == "PASS":
                    self.state.current_test_code = hardened_tests
                    self.state.active_provider = self.generator.active_provider
                    console.print("  [green]• Hardened tests verified against clean code.[/green]")
                else:
                    console.print("  [yellow]• Hardened assertions broke clean code. Retaining previous working test suite.[/yellow]")

            # B. Invert AST to generate deterministic mutants
            mutants = ASTMutator.generate_mutants(self.state.target_source_code)
            self.state.mutants = mutants
            console.print(f"  [cyan]• AST Mutator injected {len(mutants)} deterministic faults.[/cyan]")

            # C. Evaluate mutants across parallel sandbox workers
            console.print(f"  [cyan]• Parallel Sandbox evaluating mutants across {self.sandbox.max_workers} CPU workers...[/cyan]")
            evaluated_mutants = self.sandbox.evaluate_mutants_parallel(
                self.state.current_test_code,
                mutants
            )

            # D. Compute score & surviving diffs
            killed = sum(1 for m in evaluated_mutants if m.status in ("KILLED", "TIMEOUT"))
            survived = sum(1 for m in evaluated_mutants if m.status == "SURVIVED")
            timeouts = sum(1 for m in evaluated_mutants if m.status == "TIMEOUT")
            total = len(evaluated_mutants)
            score = (killed / total * 100.0) if total > 0 else 0.0

            surviving_diffs = [
                f"Mutant [{m.mutant_id}] at Line {m.line_number} ({m.mutation_type}):\n{m.unified_diff}"
                for m in evaluated_mutants if m.status == "SURVIVED"
            ]
            self.state.surviving_mutant_diffs = surviving_diffs

            iter_duration = time.perf_counter() - iter_start
            metric = IterationMetrics(
                iteration=iteration,
                total_mutants=total,
                killed_mutants=killed,
                survived_mutants=survived,
                timed_out_mutants=timeouts,
                mutation_score=round(score, 2),
                line_coverage_pct=round(cov_pct, 2),
                duration_seconds=round(iter_duration, 2)
            )
            self.state.history.append(metric)
            self.logger.log_event("ITERATION_EVALUATION", metric.model_dump())

            # Display table
            table = Table(title=f"Iteration {iteration} Benchmark", show_header=True)
            table.add_column("Total Mutants", justify="center")
            table.add_column("Killed", justify="center", style="green")
            table.add_column("Survived", justify="center", style="red")
            table.add_column("Timeouts", justify="center", style="yellow")
            table.add_column("Mutation Score", justify="center", style="bold")
            table.add_column("Elapsed", justify="center")
            table.add_row(
                str(total),
                str(killed),
                str(survived),
                str(timeouts),
                f"{score:.1f}%",
                f"{iter_duration:.2f}s"
            )
            console.print(table)

            # E. Check Termination
            if score >= self.state.target_mutation_score:
                self.state.terminated = True
                self.state.termination_reason = f"Target mutation score achieved ({score:.1f}% >= {self.state.target_mutation_score}%)."
                console.print(f"[bold green]✔ SUCCESS: {self.state.termination_reason}[/bold green]\n")
                break

            if iteration == self.state.max_iterations:
                self.state.terminated = True
                self.state.termination_reason = "Maximum allowed reflection iterations reached."
                console.print(f"[yellow]⚠ TERMINATED: {self.state.termination_reason}[/yellow]\n")
                break

            # F. AdversarialCriticAgent analyzes surviving mutants
            console.print(f"  [magenta]• AdversarialCriticAgent analyzing {survived} surviving mutant(s) with Gemini...[/magenta]")
            critic_directive = self.critic.analyze_surviving_mutants(
                target_code=self.state.target_source_code,
                surviving_mutant_diffs=surviving_diffs,
                iteration=iteration
            )
            console.print(f"  [dim]Critic Directive: {critic_directive[:140]}...[/dim]\n")

        self.logger.log_event("PIPELINE_COMPLETE", {
            "terminated": self.state.terminated,
            "reason": self.state.termination_reason,
            "final_score": self.state.history[-1].mutation_score if self.state.history else 0.0,
            "total_tokens_used": self.logger.get_total_tokens()
        })

        return self.state
