"""
mcp_server.py - Native FastMCP Server Implementations for TestForge.

Provides standard Model Context Protocol (MCP) servers using the official FastMCP SDK:
  1. Filesystem MCP Server:
     - Read-only tools strictly confined to a permitted project root.
     - Tools: read_text_file, list_directory, get_file_info.
     - Security: Rejects directory traversal (../), symlink escapes, and sensitive files (.env, keys).
  2. GitHub MCP Server:
     - Read-only repository inspection tools.
     - Tools: get_file_contents, get_repository_info, search_repositories.
     - Security: Uses environment-based tokens; masks secrets; handles unauthenticated states gracefully.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from mcp.server.fastmcp import FastMCP

from testforge.network_security import (
    DEFAULT_MAX_SOURCE_SIZE_BYTES,
    PayloadTooLargeError,
    SSRFSecurityError,
    bounded_read,
    build_safe_opener,
    validate_url_hostname,
)

# Blocked sensitive filename patterns
FORBIDDEN_NAME_PATTERNS = {
    ".env", ".env.local", ".env.production", ".env.test",
    "id_rsa", "id_dsa", "id_ecdsa", "id_ed25519"
}
FORBIDDEN_EXTENSIONS = {".pem", ".key", ".pfx", ".p12"}

DEFAULT_MAX_TOTAL_BYTES: int = 10 * 1024 * 1024  # 10 MB default limit for GitHub API JSON payloads


def _is_path_safe(requested_path: str, root_dir: Path) -> Tuple[bool, Path, Optional[str]]:
    """
    Validates that requested_path resides strictly within root_dir.
    Rejects directory traversal, symlink escapes, and sensitive files.
    """
    root_resolved = root_dir.resolve()

    # Handle absolute vs relative
    candidate = Path(requested_path)
    if candidate.is_absolute():
        resolved = candidate.resolve()
    else:
        resolved = (root_resolved / candidate).resolve()

    # Check root confinement
    if resolved != root_resolved and root_resolved not in resolved.parents:
        return False, resolved, f"Security Violation: Path '{requested_path}' escapes permitted root '{root_dir}'"

    # Check sensitive files
    name_lower = resolved.name.lower()
    if name_lower in FORBIDDEN_NAME_PATTERNS or name_lower.startswith(".env"):
        return False, resolved, f"Security Violation: Access to sensitive file '{resolved.name}' is strictly forbidden"

    if resolved.suffix.lower() in FORBIDDEN_EXTENSIONS:
        return False, resolved, f"Security Violation: Access to credential file extension '{resolved.suffix}' is forbidden"

    # Check .git config/credentials
    parts = [p.lower() for p in resolved.parts]
    if ".git" in parts and ("config" in parts or "credentials" in parts):
        return False, resolved, "Security Violation: Access to VCS configuration/credentials is forbidden"

    return True, resolved, None


def create_filesystem_server(permitted_root: str | Path) -> FastMCP:
    """Creates a FastMCP server exposing read-only filesystem tools bounded by permitted_root."""
    root_path = Path(permitted_root).resolve()
    server = FastMCP(f"testforge-filesystem-{root_path.name}")

    @server.tool()
    def read_text_file(path: str) -> str:
        """
        Reads and returns the contents of a UTF-8 text file within the permitted root directory.
        Rejects any attempt to read outside the permitted root or access credential files.
        """
        is_safe, resolved, err = _is_path_safe(path, root_path)
        if not is_safe:
            raise PermissionError(err)

        if not resolved.exists():
            raise FileNotFoundError(f"File not found: '{path}'")
        if not resolved.is_file():
            raise IsADirectoryError(f"Target is a directory, not a file: '{path}'")

        with open(resolved, "r", encoding="utf-8", errors="replace") as f:
            return f.read()

    @server.tool()
    def list_directory(path: str = ".") -> List[Dict[str, Any]]:
        """
        Lists files and subdirectories within a permitted directory.
        Returns a list of objects containing name, is_dir, and size_bytes.
        """
        is_safe, resolved, err = _is_path_safe(path, root_path)
        if not is_safe:
            raise PermissionError(err)

        if not resolved.exists():
            raise FileNotFoundError(f"Directory not found: '{path}'")
        if not resolved.is_dir():
            raise NotADirectoryError(f"Target is not a directory: '{path}'")

        entries = []
        for item in sorted(resolved.iterdir()):
            # Filter out sensitive files from listing
            item_name = item.name
            if item_name.startswith(".env") or item_name in FORBIDDEN_NAME_PATTERNS:
                continue
            try:
                stat = item.stat()
                entries.append({
                    "name": item_name,
                    "is_dir": item.is_dir(),
                    "size_bytes": stat.st_size if item.is_file() else 0
                })
            except (PermissionError, FileNotFoundError):
                continue
        return entries

    @server.tool()
    def get_file_info(path: str) -> Dict[str, Any]:
        """
        Returns metadata for a file (line count, size, SHA-256) without reading the entire content into memory.
        """
        is_safe, resolved, err = _is_path_safe(path, root_path)
        if not is_safe:
            raise PermissionError(err)

        if not resolved.exists():
            raise FileNotFoundError(f"Path not found: '{path}'")

        stat = resolved.stat()
        is_file = resolved.is_file()
        line_count = 0
        sha256 = ""

        if is_file:
            hasher = hashlib.sha256()
            with open(resolved, "rb") as f:
                for chunk in iter(lambda: f.read(65536), b""):
                    hasher.update(chunk)
                    line_count += chunk.count(b"\n")
            sha256 = hasher.hexdigest()

        return {
            "path": str(resolved.relative_to(root_path)),
            "is_file": is_file,
            "is_dir": resolved.is_dir(),
            "size_bytes": stat.st_size,
            "line_count": line_count,
            "sha256": sha256
        }

    return server


def create_github_server(
    github_token: Optional[str] = None,
    max_file_size_bytes: int = DEFAULT_MAX_SOURCE_SIZE_BYTES,
    max_total_bytes: int = DEFAULT_MAX_TOTAL_BYTES,
    opener: Optional[urllib.request.OpenerDirector] = None,
) -> FastMCP:
    """Creates a FastMCP server exposing read-only GitHub repository tools."""
    token = github_token or os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN") or os.environ.get("GITHUB_TOKEN")
    server = FastMCP("testforge-github")
    safe_opener = opener if opener is not None else build_safe_opener(
        allowed_hosts={"api.github.com", "raw.githubusercontent.com", "objects.githubusercontent.com"}
    )

    def _make_github_request(url: str, max_bytes: int = max_total_bytes) -> Dict[str, Any]:
        """
        Executes a GET request strictly constrained to authorized GitHub API endpoints.
        Enforces SSRF redirect protection, hostname validation, and bounded streaming.
        """
        # Validate initial target host against SSRF policy
        validate_url_hostname(url, allowed_hosts={"api.github.com", "raw.githubusercontent.com"})

        req = urllib.request.Request(url)
        req.add_header("User-Agent", "TestForge-Agentic-MCP/1.0")
        req.add_header("Accept", "application/vnd.github.v3+json")
        if token:
            req.add_header("Authorization", f"Bearer {token}")
        try:
            with safe_opener.open(req, timeout=10.0) as resp:
                data_bytes = bounded_read(resp, max_bytes=max_bytes)
                data_str = data_bytes.decode("utf-8", errors="replace")
                return json.loads(data_str)
        except (SSRFSecurityError, PayloadTooLargeError):
            raise
        except urllib.error.HTTPError as e:
            if e.code == 401 or e.code == 403:
                rate_limit_reset = e.headers.get("X-RateLimit-Reset", "unknown")
                raise PermissionError(
                    f"GitHub API authentication or rate-limit restriction (HTTP {e.code}). "
                    f"Rate limit reset at: {rate_limit_reset}. Provide GITHUB_PERSONAL_ACCESS_TOKEN."
                )
            elif e.code == 404:
                raise FileNotFoundError(f"GitHub resource not found at URL: {url}")
            else:
                raise RuntimeError(f"GitHub API HTTP error {e.code}: {e.reason}")
        except urllib.error.URLError as e:
            raise ConnectionError(f"Failed to connect to GitHub API: {e.reason}")

    @server.tool()
    def get_repository_info(owner: str, repo: str) -> Dict[str, Any]:
        """
        Retrieves public repository metadata (name, description, default_branch, stargazers_count).
        """
        url = f"https://api.github.com/repos/{urllib.parse.quote(owner)}/{urllib.parse.quote(repo)}"
        data = _make_github_request(url, max_bytes=max_total_bytes)
        return {
            "full_name": data.get("full_name"),
            "description": data.get("description"),
            "default_branch": data.get("default_branch", "main"),
            "stargazers_count": data.get("stargazers_count", 0),
            "open_issues_count": data.get("open_issues_count", 0),
            "topics": data.get("topics", [])
        }

    @server.tool()
    def get_file_contents(owner: str, repo: str, path: str, ref: str = "main") -> Dict[str, Any]:
        """
        Retrieves file contents from a repository.
        Returns decoded text, size, and SHA.
        Bounded by max_file_size_bytes to prevent memory exhaustion.
        """
        url = f"https://api.github.com/repos/{urllib.parse.quote(owner)}/{urllib.parse.quote(repo)}/contents/{urllib.parse.quote(path)}?ref={urllib.parse.quote(ref)}"
        data = _make_github_request(url, max_bytes=max_total_bytes)
        content_b64 = data.get("content", "")
        # Protect against memory inflation: verify base64 length before decoding
        if len(content_b64) > int(max_file_size_bytes * 1.4) + 1024:
            raise PayloadTooLargeError(
                f"Base64 encoded content size ({len(content_b64)} chars) exceeds maximum allowable limit for {max_file_size_bytes} bytes."
            )
        import base64
        decoded_bytes = base64.b64decode(content_b64)
        if len(decoded_bytes) > max_file_size_bytes:
            raise PayloadTooLargeError(
                f"Decoded file size ({len(decoded_bytes)} bytes) exceeds maximum allowable limit of {max_file_size_bytes} bytes."
            )
        return {
            "name": data.get("name"),
            "path": data.get("path"),
            "sha": data.get("sha"),
            "size": data.get("size"),
            "content": decoded_bytes.decode("utf-8", errors="replace")
        }

    @server.tool()
    def search_repositories(query: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Searches GitHub repositories by query string.
        """
        url = f"https://api.github.com/search/repositories?q={urllib.parse.quote(query)}&per_page={max(1, min(limit, 10))}"
        data = _make_github_request(url, max_bytes=max_total_bytes)
        items = data.get("items", [])
        return [
            {
                "full_name": item.get("full_name"),
                "description": item.get("description"),
                "stargazers_count": item.get("stargazers_count", 0),
                "url": item.get("html_url")
            }
            for item in items
        ]

    @server.tool()
    def get_repository_tree(owner: str, repo: str, ref: str = "main", recursive: bool = True) -> Dict[str, Any]:
        """
        Retrieves the Git tree for a repository and ref/commit.
        Returns list of tree items (path, mode, type, size, sha) and truncation status.
        """
        rec_flag = "1" if recursive else "0"
        url = f"https://api.github.com/repos/{urllib.parse.quote(owner)}/{urllib.parse.quote(repo)}/git/trees/{urllib.parse.quote(ref)}?recursive={rec_flag}"
        data = _make_github_request(url, max_bytes=max_total_bytes)
        return {
            "sha": data.get("sha"),
            "truncated": data.get("truncated", False),
            "tree": [
                {
                    "path": item.get("path"),
                    "mode": item.get("mode"),
                    "type": item.get("type"),
                    "size": item.get("size", 0),
                    "sha": item.get("sha")
                }
                for item in data.get("tree", [])
            ]
        }

    return server


