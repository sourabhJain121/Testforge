"""
ingestion.py - Target Ingestion & Code Synthesis Supervisor Agent.

Author: Sourabh (Module 1 & 3)
System: Autonomous Multi-Agent Hardening Engine

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

import ast
import hashlib
import logging
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from testforge.logger import TraceLogger
from testforge.network_security import (
    DEFAULT_MAX_SOURCE_SIZE_BYTES,
    PayloadTooLargeError,
    SSRFSecurityError,
    bounded_read,
    build_safe_opener,
    validate_url_hostname,
)

logger = logging.getLogger("testforge.ingestion")


def parse_and_normalize_github_url(url: str) -> Dict[str, Any]:
    """
    Validates and normalizes GitHub Python file URLs.
    Extracts repository coordinates, branch/ref, file path, normalized URL, and raw URL.

    Requirements enforced:
      1. Rejects empty URLs.
      2. Strips leading and trailing whitespace.
      3. Strips accidental surrounding quotes ('...', "...", `...`).
      4. Strictly rejects control characters (\\r, \\n, \\t, \\x00) and any whitespace
         or non-printable characters.
      5. Parses using urllib.parse.urlparse.
      6. Requires scheme == 'https'.
      7. Requires hostname == 'github.com' or 'raw.githubusercontent.com'.
      8. Validates path patterns:
           - github.com: /<owner>/<repo>/blob/<ref>/<file path> or /raw/<ref>/<file path>
           - raw.githubusercontent.com: /<owner>/<repo>/<ref>/<file path>
      9. Rejects URLs containing unexpected UI text, button labels, or trailing tokens.
      10. Produces debug-safe logging without secrets.
    """
    if not isinstance(url, str):
        raise ValueError("GitHub URL must be a string.")

    raw_input = url
    cleaned = url.strip()
    if not cleaned:
        raise ValueError("GitHub URL cannot be empty.")

    # Remove accidental surrounding quotes if present
    if (cleaned.startswith('"') and cleaned.endswith('"')) or \
       (cleaned.startswith("'") and cleaned.endswith("'")) or \
       (cleaned.startswith("`") and cleaned.endswith("`")):
        cleaned = cleaned[1:-1].strip()

    # Reject URLs containing control characters or whitespace
    disallowed_chars = {'\r', '\n', '\t', '\x00'}
    for ch in cleaned:
        if ch in disallowed_chars or ord(ch) < 32 or ord(ch) >= 127 or ch.isspace():
            raise ValueError(
                f"URL contains invalid control characters or unexpected text/whitespace: {repr(cleaned)}"
            )

    # Reject unexpected UI artifacts or bracketed text like [Fetch & Ingest]
    for bad_token in ('[', ']', '<', '>', '{', '}', '|', '^', '`', '"', "'"):
        if bad_token in cleaned:
            raise ValueError(
                f"URL contains unexpected characters or UI artifacts ('{bad_token}'): {repr(cleaned)}"
            )

    # Parse with urllib.parse.urlparse
    parsed = urllib.parse.urlparse(cleaned)

    if parsed.scheme.lower() != "https":
        raise ValueError(f"Invalid URL scheme '{parsed.scheme}'. Only 'https' is supported.")

    hostname = (parsed.hostname or "").lower()
    if hostname not in ("github.com", "raw.githubusercontent.com"):
        raise ValueError(
            f"Unsupported hostname '{hostname}'. Expected 'github.com' or 'raw.githubusercontent.com'."
        )

    path = parsed.path.strip("/")
    parts = [p for p in path.split("/") if p]

    if hostname == "github.com":
        # Expected: /<owner>/<repo>/blob/<ref>/<file path...> or .../raw/...
        if len(parts) < 5:
            raise ValueError(
                f"Invalid GitHub URL path '/{path}'. "
                "Expected format: https://github.com/<owner>/<repo>/blob/<branch>/<path.py>"
            )
        owner = parts[0]
        repo = parts[1]
        mode = parts[2]
        if mode not in ("blob", "raw"):
            raise ValueError(
                f"Invalid GitHub URL component '/{mode}/'. Expected '/blob/' or '/raw/'."
            )
        ref = parts[3]
        file_path = "/".join(parts[4:])
        normalized_url = f"https://github.com/{owner}/{repo}/blob/{ref}/{file_path}"
        raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{ref}/{file_path}"

    else:
        # hostname == "raw.githubusercontent.com"
        # Expected: /<owner>/<repo>/<ref>/<file path...>
        if len(parts) < 4:
            raise ValueError(
                f"Invalid raw GitHub URL path '/{path}'. "
                "Expected format: https://raw.githubusercontent.com/<owner>/<repo>/<branch>/<path.py>"
            )
        owner = parts[0]
        repo = parts[1]
        ref = parts[2]
        file_path = "/".join(parts[3:])
        raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{ref}/{file_path}"
        normalized_url = raw_url  # Support raw URL directly without reconverting

    filename = os.path.basename(file_path)
    if not filename.endswith(".py"):
        raise ValueError(f"Target file '{filename}' is not a Python (.py) source file.")

    if not re.match(r"^[a-zA-Z0-9_.-]+$", owner) or not re.match(r"^[a-zA-Z0-9_.-]+$", repo):
        raise ValueError(f"Invalid repository coordinates: owner='{owner}', repo='{repo}'.")

    # Debug-safe logging (no secrets or API keys)
    log_msg = (
        "GitHub Ingestion URL Resolved:\n"
        f"  Original input: {raw_input}\n"
        f"  Normalized URL: {normalized_url}\n"
        f"  Resolved raw URL: {raw_url}\n"
        f"  Repository: {owner}/{repo}\n"
        f"  Branch/ref: {ref}\n"
        f"  File path: {file_path}"
    )
    logger.info(log_msg)
    print(f"[TestForge:ModeC] {log_msg}", flush=True)

    return {
        "original_input": raw_input,
        "normalized_url": normalized_url,
        "raw_url": raw_url,
        "owner": owner,
        "repo": repo,
        "repository": f"{owner}/{repo}",
        "branch": ref,
        "ref": ref,
        "file_path": file_path,
        "filename": filename,
    }


def normalize_github_url(url: str) -> str:
    """
    Normalizes a GitHub URL and returns the clean normalized URL string.
    Rejects malformed strings, UI text, or control characters.
    """
    meta = parse_and_normalize_github_url(url)
    return meta["normalized_url"]


def fetch_github_source_with_meta(
    github_url: str,
    output_dir: str = "samples",
    max_file_size_bytes: int = DEFAULT_MAX_SOURCE_SIZE_BYTES
) -> Tuple[Path, Dict[str, Any]]:
    """
    Fetches raw Python source code from a GitHub URL, resolves relative package imports
    for standalone sandbox execution, validates AST syntax, saves into `samples/github_<repo>_<filename>.py`,
    and returns (Path, metadata_dict).

    Enforces:
      - SSRF redirect protection via SafeGitHubRedirectHandler
      - Bounded source downloads up to max_file_size_bytes
      - Zero partial file retention on error

    Supports:
      - Standard GitHub blob URLs (e.g., https://github.com/psf/requests/blob/main/src/requests/models.py)
      - Raw GitHub URLs (e.g., https://raw.githubusercontent.com/psf/requests/main/src/requests/models.py)
    """
    url_info = parse_and_normalize_github_url(github_url)
    raw_url = url_info["raw_url"]
    owner = url_info["owner"]
    repo = url_info["repo"]
    branch = url_info["branch"]
    file_path = url_info["file_path"]
    filename = url_info["filename"]
    normalized_url = url_info["normalized_url"]

    # Sanitize repo and filename for safe filesystem path
    clean_repo = re.sub(r"[^\w\-]", "_", repo)
    clean_filename = re.sub(r"[^\w\-\.]", "_", filename)

    # Validate destination host against SSRF policy
    validate_url_hostname(raw_url)

    # Download source content with safe opener and bounded read
    req = urllib.request.Request(
        raw_url,
        headers={"User-Agent": "TestForge/1.0 (Autonomous Systems Ingestion)"}
    )
    opener = build_safe_opener()
    try:
        with opener.open(req, timeout=15) as resp:
            content_bytes = bounded_read(resp, max_bytes=max_file_size_bytes)
            content = content_bytes.decode("utf-8", errors="replace")
    except urllib.error.HTTPError as http_err:
        raise RuntimeError(
            f"Failed to fetch GitHub file from {raw_url} (HTTP {http_err.code}: {http_err.reason})"
        ) from http_err
    except (SSRFSecurityError, PayloadTooLargeError):
        raise
    except Exception as exc:
        raise RuntimeError(f"Network error fetching GitHub file: {exc}") from exc

    # Resolve relative package imports (e.g. `from .compat import ...` -> `from requests.compat import ...`)
    clean_repo_pkg = re.sub(r"[^\w]", "", repo)
    if clean_repo_pkg:
        content = re.sub(r"from\s+\.(\w+)", rf"from {clean_repo_pkg}.\1", content)
        content = re.sub(r"from\s+\.\s+import", rf"from {clean_repo_pkg} import", content)

    # Validate AST
    try:
        ast.parse(content)
    except SyntaxError as syn_err:
        raise ValueError(
            f"Fetched file from {normalized_url} contains invalid Python AST (line {syn_err.lineno}: {syn_err.msg})"
        ) from syn_err
    except Exception as exc:
        raise ValueError(f"Failed to parse AST of fetched file: {exc}") from exc

    # Save into target path (only after bounded read and AST validation succeed)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    target_path = out_dir / f"github_{clean_repo}_{clean_filename}"
    target_path.write_text(content, encoding="utf-8")

    source_sha = hashlib.sha256(content.encode("utf-8")).hexdigest()
    clean_mod_suffix = clean_filename[:-3] if clean_filename.endswith(".py") else clean_filename
    meta = {
        "source_github_url": normalized_url,
        "raw_github_url": raw_url,
        "repository": f"{owner}/{repo}",
        "branch": branch,
        "file_path": file_path,
        "filename": filename,
        "generated_module_name": f"samples.github_{clean_repo}_{clean_mod_suffix}",
        "source_sha": source_sha,
        "line_count": len(content.splitlines()),
    }

    return target_path.resolve(), meta


def fetch_github_source(github_url: str, output_dir: str = "samples") -> Path:
    """
    Fetches raw Python source code from a GitHub URL and returns the Path.
    Maintained for backwards compatibility.
    """
    saved_path, _ = fetch_github_source_with_meta(github_url, output_dir=output_dir)
    return saved_path


class IngestionAnalysis:
    """Stores metadata of an ingested Python source file."""
    def __init__(
        self,
        file_path: str,
        source_code: str,
        module_name: str,
        functions: List[str],
        classes: List[str],
        methods: Optional[Dict[str, List[str]]] = None,
        all_callables: Optional[List[str]] = None,
        source_sha: str = "",
        line_count: int = 0,
        ast_function_count: int = 0,
        ast_class_count: int = 0,
        has_syntax_error: bool = False,
        error_msg: str = "",
        github_metadata: Optional[Dict[str, Any]] = None,
        tree: Optional[ast.AST] = None,
        dependencies: Optional[List[str]] = None
    ):
        self.file_path = file_path
        self.source_code = source_code
        self.module_name = module_name
        self.functions = functions or []
        self.classes = classes or []
        self.methods = methods or {}
        self.all_callables = all_callables if all_callables is not None else list(self.functions)
        self.source_sha = source_sha or (hashlib.sha256(source_code.encode("utf-8")).hexdigest() if source_code else "")
        self.line_count = line_count or (len(source_code.splitlines()) if source_code else 0)
        self.ast_function_count = ast_function_count or len(self.all_callables)
        self.ast_class_count = ast_class_count or len(self.classes)
        self.has_syntax_error = has_syntax_error
        self.error_msg = error_msg
        self.github_metadata = github_metadata or {}
        self.tree = tree
        self.dependencies = dependencies or []

    def get(self, key: str, default: Any = None) -> Any:
        """Enables dict-like get access for defensive UI rendering."""
        return getattr(self, key, default)

    def __getattr__(self, name: str) -> Any:
        """Defensive fallback so missing attributes never raise AttributeError."""
        defaults = {
            "methods": {},
            "all_callables": getattr(self, "functions", []),
            "source_sha": hashlib.sha256(getattr(self, "source_code", "").encode("utf-8")).hexdigest() if getattr(self, "source_code", "") else "",
            "line_count": len(getattr(self, "source_code", "").splitlines()) if getattr(self, "source_code", "") else 0,
            "ast_function_count": len(getattr(self, "functions", [])),
            "ast_class_count": len(getattr(self, "classes", [])),
            "github_metadata": {},
            "classes": [],
            "functions": [],
            "source_code": "",
            "module_name": "",
            "file_path": "",
            "has_syntax_error": False,
            "error_msg": "",
            "tree": None,
            "dependencies": [],
        }
        if name in defaults:
            return defaults[name]
        raise AttributeError(f"'IngestionAnalysis' object has no attribute '{name}'")


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
        methods: Dict[str, List[str]] = {}
        all_callables: List[str] = []
        dependencies: List[str] = []

        try:
            tree = ast.parse(code)
            for node in tree.body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    functions.append(node.name)
                    all_callables.append(node.name)
                elif isinstance(node, ast.ClassDef):
                    classes.append(node.name)
                    cls_methods: List[str] = []
                    for item in node.body:
                        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            cls_methods.append(item.name)
                            all_callables.append(f"{node.name}.{item.name}")
                    methods[node.name] = cls_methods
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        dependencies.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        dependencies.append(node.module)

            sha = hashlib.sha256(code.encode("utf-8")).hexdigest()
            return IngestionAnalysis(
                file_path=abs_path,
                source_code=code,
                module_name=module_name,
                functions=functions,
                classes=classes,
                methods=methods,
                all_callables=all_callables,
                source_sha=sha,
                line_count=len(code.splitlines()),
                ast_function_count=len(all_callables),
                ast_class_count=len(classes),
                tree=tree,
                dependencies=sorted(list(set(dependencies)))
            )
        except SyntaxError as e:
            sha = hashlib.sha256(code.encode("utf-8")).hexdigest()
            return IngestionAnalysis(
                file_path=abs_path,
                source_code=code,
                module_name=module_name,
                functions=[],
                classes=[],
                methods={},
                all_callables=[],
                source_sha=sha,
                line_count=len(code.splitlines()),
                ast_function_count=0,
                ast_class_count=0,
                has_syntax_error=True,
                error_msg=f"SyntaxError on line {e.lineno}: {e.msg}",
                tree=None,
                dependencies=[]
            )

    # --------------------------------------------------------------------------
    # Mode C: Direct GitHub URL Ingestion
    # --------------------------------------------------------------------------
    def ingest_github(
        self,
        github_url: str,
        output_dir: str = "samples",
        max_file_size_bytes: int = DEFAULT_MAX_SOURCE_SIZE_BYTES
    ) -> Tuple[Path, IngestionAnalysis]:
        """
        Ingests and validates an arbitrary Python source file directly from a public GitHub URL.
        Returns the saved file path and complete IngestionAnalysis with robust GitHub metadata.
        """
        saved_path, meta = fetch_github_source_with_meta(
            github_url,
            output_dir=output_dir,
            max_file_size_bytes=max_file_size_bytes
        )
        analysis = self.ingest_file(str(saved_path))
        meta["ast_function_count"] = analysis.ast_function_count
        meta["ast_class_count"] = analysis.ast_class_count
        meta["functions"] = analysis.functions
        meta["classes"] = analysis.classes
        meta["all_callables"] = analysis.all_callables
        meta["dependencies"] = analysis.dependencies
        analysis.github_metadata = meta
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
        from testforge.security import SecurityGuardrail
        sec_check = SecurityGuardrail().inspect_prompt(prompt)
        if not sec_check.allowed:
            raise ValueError(f"SecurityGuardrail rejected input prompt: {sec_check.explanation}")

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
        saved_path, analysis = self.ingest_github(github_url, output_dir=output_dir)
        if self.logger:
            self.logger.log_event("GITHUB_FILE_INGESTION", {
                "github_url": github_url,
                "saved_path": str(saved_path),
                "module_name": analysis.module_name,
                "functions": analysis.functions,
                "classes": analysis.classes
            })
        return saved_path, analysis

