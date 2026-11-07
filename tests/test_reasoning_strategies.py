"""
tests/test_reasoning_strategies.py

Verification suite for Handout Feature F2: Advanced Reasoning Strategies
mapped to unit test generation, planning, and defect repair:
  1. Self-Consistency in Test Generation (Multi-candidate sampling with clean Reference Execution consensus).
  2. Tree-of-Thought (ToT) in Reflection & Repair (Multi-branch search scored by delta kill & coverage).
  3. ReAct Interactive Tool Deliberation in Reflection & Repair (Thought -> Action -> Observation).
  4. Chain-of-Thought (CoT) Step-by-Step Boundary Analysis in Test Planning.
"""

import pytest

from testforge.adk_generator import ADKModelBridge, GoogleADKTestGenerator, SelfConsistencyResult
from testforge.agents import TestGeneratorAgent
from testforge.blackboard import Blackboard
from testforge.planning_agent import TestPlanningAgent
from testforge.reflection_agent import ReflectionRepairAgent

SAMPLE_TARGET_CODE = """
def calculate_discount(price: float) -> float:
    if price > 100:
        return price * 0.9
    elif price == 100:
        return price * 0.95
    return price
"""


class TestSelfConsistencyGenerator:
    """Verifies Self-Consistency multi-candidate sampling and Reference Execution consensus (Module 1)."""

    def test_self_consistency_samples_and_filters_against_reference_oracle(self):
        bridge = ADKModelBridge()
        result = bridge.generate_tests_with_self_consistency(
            target_code=SAMPLE_TARGET_CODE,
            sample_count=3,
        )

        assert isinstance(result, SelfConsistencyResult)
        assert result.candidate_count == 3
        assert result.valid_candidates >= 1
        assert result.consensus_assertions_retained >= 1
        assert "def test_" in result.consensus_test_code

        # Telemetry verification
        telemetry = result.telemetry
        assert telemetry["candidate_count"] == 3
        assert telemetry["valid_candidates"] >= 1
        assert telemetry["consensus_assertions_retained"] >= 1

    def test_self_consistency_filters_hallucinated_assertions(self):
        """Ensures candidate tests with invalid assertions against clean reference are discarded."""
        bridge = ADKModelBridge()

        # Valid candidate
        candidate_valid = """
import pytest
def test_valid_discount():
    assert calculate_discount(200) == 180.0
"""
        # Hallucinated candidate asserting false outcome
        candidate_hallucinated = """
import pytest
def test_hallucinated_discount():
    assert calculate_discount(200) == 50.0
"""
        result = bridge.generate_tests_with_self_consistency(
            target_code=SAMPLE_TARGET_CODE,
            sample_count=2,
            candidate_codes=[candidate_valid, candidate_hallucinated],
        )

        assert result.candidate_count == 2
        # Only the valid candidate should be retained
        assert result.valid_candidates == 1
        assert "test_valid_discount" in result.consensus_test_code
        assert "test_hallucinated_discount" not in result.consensus_test_code

    def test_delegated_generators_support_self_consistency(self):
        adk_gen = GoogleADKTestGenerator()
        res_adk = adk_gen.generate_tests_with_self_consistency(SAMPLE_TARGET_CODE, sample_count=3)
        assert res_adk.candidate_count == 3
        assert res_adk.consensus_assertions_retained >= 1

        agent = TestGeneratorAgent()
        res_agent = agent.generate_tests_with_self_consistency(SAMPLE_TARGET_CODE, sample_count=3)
        assert res_agent.candidate_count == 3
        assert res_agent.consensus_assertions_retained >= 1


class TestTreeOfThoughtReflection:
    """Verifies Tree-of-Thought (ToT) multi-branch search in Reflection & Repair (Module 2)."""

    def test_tot_branches_into_three_hypotheses_and_scores_candidate_patches(self):
        repair_agent = ReflectionRepairAgent()
        survivors = [
            {"mutant_id": "mut_comp_001", "operator": "COMP_OP", "status": "SURVIVED", "line_number": 3},
            {"mutant_id": "mut_arith_002", "operator": "ARITH_OP", "status": "SURVIVED", "line_number": 4},
        ]
        branch_gaps = ["3 -> 5", "5 -> exit"]

        tot_result = repair_agent.repair_with_tree_of_thought(
            surviving_mutants=survivors,
            branch_gaps=branch_gaps,
            target_source_code=SAMPLE_TARGET_CODE,
            max_depth=2,
            beam_width=3,
        )

        assert "selected_branch" in tot_result
        assert "best_candidate_code" in tot_result
        assert "best_score" in tot_result
        assert "branches_evaluated" in tot_result

        evaluated = tot_result["branches_evaluated"]
        assert len(evaluated) == 3

        # Verify all 3 hypotheses are explored
        hypotheses = [b["hypothesis"] for b in evaluated]
        assert "VALUE_BOUNDARY_INVERSION" in hypotheses
        assert "PROPERTY_INVARIANT_ENFORCEMENT" in hypotheses
        assert "CONTROL_FLOW_PATH_FORCING" in hypotheses

        # Verify scoring function: Delta_Killed * 10 + Delta_Branch * 5 - Exec_Time
        for b in evaluated:
            expected_score = round((b["delta_killed"] * 10.0) + (b["delta_branch_coverage"] * 5.0) - b["execution_time"], 2)
            assert abs(b["score"] - expected_score) <= 0.05

        # Winning branch must have the highest score
        max_score = max(b["score"] for b in evaluated)
        assert tot_result["best_score"] == max_score