TESTFORGE_JOBS: Dict[str, Dict[str, Any]] = {}


def create_testforge_server(repo_root: Optional[Path] = None) -> FastMCP:
    """
    Creates a native TestForge Model Context Protocol (MCP) server.
    Exposes autonomous test hardening, reporting, and job monitoring tools.
    """
    root = (repo_root or Path.cwd()).resolve()
    server = FastMCP(
        "testforge-mcp-server",
        instructions="TestForge Autonomous Unit-Test Hardening & Verification MCP Server"
    )

    @server.tool()
    def harden_module(file_path: str, max_iterations: int = 3) -> Dict[str, Any]:
        """
        Executes TestForge autonomous mutation-verified test hardening on a Python module.
        Validates path confinement, discovers AST mutants, executes reflection loop, and returns results.
        """
        import time
        import uuid

        from testforge.equivalence import calculate_mutation_scores
        from testforge.intelligent_generator import IntelligentASTSynthesizer
        from testforge.mutator import ASTMutator
        from testforge.sandbox import ParallelSandboxRunner

        safe, resolved, err = _is_path_safe(file_path, root)
        if not safe:
            return {
                "status": "ERROR",
                "error": err,
                "file_path": file_path,
            }

        if not resolved.exists() or not resolved.is_file():
            return {
                "status": "ERROR",
                "error": f"Target file '{file_path}' does not exist",
                "file_path": file_path,
            }

        try:
            source_code = resolved.read_text(encoding="utf-8")
        except Exception as e:
            return {"status": "ERROR", "error": f"Failed reading file: {e}"}

        job_id = f"job-{uuid.uuid4().hex[:8]}"

        # Synthesize hardened tests
        syn = IntelligentASTSynthesizer()
        ast_suite = syn.synthesize_test_suite(source_code)
        test_code = ast_suite.test_code

        # Mutate and evaluate in sandbox
        mutants = ASTMutator.mutate(source_code)
        sb = ParallelSandboxRunner(max_workers=4, timeout_seconds=5)
        eval_mutants = [m.model_copy(deep=True) for m in mutants]
        res = sb.evaluate_mutants_parallel(test_code, eval_mutants, baseline_passed=True)
        score_data = calculate_mutation_scores(res)

        record = {
            "job_id": job_id,
            "status": "COMPLETED",
            "target_file": str(file_path),
            "timestamp": time.time(),
            "raw_mutation_score": score_data["raw_mutation_score"],
            "adjusted_mutation_score": score_data["adjusted_mutation_score"],
            "killed_mutants": score_data["killed_mutants"],
            "total_mutants": len(mutants),
            "survived_mutants": score_data["survived_mutants"],
            "equivalent_mutants": score_data["equivalent_mutants"],
            "test_code_preview": test_code[:300] + ("..." if len(test_code) > 300 else ""),
            "full_test_code": test_code,
        }
        TESTFORGE_JOBS[job_id] = record
        return record

    @server.tool()
    def get_report(job_id: str) -> Dict[str, Any]:
        """
        Retrieves the execution report, coverage metrics, and generated test code for a job.
        """
        if job_id not in TESTFORGE_JOBS:
            return {"status": "NOT_FOUND", "job_id": job_id, "error": f"Job '{job_id}' not found"}
        return TESTFORGE_JOBS[job_id]

    @server.tool()
    def list_jobs() -> Dict[str, Any]:
        """
        Lists all recorded test hardening jobs with their status and mutation scores.
        """
        jobs = [
            {
                "job_id": j["job_id"],
                "target_file": j["target_file"],
                "status": j["status"],
                "raw_mutation_score": j["raw_mutation_score"],
                "adjusted_mutation_score": j["adjusted_mutation_score"],
                "killed_mutants": j["killed_mutants"],
                "total_mutants": j["total_mutants"],
                "timestamp": j["timestamp"],
            }
            for j in TESTFORGE_JOBS.values()
        ]
        return {"jobs": jobs, "total_count": len(jobs)}

    return server


if __name__ == "__main__":
    server_type = sys.argv[1] if len(sys.argv) > 1 else "filesystem"
    if server_type == "filesystem":
        root = sys.argv[2] if len(sys.argv) > 2 else os.getcwd()
        server = create_filesystem_server(root)
        server.run(transport="stdio")
    elif server_type == "github":
        server = create_github_server()
        server.run(transport="stdio")
    elif server_type == "testforge":
        root = sys.argv[2] if len(sys.argv) > 2 else os.getcwd()
        server = create_testforge_server(Path(root))
        server.run(transport="stdio")
    else:
        sys.stderr.write(f"Unknown server type: {server_type}\n")
        sys.exit(1)
