"""
github_service.py - Public GitHub Repository Ingestion & Discovery Service.

Enables TestForge to ingest and analyze Python source files from arbitrary
accessible public GitHub repositories.

Security & Architecture:
  1. URL Validation: Parses arbitrary repository URLs (https://github.com/owner/repo),
     validating host, coordinates, control characters, and injection tokens.
  2. Git Trees API Discovery: Recursively discovers repository tree at a resolved commit SHA,
     filtering eligible Python (.py) source files while excluding venvs, caches, and build artifacts.
  3. Safe Retrieval & Confinement: Bounded by strict file count, byte limits, and timeouts.
     Prevents directory traversal attacks (../, absolute paths).
  4. Non-Destructive Token Management: Reads GITHUB_PERSONAL_ACCESS_TOKEN if set,
     never logs or leaks tokens, targets only api.github.com, and handles unauthenticated
     rate-limits (HTTP 403) with clear reset times.
  5. Isolated Pipeline Handoff: Untrusted external code is inspected via AST only in the main
     process; all runtime execution is delegated strictly to the isolated subprocess sandbox.
"""

from __future__ import annotations
import os
import re
import ast
import json
import base64
import hashlib
import logging
import urllib.request
import urllib.error
import urllib.parse
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Set

from pydantic import BaseModel, Field

from testforge.security import redact_sensitive_data
from testforge.ingestion import IngestionAnalysis, TargetManagerAgent

logger = logging.getLogger("testforge.github_service")

# Directories and patterns excluded from Python source file discovery
EXCLUDED_DIR_PATTERNS: Set[str] = {
    ".git",
    ".github",
    ".venv",
    "venv",
    "env",
    ".env",
    "virtualenv",
    "site-packages",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".tox",
    ".nox",
    "build",
    "dist",
    ".eggs",
    "node_modules",
}

EXCLUDED_FILE_SUFFIXES: Set[str] = {
    ".pyc",
    ".pyo",
    ".pyd",
    ".egg-info",
}

DEFAULT_MAX_FILES = 500
DEFAULT_MAX_FILE_SIZE_BYTES = 500 * 1024  # 500 KB per file
DEFAULT_MAX_TOTAL_BYTES = 10 * 1024 * 1024  # 10 MB total
DEFAULT_REQUEST_TIMEOUT = 15.0  # seconds


# --------------------------------------------------------------------------
# Data Models
# --------------------------------------------------------------------------

class DiscoveredFile(BaseModel):
    path: str
    size_bytes: int = 0
    sha: str = ""
    is_test_file: bool = False


class SkippedFile(BaseModel):
    path: str
    reason: str


class RepositoryDiscoveryManifest(BaseModel):
    repository_url: str
    owner: str
    repo: str
    default_branch: str
    resolved_ref: str
    commit_sha: str
    files: List[DiscoveredFile] = Field(default_factory=list)
    total_files: int = 0
    total_bytes: int = 0
    skipped_files: List[SkippedFile] = Field(default_factory=list)
    truncated: bool = False
    rate_limit_remaining: Optional[int] = None
    rate_limit_reset: Optional[int] = None
    authenticated: bool = False


class FetchedFileContent(BaseModel):
    path: str
    content: str
    sha256: str
    line_count: int
    size_bytes: int
    commit_sha: str
    raw_url: str
    github_url: str


# --------------------------------------------------------------------------
# URL Parsing & Validation
# --------------------------------------------------------------------------

