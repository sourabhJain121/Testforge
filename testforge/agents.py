"""
agents.py - Live Foundation Model Agents with AST Syntax Guardrails.

Author: Sourabh (Module 1 & 3)
Course: CSE3101 - Agentic AI

Features:
  - Official `google-genai` SDK integration (`from google import genai`)
  - TestGeneratorAgent: dynamically generates/hardens Pytest tests targeting surviving mutants
  - AdversarialCriticAgent: analyzes surviving AST diffs to prescribe boundary checks
  - CodeSanitizer: extracts python code and uses native `ast.parse()` as a strict syntax guardrail
  - Real token and latency telemetry extraction from Gemini API response metadata
"""

from __future__ import annotations
import os
import re
import ast
import time
from typing import List, Dict, Any, Optional, Tuple
from google import genai
from google.genai import types
from testforge.logger import TraceLogger


class CodeSanitizer:
    """
    Extracts Python code from Markdown backticks and verifies AST validity.
    Prevents syntax errors from crashing the sandboxed test executor.
    """
    @staticmethod
    def extract_and_validate(raw_text: str) -> Tuple[bool, str, str]:
        code = raw_text.strip()
        # Strip markdown code blocks
        if "```python" in code:
            parts = code.split("```python")
            code = parts[1].split("```")[0].strip()
        elif "```" in code:
            parts = code.split("```")
            code = parts[1].split("```")[0].strip()

        # Validate with Python AST parser
        try:
            ast.parse(code)
            return (True, code, "")
        except SyntaxError as e:
            return (False, code, f"SyntaxError line {e.lineno}: {e.msg}")
        except Exception as e:
            return (False, code, f"AST Validation error: {str(e)}")


class TestGeneratorAgent:
    """
    Autonomous Test Generator Agent using Google Gemini live API.
    Synthesizes initial Pytest suites and iteratively hardens assertions
    to kill surviving mutants.
    """
    def __init__(
        self,
        model_name: str = "gemini-2.5-flash",
        logger: Optional[TraceLogger] = None,
        api_key: Optional[str] = None
    ):
        self.model_name = model_name
        self.logger = logger
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "").strip()
        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY environment variable is not set. "
                "Please export GEMINI_API_KEY='your_api_key' to enable live Foundation Model inference."
            )
        self.client = genai.Client(api_key=self.api_key)

    def generate_tests(
        self,
        source_code: str,
        missing_branches: Optional[List[str]] = None,
        surviving_diffs: Optional[List[str]] = None,
        critic_feedback: Optional[str] = None,
        iteration: int = 1
    ) -> str:
        """
        Calls Gemini to write strict, executable Pytest tests that kill surviving mutants.
        Validates the output via ast.parse() before returning.
        """
        system_instruction = (
            "You are a Principal Software QA Automation Engineer. "
            "Your mission is to generate and harden a standalone Pytest test suite for the provided Python source code. "
            "You must write rigorous, parameterized, and boundary-sensitive assertions. "
            "Every test must import the module under test using: `from target import *`.\n"
            "Rules:\n"
            "1. Output ONLY executable Python code within a single ```python ... ``` markdown block.\n"
            "2. Do NOT write prose, commentary, or conversational filler outside the code block.\n"
            "3. Target boundary values, comparison flips (< vs <=, > vs >=, == vs !=), zero/negative values, and arithmetic changes.\n"
            "4. If surviving mutant diffs or critic directives are provided, specifically write assertions that FAIL when the mutated code runs."
        )

        prompt_parts = [f"### Target Source Code to Test:\n```python\n{source_code}\n```"]

        if missing_branches:
            branches_str = "\n".join(f"- {b}" for b in missing_branches)
            prompt_parts.append(f"### Uncovered / Missing Branches:\n{branches_str}")

        if surviving_diffs:
            diffs_str = "\n\n".join(
                f"--- Surviving Mutant #{i+1} ---\n{diff}"
                for i, diff in enumerate(surviving_diffs)
            )
            prompt_parts.append(f"### Surviving Mutant AST Diffs (Faults Your Previous Tests Failed to Kill):\n{diffs_str}")

        if critic_feedback:
            prompt_parts.append(f"### Adversarial Critic Reasoning & Directives:\n{critic_feedback}")

        prompt_parts.append("Write the complete, runnable Pytest test file now.")
        full_prompt = "\n\n".join(prompt_parts)

        start_time = time.perf_counter()
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=full_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.2
            )
        )
        latency_sec = time.perf_counter() - start_time
        raw_text = response.text or ""

        # Extract token counts from response metadata
        prompt_tokens = 0
        completion_tokens = 0
        total_tokens = 0
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            meta = response.usage_metadata
            prompt_tokens = getattr(meta, "prompt_token_count", 0) or 0
            completion_tokens = getattr(meta, "candidates_token_count", 0) or 0
            total_tokens = getattr(meta, "total_token_count", 0) or 0

        # Extract and validate pure Python AST
        is_valid, sanitized_code, err = CodeSanitizer.extract_and_validate(raw_text)

        if self.logger:
            self.logger.log_llm_event(
                agent_name="TestGeneratorAgent",
                model_name=self.model_name,
                prompt=full_prompt,
                response_text=raw_text,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                latency_sec=latency_sec,
                iteration=iteration,
                is_valid_ast=is_valid,
                validation_error=err
            )

        if not is_valid:
            raise ValueError(f"TestGenerator generated invalid Python syntax: {err}\nRaw snippet: {raw_text[:200]}")

        return sanitized_code


