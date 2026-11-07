"""
tests/test_adk_workflow_constructs.py

Automated test suite verifying Handout Feature F4:
Native Google ADK Workflow and Structural Primitives.
Tests ADKParallelAnalysisAgent, ADKLoopReflectionAgent,
ADK Lifecycle Callbacks, and ADKBlackboardSessionBridge.
"""

import pytest
from testforge.adk_workflow_agents import (
    ADKParallelAnalysisAgent,
    ADKLoopReflectionAgent,
    ParallelAnalysisResult,
    LoopReflectionResult,
)
from testforge.adk_callbacks import (
    adk_before_model_callback,
    adk_after_model_callback,
    redact_secrets_and_pii,
    validate_python_syntax,
)
from testforge.adk_session_bridge import ADKBlackboardSessionBridge
from testforge.blackboard import Blackboard
from testforge.security_agent import SecurityAgent
from testforge.code_intelligence_agent import CodeIntelligenceAgent


class TestADKParallelAnalysisAgent:
    def test_parallel_analysis_safe_code(self):
        agent = ADKParallelAnalysisAgent()
        safe_code = (
            "def calculate_total(price: float, tax: float) -> float:\n"
            "    return price * (1.0 + tax)\n\n"
            "class InvoiceCalculator:\n"
            "    def compute_net(self, amount: float) -> float:\n"
            "        return amount * 0.9\n"
        )

        res: ParallelAnalysisResult = agent.run_parallel_analysis(
            source_code=safe_code,
            task_id="test_safe_01",
        )

        assert isinstance(res, ParallelAnalysisResult)
        assert res.status == "PASSED"
        assert res.allowed is True
        assert res.risk_level == "SAFE"
        assert "calculate_total" in res.callables
        assert "InvoiceCalculator" in res.callables
        assert res.security_payload is not None
        assert res.code_intel_payload is not None
        assert res.execution_time >= 0.0

    def test_parallel_analysis_security_refusal(self):
        agent = ADKParallelAnalysisAgent()
        # Code containing dangerous eval primitive that triggers security gatekeeping
        unsafe_code = (
            "import os\n"
            "def run_command(cmd: str):\n"
            "    eval('__import__(\"os\").system(\"rm -rf /\")')\n"
        )

        res: ParallelAnalysisResult = agent.run_parallel_analysis(
            source_code=unsafe_code,
            task_id="test_unsafe_01",
            enforce_security=True,
        )

        assert isinstance(res, ParallelAnalysisResult)
        assert res.status == "REFUSED"
        assert res.allowed is False
        assert res.refusal_reason is not None
        assert "Security Gatekeeping Refusal" in res.refusal_reason
        assert res.callables == []


class TestADKLoopReflectionAgent:
    def test_reflection_loop_terminates_on_convergence(self):
        agent = ADKLoopReflectionAgent(max_iterations=3, target_score=80.0)
        target_code = "def add(a, b): return a + b\n"
        initial_tests = "def test_add(): assert add(1, 2) == 3\n"
        mutants = [
            {"mutant_id": "M1", "status": "KILLED", "operator": "ARITH"},
            {"mutant_id": "M2", "status": "KILLED", "operator": "ARITH"},
        ]

        res: LoopReflectionResult = agent.run_reflection_loop(
            target_code=target_code,
            initial_test_code=initial_tests,
            mutants=mutants,
            target_score=80.0,
            max_iterations=3,
        )

        assert isinstance(res, LoopReflectionResult)
        assert res.converged is True
        assert res.final_score >= 80.0
        assert "CONVERGENCE_TARGET_ACHIEVED" in res.stop_reason or "ALL_MUTANTS_KILLED" in res.stop_reason
        assert len(res.telemetry) >= 1
        assert res.iterations_executed <= 3

    def test_reflection_loop_terminates_on_max_iterations(self):
        agent = ADKLoopReflectionAgent(max_iterations=2, target_score=95.0)
        target_code = "def multiply(a, b): return a * b\n"
        initial_tests = "def test_mult(): assert multiply(2, 3) == 6\n"
        mutants = [
            {"mutant_id": f"M{i}", "status": "SURVIVED", "operator": "OP"}
            for i in range(10)
        ]

        res: LoopReflectionResult = agent.run_reflection_loop(
            target_code=target_code,
            initial_test_code=initial_tests,
            mutants=mutants,
            target_score=95.0,
            max_iterations=2,
        )

        assert isinstance(res, LoopReflectionResult)
        assert res.converged is False
        assert res.iterations_executed == 2
        assert "MAX_ITERATIONS_REACHED" in res.stop_reason
        assert len(res.telemetry) == 2


class TestADKCallbacks:
    def test_before_model_callback_redacts_api_keys_and_pii(self):
        dirty_prompt = (
            "Analyze target with key AIzaSyA1234567890abcdefghijklmnopqrstuv and "
            "contact developer at admin@testforge.internal. Also token: ghp_1234567890abcdefghijklmn."
        )

        sanitized = adk_before_model_callback(dirty_prompt)
        assert "AIzaSy" not in sanitized
        assert "[REDACTED_API_KEY]" in sanitized
        assert "admin@testforge.internal" not in sanitized
        assert "[REDACTED_PII_EMAIL]" in sanitized
        assert "ghp_12345" not in sanitized

    def test_after_model_callback_validates_syntax(self):
        valid_code = (
            "import pytest\n"
            "def test_valid_case():\n"
            "    assert 1 + 1 == 2\n"
        )
        assert adk_after_model_callback(valid_code) == valid_code

        invalid_code = (
            "def test_broken_syntax(\n"
            "    assert missing closing paren and syntax error\n"
        )
        with pytest.raises(ValueError, match="invalid Python syntax"):
            adk_after_model_callback(invalid_code)