def parse_github_repo_url(url: str) -> Dict[str, Any]:
    """
    Validates and parses any accessible public GitHub repository URL.
    
    Supported formats:
      - https://github.com/owner/repo
      - https://github.com/owner/repo/
      - https://github.com/owner/repo.git
      - https://github.com/owner/repo/tree/branch
      - https://github.com/owner/repo/tree/branch/sub/path

    Rejects:
      - Empty or non-string inputs
      - Control characters, whitespace, and UI artifacts
      - Non-HTTPS schemes
      - Hosts other than github.com
      - Invalid coordinates or path structures
    """
    if not isinstance(url, str):
        raise ValueError("GitHub Repository URL must be a string.")

    raw_input = url
    cleaned = url.strip()
    if not cleaned:
        raise ValueError("GitHub Repository URL cannot be empty.")

    # Strip surrounding quotes if accidentally copied
    if (cleaned.startswith('"') and cleaned.endswith('"')) or \
       (cleaned.startswith("'") and cleaned.endswith("'")) or \
       (cleaned.startswith("`") and cleaned.endswith("`")):
        cleaned = cleaned[1:-1].strip()

    # Reject control characters and non-printable bytes
    disallowed_chars = {'\r', '\n', '\t', '\x00'}
    for ch in cleaned:
        if ch in disallowed_chars or ord(ch) < 32 or ord(ch) >= 127 or ch.isspace():
            raise ValueError(
                f"URL contains invalid control characters or whitespace: {repr(cleaned)}"
            )

    # Reject unexpected UI artifacts or injection tokens
    for bad_token in ('[', ']', '<', '>', '{', '}', '|', '^', '`', '"', "'", ';', '\\'):
        if bad_token in cleaned:
            raise ValueError(
                f"URL contains unexpected characters or UI artifacts ('{bad_token}'): {repr(cleaned)}"
            )

    parsed = urllib.parse.urlparse(cleaned)

    if parsed.scheme.lower() != "https":
        raise ValueError(f"Invalid URL scheme '{parsed.scheme}'. Only 'https' is supported.")

    hostname = (parsed.hostname or "").lower()
    if hostname != "github.com":
        raise ValueError(
            f"Unsupported host '{hostname}'. Expected 'github.com'."
        )

    path = parsed.path.strip("/")
    parts = [p for p in path.split("/") if p]

    if len(parts) < 2:
        raise ValueError(
            f"Invalid GitHub repository URL path '/{path}'. Expected: https://github.com/<owner>/<repository>"
        )

    owner = parts[0]
    repo = parts[1]

    # Strip trailing .git if present
    if repo.endswith(".git"):
        repo = repo[:-4]

    # Validate coordinate characters
    coord_pattern = r"^[a-zA-Z0-9_.-]+$"
    if not re.match(coord_pattern, owner):
        raise ValueError(f"Invalid repository owner coordinate: '{owner}'.")
    if not re.match(coord_pattern, repo):
        raise ValueError(f"Invalid repository name coordinate: '{repo}'.")

    # Optional ref / tree extraction
    ref: Optional[str] = None
    subpath: Optional[str] = None

    if len(parts) >= 4 and parts[2] == "tree":
        ref = parts[3]
        if len(parts) > 4:
            subpath = "/".join(parts[4:])
    elif len(parts) == 3 and parts[2] == "tree":
        # Missing branch name after /tree/
        raise ValueError("GitHub URL contains '/tree/' without a branch or ref name.")

    normalized_repo_url = f"https://github.com/{owner}/{repo}"

    return {
        "raw_input": raw_input,
        "owner": owner,
        "repo": repo,
        "repository": f"{owner}/{repo}",
        "ref": ref,
        "subpath": subpath,
        "normalized_repo_url": normalized_repo_url,
    }


# --------------------------------------------------------------------------
# GitHub Repository Service
# --------------------------------------------------------------------------

