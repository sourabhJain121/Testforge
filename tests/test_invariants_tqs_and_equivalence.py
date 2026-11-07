"""
test_invariants_tqs_and_equivalence.py - Rigorous verification of GAP-002, GAP-005, and GAP-006.

Validates:
1. GAP-002: Property Invariant Soundness & Multi-Sample Confidence Scoring.
2. GAP-005: TQS Scientific Calibration, Transparency & Raw Metric Preservation.
3. GAP-006: Domain-Constrained Boundary Equivalent Mutant Classifier.
"""

from __future__ import annotations
import pytest
from testforge.state import MutantRecord
from testforge.intelligent_generator import IntelligentASTSynthesizer
from testforge.crew_critic import TestQualityAnalyzer
from testforge.equivalence import (
    EquivalentMutantAnalyzer,
    EquivalenceClassification,
    EquivalenceConfidence,
    EquivalenceMethod,
    detect_boundary_equivalent_mutants,
    calculate_mutation_scores,
)
from testforge.a2a import MutationQualityCriticPayload, CriticDirectivePayload
from testforge.sandbox import ParallelSandboxRunner


class TestPropertyInvariantSoundnessGAP002:
    """Verifies GAP-002 Property Invariant Soundness and Confidence Tagging."""
    __test__ = True

    def test_numeric_discount_property_invariants_and_confidence(self):
        source_code = """
def calculate_discount(price: float, quantity: int, is_member: bool) -> float:
    if price <= 0.0:
        return 0.0
    discount_rate = 0.0
    if quantity >= 5:
        discount_rate = discount_rate + 0.10
    if is_member:
        discount_rate = discount_rate + 0.10
    final_price = price * (1.0 - discount_rate)
    return round(final_price, 2)
"""
        synth = IntelligentASTSynthesizer()
        result = synth.synthesize_test_suite(source_code)
        test_code = result.test_code

        # Property test generated
        assert result.property_tests_count >= 1
        assert "property_confidence=" in test_code

        # Run generated suite in sandbox
        runner = ParallelSandboxRunner(timeout_seconds=5)
        exec_res = runner.run_single(test_code, source_code)
        assert exec_res["status"] == "PASS", f"Synthesized suite failed: {exec_res.get('stderr')}"

    def test_idempotent_property_with_high_confidence(self):
        source_code = """
def sanitize_slug(name: str) -> str:
    return name.strip().lower().replace(" ", "-")
"""
        synth = IntelligentASTSynthesizer()
        result = synth.synthesize_test_suite(source_code)
        test_code = result.test_code

        assert "test_sanitize_slug_property_idempotent" in test_code
        assert 'property_confidence="HIGH"' in test_code

        runner = ParallelSandboxRunner(timeout_seconds=5)
        exec_res = runner.run_single(test_code, source_code)
        assert exec_res["status"] == "PASS"

    def test_monotonicity_property_with_high_confidence(self):
        source_code = """
def score_tier(points: int) -> int:
    if points <= 10:
        return 1
    elif points <= 50:
        return 2
    else:
        return 3
"""
        synth = IntelligentASTSynthesizer()
        result = synth.synthesize_test_suite(source_code)
        test_code = result.test_code

        assert "test_score_tier_property_monotonicity" in test_code
        assert 'property_confidence="HIGH"' in test_code

        runner = ParallelSandboxRunner(timeout_seconds=5)
        exec_res = runner.run_single(test_code, source_code)
        assert exec_res["status"] == "PASS"


class TestTQSCalibrationAndTransparencyGAP005:
    """Verifies GAP-005 TQS Scientific Calibration, Weights, and Transparency."""
    __test__ = True

    def test_tqs_weights_and_raw_dimensions(self):
        test_code = """
def test_calc():
    assert 2 + 2 == 4
    assert 3 * 3 == 9
"""
        target_source = """
def calc(x: int) -> int:
    if x > 10:
        return x * 2
    return x
"""
        tqs = TestQualityAnalyzer.calculate_test_quality_score(
            test_code=test_code,
            target_source_code=target_source,
            mutation_score=85.5,
            line_coverage=90.0,
            branch_coverage=80.0,
        )

        # Transparency checks
        assert "composite_tqs" in tqs
        assert "raw_dimensions" in tqs
        assert "weights" in tqs
        assert tqs["weights"]["assertion_density"] == 0.30
        assert tqs["weights"]["mutation_kill_rate"] == 0.30
        assert tqs["weights"]["line_branch_reachability"] == 0.20
        assert tqs["weights"]["boundary_coverage"] == 0.10
        assert tqs["weights"]["test_independence"] == 0.10

        # Raw scores preserved
        assert tqs["raw_mutation_score"] == 85.5
        assert tqs["raw_dimensions"]["mutation_score"] == 85.5
        assert isinstance(tqs["composite_tqs"], float)

        # Alias verification
        alias_tqs = TestQualityAnalyzer.evaluate_test_quality_score(
            test_code=test_code,
            target_source_code=target_source,
            mutation_score=85.5,
            line_coverage=90.0,
        )
        assert alias_tqs["composite_score"] == alias_tqs["composite_tqs"]

    def test_critic_payloads_preserve_transparency_fields(self):
        payload = MutationQualityCriticPayload(
            task_id="job_tqs_001",
            mutation_score=75.0,
            denominator=10,
            killed_mutants=["MUT_1", "MUT_2"],
            survived_mutants=["MUT_3"],
            test_quality_score=82.5,
            composite_tqs=82.5,
            raw_mutation_score=75.0,
            raw_branch_coverage=88.0,
            raw_dimensions={"assertion_score": 90.0, "mutation_score": 75.0},
            tqs_weights={"assertion_density": 0.30, "mutation_kill_rate": 0.30},
        )
        assert payload.composite_tqs == 82.5
        assert payload.raw_mutation_score == 75.0
        assert payload.raw_branch_coverage == 88.0

        # Convert to directive payload
        directive = payload.to_directive_payload()
        assert isinstance(directive, CriticDirectivePayload)
        assert directive.composite_tqs == 82.5
        assert directive.raw_mutation_score == 75.0
        assert directive.raw_branch_coverage == 88.0
        assert "assertion_score" in directive.raw_dimensions


