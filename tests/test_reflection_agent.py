"""
tests/test_reflection_agent.py - Unit and Gap Analysis Tests for
ReflectionRepairAgent, TestGapAnalyzer, and TestGapRemediationPlan (GAP-004).
"""

import pytest
from testforge.blackboard import Blackboard
from testforge.reflection_agent import (
    ReflectionRepairAgent,
    TestGapAnalyzer,
    TestGapRemediationPlan,
)
from testforge.mutator import MutantRecord


SAMPLE_TARGET = """
def process_order(price: float, quantity: int, is_express: bool) -> float:
    if price <= 0:
        return 0.0
    discount = 0.0
    if quantity >= 10:
        discount = 0.20
    elif quantity >= 5:
        discount = 0.10
    total = price * quantity * (1.0 - discount)
    if is_express:
        total += 15.0
    return round(total, 2)
"""

INITIAL_TESTS = """
from target import process_order

def test_nominal():
    assert process_order(100.0, 1, False) == 100.0

def test_zero_price():
    assert process_order(0.0, 1, False) == 0.0
"""


class TestBranchGapAnalyzerGAP004:
    """Verifies TestGapAnalyzer correlation of unreached branch arcs with surviving mutants."""

    def test_gap_analyzer_correlates_missing_branches_with_mutants(self):
        """TestGapAnalyzer accurately pinpoints mutants trapped within uncovered branch arcs."""
        # Simulated missing branch arcs from pytest-cov JSON
        # Line 6 is 'if quantity >= 10', Line 8 is 'elif quantity >= 5'
        missing_branches = [
            [6, 7],   # quantity >= 10 body branch missed
            [8, 9],   # quantity >= 5 body branch missed
            [11, 12], # is_express branch missed
        ]

        # Simulated surviving mutants
        surviving_mutants = [
            {"mutant_id": "MUT_QUANT_10", "line_number": 7, "operator": "REPLACEMENT", "diff": "- discount = 0.20\n+ discount = 0.0"},
            {"mutant_id": "MUT_QUANT_5", "line_number": 9, "operator": "REPLACEMENT", "diff": "- discount = 0.10\n+ discount = 0.0"},
            {"mutant_id": "MUT_EXPRESS", "line_number": 12, "operator": "ARITHMETIC_INVERSION", "diff": "- total += 15.0\n+ total -= 15.0"},
            {"mutant_id": "MUT_PRICE", "line_number": 3, "operator": "RETURN_VALUE", "diff": "- return 0.0\n+ return -1.0"},  # Already covered branch
        ]

        plan = TestGapAnalyzer.analyze_gaps(
            missing_branches=missing_branches,
            surviving_mutants=surviving_mutants,
            target_source_code=SAMPLE_TARGET,
        )

        assert isinstance(plan, TestGapRemediationPlan)
        assert plan.total_gaps_identified == 3
        assert len(plan.uncovered_branch_arcs) == 3

        # Mutants at lines 7, 9, 12 should be identified as trapped in gap
        assert "MUT_QUANT_10" in plan.surviving_mutants_in_gap
        assert "MUT_QUANT_5" in plan.surviving_mutants_in_gap
        assert "MUT_EXPRESS" in plan.surviving_mutants_in_gap
        assert "MUT_PRICE" not in plan.surviving_mutants_in_gap

        # Directives should include branch arc guidance
        assert len(plan.synthesized_directives) >= 3
        assert any("6 -> 7" in d for d in plan.synthesized_directives)
        assert any("8 -> 9" in d for d in plan.synthesized_directives)
        assert any("11 -> 12" in d for d in plan.synthesized_directives)
        assert plan.priority_score > 0.0

    def test_gap_analyzer_empty_branches_fallback(self):
        """When no missing branches are reported, fall back gracefully to mutant-targeted directives."""
        surviving = [
            {"mutant_id": "MUT_FALLBACK", "line_number": 10, "operator": "MATH"}
        ]
        plan = TestGapAnalyzer.analyze_gaps(
            missing_branches=[],
            surviving_mutants=surviving,
            target_source_code=SAMPLE_TARGET,
        )
        assert plan.total_gaps_identified == 0
        assert len(plan.synthesized_directives) >= 1
        assert "MUT_FALLBACK" in plan.synthesized_directives[0]

    def test_reflection_repair_agent_generate_repair_patch(self):
        """ReflectionRepairAgent.generate_repair_patch consumes gap analysis to produce targeted candidate suite."""
        bb = Blackboard()
        bb.update_target_space(
            target_source_code=SAMPLE_TARGET,
            target_module_path="samples/order.py"
        )
        bb.record_coverage(
            line_coverage_pct=60.0,
            lines_covered=6,
            lines_total=10,
            branch_coverage=40.0,
            total_branches=6,
            covered_branches=2,
            missing_branches=[[6, 7], [8, 9], [11, 12]],
        )

        agent = ReflectionRepairAgent(blackboard=bb)

        surviving = [
            {"mutant_id": "MUT_01", "line_number": 7, "operator": "REPLACEMENT", "status": "SURVIVED"},
            {"mutant_id": "MUT_02", "line_number": 12, "operator": "ARITHMETIC", "status": "SURVIVED"},
        ]

        candidate_code, plan = agent.generate_repair_patch(
            target_source_code=SAMPLE_TARGET,
            current_test_code=INITIAL_TESTS,
            mutants=surviving,
            iteration=1,
        )

        assert isinstance(candidate_code, str)
        assert len(candidate_code) > 0
        assert isinstance(plan, TestGapRemediationPlan)
        assert plan.total_gaps_identified == 3
        assert "MUT_01" in plan.surviving_mutants_in_gap
        assert "MUT_02" in plan.surviving_mutants_in_gap

        # Verify Blackboard CriticSpace updated with gap directives
        critic_space = bb.get_critic_space()
        assert len(critic_space.critic_directives) > 0
        assert critic_space.latest_directive is not None

