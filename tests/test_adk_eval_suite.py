"""
tests/test_adk_eval_suite.py

Verification tests for Stage 1.7: Google ADK Evaluation Suite.
Verifies:
  1. evals/planner_eval.evalset.json and evals/generator_eval.evalset.json exist and are valid ADK EvalSet JSON.
  2. qa_artifacts/ADK_EVAL_RESULTS.json exists and records both TestPlanningAgent and GoogleADKTestGenerator.
  3. Macro average tool trajectory and response match scores are >= 90%.
  4. docs/ADK_EVAL_REPORT.md exists and is populated.
"""

import json
from pathlib import Path
import pytest


def test_evalset_files_valid_adk_format():
    planner_eval = Path("evals/planner_eval.evalset.json")
    generator_eval = Path("evals/generator_eval.evalset.json")

    assert planner_eval.exists()
    assert generator_eval.exists()

    with open(planner_eval, "r", encoding="utf-8") as f:
        p_data = json.load(f)
    assert p_data["eval_set_id"] == "testforge_planner_eval"
    assert len(p_data["eval_cases"]) >= 3

    with open(generator_eval, "r", encoding="utf-8") as f:
        g_data = json.load(f)
    assert g_data["eval_set_id"] == "testforge_generator_eval"
    assert len(g_data["eval_cases"]) >= 2


def test_adk_eval_results_json():
    path = Path("qa_artifacts/ADK_EVAL_RESULTS.json")
    assert path.exists()

    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert "metadata" in data
    assert "summary" in data
    assert data["summary"]["macro_avg_tool_trajectory_score"] >= 0.9
    assert data["summary"]["macro_avg_response_match_score"] >= 0.9

    agents = data["agents"]
    assert "TestPlanningAgent" in agents
    assert "GoogleADKTestGenerator" in agents

    assert agents["TestPlanningAgent"]["mean_tool_trajectory_score"] >= 0.9
    assert agents["GoogleADKTestGenerator"]["mean_response_match_score"] >= 0.9


def test_adk_eval_documentation():
    path = Path("docs/ADK_EVAL_REPORT.md")
    assert path.exists()
    content = path.read_text(encoding="utf-8")
    assert "Google ADK Evaluation Report" in content
    assert "TestPlanningAgent" in content
    assert "GoogleADKTestGenerator" in content
    assert len(content) > 1000
