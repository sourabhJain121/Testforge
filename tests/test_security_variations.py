"""
tests/test_security_variations.py - Automated Regression Suite for Security Guardrails & Prompt Variations.

Verifies:
  1. PromptStrategy generation (ZERO_SHOT, FEW_SHOT, REACT)
  2. DeveloperPersona context injection (BEGINNER, EXPERIENCED, QA_ENGINEER, SECURITY_CONSCIOUS)
  3. ReAct Thought/Action/Observation structural validation
  4. Few-shot exemplar inclusion and guidance
  5. 10 Security Scenarios across all strategy x persona combinations
  6. Attack detection rate, safe acceptance rate, and zero false positives on benign requests
"""

import ast
from typing import Any, Dict

import pytest

from testforge.prompt_guard import (
    inspect_source_for_indirect_injections,
    sanitize_critic_directive,
    verify_tool_call_safety,
    wrap_untrusted_content,
)
from testforge.security import SecurityGuardrail, SecurityPolicy
from testforge.security_evaluation_engine import (
    STANDARDIZED_SECURITY_SCENARIOS,
    ScenarioEvaluationResult,
    SecurityEvaluationHarness,
)
from testforge.security_prompts import (
    FEW_SHOT_EXEMPLARS,
    PERSONA_PROMPTS,
    REACT_FRAMEWORK_INSTRUCTIONS,
    DeveloperPersona,
    PromptConfiguration,
    PromptStrategy,
    PromptVariationBuilder,
)

# ==============================================================================
# 1. Prompt Strategy & Persona Architecture Tests
# ==============================================================================

class TestPromptStrategyArchitecture:
    """Verifies that Zero-Shot, Few-Shot, and ReAct prompt architectures are distinctly constructed."""

    def test_zero_shot_prompt_is_concise_without_exemplars_or_react(self):
        config = PromptConfiguration(strategy=PromptStrategy.ZERO_SHOT, persona=DeveloperPersona.EXPERIENCED)
        sys_prompt = PromptVariationBuilder.build_system_prompt(config)
        user_prompt = PromptVariationBuilder.build_user_prompt(
            target_source_code="def add(a, b): return a + b\n",
            user_request="Test add",
            config=config
        )
        assert "EXEMPLARS OF SAFE TESTING PATTERNS" not in sys_prompt
        assert "REACT INTERACTION PROTOCOL" not in sys_prompt
        assert "Experienced Senior Developer" in sys_prompt
        assert "<untrusted_content" in user_prompt

    def test_few_shot_prompt_includes_curated_exemplars(self):
        config = PromptConfiguration(strategy=PromptStrategy.FEW_SHOT, persona=DeveloperPersona.QA_ENGINEER)
        sys_prompt = PromptVariationBuilder.build_system_prompt(config)
        assert "EXEMPLARS OF SAFE TESTING PATTERNS" in sys_prompt
        assert "[IN-CONTEXT DEMONSTRATION 1" in sys_prompt
        assert "Lead QA Engineer" in sys_prompt

    def test_react_prompt_mandates_observable_thought_action_observation_steps(self):
        config = PromptConfiguration(strategy=PromptStrategy.REACT, persona=DeveloperPersona.SECURITY_CONSCIOUS)
        sys_prompt = PromptVariationBuilder.build_system_prompt(config)
        user_prompt = PromptVariationBuilder.build_user_prompt(
            target_source_code="def add(a, b): return a + b\n",
            user_request="Test add",
            config=config
        )
        assert "REACT INTERACTION PROTOCOL" in sys_prompt
        assert "Thought: <Reasoning" in sys_prompt
        assert "Action: <Tool to call" in sys_prompt
        assert "Observation: <Observed outcome" in sys_prompt
        assert "Begin your analysis now. State your first Thought" in user_prompt


class TestPersonaContextVariations:
    """Verifies that all 4 developer personas impart distinct behavioral guidance."""

    @pytest.mark.parametrize("persona,keyword", [
        (DeveloperPersona.BEGINNER, "Beginner Developer"),
        (DeveloperPersona.EXPERIENCED, "Experienced Senior Developer"),
        (DeveloperPersona.QA_ENGINEER, "Lead QA Engineer"),
        (DeveloperPersona.SECURITY_CONSCIOUS, "Security-Conscious Software Engineer"),
    ])
    def test_persona_injected_correctly(self, persona: DeveloperPersona, keyword: str):
        config = PromptConfiguration(strategy=PromptStrategy.ZERO_SHOT, persona=persona)
        sys_prompt = PromptVariationBuilder.build_system_prompt(config)
        assert keyword in sys_prompt


# ==============================================================================
# 2. Security Evaluation Matrix Execution Tests
# ==============================================================================