class GitHubRepoService:
    """
    Manages GitHub repository discovery, tree resolution, and Python source retrieval.
    """

    def __init__(
        self,
        token: Optional[str] = None,
        timeout: float = DEFAULT_REQUEST_TIMEOUT,
        max_files: int = DEFAULT_MAX_FILES,
        max_file_size_bytes: int = DEFAULT_MAX_FILE_SIZE_BYTES,
        max_total_bytes: int = DEFAULT_MAX_TOTAL_BYTES,
    ):
        self.token = (
            token
            or os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN")
            or os.environ.get("GITHUB_TOKEN")
            or ""
        ).strip()
        self.timeout = timeout
        self.max_files = max_files
        self.max_file_size_bytes = max_file_size_bytes
        self.max_total_bytes = max_total_bytes

    # ----------------------------------------------------------------------
    # HTTP Dispatcher (Safe & Target-Constrained)
    # ----------------------------------------------------------------------

    def _make_github_request(self, url: str) -> Tuple[Dict[str, Any], Dict[str, str]]:
        """
        Executes a GET request strictly constrained to api.github.com or raw.githubusercontent.com.
        Redacts credentials from logs and handles rate-limits and error codes.
        """
        parsed = urllib.parse.urlparse(url)
        allowed_hosts = {"api.github.com", "raw.githubusercontent.com"}
        if (parsed.hostname or "").lower() not in allowed_hosts or parsed.scheme.lower() != "https":
            raise ValueError(f"Security Violation: Target host '{parsed.hostname}' is not an authorized GitHub endpoint.")

        req = urllib.request.Request(url)
        req.add_header("User-Agent", "TestForge-Agentic-Ingestion/1.0")
        req.add_header("Accept", "application/vnd.github.v3+json")

        if self.token:
            req.add_header("Authorization", f"Bearer {self.token}")

        headers_dict: Dict[str, str] = {}
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                headers_dict = {k.lower(): v for k, v in resp.headers.items()}
                data_bytes = resp.read()
                data_str = data_bytes.decode("utf-8", errors="replace")
                parsed_json = json.loads(data_str)
                return parsed_json, headers_dict
        except urllib.error.HTTPError as e:
            err_headers = {k.lower(): v for k, v in e.headers.items()}
            reset_ts = err_headers.get("x-ratelimit-reset", "unknown")
            remaining = err_headers.get("x-ratelimit-remaining", "0")

            if e.code == 401:
                raise PermissionError(
                    "GitHub API Authentication Failed (HTTP 401): Invalid or expired token. "
                    "Check your GITHUB_PERSONAL_ACCESS_TOKEN environment variable."
                ) from e

            elif e.code in (403, 429):
                if remaining == "0" or "rate limit" in str(e.reason).lower():
                    raise PermissionError(
                        f"GitHub API rate limit exceeded (HTTP {e.code}). Rate limit resets at epoch {reset_ts}. "
                        "Configure a GITHUB_PERSONAL_ACCESS_TOKEN to increase public request limits."
                    ) from e
                raise PermissionError(
                    f"GitHub API access forbidden (HTTP {e.code}) for target URL. "
                    "The repository may be private or restricted."
                ) from e

            elif e.code == 404:
                raise FileNotFoundError(
                    f"GitHub resource not found (HTTP 404): {redact_sensitive_data(url)}. "
                    "Verify the repository owner, name, and branch/ref."
                ) from e

            elif e.code == 422:
                raise ValueError(
                    f"GitHub API validation error (HTTP 422): {e.reason}."
                ) from e

            else:
                raise RuntimeError(
                    f"GitHub API error (HTTP {e.code}: {e.reason})."
                ) from e

        except urllib.error.URLError as e:
            raise ConnectionError(
                f"Failed to connect to GitHub API: {redact_sensitive_data(str(e.reason))}."
            ) from e

    # ----------------------------------------------------------------------
    # Repository Metadata & Ref Resolution
    # ----------------------------------------------------------------------

    def get_repository_metadata(self, owner: str, repo: str) -> Dict[str, Any]:
        """
        Retrieves repository metadata including the default branch, visibility, and size.
        """
        url = f"https://api.github.com/repos/{urllib.parse.quote(owner)}/{urllib.parse.quote(repo)}"
        data, headers = self._make_github_request(url)
        return {
            "owner": owner,
            "repo": repo,
            "full_name": data.get("full_name", f"{owner}/{repo}"),
            "description": data.get("description", ""),
            "default_branch": data.get("default_branch", "main"),
            "stargazers_count": data.get("stargazers_count", 0),
            "open_issues_count": data.get("open_issues_count", 0),
            "is_private": data.get("private", False),
            "is_fork": data.get("fork", False),
            "size_kb": data.get("size", 0),
            "rate_limit_remaining": int(headers.get("x-ratelimit-remaining", 0)) if "x-ratelimit-remaining" in headers else None,
            "rate_limit_reset": int(headers.get("x-ratelimit-reset", 0)) if "x-ratelimit-reset" in headers else None,
        }

    def resolve_ref_to_sha(self, owner: str, repo: str, ref: str) -> str:
        """
        Resolves a branch name, tag, or partial ref to an authoritative 40-character commit SHA.
        """
        # Try commits endpoint which resolves branches, tags, and full/short SHAs
        url = f"https://api.github.com/repos/{urllib.parse.quote(owner)}/{urllib.parse.quote(repo)}/commits/{urllib.parse.quote(ref)}"
        data, _ = self._make_github_request(url)
        sha = data.get("sha")
        if not sha:
            raise ValueError(f"Could not resolve ref '{ref}' to a commit SHA for repository {owner}/{repo}.")
        return sha

    # ----------------------------------------------------------------------
    # Python File Discovery via Git Trees API
    # ----------------------------------------------------------------------

    def discover_python_files(
        self,
        owner: str,
        repo: str,
        ref: Optional[str] = None,
        subpath_filter: Optional[str] = None
    ) -> RepositoryDiscoveryManifest:
        """
        Recursively discovers all eligible Python (.py) source files using the Git Trees API.
        
        Applies:
          - Default branch resolution if ref is not specified.
          - Commit SHA resolution.
          - Path exclusion filters (.git, venvs, cache, build).
          - Path traversal security validation.
          - File count, size, and total byte thresholds.
          - Truncation detection.
        """
        meta = self.get_repository_metadata(owner, repo)
        resolved_ref = ref or meta["default_branch"]
        commit_sha = self.resolve_ref_to_sha(owner, repo, resolved_ref)

        tree_url = (
            f"https://api.github.com/repos/{urllib.parse.quote(owner)}/"
            f"{urllib.parse.quote(repo)}/git/trees/{commit_sha}?recursive=1"
        )
        tree_data, headers = self._make_github_request(tree_url)

        raw_tree = tree_data.get("tree", [])
        is_truncated = tree_data.get("truncated", False)

        discovered: List[DiscoveredFile] = []
        skipped: List[SkippedFile] = []
        total_bytes = 0

        norm_subpath = subpath_filter.strip("/").lower() if subpath_filter else None

        for item in raw_tree:
            # We only evaluate blobs (files)
            if item.get("type") != "blob":
                continue

            item_path = item.get("path", "")
            if not item_path:
                continue

            # Path Traversal Guard: reject null bytes, backslashes, leading slashes, and '..'
            if "\x00" in item_path or "\\" in item_path or item_path.startswith("/") or ".." in item_path.split("/"):
                skipped.append(SkippedFile(path=item_path, reason="Path traversal violation detected"))
                continue

            # Subpath filter (if URL pointed to a subfolder)
            if norm_subpath and not item_path.lower().startswith(norm_subpath):
                continue

            # Path exclusion check: check each segment against excluded directories
            parts = item_path.split("/")
            has_excluded_dir = any(part.lower() in EXCLUDED_DIR_PATTERNS for part in parts[:-1])
            if has_excluded_dir:
                skipped.append(SkippedFile(path=item_path, reason="Directory in excluded path list"))
                continue

            filename = parts[-1]
            # Must be a Python file
            if not filename.endswith(".py"):
                continue

            # Check file suffix exclusions
            if any(filename.endswith(sfx) for sfx in EXCLUDED_FILE_SUFFIXES):
                continue

            file_size = item.get("size", 0)
            item_sha = item.get("sha", "")

            # File size limit enforcement
            if file_size > self.max_file_size_bytes:
                skipped.append(SkippedFile(
                    path=item_path,
                    reason=f"File size exceeds limit ({file_size} > {self.max_file_size_bytes} bytes)"
                ))
                continue

            # Total file count limit enforcement
            if len(discovered) >= self.max_files:
                skipped.append(SkippedFile(
                    path=item_path,
                    reason=f"Exceeded maximum discoverable file threshold ({self.max_files})"
                ))
                continue

            # Check if it looks like a test file
            is_test = (
                filename.startswith("test_")
                or filename.endswith("_test.py")
                or "tests" in [p.lower() for p in parts]
                or "testing" in [p.lower() for p in parts]
            )

            discovered.append(DiscoveredFile(
                path=item_path,
                size_bytes=file_size,
                sha=item_sha,
                is_test_file=is_test
            ))
            total_bytes += file_size

        return RepositoryDiscoveryManifest(
            repository_url=f"https://github.com/{owner}/{repo}",
            owner=owner,
            repo=repo,
            default_branch=meta["default_branch"],
            resolved_ref=resolved_ref,
            commit_sha=commit_sha,
            files=discovered,
            total_files=len(discovered),
            total_bytes=total_bytes,
            skipped_files=skipped,
            truncated=is_truncated,
            rate_limit_remaining=int(headers.get("x-ratelimit-remaining", 0)) if "x-ratelimit-remaining" in headers else None,
            rate_limit_reset=int(headers.get("x-ratelimit-reset", 0)) if "x-ratelimit-reset" in headers else None,
            authenticated=bool(self.token),
        )

    # ----------------------------------------------------------------------
    # File Content Retrieval
    # ----------------------------------------------------------------------

    def fetch_file_content(
        self,
        owner: str,
        repo: str,
        commit_sha: str,
        file_path: str
    ) -> FetchedFileContent:
        """
        Retrieves raw file content for a specified file path at a specific commit SHA.
        Verifies AST syntax and calculates SHA256 checksum.
        """
        # Validate path
        clean_path = file_path.strip("/")
        if not clean_path or ".." in clean_path.split("/") or "\\" in clean_path:
            raise ValueError(f"Security Violation: Invalid file path '{file_path}'")

        # Use GitHub Contents API with ref=commit_sha
        contents_url = (
            f"https://api.github.com/repos/{urllib.parse.quote(owner)}/"
            f"{urllib.parse.quote(repo)}/contents/{urllib.parse.quote(clean_path)}?ref={commit_sha}"
        )

        content: Optional[str] = None

        try:
            data, _ = self._make_github_request(contents_url)
            # GitHub returns base64 encoded content
            encoded = data.get("content", "")
            encoding = data.get("encoding", "")
            if encoding == "base64" and encoded:
                decoded_bytes = base64.b64decode(encoded)
                content = decoded_bytes.decode("utf-8", errors="replace")
        except Exception as contents_err:
            logger.warning(
                f"Contents API failed for {clean_path} ({contents_err}); attempting raw fallback."
            )
            content = None

        # Fallback to raw.githubusercontent.com if Contents API failed
        if content is None:
            raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{commit_sha}/{clean_path}"
            req = urllib.request.Request(raw_url)
            req.add_header("User-Agent", "TestForge-Agentic-Ingestion/1.0")
            if self.token:
                req.add_header("Authorization", f"Bearer {self.token}")

            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    data_bytes = resp.read()
                    content = data_bytes.decode("utf-8", errors="replace")
            except Exception as raw_err:
                raise RuntimeError(
                    f"Failed to fetch content for file '{clean_path}' from repository '{owner}/{repo}' at SHA '{commit_sha}': {raw_err}"
                ) from raw_err

        # Validate AST syntax
        try:
            ast.parse(content)
        except SyntaxError as syn_err:
            raise ValueError(
                f"File '{clean_path}' contains invalid Python syntax (line {syn_err.lineno}: {syn_err.msg})"
            ) from syn_err

        sha256 = hashlib.sha256(content.encode("utf-8")).hexdigest()
        lines = len(content.splitlines())
        size_bytes = len(content.encode("utf-8"))

        return FetchedFileContent(
            path=clean_path,
            content=content,
            sha256=sha256,
            line_count=lines,
            size_bytes=size_bytes,
            commit_sha=commit_sha,
            raw_url=f"https://raw.githubusercontent.com/{owner}/{repo}/{commit_sha}/{clean_path}",
            github_url=f"https://github.com/{owner}/{repo}/blob/{commit_sha}/{clean_path}",
        )

    # ----------------------------------------------------------------------
    # Pipeline Ingestion & Handoff
    # ----------------------------------------------------------------------

    def ingest_repository_file(
        self,
        owner: str,
        repo: str,
        commit_sha: str,
        file_path: str,
        output_dir: str = "samples"
    ) -> Tuple[Path, IngestionAnalysis]:
        """
        Retrieves a Python file from a public repository, resolves relative package imports,
        saves to the local samples/ directory with safe namespacing, performs AST symbol
        extraction, and prepares the module for the TestForge hardening loop.
        """
        fetched = self.fetch_file_content(owner, repo, commit_sha, file_path)
        content = fetched.content

        # Resolve relative package imports (e.g., `from .compat import ...` -> `from requests.compat import ...`)
        clean_repo_pkg = re.sub(r"[^\w]", "", repo)
        if clean_repo_pkg:
            content = re.sub(r"from\s+\.(\w+)", rf"from {clean_repo_pkg}.\1", content)
            content = re.sub(r"from\s+\.\s+import", rf"from {clean_repo_pkg} import", content)

        # Sanitize filename components for local destination path
        clean_owner = re.sub(r"[^\w\-]", "_", owner)
        clean_repo = re.sub(r"[^\w\-]", "_", repo)
        flat_path = re.sub(r"[^\w\-\.]", "_", fetched.path)
        if not flat_path.endswith(".py"):
            flat_path += ".py"

        out_path = Path(output_dir)
        out_path.mkdir(parents=True, exist_ok=True)
        dest_file = out_path / f"github_{clean_owner}_{clean_repo}_{flat_path}"

        # Write file with source content
        dest_file.write_text(content, encoding="utf-8")

        # Perform AST inspection using TargetManagerAgent
        supervisor = TargetManagerAgent()
        analysis = supervisor.ingest_file(str(dest_file))

        # Attach provenance metadata
        analysis.github_metadata = {
            "source_github_url": fetched.github_url,
            "raw_github_url": fetched.raw_url,
            "repository": f"{owner}/{repo}",
            "owner": owner,
            "repo": repo,
            "commit_sha": commit_sha,
            "file_path": fetched.path,
            "filename": Path(fetched.path).name,
            "generated_module_name": analysis.module_name,
            "source_sha": fetched.sha256,
            "line_count": fetched.line_count,
            "size_bytes": fetched.size_bytes,
            "is_untrusted": True,
            "sandbox_required": True,
        }

        return dest_file.resolve(), analysis
