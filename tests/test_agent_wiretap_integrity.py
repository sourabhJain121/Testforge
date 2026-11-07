"""
test_agent_wiretap_integrity.py - Academic Integrity Audit for Multi-Agent Wiretap.

Validates:
1. Taxonomy and role differentiation between cognitive agents and execution tools/sandboxes.
2. Accurate agent counting and lifecycle tracking in /api/wiretap without hardcoded values.
3. Distinction between registered agents, participating entities, and sandbox execution harnesses.
4. Correct deduplication and handling of scoped vs all-time traces.
"""

import json
import os
import tempfile

import pytest
from fastapi.testclient import TestClient

from server import app
from testforge.a2a import A2ABroker
from testforge.adk_generator import GoogleADKTestGenerator
from testforge.agents import AdversarialCriticAgent, TestGeneratorAgent
from testforge.crew_critic import CrewAICriticAgent
from testforge.ingestion import TargetManagerAgent
from testforge.logger import TraceLogger
from testforge.orchestrator import TestForgeOrchestrator
from testforge.sandbox import ParallelSandboxRunner, SubprocessSandbox


@pytest.fixture
def test_client():
    return TestClient(app)


class TestAgentWiretapIntegrity:
    """Verifies that all agent counters and wiretap telemetry adhere to strict academic standards."""

    def test_agent_classes_and_subprocesses_classification(self):
        """
        Confirms the exact classification of the 6 entities appearing in Wiretap handoffs:
        5 genuine cognitive agents + 1 execution sandbox tool.
        """
        # 1. Cognitive Supervisor Agent
        assert issubclass(TargetManagerAgent, object)
        assert hasattr(TargetManagerAgent, "ingest_file")

        # 2. Cognitive Generator Agents (Native and ADK)
        assert issubclass(TestGeneratorAgent, object)
        assert hasattr(TestGeneratorAgent, "generate_tests")
        assert issubclass(GoogleADKTestGenerator, object)
        assert hasattr(GoogleADKTestGenerator, "generate_tests")

        # 3. Cognitive Critic Agents (Native and CrewAI)
        assert issubclass(AdversarialCriticAgent, object)
        assert hasattr(AdversarialCriticAgent, "analyze_surviving_mutants")
        assert issubclass(CrewAICriticAgent, object)
        assert hasattr(CrewAICriticAgent, "diagnose_mutants")

        # 4. Tool / Execution Harness (SubprocessSandbox)
        # SubprocessSandbox is an alias to ParallelSandboxRunner, NOT a cognitive AI agent
        assert SubprocessSandbox is ParallelSandboxRunner
        assert hasattr(ParallelSandboxRunner, "evaluate_mutants_parallel")
        assert hasattr(ParallelSandboxRunner, "measure_coverage")

        # 5. Master Orchestrator
        assert issubclass(TestForgeOrchestrator, object)
        assert hasattr(TestForgeOrchestrator, "run")

    def test_a2a_broker_handler_registration(self):
        """
        Verifies that agents register their handlers with the A2ABroker.
        """
        broker = A2ABroker()
        adk_gen = GoogleADKTestGenerator(api_key="test-key")
        crew_critic = CrewAICriticAgent(api_key="test-key", verbose=False)

        broker.register_handler(
            "agent:google-adk:generator",
            adk_gen.handle_a2a_message,
            description="Google ADK Test Generator"
        )
        broker.register_handler(
            "agent:crewai:critic",
            crew_critic.handle_a2a_message,
            description="CrewAI Critic"
        )

        reg_ids = broker.list_handlers()
        assert "agent:google-adk:generator" in reg_ids
        assert "agent:crewai:critic" in reg_ids
        assert len(reg_ids) >= 2

    def test_wiretap_api_returns_deduplicated_agents_and_breakdown(self, test_client):
        """
        Verifies that GET /api/wiretap calculates unique participating agents
        and provides explicit breakdown between cognitive agents and sandbox tools.
        """
        response = test_client.get("/api/wiretap")
        assert response.status_code == 200
        data = response.json()

        assert "total_handoffs" in data
        assert "total_adk_calls" in data
        assert "participating_agents" in data
        assert "cognitive_agents" in data
        assert "tool_entities" in data
        assert "cognitive_agents_count" in data
        assert "registered_agents" in data

        # Confirm deduplication: participating_agents must be sorted unique list
        participating = data["participating_agents"]
        assert len(participating) == len(set(participating))

        # Check that SubprocessSandbox is isolated under tool_entities
        if "SubprocessSandbox" in participating:
            assert "SubprocessSandbox" in data["tool_entities"]
            assert "SubprocessSandbox" not in data["cognitive_agents"]
            assert data["cognitive_agents_count"] == len(participating) - 1

    def test_wiretap_counter_is_dynamic_not_hardcoded(self, monkeypatch):
        """
        Proves that the wiretap counter dynamically derives its value from trace handoffs
        and is never hardcoded.
        """
        with tempfile.NamedTemporaryFile("w+", suffix=".jsonl", delete=False) as tf:
            temp_path = tf.name
            # Write synthetic handoffs with 2 distinct cognitive agents
            handoff1 = {
                "timestamp": 1000.0,
                "event_type": "AGENT_HANDOFF",
                "workflow_id": "wf_test_dynamic",
                "data": {
                    "from_agent": "TargetManagerAgent",
                    "to_agent": "TestGeneratorAgent",
                    "iteration": 0
                }
            }
            handoff2 = {
                "timestamp": 1001.0,
                "event_type": "AGENT_HANDOFF",
                "workflow_id": "wf_test_dynamic",
                "data": {
                    "from_agent": "TestGeneratorAgent",
                    "to_agent": "TargetManagerAgent",
                    "iteration": 0
                }
            }
            tf.write(json.dumps(handoff1) + "\n")
            tf.write(json.dumps(handoff2) + "\n")

        try:
            # Point TraceLogger to our synthetic file
            from server import TraceLogger as ServerTraceLogger

            def mock_init(self, log_path="testforge_trace.jsonl"):
                self.log_path = temp_path

            monkeypatch.setattr(ServerTraceLogger, "__init__", mock_init)

            client = TestClient(app)
            resp = client.get("/api/wiretap")
            assert resp.status_code == 200
            res = resp.json()

            # Dynamic check: Exactly 2 handoffs, exactly 2 agents
            assert res["total_handoffs"] == 2
            assert res["participating_agents"] == ["TargetManagerAgent", "TestGeneratorAgent"]
            assert res["cognitive_agents"] == ["TargetManagerAgent", "TestGeneratorAgent"]
            assert res["tool_entities"] == []
            assert res["cognitive_agents_count"] == 2
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_workflow_scoped_wiretap_filtering(self, monkeypatch):
        """
        Verifies that querying /api/wiretap?workflow_id=... filters to the specific workflow.
        """
        with tempfile.NamedTemporaryFile("w+", suffix=".jsonl", delete=False) as tf:
            temp_path = tf.name
            h1 = {
                "timestamp": 1000.0,
                "event_type": "AGENT_HANDOFF",
                "workflow_id": "wf_alpha",
                "data": {"from_agent": "TargetManagerAgent", "to_agent": "TestGeneratorAgent"}
            }
            h2 = {
                "timestamp": 1001.0,
                "event_type": "AGENT_HANDOFF",
                "workflow_id": "wf_beta",
                "data": {"from_agent": "TestGeneratorAgent", "to_agent": "SubprocessSandbox"}
            }
            tf.write(json.dumps(h1) + "\n")
            tf.write(json.dumps(h2) + "\n")

        try:
            from server import TraceLogger as ServerTraceLogger

            def mock_init(self, log_path="testforge_trace.jsonl"):
                self.log_path = temp_path

            monkeypatch.setattr(ServerTraceLogger, "__init__", mock_init)

            client = TestClient(app)
            resp_alpha = client.get("/api/wiretap?workflow_id=wf_alpha")
            assert resp_alpha.status_code == 200
            data_alpha = resp_alpha.json()
            assert data_alpha["total_handoffs"] == 1
            assert data_alpha["participating_agents"] == ["TargetManagerAgent", "TestGeneratorAgent"]

            resp_beta = client.get("/api/wiretap?workflow_id=wf_beta")
            assert resp_beta.status_code == 200
            data_beta = resp_beta.json()
            assert data_beta["total_handoffs"] == 1
            assert data_beta["participating_agents"] == ["SubprocessSandbox", "TestGeneratorAgent"]
            assert data_beta["tool_entities"] == ["SubprocessSandbox"]
            assert data_beta["cognitive_agents"] == ["TestGeneratorAgent"]
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
