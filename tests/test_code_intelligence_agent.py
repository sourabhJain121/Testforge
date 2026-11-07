"""
test_code_intelligence_agent.py - Comprehensive Unit Tests for CodeIntelligenceAgent.

Covers:
1. Function and class extraction with arguments, types, and scopes.
2. Branch identification (if, while, for, match) and comparison operators.
3. Exception-path identification (raise, try/except).
4. Dependency extraction (ast.Import, ast.ImportFrom).
5. Invalid Python source handling (SyntaxError).
6. Empty source code handling.
7. Structured output validation against CodeIntelligencePayload.
8. Blackboard publication to TargetSpace and PlanSpace.
9. In-process A2A message exchange via A2ABroker.
"""

import ast
import pytest
from testforge.code_intelligence_agent import CodeIntelligenceAgent, CodeIntelligenceModelBridge
from testforge.a2a import (
    CodeIntelligencePayload,
    A2AMessage,
    A2APerformative,
    A2ABroker,
)
from testforge.blackboard import Blackboard


SAMPLE_PYTHON_CODE = """
import os
import math
from typing import List, Optional

class InventoryManager:
    \"\"\"Manages stock levels and reorder policies.\"\"\"
    def __init__(self, capacity: int = 100):
        self.capacity = capacity
        self.items = {}

    def add_stock(self, item_id: str, quantity: int) -> bool:
        if quantity <= 0:
            raise ValueError("Quantity must be positive.")
        if len(self.items) >= self.capacity:
            return False
        self.items[item_id] = self.items.get(item_id, 0) + quantity
        return True

def calculate_discount(price: float, items: int) -> float:
    \"\"\"Calculates volume discount with boundary rules.\"\"\"
    if items < 0 or price < 0:
        raise ValueError("Invalid negative input")
    if items >= 50:
        return price * 0.70
    elif items >= 10:
        return price * 0.85
    elif items >= 5:
        return price * 0.90
    else:
        return price

def safe_divide(a: float, b: float) -> Optional[float]:
    try:
        return a / b
    except ZeroDivisionError:
        return None
"""


