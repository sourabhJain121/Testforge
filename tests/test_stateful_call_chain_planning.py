"""
tests/test_stateful_call_chain_planning.py

Unit and integration tests for Stateful Call-Chain Planning & Multi-Step Sequence Synthesis:
1. CodeIntelligenceAgent extracts LRUCache stateful metadata (capacity constructor param, get accessor, put mutator).
2. mcp_ast_symbol_analyzer emits structured stateful_classes metadata.
3. TestPlanningAgent formulates ordered multi-step eviction and recency sequence plans and emits STATEFUL_SEQUENCE_PLAN_GENERATED telemetry.
4. CrewAI Critic emits targeted stateful transition and doubly-linked pointer integrity directives.
5. End-to-end benchmark on samples/lru_cache.py achieves 100% Pass@1 clean preflight and mutation score >= 75%.
6. Agentic RAG corpus includes enriched canonical stateful cache & FSM rules.
"""

import pytest
from pathlib import Path
from testforge.code_intelligence_agent import CodeIntelligenceAgent, extract_stateful_classes_from_ast
from testforge.mcp_server import mcp_ast_symbol_analyzer
from testforge.planning_agent import TestPlanningAgent
from testforge.crewai_agents import CrewCodeIntelligenceCriticCrew
from testforge.intelligent_generator import IntelligentASTSynthesizer
from testforge.benchmarking import BenchmarkRunner
from testforge.rag.corpus import load_all_corpus_documents


@pytest.fixture
def lru_cache_source() -> str:
    path = Path("samples/lru_cache.py")
    assert path.exists(), "samples/lru_cache.py must exist"
    return path.read_text(encoding="utf-8")


def test_code_intelligence_agent_extracts_lru_cache_stateful_metadata(lru_cache_source: str):
    """Verify CodeIntelligenceAgent extracts LRUCache stateful metadata (capacity, get, put)."""
    cia = CodeIntelligenceAgent(use_live_llm=False)
    payload = cia.analyze_source(lru_cache_source, target_file_path="samples/lru_cache.py")

    assert payload.analysis_status == "SUCCESS"
    assert len(payload.stateful_classes) >= 1

    lru = next((c for c in payload.stateful_classes if c["class_name"] == "LRUCache"), None)
    assert lru is not None, "LRUCache must be discovered as a stateful class"

    # Verify constructor parameters
    param_names = [p["name"] for p in lru["constructor_params"]]
    assert "capacity" in param_names, "Constructor parameter 'capacity' must be extracted"
    assert lru["has_capacity_limit"] is True
    assert lru["capacity_param"] == "capacity"

    # Verify mutator and accessor methods
    assert "put" in lru["mutator_methods"], "Method 'put' must be classified as a mutator"
    assert "get" in lru["methods"], "Method 'get' must be identified in class methods"
    assert "get" in lru["accessor_methods"] or "get" in lru["mutator_methods"]

    # Verify state attributes
    assert "lookup" in lru["state_attributes"]
    assert "capacity" in lru["state_attributes"]


def test_mcp_ast_symbol_analyzer_emits_stateful_classes(lru_cache_source: str):
    """Verify mcp_ast_symbol_analyzer MCP tool returns stateful_classes metadata."""
    mcp_res = mcp_ast_symbol_analyzer(lru_cache_source)

    assert mcp_res["status"] == "SUCCESS"
    assert "stateful_classes" in mcp_res
    assert len(mcp_res["stateful_classes"]) >= 1

    lru = next((c for c in mcp_res["stateful_classes"] if c["class_name"] == "LRUCache"), None)
    assert lru is not None
    assert any(p["name"] == "capacity" for p in lru["constructor_params"])
    assert "put" in lru["mutator_methods"]
    assert "get" in lru["methods"]


def test_planning_agent_produces_ordered_stateful_call_chains(lru_cache_source: str):
    """Verify TestPlanningAgent produces ordered multi-step eviction & recency sequences."""
    planner = TestPlanningAgent(use_live_llm=False)
    plan = planner.plan_tests(code_intelligence=lru_cache_source)

    assert plan.status == "PLANNED"
    assert len(plan.stateful_call_chains) >= 1

    # Verify multi-step eviction & recency sequence scenario
    eviction_chain = next(
        (c for c in plan.stateful_call_chains if "eviction" in c.get("title", "").lower() or "eviction" in c.get("scenario_name", "").lower()),
        None
    )
    assert eviction_chain is not None, "Stateful plan must include eviction & recency transition sequence"
    assert eviction_chain["category"] == "stateful_call_chain"
    assert len(eviction_chain.get("steps", [])) >= 4

    # Verify steps contain ordered method transitions
    steps_text = " ".join(eviction_chain["steps"])
    assert "put" in steps_text
    assert "get" in steps_text
    assert "evict" in steps_text.lower() or "boundary" in steps_text.lower()

    # Verify key update recency sequence exists
    update_chain = next(
        (c for c in plan.stateful_call_chains if "update" in c.get("title", "").lower() or "update" in c.get("scenario_name", "").lower()),
        None
    )
    assert update_chain is not None, "Stateful plan must include key update recency sequence"


def test_crewai_critic_stateful_transition_directives(lru_cache_source: str):
    """Verify CrewCriticAgent emits stateful transition directives when pointer or boundary mutants survive."""
    critic = CrewCodeIntelligenceCriticCrew()
    surviving_mutants = [
        {
            "mutant_id": "MUT_POINTER_01",
            "line_number": 48,
            "mutation_type": "POINTER_MUTATION",
            "original_expr": "node.next = self.head.next",
            "mutated_expr": "node.next = None",
        }
    ]
    critique = critic.critique_surviving_mutants(source_code=lru_cache_source, surviving_mutants=surviving_mutants)

    assert critique["status"] == "success"
    directive_text = critique["directive"].lower()
    assert "doubly-linked" in directive_text or "pointer" in directive_text or "stateful" in directive_text


def test_lru_cache_pass_at_1_and_lifted_mutation_score(lru_cache_source: str):
    """
    Verify running TestForge on samples/lru_cache.py achieves 100% Pass@1 clean preflight
    and significantly lifts mutation kill score above the 30.95% baseline (>= 75% raw MS).
    """
    synth = IntelligentASTSynthesizer().synthesize_test_suite(lru_cache_source)
    assert "def test_" in synth.test_code

    runner = BenchmarkRunner(target_code=lru_cache_source, target_file_path="samples/lru_cache.py")
    res = runner.evaluate_suite(synth.test_code)

    assert res.baseline_passed is True, "LRUCache test suite must achieve 100% Pass@1 on clean reference code"
    assert res.invalid_suite is False, "LRUCache test suite must be marked valid"
    assert res.score is not None
    assert res.score >= 75.0, f"Mutation score must achieve >= 75.0%, achieved {res.score}% ({res.killed}/{res.total})"
    assert res.killed >= 30, f"Expected at least 30 mutants killed, got {res.killed}"


def test_rag_corpus_contains_enriched_stateful_cache_rules():
    """Verify stateful_cache_fsm.json corpus contains enriched canonical LRU & FSM invariants."""
    docs = load_all_corpus_documents()
    doc_ids = {d.get("doc_id") for d in docs}

    assert "rule_fsm_cache_eviction" in doc_ids
    assert "rule_lru_recency_promotion" in doc_ids
    assert "rule_lru_key_update_recency" in doc_ids
    assert "rule_doubly_linked_sentinel_invariants" in doc_ids
    assert "rule_cache_capacity_boundary_validation" in doc_ids
    assert "rule_cache_hit_ratio_and_reset" in doc_ids
