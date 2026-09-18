"""
sandbox.py - Multiprocess Sandboxed Test Execution Runtime.

Author: Shreshth (Module 2)
Course: CSE3101 - Agentic AI

Features:
  - Subprocess isolation in ephemeral temporary directories
  - Strict timeout enforcement (5s default) to guard against mutation infinite loops
  - Parallel batch execution across CPU cores via ProcessPoolExecutor
  - Hardware tuned for Apple Silicon M2 Pro (10 cores)
  - Pytest & pytest-cov execution with JSON coverage extraction
"""

from __future__ import annotations
import os
import sys
import json
import time
import tempfile
import subprocess
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Dict, Any, Tuple, List, Optional
from testforge.accel import hw_profile
from testforge.state import MutantRecord


def _run_single_test_task(test_code: str, target_code: str, timeout_seconds: int) -> Dict[str, Any]:
    """
    Isolated worker function designed for ProcessPoolExecutor execution.
    Executes pytest in a sandbox directory and returns structured output.
    """
    start_time = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="testforge_box_") as tmpdir:
        src_file = os.path.join(tmpdir, "target.py")
        test_file = os.path.join(tmpdir, "test_target.py")

        with open(src_file, "w", encoding="utf-8") as f:
            f.write(target_code)

        with open(test_file, "w", encoding="utf-8") as f:
            f.write(test_code)

        # Use the virtualenv's python executable
        pytest_cmd = [sys.executable, "-m", "pytest", test_file, "-v", "--disable-warnings", "-p", "no:cacheprovider"]

        try:
            res = subprocess.run(
                pytest_cmd,
                cwd=tmpdir,
                capture_output=True,
                text=True,
                timeout=timeout_seconds
            )
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return {
                "exit_code": res.returncode,
                "stdout": res.stdout,
                "stderr": res.stderr,
                "status": "PASS" if res.returncode == 0 else "FAIL",
                "timed_out": False,
                "duration_ms": elapsed_ms
            }
        except subprocess.TimeoutExpired:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Subprocess timed out after {timeout_seconds}s (Safety Guardrail: Infinite loop caught)",
                "status": "TIMEOUT",
                "timed_out": True,
                "duration_ms": elapsed_ms
            }
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return {
                "exit_code": -2,
                "stdout": "",
                "stderr": str(exc),
                "status": "ERROR",
                "timed_out": False,
                "duration_ms": elapsed_ms
            }


class ParallelSandboxRunner:
    """
    High-throughput sandboxed runner designed to maximize multi-core CPU throughput.
    """
    def __init__(self, timeout_seconds: int = 5, max_workers: Optional[int] = None):
        self.timeout = timeout_seconds
        self.max_workers = max_workers or hw_profile.recommended_workers

    def run_single(self, test_code: str, target_code: str) -> Dict[str, Any]:
        """Runs a single test synchronously (e.g. for baseline suite validation)."""
        return _run_single_test_task(test_code, target_code, self.timeout)

    def evaluate_mutants_parallel(
        self,
        test_code: str,
        mutants: List[MutantRecord]
    ) -> List[MutantRecord]:
        """
        Runs the test suite against every mutant concurrently across CPU cores.
        """
        if not mutants:
            return []

        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_mutant = {
                executor.submit(
                    _run_single_test_task,
                    test_code,
                    m.mutated_code_snippet,
                    self.timeout
                ): m for m in mutants
            }

            for future in as_completed(future_to_mutant):
                mutant = future_to_mutant[future]
                try:
                    result = future.result()
                    mutant.stdout = result.get("stdout", "")
                    mutant.stderr = result.get("stderr", "")
                    mutant.execution_time_ms = result.get("duration_ms", 0.0)

                    if result["timed_out"]:
                        mutant.status = "TIMEOUT"
                    elif result["status"] == "FAIL":
                        mutant.status = "KILLED"
                    elif result["status"] == "PASS":
                        mutant.status = "SURVIVED"
                    else:
                        mutant.status = "ERROR"
                except Exception as exc:
                    mutant.status = "ERROR"
                    mutant.stderr = str(exc)

        return mutants

    def measure_coverage(self, test_code: str, target_code: str) -> Tuple[float, str]:
        """
        Executes pytest-cov inside the sandbox and parses coverage percentage.
        """
        with tempfile.TemporaryDirectory(prefix="testforge_cov_") as tmpdir:
            src_file = os.path.join(tmpdir, "target.py")
            test_file = os.path.join(tmpdir, "test_target.py")
            cov_json_path = os.path.join(tmpdir, "cov.json")

            with open(src_file, "w", encoding="utf-8") as f:
                f.write(target_code)

            with open(test_file, "w", encoding="utf-8") as f:
                f.write(test_code)

            cmd = [
                sys.executable, "-m", "pytest",
                f"--cov={tmpdir}",
                f"--cov-report=json:{cov_json_path}",
                test_file,
                "-p", "no:cacheprovider"
            ]

            res = subprocess.run(cmd, cwd=tmpdir, capture_output=True, text=True, timeout=self.timeout)

            if os.path.exists(cov_json_path):
                try:
                    with open(cov_json_path, "r", encoding="utf-8") as jf:
                        data = json.load(jf)
                        percent = data.get("totals", {}).get("percent_covered", 0.0)
                        return float(percent), res.stdout
                except Exception:
                    pass

            return 0.0, res.stderr
