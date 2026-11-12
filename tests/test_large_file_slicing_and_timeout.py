"""
tests/test_large_file_slicing_and_timeout.py - Validation for AST Context Slicing,
LLM Synthesis Timeout Fallback, and Mutant Stratification on Large Codebases.
"""

from __future__ import annotations

import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from testforge.hybrid_synthesizer import (
    _slice_large_target_context,
    execute_llm_synthesis_with_timeout,
    get_sliced_target_scope,
)
from testforge.mutator import ASTMutator, _stratify_mutants
from testforge.orchestrator import TestForgeOrchestrator
from testforge.state import MutantRecord


def test_slice_large_target_context_leaves_small_files_intact():
    """Verify small/medium targets (<350 lines) are returned unmodified."""
    discount_path = Path("samples/discount.py")
    if not discount_path.exists():
        pytest.skip("samples/discount.py not found")
    source = discount_path.read_text()
    sliced = _slice_large_target_context(source, max_lines=350, max_functions=15)
    assert sliced == source


def test_slice_large_target_context_slices_massive_file():
    """Verify massive targets (>350 lines) are sliced to top functions with imports."""
    bottle_path = Path("samples/bottle.py")
    if not bottle_path.exists():
        pytest.skip("samples/bottle.py not found")
    source = bottle_path.read_text()
    sliced = _slice_large_target_context(source, max_lines=350, max_functions=15)

    assert sliced != source
    assert sliced.startswith("# [Context Sliced: Top 15 functions of")
    assert "import " in sliced or "from " in sliced
    # Must be valid syntax
    import ast
    parsed = ast.parse(sliced)
    assert len(parsed.body) > 0


def test_execute_llm_synthesis_timeout_fallback():
    """Verify LLM synthesis strictly times out and falls back to deterministic code."""
    def hanging_generator():
        time.sleep(1.0)
        return "def test_never_reached(): pass"

    fallback = "def test_fallback(): assert True"
    code, timed_out = execute_llm_synthesis_with_timeout(
        hanging_generator,
        timeout_seconds=0.05,
        fallback_code=fallback,
    )
    assert timed_out is True
    assert code == fallback


def test_execute_llm_synthesis_success_within_timeout():
    """Verify LLM synthesis finishes successfully within timeout."""
    def quick_generator():
        return "def test_quick(): assert 1 == 1"

    code, timed_out = execute_llm_synthesis_with_timeout(
        quick_generator,
        timeout_seconds=2.0,
    )
    assert timed_out is False
    assert "test_quick" in code


def test_stratify_mutants_distributes_categories():
    """Verify _stratify_mutants samples evenly across distinct mutation types."""
    mutants = []
    types = ["COMP_OP", "ARITH_OP", "COND_INV", "RETURN_VAL", "OFF_BY_ONE"]
    for i in range(100):
        m_type = types[i % len(types)]
        mutants.append(
            MutantRecord(
                mutant_id=f"MUT_{m_type}_{i:03d}",
                mutation_type=m_type,
                line_number=i + 1,
                original_code_snippet="x = 1",
                mutated_code_snippet="x = 2",
                unified_diff="",
                status="PENDING",
            )
        )

    sampled = _stratify_mutants(mutants, max_limit=20)
    assert len(sampled) == 20
    sampled_types = set(m.mutation_type for m in sampled)
    assert len(sampled_types) == len(types)


def test_get_sliced_target_scope_and_allowed_line_ranges():
    """Verify get_sliced_target_scope returns valid line ranges and ASTMutator respects them."""
    bottle_path = Path("samples/bottle.py")
    if not bottle_path.exists():
        pytest.skip("samples/bottle.py not found")
    source = bottle_path.read_text()

    sliced_code, line_ranges = get_sliced_target_scope(source, max_lines=350, max_functions=15)
    assert len(line_ranges) <= 15
    assert len(line_ranges) > 0
    for start, end in line_ranges:
        assert start <= end

    # Test that ASTMutator restricts mutants strictly to allowed_line_ranges
    mutants = ASTMutator.mutate(source, max_mutants=30, allowed_line_ranges=line_ranges)
    assert len(mutants) > 0
    for m in mutants:
        in_range = any(start <= m.line_number <= end for start, end in line_ranges)
        assert in_range, f"Mutant {m.mutant_id} on line {m.line_number} is outside allowed_line_ranges!"


