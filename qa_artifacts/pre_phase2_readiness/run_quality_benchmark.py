#!/usr/bin/env python3
"""
TestForge Pre-Phase 2 Evaluation Readiness: Stage 6 Test Quality & Measurement Benchmark
Executes end-to-end AST test generation, test execution, and mutation evaluation
across 6 representative target modules in safe isolated sandboxes.
"""

import sys
import json
import time
from pathlib import Path

BASE_DIR = Path("/Users/sourabh/TestForge")
sys.path.insert(0, str(BASE_DIR))

from testforge.agents import TestGeneratorAgent
from testforge.mutator import ASTMutator
from testforge.sandbox import SubprocessSandbox

TARGET_MODULES = [
    {
        "name": "banking.py",
        "path": BASE_DIR / "samples" / "banking.py",
        "description": "Core bank account deposit/withdrawal business logic"
    },
    {
        "name": "discount.py",
        "path": BASE_DIR / "samples" / "discount.py",
        "description": "E-commerce tiered customer discount rules"
    },
    {
        "name": "currency_converter.py",
        "path": BASE_DIR / "samples" / "currency_converter.py",
        "description": "Cross-currency conversion with spread margins & fees"
    },
    {
        "name": "inventory_pricing.py",
        "path": BASE_DIR / "samples" / "inventory_pricing.py",
        "description": "Multi-tier inventory pricing with volume breaks"
    },
    {
        "name": "rate_limiter.py",
        "path": BASE_DIR / "samples" / "rate_limiter.py",
        "description": "Token bucket rate limiter with burst bounds"
    },
    {
        "name": "logistics_engine.py",
        "path": BASE_DIR / "qa_artifacts" / "complete_frontend_acceptance_audit" / "random_python_target" / "logistics_engine.py",
        "description": "Complex multi-class dispatch, routing & inventory system"
    }
]

def run_benchmark():
    print("=== STARTING STAGE 6: TEST QUALITY & MEASUREMENT BENCHMARK ===")
    agent = TestGeneratorAgent(api_key="")
    mutator = ASTMutator()
    sandbox = SubprocessSandbox()

    benchmark_results = []

    for item in TARGET_MODULES:
        target_path = item["path"]
        if not target_path.exists():
            print(f"[WARN] Target path {target_path} not found, skipping...")
            continue

        print(f"\n---> Benchmarking {item['name']}...")
        source_code = target_path.read_text(encoding="utf-8")
        loc = len([l for l in source_code.splitlines() if l.strip() and not l.strip().startswith("#")])
        total_lines = len(source_code.splitlines())

        t0 = time.perf_counter()

        # Step 1: Synthesize tests via deterministic fallback chain
        generated_test_code = agent.generate_tests(source_code)
        gen_duration_ms = (time.perf_counter() - t0) * 1000

        # Step 2: Validate generated tests in sandbox
        t_exec_start = time.perf_counter()
        exec_res = sandbox.run_single(generated_test_code, source_code)
        exec_duration_ms = (time.perf_counter() - t_exec_start) * 1000

        tests_collected = exec_res.get("tests_collected", 0)
        tests_passed = exec_res.get("tests_passed", 0)
        tests_failed = exec_res.get("tests_failed", 0)
        pass_rate = (tests_passed / tests_collected * 100.0) if tests_collected > 0 else 0.0

        # Step 3: Mutate source code
        t_mut_start = time.perf_counter()
        mutants = mutator.mutate(source_code)
        
        # Step 4: Evaluate mutants against generated test suite (sample up to 25 mutants for fast benchmark)
        sample_mutants = mutants[:25] if len(mutants) > 25 else mutants
        evaluated = sandbox.evaluate_mutants_parallel(
            generated_test_code,
            sample_mutants,
            baseline_passed=(exec_res.get("status") == "PASS")
        )
        mut_eval_duration_ms = (time.perf_counter() - t_mut_start) * 1000

        killed = sum(1 for m in evaluated if m.status == "KILLED")
        survived = sum(1 for m in evaluated if m.status == "SURVIVED")
        total_eval = len(evaluated)
        mutation_score = (killed / total_eval * 100.0) if total_eval > 0 else 0.0

        total_module_time_ms = (time.perf_counter() - t0) * 1000

        record = {
            "module_name": item["name"],
            "description": item["description"],
            "loc": loc,
            "total_lines": total_lines,
            "tests_collected": tests_collected,
            "tests_passed": tests_passed,
            "tests_failed": tests_failed,
            "pass_rate_pct": round(pass_rate, 2),
            "total_mutants_generated": len(mutants),
            "mutants_evaluated": total_eval,
            "mutants_killed": killed,
            "mutants_survived": survived,
            "mutation_score_pct": round(mutation_score, 2),
            "generation_time_ms": round(gen_duration_ms, 2),
            "execution_time_ms": round(exec_duration_ms, 2),
            "mutation_eval_time_ms": round(mut_eval_duration_ms, 2),
            "total_duration_ms": round(total_module_time_ms, 2)
        }
        benchmark_results.append(record)

        print(f"     LOC: {loc} (Total: {total_lines})")
        print(f"     Tests Generated: {tests_collected} | Passed: {tests_passed} ({round(pass_rate, 1)}%)")
        print(f"     Mutants Gen: {len(mutants)} | Eval: {total_eval} | Killed: {killed} (Score: {round(mutation_score, 1)}%)")
        print(f"     Latency: {round(total_module_time_ms, 1)}ms (Gen: {round(gen_duration_ms, 1)}ms, Exec: {round(exec_duration_ms, 1)}ms, Mut: {round(mut_eval_duration_ms, 1)}ms)")

    out_file = BASE_DIR / "qa_artifacts" / "pre_phase2_readiness" / "benchmark_quality_results.json"
    out_file.write_text(json.dumps(benchmark_results, indent=2), encoding="utf-8")
    print(f"\n[DONE] Benchmark complete for {len(benchmark_results)} modules! Saved to {out_file}")

if __name__ == "__main__":
    run_benchmark()

