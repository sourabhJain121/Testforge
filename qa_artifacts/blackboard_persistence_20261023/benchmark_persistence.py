"""
benchmark_persistence.py - Micro-benchmark measuring SQLite Blackboard Checkpoint performance.
Measures snapshot size, save latency, load latency, and in-memory vs persisted overhead.
"""

import os
import time
import json
import statistics
from pathlib import Path
from typing import Dict, Any, List

from testforge.persistence import SQLiteBlackboardStorage
from testforge.blackboard import Blackboard
from testforge.state import MutantRecord, IterationMetrics

OUTPUT_DIR = Path("qa_artifacts/blackboard_persistence_20261023")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
BENCHMARK_DB = OUTPUT_DIR / "perf_benchmark.db"

def build_representative_blackboard(num_mutants: int = 50) -> Blackboard:
    bb = Blackboard()
    source_code = (
        "def process_transactions(records, fee_rate=0.015):\n"
        "    total_fees = 0.0\n"
        "    processed = []\n"
        "    for rec in records:\n"
        "        amount = rec.get('amount', 0.0)\n"
        "        if amount > 0:\n"
        "            fee = amount * fee_rate\n"
        "            total_fees += fee\n"
        "            processed.append({'id': rec.get('id'), 'net': amount - fee})\n"
        "    return {'total_fees': total_fees, 'processed': processed}\n"
    )
    bb.update_target_space(
        target_module_path="samples/billing.py",
        target_source_code=source_code,
        functions=["process_transactions"],
        blast_risk="MEDIUM",
        line_count=10,
    )
    mutants = []
    for i in range(1, num_mutants + 1):
        m_type = "ARITH_OP" if i % 2 == 0 else "COMP_OP"
        status = "KILLED" if i % 4 != 0 else "SURVIVED"
        mutants.append(
            MutantRecord(
                mutant_id=f"MUT_PERF_{i:03d}",
                mutation_type=m_type,
                line_number=(i % 8) + 2,
                original_code_snippet=f"line snippet {i} in billing",
                mutated_code_snippet=f"mutated snippet {i} in billing",
                unified_diff=f"--- billing.py\n+++ billing.py\n@@ -{i},1 +{i},1 @@\n- fee = amount * fee_rate\n+ fee = amount / fee_rate\n",
                status=status,
                execution_time_ms=10.5 + (i * 0.1),
            )
        )
    bb.update_mutant_space(
        mutants=mutants,
        mutants_generated=num_mutants,
        mutants_executed=num_mutants,
        mutants_killed=sum(1 for m in mutants if m.status == "KILLED"),
        mutants_survived=sum(1 for m in mutants if m.status == "SURVIVED"),
        current_mutation_score=75.0,
        surviving_mutant_diffs=[m.unified_diff for m in mutants if m.status == "SURVIVED"],
    )
    bb.update_critic_space(
        critic_directives=[f"Directive {j}: verify division by zero handling" for j in range(5)],
        latest_directive="Directive 4: verify division by zero handling",
        reflection_notes=["Note A: floating point boundary rounding", "Note B: zero fee rate edge case"],
    )
    test_code = (
        "import pytest\n"
        "from samples.billing import process_transactions\n\n"
        "def test_process_transactions():\n"
        "    res = process_transactions([{'id': 1, 'amount': 100.0}])\n"
        "    assert res['total_fees'] == 1.5\n"
    )
    bb.update_suite_space(
        test_module_path="test_billing.py",
        current_test_code=test_code,
        baseline_test_code=test_code,
        active_provider="Google GenAI Live",
        baseline_passed=True,
        baseline_tests_generated=5,
        baseline_tests_executed=5,
        baseline_tests_passed=5,
    )
    history = []
    for it in range(1, 4):
        history.append(
            IterationMetrics(
                iteration=it,
                total_mutants=num_mutants,
                killed_mutants=int(num_mutants * (0.5 + it * 0.1)),
                survived_mutants=num_mutants - int(num_mutants * (0.5 + it * 0.1)),
                timed_out_mutants=0,
                mutation_score=50.0 + it * 10.0,
                line_coverage_pct=90.0,
                duration_seconds=2.5,
            )
        )
    bb.update_metrics_space(
        current_iteration=3,
        max_iterations=3,
        target_mutation_score=85.0,
        baseline_line_coverage=90.0,
        lines_covered=9,
        num_statements=10,
        history=history,
        final_mutation_score=80.0,
        reflection_iterations_performed=3,
        final_hardening_status="SUCCESS",
        hardware_info={"cores": 10, "arch": "arm64", "memory_gb": 16},
    )
    return bb

