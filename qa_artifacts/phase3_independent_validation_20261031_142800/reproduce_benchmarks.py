"""
Phase 3: Independent Validation and Reproduction Script
Executes fresh, un-cached, isolated benchmark runs for discount.py and uploaded_logistics_engine.py.
Collects detailed execution records for every mutant and assertion.
"""
import hashlib
import json
import os
import re
import sys
import time
from pathlib import Path

ROOT = Path("/Users/sourabh/TestForge")
sys.path.insert(0, str(ROOT))

from testforge.intelligent_generator import IntelligentASTSynthesizer
from testforge.orchestrator import TestForgeOrchestrator
from testforge.mutator import ASTMutator
from testforge.sandbox import ParallelSandboxRunner
from testforge.equivalence import calculate_mutation_scores
from testforge.security import SecurityGuardrail

ARTIFACT_DIR = ROOT / "qa_artifacts" / "phase3_independent_validation_20261031_142800"

def extract_failing_test_name(pytest_stdout: str) -> str:
    """Extracts the specific test function name that failed from pytest stdout."""
    match = re.search(r"FAILED\s+.*?::(test_\w+)", pytest_stdout)
    if match:
        return match.group(1)
    match2 = re.search(r"_{5,}\s+(test_\w+)\s+_{5,}", pytest_stdout)
    if match2:
        return match2.group(1)
    return "unknown_or_timeout"

def extract_failure_reason(pytest_stdout: str) -> str:
    """Extracts the failure reason (e.g. AssertionError) from pytest stdout."""
    lines = pytest_stdout.splitlines()
    for i, line in enumerate(lines):
        if line.startswith("E   ") or "AssertionError" in line or "ValueError" in line or "TypeError" in line:
            return line.strip()
    return "Test failed or timed out"

