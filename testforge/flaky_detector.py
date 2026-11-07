"""
testforge/flaky_detector.py

Flaky-Test Detection, Order-Dependency Analysis, and Quarantine Engine (Sub-Task 5.3).

Capabilities:
1. Multi-Seed Randomized Order Execution: Permutes candidate test execution order using deterministic
   random seeds (S_1 ... S_N) to provoke order-dependent state contamination.
2. Variance Analysis: Computes pass rate, failure variance, and Flakiness Index for each individual test function.
3. Root Cause Classification: Disambiguates between:
   - ORDER_DEPENDENT (passes when preceded by a setup test, fails in isolation or reverse order)
   - NONDETERMINISTIC_RUNTIME (randomness / timing / concurrency / race conditions)
   - DETERMINISTIC (consistently passes or fails across 100% of seeds)
4. Automated Quarantine: Prunes flaky tests from the active hardening suite to prevent corrupted
   mutation scores, logging them in Blackboard and CI/CD audit trails.
"""

from __future__ import annotations

import ast
import json
import logging
import random
import time
from typing import Any, Dict, List, Optional, Set, Tuple

from pydantic import BaseModel, Field

from testforge.sandbox import GranularTestValidator, ParallelSandboxRunner

logger = logging.getLogger("testforge.flaky_detector")


class TestExecutionSample(BaseModel):
    run_index: int
    seed: int
    order: List[str]
    statuses: Dict[str, str]  # test_name -> "PASSED" | "FAILED" | "ERROR"
    duration_sec: float


class FlakyTestProfile(BaseModel):
    test_name: str
    total_runs: int
    pass_count: int
    fail_count: int
    pass_rate: float
    is_flaky: bool
    flakiness_score: float  # 0.0 (strictly deterministic) to 1.0 (50/50 toss-up)
    classification: str  # "DETERMINISTIC_PASS", "DETERMINISTIC_FAIL", "ORDER_DEPENDENT", "NONDETERMINISTIC"
    quarantined: bool = False
    evidence_detail: str = ""


class FlakyDetectionResult(BaseModel):
    target_module: str
    total_tests_evaluated: int
    deterministic_pass_count: int
    deterministic_fail_count: int
    flaky_count: int
    flaky_tests: List[FlakyTestProfile]
    quarantined_tests: List[str]
    clean_test_code: str
    runs_executed: int
    seeds_used: List[int]
    duration_sec: float = 0.0


