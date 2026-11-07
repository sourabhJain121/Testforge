"""
tests/test_adk_production_path.py

Verifies Handout Stage 0.8: ADK Production Orchestrator Path Verification.
Proves that:
1. The pinned `google-adk` version is strictly 1.14.1.
2. Production agents instantiate and bind to `google.adk.runners.Runner` and `google.adk.sessions.SessionService`.
3. The production orchestrator path integrates native Google ADK Runner execution.
"""

import importlib.metadata

import pytest
from google.adk.runners import Runner
from google.adk.sessions import BaseSessionService, InMemorySessionService

from testforge.adk_generator import GoogleADKTestGenerator
from testforge.code_intelligence_agent import CodeIntelligenceAgent
from testforge.execution_agent import TestExecutionAgent
from testforge.orchestrator import TestForgeOrchestrator
from testforge.planning_agent import TestPlanningAgent
from testforge.reflection_agent import ReflectionRepairAgent
from testforge.security_agent import SecurityAgent
from testforge.supervisor_agent import SupervisorAgent


def test_google_adk_pinned_version():
    """Verify that google-adk is pinned to version 1.14.1."""
    ver = importlib.metadata.version("google-adk")
    assert ver == "1.14.1", f"Expected google-adk==1.14.1, but found {ver}"


def test_all_adk_agents_bind_runner_and_session_service():
    """Verify that all core specialist agents instantiate a valid Google ADK Runner and SessionService."""
    agents = [
        ("GoogleADKTestGenerator", GoogleADKTestGenerator(use_live_llm=False)),
        ("SupervisorAgent", SupervisorAgent(use_live_llm=False)),
        ("ReflectionRepairAgent", ReflectionRepairAgent(use_live_llm=False)),
        ("CodeIntelligenceAgent", CodeIntelligenceAgent(use_live_llm=False)),
        ("TestExecutionAgent", TestExecutionAgent(use_live_llm=False)),
        ("SecurityAgent", SecurityAgent(use_live_llm=False)),
        ("TestPlanningAgent", TestPlanningAgent(use_live_llm=False)),
    ]

    for name, agent in agents:
        assert hasattr(agent, "runner"), f"Agent '{name}' missing ADK Runner attribute"
        assert isinstance(agent.runner, Runner), f"Agent '{name}' runner is not an instance of google.adk.runners.Runner"
        assert hasattr(agent.runner, "session_service"), f"Agent '{name}' runner missing session_service"
        assert isinstance(agent.runner.session_service, BaseSessionService), (
            f"Agent '{name}' session_service is not a BaseSessionService"
        )


def test_production_orchestrator_integrates_adk_agents():
    """Verify that TestForgeOrchestrator instantiates Supervisor and Reflection agents with ADK runners."""
    orchestrator = TestForgeOrchestrator(model_name="mock")
    
    assert hasattr(orchestrator, "supervisor"), "Orchestrator missing supervisor attribute"
    assert hasattr(orchestrator, "reflection_agent"), "Orchestrator missing reflection_agent attribute"
    
    assert isinstance(orchestrator.supervisor.runner, Runner), "Orchestrator supervisor is not bound to ADK Runner"
    assert isinstance(orchestrator.reflection_agent.runner, Runner), "Orchestrator reflection_agent is not bound to ADK Runner"
    
    # Check session services
    assert isinstance(orchestrator.supervisor.session_service, BaseSessionService)
    assert isinstance(orchestrator.reflection_agent.session_service, BaseSessionService)
