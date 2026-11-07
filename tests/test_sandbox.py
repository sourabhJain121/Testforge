"""
Unit tests verifying the Parallel Sandbox Runtime, process isolation, and timeout guardrails.

Author: Shreshth
"""

import pytest

from testforge.mutator import ASTMutator
from testforge.sandbox import ParallelSandboxRunner


def test_sandbox_clean_run():
    sandbox = ParallelSandboxRunner(timeout_seconds=3)
    target = "def add(a, b): return a + b\n"
    test_code = "from target import add\ndef test_add(): assert add(2, 3) == 5\n"
    
    res = sandbox.run_single(test_code, target)
    assert res["status"] == "PASS"
    assert res["exit_code"] == 0

def test_sandbox_timeout_guardrail():
    # Injected infinite loop simulating bad mutant
    sandbox = ParallelSandboxRunner(timeout_seconds=2)
    target = "def infinite_loop():\n    while True:\n        pass\n"
    test_code = "from target import infinite_loop\ndef test_inf(): infinite_loop()\n"

    res = sandbox.run_single(test_code, target)
    assert res["timed_out"] is True
    assert res["status"] == "TIMEOUT"

def test_parallel_mutant_evaluation():
    sandbox = ParallelSandboxRunner(timeout_seconds=3, max_workers=2)
    target = "def calc(x): return x * 2\n"
    test_code = "from target import calc\ndef test_calc(): assert calc(3) == 6\n"

    mutants = ASTMutator.generate_mutants(target)
    evaluated = sandbox.evaluate_mutants_parallel(test_code, mutants)
    assert len(evaluated) > 0
    assert all(m.status in ("KILLED", "SURVIVED", "TIMEOUT", "ERROR") for m in evaluated)
