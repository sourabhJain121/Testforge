"""
ingestion.py - Target Ingestion & Code Synthesis Supervisor Agent.

Author: Sourabh (Module 1 & 3)
Course: CSE3101 - Agentic AI

Features:
  - Mode A (Arbitrary File Ingestion):
      * Ingests any arbitrary .py file path from filesystem
      * Inspects AST to extract top-level functions, classes, and exported symbols
      * Generates a dynamic testing harness and standalone import adapter
  - Mode B (Autonomous Code Generation):
      * Accepts natural-language specification
      * Uses Gemini (or deterministic fallback) to generate production-ready Python modules with boundary conditions
      * Saves to samples/generated_<name>.py and prepares it for the TestForge hardening loop
"""

from __future__ import annotations
import os
import re
import ast
from typing import List, Dict, Any, Optional, Tuple
from testforge.logger import TraceLogger


class IngestionAnalysis:
    """Stores metadata of an ingested Python source file."""
    def __init__(
        self,
        file_path: str,
        source_code: str,
        module_name: str,
        functions: List[str],
        classes: List[str],
        has_syntax_error: bool = False,
        error_msg: str = ""
    ):
        self.file_path = file_path
        self.source_code = source_code
        self.module_name = module_name
        self.functions = functions
        self.classes = classes
        self.has_syntax_error = has_syntax_error
        self.error_msg = error_msg


class TargetManagerAgent:
    """
    Supervisor Agent that manages target discovery, AST analysis,
    and autonomous module synthesis.
    """
    def __init__(
        self,
        model_name: str = "gemini-3.6-flash",
        logger: Optional[TraceLogger] = None,
        api_key: Optional[str] = None
    ):
        self.model_name = model_name
        self.logger = logger
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "").strip()
        self.client = None
        self.is_live = False

        if self.api_key:
            try:
                from google import genai
                self.client = genai.Client(api_key=self.api_key)
                self.is_live = True
            except Exception:
                self.client = None

    # --------------------------------------------------------------------------
    # Mode A: Arbitrary File Ingestion & AST Inspection
    # --------------------------------------------------------------------------
    def ingest_file(self, file_path: str) -> IngestionAnalysis:
        """
        Inspects an arbitrary Python file and extracts AST metadata.
        """
        abs_path = os.path.abspath(file_path)
        if not os.path.exists(abs_path):
            raise FileNotFoundError(f"Target file not found at: {file_path}")

        with open(abs_path, "r", encoding="utf-8") as f:
            code = f.read()

        # Resolve clean module name relative to workspace or cwd
        cwd = os.getcwd()
        if abs_path.startswith(cwd):
            rel_path = os.path.relpath(abs_path, cwd)
        else:
            rel_path = os.path.basename(abs_path)

        norm = os.path.normpath(rel_path)
        if norm.endswith(".py"):
            norm = norm[:-3]
        module_name = norm.replace(os.sep, ".").replace("/", ".").lstrip(".")

        functions: List[str] = []
        classes: List[str] = []

        try:
            tree = ast.parse(code)
            for node in tree.body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    functions.append(node.name)
                elif isinstance(node, ast.ClassDef):
                    classes.append(node.name)
            return IngestionAnalysis(
                file_path=abs_path,
                source_code=code,
                module_name=module_name,
                functions=functions,
                classes=classes
            )
        except SyntaxError as e:
            return IngestionAnalysis(
                file_path=abs_path,
                source_code=code,
                module_name=module_name,
                functions=[],
                classes=[],
                has_syntax_error=True,
                error_msg=f"SyntaxError on line {e.lineno}: {e.msg}"
            )

    # --------------------------------------------------------------------------
    # Mode B: Autonomous Module Synthesis
    # --------------------------------------------------------------------------
    def synthesize_module(self, prompt: str, output_dir: str = "samples") -> Tuple[str, str]:
        """
        Synthesizes a full, bug-free Python module from a natural-language description.
        Saves the file to `samples/generated_<slug>.py`.
        Returns:
          (file_path, generated_source_code)
        """
        slug = self._create_slug(prompt)
        os.makedirs(output_dir, exist_ok=True)
        target_path = os.path.join(output_dir, f"generated_{slug}.py")

        system_instruction = (
            "You are a Principal Python Systems Architect. "
            "Your task is to implement a complete, self-contained, and bug-free Python module matching the user's specification. "
            "Ensure the code includes:\n"
            "1. Clear type hints and comprehensive docstrings.\n"
            "2. Robust input validation, edge-case handling, and numerical/logical boundary checks.\n"
            "3. Clean standard library imports only (no external non-standard packages).\n"
            "4. Output ONLY valid Python code inside a single ```python ... ``` markdown block without commentary."
        )

        code_text = ""
        if self.is_live and self.client:
            from testforge.agents import execute_genai_with_retry_and_fallback
            try:
                raw_text, tokens, latency, used_model = execute_genai_with_retry_and_fallback(
                    client=self.client,
                    primary_model=self.model_name,
                    contents=f"Implement the following Python module with rich boundary conditions:\n{prompt}",
                    system_instruction=system_instruction,
                    temperature=0.2,
                    logger=self.logger
                )
                from testforge.agents import CodeSanitizer
                is_valid, sanitized, err = CodeSanitizer.extract_and_validate(raw_text)
                if is_valid:
                    code_text = sanitized
            except Exception as exc:
                print(f"[!] Live synthesis failed: {exc}. Using deterministic synthesis fallback.")

        if not code_text:
            code_text = self._fallback_synthesis(prompt)

        with open(target_path, "w", encoding="utf-8") as f:
            f.write(code_text)

        if self.logger:
            self.logger.log_event("MODULE_SYNTHESIS", {
                "prompt": prompt,
                "target_path": target_path,
                "length_chars": len(code_text)
            })

        return target_path, code_text

    def _create_slug(self, prompt: str) -> str:
        words = re.findall(r"[a-zA-Z0-9]+", prompt.lower())
        slug = "_".join(words[:4]) if words else "custom_module"
        return slug

    def _fallback_synthesis(self, prompt: str) -> str:
        """Deterministic module synthesis for offline demo or fallback."""
        return f'''"""
Auto-generated module based on specification:
{prompt}
"""

def process_transaction(amount: float, balance: float, is_vip: bool) -> tuple[bool, float]:
    """
    Executes a processed transaction with balance verification and VIP waivers.
    """
    if amount <= 0.0:
        return (False, balance)

    fee = 0.0 if is_vip else 2.50
    total_needed = amount + fee

    if balance >= total_needed:
        new_balance = balance - total_needed
        return (True, round(new_balance, 2))

    return (False, balance)
'''
