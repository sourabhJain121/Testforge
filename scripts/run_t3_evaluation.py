"""
scripts/run_t3_evaluation.py - Evaluation Runner for T3 New Targets.

Evaluates Developer Baseline vs. Pure Deterministic vs. Hybrid Synthesizer
across 2 brand-new targets:
  1. samples/jwt_validator.py
  2. samples/rate_limiter.py

Enforces strict DEF-022 clean preflight validation and saves raw evidence
to docs/AUDIT_EVIDENCE/T3/.
"""

from __future__ import annotations

import json
import os
import sys
import time
from typing import Any, Dict

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from testforge.benchmarking import BenchmarkRunner
from testforge.hybrid_synthesizer import HybridSynthesizer
from testforge.intelligent_generator import IntelligentASTSynthesizer

NEW_TARGETS = [
    {
        "name": "jwt_validator",
        "file": "jwt_validator.py",
        "path": "samples/jwt_validator.py",
        "starter_test": (
            "from target import encode_jwt, decode_jwt, is_token_expired, validate_token_claims\n\n"
            "def test_jwt_starter():\n"
            "    token = encode_jwt({'sub': 'admin', 'exp': 2000000000}, secret='secret_key')\n"
            "    payload = decode_jwt(token, secret='secret_key', current_time=1900000000)\n"
            "    assert payload['sub'] == 'admin'\n"
            "    assert is_token_expired(token, current_time=1900000000) is False\n"
            "    assert validate_token_claims(payload, ['sub']) is True\n"
        ),
    },
    {
        "name": "rate_limiter",
        "file": "rate_limiter.py",
        "path": "samples/rate_limiter.py",
        "starter_test": (
            "from target import TokenBucket, SlidingWindowRateLimiter\n\n"
            "def test_rate_limiter_starter():\n"
            "    tb = TokenBucket(capacity=10.0, refill_rate=2.0, initial_tokens=10.0, now=100.0)\n"
            "    assert tb.consume(5.0, now=100.0) is True\n"
            "    assert tb.time_until_available(1.0, now=100.0) == 0.0\n"
            "    sw = SlidingWindowRateLimiter(max_requests=5, window_seconds=60.0)\n"
            "    assert sw.allow_request('client_a', now=100.0) is True\n"
            "    assert sw.get_remaining_calls('client_a', now=100.0) == 4\n"
        ),
    },
]


