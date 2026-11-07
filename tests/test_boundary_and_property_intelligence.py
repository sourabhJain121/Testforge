"""
tests/test_boundary_and_property_intelligence.py - Automated Suite for Boundary-Value and Property-Based Test Synthesis.

Verifies:
  1. Synthesis of extreme boundary partition tests (zero, negative, empty collection, large positive).
  2. Synthesis of property-based invariant tests (idempotence, range bounds, monotonicity).
  3. Clean execution (pass@1) of synthesized boundary & property tests in the sandbox.
  4. Behavior on diverse function types (numeric functions, idempotent string normalizers, monotonic scalers).
"""

import pytest

from testforge.intelligent_generator import IntelligentASTSynthesizer
from testforge.sandbox import ParallelSandboxRunner


class TestBoundaryAndPropertyIntelligence:
    """Verifies that the test intelligence engine produces valid boundary and property tests."""

    def test_synthesizes_extreme_boundaries_for_numeric_target(self):
        source_code = """
def calculate_fee(amount: float, is_vip: bool = False) -> float:
    if amount < 0:
        raise ValueError("Amount cannot be negative")
    if amount == 0:
        return 0.0
    fee = amount * 0.05
    if is_vip:
        fee *= 0.5
    return round(fee, 2)
"""
        synth = IntelligentASTSynthesizer()
        res = synth.synthesize_test_suite(source_code)

        assert res.total_test_count > 0
        assert res.boundary_tests_count > 0
        assert res.negative_tests_count > 0

        # Verify generated test code contains zero and negative boundary tests
        test_code = res.test_code
        assert "extreme" in test_code
        assert "zero" in test_code or "negative" in test_code

        # Verify synthesized suite passes cleanly in the sandbox
        runner = ParallelSandboxRunner(timeout_seconds=5)
        exec_res = runner.run_single(test_code, source_code)
        assert exec_res["status"] == "PASS", f"Synthesized tests failed: {exec_res.get('stderr')}"
        assert exec_res["tests_passed"] >= 3

    def test_synthesizes_idempotent_property_test(self):
        source_code = """
def clean_identifier(text: str) -> str:
    cleaned = text.strip().lower().replace(" ", "_")
    return cleaned
"""
        synth = IntelligentASTSynthesizer()
        res = synth.synthesize_test_suite(source_code)

        test_code = res.test_code
        assert "property_idempotent" in test_code
        assert res.property_tests_count >= 1

        # Verify property test passes in sandbox
        runner = ParallelSandboxRunner(timeout_seconds=5)
        exec_res = runner.run_single(test_code, source_code)
        assert exec_res["status"] == "PASS", f"Synthesized tests failed: {exec_res.get('stderr')}"

    def test_synthesizes_monotonicity_property_test(self):
        source_code = """
def compute_premium(risk_score: int) -> int:
    if risk_score <= 10:
        return 100
    elif risk_score <= 50:
        return 250
    else:
        return 500
"""
        synth = IntelligentASTSynthesizer()
        res = synth.synthesize_test_suite(source_code)

        test_code = res.test_code
        assert "property_monotonicity" in test_code or "threshold" in test_code
        assert res.meaningful_assertions_count >= 3

        # Verify passes in sandbox
        runner = ParallelSandboxRunner(timeout_seconds=5)
        exec_res = runner.run_single(test_code, source_code)
        assert exec_res["status"] == "PASS", f"Synthesized tests failed: {exec_res.get('stderr')}"

    def test_synthesizes_non_negative_range_property_test(self):
        source_code = """
def apply_rate(val: float) -> float:
    return max(0.0, float(val) * 1.15)
"""
        synth = IntelligentASTSynthesizer()
        res = synth.synthesize_test_suite(source_code)

        test_code = res.test_code
        assert "property_non_negative_range" in test_code or "nominal" in test_code

        runner = ParallelSandboxRunner(timeout_seconds=5)
        exec_res = runner.run_single(test_code, source_code)
        assert exec_res["status"] == "PASS", f"Synthesized tests failed: {exec_res.get('stderr')}"