class TestADKBlackboardSessionBridge:
    def test_blackboard_to_session_synchronization(self):
        bb = Blackboard()
        bb.update_target_space(
            target_file_path="/samples/calc.py",
            target_source_code="def calc(): pass",
            source_sha="abcdef1234567890",
        )
        bb.update_metrics_space(
            final_mutation_score=78.5,
            branch_coverage=82.0,
            max_iterations=4,
            target_mutation_score=90.0,
        )
        bb.update_critic_space(
            latest_directive="Probe boundary threshold 100",
            critic_directives=["Probe boundary threshold 100"],
        )

        bridge = ADKBlackboardSessionBridge(blackboard=bb)
        session = bridge.sync_blackboard_to_session("session_unit_01")

        # Verify scoped keys
        assert session.state["app:target_path"] == "/samples/calc.py"
        assert session.state["app:sha256_hash"] == "abcdef1234567890"
        assert session.state["app:mutation_score"] == 78.5
        assert session.state["app:branch_coverage"] == 82.0
        assert session.state["user:config_iterations"] == 4
        assert session.state["user:target_score"] == 90.0
        assert session.state["temp:latest_critique_directives"] == "Probe boundary threshold 100"

    def test_session_to_blackboard_synchronization(self):
        bb = Blackboard()
        bridge = ADKBlackboardSessionBridge(blackboard=bb)

        bridge.set_scoped("app:mutation_score", 95.0, "session_unit_02")
        bridge.set_scoped("app:branch_coverage", 88.0, "session_unit_02")
        bridge.set_scoped("user:config_iterations", 5, "session_unit_02")
        bridge.set_scoped("user:target_score", 92.0, "session_unit_02")
        bridge.set_scoped("temp:latest_critique_directives", "Tighten boundary equality", "session_unit_02")

        bridge.sync_session_to_blackboard("session_unit_02")

        metrics = bb.get_metrics_space()
        critic = bb.get_critic_space()

        assert metrics.final_mutation_score == 95.0
        assert metrics.branch_coverage == 88.0
        assert metrics.max_iterations == 5
        assert metrics.target_mutation_score == 92.0
        assert critic.latest_directive == "Tighten boundary equality"
        assert "Tighten boundary equality" in critic.critic_directives


class TestADKNativenessAndRunnerIntegration:
    """Verifies genuine Google ADK class inheritance and Runner session execution."""

    def test_native_agent_class_inheritance(self):
        from google.adk.agents.base_agent import BaseAgent
        from google.adk.agents.parallel_agent import ParallelAgent
        from google.adk.agents.loop_agent import LoopAgent
        from google.adk.agents.llm_agent import LlmAgent
        from testforge.adk_generator import GoogleADKTestGenerator
        from testforge.supervisor_agent import SupervisorAgent
        from testforge.code_intelligence_agent import CodeIntelligenceAgent

        par_agent = ADKParallelAnalysisAgent()
        assert isinstance(par_agent, ParallelAgent)
        assert isinstance(par_agent, BaseAgent)

        loop_agent = ADKLoopReflectionAgent(max_iterations=2, target_score=90.0)
        assert isinstance(loop_agent, LoopAgent)
        assert isinstance(loop_agent, BaseAgent)

        gen = GoogleADKTestGenerator()
        assert isinstance(gen.adk_agent, LlmAgent)
        assert isinstance(gen.adk_agent, BaseAgent)

        sup = SupervisorAgent()
        assert isinstance(sup.adk_agent, LlmAgent)
        assert isinstance(sup.adk_agent, BaseAgent)

        code_intel = CodeIntelligenceAgent()
        assert isinstance(code_intel.adk_agent, LlmAgent)
        assert isinstance(code_intel.adk_agent, BaseAgent)

    def test_native_runner_pipeline_execution_and_session_state(self):
        import asyncio
        from google.adk.runners import Runner
        from google.adk.sessions.in_memory_session_service import InMemorySessionService
        from google.genai import types

        async def _run_test():
            par_agent = ADKParallelAnalysisAgent()
            session_service = InMemorySessionService()
            runner = Runner(agent=par_agent, session_service=session_service, app_name="testforge_integration")

            test_code = "def add(x: int, y: int) -> int:\n    return x + y\n"
            session = await session_service.create_session(
                app_name="testforge_integration",
                user_id="test_qa",
                state={"app:source_code": test_code, "app:job_id": "job_int_01"},
            )

            user_message = types.Content(role="user", parts=[types.Part(text="analyze_target")])
            events = []
            async for event in runner.run_async(
                user_id="test_qa",
                session_id=session.id,
                new_message=user_message,
            ):
                events.append(event)

            assert len(events) >= 2
            updated_session = await session_service.get_session(
                app_name="testforge_integration",
                user_id="test_qa",
                session_id=session.id,
            )

            assert updated_session.state.get("app:security_allowed") is True
            assert updated_session.state.get("app:security_risk") == "SAFE"
            callables = updated_session.state.get("app:discovered_callables", [])
            assert "add" in callables

        asyncio.run(_run_test())

