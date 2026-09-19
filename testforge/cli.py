"""
cli.py - TestForge Command Line Interface with Clean Standalone Export.

Authors: Sourabh & Shreshth
Course: CSE3101 - Agentic AI
"""

import os
import sys
import re
import argparse
from testforge.orchestrator import TestForgeOrchestrator


def resolve_import_path(target_path: str) -> str:
    """
    Converts a file path like 'samples/discount.py' or './samples/discount.py'
    into a clean Python module import string like 'samples.discount'.
    """
    normalized = os.path.normpath(target_path)
    if normalized.endswith(".py"):
        normalized = normalized[:-3]
    # Replace path separators with dot notation
    module_import = normalized.replace(os.sep, ".").replace("/", ".")
    # Strip leading dots if any
    module_import = module_import.lstrip(".")
    return module_import


def adapt_tests_for_standalone_export(test_code: str, target_path: str) -> str:
    """
    Replaces internal sandbox references (`from target import *`, `import target`)
    with the actual module path (e.g. `from samples.discount import *`).
    Also ensures the project root directory is added to sys.path if needed.
    """
    module_name = resolve_import_path(target_path)

    # Replace variations of target import
    adapted = re.sub(r"from\s+target\s+import\s+", f"from {module_name} import ", test_code)
    adapted = re.sub(r"import\s+target\s+", f"import {module_name} as target ", adapted)

    # Prefix with sys.path guardrail so pytest executes cleanly from anywhere
    path_guard = (
        "import sys, os\n"
        "sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))\n"
    )

    if "sys.path.insert" not in adapted:
        adapted = path_guard + adapted

    return adapted


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
        model_name=args.model
    )

    final_state = orchestrator.run()

    # Adapt sandbox imports to actual module path for standalone execution
    standalone_test_code = adapt_tests_for_standalone_export(
        final_state.current_test_code,
        args.target
    )

    with open(args.output, "w", encoding="utf-8") as f:
        f.write(standalone_test_code)

    print(f"\n[TestForge] Exported standalone hardened tests to: {args.output}")
    print(f"[TestForge] Run anytime using: pytest {args.output} -v")


if __name__ == "__main__":
    main()
