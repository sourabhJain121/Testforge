"""
run_demo.py - TestForge End-to-End Benchmark & Demonstration.

Course: CSE3101 - Agentic AI
Authors: Sourabh & Shreshth
"""

import os
import sys
from testforge.orchestrator import TestForgeOrchestrator
from testforge.logger import TraceLogger

def run():
    target_file = os.path.join("samples", "banking.py")
    with open(target_file, "r") as f:
        code = f.read()

    # Initial weak test suite (leaves boundary mutants alive)
    weak_tests = """
from target import banking_transaction

def test_nominal_pass():
    assert banking_transaction(100.0, 50.0, 5.0) is True

def test_negative_balance():
    assert banking_transaction(-10.0, 50.0, 5.0) is False
"""

    orchestrator = TestForgeOrchestrator(
        target_source_code=code,
        initial_test_code=weak_tests,
        max_iterations=3,
        target_mutation_score=85.0
    )

    final_state = orchestrator.run()

    print("\n==========================================================")
    print("                    FINAL BENCHMARK AUDIT                 ")
    print("==========================================================")
    for m in final_state.history:
        print(f"Iteration {m.iteration}: Total: {m.total_mutants} | Killed: {m.killed_mutants} | Survived: {m.survived_mutants} | Score: {m.mutation_score}% | Duration: {m.duration_seconds}s")
    
    print(f"\nFinal Test Hardening Status: {'ACHIEVED' if final_state.terminated else 'IN_PROGRESS'}")
    print(f"Reason: {final_state.termination_reason}")
    print(f"Trace log saved to: testforge_trace.jsonl")

    # Output trace file inspection
    logger = TraceLogger()
    traces = logger.read_traces()
    print(f"Recorded {len(traces)} structured telemetry events for academic viva review.")

if __name__ == "__main__":
    run()
