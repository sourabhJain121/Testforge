"""
testforge/diff_incremental.py

Diff-Incremental Mutation and PR-Aware Hardening Engine (Handout Stage 5 / Sub-Task 5.2).

Capabilities:
1. Unified Diff Parsing: Extracts precise line numbers of modified and newly introduced code
   from standard git diff outputs, GitHub PR patches, or unified diff strings.
2. Git Working Tree & PR Integration: Directly queries git diff (against main, HEAD~1, or custom branch).
3. Selective AST Mutation: Conforms mutator to inject faults ONLY into lines touched by the diff,
   reducing mutation matrix dimensions and CI execution latency.
4. Empirical Performance Benchmarking: Quantifies mutants avoided, execution time saved,
   and acceleration factor relative to full-module regression.
"""

from __future__ import annotations

import logging
import os
import re
import subprocess
import time
from typing import Any, Dict, List, Optional, Set, Tuple

from pydantic import BaseModel, Field

from testforge.mutator import ASTMutator
from testforge.sandbox import ParallelSandboxRunner
from testforge.state import MutantRecord

logger = logging.getLogger("testforge.diff_incremental")


def parse_unified_diff_lines(diff_text: str, target_file_name: Optional[str] = None) -> List[int]:
    """
    Parses a unified diff string and returns the 1-based line numbers of added/modified lines
    in the new version of the specified target file (or across all hunks if target_file_name is None).
    """
    changed_lines: Set[int] = set()
    current_file_matches = True if target_file_name is None else False
    current_new_line = 0

    hunk_regex = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")

    for line in diff_text.splitlines():
        # Check file header
        if line.startswith("+++ "):
            path_part = line[4:].strip()
            # strip b/ prefix if present
            if path_part.startswith("b/"):
                path_part = path_part[2:]
            if target_file_name is not None:
                current_file_matches = os.path.basename(path_part) == os.path.basename(target_file_name)
            else:
                current_file_matches = True
            continue

        if not current_file_matches:
            continue

        # Check hunk header
        hunk_match = hunk_regex.match(line)
        if hunk_match:
            current_new_line = int(hunk_match.group(1))
            continue

        if line.startswith("+") and not line.startswith("+++"):
            changed_lines.add(current_new_line)
            current_new_line += 1
        elif line.startswith(" "):
            current_new_line += 1
        elif line.startswith("-") and not line.startswith("---"):
            # Deletions do not advance the new file line counter
            pass

    return sorted(list(changed_lines))


def get_git_diff_lines(
    repo_dir: str = ".",
    base_ref: str = "main",
    target_file_path: Optional[str] = None
) -> List[int]:
    """
    Invokes git diff in repo_dir against base_ref and returns changed line numbers
    for target_file_path.
    """
    cmd = ["git", "diff", f"{base_ref}...HEAD"]
    if target_file_path:
        cmd.extend(["--", target_file_path])

    try:
        proc = subprocess.run(
            cmd,
            cwd=repo_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10,
        )
        if proc.returncode != 0 or not proc.stdout.strip():
            # Fallback to working directory diff
            proc = subprocess.run(
                ["git", "diff", "HEAD", "--", target_file_path] if target_file_path else ["git", "diff", "HEAD"],
                cwd=repo_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=10,
            )
        return parse_unified_diff_lines(proc.stdout, target_file_path)
    except Exception as exc:
        logger.warning(f"Failed to query git diff ({exc}). Returning empty changed lines.")
        return []


class DiffIncrementalResult(BaseModel):
    target_file: str
    diff_lines: List[int]
    full_mutants_count: int
    incremental_mutants_count: int
    mutants_avoided: int
    mutant_reduction_pct: float
    full_duration_sec: float
    incremental_duration_sec: float
    time_saved_sec: float
    speedup_factor: float
    incremental_killed_mutants: int
    incremental_mutation_score: float
    all_diff_mutants_killed: bool


class IncrementalHardeningEngine:
    """
    Orchestrates diff-incremental mutation testing against modified lines.
    """

    def __init__(self, target_file_path: str):
        self.target_file_path = target_file_path

    def evaluate_incremental_vs_full(
        self,
        diff_lines: List[int],
        test_code: str,
        target_source_code: str,
    ) -> DiffIncrementalResult:
        """
        Runs both full and diff-incremental mutation evaluations and computes
        exact empirical metrics comparing time saved and speedup factor.
        """
        sandbox = ParallelSandboxRunner(target_file_path=self.target_file_path)
        mutator = ASTMutator()

        # 1. Full Mutation
        t0_full = time.perf_counter()
        full_mutants = mutator.mutate(target_source_code)
        full_eval = sandbox.evaluate_mutants_parallel(test_code, full_mutants, target_source_code)
        full_duration = time.perf_counter() - t0_full

        # 2. Incremental Mutation (only diff_lines)
        t0_inc = time.perf_counter()
        inc_mutants = mutator.mutate(target_source_code, target_lines=diff_lines)
        inc_eval = sandbox.evaluate_mutants_parallel(test_code, inc_mutants, target_source_code)
        inc_duration = time.perf_counter() - t0_inc

        full_count = len(full_mutants)
        inc_count = len(inc_mutants)
        avoided = full_count - inc_count
        reduction_pct = round((avoided / full_count) * 100.0, 1) if full_count > 0 else 0.0

        inc_killed = sum(1 for m in inc_eval if m.status in ("KILLED", "TIMEOUT"))
        inc_ms = round((inc_killed / inc_count) * 100.0, 1) if inc_count > 0 else 100.0

        time_saved = max(0.0, full_duration - inc_duration)
        speedup = round(full_duration / inc_duration, 2) if inc_duration > 0.01 else 1.0

        return DiffIncrementalResult(
            target_file=os.path.basename(self.target_file_path),
            diff_lines=diff_lines,
            full_mutants_count=full_count,
            incremental_mutants_count=inc_count,
            mutants_avoided=avoided,
            mutant_reduction_pct=reduction_pct,
            full_duration_sec=round(full_duration, 3),
            incremental_duration_sec=round(inc_duration, 3),
            time_saved_sec=round(time_saved, 3),
            speedup_factor=speedup,
            incremental_killed_mutants=inc_killed,
            incremental_mutation_score=inc_ms,
            all_diff_mutants_killed=(inc_killed == inc_count),
        )
