"""
testforge/scripts/run_tests.py

Optimized Test Runner Profile Script for TestForge.
Supports:
  --profile fast    : Executes unit, security, AST, and contract tests in parallel (~5-10s).
  --profile full    : Executes the entire comprehensive repository test suite with zero omissions.
  --parallel N      : Configures pytest-xdist worker count (defaults to min(4, CPU count)).
  --durations N     : Prints top N slowest test durations.
"""

import argparse
import multiprocessing
import subprocess
import sys


def run_tests() -> int:
    parser = argparse.ArgumentParser(description="TestForge Optimized Test Runner")
    parser.add_argument(
        "--profile",
        choices=["fast", "full"],
        default="fast",
        help="Test profile: 'fast' for rapid unit/contract verification, 'full' for complete suite",
    )
    parser.add_argument(
        "--parallel",
        "-n",
        type=int,
        default=min(4, multiprocessing.cpu_count()),
        help="Number of parallel pytest workers (xdist)",
    )
    parser.add_argument(
        "--durations",
        type=int,
        default=10,
        help="Report top slowest test durations",
    )
    parser.add_argument(
        "extra_args",
        nargs="*",
        help="Additional pytest flags or paths",
    )

    args = parser.parse_args()

    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "-q",
        f"--durations={args.durations}",
    ]

    if args.parallel > 1:
        cmd.extend(["-n", str(args.parallel)])

    if args.profile == "fast":
        # Fast profile selects fast unit, contract, security, mutator, and AST tests
        import glob
        fast_patterns = [
            "tests/test_evaluation_corpus_hardening.py",
            "tests/test_adk_production_path.py",
            "tests/test_benchmark_source_of_truth_sync.py",
            "tests/test_security*.py",
            "tests/test_a2a*.py",
            "tests/test_ast_*.py",
            "tests/test_mutator*.py",
            "tests/test_sandbox_backend.py",
        ]
        resolved = []
        for pat in fast_patterns:
            matches = sorted(glob.glob(pat))
            if matches:
                resolved.extend(matches)
            else:
                resolved.append(pat)
        cmd.extend(resolved)
    else:
        cmd.append("tests/")

    cmd.extend(args.extra_args)

    print(f"[⚡] Running TestForge test profile '{args.profile}' with command:")
    print(f"    {' '.join(cmd)}\n")

    result = subprocess.run(cmd)
    return result.returncode


if __name__ == "__main__":
    sys.exit(run_tests())
