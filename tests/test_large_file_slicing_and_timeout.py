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

