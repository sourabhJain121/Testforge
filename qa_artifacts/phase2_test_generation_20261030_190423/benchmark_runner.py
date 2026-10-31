"""
Benchmark Runner for Phase 2: Intelligent Multi-Callable Test Generation & Refinement.
Collects all empirical data and provenance records for discount.py and uploaded_logistics_engine.py.
"""
import hashlib
import json
import os
import sys
import time
from pathlib import Path

# Add project root to path
ROOT = Path("/Users/sourabh/TestForge")
sys.path.insert(0, str(ROOT))

from testforge.intelligent_generator import (
    IntelligentASTSynthesizer,
    ASTCallableAnalyzer,
    ReferenceExecutor
)
from testforge.orchestrator import TestForgeOrchestrator
from testforge.mutator import ASTMutator
from testforge.sandbox import ParallelSandboxRunner
from testforge.equivalence import calculate_mutation_scores

OUTPUT_DIR = Path("/Users/sourabh/TestForge/qa_artifacts/phase2_test_generation_20261030_190423")

def run_target_benchmark(target_name: str, target_rel_path: str):
    target_path = ROOT / target_rel_path
    with open(target_path, "r", encoding="utf-8") as f:
        source_code = f.read()

    print(f"\n{'='*70}\n[BENCHMARK] Running target: {target_name} ({target_rel_path})\n{'='*70}")
    
    synthesizer = IntelligentASTSynthesizer()
    disc = synthesizer.discover_callables(source_code)
    
    all_callables = disc.module_functions + [m for cl in disc.classes for m in cl.methods]
    print(f"Discovered Callables: {len(all_callables)}")
    for c in all_callables:
        print(f"  - [{c.scope}] {c.parent_class + '.' if c.parent_class else ''}{c.name} ({c.method_type or 'function'}) eligible={c.is_eligible}")
    print(f"Classes Discovered: {len(disc.classes)}")
    for cl in disc.classes:
        print(f"  - Class {cl.name} (methods: {len(cl.methods)})")

    # Step 1: Initial Intelligent Synthesis
    t0 = time.perf_counter()
    initial_res = synthesizer.synthesize_test_suite(source_code)
    t_synth = time.perf_counter() - t0

    candidate_code = initial_res.test_code
    cand_sha256 = hashlib.sha256(candidate_code.encode("utf-8")).hexdigest()

    # Step 2: Clean Sandbox Validation (pass@1 check)
    sandbox = ParallelSandboxRunner(timeout_seconds=10)
    sand_res = sandbox.run_single(candidate_code, source_code)
    val_status = sand_res["status"]
    passed_tests = sand_res["tests_passed"]
    failed_tests = sand_res["tests_failed"]
    total_tests = sand_res["tests_collected"]
    val_sha256 = hashlib.sha256(candidate_code.encode("utf-8")).hexdigest()

    print(f"\n[Validation] Clean Pass@1: {val_status} ({passed_tests}/{total_tests} passed, {failed_tests} failed)")
    assert val_status == "PASS" and failed_tests == 0, f"Candidate suite failed on clean target: {sand_res.get('error_trace')}"

    # Step 3: Initial Mutation Testing Run
    mutants = ASTMutator.mutate(source_code)
    print(f"\n[Mutants Generated] {len(mutants)} AST mutants")
    
    eval_mutants_r1 = sandbox.evaluate_mutants_parallel(
        candidate_code,
        mutants,
        baseline_passed=passed_tests
    )
    score_data_r1 = calculate_mutation_scores(eval_mutants_r1)

    r1_generated = score_data_r1["total_mutants"]
    r1_killed = score_data_r1["killed_mutants"]
    r1_survived = score_data_r1["survived_mutants"]
    r1_timeout = score_data_r1["timed_out_mutants"]
    r1_score = score_data_r1["raw_mutation_score"]

    print(f"\n[Mutation Round 1] Generated: {r1_generated}, Killed: {r1_killed}, Survived: {r1_survived}, Score: {r1_score:.2f}%")

    # Step 4: Mutation-Guided Refinement
    surviving_mutants = [m for m in eval_mutants_r1 if m.status == "SURVIVED"]
    surviving_diffs = [
        f"Mutant [{m.mutant_id}] at Line {m.line_number} ({m.mutation_type}):\n{m.unified_diff}"
        for m in surviving_mutants if m.unified_diff
    ]
    surviving_mut_dicts = [
        {
            "id": m.mutant_id,
            "operator": m.mutation_type,
            "line_number": m.line_number,
            "diff": m.unified_diff
        }
        for m in surviving_mutants
    ]
    
    refinement_res = synthesizer.synthesize_test_suite(
        source_code,
        surviving_mutants=surviving_mut_dicts,
        surviving_diffs=surviving_diffs
    )
    refined_code = refinement_res.test_code
    ref_cand_sha256 = hashlib.sha256(refined_code.encode("utf-8")).hexdigest()

    # Validate Refined Suite
    sand_ref_res = sandbox.run_single(refined_code, source_code)
    ref_val_status = sand_ref_res["status"]
    ref_passed = sand_ref_res["tests_passed"]
    ref_failed = sand_ref_res["tests_failed"]
    ref_val_sha256 = hashlib.sha256(refined_code.encode("utf-8")).hexdigest()

    print(f"\n[Refinement Validation] Clean Pass@1: {ref_val_status} ({ref_passed}/{sand_ref_res['tests_collected']} passed)")
    assert ref_val_status == "PASS" and ref_failed == 0

    # Step 5: Mutation Testing on Refined Suite
    eval_mutants_r2 = sandbox.evaluate_mutants_parallel(
        refined_code,
        mutants,
        baseline_passed=ref_passed
    )
    score_data_r2 = calculate_mutation_scores(eval_mutants_r2)

    r2_generated = score_data_r2["total_mutants"]
    r2_killed = score_data_r2["killed_mutants"]
    r2_survived = score_data_r2["survived_mutants"]
    r2_timeout = score_data_r2["timed_out_mutants"]
    r2_score = score_data_r2["raw_mutation_score"]

    print(f"\n[Mutation Round 2 (Refined)] Generated: {r2_generated}, Killed: {r2_killed}, Survived: {r2_survived}, Score: {r2_score:.2f}%")

    # Step 6: Full Orchestrator End-to-End Hardening Pipeline
    trace_path = OUTPUT_DIR / f"orchestrator_trace_{target_name}.jsonl"
    orch = TestForgeOrchestrator(
        target_source_code=source_code,
        max_iterations=2,
        target_mutation_score=85.0,
        trace_log_path=str(trace_path),
        target_file_path=str(target_path),
        engine_mode="local"
    )
    orch_state = orch.run()
    
    # Save test suites
    (OUTPUT_DIR / f"generated_tests_{target_name}_round1.py").write_text(candidate_code, encoding="utf-8")
    (OUTPUT_DIR / f"generated_tests_{target_name}_refined.py").write_text(refined_code, encoding="utf-8")
    (OUTPUT_DIR / f"generated_tests_{target_name}_final_orch.py").write_text(orch_state.current_test_code or "", encoding="utf-8")

    bench_data = {
        "target_name": target_name,
        "target_path": str(target_path),
        "lines_of_code": len(source_code.splitlines()),
        "discovered_callables": [
            {
                "name": c.name,
                "scope": c.scope,
                "parent_class": c.parent_class,
                "method_type": c.method_type,
                "eligible": c.is_eligible,
                "reason": c.ineligibility_reason
            }
            for c in all_callables
        ],
        "classes": [
            {
                "name": cl.name,
                "methods": [m.name for m in cl.methods],
                "init_params": cl.init_method.pos_args if cl.init_method else []
            }
            for cl in disc.classes
        ],
        "synthesis_metrics_r1": {
            "total_tests": initial_res.total_test_count,
            "meaningful_assertions": initial_res.meaningful_assertions_count,
            "invariant_assertions": initial_res.invariant_assertions_count,
            "boundary_tests": initial_res.boundary_tests_count,
            "negative_tests": initial_res.negative_tests_count,
            "covered_callables": initial_res.covered_callables,
            "skipped_callables": initial_res.skipped_callables
        },
        "synthesis_metrics_r2": {
            "total_tests": refinement_res.total_test_count,
            "meaningful_assertions": refinement_res.meaningful_assertions_count,
            "invariant_assertions": refinement_res.invariant_assertions_count,
            "boundary_tests": refinement_res.boundary_tests_count,
            "negative_tests": refinement_res.negative_tests_count,
            "covered_callables": refinement_res.covered_callables,
            "skipped_callables": refinement_res.skipped_callables,
            "mutants_targeted": refinement_res.mutants_targeted
        },
        "mutation_round1": {
            "generated": r1_generated,
            "killed": r1_killed,
            "survived": r1_survived,
            "timeout": r1_timeout,
            "score": r1_score
        },
        "mutation_round2": {
            "generated": r2_generated,
            "killed": r2_killed,
            "survived": r2_survived,
            "timeout": r2_timeout,
            "score": r2_score
        },
        "orchestrator_final": {
            "iterations_executed": orch_state.current_iteration,
            "mutants_generated": orch_state.mutants_generated,
            "mutants_killed": orch_state.mutants_killed,
            "mutants_survived": orch_state.mutants_survived,
            "final_mutation_score": orch_state.final_mutation_score,
            "tests_passed": orch_state.baseline_tests_passed,
            "total_tests": orch_state.baseline_tests_generated
        },
        "provenance": {
            "candidate_sha256": cand_sha256,
            "validated_sha256": val_sha256,
            "matches_candidate": cand_sha256 == val_sha256,
            "refined_candidate_sha256": ref_cand_sha256,
            "refined_validated_sha256": ref_val_sha256,
            "matches_refined": ref_cand_sha256 == ref_val_sha256,
        },
        "surviving_mutants_r2_summary": [
            {
                "id": m.mutant_id,
                "operator": m.mutation_type,
                "line": m.line_number,
                "diff": m.unified_diff
            }
            for m in eval_mutants_r2 if m.status == "SURVIVED"
        ]
    }

    with open(OUTPUT_DIR / f"benchmark_{target_name}.json", "w", encoding="utf-8") as f:
        json.dump(bench_data, f, indent=2)

    print(f"\n[BENCHMARK COMPLETE] Saved summary to {OUTPUT_DIR / f'benchmark_{target_name}.json'}")
    return bench_data

if __name__ == "__main__":
    b1 = run_target_benchmark("discount", "samples/discount.py")
    b2 = run_target_benchmark("logistics", "samples/uploaded_logistics_engine.py")
    print("\nALL BENCHMARKS COMPLETED SUCCESSFULLY!")