class TestReActReflectionLoop:
    """Verifies ReAct interactive tool deliberation in Reflection & Repair (Module 2)."""

    def test_react_tool_methods_execute_and_return_structured_observations(self):
        bb = Blackboard()
        bb.update_target_space(target_source_code=SAMPLE_TARGET_CODE)
        bb.update_execution_space(missing_branches=["3 -> 5", "5 -> exit"])
        bb.update_mutant_space(mutants=[
            {
                "mutant_id": "mut_react_01",
                "mutation_type": "COMP_OP",
                "line_number": 3,
                "original_code_snippet": "if price > 100:",
                "mutated_code_snippet": "if price >= 100:",
                "unified_diff": "- if price > 100:\n+ if price >= 100:",
                "status": "SURVIVED",
            }
        ])

        repair_agent = ReflectionRepairAgent(blackboard=bb)

        # 1. tool_get_unreached_branches
        branches = repair_agent.tool_get_unreached_branches()
        assert len(branches) == 2
        assert "3 -> 5" in branches

        # 2. tool_inspect_mutant_diff
        diff = repair_agent.tool_inspect_mutant_diff("mut_react_01")
        assert "price >= 100" in diff

        # 3. tool_run_sandbox
        test_patch = "import pytest\nfrom target import calculate_discount\ndef test_dummy(): assert calculate_discount(150) == 135.0"
        sandbox_res = repair_agent.tool_run_sandbox(test_patch, target_code=SAMPLE_TARGET_CODE)
        assert sandbox_res["status"] in ("PASS", "PASSED", "SUCCESS")
        assert sandbox_res["tests_passed"] >= 1

    def test_run_react_repair_loop_records_thought_action_observation_trajectory(self):
        bb = Blackboard()
        bb.update_target_space(target_source_code=SAMPLE_TARGET_CODE)
        bb.update_execution_space(missing_branches=["3 -> 5"])
        bb.update_mutant_space(mutants=[
            {
                "mutant_id": "mut_001",
                "mutation_type": "COMP_OP",
                "line_number": 3,
                "original_code_snippet": "if price > 100:",
                "mutated_code_snippet": "if price >= 100:",
                "unified_diff": "- if price > 100:\n+ if price >= 100:",
                "status": "SURVIVED",
            }
        ])

        repair_agent = ReflectionRepairAgent(blackboard=bb)
        trajectory = repair_agent.run_react_repair_loop(
            target_source_code=SAMPLE_TARGET_CODE,
            current_test_code="import pytest\n",
            surviving_mutants=[{"mutant_id": "mut_001", "operator": "COMP_OP"}],
            max_steps=3,
        )

        assert "steps" in trajectory
        assert len(trajectory["steps"]) == 3

        # Validate Thought-Action-Observation schema
        for step in trajectory["steps"]:
            assert "step" in step
            assert "thought" in step
            assert "action" in step
            assert "observation" in step
            assert len(step["thought"]) > 5
            assert len(step["action"]) > 3

        # Verify Blackboard CriticSpace updated with ReAct trajectory
        critic_space = bb.get_critic_space()
        assert len(critic_space.react_trajectories) >= 1
        assert "ReAct repair completed" in critic_space.latest_directive


class TestChainOfThoughtPlanning:
    """Verifies Chain-of-Thought (CoT) boundary analysis in Test Planning (Module 3)."""

    def test_cot_step_by_step_boundary_derivation(self):
        bb = Blackboard()
        planner = TestPlanningAgent(blackboard=bb)

        plan = planner.plan_tests(SAMPLE_TARGET_CODE, job_id="job_cot_test")

        assert plan.cot_reasoning_trace, "cot_reasoning_trace should be populated"
        trace = plan.cot_reasoning_trace
        assert len(trace) >= 4

        steps = [s["step"] for s in trace]
        assert 1 in steps  # Step 1: Input signature and domain type classification
        assert 2 in steps  # Step 2: Identification of conditional comparison operators & threshold values (T)
        assert 3 in steps  # Step 3: Derivation of boundary regions (T-1, T, T+1, extreme zero/negatives)
        assert 4 in steps  # Step 4: Formulation of planned assertion targets

        # Step 1 checks
        s1 = next(s for s in trace if s["step"] == 1)
        assert s1["step_name"] == "DOMAIN_CLASSIFICATION"
        assert "price" in s1["domain_types"]

        # Step 2 checks: threshold 100 identified
        s2 = next(s for s in trace if s["step"] == 2)
        assert s2["step_name"] == "THRESHOLD_IDENTIFICATION"
        thresholds = [t["threshold"] for t in s2["thresholds"]]
        assert 100 in thresholds or 100.0 in thresholds

        # Step 3 checks: neighborhood around 100
        s3 = next(s for s in trace if s["step"] == 3)
        assert s3["step_name"] == "BOUNDARY_REGION_DERIVATION"
        neighborhoods = [r["boundary_neighborhood"] for r in s3["boundary_regions"]]
        assert any(100 in n or 100.0 in n for n in neighborhoods)

        # Step 4 checks: planned assertions
        s4 = next(s for s in trace if s["step"] == 4)
        assert s4["step_name"] == "PLANNED_ASSERTION_TARGETS"
        assert s4["planned_assertions_count"] >= 1

        # Blackboard PlanSpace verification
        plan_space = bb.get_plan_space()
        assert len(plan_space.cot_reasoning_trace) >= 4
        assert plan_space.planning_status == "PLANNED"
