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
import re
import tempfile
import subprocess
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Dict, Any, Tuple, List, Optional
from testforge.accel import hw_profile
from testforge.state import MutantRecord
from testforge.equivalence import EquivalentMutantAnalyzer, EquivalenceClassification


def parse_pytest_output(stdout: str, stderr: str, exit_code: int) -> Dict[str, Any]:
    """
    Parses pytest console output to distinguish real test assertion failures from
    infrastructure/import/syntax errors.
    """
    collected_m = re.search(r"collected\s+(\d+)\s+item", stdout)
    collected = int(collected_m.group(1)) if collected_m else 0

    passed_m = re.search(r"(\d+)\s+passed", stdout)
    passed = int(passed_m.group(1)) if passed_m else 0

    failed_m = re.search(r"(\d+)\s+failed", stdout)
    failed = int(failed_m.group(1)) if failed_m else 0

    errors_m = re.search(r"(\d+)\s+error", stdout)
    errors = int(errors_m.group(1)) if errors_m else 0

    # Distinguish execution/infrastructure errors (ImportError, ModuleNotFoundError, SyntaxError, collection error)
    combined = f"{stdout}\n{stderr}"
    has_exec_error = (
        (exit_code != 0 and collected == 0)
        or "ImportError" in combined
        or "ModuleNotFoundError" in combined
        or "SyntaxError" in combined
        or "IndentationError" in combined
        or exit_code in (2, 3, 4)
    )

    if exit_code == 0 and passed > 0:
        status = "PASS"
    elif exit_code == 1 and failed > 0 and not has_exec_error:
        status = "FAIL"
    elif exit_code == -1:
        status = "TIMEOUT"
    else:
        status = "ERROR"

    return {
        "collected": collected,
        "passed": passed,
        "failed": failed,
        "errors": errors,
        "status": status,
        "has_exec_error": has_exec_error
    }


def _run_single_test_task(test_code: str, target_code: str, timeout_seconds: int, enforce_security: bool = True) -> Dict[str, Any]:
    """
    Isolated worker function designed for ProcessPoolExecutor execution.
    Inspects test code against AST security policies before executing pytest in a sandbox directory.
    """
    start_time = time.perf_counter()

    if enforce_security:
        from testforge.security import SecurityGuardrail
        sec_res = SecurityGuardrail().inspect_code_ast(test_code, enforce_policy=True)
        if not sec_res.allowed:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            violation_summary = "; ".join(f"[{v.rule_id}] {v.message}" for v in sec_res.violations)
            return {
                "exit_code": -3,
                "stdout": "",
                "stderr": f"Security Guardrail Blocked: {violation_summary}",
                "status": "SECURITY_BLOCKED",
                "timed_out": False,
                "duration_ms": elapsed_ms,
                "tests_collected": 0,
                "tests_passed": 0,
                "tests_failed": 0,
                "tests_errors": 1,
                "has_exec_error": True
            }

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
            parsed = parse_pytest_output(res.stdout, res.stderr, res.returncode)
            return {
                "exit_code": res.returncode,
                "stdout": res.stdout,
                "stderr": res.stderr,
                "status": parsed["status"],
                "timed_out": False,
                "duration_ms": elapsed_ms,
                "tests_collected": parsed["collected"],
                "tests_passed": parsed["passed"],
                "tests_failed": parsed["failed"],
                "tests_errors": parsed["errors"],
                "has_exec_error": parsed["has_exec_error"]
            }
        except subprocess.TimeoutExpired:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return {
                "exit_code": -1,
                "stdout": "",
                "stderr": f"Subprocess timed out after {timeout_seconds}s (Safety Guardrail: Infinite loop caught)",
                "status": "TIMEOUT",
                "timed_out": True,
                "duration_ms": elapsed_ms,
                "tests_collected": 0,
                "tests_passed": 0,
                "tests_failed": 0,
                "tests_errors": 1,
                "has_exec_error": False
            }
        except Exception as exc:
            elapsed_ms = (time.perf_counter() - start_time) * 1000.0
            return {
                "exit_code": -2,
                "stdout": "",
                "stderr": str(exc),
                "status": "ERROR",
                "timed_out": False,
                "duration_ms": elapsed_ms,
                "tests_collected": 0,
                "tests_passed": 0,
                "tests_failed": 0,
                "tests_errors": 1,
                "has_exec_error": True
            }


