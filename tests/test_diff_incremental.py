"""
tests/test_diff_incremental.py

Automated Test Suite for Diff-Incremental Mutation Testing (Sub-Task 5.2).
"""

import pytest
from starlette.testclient import TestClient

from server import app
from testforge.diff_incremental import (
    DiffIncrementalResult,
    IncrementalHardeningEngine,
    parse_unified_diff_lines,
)

SAMPLE_DIFF = """--- a/samples/discount.py
+++ b/samples/discount.py
@@ -18,5 +18,7 @@ def calculate_discount(price, quantity, is_member):
     if price <= 0:
         return 0.0
+    if quantity > 100:
+        base_discount += 0.20
     if quantity >= 5:
         base_discount += 0.05
"""


def test_parse_unified_diff_lines():
    lines = parse_unified_diff_lines(SAMPLE_DIFF, "samples/discount.py")
    assert lines == [20, 21]

    # Filter for non-matching file
    other_lines = parse_unified_diff_lines(SAMPLE_DIFF, "samples/other.py")
    assert other_lines == []


def test_incremental_hardening_engine_eval():
    with open("samples/discount.py", "r", encoding="utf-8") as f:
        src = f.read()
    with open("qa_artifacts/test_hardened_discount.py", "r", encoding="utf-8") as f:
        tests = f.read()

    engine = IncrementalHardeningEngine("samples/discount.py")
    res = engine.evaluate_incremental_vs_full([18, 19, 20], tests, src)

    assert isinstance(res, DiffIncrementalResult)
    assert res.full_mutants_count > res.incremental_mutants_count
    assert res.mutants_avoided > 0
    assert res.mutant_reduction_pct >= 50.0
    assert res.speedup_factor >= 1.0


def test_diff_analyze_api_endpoint():
    client = TestClient(app)
    resp = client.post("/api/diff/analyze", json={
        "diff_text": SAMPLE_DIFF,
        "target_file": "samples/discount.py"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["changed_lines"] == [20, 21]
    assert data["changed_lines_count"] == 2
