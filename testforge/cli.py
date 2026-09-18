"""
cli.py - TestForge Command Line Interface.

Authors: Sourabh & Shreshth
"""

import sys
import argparse
from testforge.orchestrator import TestForgeOrchestrator

def main():
    parser = argparse.ArgumentParser(description="TestForge: Autonomous Test Hardening System")
    parser.add_argument("--target", "-t", required=True, help="Path to Python target source file")
    parser.add_argument("--tests", "-s", default=None, help="Path to initial test file (optional)")
    parser.add_argument("--max-iter", "-i", type=int, default=3, help="Maximum reflection iterations")
    parser.add_argument("--target-score", "-score", type=float, default=85.0, help="Target mutation score (pct)")
    parser.add_argument("--output", "-o", default="test_hardened.py", help="Output file for hardened tests")
    args = parser.parse_args()

    with open(args.target, "r", encoding="utf-8") as f:
        target_code = f.read()

    initial_tests = None
    if args.tests:
        with open(args.tests, "r", encoding="utf-8") as f:
            initial_tests = f.read()

    orchestrator = TestForgeOrchestrator(
        target_source_code=target_code,
        initial_test_code=initial_tests,
        max_iterations=args.max_iter,
        target_mutation_score=args.target_score
    )

    final_state = orchestrator.run()

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(final_state.current_test_code)

    print(f"\n[TestForge] Hardened test suite exported to: {args.output}")

if __name__ == "__main__":
    main()