def test_small_file_mutates_all_functions_without_restriction():
    """Verify small/medium files (<=350 lines) are not restricted in mutant generation."""
    discount_path = Path("samples/discount.py")
    if not discount_path.exists():
        pytest.skip("samples/discount.py not found")
    source = discount_path.read_text()

    sliced, ranges = get_sliced_target_scope(source, max_lines=350, max_functions=15)
    assert ranges == [(1, len(source.splitlines()))]
    mutants = ASTMutator.mutate(source)
    assert len(mutants) > 0


def test_frontend_finalization_banner_and_bb_sync_contracts():
    """Verify frontend/app.js handles score comparison and updates #bb-suite-status."""
    app_js = Path("frontend/app.js").read_text()
    index_html = Path("frontend/index.html").read_text()

    # Element exists in index.html
    assert 'id="bb-suite-status"' in index_html or 'id="bb-suite-summary"' in index_html
    # Suite status updated upon finalization
    assert "Finalized (${basePass} clean tests)" in app_js or "Finalized (${passedCount} clean tests)" in app_js
    # Score check renders amber warning when below target
    assert "Hardening Complete: Finalized below target" in app_js
    assert "Hardening Complete: Achieved target score!" in app_js
    # TIMED_OUT handling
    assert "TIMED_OUT (PARTIAL)" in app_js
    assert "Timed Out (Best Metrics Preserved)" in app_js


def test_testability_ranking_penalizes_servers_and_boosts_pure_helpers():
    """Verify testability scoring formula prioritizes pure data structures over WSGI servers."""
    import ast
    from testforge.hybrid_synthesizer import _score_callable_testability

    code_helper = "def parse_token_cookie(key, secret, default=None): return key + secret"
    tree_helper = ast.parse(code_helper)
    score_helper = _score_callable_testability(tree_helper.body[0], class_name="CookieDict")

    code_server = "def wsgi_handler(environ, start_response): pass"
    tree_server = ast.parse(code_server)
    score_server = _score_callable_testability(tree_server.body[0], class_name="WSGIServerAdapter")

    assert score_helper > score_server
    assert score_helper >= 30
    assert score_server < 0


def test_orchestrator_finalize_timeout_preserves_best_metrics():
    """Verify orchestrator _finalize_cancellation_or_timeout hydrates and preserves peak metrics."""
    from testforge.orchestrator import TestForgeOrchestrator
    from testforge.blackboard import Blackboard
    from testforge.state import MutantRecord

    orch = TestForgeOrchestrator(
        target_file_path="samples/discount.py",
        timeout_seconds=90.0,
    )
    orch.blackboard = Blackboard()

    # Simulate best metrics achieved
    orch._best_iteration = 1
    orch._best_mutants_generated = 20
    orch._best_mutants_killed = 14
    orch._best_mutants_survived = 6
    orch._best_mutants_executed = 20
    orch._best_raw_mutation_score = 70.0
    orch._best_test_code = "def test_peak(): assert True"
    orch._best_mutants = [
        MutantRecord(
            mutant_id="MUT_01",
            mutation_type="COMP_OP",
            line_number=10,
            original_code_snippet="a < b",
            mutated_code_snippet="a <= b",
            unified_diff="",
            status="KILLED",
        )
    ]

    orch._finalize_cancellation_or_timeout("TIMED_OUT", "Job execution exceeded time bound")

    assert orch.state.final_hardening_status == "TIMED_OUT"
    assert orch.state.mutants_killed == 14
    assert orch.state.mutants_generated == 20
    assert orch.state.final_mutation_score == 70.0

    bb_mutant = orch.blackboard.get_mutant_space()
    assert bb_mutant.mutants_killed == 14
    assert bb_mutant.mutants_generated == 20
    assert bb_mutant.raw_mutation_score == 70.0




