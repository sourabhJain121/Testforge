"""
testforge/scripts/cross_check_mutmut.py

Task 5 (mutmut Cross-Check):
Runs mutmut on 3 targets (samples/discount.py, samples/order_fsm.py, samples/sealed_v2/bisect_algo.py)
in an isolated temporary workspace and compares per-mutant outcomes against TestForge ASTMutator.
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from typing import Any, Dict, List

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from testforge.benchmarking import BenchmarkRunner
from testforge.mutator import ASTMutator

TARGET_CONFIGS = [
    {
        "name": "discount",
        "target_path": "samples/discount.py",
        "test_path": "tests/manual_oracles/test_manual_discount.py",
        "module_import": "from samples.discount import calculate_discount",
    },
    {
        "name": "order_fsm",
        "target_path": "samples/order_fsm.py",
        "test_path": "tests/manual_oracles/test_manual_order_fsm.py",
        "module_import": "from samples.order_fsm import OrderFSM, OrderState, OrderEvent",
    },
    {
        "name": "bisect_algo",
        "target_path": "samples/sealed_v2/bisect_algo.py",
        "test_content": """import pytest
from samples.sealed_v2.bisect_algo import bisect_left, bisect_right, insort_left, insort_right

def test_bisect_starter():
    a = [1, 2, 4, 5]
    assert bisect_left(a, 3) == 2
    assert bisect_right(a, 3) == 2
    insort_left(a, 3)
    assert a == [1, 2, 3, 4, 5]
""",
    },
]


def run_testforge_evaluation(target_path: str, test_code: str) -> Dict[str, Any]:
    with open(os.path.join(REPO_ROOT, target_path), "r", encoding="utf-8") as f:
        src = f.read()
    runner = BenchmarkRunner(target_code=src, target_file_path=os.path.join(REPO_ROOT, target_path))
    eval_res = runner.evaluate_suite(test_code)
    return {
        "engine": "TestForge ASTMutator",
        "total_mutants": eval_res.total,
        "killed": eval_res.killed,
        "survived": eval_res.survived,
        "timed_out": eval_res.timed_out,
        "mutation_score_pct": eval_res.score or 0.0,
        "line_cov_pct": eval_res.cov_pct,
        "branch_cov_pct": eval_res.branch_cov_pct,
        "baseline_passed": eval_res.baseline_passed,
    }


def run_mutmut_evaluation(target_path: str, test_code: str, target_name: str) -> Dict[str, Any]:
    py_bin = os.path.join(REPO_ROOT, ".venv-release/bin/python")
    mutmut_bin = os.path.join(REPO_ROOT, ".venv-release/bin/mutmut")
    
    with tempfile.TemporaryDirectory(prefix=f"testforge_mutmut_{target_name}_") as tmpdir:
        # Copy target into tmpdir
        target_filename = os.path.basename(target_path)
        tmp_target = os.path.join(tmpdir, target_filename)
        with open(os.path.join(REPO_ROOT, target_path), "r", encoding="utf-8") as f:
            src = f.read()
        with open(tmp_target, "w", encoding="utf-8") as f:
            f.write(src)
            
        # Write test file adapting import to local target
        local_test_code = re.sub(r"from samples(?:\.sealed_v2)?\.([a-zA-Z0-9_]+)", r"from \1", test_code)
        local_test_file = os.path.join(tmpdir, f"test_{target_filename}")
        with open(local_test_file, "w", encoding="utf-8") as f:
            f.write(local_test_code)
            
        # Write pyproject.toml for mutmut
        pyproject_path = os.path.join(tmpdir, "pyproject.toml")
        with open(pyproject_path, "w", encoding="utf-8") as f:
            f.write(f"""[tool.mutmut]
source_paths = ["{target_filename}"]
tests_dir = ["test_{target_filename}"]
runner = "{py_bin} -m pytest test_{target_filename} -p no:cacheprovider"
""")
        
        env = os.environ.copy()
        env["PYTHONPATH"] = tmpdir
        
        # Run mutmut
        t0 = time.perf_counter()
        run_proc = subprocess.run(
            [mutmut_bin, "run"],
            cwd=tmpdir,
            env=env,
            capture_output=True,
            text=True,
            timeout=120
        )
        duration = round(time.perf_counter() - t0, 2)
        
        # Run mutmut results
        res_proc = subprocess.run(
            [mutmut_bin, "results"],
            cwd=tmpdir,
            env=env,
            capture_output=True,
            text=True,
            timeout=30
        )
        
        results_output = res_proc.stdout or ""
        # Parse mutmut results:
        # e.g. "discount.x_calculate_discount__mutmut_1: killed" or "survived" or "timed out"
        lines = [line.strip() for line in results_output.splitlines() if ":" in line]
        total = len(lines)
        killed = sum(1 for line in lines if "killed" in line.lower())
        survived = sum(1 for line in lines if "survived" in line.lower())
        timed_out = sum(1 for line in lines if "timed out" in line.lower() or "timeout" in line.lower())
        score = round((killed / total * 100.0), 2) if total > 0 else 0.0
        
        return {
            "engine": "mutmut 3.8.1",
            "total_mutants": total,
            "killed": killed,
            "survived": survived,
            "timed_out": timed_out,
            "mutation_score_pct": score,
            "duration_sec": duration,
            "raw_results_snippet": results_output[:400]
        }


def main():
    print("=" * 70)
    print("TESTFORGE vs. MUTMUT CROSS-CHECK AUDIT (Task 5)")
    print("=" * 70)
    
    comparisons = []
    
    for cfg in TARGET_CONFIGS:
        t_name = cfg["name"]
        print(f"\n[+] Cross-checking target: {t_name}")
        
        if "test_path" in cfg:
            with open(os.path.join(REPO_ROOT, cfg["test_path"]), "r", encoding="utf-8") as f:
                test_code = f.read()
        else:
            test_code = cfg["test_content"]
            
        print("  • Running TestForge ASTMutator evaluation...")
        tf_res = run_testforge_evaluation(cfg["target_path"], test_code)
        print(f"    TestForge: {tf_res['killed']}/{tf_res['total_mutants']} killed ({tf_res['mutation_score_pct']}%)")
        
        print("  • Running mutmut 3.8.1 evaluation...")
        try:
            mm_res = run_mutmut_evaluation(cfg["target_path"], test_code, t_name)
            print(f"    mutmut:    {mm_res['killed']}/{mm_res['total_mutants']} killed ({mm_res['mutation_score_pct']}%) in {mm_res['duration_sec']}s")
        except Exception as exc:
            mm_res = {"engine": "mutmut 3.8.1", "error": str(exc)}
            print(f"    mutmut failed: {exc}")
            
        comparisons.append({
            "target": t_name,
            "testforge": tf_res,
            "mutmut": mm_res
        })
        
    out_dir = os.path.join(REPO_ROOT, "docs/AUDIT_EVIDENCE/release")
    os.makedirs(out_dir, exist_ok=True)
    out_file = os.path.join(out_dir, "mutmut_cross_check.txt")
    with open(out_file, "w", encoding="utf-8") as f:
        f.write("TESTFORGE vs MUTMUT CROSS-CHECK REPORT\n")
        f.write("Generated at: " + time.strftime("%Y-%m-%d %H:%M:%S") + "\n\n")
        f.write(json.dumps(comparisons, indent=2))
        f.write("\n")
        
    print(f"\n[✓] Mutmut cross-check completed. Evidence written to {out_file}")


if __name__ == "__main__":
    main()

