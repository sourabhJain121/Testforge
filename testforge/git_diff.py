"""
git_diff.py - Git Diff Inspection Engine for Targeted AST Mutation.

Author: Sourabh & Shreshth
Course: CSE3101 - Agentic AI

Features:
  - GitDiffInspector:
      * Inspects git working trees (unstaged, staged, or recent commits)
        using `git diff -U0`.
      * Parses unified diff chunk headers (@@ -l,s +start,count @@) to extract
        exact modified / added line numbers.
      * Enables targeted mutation testing restricted to developer changes.
"""

from __future__ import annotations
import os
import re
import subprocess
from typing import List, Optional, Set


class GitDiffInspector:
    """
    Extracts modified and added line numbers from git diffs for targeted test hardening.
    """

    @staticmethod
    def get_modified_lines(repo_path: str = ".", target_file: Optional[str] = None) -> List[int]:
        """
        Runs `git diff -U0` via subprocess to extract added/modified line numbers
        from unified diff hunks (@@ -l,s +start,count @@).

        Fallback hierarchy:
          1. Unstaged working tree changes: `git diff -U0`
          2. Staged changes: `git diff --cached -U0`
          3. Most recent commit changes: `git diff HEAD~1 -U0` or `git diff HEAD -U0`

        Returns:
          Sorted list of 1-indexed line numbers that were modified or added.
        """
        # If target_file provided, make relative to repo_path if absolute
        rel_target = None
        if target_file:
            if os.path.isabs(target_file):
                try:
                    rel_target = os.path.relpath(target_file, repo_path)
                except ValueError:
                    rel_target = target_file
            else:
                rel_target = target_file

        cmd_base = ["git", "diff", "-U0"]
        target_arg = ["--", rel_target] if rel_target else []

        diff_text = ""
        try:
            # 1. Unstaged diff
            res = subprocess.run(cmd_base + target_arg, cwd=repo_path, capture_output=True, text=True, check=False)
            diff_text = res.stdout.strip()

            # 2. Staged diff if unstaged was empty
            if not diff_text:
                res_cached = subprocess.run(["git", "diff", "--cached", "-U0"] + target_arg, cwd=repo_path, capture_output=True, text=True, check=False)
                diff_text = res_cached.stdout.strip()

            # 3. Recent commit diff if working tree clean
            if not diff_text:
                res_head = subprocess.run(["git", "diff", "HEAD~1", "-U0"] + target_arg, cwd=repo_path, capture_output=True, text=True, check=False)
                if res_head.returncode == 0 and res_head.stdout.strip():
                    diff_text = res_head.stdout.strip()
                else:
                    res_head0 = subprocess.run(["git", "diff", "HEAD", "-U0"] + target_arg, cwd=repo_path, capture_output=True, text=True, check=False)
                    diff_text = res_head0.stdout.strip()
        except Exception:
            return []

        if not diff_text:
            return []

        modified_lines: Set[int] = set()
        # Parse hunks: @@ -old_start,old_count +new_start,new_count @@
        pattern = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@", re.MULTILINE)
        for match in pattern.finditer(diff_text):
            start = int(match.group(1))
            count = int(match.group(2)) if match.group(2) is not None else 1
            if count == 0:
                # Pure deletion in new file, no new line added
                continue
            for line_no in range(start, start + count):
                modified_lines.add(line_no)

        return sorted(list(modified_lines))