class TestBoundaryEquivalentMutantClassifierGAP006:
    """Verifies GAP-006 Domain-Constrained Boundary Equivalent Mutant Classifier."""
    __test__ = True

    def test_relational_boundary_swap_classified_as_equivalent(self):
        record = MutantRecord(
            mutant_id="MUT_BOUNDARY_SWAP_003",
            mutation_type="BOUNDARY_SWAP",
            line_number=7,
            original_code_snippet="if price <= 0.0:\n    return 0.0",
            mutated_code_snippet="if price < 0.0:\n    return 0.0",
            unified_diff="--- target.py\n+++ mutant\n@@ -7 +7 @@\n- if price <= 0.0:\n+ if price < 0.0:",
            status="SURVIVED",
            is_executed=True,
            is_valid_syntax=True,
            original_expression="price <= 0.0",
            mutated_expression="price < 0.0",
        )
        eq_res = detect_boundary_equivalent_mutants(record)
        assert eq_res is not None
        assert eq_res.status == EquivalenceClassification.EQUIVALENT
        assert eq_res.confidence == EquivalenceConfidence.HIGH
        assert "Boundary perturbation produces mathematically identical return value" in eq_res.reason

        # Integrated analyzer call
        full_res = EquivalentMutantAnalyzer.analyze_mutant(record)
        assert full_res.status == EquivalenceClassification.EQUIVALENT
        assert full_res.confidence == EquivalenceConfidence.HIGH

    def test_integer_domain_boundary_shift_classified_as_equivalent(self):
        record = MutantRecord(
            mutant_id="MUT_INT_BOUND_001",
            mutation_type="RELATIONAL_BOUNDARY",
            line_number=11,
            original_code_snippet="if quantity >= 5:\n    discount = 0.1",
            mutated_code_snippet="if quantity > 4:\n    discount = 0.1",
            unified_diff="--- target.py\n+++ mutant\n@@ -11 +11 @@\n- if quantity >= 5:\n+ if quantity > 4:",
            status="SURVIVED",
            is_executed=True,
            is_valid_syntax=True,
            original_expression="quantity >= 5",
            mutated_expression="quantity > 4",
        )
        eq_res = EquivalentMutantAnalyzer.analyze_mutant(record)
        assert eq_res.status == EquivalenceClassification.EQUIVALENT
        assert eq_res.confidence == EquivalenceConfidence.HIGH
        assert "integer_domain_boundary_shift" in str(eq_res.evidence)

    def test_adjusted_mutation_score_recalculation_with_boundary_equivalent(self):
        mutants = [
            MutantRecord(
                mutant_id="MUT_KILLED_1",
                mutation_type="COMP_OP",
                line_number=5,
                original_code_snippet="a",
                mutated_code_snippet="b",
                unified_diff="",
                status="KILLED",
            ),
            MutantRecord(
                mutant_id="MUT_KILLED_2",
                mutation_type="COMP_OP",
                line_number=6,
                original_code_snippet="a",
                mutated_code_snippet="b",
                unified_diff="",
                status="KILLED",
            ),
            MutantRecord(
                mutant_id="MUT_SURVIVED_1",
                mutation_type="COMP_OP",
                line_number=7,
                original_code_snippet="a",
                mutated_code_snippet="b",
                unified_diff="",
                status="SURVIVED",
            ),
            MutantRecord(
                mutant_id="MUT_EQUIV_1",
                mutation_type="BOUNDARY_SWAP",
                line_number=8,
                original_code_snippet="if price <= 0.0: return 0.0",
                mutated_code_snippet="if price < 0.0: return 0.0",
                unified_diff="",
                status="EQUIVALENT",
                equivalence_status="EQUIVALENT",
            ),
        ]

        scores = calculate_mutation_scores(mutants)
        # Evaluables = 2 killed + 1 survived + 1 equiv = 4
        # Raw score = 2 / 4 * 100 = 50.0%
        # Adjusted score = 2 / (4 - 1) * 100 = 66.67%
        assert scores["raw_mutation_score"] == 50.0
        assert scores["adjusted_mutation_score"] == 66.67
        assert scores["equivalent_mutants"] == 1

