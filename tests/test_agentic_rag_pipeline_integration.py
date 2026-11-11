"""
tests/test_agentic_rag_pipeline_integration.py

Comprehensive integration test suite for Handout Feature F1:
Agentic RAG Pipeline Integration (Phase B).

Verifies:
  1. Local Zero-Egress Knowledge Base retrieval via AgenticKnowledgeRetriever.
  2. AST Symbol & Sequence Parameter query synthesis in TestPlanningAgent.derive_test_plan.
  3. Live Orchestrator integration and OpenTelemetry 'rag.retrieval' span emission.
  4. DEF-022 Clean Pre-Flight Guard compliance (Pass@1 == 100%) in HybridSynthesizer.
  5. Graceful fallback when RAG retrieval is disabled or returns empty.
"""

from __future__ import annotations

import ast
import tempfile
from pathlib import Path

import pytest

from testforge.a2a import TestPlanPayload
from testforge.blackboard import Blackboard
from testforge.hybrid_synthesizer import HybridSynthesizer
from testforge.observability import TestForgeOtelTracer
from testforge.orchestrator import TestForgeOrchestrator
from testforge.planning_agent import TestPlanningAgent, derive_test_plan
from testforge.rag.knowledge_retriever import AgenticKnowledgeRetriever


def test_retriever_query_reformulation_and_grading_for_division_ast():
    """
    Test 1: AgenticKnowledgeRetriever correctly reformulates and grades
    chunks when querying arithmetic AST patterns like BinOp(Div).
    """
    retriever = AgenticKnowledgeRetriever()
    query = "BinOp(Div) division zero denominator"
    res = retriever.retrieve(query=query, top_k=3, min_score=0.1)

    assert len(res.chunks) > 0, "Expected at least one retrieved chunk for BinOp(Div)"
    categories = [c.get("metadata", {}).get("category") for c in res.chunks]
    assert "arithmetic_division" in categories, f"Expected arithmetic_division in {categories}"

    top_chunk = res.chunks[0]
    assert top_chunk.get("relevance_score", 0.0) > 0.3
    assert "doc_id" in top_chunk
    assert "text" in top_chunk


def test_derive_test_plan_ast_inference_and_blackboard_population():
    """
    Test 2: TestPlanningAgent.derive_test_plan extracts AST symbols,
    retrieves testing heuristics, and populates TestPlanPayload & Blackboard.
    """
    code = (
        "def compute_discount(price, rate):\n"
        "    if rate == 0:\n"
        "        raise ZeroDivisionError('zero rate')\n"
        "    return price / rate\n"
    )
    tree = ast.parse(code)
    heuristics = derive_test_plan(tree)
    assert len(heuristics) > 0
    assert any(h.get("metadata", {}).get("category") == "arithmetic_division" for h in heuristics)

    # Test via TestPlanningAgent and Blackboard
    bb = Blackboard()
    agent = TestPlanningAgent(blackboard=bb)
    plan = agent.plan_tests(code, job_id="test_plan_rag_001")

    assert isinstance(plan, TestPlanPayload)
    assert len(plan.rag_heuristics) > 0
    assert "RAG testing heuristics" in plan.planning_rationale

    # Check Blackboard PlanSpace
    plan_space = bb.get_plan_space()
    assert len(plan_space.rag_heuristics) == len(plan.rag_heuristics)


def test_orchestrator_rag_span_emission():
    """
    Test 3: TestForgeOrchestrator with enable_rag=True emits an OpenTelemetry
    'rag.retrieval' span containing telemetry attributes.
    """
    tracer = TestForgeOtelTracer.get_instance()
    tracer.clear()

    target_code = (
        "def divide_safe(x, y):\n"
        "    if y == 0:\n"
        "        return 0\n"
        "    return x / y\n"
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        tpath = Path(tmpdir) / "target_div.py"
        tpath.write_text(target_code, encoding="utf-8")

        orch = TestForgeOrchestrator(
            target_source_code=target_code,
            target_file_path=str(tpath),
            max_iterations=1,
            engine_mode="local",
            enable_rag=True,
            job_id="job_otel_rag_verify",
        )
        orch.run()

    traces = tracer.get_traces_summary(job_id="job_otel_rag_verify")
    rag_spans = [s for s in traces if s.get("name") == "rag.retrieval"]

    assert len(rag_spans) >= 1, "Expected at least one 'rag.retrieval' span recorded"
    span_attrs = rag_spans[0].get("attributes", {})
    assert span_attrs.get("testforge.job_id") == "job_otel_rag_verify"
    assert "rules_count" in span_attrs
    assert span_attrs.get("rules_count", 0) > 0
    assert "top_score" in span_attrs


def test_hybrid_synthesizer_clean_pass_integrity_with_rag():
    """
    Test 4: HybridSynthesizer with enable_rag=True injects RAG heuristics and
    strictly guarantees clean pre-flight validation (DEF-022 Pass@1 == 100%).
    """
    target_code = (
        "def rate_calculator(amount, factor):\n"
        "    if factor == 0:\n"
        "        raise ZeroDivisionError('factor cannot be zero')\n"
        "    return amount / factor\n"
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        tpath = Path(tmpdir) / "calc.py"
        tpath.write_text(target_code, encoding="utf-8")

        synth = HybridSynthesizer(
            target_code=target_code,
            target_file_path=str(tpath),
            enable_rag=True,
        )
        seed_suite = synth._generate_seed_tests()
        assert "def test_" in seed_suite

        # Pass@1 check
        clean_suite, is_clean = synth.filter_clean_passing_tests(seed_suite)
        assert is_clean is True
        assert "def test_" in clean_suite


def test_rag_disabled_fallback():
    """
    Test 5: When enable_rag=False, TestForgeOrchestrator executes safely
    without triggering RAG retrieval spans.
    """
    tracer = TestForgeOtelTracer.get_instance()
    tracer.clear()

    target_code = (
        "def add(a, b):\n"
        "    return a + b\n"
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        tpath = Path(tmpdir) / "add.py"
        tpath.write_text(target_code, encoding="utf-8")

        orch = TestForgeOrchestrator(
            target_source_code=target_code,
            target_file_path=str(tpath),
            max_iterations=1,
            engine_mode="local",
            enable_rag=False,
            job_id="job_rag_disabled",
        )
        orch.run()

    traces = tracer.get_traces_summary(job_id="job_rag_disabled")
    rag_spans = [s for s in traces if s.get("name") == "rag.retrieval"]
    assert len(rag_spans) == 0, "No 'rag.retrieval' span should be emitted when enable_rag=False"

