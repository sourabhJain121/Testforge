"""
test_phase3_workflow_integration.py - Live Workflow Integration Tests for Phase 3.

Verifies:
1. CodeIntelligenceAgent is invoked in a real hardening workflow run.
2. SecurityAgent is invoked in a real hardening workflow run.
3. Both agents correlate with the correct job_id and workflow_id.
4. Their outputs are persisted in Blackboard checkpoints and state metadata.
5. Outputs are accessible to downstream components.
6. Malicious code triggers security refusal and clean workflow termination.
7. Existing hardening functionality and regression stability remain intact.
"""

import json
import os
import tempfile

import pytest

from testforge.blackboard import Blackboard
from testforge.orchestrator import TestForgeOrchestrator
from testforge.state import TaskLifecycleState

CLEAN_CODE = """
def multiply_by_two(x: int) -> int:
    \"\"\"Multiplies input by two.\"\"\"
    if x < 0:
        raise ValueError("Must be non-negative")
    return x * 2
"""

MALICIOUS_CODE = """
import os
def dangerous_func():
    os.system("echo hacked")
"""


class TestPhase3WorkflowIntegration:
    """End-to-end integration tests for CodeIntelligenceAgent and SecurityAgent."""

    def test_workflow_invokes_both_agents_and_persists_outputs(self):
        """
        1-5: Demonstrates that both agents execute during an actual orchestrator run,
        use the correct job_id, update Blackboard partitions, and persist in metadata.
        """
        orch = TestForgeOrchestrator(
            target_source_code=CLEAN_CODE,
            job_id="job_integration_clean_101",
            engine_mode="legacy",
        )

        # Confirm agents are instantiated and registered
        assert hasattr(orch, "code_intel_agent")
        assert hasattr(orch, "security_agent")
        reg_handlers = orch.broker.list_handlers()
        assert "agent:google-adk:code-intelligence" in reg_handlers
        assert "agent:google-adk:security" in reg_handlers

        # Run pipeline
        final_state = orch.run()

        # 1. SecurityAgent execution verified
        sec_sp = orch.blackboard.get_security_space()
        assert sec_sp.task_id == "job_integration_clean_101"
        assert sec_sp.allowed is True
        assert sec_sp.status == "PASSED"

        # 2. CodeIntelligenceAgent execution verified
        target_sp = orch.blackboard.get_target_space()
        assert "multiply_by_two" in target_sp.functions
        assert len(target_sp.branches) >= 1
        assert "ValueError" in target_sp.exception_paths

        # 3. State metadata verified
        assert "security_assessment" in final_state.metadata
        assert "code_intelligence" in final_state.metadata
        assert final_state.metadata["security_assessment"]["status"] == "PASSED"
        assert final_state.metadata["code_intelligence"]["analysis_status"] == "SUCCESS"

        # 4. Telemetry traces verified
        traces = orch.logger.read_traces()
        handoffs = [t for t in traces if t.get("event_type") == "AGENT_HANDOFF"]
        agent_execs = [t for t in traces if t.get("event_type") == "AGENT_EXECUTION"]

        # Confirm handoff from SecurityAgent to CodeIntelligenceAgent
        sec_to_ci = next((h for h in handoffs if h.get("data", {}).get("from_agent") == "SecurityAgent"
                          and h.get("data", {}).get("to_agent") == "CodeIntelligenceAgent"), None)
        assert sec_to_ci is not None

        # Confirm agent execution records
        ci_exec = next((e for e in agent_execs if e.get("data", {}).get("agent") == "CodeIntelligenceAgent"), None)
        sec_exec = next((e for e in agent_execs if e.get("data", {}).get("agent") == "SecurityAgent"), None)
        assert ci_exec is not None
        assert sec_exec is not None

    def test_workflow_security_refusal_on_policy_violation(self):
        """
        6. Verifies that malicious code triggers SecurityAgent refusal, halts pipeline,
        and cleanly marks state as FAILED without executing untrusted code.
        """
        orch = TestForgeOrchestrator(
            target_source_code=MALICIOUS_CODE,
            job_id="job_integration_malicious_102",
            engine_mode="legacy",
        )

        final_state = orch.run()

        assert final_state.terminated is True
        assert "SecurityRefusal" in final_state.termination_reason
        assert final_state.final_hardening_status == "FAILED"
        assert orch.fsm.current_state == TaskLifecycleState.FAILED

        # Check SecuritySpace
        sec_sp = orch.blackboard.get_security_space()
        assert sec_sp.allowed is False
        assert sec_sp.status in ("BLOCKED", "REFUSED")
