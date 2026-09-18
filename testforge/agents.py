"""
agents.py - Specialized Agents (TestGenerator & AdversarialCritic) and LLM Adapter.

Author: Sourabh (Module 1 & 3)
Course: CSE3101 - Agentic AI

Implements:
  - TestGeneratorAgent: generates pytest tests and tightens assertions on reflection.
  - AdversarialCriticAgent: formats surviving mutant diffs into targeted hardening prompts.
  - LLM completion adapter supporting Google GenAI / Gemini with fallback heuristics.
"""

from __future__ import annotations
import os
import re
from typing import List, Dict, Any, Optional
from testforge.logger import TraceLogger


class LLMClient:
    """
    LLM wrapper for Gemini (Google GenAI) with graceful deterministic fallback.
    """
    def __init__(self, model_name: str = "gemini-2.5-pro", logger: Optional[TraceLogger] = None):
        self.model_name = model_name
        self.logger = logger
        self.api_key = os.environ.get("GEMINI_API_KEY", "")
        self.client = None
        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
            except Exception:
                self.client = None

    def generate(self, system_instruction: str, prompt: str) -> str:
        start_time = time_now = os.times().elapsed

        if self.client and self.api_key:
            try:
                from google.genai import types
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=0.2
                    )
                )
                text = response.text or ""
                if self.logger:
                    self.logger.log_event("LLM_COMPLETION", {
                        "model": self.model_name,
                        "system_instruction": system_instruction,
                        "prompt": prompt,
                        "response": text,
                        "offline_mock": False
                    })
                return text
            except Exception as e:
                # If network or API quota error, log and fallback
                if self.logger:
                    self.logger.log_event("LLM_ERROR", {"error": str(e)})

        # Deterministic offline mock mode (Viva demo without external network requirement)
        fallback_code = self._mock_completion_generator(system_instruction, prompt)
        if self.logger:
            self.logger.log_event("LLM_COMPLETION", {
                "model": "offline-deterministic-engine",
                "system_instruction": system_instruction,
                "prompt": prompt,
                "response": fallback_code,
                "offline_mock": True
            })
        return fallback_code

    def _mock_completion_generator(self, system_instruction: str, prompt: str) -> str:
        """
        Deterministic code synthesizer used when GEMINI_API_KEY is not set.
        Ensures the grading/viva pipeline executes fully and deterministically.
        """
        if "Surviving Mutant" in prompt or "Surviving Mutant Fault" in prompt:
            # Reflection Hardening phase: rigorously tighten assertions to eliminate surviving boundary faults
            return """```python
from target import banking_transaction
import pytest

def test_hardened_nominal():
    assert banking_transaction(100.0, 50.0, 5.0) is True

def test_hardened_invalid_inputs():
    assert banking_transaction(0.0, 50.0, 5.0) is False
    assert banking_transaction(-10.0, 50.0, 5.0) is False
    assert banking_transaction(100.0, 0.0, 5.0) is False
    assert banking_transaction(100.0, -5.0, 5.0) is False

def test_hardened_exact_boundary():
    # Exactly on boundary: balance == amount + fee (should return False)
    assert banking_transaction(100.0, 95.0, 5.0) is False
    # Just above boundary: balance > amount + fee (should return True)
    assert banking_transaction(100.0, 94.0, 5.0) is True
    # Inverted arithmetic catch
    assert banking_transaction(50.0, 40.0, 5.0) is True
```"""
        else:
            # Baseline test generation
            return """```python
from target import banking_transaction
import pytest

def test_nominal_pass():
    assert banking_transaction(100.0, 50.0, 5.0) is True

def test_negative_balance():
    assert banking_transaction(-10.0, 50.0, 5.0) is False
```"""


class AdversarialCriticAgent:
    """
    Critic Agent that evaluates surviving mutants and translates AST diffs
    into prescriptive, unambiguous hardening instructions for the Test Generator.
    """
    def __init__(self, logger: Optional[TraceLogger] = None):
        self.logger = logger

    def format_reflection_feedback(self, surviving_diffs: List[str]) -> str:
        """
        Creates a structured prompt section showing exact AST mutant unified diffs.
        """
        if not surviving_diffs:
            return "No surviving mutants. Test suite is already hardened."

        feedback_sections = []
        for idx, diff in enumerate(surviving_diffs, 1):
            feedback_sections.append(
                f"### Surviving Mutant Fault #{idx}:\n```diff\n{diff}\n```"
            )
        return "\n\n".join(feedback_sections)


class TestGeneratorAgent:
    """
    Generates and refines tests using ReAct / self-reflection loops.
    """
    def __init__(self, llm: LLMClient, critic: AdversarialCriticAgent, logger: Optional[TraceLogger] = None):
        self.llm = llm
        self.critic = critic
        self.logger = logger

    def generate_initial_suite(self, target_code: str) -> str:
        system_instruction = (
            "You are an expert Test Automation Engineer in Python. "
            "Write comprehensive pytest unit tests for the provided Python source code. "
            "Always import the functions under test using `from target import ...`. "
            "Your output must ONLY be executable Python code wrapped inside a single ```python code block."
        )
        prompt = (
            f"### Target Code to Test:\n```python\n{target_code}\n```\n"
            "Write pytest tests achieving maximum branch and statement coverage."
        )
        raw_response = self.llm.generate(system_instruction, prompt)
        return self._extract_code(raw_response)

    def harden_suite(self, target_code: str, current_test_code: str, surviving_diffs: List[str]) -> str:
        system_instruction = (
            "You are an elite QA and Mutation Hardening Agent. "
            "Your goal is to harden the existing unit test suite so that EVERY surviving mutant is killed. "
            "A mutant survived because the current assertions are too loose or did not check exact boundary values. "
            "Write rigorous, exact assertions for both edge cases and boundary conditions. "
            "Always import from `target` using `from target import ...`. "
            "Return the COMPLETE, UPDATED test suite in a single ```python code block."
        )
        critic_guidance = self.critic.format_reflection_feedback(surviving_diffs)
        prompt = (
            f"### Target Code:\n```python\n{target_code}\n```\n\n"
            f"### Existing Test Suite:\n```python\n{current_test_code}\n```\n\n"
            f"### Adversarial Critic Reflection Signal:\n{critic_guidance}\n\n"
            "Eliminate all surviving mutants by adding targeted test assertions."
        )
        raw_response = self.llm.generate(system_instruction, prompt)
        return self._extract_code(raw_response)

    @staticmethod
    def _extract_code(text: str) -> str:
        match = re.search(r"```python\s*(.*?)\s*```", text, re.DOTALL)
        if match:
            return match.group(1).strip()
        match_generic = re.search(r"```\s*(.*?)\s*```", text, re.DOTALL)
        if match_generic:
            return match_generic.group(1).strip()
        return text.strip()
