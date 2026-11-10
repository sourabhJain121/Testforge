"""
scripts/run_t2_rescore.py - Verification & Audit Rescore Script for T2.

Executes the fixed DEF-022 verification harness across:
1. Canonical 4 Targets (samples/discount.py, samples/order_fsm.py, samples/lru_cache.py, samples/stats_calculator.py):
   - Developer baseline starter tests
   - Deterministic AST synthesized tests (IntelligentASTSynthesizer)
   - Empirical agentic reflection benchmark results from qa_artifacts/MULTI_TARGET_BENCHMARK_RESULTS.json
2. Sealed Set V2 (6 Targets in samples/sealed_v2/*.py):
   - Developer baseline starter tests
   - Deterministic AST synthesized tests (IntelligentASTSynthesizer)
   - DEF-022 Clean reference execution check (Pass@1)
   - Full mutation kill accounting: killed, survived, equivalent, raw_ms, adj_ms, status (VALID vs INVALID_SUITE)
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

from testforge.benchmarking import BenchmarkRunner, SuiteEvaluationResult
from testforge.intelligent_generator import IntelligentASTSynthesizer

CANONICAL_TARGETS = [
    "samples/discount.py",
    "samples/order_fsm.py",
    "samples/lru_cache.py",
    "samples/stats_calculator.py",
]

SEALED_V2_TARGETS = [
    {
        "name": "bisect_algo",
        "file": "bisect_algo.py",
        "path": "samples/sealed_v2/bisect_algo.py",
        "starter_test": (
            "import pytest\n"
            "from target import bisect_left, bisect_right, insort_left, insort_right\n\n"
            "def test_bisect_starter():\n"
            "    data = [1, 3, 5, 7]\n"
            "    assert bisect_left(data, 3) == 1\n"
            "    assert bisect_right(data, 3) == 2\n"
        ),
    },
    {
        "name": "fractions_algo",
        "file": "fractions_algo.py",
        "path": "samples/sealed_v2/fractions_algo.py",
        "starter_test": (
            "import pytest\n"
            "from target import Fraction, gcd\n\n"
            "def test_fraction_starter():\n"
            "    f = Fraction(2, 4)\n"
            "    assert f.numerator == 1\n"
            "    assert f.denominator == 2\n"
            "    assert gcd(12, 18) == 6\n"
        ),
    },
    {
        "name": "heapq_algo",
        "file": "heapq_algo.py",
        "path": "samples/sealed_v2/heapq_algo.py",
        "starter_test": (
            "import pytest\n"
            "from target import heappush, heappop, heapify\n\n"
            "def test_heap_starter():\n"
            "    h = [5, 1, 3]\n"
            "    heapify(h)\n"
            "    assert heappop(h) == 1\n"
        ),
    },
    {
        "name": "shlex_algo",
        "file": "shlex_algo.py",
        "path": "samples/sealed_v2/shlex_algo.py",
        "starter_test": (
            "import pytest\n"
            "from target import shlex_split\n\n"
            "def test_shlex_starter():\n"
            "    assert shlex_split('hello world') == ['hello', 'world']\n"
        ),
    },
    {
        "name": "statistics_algo",
        "file": "statistics_algo.py",
        "path": "samples/sealed_v2/statistics_algo.py",
        "starter_test": (
            "import pytest\n"
            "from target import fmean, median, variance\n\n"
            "def test_stats_starter():\n"
            "    assert fmean([1.0, 2.0, 3.0]) == 2.0\n"
            "    assert median([1, 2, 3]) == 2\n"
        ),
    },
    {
        "name": "textwrap_algo",
        "file": "textwrap_algo.py",
        "path": "samples/sealed_v2/textwrap_algo.py",
        "starter_test": (
            "import pytest\n"
            "from target import wrap, fill\n\n"
            "def test_textwrap_starter():\n"
            "    res = wrap('hello world foo bar', width=10)\n"
            "    assert res == ['hello', 'world foo', 'bar']\n"
        ),
    },
]


def rescore_canonical_targets() -> Dict[str, Any]:
    print("=" * 80)
    print("PART 1: CANONICAL 4 TARGET RESCORE (DEF-022 FIXED HARNESS)")
    print("=" * 80)

    multi_target_artifact_path = os.path.join(REPO_ROOT, "qa_artifacts", "MULTI_TARGET_BENCHMARK_RESULTS.json")
    with open(multi_target_artifact_path, "r", encoding="utf-8") as f:
        mt_artifact = json.load(f)

    results = {}

    for t_path in CANONICAL_TARGETS:
        full_path = os.path.join(REPO_ROOT, t_path)
        with open(full_path, "r", encoding="utf-8") as f:
            src = f.read()

        runner = BenchmarkRunner(target_code=src, target_file_path=t_path)
        base_test = runner._resolve_default_baseline()

        # 1. Dev Baseline
        t0 = time.perf_counter()
        base_eval = runner.evaluate_suite(base_test)
        base_dur = time.perf_counter() - t0

        # 2. Deterministic AST Synthesizer
        synth = IntelligentASTSynthesizer()
        synth_suite = synth.synthesize_test_suite(src)
        t0 = time.perf_counter()
        synth_eval = runner.evaluate_suite(synth_suite.test_code)
        synth_dur = time.perf_counter() - t0

        # 3. Read empirical reflection numbers from multi-target artifact
        art_target = mt_artifact["targets"].get(t_path, {})
        refl_data = art_target.get("scenarios", {}).get("agentic_reflection", {})

        results[t_path] = {
            "baseline": {
                "cov_pct": base_eval.cov_pct,
                "branch_cov": base_eval.branch_cov_pct,
                "raw_ms": base_eval.score,
                "adj_ms": base_eval.adj_score,
                "killed": base_eval.killed,
                "total": base_eval.total,
                "baseline_passed": base_eval.baseline_passed,
                "invalid_suite": base_eval.invalid_suite,
                "duration_sec": round(base_dur, 3),
            },
            "deterministic_ast": {
                "cov_pct": synth_eval.cov_pct,
                "branch_cov": synth_eval.branch_cov_pct,
                "raw_ms": synth_eval.score,
                "adj_ms": synth_eval.adj_score,
                "killed": synth_eval.killed,
                "total": synth_eval.total,
                "baseline_passed": synth_eval.baseline_passed,
                "invalid_suite": synth_eval.invalid_suite,
                "duration_sec": round(synth_dur, 3),
            },
            "agentic_reflection_empirical": {
                "cov_pct": refl_data.get("line_coverage_pct"),
                "branch_cov": refl_data.get("branch_coverage_pct"),
                "raw_ms": refl_data.get("raw_mutation_score"),
                "adj_ms": refl_data.get("adjusted_mutation_score"),
                "killed": refl_data.get("killed_mutants"),
                "total": refl_data.get("total_mutants"),
                "duration_sec": refl_data.get("mean_latency_sec"),
            },
        }

        print(f"\n--- Target: {t_path} (Total Mutants: {base_eval.total}) ---")
        print(f"  [Baseline]      Line Cov: {base_eval.cov_pct:.1f}% | Branch Cov: {base_eval.branch_cov_pct:.1f}% | "
              f"Killed: {base_eval.killed}/{base_eval.total} | Raw MS: {base_eval.score}% | Adj MS: {base_eval.adj_score}% | "
              f"Status: {'VALID' if not base_eval.invalid_suite else 'INVALID_SUITE'}")
        print(f"  [Deterministic] Line Cov: {synth_eval.cov_pct:.1f}% | Branch Cov: {synth_eval.branch_cov_pct:.1f}% | "
              f"Killed: {synth_eval.killed}/{synth_eval.total} | Raw MS: {synth_eval.score}% | Adj MS: {synth_eval.adj_score}% | "
              f"Status: {'VALID' if not synth_eval.invalid_suite else 'INVALID_SUITE'}")
        print(f"  [Reflection]    Line Cov: {refl_data.get('line_coverage_pct')}% | Branch Cov: {refl_data.get('branch_coverage_pct')}% | "
              f"Killed: {refl_data.get('killed_mutants')}/{refl_data.get('total_mutants')} | "
              f"Raw MS: {refl_data.get('raw_mutation_score')}% | Adj MS: {refl_data.get('adjusted_mutation_score')}%")

    return results


def rescore_sealed_v2_targets() -> Dict[str, Any]:
    print("\n" + "=" * 80)
    print("PART 2: SEALED SET V2 TARGET RESCORE (DEF-022 STRICT HARNESS)")
    print("=" * 80)

    results = {}

    for t_spec in SEALED_V2_TARGETS:
        t_name = t_spec["name"]
        t_path = t_spec["path"]
        full_path = os.path.join(REPO_ROOT, t_path)
        with open(full_path, "r", encoding="utf-8") as f:
            src = f.read()

        runner = BenchmarkRunner(target_code=src, target_file_path=t_path)

        # 1. Developer Starter Baseline
        t0 = time.perf_counter()
        dev_eval = runner.evaluate_suite(t_spec["starter_test"])
        dev_dur = time.perf_counter() - t0

        # 2. IntelligentASTSynthesizer
        synth = IntelligentASTSynthesizer()
        synth_suite = synth.synthesize_test_suite(src)
        t0 = time.perf_counter()
        det_eval = runner.evaluate_suite(synth_suite.test_code)
        det_dur = time.perf_counter() - t0

        results[t_name] = {
            "dev_baseline": {
                "cov_pct": dev_eval.cov_pct,
                "branch_cov": dev_eval.branch_cov_pct,
                "killed": dev_eval.killed,
                "total": dev_eval.total,
                "raw_ms": dev_eval.score or 0.0,
                "adj_ms": dev_eval.adj_score or 0.0,
                "baseline_passed": dev_eval.baseline_passed,
                "invalid_suite": dev_eval.invalid_suite,
                "duration_sec": round(dev_dur, 3),
            },
            "deterministic": {
                "cov_pct": det_eval.cov_pct,
                "branch_cov": det_eval.branch_cov_pct,
                "killed": det_eval.killed,
                "total": det_eval.total,
                "raw_ms": det_eval.score or 0.0,
                "adj_ms": det_eval.adj_score or 0.0,
                "baseline_passed": det_eval.baseline_passed,
                "invalid_suite": det_eval.invalid_suite,
                "duration_sec": round(det_dur, 3),
            },
        }

        print(f"\n--- Target: {t_name} ({t_path}, Mutants: {dev_eval.total}) ---")
        print(f"  [Dev Baseline]  Line Cov: {dev_eval.cov_pct:.1f}% | Branch Cov: {dev_eval.branch_cov_pct:.1f}% | "
              f"Killed: {dev_eval.killed}/{dev_eval.total} | Raw MS: {dev_eval.score or 0.0:.2f}% | "
              f"Pass@1: {'PASS' if dev_eval.baseline_passed else 'FAIL'} | "
              f"Status: {'VALID' if not dev_eval.invalid_suite else 'INVALID_SUITE'}")
        print(f"  [Deterministic] Line Cov: {det_eval.cov_pct:.1f}% | Branch Cov: {det_eval.branch_cov_pct:.1f}% | "
              f"Killed: {det_eval.killed}/{det_eval.total} | Raw MS: {det_eval.score or 0.0:.2f}% | "
              f"Pass@1: {'PASS' if det_eval.baseline_passed else 'FAIL'} | "
              f"Status: {'VALID' if not det_eval.invalid_suite else 'INVALID_SUITE'}")

    return results


def main():
    print(f"TestForge DEF-022 Provenance Rescore Runner")
    print(f"Timestamp: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Python: {sys.version}")

    canonical_res = rescore_canonical_targets()
    sealed_res = rescore_sealed_v2_targets()

    # Calculate Sealed V2 Deterministic Aggregate
    sealed_det_scores = [v["deterministic"]["raw_ms"] for v in sealed_res.values()]
    mean_sealed_det = sum(sealed_det_scores) / len(sealed_det_scores)
    print("\n" + "=" * 80)
    print("SEALED SET V2 SUMMARY AUDIT")
    print("=" * 80)
    print(f"Audited Deterministic Raw Mutation Scores across 6 targets:")
    for k, v in sealed_res.items():
        status_lbl = "INVALID_SUITE (0 kills)" if v["deterministic"]["invalid_suite"] else f"VALID ({v['deterministic']['raw_ms']}%)"
        print(f"  {k:18s}: {status_lbl}")
    print(f"\nMean Audited Deterministic Raw Mutation Score: {mean_sealed_det:.2f}%")
    print(f"Historical Pre-DEF-022 Inflated Mean: 62.8% (RETRACTED)")
    print(f"Defect Correction: bisect_algo & heapq_algo candidate suites failed clean code and were corrected from 100% false-kills to 0% kills.")

    # Save output json
    out_dir = os.path.join(REPO_ROOT, "docs", "AUDIT_EVIDENCE", "T2")
    os.makedirs(out_dir, exist_ok=True)
    out_json = os.path.join(out_dir, "rescore_verified_summary.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump({"canonical": canonical_res, "sealed_v2": sealed_res, "mean_sealed_v2_deterministic": round(mean_sealed_det, 2)}, f, indent=2)
    print(f"\nSaved structured audit summary to {out_json}")


if __name__ == "__main__":
    main()
