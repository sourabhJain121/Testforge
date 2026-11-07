"""
tests/test_adk_callbacks.py

Unit test suite verifying Google ADK lifecycle callbacks (Sub-Task 3.2):
- before_model_callback: Secret and PII sanitization.
- after_model_callback: AST syntax validation.
- before_tool_callback: Path containment policy and sensitive file guards.
- before_agent_callback: Iteration, token, and cost budget guards.
"""

import pytest

from testforge.adk_callbacks import (
    ADKSecurityPolicy,
    adk_after_model_callback,
    adk_before_agent_callback,
    adk_before_model_callback,
    adk_before_tool_callback,
)


class TestADKModelCallbacks:
    def test_before_model_callback_redacts_api_keys_and_pii(self):
        prompt = (
            "Analyze module with key AIzaSyD9x829182390123812038102938102938 "
            "contact admin@enterprise.corp or user sk-1234567890abcdef1234567890."
        )
        sanitized = adk_before_model_callback(prompt)
        assert "AIzaSy" not in sanitized
        assert "admin@enterprise.corp" not in sanitized
        assert "[REDACTED_API_KEY]" in sanitized
        assert "[REDACTED_PII_EMAIL]" in sanitized

    def test_after_model_callback_validates_ast_syntax(self):
        valid_code = "def test_nominal():\n    assert 1 + 1 == 2\n"
        assert adk_after_model_callback(valid_code) == valid_code

        invalid_code = "def test_broken(:\n    assert 1 + \n"
        with pytest.raises(ValueError, match="invalid Python syntax"):
            adk_after_model_callback(invalid_code)


class TestADKToolCallbacks:
    def test_before_tool_callback_allows_safe_path(self):
        status, err = adk_before_tool_callback("read_file", {"path": "samples/discount.py"})
        assert status is True
        assert err is None

    def test_before_tool_callback_blocks_directory_traversal(self):
        with pytest.raises(PermissionError, match="Directory traversal"):
            adk_before_tool_callback("read_file", {"path": "../../etc/shadow"})

    def test_before_tool_callback_blocks_sensitive_files(self):
        with pytest.raises(PermissionError, match="sensitive file"):
            adk_before_tool_callback("read_file", {"path": ".env"})

        with pytest.raises(PermissionError, match="sensitive file"):
            adk_before_tool_callback("cat_file", {"file_path": "certs/id_rsa"})

    def test_before_tool_callback_blocks_system_prefixes(self):
        with pytest.raises(PermissionError, match="system directory"):
            adk_before_tool_callback("inspect_file", {"path": "/etc/passwd"})

    def test_before_tool_callback_runner_protocol(self):
        class MockTool:
            name = "file_reader"

        mock_tool = MockTool()
        mock_ctx = object()

        # Safe input returns tool_input
        safe_input = {"path": "samples/discount.py"}
        res = adk_before_tool_callback(mock_ctx, mock_tool, safe_input)
        assert res == safe_input

        # Unsafe input raises PermissionError
        unsafe_input = {"path": "/root/.ssh/id_rsa"}
        with pytest.raises(PermissionError):
            adk_before_tool_callback(mock_ctx, mock_tool, unsafe_input)


class TestADKAgentCallbacks:
    def test_before_agent_callback_allows_within_budget(self):
        state = {"iteration": 1, "tokens_consumed": 1500, "cost_usd": 0.05}
        status, err = adk_before_agent_callback("GoogleADKTestGenerator", {}, state)
        assert status is True
        assert err is None

    def test_before_agent_callback_aborts_on_max_iterations(self):
        policy = ADKSecurityPolicy(max_iterations=3)
        state = {"iteration": 3, "tokens_consumed": 1000, "cost_usd": 0.01}
        with pytest.raises(RuntimeError, match="Maximum iteration limit"):
            adk_before_agent_callback("ReflectionRepairAgent", {}, state, policy=policy)

    def test_before_agent_callback_aborts_on_token_budget_exceeded(self):
        policy = ADKSecurityPolicy(max_token_budget=10_000)
        state = {"iteration": 1, "tokens_consumed": 10_500, "cost_usd": 0.02}
        with pytest.raises(RuntimeError, match="Token budget limit"):
            adk_before_agent_callback("GoogleADKTestGenerator", {}, state, policy=policy)

    def test_before_agent_callback_aborts_on_cost_ceiling_exceeded(self):
        policy = ADKSecurityPolicy(max_cost_usd=1.0)
        state = {"iteration": 1, "tokens_consumed": 5000, "cost_usd": 1.25}
        with pytest.raises(RuntimeError, match="Cost ceiling"):
            adk_before_agent_callback("GoogleADKTestGenerator", {}, state, policy=policy)

    def test_before_agent_callback_runner_protocol(self):
        class MockAgent:
            name = "SupervisorAgent"

        class MockContext:
            state = {"iteration": 0, "tokens_consumed": 100, "cost_usd": 0.001}

        agent = MockAgent()
        ctx = MockContext()

        # Allowed returns agent
        res = adk_before_agent_callback(ctx, agent)
        assert res == agent

        # Exceeded iteration raises RuntimeError
        ctx.state["iteration"] = 10
        with pytest.raises(RuntimeError, match="Maximum iteration limit"):
            adk_before_agent_callback(ctx, agent)
