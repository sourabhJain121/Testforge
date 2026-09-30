"""
test_blast_and_adk.py - Unit tests for BlastRadiusAnalyzer, GitDiffInspector, and ADK Engine.

Author: Sourabh & Shreshth
Course: CSE3101 - Agentic AI
"""

import pytest
from testforge.blast_analyzer import BlastRadiusAnalyzer, ASTCallGraphVisitor
from testforge.git_diff import GitDiffInspector
from testforge.mutator import ASTMutator
from testforge.adk_engine import ADKToolRegistry, ToolDefinition, ToolCallResult, ADKContext

SAMPLE_CODE = """
def sanitize(val):
    return val.strip() if val else ""

def format_name(first, last):
    f = sanitize(first)
    l = sanitize(last)
    return f"{f} {l}"

def create_user_record(first, last, age):
    full_name = format_name(first, last)
    is_adult = (age >= 18)
    return {"name": full_name, "adult": is_adult}
"""


def test_blast_radius_analyzer():
    cg = BlastRadiusAnalyzer.build_call_graph(SAMPLE_CODE)
    assert "format_name" in cg
    assert "sanitize" in cg["format_name"]

    impact = BlastRadiusAnalyzer.analyze_impact("sanitize", SAMPLE_CODE)
    assert impact["target_function"] == "sanitize"
    assert "format_name" in impact["upstream_callers"]
    assert "create_user_record" in impact["upstream_callers"]
    assert impact["risk_category"] in ("MEDIUM", "HIGH")
    assert "ASCII Call Tree" or "📌" in impact["tree_representation"]


def test_targeted_mutations():
    all_mutants = ASTMutator.mutate(SAMPLE_CODE)
    assert len(all_mutants) > 0

    # Target only the line with `age >= 18` (line 12)
    targeted_mutants = ASTMutator.mutate(SAMPLE_CODE, target_lines=[12])
    assert len(targeted_mutants) > 0
    assert len(targeted_mutants) < len(all_mutants)
    for m in targeted_mutants:
        assert m.line_number == 12


def test_git_diff_inspector():
    # Should run safely on current repo without throwing exceptions
    lines = GitDiffInspector.get_modified_lines(repo_path=".")
    assert isinstance(lines, list)


def test_adk_engine_contracts():
    registry = ADKToolRegistry()
    tools = registry.list_tools()
    tool_names = {t.name for t in tools}
    assert "tool_compute_blast_radius" in tool_names
    assert "tool_inspect_git_diff" in tool_names
    assert "tool_execute_sandbox" in tool_names
    assert "tool_ast_audit" in tool_names

    ctx = ADKContext(iteration=1)
    res = registry.execute_tool(
        "tool_compute_blast_radius",
        {"source_code": SAMPLE_CODE, "target_function": "sanitize"},
        context=ctx
    )
    assert res.success is True
    assert res.output["target_function"] == "sanitize"
    assert ctx.active_tool == "tool_compute_blast_radius"
    assert len(ctx.reflection_history) == 1
