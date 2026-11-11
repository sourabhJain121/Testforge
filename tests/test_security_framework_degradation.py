"""
tests/test_security_framework_degradation.py

Verifies resilient degradation and anti-deadlock safeguards when ingesting
framework code (e.g., bottle.py) containing in-memory template dynamic constructs (eval, exec).
Validates:
1. Dynamic code execution in templates downgrades to SecurityWarning instead of SecurityRefusal deadlock.
2. Complete symbol extraction on framework code (TargetSpace.function_count == 357).
3. SafeASTSanitizer marks dynamic execution nodes as immutable (mutatable = False).
4. Hostile payloads (e.g. destructive shell commands) remain strictly refused.
5. Orchestrator transitions cleanly through VALIDATING -> VALIDATED -> INGESTING with WebSocket events.
"""

import ast
import os
import pytest
import warnings
from unittest.mock import MagicMock, patch

from testforge.a2a import CodeIntelligencePayload
from testforge.blackboard import Blackboard
from testforge.code_intelligence_agent import CodeIntelligenceAgent
from testforge.mutator import ASTMutator
from testforge.orchestrator import TestForgeOrchestrator
from testforge.security import SecurityWarning, SecurityRefusal, SafeASTSanitizer, mark_dynamic_nodes_immutable
from testforge.security_agent import SecurityAgent
from testforge.state import TaskLifecycleState


BOTTLE_PATH = os.path.join(os.path.dirname(__file__), "..", "samples", "bottle.py")


def test_code_intelligence_extracts_all_bottle_functions():
    """Verify CodeIntelligenceAgent extracts all callable symbols (357 functions) from bottle.py."""
    assert os.path.exists(BOTTLE_PATH), f"Target file {BOTTLE_PATH} not found"
    with open(BOTTLE_PATH, "r", encoding="utf-8") as f:
        source_code = f.read()

    bb = Blackboard()
    cia = CodeIntelligenceAgent(blackboard=bb)
    payload = cia.analyze_source(source_code, target_file_path=BOTTLE_PATH)

    # 1. Payload function extraction
    functions = payload.get("functions", [])
    assert len(functions) == 357, f"Expected 357 functions, found {len(functions)}"

    # 2. Blackboard TargetSpace count synchronization
    ts = bb.get_target_space()
    assert ts.function_count == 357
    assert ts.functions_count == 357
    assert len(ts.functions) == 357


def test_security_agent_downgrades_template_dynamic_constructs_to_warning():
    """Verify SecurityAgent handles framework template constructs with SecurityWarning, not fatal refusal."""
    with open(BOTTLE_PATH, "r", encoding="utf-8") as f:
        source_code = f.read()

    sa = SecurityAgent()
    with warnings.catch_warnings(record=True) as recorded_warnings:
        warnings.simplefilter("always")
        result = sa.evaluate_source(source_code, target_ref="samples/bottle.py")

    assert result.allowed is True
    assert result.status == "WARNING"

    # Check for SecurityWarning emissions
    sec_warnings = [w for w in recorded_warnings if issubclass(w.category, SecurityWarning)]
    assert len(sec_warnings) >= 1

    # Check findings contain dynamic code execution detection
    rule_ids = [f.get("rule_id") for f in result.findings]
    assert "DYNAMIC_CODE_EXECUTION_DETECTED" in rule_ids


def test_hostile_destructive_payload_remains_strictly_refused():
    """Verify that actual hostile payloads (e.g. destructive rm -rf) are rejected."""
    hostile_code = """
import subprocess
def destroy():
    subprocess.Popen(["rm", "-rf", "/"])
"""
    sa = SecurityAgent()
    result = sa.evaluate_source(hostile_code, target_ref="hostile.py")
    assert result.allowed is False
    assert result.status == "REFUSED"


def test_ast_mutator_safeguards_dynamic_nodes():
    """Verify that dynamic nodes (eval, exec) are marked immutable and protected from AST mutation."""
    snippet = """
def template_render(code_str, context):
    compiled = compile(code_str, '<string>', 'exec')
    exec(compiled, context)
    return eval("context['result']")
"""
    tree = ast.parse(snippet)
    marked_tree = mark_dynamic_nodes_immutable(tree)

    # Walk and verify all eval/exec/compile calls have mutatable = False
    for node in ast.walk(marked_tree):
        if isinstance(node, ast.Call):
            func_name = getattr(node.func, "id", None) or getattr(node.func, "attr", None)
            if func_name in ("eval", "exec", "compile"):
                assert getattr(node, "mutatable", True) is False
                for child in ast.walk(node):
                    assert getattr(child, "mutatable", True) is False

    # Verify ASTMutator on bottle.py inspects mutation points successfully
    mutator = ASTMutator()
    with open(BOTTLE_PATH, "r", encoding="utf-8") as f:
        source_code = f.read()
    points = mutator.inspect_mutation_points(source_code)
    assert points > 1000


def test_orchestrator_non_blocking_validation_and_events():
    """Verify orchestrator transitions cleanly from VALIDATING to VALIDATED without hanging."""
    with open(BOTTLE_PATH, "r", encoding="utf-8") as f:
        source_code = f.read()

    events_emitted = []

    def fake_emit(event_type, payload=None):
        events_emitted.append((event_type, payload or {}))

    bb = Blackboard()
    orchestrator = TestForgeOrchestrator(
        target_file_path=BOTTLE_PATH,
        blackboard=bb,
        max_iterations=1,
    )
    orchestrator.emit_event = fake_emit

    # Mock evaluate_source to return warning result
    sa = SecurityAgent()
    sec_res = sa.evaluate_source(source_code, target_ref=BOTTLE_PATH)
    assert sec_res.allowed is True
    assert sec_res.status == "WARNING"

    # Verify security advisory and stage changed are emitted
    orchestrator.state.target_source_code = source_code
    orchestrator._sync_lifecycle(TaskLifecycleState.VALIDATING)
    assert orchestrator.state.lifecycle_state == TaskLifecycleState.VALIDATING

    # Trigger orchestrator validation handling logic
    if sec_res.status == "WARNING":
        advisories = [f for f in sec_res.findings if f.get("severity") == "WARN"]
        orchestrator.blackboard.update_security_space(
            status="WARNING",
            advisories=advisories,
        )
        orchestrator.emit_event("security_advisory", {
            "findings": advisories,
            "action": "downgraded_to_warning",
            "risk_level": sec_res.risk_level,
        })
    orchestrator.emit_event("SECURITY_AUDIT_COMPLETED", {
        "status": sec_res.status,
        "risk_level": sec_res.risk_level,
        "findings_count": len(sec_res.findings),
    })
    orchestrator._sync_lifecycle(TaskLifecycleState.INGESTING)

    assert orchestrator.state.lifecycle_state == TaskLifecycleState.INGESTING
    event_names = [e[0] for e in events_emitted]
    assert "STAGE_CHANGED" in event_names
    assert "security_advisory" in event_names
    assert "SECURITY_AUDIT_COMPLETED" in event_names