class TestSecurityScenariosMatrix:
    """Verifies that all 10 standard security scenarios evaluate correctly across strategies."""

    @pytest.fixture(scope="module")
    def harness(self):
        return SecurityEvaluationHarness()

    def test_sec_01_benign_normal_request_allowed(self, harness):
        """Verifies legitimate user request with clean code is allowed (0% false positives)."""
        scenario = next(s for s in STANDARDIZED_SECURITY_SCENARIOS if s.scenario_id == "SEC_01_NORMAL_VALID_REQUEST")
        res = harness.evaluate_scenario(scenario, PromptStrategy.ZERO_SHOT, DeveloperPersona.EXPERIENCED)
        assert res.passed is True
        assert res.actual_outcome == "ALLOW"
        assert res.attack_detected is False

    def test_sec_02_malformed_syntax_rejected(self, harness):
        """Verifies malformed syntax is caught and rejected."""
        scenario = next(s for s in STANDARDIZED_SECURITY_SCENARIOS if s.scenario_id == "SEC_02_MALFORMED_REQUEST")
        res = harness.evaluate_scenario(scenario, PromptStrategy.FEW_SHOT, DeveloperPersona.BEGINNER)
        assert res.passed is True
        assert res.actual_outcome == "REJECT"

    def test_sec_03_direct_prompt_injection_blocked(self, harness):
        """Verifies direct prompt injection is rejected and attack is flagged."""
        scenario = next(s for s in STANDARDIZED_SECURITY_SCENARIOS if s.scenario_id == "SEC_03_DIRECT_PROMPT_INJECTION")
        res = harness.evaluate_scenario(scenario, PromptStrategy.REACT, DeveloperPersona.SECURITY_CONSCIOUS)
        assert res.passed is True
        assert res.actual_outcome == "REJECT"
        assert res.attack_detected is True

    def test_sec_04_indirect_prompt_injection_defused(self, harness):
        """Verifies indirect injection inside comments/docstrings is neutralized via DEFUSE."""
        scenario = next(s for s in STANDARDIZED_SECURITY_SCENARIOS if s.scenario_id == "SEC_04_INDIRECT_PROMPT_INJECTION")
        res = harness.evaluate_scenario(scenario, PromptStrategy.ZERO_SHOT, DeveloperPersona.QA_ENGINEER)
        assert res.passed is True
        assert res.actual_outcome == "DEFUSE"
        assert res.attack_detected is True
        assert res.sanitized is True

    def test_sec_05_toxic_abusive_language_blocked(self, harness):
        """Verifies toxic and abusive language triggers security block."""
        scenario = next(s for s in STANDARDIZED_SECURITY_SCENARIOS if s.scenario_id == "SEC_05_TOXIC_ABUSIVE_LANGUAGE")
        res = harness.evaluate_scenario(scenario, PromptStrategy.FEW_SHOT, DeveloperPersona.EXPERIENCED)
        assert res.passed is True
        assert res.actual_outcome == "REJECT"
        assert res.attack_detected is True

    def test_sec_06_malicious_tool_output_sanitized(self, harness):
        """Verifies tool outputs bearing override directives are sanitized."""
        scenario = next(s for s in STANDARDIZED_SECURITY_SCENARIOS if s.scenario_id == "SEC_06_MALICIOUS_TOOL_OUTPUT")
        res = harness.evaluate_scenario(scenario, PromptStrategy.REACT, DeveloperPersona.SECURITY_CONSCIOUS)
        assert res.passed is True
        assert res.actual_outcome == "SANITIZE"
        assert res.attack_detected is True

    def test_sec_07_invalid_structured_output_rejected(self, harness):
        """Verifies malformed structured output violating Pydantic schema is rejected."""
        scenario = next(s for s in STANDARDIZED_SECURITY_SCENARIOS if s.scenario_id == "SEC_07_INVALID_STRUCTURED_OUTPUT")
        res = harness.evaluate_scenario(scenario, PromptStrategy.ZERO_SHOT, DeveloperPersona.BEGINNER)
        assert res.passed is True
        assert res.actual_outcome == "REJECT"

    def test_sec_08_invalid_callback_data_scrubbed(self, harness):
        """Verifies credentials in callback payloads are redacted to [REDACTED_SECRET]."""
        scenario = next(s for s in STANDARDIZED_SECURITY_SCENARIOS if s.scenario_id == "SEC_08_INVALID_CALLBACK_DATA")
        res = harness.evaluate_scenario(scenario, PromptStrategy.FEW_SHOT, DeveloperPersona.QA_ENGINEER)
        assert res.passed is True
        assert res.actual_outcome == "SANITIZE"
        assert res.sanitized is True

    def test_sec_09_unauthorized_tool_invocation_rejected(self, harness):
        """Verifies unauthorized tool calls (e.g. execute_bash) are blocked."""
        scenario = next(s for s in STANDARDIZED_SECURITY_SCENARIOS if s.scenario_id == "SEC_09_UNAUTHORIZED_TOOL_INVOCATION")
        res = harness.evaluate_scenario(scenario, PromptStrategy.REACT, DeveloperPersona.SECURITY_CONSCIOUS)
        assert res.passed is True
        assert res.actual_outcome == "REJECT"
        assert res.attack_detected is True

    def test_sec_10_sandbox_restriction_bypass_blocked(self, harness):
        """Verifies AST visitor blocks os.system and socket calls in candidate tests."""
        scenario = next(s for s in STANDARDIZED_SECURITY_SCENARIOS if s.scenario_id == "SEC_10_SANDBOX_RESTRICTION_BYPASS")
        res = harness.evaluate_scenario(scenario, PromptStrategy.ZERO_SHOT, DeveloperPersona.EXPERIENCED)
        assert res.passed is True
        assert res.actual_outcome == "REJECT"
        assert res.attack_detected is True

    def test_full_matrix_pass_rate_is_100_percent(self, harness):
        """Verifies complete 120-test cross-product matrix executes deterministically with 100% pass rate."""
        results = harness.run_full_evaluation_matrix()
        assert len(results) == 120  # 3 strategies * 4 personas * 10 scenarios
        passed = sum(1 for r in results if r.passed)
        assert passed == 120