class ParallelSandboxRunner:
    """
    High-throughput sandboxed runner designed to maximize multi-core CPU throughput.
    """
    def __init__(self, timeout_seconds: int = 5, max_workers: Optional[int] = None, cancel_event: Optional[Any] = None):
        self.timeout = timeout_seconds
        self.max_workers = max_workers or hw_profile.recommended_workers
        self.cancel_event = cancel_event

    def run_single(self, test_code: str, target_code: str) -> Dict[str, Any]:
        """Runs a single test synchronously (e.g. for baseline suite validation)."""
        if self.cancel_event and self.cancel_event.is_set():
            return {
                "exit_code": -4,
                "stdout": "",
                "stderr": "Execution cancelled before single test execution",
                "status": "CANCELLED",
                "cancelled": True,
                "timed_out": False,
                "duration_ms": 0.0,
                "tests_collected": 0,
                "tests_passed": 0,
                "tests_failed": 0,
                "tests_errors": 0,
                "has_exec_error": True
            }
        return _run_single_test_task(test_code, target_code, self.timeout)

    def evaluate_mutants_parallel(
        self,
        test_code: str,
        mutants: List[MutantRecord],
        baseline_passed: bool = True
    ) -> List[MutantRecord]:
        """
        Runs the test suite against every mutant concurrently across CPU cores.
        Strict mutation testing contract: A mutant is ONLY marked KILLED if:
        1. Baseline clean tests passed
        2. Test suite actually executed against the mutant and failed an assertion or timed out.
        """
        if not mutants:
            return []

        if self.cancel_event and self.cancel_event.is_set():
            return mutants

        executable_mutants: List[MutantRecord] = []
        for m in mutants:
            if not m.is_valid_syntax or m.status == "INVALID":
                m.status = "INVALID"
                m.is_executed = False
                m.equivalence_status = "NOT_EQUIVALENT"
                m.equivalence_method = "NONE"
                m.equivalence_confidence = "HIGH"
                m.equivalence_reason = "Mutant rejected prior to execution: invalid Python AST syntax."
            else:
                executable_mutants.append(m)

        if not executable_mutants:
            return mutants

        with ProcessPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_mutant = {
                executor.submit(
                    _run_single_test_task,
                    test_code,
                    m.mutated_code_snippet,
                    self.timeout
                ): m for m in executable_mutants
            }

            for future in as_completed(future_to_mutant):
                if self.cancel_event and self.cancel_event.is_set():
                    # Stop processing and cancel any remaining futures
                    for f in future_to_mutant:
                        if not f.done():
                            f.cancel()
                    break
                mutant = future_to_mutant[future]
                try:
                    result = future.result()
                    mutant.is_executed = True
                    mutant.stdout = result.get("stdout", "")
                    mutant.stderr = result.get("stderr", "")
                    mutant.execution_time_ms = result.get("duration_ms", 0.0)

                    if not baseline_passed:
                        # Baseline didn't pass, cannot verify mutant kill
                        mutant.status = "ERROR"
                        mutant.equivalence_status = "UNKNOWN"
                        mutant.equivalence_reason = "Baseline test suite failed; cannot evaluate mutant."
                    elif result.get("timed_out"):
                        mutant.status = "TIMEOUT"
                        mutant.equivalence_status = "NOT_EQUIVALENT"
                        mutant.equivalence_confidence = "HIGH"
                        mutant.equivalence_reason = "Execution timed out in sandbox (infinite loop or hang)."
                    elif result.get("has_exec_error") or result.get("status") == "ERROR":
                        # Infrastructure/import/syntax failure is NOT a kill
                        mutant.status = "ERROR"
                        mutant.equivalence_status = "NOT_EQUIVALENT"
                        mutant.equivalence_confidence = "HIGH"
                        mutant.equivalence_reason = "Subprocess suffered execution or environment error."
                    elif result.get("status") == "FAIL" and result.get("tests_failed", 0) > 0:
                        mutant.status = "KILLED"
                        mutant.equivalence_status = "NOT_EQUIVALENT"
                        mutant.equivalence_confidence = "HIGH"
                        mutant.equivalence_reason = "Detected and killed by failing test assertion."
                    elif result.get("status") == "PASS":
                        # Mutant survived test suite; run conservative equivalent-mutant analysis
                        eq_res = EquivalentMutantAnalyzer.analyze_mutant(mutant)
                        if eq_res.status == EquivalenceClassification.EQUIVALENT:
                            mutant.status = "EQUIVALENT"
                            mutant.equivalence_status = eq_res.status.value
                            mutant.equivalence_method = eq_res.method.value
                            mutant.equivalence_reason = eq_res.reason
                            mutant.equivalence_confidence = eq_res.confidence.value
                        elif eq_res.status == EquivalenceClassification.POTENTIALLY_EQUIVALENT:
                            mutant.status = "POTENTIALLY_EQUIVALENT"
                            mutant.equivalence_status = eq_res.status.value
                            mutant.equivalence_method = eq_res.method.value
                            mutant.equivalence_reason = eq_res.reason
                            mutant.equivalence_confidence = eq_res.confidence.value
                        else:
                            mutant.status = "SURVIVED"
                            mutant.equivalence_status = "UNKNOWN"
                            mutant.equivalence_method = "NONE"
                            mutant.equivalence_reason = eq_res.reason
                            mutant.equivalence_confidence = "NONE"
                    else:
                        mutant.status = "ERROR"
                except Exception as exc:
                    mutant.status = "ERROR"
                    mutant.stderr = str(exc)

        return mutants

    def measure_coverage(self, test_code: str, target_code: str) -> Tuple[float, Dict[str, Any]]:
        """
        Executes pytest-cov inside the sandbox and parses coverage percentage and statement counts.
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
                "--cov=target",
                f"--cov-report=json:{cov_json_path}",
                test_file,
                "-p", "no:cacheprovider"
            ]

            res = subprocess.run(cmd, cwd=tmpdir, capture_output=True, text=True, timeout=self.timeout)

            cov_info = {
                "percent_covered": 0.0,
                "covered_lines": 0,
                "num_statements": 0,
                "missing_lines": 0,
                "raw_output": res.stdout or res.stderr
            }

            if os.path.exists(cov_json_path):
                try:
                    with open(cov_json_path, "r", encoding="utf-8") as jf:
                        data = json.load(jf)
                        totals = data.get("totals", {})
                        pct = float(totals.get("percent_covered", 0.0))
                        cov_info["percent_covered"] = pct
                        cov_info["covered_lines"] = int(totals.get("covered_lines", 0))
                        cov_info["num_statements"] = int(totals.get("num_statements", 0))
                        cov_info["missing_lines"] = int(totals.get("missing_lines", 0))
                        return pct, cov_info
                except Exception:
                    pass

            return 0.0, cov_info


# Alias for ADK and single-process usage
SubprocessSandbox = ParallelSandboxRunner