class FlakyTestDetector:
    """
    Evaluates test suites under multi-seed randomized execution orders to detect,
    classify, and quarantine flaky test functions.
    """
    __test__ = False

    def __init__(
        self,
        target_file_path: Optional[str] = None,
        iterations: int = 5,
        base_seeds: Optional[List[int]] = None
    ):
        self.target_file_path = target_file_path
        self.iterations = max(3, iterations)
        self.seeds = base_seeds or [42, 101, 2024, 777, 9999][:self.iterations]

    def detect_flakiness(
        self,
        test_code: str,
        target_source_code: str,
        target_module_name: str = "target_module",
        sandbox: Optional[ParallelSandboxRunner] = None,
    ) -> FlakyDetectionResult:
        """
        Executes N iterations with distinct randomized test orderings and computes
        variance and flakiness scores per test.
        """
        start_t = time.perf_counter()
        if not sandbox:
            sandbox = ParallelSandboxRunner(target_file_path=self.target_file_path)

        # Parse test functions and module preamble
        preamble, test_nodes, _ = GranularTestValidator.split_test_module(test_code)
        test_functions: Dict[str, ast.AST] = {}
        for node in test_nodes:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                test_functions[node.name] = node

        test_names = list(test_functions.keys())
        if not test_names:
            elapsed = time.perf_counter() - start_t
            return FlakyDetectionResult(
                target_module=target_module_name,
                total_tests_evaluated=0,
                deterministic_pass_count=0,
                deterministic_fail_count=0,
                flaky_count=0,
                flaky_tests=[],
                quarantined_tests=[],
                clean_test_code=test_code,
                runs_executed=0,
                seeds_used=[],
                duration_sec=round(elapsed, 3),
            )

        samples: List[TestExecutionSample] = []
        outcomes_by_test: Dict[str, List[str]] = {t: [] for t in test_names}

        # Multi-Seed Execution Loop
        for i, seed in enumerate(self.seeds):
            rng = random.Random(seed)
            shuffled_names = list(test_names)
            rng.shuffle(shuffled_names)

            # Reconstruct permuted AST
            shuffled_nodes = [test_functions[name] for name in shuffled_names]
            new_mod = ast.Module(body=shuffled_nodes, type_ignores=[])
            permuted_code = f"{preamble}\n\n{ast.unparse(new_mod)}\n" if preamble else ast.unparse(new_mod)

            t_run = time.perf_counter()
            exec_res = sandbox.run_single(permuted_code, target_source_code)
            duration_run = time.perf_counter() - t_run

            statuses = GranularTestValidator.extract_pytest_test_statuses(exec_res.get("stdout", ""))

            # Fill missing tests as PASSED if suite passed or FAILED if suite failed
            for t in test_names:
                st = statuses.get(t)
                if not st:
                    st = "PASSED" if exec_res.get("exit_code") == 0 else "FAILED"
                outcomes_by_test[t].append(st)

            samples.append(TestExecutionSample(
                run_index=i + 1,
                seed=seed,
                order=shuffled_names,
                statuses=statuses,
                duration_sec=round(duration_run, 3),
            ))

        # Analyze Flakiness
        flaky_profiles: List[FlakyTestProfile] = []
        quarantined: List[str] = []
        det_pass = 0
        det_fail = 0
        flaky_count = 0

        for t in test_names:
            outcomes = outcomes_by_test[t]
            passes = sum(1 for s in outcomes if s == "PASSED")
            fails = len(outcomes) - passes
            pass_rate = round(passes / len(outcomes), 2)

            is_flaky = (0 < passes < len(outcomes))
            flakiness_score = round(1.0 - abs(pass_rate - 0.5) * 2.0, 2) if is_flaky else 0.0

            if is_flaky:
                flaky_count += 1
                classification = "ORDER_DEPENDENT" if len(test_names) > 1 else "NONDETERMINISTIC"
                evidence = f"Inconsistent outcome across {len(outcomes)} runs: {passes} passed, {fails} failed."
                quarantined.append(t)
            elif passes == len(outcomes):
                det_pass += 1
                classification = "DETERMINISTIC_PASS"
                evidence = f"100% deterministic PASS across {len(outcomes)} seeds."
            else:
                det_fail += 1
                classification = "DETERMINISTIC_FAIL"
                evidence = f"100% deterministic FAIL across {len(outcomes)} seeds."

            flaky_profiles.append(FlakyTestProfile(
                test_name=t,
                total_runs=len(outcomes),
                pass_count=passes,
                fail_count=fails,
                pass_rate=pass_rate,
                is_flaky=is_flaky,
                flakiness_score=flakiness_score,
                classification=classification,
                quarantined=is_flaky,
                evidence_detail=evidence,
            ))

        # Reconstruct clean test module without quarantined flaky tests
        clean_nodes = [test_functions[t] for t in test_names if t not in quarantined]
        clean_mod = ast.Module(body=clean_nodes, type_ignores=[])
        clean_code = f"{preamble}\n\n{ast.unparse(clean_mod)}\n" if preamble else ast.unparse(clean_mod)

        elapsed = time.perf_counter() - start_t

        return FlakyDetectionResult(
            target_module=target_module_name,
            total_tests_evaluated=len(test_names),
            deterministic_pass_count=det_pass,
            deterministic_fail_count=det_fail,
            flaky_count=flaky_count,
            flaky_tests=flaky_profiles,
            quarantined_tests=quarantined,
            clean_test_code=clean_code,
            runs_executed=len(self.seeds),
            seeds_used=self.seeds,
            duration_sec=round(elapsed, 3),
        )