class TestCodeIntelligenceAgent:
    """Tests for Google ADK-powered CodeIntelligenceAgent."""

    def test_function_and_class_extraction(self):
        """1. Verifies that functions, methods, classes, and signatures are extracted accurately."""
        agent = CodeIntelligenceAgent(api_key="test-key")
        payload = agent.analyze_source(SAMPLE_PYTHON_CODE, job_id="job_test_01")

        assert payload.analysis_status == "SUCCESS"
        func_names = [f["name"] for f in payload.functions]
        assert "add_stock" in func_names
        assert "calculate_discount" in func_names
        assert "safe_divide" in func_names

        class_names = [c["name"] for c in payload.classes]
        assert "InventoryManager" in class_names
        cls_info = payload.classes[0]
        assert "add_stock" in cls_info["methods"]
        assert "Manages stock levels" in cls_info["docstring"]

    def test_branch_identification(self):
        """2. Verifies branch conditions, line numbers, operators, and boundary values."""
        agent = CodeIntelligenceAgent(api_key="test-key")
        payload = agent.analyze_source(SAMPLE_PYTHON_CODE, job_id="job_test_02")

        assert len(payload.branches) >= 5
        branch_types = [b["type"] for b in payload.branches]
        assert "if" in branch_types

        # Check boundary constants discovered in calculate_discount
        boundary_vals = []
        for b in payload.branches:
            boundary_vals.extend(b.get("boundary_values", []))

        assert 50 in boundary_vals
        assert 10 in boundary_vals
        assert 5 in boundary_vals
        assert 0 in boundary_vals

    def test_exception_path_identification(self):
        """3. Verifies raise statements and try-except error handling paths."""
        agent = CodeIntelligenceAgent(api_key="test-key")
        payload = agent.analyze_source(SAMPLE_PYTHON_CODE, job_id="job_test_03")

        assert len(payload.exception_paths) >= 2
        exc_types = [p.get("exception_type", "") for p in payload.exception_paths]
        assert any("ValueError" in t for t in exc_types)
        assert any("ZeroDivisionError" in t for t in exc_types)

    def test_dependency_extraction(self):
        """4. Verifies extracted external and standard library imports."""
        agent = CodeIntelligenceAgent(api_key="test-key")
        payload = agent.analyze_source(SAMPLE_PYTHON_CODE, job_id="job_test_04")

        assert "os" in payload.dependencies
        assert "math" in payload.dependencies
        assert "typing" in payload.dependencies

    def test_invalid_python_source(self):
        """5. Verifies graceful handling of invalid Python syntax without crashing."""
        agent = CodeIntelligenceAgent(api_key="test-key")
        bad_code = "def broken_syntax(x:\n    return x +"
        payload = agent.analyze_source(bad_code, job_id="job_test_05")

        assert payload.analysis_status == "SYNTAX_ERROR"
        assert "syntax_error" in payload.evidence
        assert payload.evidence["line_number"] is not None

    def test_empty_source(self):
        """6. Verifies graceful handling of empty source code."""
        agent = CodeIntelligenceAgent(api_key="test-key")
        payload = agent.analyze_source("   \n\t  ", job_id="job_test_06")

        assert payload.analysis_status == "FAILED"
        assert "error" in payload.evidence
        assert len(payload.functions) == 0

    def test_structured_output_validation(self):
        """7. Verifies payload conforms strictly to CodeIntelligencePayload."""
        agent = CodeIntelligenceAgent(api_key="test-key")
        payload = agent.analyze_source(SAMPLE_PYTHON_CODE, job_id="job_test_07")

        assert isinstance(payload, CodeIntelligencePayload)
        assert payload.task_id == "job_test_07"
        assert payload.job_id == "job_test_07"
        assert payload.source_sha != ""
        assert "total_complexity" in payload.complexity_risk
        assert len(payload.suggested_testing_targets) > 0

    def test_blackboard_publication(self):
        """8. Verifies outputs are published to TargetSpace and PlanSpace."""
        bb = Blackboard()
        agent = CodeIntelligenceAgent(api_key="test-key", blackboard=bb)
        payload = agent.analyze_source(SAMPLE_PYTHON_CODE, job_id="job_test_08")

        target_sp = bb.get_target_space()
        assert "calculate_discount" in target_sp.functions
        assert "InventoryManager" in target_sp.classes
        assert len(target_sp.branches) >= 5
        assert target_sp.blast_risk in ("LOW", "MEDIUM", "HIGH")

        plan_sp = bb.get_plan_space()
        assert len(plan_sp.boundary_conditions) > 0
        assert "50" in plan_sp.boundary_conditions or 50 in plan_sp.boundary_conditions

    def test_a2a_communication(self):
        """9. Verifies in-process A2A message request and response via A2ABroker."""
        bb = Blackboard()
        agent = CodeIntelligenceAgent(api_key="test-key", blackboard=bb)
        broker = A2ABroker(blackboard=bb)

        broker.register_handler(
            "agent:google-adk:code-intelligence",
            agent.handle_a2a_message,
            description="Code Intelligence"
        )

        msg = A2AMessage(
            sender="orchestrator",
            recipient="agent:google-adk:code-intelligence",
            performative=A2APerformative.REQUEST,
            action="analyze_code",
            correlation_id="corr_test_a2a",
            payload={"target_source_code": SAMPLE_PYTHON_CODE, "job_id": "job_a2a_09"},
        )

        resp = broker.send_message(msg)
        assert resp.performative == A2APerformative.INFORM
        assert resp.payload["analysis_status"] == "SUCCESS"
        assert len(resp.payload["functions"]) >= 3
        # Blackboard should be synchronized automatically via broker
        target_sp = bb.get_target_space()
        assert "calculate_discount" in target_sp.functions

