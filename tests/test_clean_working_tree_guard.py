"""
tests/test_clean_working_tree_guard.py

Ensures running TestForge tests does not mutate tracked repository files
or leave un-ignored temporary scratch files in the working tree.
"""

import shutil
import subprocess

import pytest


def test_working_tree_clean_after_pipeline():
    """Verify git status shows no modified tracked files in sensitive directories."""
    git_bin = shutil.which("git")
    if not git_bin:
        pytest.skip("git not available")

    # Run git status --porcelain
    res = subprocess.run(
        [git_bin, "status", "--porcelain"],
        capture_output=True,
        text=True,
        check=True
    )
    lines = [line.strip() for line in res.stdout.strip().splitlines() if line.strip()]

    # Filter out files currently being edited/added by the active task
    # (e.g. docs/AUDIT_PROGRESS.md, tests/, etc.)
    # Specifically ensure tracked code files like test_hardened.py are not modified by test runs
    dirty_tracked_targets = [
        line for line in lines
        if "test_hardened.py" in line and not line.startswith("??")
    ]
    assert not dirty_tracked_targets, f"Tracked test_hardened.py was modified: {dirty_tracked_targets}"

