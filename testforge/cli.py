"""
cli.py - TestForge Command Line Interface with Clean Standalone Export.

Authors: Sourabh & Shreshth
Course: CSE3101 - Agentic AI
"""

import os
import sys
import argparse
from testforge.orchestrator import TestForgeOrchestrator


def main():
    parser = argparse.ArgumentParser(description="TestForge: Autonomous Test Hardening System")
    parser.add_argument("--target", "-t", default="samples/banking.py", help="Path to Python target source file")
    parser.add_argument("--tests", "-s", default=None, help="Path to initial test file (optional)")
    parser.add_argument("--max-iter", "-i", type=int, default=3, help="Maximum reflection iterations")
    parser.add_argument("--target-score", "-score", type=float, default=85.0, help="Target mutation score (pct)")
    parser.add_argument("--model", "-m", default="gemini-3.6-flash", help="LLM foundation model name")
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
        target_mutation_score=args.target_score,
        model_name=args.model,
        target_file_path=args.target
    )

    final_state = orchestrator.run()

    # Export using orchestrator export method which guarantees standalone execution
    orchestrator.export_hardened_suite(output_path=args.output)

    print(f"\n[TestForge] Exported standalone hardened tests to: {args.output}")
    print(f"[TestForge] Run anytime using: pytest {args.output} -v")


if __name__ == "__main__":
    main()