def run_benchmark():
    if BENCHMARK_DB.exists():
        BENCHMARK_DB.unlink()

    storage = SQLiteBlackboardStorage(BENCHMARK_DB)
    bb = build_representative_blackboard(num_mutants=50)
    snapshot = bb.get_snapshot()

    raw_json = json.dumps(snapshot.model_dump())
    snapshot_bytes = len(raw_json)

    # 1. Measure Save Latency
    save_times_ms: List[float] = []
    checkpoint_ids: List[str] = []
    for i in range(100):
        t0 = time.perf_counter()
        meta = storage.save_checkpoint(
            snapshot=snapshot,
            stage=f"PERF_STEP_{i}",
            job_id="bench_job_1",
            workflow_id="bench_wf_1"
        )
        t1 = time.perf_counter()
        save_times_ms.append((t1 - t0) * 1000.0)
        checkpoint_ids.append(meta.checkpoint_id)

    # 2. Measure Load Latency
    load_times_ms: List[float] = []
    for cid in checkpoint_ids[:50]:
        t0 = time.perf_counter()
        storage.load_checkpoint(cid)
        t1 = time.perf_counter()
        load_times_ms.append((t1 - t0) * 1000.0)

    # 3. Measure In-Memory vs Persistent blackboard update overhead
    in_mem_bb = Blackboard()
    t_in_mem_start = time.perf_counter()
    for _ in range(1000):
        in_mem_bb.update_metrics_space(current_iteration=1)
    in_mem_overhead_ms = (time.perf_counter() - t_in_mem_start) * 1000.0 / 1000.0

    persisted_bb = Blackboard(storage=storage)
    t_persist_bb_start = time.perf_counter()
    for j in range(50):
        persisted_bb.update_metrics_space(current_iteration=j % 3)
        persisted_bb.save_checkpoint(stage=f"OVERHEAD_{j}")
    persisted_op_ms = (time.perf_counter() - t_persist_bb_start) * 1000.0 / 50.0

    storage.close()

    db_size_bytes = BENCHMARK_DB.stat().st_size if BENCHMARK_DB.exists() else 0

    results = {
        "timestamp": time.time(),
        "database_path": str(BENCHMARK_DB),
        "database_size_bytes": db_size_bytes,
        "database_size_kb": round(db_size_bytes / 1024.0, 2),
        "representative_snapshot": {
            "num_mutants": 50,
            "num_history_entries": 3,
            "snapshot_size_bytes": snapshot_bytes,
            "snapshot_size_kb": round(snapshot_bytes / 1024.0, 2),
        },
        "save_performance_ms": {
            "samples": len(save_times_ms),
            "mean": round(statistics.mean(save_times_ms), 3),
            "median": round(statistics.median(save_times_ms), 3),
            "min": round(min(save_times_ms), 3),
            "max": round(max(save_times_ms), 3),
            "p95": round(statistics.quantiles(save_times_ms, n=20)[18], 3),
        },
        "load_performance_ms": {
            "samples": len(load_times_ms),
            "mean": round(statistics.mean(load_times_ms), 3),
            "median": round(statistics.median(load_times_ms), 3),
            "min": round(min(load_times_ms), 3),
            "max": round(max(load_times_ms), 3),
            "p95": round(statistics.quantiles(load_times_ms, n=20)[18], 3),
        },
        "overhead_comparison_ms": {
            "in_memory_update_only_ms": round(in_mem_overhead_ms, 4),
            "update_and_checkpoint_save_ms": round(persisted_op_ms, 3),
        }
    }

    results_file = OUTPUT_DIR / "persistence_benchmark_results.json"
    results_file.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(json.dumps(results, indent=2))
    return results

if __name__ == "__main__":
    run_benchmark()
