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
import ast
import tempfile
import subprocess
from dataclasses import dataclass, field
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Dict, Any, Tuple, List, Optional, Set
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

        # Strict evaluation contract: If baseline tests failed on clean reference code,
        # mutants CANNOT be evaluated or killed.
        if not baseline_passed:
            for m in executable_mutants:
                m.status = "ERROR"
                m.is_executed = False
                m.equivalence_status = "UNKNOWN"
                m.equivalence_method = "NONE"
                m.equivalence_confidence = "NONE"
                m.equivalence_reason = "Baseline clean test suite failed; cannot evaluate or kill mutants."
            return mutants

        # If no test code is provided, mutants survive by default
        if not test_code or not test_code.strip():
            for m in executable_mutants:
                m.status = "SURVIVED"
                m.is_executed = False
                m.equivalence_status = "UNKNOWN"
                m.equivalence_method = "NONE"
                m.equivalence_confidence = "NONE"
                m.equivalence_reason = "No test assertions provided; mutant survives by default."
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

    def validate_and_filter_candidate_suite(
        self,
        candidate_test_code: str,
        target_code: str,
        existing_test_code: Optional[str] = None,
        surviving_mutants: Optional[List[Any]] = None
    ) -> CandidateSuiteValidationResult:
        """
        Validates candidate test functions individually against clean target code so that
        one broken test does not force the entire candidate suite to be discarded.
        """
        validator = GranularTestValidator()
        return validator.validate_candidate_suite(
            candidate_test_code=candidate_test_code,
            target_code=target_code,
            sandbox_runner=self,
            timeout_seconds=self.timeout,
            existing_test_code=existing_test_code,
            surviving_mutants=surviving_mutants
        )


class TestValidationStatus:
    VALID = "VALID"
    FAILING = "FAILING"
    SYNTAX_ERROR = "SYNTAX_ERROR"
    TIMEOUT = "TIMEOUT"
    INFRASTRUCTURE_ERROR = "INFRASTRUCTURE_ERROR"
    TRIVIAL_NO_ASSERTIONS = "TRIVIAL_NO_ASSERTIONS"
    REQUIRES_SUITE_CONTEXT = "REQUIRES_SUITE_CONTEXT"


@dataclass
class TestFunctionRecord:
    name: str
    code: str
    status: str
    reason: str = ""
    has_meaningful_assertions: bool = True
    duration_ms: float = 0.0
    is_async: bool = False
    decorators: List[str] = field(default_factory=list)
    mutants_killed: List[str] = field(default_factory=list)


@dataclass
class CandidateSuiteValidationResult:
    overall_status: str
    total_candidates: int
    valid_tests: List[TestFunctionRecord] = field(default_factory=list)
    failing_tests: List[TestFunctionRecord] = field(default_factory=list)
    inconclusive_tests: List[TestFunctionRecord] = field(default_factory=list)
    trivial_tests: List[TestFunctionRecord] = field(default_factory=list)
    retained_test_code: str = ""
    retained_count: int = 0
    rejected_count: int = 0
    quarantined_count: int = 0
    error_message: Optional[str] = None
    summary: str = ""
    mutants_killed: List[str] = field(default_factory=list)


