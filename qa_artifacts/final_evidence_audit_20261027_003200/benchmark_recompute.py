#!/usr/bin/env python3
"""
benchmark_recompute.py - Independent verification and recomputation of TestForge benchmark metrics
from the primary source of truth: raw_benchmark_results.json.
"""

import json
import sys
from pathlib import Path
from typing import Dict, Any, List

def recompute_benchmark_metrics(json_path: Path):
    if not json_path.exists():
        print(f"Error: {json_path} does not exist.")
        sys.exit(1)

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    print("=" * 80)
    print("TESTFORGE BENCHMARK SOURCE OF TRUTH RECOMPUTATION")
    print("=" * 80)
    print(f"Source JSON: {json_path}")
    print(f"Model Claimed: {data.get('model')}")
    print(f"Total Fixtures in Header: {data.get('total_fixtures')}")
    print(f"Repetitions in Header: {data.get('repetitions')}")
    print(f"Total Records in File: {len(data.get('records', []))}")
    print(f"Global Disclaimer: {data.get('disclaimer')}")
    print("-" * 80)

    records: List[Dict[str, Any]] = data.get("records", [])

    # Group by strategy
    strategies = ["baseline", "zeroshot", "agentic_reflection"]
    by_strat: Dict[str, List[Dict[str, Any]]] = {s: [] for s in strategies}

    for r in records:
        strat = r.get("strategy")
        if strat in by_strat:
            by_strat[strat].append(r)
        else:
            by_strat.setdefault(strat, []).append(r)

    # Detailed per-fixture records
    print("\nPER-RECORD BREAKDOWN:")
    print(f"{'Strategy':<20} {'Fixture':<25} {'Tests':<6} {'Killed':<8} {'Total':<8} {'Score%':<8} {'Defect%':<8} {'FP Rate%':<10} {'Runtime(s)':<10} {'Mode'}")
    print("-" * 125)

    for strat in strategies:
        recs = by_strat.get(strat, [])
        for r in recs:
            fid = r.get("fixture_id")
            tc = r.get("tests_collected", 0)
            mk = r.get("mutants_killed", 0)
            mt = r.get("mutants_total", 0)
            score = r.get("mutation_score_pct", 0.0)
            ddr = r.get("defect_detection_rate_pct", 0.0)
            fpr = r.get("false_positive_rate_pct", 0.0)
            rt = r.get("runtime_seconds", 0.0)
            mode = r.get("execution_mode", "UNKNOWN")
            print(f"{strat:<20} {fid:<25} {tc:<6} {mk:<8} {mt:<8} {score:<8.2f} {ddr:<8.2f} {fpr:<10.2f} {rt:<10.3f} {mode}")

    print("\n" + "=" * 80)
    print("METRIC RECONCILIATION SUMMARY")
    print("=" * 80)

    summary_table = []

    for strat in strategies:
        recs = by_strat.get(strat, [])
        if not recs:
            continue

        n_recs = len(recs)
        
        # 1. Arithmetic mean of per-fixture mutation score
        scores = [r.get("mutation_score_pct", 0.0) for r in recs]
        arith_mean_score = sum(scores) / n_recs if n_recs else 0.0

        # 2. Pooled mutation score: sum(killed) / sum(total)
        total_killed = sum(r.get("mutants_killed", 0) for r in recs)
        total_mutants = sum(r.get("mutants_total", 0) for r in recs)
        pooled_score = (total_killed / total_mutants * 100.0) if total_mutants else 0.0

        # 3. Arithmetic mean of defect detection
        defects_pcts = [r.get("defect_detection_rate_pct", 0.0) for r in recs]
        arith_mean_defect = sum(defects_pcts) / n_recs if n_recs else 0.0

        # 4. Pooled defect detection: sum(defects_detected) / sum(defects_total)
        total_defects_detected = sum(len(r.get("defects_detected", [])) for r in recs)
        total_defects = sum(len(r.get("defects_detected", [])) + len(r.get("defects_survived", [])) for r in recs)
        pooled_defect = (total_defects_detected / total_defects * 100.0) if total_defects else 0.0

        # 5. Mean line coverage
        covs = [r.get("line_coverage_pct", 0.0) for r in recs]
        arith_mean_cov = sum(covs) / n_recs if n_recs else 0.0

        # 6. Mean false positive rate
        fps = [r.get("false_positive_rate_pct", 0.0) for r in recs]
        arith_mean_fp = sum(fps) / n_recs if n_recs else 0.0

        # 7. Mean runtime
        rts = [r.get("runtime_seconds", 0.0) for r in recs]
        arith_mean_rt = sum(rts) / n_recs if n_recs else 0.0

        # 8. Token expenditure
        prompt_toks = sum(r.get("tokens_prompt", 0) for r in recs)
        comp_toks = sum(r.get("tokens_completion", 0) for r in recs)
        cost_usd = sum(r.get("estimated_cost_usd", 0.0) for r in recs)

        # JSON header summary values (if present)
        json_summary = data.get("strategy_summaries", {}).get(strat, {})

        summary_table.append({
            "strategy": strat,
            "n_fixtures": n_recs,
            "arith_mean_score": arith_mean_score,
            "pooled_score": pooled_score,
            "json_mean_score": json_summary.get("mean_mutation_score"),
            "arith_mean_defect": arith_mean_defect,
            "pooled_defect": pooled_defect,
            "json_mean_defect": json_summary.get("mean_defect_detection_rate"),
            "mean_coverage": arith_mean_cov,
            "json_mean_cov": json_summary.get("mean_line_coverage"),
            "mean_fp_rate": arith_mean_fp,
            "json_mean_fp": json_summary.get("mean_false_positive_rate"),
            "mean_runtime": arith_mean_rt,
            "json_mean_rt": json_summary.get("mean_runtime_seconds"),
            "total_killed": total_killed,
            "total_mutants": total_mutants,
            "defects_detected": total_defects_detected,
            "defects_total": total_defects,
            "prompt_tokens": prompt_toks,
            "completion_tokens": comp_toks,
            "cost_usd": cost_usd,
        })

    print(f"{'Strategy':<20} {'Arith Mean Score':<18} {'Pooled Score':<15} {'JSON Summary Score':<20} {'Arith Defect%':<15} {'Pooled Defect%':<15} {'Mean Runtime':<15}")
    print("-" * 120)
    for s in summary_table:
        print(f"{s['strategy']:<20} {s['arith_mean_score']:<18.2f} {s['pooled_score']:<15.2f} {str(s['json_mean_score']):<20} {s['arith_mean_defect']:<15.2f} {s['pooled_defect']:<15.2f} {s['mean_runtime']:<15.2f}s")

    return summary_table, records

if __name__ == "__main__":
    default_json = Path("/Users/sourabh/TestForge/qa_artifacts/phase2_finalization_20261026_141500/phase5_m2_quality/raw_benchmark_results.json")
    recompute_benchmark_metrics(default_json)