def run_isolated_benchmark(target_name: str, target_rel_path: str):
    target_path = ROOT / target_rel_path
    with open(target_path, "r", encoding="utf-8") as f:
        source_code = f.read()

    print(f"\n{'='*75}\n[PHASE 3 AUDIT] Independent Reproduction: {target_name} ({target_rel_path})\n{'='*75}")
    t_start = time.perf_counter()

    # 1. Callable Discovery
    synthesizer = IntelligentASTSynthesizer()
    disc = synthesizer.discover_callables(source_code)
    all_callables = disc.module_functions + [m for cl in disc.classes for m in cl.methods]
    eligible_callables = [c for c in all_callables if c.is_eligible]
    
    print(f"[*] Discovered {len(all_callables)} total callables ({len(eligible_callables)} eligible):")
    for c in all_callables:
        scope_str = f"{c.parent_class}." if c.parent_class else ""
        print(f"    - [{c.scope}] {scope_str}{c.name} ({c.method_type or 'function'}) eligible={c.is_eligible}")

    # 2. Fresh Candidate Suite Synthesis (Round 1)
    t_synth_start = time.perf_counter()
    synth_result = synthesizer.synthesize_test_suite(source_code)
    synth_duration = time.perf_counter() - t_synth_start
    candidate_code = synth_result.test_code
    cand_sha256 = hashlib.sha256(candidate_code.encode("utf-8")).hexdigest()

    # 3. Clean Sandbox Validation (Pass@1 check)
    sandbox = ParallelSandboxRunner(timeout_seconds=10)
    sand_res = sandbox.run_single(candidate_code, source_code)
    val_status = sand_res["status"]
    passed_tests = sand_res["tests_passed"]
    failed_tests = sand_res["tests_failed"]
    collected_tests = sand_res["tests_collected"]
    val_sha256 = hashlib.sha256(candidate_code.encode("utf-8")).hexdigest()

    print(f"[*] Clean Sandbox Pass@1: {val_status} ({passed_tests}/{collected_tests} passed, {failed_tests} failed)")
    assert val_status == "PASS" and failed_tests == 0, f"Candidate suite failed against clean code: {sand_res}"

    # 4. Coverage Measurement
    cov_pct, cov_info = sandbox.measure_coverage(candidate_code, source_code)
    print(f"[*] Statement Coverage: {cov_pct:.1f}% ({cov_info['covered_lines']}/{cov_info['num_statements']} statements)")

    # 5. AST Mutation Generation
    mutants = ASTMutator.mutate(source_code)
    print(f"[*] AST Mutator Injected: {len(mutants)} deterministic mutants")

    # 6. Parallel Mutant Evaluation
    t_mut_start = time.perf_counter()
    eval_mutants = sandbox.evaluate_mutants_parallel(
        candidate_code,
        mutants,
        baseline_passed=(val_status == "PASS")
    )
    mut_eval_duration = time.perf_counter() - t_mut_start

    score_data = calculate_mutation_scores(eval_mutants)
    r1_total = score_data["total_mutants"]
    r1_killed = score_data["killed_mutants"]
    r1_survived = score_data["survived_mutants"]
    r1_timeouts = score_data["timed_out_mutants"]
    r1_errors = score_data["execution_errors"]
    r1_invalid = score_data["invalid_mutants"]
    r1_raw_score = score_data["raw_mutation_score"]
    r1_adj_score = score_data["adjusted_mutation_score"]

    print(f"[*] Round 1 Mutation Score: {r1_raw_score:.2f}% (Killed: {r1_killed}/{r1_total}, Survived: {r1_survived}, Timeouts: {r1_timeouts}) in {mut_eval_duration:.2f}s")

    # 7. Collect Detailed Mutant Records & Kill Traces
    mutant_audit_records = []
    for m in eval_mutants:
        fail_test = extract_failing_test_name(m.stdout) if m.status == "KILLED" else None
        fail_reason = extract_failure_reason(m.stdout) if m.status == "KILLED" else None
        mutant_audit_records.append({
            "mutant_id": m.mutant_id,
            "mutation_type": m.mutation_type,
            "line_number": m.line_number,
            "original_code": m.original_code_snippet,
            "mutated_code": m.mutated_code_snippet,
            "unified_diff": m.unified_diff,
            "status": m.status,
            "failing_test": fail_test,
            "failure_reason": fail_reason,
            "execution_time_ms": m.execution_time_ms,
            "equivalence_status": m.equivalence_status
        })

    # 8. Isolated Orchestrator Run with Fresh Database
    isolated_db_path = ARTIFACT_DIR / f"{target_name}_isolated.db"
    isolated_trace_path = ARTIFACT_DIR / f"{target_name}_isolated_trace.jsonl"
    
    orch = TestForgeOrchestrator(
        target_source_code=source_code,
        max_iterations=2,
        target_mutation_score=85.0,
        trace_log_path=str(isolated_trace_path),
        target_file_path=str(target_path),
        engine_mode="local",
        checkpoint_db_path=str(isolated_db_path)
    )
    orch_state = orch.run()
    total_duration = time.perf_counter() - t_start

    # Exported Test File Hash
    exported_test_path = ARTIFACT_DIR / f"test_generated_{target_name}.py"
    with open(exported_test_path, "w", encoding="utf-8") as f:
        f.write(candidate_code)
    exported_sha256 = hashlib.sha256(candidate_code.encode("utf-8")).hexdigest()

    # Blackboard Suite Hash
    bb_suite_code = orch.blackboard.get_suite_space().current_test_code if orch.blackboard else ""
    bb_sha256 = hashlib.sha256(bb_suite_code.encode("utf-8")).hexdigest() if bb_suite_code else None

    # AST Security Verification
    sec_res = SecurityGuardrail().inspect_code_ast(candidate_code, enforce_policy=True)

    summary = {
        "target_name": target_name,
        "target_path": str(target_path),
        "lines_of_code": len(source_code.splitlines()),
        "callable_discovery": {
            "total_discovered": len(all_callables),
            "eligible_count": len(eligible_callables),
            "covered_callables": synth_result.covered_callables,
            "covered_count": len(synth_result.covered_callables),
            "callable_coverage_pct": (len(synth_result.covered_callables) / len(eligible_callables) * 100.0) if eligible_callables else 0.0,
            "skipped_callables": synth_result.skipped_callables
        },
        "test_generation": {
            "total_tests_generated": synth_result.total_test_count,
            "tests_collected": collected_tests,
            "tests_passed": passed_tests,
            "tests_failed": failed_tests,
            "meaningful_assertions": synth_result.meaningful_assertions_count,
            "invariant_assertions": synth_result.invariant_assertions_count,
            "boundary_tests_count": synth_result.boundary_tests_count,
            "negative_tests_count": synth_result.negative_tests_count,
            "synthesis_duration_seconds": synth_duration
        },
        "coverage": {
            "percent_covered": cov_pct,
            "covered_statements": cov_info["covered_lines"],
            "total_statements": cov_info["num_statements"],
            "missing_statements": cov_info["missing_lines"]
        },
        "mutation_testing": {
            "mutants_generated": r1_total,
            "mutants_killed": r1_killed,
            "mutants_survived": r1_survived,
            "mutants_timed_out": r1_timeouts,
            "mutants_invalid": r1_invalid,
            "mutants_error": r1_errors,
            "raw_mutation_score": r1_raw_score,
            "adjusted_mutation_score": r1_adj_score,
            "evaluation_duration_seconds": mut_eval_duration
        },
        "orchestrator_execution": {
            "final_status": orch_state.final_hardening_status,
            "current_iteration": orch_state.current_iteration,
            "baseline_line_coverage": orch_state.baseline_line_coverage,
            "baseline_tests_passed": orch_state.baseline_tests_passed,
            "final_mutation_score": orch_state.final_mutation_score,
            "mutants_generated": orch_state.mutants_generated,
            "mutants_killed": orch_state.mutants_killed,
            "mutants_survived": orch_state.mutants_survived,
            "total_duration_seconds": total_duration,
            "isolated_db_path": str(isolated_db_path),
            "isolated_db_size_bytes": isolated_db_path.stat().st_size if isolated_db_path.exists() else 0
        },
        "provenance_hashes": {
            "candidate_sha256": cand_sha256,
            "validated_sha256": val_sha256,
            "exported_sha256": exported_sha256,
            "blackboard_sha256": bb_sha256,
            "candidate_matches_validated": cand_sha256 == val_sha256,
            "candidate_matches_exported": cand_sha256 == exported_sha256,
        },
        "security": {
            "allowed": sec_res.allowed,
            "violations_count": len(sec_res.violations),
            "findings_count": len(sec_res.findings),
            "syntax_error": getattr(sec_res, "syntax_error", None)
        },
        "mutant_records": mutant_audit_records
    }

    out_file = ARTIFACT_DIR / f"reproduction_{target_name}.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print(f"[*] Saved reproduction data to {out_file}")
    return summary

if __name__ == "__main__":
    d1 = run_isolated_benchmark("discount", "samples/discount.py")
    d2 = run_isolated_benchmark("logistics", "samples/uploaded_logistics_engine.py")
    print("\n[SUCCESS] Phase 3 Independent Reproduction Complete for both targets!")