def run_evaluation() -> Dict[str, Any]:
    print("=" * 80)
    print("TESTFORGE T3 NEW TARGETS BENCHMARK EVALUATION")
    print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("Conditions: 1. Developer Baseline | 2. Pure Deterministic AST | 3. Hybrid Synthesizer")
    print("=" * 80)

    results = {}

    for t_spec in NEW_TARGETS:
        t_name = t_spec["name"]
        t_path = t_spec["path"]
        full_path = os.path.join(REPO_ROOT, t_path)
        with open(full_path, "r", encoding="utf-8") as f:
            src = f.read()

        runner = BenchmarkRunner(target_code=src, target_file_path=t_path)

        # ----------------------------------------------------------------------
        # 1. Developer Starter Baseline
        # ----------------------------------------------------------------------
        t0 = time.perf_counter()
        base_eval = runner.evaluate_suite(t_spec["starter_test"])
        base_dur = round(time.perf_counter() - t0, 3)

        # ----------------------------------------------------------------------
        # 2. Pure Deterministic AST Synthesizer
        # ----------------------------------------------------------------------
        synth = IntelligentASTSynthesizer()
        synth_res = synth.synthesize_test_suite(src)
        t0 = time.perf_counter()
        det_eval = runner.evaluate_suite(synth_res.test_code)
        det_dur = round(time.perf_counter() - t0, 3)

        # ----------------------------------------------------------------------
        # 3. Hybrid Synthesizer with Never-Regress Guard
        # ----------------------------------------------------------------------
        t0 = time.perf_counter()
        hybrid_engine = HybridSynthesizer(
            target_code=src,
            target_file_path=t_path,
            max_iterations=3,
            timeout_seconds=3.0,
        )
        hybrid_res = hybrid_engine.synthesize(initial_seed_tests=t_spec["starter_test"])
        hybrid_dur = round(time.perf_counter() - t0, 3)

        results[t_name] = {
            "target_path": t_path,
            "total_mutants": base_eval.total,
            "developer_baseline": {
                "line_cov": base_eval.cov_pct,
                "branch_cov": base_eval.branch_cov_pct,
                "raw_ms": base_eval.score or 0.0,
                "adj_ms": base_eval.adj_score or 0.0,
                "killed": base_eval.killed,
                "total": base_eval.total,
                "clean_pass": base_eval.baseline_passed,
                "status": "VALID" if not base_eval.invalid_suite else "INVALID_SUITE",
                "duration_sec": base_dur,
            },
            "pure_deterministic_ast": {
                "line_cov": det_eval.cov_pct,
                "branch_cov": det_eval.branch_cov_pct,
                "raw_ms": det_eval.score or 0.0,
                "adj_ms": det_eval.adj_score or 0.0,
                "killed": det_eval.killed,
                "total": det_eval.total,
                "clean_pass": det_eval.baseline_passed,
                "status": "VALID" if not det_eval.invalid_suite else "INVALID_SUITE",
                "duration_sec": det_dur,
            },
            "hybrid_synthesizer": {
                "line_cov": hybrid_res.line_coverage,
                "branch_cov": hybrid_res.branch_coverage,
                "raw_ms": hybrid_res.final_raw_ms,
                "adj_ms": hybrid_res.final_adj_ms,
                "killed": hybrid_res.killed_mutants,
                "total": hybrid_res.total_mutants,
                "clean_pass": hybrid_res.clean_pass,
                "status": "VALID" if hybrid_res.clean_pass else "INVALID_SUITE",
                "iterations_run": hybrid_res.iterations_run,
                "guard_interventions": hybrid_res.guard_interventions,
                "duration_sec": hybrid_dur,
                "delta_vs_baseline": round(hybrid_res.final_raw_ms - (base_eval.score or 0.0), 2),
                "delta_vs_deterministic": round(hybrid_res.final_raw_ms - (det_eval.score or 0.0), 2),
            },
        }

        print(f"\nTarget: {t_name} ({t_path}, Mutants: {base_eval.total})")
        print(f"  [1. Dev Baseline]    Line Cov: {base_eval.cov_pct:.1f}% | Branch: {base_eval.branch_cov_pct:.1f}% | "
              f"Killed: {base_eval.killed}/{base_eval.total} | Raw MS: {base_eval.score or 0.0:.2f}% | "
              f"Pass@1: {'PASS' if base_eval.baseline_passed else 'FAIL'}")
        print(f"  [2. Deterministic]   Line Cov: {det_eval.cov_pct:.1f}% | Branch: {det_eval.branch_cov_pct:.1f}% | "
              f"Killed: {det_eval.killed}/{det_eval.total} | Raw MS: {det_eval.score or 0.0:.2f}% | "
              f"Pass@1: {'PASS' if det_eval.baseline_passed else 'FAIL'}")
        print(f"  [3. Hybrid Synthesizer] Line Cov: {hybrid_res.line_coverage:.1f}% | Branch: {hybrid_res.branch_coverage:.1f}% | "
              f"Killed: {hybrid_res.killed_mutants}/{hybrid_res.total_mutants} | Raw MS: {hybrid_res.final_raw_ms:.2f}% | "
              f"Adj MS: {hybrid_res.final_adj_ms:.2f}% | Delta vs Base: +{results[t_name]['hybrid_synthesizer']['delta_vs_baseline']}% | "
              f"Pass@1: {'PASS' if hybrid_res.clean_pass else 'FAIL'} (Never-Regress Guard: {hybrid_res.guard_interventions} interventions)")

    return results


def main():
    results = run_evaluation()

    out_dir = os.path.join(REPO_ROOT, "docs", "AUDIT_EVIDENCE", "T3")
    os.makedirs(out_dir, exist_ok=True)

    json_path = os.path.join(out_dir, "t3_evaluation_results.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

    print("\n" + "=" * 80)
    print(f"Saved evaluation results to {json_path}")
    print("=" * 80)


if __name__ == "__main__":
    main()

