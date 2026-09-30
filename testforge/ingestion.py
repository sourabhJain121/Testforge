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
from pathlib import Path
import urllib.request
import urllib.error
from typing import List, Dict, Any, Optional, Tuple
from testforge.logger import TraceLogger


def fetch_github_source(github_url: str, output_dir: str = "samples") -> Path:
    """
    Fetches raw Python source code from a GitHub URL, validates AST syntax,
    saves into `samples/github_<repo>_<filename>.py`, and returns the Path.

    Supports:
      - Standard GitHub blob URLs (e.g., https://github.com/psf/requests/blob/main/requests/utils.py)
      - Raw GitHub URLs (e.g., https://raw.githubusercontent.com/psf/requests/main/requests/utils.py)
    """
    clean_url = github_url.strip()
    if not clean_url:
        raise ValueError("GitHub URL cannot be empty.")

    # Strip URL fragments / query strings for endpoint derivation
    base_url = clean_url.split("#")[0].split("?")[0].rstrip("/")

    # Pattern 1: standard github.com blob or raw URL
    # https://github.com/<owner>/<repo>/blob/<ref>/<filepath> or .../raw/...
    blob_pattern = r"^https?://github\.com/([^/]+)/([^/]+)/(?:blob|raw)/([^/]+)/(.+)$"
    # Pattern 2: raw.githubusercontent.com URL
    # https://raw.githubusercontent.com/<owner>/<repo>/<ref>/<filepath>
    raw_pattern = r"^https?://raw\.githubusercontent\.com/([^/]+)/([^/]+)/([^/]+)/(.+)$"

    m_blob = re.match(blob_pattern, base_url)
    m_raw = re.match(raw_pattern, base_url)

    if m_blob:
        owner, repo, branch, file_path = m_blob.groups()
        raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{branch}/{file_path}"
        filename = os.path.basename(file_path)
    elif m_raw:
        owner, repo, branch, file_path = m_raw.groups()
        raw_url = base_url
        filename = os.path.basename(file_path)
    else:
        # Fallback heuristic if URL is roughly github
        if "github.com" in base_url and "/blob/" in base_url:
            raw_url = base_url.replace("github.com", "raw.githubusercontent.com").replace("/blob/", "/")
            parts = base_url.split("/")
            repo = parts[4] if len(parts) > 4 else "repo"
            filename = parts[-1] if parts else "module.py"
        else:
            raise ValueError(
                f"Unsupported GitHub URL format: {github_url}. "
                "Expected https://github.com/<owner>/<repo>/blob/<branch>/<path.py> "
                "or https://raw.githubusercontent.com/<owner>/<repo>/<branch>/<path.py>"
            )

    if not filename.endswith(".py"):
        filename = f"{filename}.py"

    # Sanitize repo and filename for safe filesystem path
    clean_repo = re.sub(r"[^\w\-]", "_", repo)
    clean_filename = re.sub(r"[^\w\-\.]", "_", filename)

    # Download source content
    req = urllib.request.Request(
        raw_url,
        headers={"User-Agent": "TestForge/1.0 (Autonomous Systems Ingestion)"}
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            content_bytes = resp.read()
            content = content_bytes.decode("utf-8", errors="replace")
    except urllib.error.HTTPError as http_err:
        raise RuntimeError(
            f"Failed to fetch GitHub file from {raw_url} (HTTP {http_err.code}: {http_err.reason})"
        ) from http_err
    except Exception as exc:
        raise RuntimeError(f"Network error fetching GitHub file: {exc}") from exc

    # Validate AST
    try:
        ast.parse(content)
    except SyntaxError as syn_err:
        raise ValueError(
            f"Fetched file from {github_url} contains invalid Python AST (line {syn_err.lineno}: {syn_err.msg})"
        ) from syn_err
    except Exception as exc:
        raise ValueError(f"Failed to parse AST of fetched file: {exc}") from exc

    # Save into target path
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    target_path = out_dir / f"github_{clean_repo}_{clean_filename}"
    target_path.write_text(content, encoding="utf-8")

    return target_path.resolve()


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
    # Mode C: Direct GitHub URL Ingestion
    # --------------------------------------------------------------------------
    def ingest_github(self, github_url: str, output_dir: str = "samples") -> Tuple[Path, IngestionAnalysis]:
        """
        Ingests and validates an arbitrary Python source file directly from a public GitHub URL.
        """
        saved_path = fetch_github_source(github_url, output_dir=output_dir)
        analysis = self.ingest_file(str(saved_path))
        return saved_path, analysis

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

    # --------------------------------------------------------------------------
    # Mode C: Direct GitHub Ingestion & AST Inspection
    # --------------------------------------------------------------------------
    def fetch_and_ingest_github(self, github_url: str, output_dir: str = "samples") -> Tuple[Path, IngestionAnalysis]:
        """
        Pulls raw Python file from public GitHub URL, validates AST syntax,
        persists into samples directory, and inspects exported symbols.
        """
        saved_path = fetch_github_source(github_url, output_dir=output_dir)
        analysis = self.ingest_file(str(saved_path))
        if self.logger:
            self.logger.log_event("GITHUB_FILE_INGESTION", {
                "github_url": github_url,
                "saved_path": str(saved_path),
                "module_name": analysis.module_name,
                "functions": analysis.functions,
                "classes": analysis.classes
            })
        return saved_path, analysis