class GranularTestValidator:
    """
    AST-aware granular validator that inspects, extracts, and validates candidate
    test functions individually against unchanged original code so that one broken
    test does not force the entire candidate suite to be discarded.
    """

    @staticmethod
    def is_meaningful_assertion(node: ast.AST) -> bool:
        if isinstance(node, ast.Assert):
            test = node.test
            # Constant booleans / literals are trivial (e.g. assert True, assert 1, assert "ok")
            if isinstance(test, ast.Constant):
                return False
            # Negated constants (e.g. assert not False)
            if isinstance(test, ast.UnaryOp) and isinstance(test.op, ast.Not):
                if isinstance(test.operand, ast.Constant):
                    return False
            return True
        return False

    @classmethod
    def has_meaningful_assertions(
        cls,
        func_node: ast.AST,
        helper_defs: Optional[Dict[str, ast.AST]] = None,
        visited_helpers: Optional[Set[str]] = None
    ) -> bool:
        """
        Validates that a test function contains substantive assertions, exception
        checks (pytest.raises / warns / self.assert*), or delegates verification to a
        custom assertion helper (e.g. assert_valid_order, verify_account).
        Preserves rejection of trivial tests and calls to ordinary non-assertion helpers.
        """
        if visited_helpers is None:
            visited_helpers = set()

        for n in ast.walk(func_node):
            if cls.is_meaningful_assertion(n):
                return True
            # Exception / warning checks via context manager: with pytest.raises(...):
            if isinstance(n, ast.With):
                for item in n.items:
                    ctx = item.context_expr
                    if isinstance(ctx, ast.Call):
                        func = ctx.func
                        if isinstance(func, ast.Attribute) and func.attr in ("raises", "warns"):
                            return True
                        elif isinstance(func, ast.Name) and func.id in ("raises", "warns"):
                            return True
            # unittest-style or object assertions: self.assertEqual, tester.assert_valid, etc.
            if isinstance(n, ast.Call):
                func = n.func
                if isinstance(func, ast.Attribute) and func.attr.startswith(("assert", "verify")):
                    return True
                # Standalone custom assertion helpers (addresses M-01)
                if isinstance(func, ast.Name):
                    fn_name = func.id
                    if fn_name.startswith(("assert_", "verify_")) or fn_name == "assert_never":
                        return True
                    # If helper is defined in module context, inspect helper body for assertions
                    if helper_defs and fn_name in helper_defs and fn_name not in visited_helpers:
                        visited_helpers.add(fn_name)
                        if cls.has_meaningful_assertions(
                            helper_defs[fn_name],
                            helper_defs=helper_defs,
                            visited_helpers=visited_helpers
                        ):
                            return True
        return False

    @staticmethod
    def split_test_module(test_code: str) -> Tuple[str, List[ast.AST], List[str]]:
        """
        Parses test module using AST, separating module context (imports, constants,
        fixtures, helpers, setup) from candidate test functions/classes.
        """
        warnings: List[str] = []
        tree = ast.parse(test_code)
        preamble_nodes: List[ast.AST] = []
        test_nodes: List[ast.AST] = []

        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Detect @pytest.fixture decorators
                is_fixture = any(
                    (isinstance(dec, ast.Name) and dec.id == "fixture") or
                    (isinstance(dec, ast.Attribute) and dec.attr == "fixture") or
                    (isinstance(dec, ast.Call) and isinstance(dec.func, (ast.Name, ast.Attribute)) and
                     getattr(dec.func, "id", getattr(dec.func, "attr", "")) == "fixture")
                    for dec in node.decorator_list
                )
                is_test_name = node.name.startswith("test_") or node.name.endswith("_test")
                if is_test_name and not is_fixture:
                    test_nodes.append(node)
                else:
                    preamble_nodes.append(node)
            elif isinstance(node, ast.ClassDef):
                if node.name.startswith("Test"):
                    test_nodes.append(node)
                else:
                    preamble_nodes.append(node)
            else:
                preamble_nodes.append(node)

        preamble_mod = ast.Module(body=preamble_nodes, type_ignores=[])
        preamble_code = ast.unparse(preamble_mod).strip()
        return preamble_code, test_nodes, warnings

    @staticmethod
    def extract_pytest_test_statuses(stdout: str) -> Dict[str, str]:
        """
        Extracts individual test statuses from pytest console output.
        """
        statuses: Dict[str, str] = {}
        pattern = re.compile(
            r"(?:^|[\r\n])\S*?(?:test_\w+\.py|\w+\.py)::(?:(?P<class>\w+)::)?(?P<test>\w+)(?:\[.*?\])?\s+(?P<status>PASSED|FAILED|ERROR|SKIPPED)"
        )
        for match in pattern.finditer(stdout):
            test_name = match.group("test")
            status = match.group("status")
            if test_name not in statuses or status in ("FAILED", "ERROR"):
                statuses[test_name] = status
        return statuses

    @classmethod
    def merge_test_suites(
        cls,
        existing_test_code: str,
        new_valid_test_code: str,
        target_code: str,
        sandbox_runner: Optional[ParallelSandboxRunner] = None
    ) -> str:
        """
        Safely merges existing accepted test suite with newly validated test functions.
        Ensures existing tests are preserved and merged suite passes against target code.
        """
        if not existing_test_code or not existing_test_code.strip():
            return new_valid_test_code
        if not new_valid_test_code or not new_valid_test_code.strip():
            return existing_test_code

        try:
            exist_tree = ast.parse(existing_test_code)
            cand_tree = ast.parse(new_valid_test_code)
        except Exception:
            return existing_test_code

        exist_tests: Dict[str, ast.AST] = {}
        exist_preamble: List[ast.AST] = []
        for n in exist_tree.body:
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and (
                n.name.startswith("test_") or n.name.endswith("_test") or n.name.startswith("Test")
            ):
                exist_tests[n.name] = n
            else:
                exist_preamble.append(n)

        cand_tests: Dict[str, ast.AST] = {}
        cand_preamble: List[ast.AST] = []
        for n in cand_tree.body:
            if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and (
                n.name.startswith("test_") or n.name.endswith("_test") or n.name.startswith("Test")
            ):
                cand_tests[n.name] = n
            else:
                cand_preamble.append(n)

        # Merge preambles avoiding duplicate imports/constants
        combined_preamble: List[ast.AST] = list(exist_preamble)
        existing_unparsed = {ast.unparse(n).strip() for n in exist_preamble}
        for n in cand_preamble:
            unparsed = ast.unparse(n).strip()
            if unparsed not in existing_unparsed:
                combined_preamble.append(n)
                existing_unparsed.add(unparsed)

        # Merge test functions (candidate tests augment/update existing suite)
        merged_tests = dict(exist_tests)
        for name, node in cand_tests.items():
            merged_tests[name] = node

        final_body = combined_preamble + list(merged_tests.values())
        merged_code = ast.unparse(ast.Module(body=final_body, type_ignores=[]))

        # Validate merged suite if sandbox is available
        if sandbox_runner:
            check = sandbox_runner.run_single(merged_code, target_code)
            if check["status"] == "PASS" and check.get("tests_passed", 0) > 0:
                return merged_code
            else:
                return existing_test_code

        return merged_code

    def validate_candidate_suite(
        self,
        candidate_test_code: str,
        target_code: str,
        sandbox_runner: Optional[ParallelSandboxRunner] = None,
        timeout_seconds: int = 5,
        existing_test_code: Optional[str] = None,
        surviving_mutants: Optional[List[Any]] = None
    ) -> CandidateSuiteValidationResult:
        """
        Executes granular validation on candidate test suite:
        1. Safely parses module via AST.
        2. Separates module context from candidate test functions.
        3. Identifies meaningful assertions and custom assertion helpers.
        4. Evaluates suite & individual tests against unchanged clean target code.
        5. Separates valid tests from failing/timeout/infrastructure errors.
        6. Retains valid tests while quarantining failing candidates.
        7. Optionally re-evaluates retained candidates against surviving mutants.
        """
        if not candidate_test_code or not candidate_test_code.strip():
            return CandidateSuiteValidationResult(
                overall_status="EMPTY_CANDIDATE",
                total_candidates=0,
                retained_test_code=existing_test_code or "",
                summary="Candidate test code was empty. Existing suite retained."
            )

        # 1. AST Syntax Check
        try:
            preamble_code, test_nodes, _ = self.split_test_module(candidate_test_code)
        except SyntaxError as exc:
            return CandidateSuiteValidationResult(
                overall_status=TestValidationStatus.SYNTAX_ERROR,
                total_candidates=0,
                retained_test_code=existing_test_code or "",
                quarantined_count=1,
                error_message=f"SyntaxError at line {exc.lineno}: {exc.msg}",
                summary=f"Candidate suite rejected due to SyntaxError at line {exc.lineno}."
            )
        except Exception as exc:
            return CandidateSuiteValidationResult(
                overall_status=TestValidationStatus.SYNTAX_ERROR,
                total_candidates=0,
                retained_test_code=existing_test_code or "",
                quarantined_count=1,
                error_message=f"AST Parse Error: {str(exc)}",
                summary="Candidate suite rejected due to AST parse error."
            )

        total_candidates = len(test_nodes)
        if total_candidates == 0:
            return CandidateSuiteValidationResult(
                overall_status="NO_TESTS_FOUND",
                total_candidates=0,
                retained_test_code=existing_test_code or "",
                summary="No candidate test functions found in module."
            )

        runner = sandbox_runner or ParallelSandboxRunner(timeout_seconds=timeout_seconds)

        # Extract helper function definitions from preamble and existing suite context
        helper_defs: Dict[str, ast.AST] = {}
        try:
            if preamble_code:
                p_tree = ast.parse(preamble_code)
                for n in p_tree.body:
                    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        helper_defs[n.name] = n
        except Exception:
            pass
        try:
            if existing_test_code:
                e_tree = ast.parse(existing_test_code)
                for n in e_tree.body:
                    if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        if n.name not in helper_defs:
                            helper_defs[n.name] = n
        except Exception:
            pass

        # 2. Fast Path: Run full candidate suite against clean target
        full_run = runner.run_single(candidate_test_code, target_code)

        # Infrastructure / Collection error check (e.g. missing import, module not found)
        if full_run.get("has_exec_error") and full_run.get("tests_collected", 0) == 0:
            inconclusive = [
                TestFunctionRecord(
                    name=getattr(node, "name", "unknown"),
                    code=ast.unparse(node),
                    status=TestValidationStatus.INFRASTRUCTURE_ERROR,
                    reason=full_run.get("stderr") or full_run.get("stdout") or "Collection error in candidate module"
                )
                for node in test_nodes
            ]
            return CandidateSuiteValidationResult(
                overall_status=TestValidationStatus.INFRASTRUCTURE_ERROR,
                total_candidates=total_candidates,
                inconclusive_tests=inconclusive,
                retained_test_code=existing_test_code or "",
                retained_count=0,
                rejected_count=0,
                quarantined_count=total_candidates,
                error_message=full_run.get("stderr") or "Infrastructure error during test collection",
                summary=f"Candidate suite collection failed due to infrastructure error ({full_run.get('stderr', '').strip()[:80]}). Existing suite preserved."
            )

        # Parse per-test results from stdout if available
        suite_statuses = self.extract_pytest_test_statuses(full_run.get("stdout", ""))

        valid_records: List[TestFunctionRecord] = []
        failing_records: List[TestFunctionRecord] = []
        inconclusive_records: List[TestFunctionRecord] = []
        trivial_records: List[TestFunctionRecord] = []
        valid_nodes: List[ast.AST] = []

        # 3. Granular Inspection & Validation of Candidate Tests
        for node in test_nodes:
            test_name = getattr(node, "name", "unknown")
            is_async = isinstance(node, ast.AsyncFunctionDef)
            node_code = ast.unparse(node)
            decorators = [ast.unparse(d) for d in getattr(node, "decorator_list", [])]

            # Assertion quality screening (including custom assertion helper resolution)
            if not self.has_meaningful_assertions(node, helper_defs=helper_defs):
                rec = TestFunctionRecord(
                    name=test_name,
                    code=node_code,
                    status=TestValidationStatus.TRIVIAL_NO_ASSERTIONS,
                    reason="Test contains no substantive assertions or exception checks.",
                    has_meaningful_assertions=False,
                    is_async=is_async,
                    decorators=decorators
                )
                trivial_records.append(rec)
                continue

            # Check if full suite already passed completely
            if full_run["status"] == "PASS" and full_run.get("tests_failed", 0) == 0:
                rec = TestFunctionRecord(
                    name=test_name,
                    code=node_code,
                    status=TestValidationStatus.VALID,
                    reason="Verified in clean candidate suite execution.",
                    has_meaningful_assertions=True,
                    is_async=is_async,
                    decorators=decorators
                )
                valid_records.append(rec)
                valid_nodes.append(node)
                continue

            # Check if this test passed in the full suite run
            if suite_statuses.get(test_name) == "PASSED":
                rec = TestFunctionRecord(
                    name=test_name,
                    code=node_code,
                    status=TestValidationStatus.VALID,
                    reason="Passed in module context during suite run.",
                    has_meaningful_assertions=True,
                    is_async=is_async,
                    decorators=decorators
                )
                valid_records.append(rec)
                valid_nodes.append(node)
                continue

            # Otherwise, evaluate test individually in isolated context
            isolated_module = f"{preamble_code}\n\n{node_code}" if preamble_code else node_code
            iso_res = runner.run_single(isolated_module, target_code)

            if iso_res.get("timed_out"):
                rec = TestFunctionRecord(
                    name=test_name,
                    code=node_code,
                    status=TestValidationStatus.TIMEOUT,
                    reason=f"Isolated execution timed out after {timeout_seconds}s.",
                    has_meaningful_assertions=True,
                    is_async=is_async,
                    decorators=decorators
                )
                inconclusive_records.append(rec)
            elif iso_res.get("has_exec_error") or iso_res.get("status") == "ERROR":
                rec = TestFunctionRecord(
                    name=test_name,
                    code=node_code,
                    status=TestValidationStatus.INFRASTRUCTURE_ERROR,
                    reason=iso_res.get("stderr") or "Execution/import error in isolated test.",
                    has_meaningful_assertions=True,
                    is_async=is_async,
                    decorators=decorators
                )
                inconclusive_records.append(rec)
            elif iso_res.get("status") == "FAIL" and iso_res.get("tests_failed", 0) > 0:
                rec = TestFunctionRecord(
                    name=test_name,
                    code=node_code,
                    status=TestValidationStatus.FAILING,
                    reason=iso_res.get("stderr") or iso_res.get("stdout") or "Failed assertion against clean code.",
                    has_meaningful_assertions=True,
                    is_async=is_async,
                    decorators=decorators
                )
                failing_records.append(rec)
            elif iso_res.get("status") == "PASS" and iso_res.get("tests_passed", 0) > 0:
                rec = TestFunctionRecord(
                    name=test_name,
                    code=node_code,
                    status=TestValidationStatus.VALID,
                    reason="Passed clean target check in isolated execution.",
                    has_meaningful_assertions=True,
                    is_async=is_async,
                    decorators=decorators
                )
                valid_records.append(rec)
                valid_nodes.append(node)
            else:
                rec = TestFunctionRecord(
                    name=test_name,
                    code=node_code,
                    status=TestValidationStatus.FAILING,
                    reason=iso_res.get("stderr") or "Unverified test outcome.",
                    has_meaningful_assertions=True,
                    is_async=is_async,
                    decorators=decorators
                )
                failing_records.append(rec)

        # 4. Reassemble Retained Valid Tests
        retained_code = ""
        if valid_nodes:
            candidate_retained_mod = f"{preamble_code}\n\n" + "\n\n".join(ast.unparse(n) for n in valid_nodes)
            reassemble_check = runner.run_single(candidate_retained_mod, target_code)
            if reassemble_check.get("status") == "PASS" and reassemble_check.get("tests_passed", 0) > 0:
                retained_code = candidate_retained_mod
            else:
                retained_code = existing_test_code or ""

        # Merge with existing suite if existing code is provided
        if existing_test_code and existing_test_code.strip():
            if retained_code:
                merged = self.merge_test_suites(
                    existing_test_code=existing_test_code,
                    new_valid_test_code=retained_code,
                    target_code=target_code,
                    sandbox_runner=runner
                )
                retained_code = merged
            else:
                retained_code = existing_test_code

        # 5. Re-evaluate retained tests against surviving mutants to verify differentiation/killing
        killed_mutant_ids: List[str] = []
        if surviving_mutants and retained_code:
            for m in surviving_mutants:
                mut_code = getattr(m, "mutated_code_snippet", None)
                mut_id = getattr(m, "mutant_id", "unknown")
                if mut_code:
                    mut_run = runner.run_single(retained_code, mut_code)
                    if mut_run.get("status") == "FAIL" or mut_run.get("tests_failed", 0) > 0:
                        killed_mutant_ids.append(mut_id)

        retained_count = len(valid_records)
        quarantined_count = len(failing_records) + len(trivial_records) + len(inconclusive_records)

        if retained_count == total_candidates:
            overall_status = "ALL_VALID"
        elif retained_count > 0:
            overall_status = "PARTIALLY_VALID"
        else:
            overall_status = "ALL_FAILED"

        summary = (
            f"Validated {total_candidates} candidate test(s): {retained_count} valid, "
            f"{len(failing_records)} failing, {len(trivial_records)} trivial, "
            f"{len(inconclusive_records)} inconclusive."
        )
        if killed_mutant_ids:
            summary += f" Distinguished/killed {len(killed_mutant_ids)} surviving mutant(s)."

        return CandidateSuiteValidationResult(
            overall_status=overall_status,
            total_candidates=total_candidates,
            valid_tests=valid_records,
            failing_tests=failing_records,
            inconclusive_tests=inconclusive_records,
            trivial_tests=trivial_records,
            retained_test_code=retained_code,
            retained_count=retained_count,
            rejected_count=len(failing_records),
            quarantined_count=quarantined_count,
            summary=summary,
            mutants_killed=killed_mutant_ids
        )


# Alias for ADK and single-process usage
SubprocessSandbox = ParallelSandboxRunner
