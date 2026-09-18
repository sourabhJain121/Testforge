"""
orchestrator.py - Multi-Agent State Graph Orchestration & Reflection Loop.

Author: Sourabh (Module 1 & 3)
Course: CSE3101 - Agentic AI

Agent State Graph:
  Coverage Profiler -> Test Generator -> Sandbox Baseline -> Parallel AST Mutator 
  -> Parallel Sandbox Mutants -> Apple Silicon GPU Triage -> Adversarial Critic (LLM Reasoning)
  -> Hardened Test Generator -> Reflection Decision
"""

from __future__ import annotations
import time
from typing import Optional
from rich.console import Console
from rich.table import Table

from testforge.state import TestForgeState, IterationMetrics
from testforge.accel import hw_profile
from testforge.mutator import ASTMutator
from testforge.sandbox import ParallelSandboxRunner
from testforge.logger import TraceLogger
from testforge.agents import LLMClient, AdversarialCriticAgent, TestGeneratorAgent
from testforge.classifier import MutantTriageModel

console = Console()


class TestForgeOrchestrator:
    """
    Coordinates the multi-agent reflection loop across iterations until termination.
    """
    def __init__(
        self,
        target_source_code: str,
        initial_test_code: Optional[str] = None,
        max_iterations: int = 3,
        target_mutation_score: float = 85.0,
        model_name: str = "gemini-2.5-flash",
        trace_log_path: str = "testforge_trace.jsonl"
    ):
        self.state = TestForgeState(
            target_source_code=target_source_code.strip(),
            current_test_code=(initial_test_code or "").strip(),
            max_iterations=max_iterations,
            target_mutation_score=target_mutation_score,
            hardware_info=hw_profile.summary()
        )
        self.logger = TraceLogger(log_path=trace_log_path)
        self.sandbox = ParallelSandboxRunner(timeout_seconds=5)
        self.llm = LLMClient(model_name=model_name, logger=self.logger)
        self.critic = AdversarialCriticAgent(self.llm, logger=self.logger)
        self.generator = TestGeneratorAgent(self.llm, self.critic, logger=self.logger)
        self.triage_model = MutantTriageModel()

    def run(self) -> TestForgeState:
        console.print("[bold cyan]==========================================================[/bold cyan]")
        console.print("[bold cyan]       TESTFORGE: AUTONOMOUS TEST HARDENING ENGINE        [/bold cyan]")
        console.print(f"[dim]Hardware: Apple Silicon M-Series | Cores: {hw_profile.cpu_count} | Workers: {hw_profile.recommended_workers}[/dim]")
        if self.llm.is_live:
            console.print(f"[bold green]Foundation Model Backend: Google GenAI Live ({self.llm.model_name})[/bold green]")
        else:
            console.print("[bold yellow]Foundation Model Backend: Deterministic Simulation (Set GEMINI_API_KEY for live GenAI)[/bold yellow]")
        console.print("[bold cyan]==========================================================[/bold cyan]\n")

        self.logger.log_event("PIPELINE_START", {
            "max_iterations": self.state.max_iterations,
            "target_score": self.state.target_mutation_score,
            "hardware": self.state.hardware_info,
            "is_live_llm": self.llm.is_live,
            "model_name": self.llm.model_name
        })

        # Step 1: Initial Test Generation (if no initial test suite supplied)
        if not self.state.current_test_code:
            console.print("[yellow][Step 1/6] Test Generator Agent synthesizing baseline unit tests...[/yellow]")
            self.state.current_test_code = self.generator.generate_initial_suite(self.state.target_source_code)
            self.logger.log_event("TESTS_GENERATED", {"code": self.state.current_test_code})

        # Step 2: Sandbox Verification of Baseline Tests
        console.print("[yellow][Step 2/6] Sandbox validating baseline test suite against clean code...[/yellow]")
        baseline_exec = self.sandbox.run_single(self.state.current_test_code, self.state.target_source_code)
        
        if baseline_exec["status"] != "PASS":
            console.print(f"[red][!] Baseline test suite failed against clean code:[/red]\n{baseline_exec['stderr']}")
            self.logger.log_event("BASELINE_FAILURE", baseline_exec)
        else:
            console.print("[green][✓] Baseline tests pass cleanly.[/green]")

        # Step 3: Measure Baseline Line Coverage
        cov_pct, _ = self.sandbox.measure_coverage(self.state.current_test_code, self.state.target_source_code)
        self.state.baseline_line_coverage = cov_pct
        console.print(f"[green][✓] Initial Line Coverage: {cov_pct:.1f}%[/green]\n")

        # Step 4: Iterative Reflection & Hardening Loop
        for iteration in range(1, self.state.max_iterations + 1):
            iter_start = time.perf_counter()
            self.state.current_iteration = iteration
            console.print(f"[bold magenta]▶ Iteration {iteration} of {self.state.max_iterations} (Target Score: {self.state.target_mutation_score}%)[/bold magenta]")

            # A. AST Fault Injection
            mutants = ASTMutator.generate_mutants(self.state.target_source_code)
            self.state.mutants = mutants
            console.print(f"  [cyan]• AST Mutator injected {len(mutants)} deterministic faults.[/cyan]")

            # B. Parallel Sandbox Execution against all Mutants
            console.print(f"  [cyan]• Parallel Sandbox evaluating mutants across {self.sandbox.max_workers} CPU workers...[/cyan]")
            evaluated_mutants = self.sandbox.evaluate_mutants_parallel(
                self.state.current_test_code,
                mutants
            )

            # C. Aggregate Metrics
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

            # Print Summary Table
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

            # D. Evaluate Termination
            if score >= self.state.target_mutation_score:
                self.state.terminated = True
                self.state.termination_reason = f"Target mutation score reached ({score:.1f}% >= {self.state.target_mutation_score}%)."
                console.print(f"[bold green]✔ SUCCESS: {self.state.termination_reason}[/bold green]\n")
                break

            if iteration == self.state.max_iterations:
                self.state.terminated = True
                self.state.termination_reason = "Maximum allowed iterations reached."
                console.print(f"[yellow]⚠ TERMINATED: {self.state.termination_reason}[/yellow]\n")
                break

            # E. Apple Silicon MLX GPU Model: Predict Mutant Triage & Hardness
            difficulty_tags = self.triage_model.predict_difficulty(
                [m for m in evaluated_mutants if m.status == "SURVIVED"]
            )
            console.print(f"  [cyan]• Apple Silicon GPU (MLX) triaged {len(difficulty_tags)} surviving mutants on Metal shaders.[/cyan]")
            self.logger.log_event("MLX_GPU_TRIAGE", {"tags": difficulty_tags})

            # F. Adversarial Critic Agent: Real LLM Reasoning over AST Diffs
            console.print(f"  [magenta]• Adversarial Critic analyzing {survived} surviving mutant(s)...[/magenta]")
            critic_directive = self.critic.analyze_surviving_mutants(
                self.state.target_source_code,
                surviving_diffs
            )
            self.logger.log_event("CRITIC_REFLECTION", {
                "survived_count": survived,
                "directive": critic_directive[:200] + "..."
            })

            # G. Test Generator Agent: Synthesizes Hardened Pytest Assertions
            console.print("  [magenta]• Test Generator Agent synthesizing hardened assertions...[/magenta]")
            hardened_test_suite = self.generator.harden_suite(
                self.state.target_source_code,
                self.state.current_test_code,
                surviving_diffs,
                critic_directive
            )

            # H. Sandbox Guardrail: Verify hardened tests pass cleanly against baseline
            clean_check = self.sandbox.run_single(hardened_test_suite, self.state.target_source_code)
            if clean_check["status"] == "PASS":
                self.state.current_test_code = hardened_test_suite
                console.print("  [green]• Hardened test assertions verified against clean target.[/green]\n")
            else:
                console.print("  [red]• Hardened assertions failed against clean target. Retaining previous suite.[/red]\n")

        self.logger.log_event("PIPELINE_COMPLETE", {
            "terminated": self.state.terminated,
            "reason": self.state.termination_reason,
            "final_score": self.state.history[-1].mutation_score if self.state.history else 0.0
        })

        return self.state
