"""
tests/test_feature_flags.py

Behavioral test suite verifying Handout Criterion 1.1:
Configurable feature flags and capability toggles across the 9 modules:
  1. ref_exec
  2. reflection
  3. self_consistency
  4. tot
  5. react
  6. rag
  7. memory
  8. critic
  9. equivalence
"""

import os
import pytest
from testforge.feature_flags import FeatureFlags
from testforge.orchestrator import TestForgeOrchestrator
from testforge.reflection_agent import ReflectionRepairAgent


def test_feature_flags_all_enabled_defaults():
    flags = FeatureFlags.all_enabled()
    assert flags.ref_exec is True
    assert flags.reflection is True
    assert flags.self_consistency is True
    assert flags.tot is True
    assert flags.react is True
    assert flags.rag is True
    assert flags.memory is True
    assert flags.critic is True
    assert flags.equivalence is True


def test_feature_flags_zero_shot_baseline():
    flags = FeatureFlags.zero_shot()
    assert flags.ref_exec is False
    assert flags.reflection is False
    assert flags.self_consistency is False
    assert flags.tot is False
    assert flags.react is False
    assert flags.rag is False
    assert flags.memory is False
    assert flags.critic is False
    assert flags.equivalence is False


def test_feature_flags_from_env(monkeypatch):
    monkeypatch.setenv("TESTFORGE_FLAG_REFLECTION", "0")
    monkeypatch.setenv("TESTFORGE_FLAG_CRITIC", "false")
    monkeypatch.setenv("TESTFORGE_FLAG_EQUIVALENCE", "off")
    monkeypatch.setenv("TESTFORGE_FLAG_TOT", "1")

    flags = FeatureFlags.from_env()
    assert flags.reflection is False
    assert flags.critic is False
    assert flags.equivalence is False
    assert flags.tot is True
    assert flags.self_consistency is True  # default unchanged


def test_feature_flags_clone_with():
    flags = FeatureFlags.all_enabled()
    modified = flags.clone_with(reflection=False, memory=False)
    assert flags.reflection is True  # original unmodified
    assert modified.reflection is False
    assert modified.memory is False
    assert modified.tot is True


def test_reflection_repair_agent_tot_disabled():
    """Verify that when tot=False, Tree of Thoughts evaluates only 1 branch."""
    flags = FeatureFlags.all_enabled().clone_with(tot=False)
    agent = ReflectionRepairAgent(use_live_llm=False, feature_flags=flags)
    
    survivors = [{"mutant_id": "m1", "operator": "COMP_OP", "status": "SURVIVED"}]
    res = agent.repair_with_tree_of_thought(
        surviving_mutants=survivors,
        target_source_code="def f(x): return x > 0",
    )
    assert len(res["branches_evaluated"]) == 1


def test_reflection_repair_agent_react_disabled():
    """Verify that when react=False, ReAct repair loop is bypassed."""
    flags = FeatureFlags.all_enabled().clone_with(react=False)
    agent = ReflectionRepairAgent(use_live_llm=False, feature_flags=flags)

    res = agent.run_react_repair_loop(
        target_source_code="def f(x): return x > 0",
        current_test_code="def test_f(): pass",
    )
    assert res["total_steps"] == 0
    assert "disabled" in res["final_thought"].lower()


def test_reflection_repair_agent_memory_disabled():
    """Verify that when memory=False, mutant_memory is disabled."""
    flags = FeatureFlags.all_enabled().clone_with(memory=False)
    agent = ReflectionRepairAgent(use_live_llm=False, feature_flags=flags)
    assert agent.mutant_memory is None


def test_orchestrator_reflection_disabled_exits_early():
    """Verify that when reflection=False, orchestrator exits after initial pass without repair loop."""
    flags = FeatureFlags.all_enabled().clone_with(reflection=False)
    target_code = "def is_positive(x: int) -> bool:\n    return x > 0\n"
    initial_test = "from target import is_positive\ndef test_pos():\n    assert is_positive(5) is True\n"

    orchestrator = TestForgeOrchestrator(
        target_source_code=target_code,
        initial_test_code=initial_test,
        max_iterations=3,
        target_mutation_score=100.0,
        feature_flags=flags,
    )

    state = orchestrator.harden()
    assert state.current_iteration == 1
    assert "reflection=False" in state.termination_reason


def test_orchestrator_equivalence_disabled_equalizes_raw_and_adj_scores():
    """Verify that when equivalence=False, equivalent mutants are not deducted."""
    flags = FeatureFlags.all_enabled().clone_with(equivalence=False, reflection=False)
    target_code = "def check(x: int) -> int:\n    if x > 10:\n        return x * 2\n    return x\n"
    initial_test = "from target import check\ndef test_chk():\n    assert check(20) == 40\n"

    orchestrator = TestForgeOrchestrator(
        target_source_code=target_code,
        initial_test_code=initial_test,
        max_iterations=1,
        feature_flags=flags,
    )

    state = orchestrator.harden()
    assert len(state.history) >= 1
    last_metrics = state.history[-1]
    assert last_metrics.equivalent_mutants == 0
    assert last_metrics.potentially_equivalent_mutants == 0
    assert last_metrics.adjusted_mutation_score == last_metrics.raw_mutation_score