class AdversarialCriticAgent:
    """
    Adversarial Critic Agent using Google Gemini live API.
    Analyzes surviving AST unified diffs and formulates targeted directives
    explaining why assertions bypassed the fault and what inputs are needed.
    """
    def __init__(
        self,
        model_name: str = "gemini-2.5-flash",
        logger: Optional[TraceLogger] = None,
        api_key: Optional[str] = None
    ):
        self.model_name = model_name
        self.logger = logger
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "").strip()
        if not self.api_key:
            raise ValueError(
                "GEMINI_API_KEY environment variable is not set. "
                "Please export GEMINI_API_KEY='your_api_key' to enable live Foundation Model inference."
            )
        self.client = genai.Client(api_key=self.api_key)

    def analyze_surviving_mutants(
        self,
        target_code: str,
        surviving_mutant_diffs: List[str],
        iteration: int = 1
    ) -> str:
        """
        Sends the surviving unified diffs and target code to Gemini.
        Returns concise, actionable directives explaining the bypassed logic.
        """
        if not surviving_mutant_diffs:
            return "All mutants killed. Suite is hardened."

        system_instruction = (
            "You are an Adversarial QA Critic in an automated mutation-testing loop. "
            "You inspect AST mutations (faults) that survived existing unit tests. "
            "For each surviving mutant:\n"
            "1. State concisely why previous assertions failed to detect the inverted/swapped operator.\n"
            "2. Prescribe exact numerical or boolean boundary inputs that will force the mutant to fail while passing the clean code.\n"
            "Be terse, authoritative, and direct. Output numbered directives."
        )

        diffs_text = "\n\n".join(
            f"--- Mutant #{idx+1} ---\n{diff}"
            for idx, diff in enumerate(surviving_mutant_diffs)
        )

        prompt = (
            f"### Target Code Under Test:\n```python\n{target_code}\n```\n\n"
            f"### Surviving Mutant Unified Diffs:\n{diffs_text}\n\n"
            "Analyze why these mutants survived and specify exact assertions required to kill them."
        )

        start_time = time.perf_counter()
        response = self.client.models.generate_content(
            model=self.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.1
            )
        )
        latency_sec = time.perf_counter() - start_time
        analysis_text = response.text or ""

        # Extract tokens
        prompt_tokens = 0
        completion_tokens = 0
        total_tokens = 0
        if hasattr(response, "usage_metadata") and response.usage_metadata:
            meta = response.usage_metadata
            prompt_tokens = getattr(meta, "prompt_token_count", 0) or 0
            completion_tokens = getattr(meta, "candidates_token_count", 0) or 0
            total_tokens = getattr(meta, "total_token_count", 0) or 0

        if self.logger:
            self.logger.log_llm_event(
                agent_name="AdversarialCriticAgent",
                model_name=self.model_name,
                prompt=prompt,
                response_text=analysis_text,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
                latency_sec=latency_sec,
                iteration=iteration,
                is_valid_ast=True
            )

        return analysis_text
