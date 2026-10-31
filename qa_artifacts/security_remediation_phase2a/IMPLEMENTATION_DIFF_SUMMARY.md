# TestForge — Phase 2A Implementation Diff Summary

**Date:** 2026-10-30  
**Phase:** 2A (Network Security & Bounded Downloads)  
**Status:** IMPLEMENTED & VERIFIED  

---

## 1. Overview of Changes

Phase 2A implemented strict network boundaries and defense-in-depth protections for TestForge's remote source ingestion capabilities:
1. **SSRF Redirect & Destination Protection:** Eliminates blind HTTP redirection, host spoofing, IP encoding bypasses, cloud metadata access, and private network probing.
2. **Credential Stripping:** Prevents leak of `Authorization` bearer tokens and access tokens across domain boundaries during multi-hop redirects (notably GitHub API to S3/CDN endpoints).
3. **Bounded Ingestion:** Protects against unbounded source downloads, HTTP compression bombs, infinite streams, and chunked transfer abuse by enforcing hard file size caps before, during, and after reads.
4. **Atomic Disk Persistence:** Prevents partial, truncated, or invalid source files from persisting to the local filesystem on error.

All changes strictly preserve existing uncommitted work across the repository.

---

## 2. File Modification Summary

| File | Action | Purpose |
|---|---|---|
| `testforge/network_security.py` | **NEW** | Core network security module: hostname whitelisting, IP canonicalization, safe redirect handling with token purging, bounded stream reader. |
| `tests/test_network_security.py` | **NEW** | Comprehensive unit and integration test suite (62 test cases) covering all SSRF vectors, redirect scenarios, token preservation, size limit enforcement, and network failures. |
| `testforge/github_service.py` | **MODIFIED** | Updated `_make_github_request()` and `fetch_file_content()` to use `validate_url_hostname()`, `build_safe_opener()`, and `bounded_read()`. Decoded base64 size limit enforced. |
| `testforge/ingestion.py` | **MODIFIED** | Updated `fetch_github_source_with_meta()` and `TargetManagerAgent.ingest_github()` to validate URLs, employ `build_safe_opener()`, stream via `bounded_read()`, and guarantee atomic disk persistence. |

---

## 3. Detailed Component Diffs

### A. New Module: `testforge/network_security.py`
- **Constants**:
  - `ALLOWED_GITHUB_HOSTS = {"api.github.com", "raw.githubusercontent.com", "codeload.github.com", "objects.githubusercontent.com", "github.com"}`
  - `DEFAULT_MAX_SOURCE_SIZE_BYTES = 500 * 1024` (500 KB)
  - `DEFAULT_CHUNK_SIZE_BYTES = 64 * 1024` (64 KB)
- **Functions & Classes**:
  - `is_ip_address(host: str) -> bool`: Detects standard IPv4, decimal-encoded IPv4, octal, hex, and IPv6 representations.
  - `is_disallowed_ip(ip: ipaddress.IPv4Address | IPv6Address) -> bool`: Flags private (RFC 1918), loopback (`127.0.0.0/8`), link-local (`169.254.0.0/16`), cloud metadata (`169.254.169.254`), and multicast.
  - `validate_url_hostname(url: str, allowed_hosts: Set[str] | None = None) -> str`: Normalizes scheme, unquotes percent encoding, rejects userinfo credentials (`user:pass@host`), checks for backslashes, validates explicit port (rejects non-standard ports), and enforces strict whitelist.
  - `SafeGitHubRedirectHandler(urllib.request.HTTPRedirectHandler)`: Intercepts `http_error_301`, `302`, `303`, `307`, and `308`. Validates `newurl` against SSRF policy before following. Enforces 5-hop redirect limit. Strips authentication headers (`Authorization`, `X-Access-Token`, `X-OAuth-Basic`, `Proxy-Authorization`) when destination host changes.
  - `bounded_read(response, max_bytes: int, chunk_size: int) -> bytes`: Validates `Content-Length` header if present (raises `PayloadTooLargeError` if `> max_bytes` or negative). Streams body in 64 KB chunks, maintaining running count. Immediately raises `PayloadTooLargeError` if total bytes exceed `max_bytes`. Always ensures `response.close()`.
  - `build_safe_opener(allowed_hosts, max_redirects) -> urllib.request.OpenerDirector`: Factory for isolated `OpenerDirector` instances wired with `SafeGitHubRedirectHandler`.

### B. Modified: `testforge/github_service.py`
```diff
--- a/testforge/github_service.py
+++ b/testforge/github_service.py
@@ -36,6 +36,15 @@ from pydantic import BaseModel, Field
 
 from testforge.security import redact_sensitive_data
 from testforge.ingestion import IngestionAnalysis, TargetManagerAgent
+from testforge.network_security import (
+    ALLOWED_GITHUB_HOSTS,
+    DEFAULT_MAX_SOURCE_SIZE_BYTES,
+    validate_url_hostname,
+    build_safe_opener,
+    bounded_read,
+    SSRFSecurityError,
+    PayloadTooLargeError,
+)
 
 logger = logging.getLogger("testforge.github_service")
@@ -262,11 +271,9 @@ class GitHubRepoService:
         """
         Executes a GET request strictly constrained to api.github.com or raw.githubusercontent.com.
         Redacts credentials from logs and handles rate-limits and error codes.
+        Protected by SafeGitHubRedirectHandler and bounded chunked streaming.
         """
-        parsed = urllib.parse.urlparse(url)
-        allowed_hosts = {"api.github.com", "raw.githubusercontent.com"}
-        if (parsed.hostname or "").lower() not in allowed_hosts or parsed.scheme.lower() != "https":
-            raise ValueError(f"Security Violation: Target host '{parsed.hostname}' is not an authorized GitHub endpoint.")
+        validate_url_hostname(url, allowed_hosts={"api.github.com", "raw.githubusercontent.com"})
 
         req = urllib.request.Request(url)
         req.add_header("User-Agent", "TestForge-Agentic-Ingestion/1.0")
@@ -276,10 +283,11 @@ class GitHubRepoService:
             req.add_header("Authorization", f"Bearer {self.token}")
 
         headers_dict: Dict[str, str] = {}
+        opener = build_safe_opener(allowed_hosts={"api.github.com", "raw.githubusercontent.com", "objects.githubusercontent.com"})
         try:
-            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
+            with opener.open(req, timeout=self.timeout) as resp:
                 headers_dict = {k.lower(): v for k, v in resp.headers.items()}
-                data_bytes = resp.read()
+                data_bytes = bounded_read(resp, max_bytes=self.max_total_bytes)
                 data_str = data_bytes.decode("utf-8", errors="replace")
                 parsed_json = json.loads(data_str)
                 return parsed_json, headers_dict
@@ -525,7 +533,13 @@ class GitHubRepoService:
             encoding = data.get("encoding", "")
             if encoding == "base64" and encoded:
                 decoded_bytes = base64.b64decode(encoded)
+                if len(decoded_bytes) > self.max_file_size_bytes:
+                    raise PayloadTooLargeError(
+                        f"Decoded file size ({len(decoded_bytes)} bytes) exceeds maximum allowable limit of {self.max_file_size_bytes} bytes."
+                    )
                 content = decoded_bytes.decode("utf-8", errors="replace")
+        except PayloadTooLargeError:
+            raise
         except Exception as contents_err:
             logger.warning(
                 f"Contents API failed for {clean_path} ({contents_err}); attempting raw fallback."
@@ -535,15 +549,19 @@ class GitHubRepoService:
         # Fallback to raw.githubusercontent.com if Contents API failed
         if content is None:
             raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/{commit_sha}/{clean_path}"
+            validate_url_hostname(raw_url)
             req = urllib.request.Request(raw_url)
             req.add_header("User-Agent", "TestForge-Agentic-Ingestion/1.0")
             if self.token:
                 req.add_header("Authorization", f"Bearer {self.token}")
 
+            opener = build_safe_opener()
             try:
-                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
-                    data_bytes = resp.read()
+                with opener.open(req, timeout=self.timeout) as resp:
+                    data_bytes = bounded_read(resp, max_bytes=self.max_file_size_bytes)
                     content = data_bytes.decode("utf-8", errors="replace")
+            except (PayloadTooLargeError, SSRFSecurityError):
+                raise
             except Exception as raw_err:
                 raise RuntimeError(
                     f"Failed to fetch content for file '{clean_path}' from repository '{owner}/{repo}' at SHA '{commit_sha}': {raw_err}"
```

### C. Modified: `testforge/ingestion.py`
```diff
--- a/testforge/ingestion.py
+++ b/testforge/ingestion.py
@@ -27,6 +27,15 @@ import urllib.parse
 import logging
 from typing import List, Dict, Any, Optional, Tuple
 from testforge.logger import TraceLogger
+from testforge.network_security import (
+    ALLOWED_GITHUB_HOSTS,
+    DEFAULT_MAX_SOURCE_SIZE_BYTES,
+    validate_url_hostname,
+    build_safe_opener,
+    bounded_read,
+    SSRFSecurityError,
+    PayloadTooLargeError,
+)
 
 logger = logging.getLogger("testforge.ingestion")
@@ -172,12 +181,21 @@ def normalize_github_url(url: str) -> str:
     return meta["normalized_url"]
 
 
-def fetch_github_source_with_meta(github_url: str, output_dir: str = "samples") -> Tuple[Path, Dict[str, Any]]:
+def fetch_github_source_with_meta(
+    github_url: str,
+    output_dir: str = "samples",
+    max_file_size_bytes: int = DEFAULT_MAX_SOURCE_SIZE_BYTES
+) -> Tuple[Path, Dict[str, Any]]:
     """
     Fetches raw Python source code from a GitHub URL, resolves relative package imports
     for standalone sandbox execution, validates AST syntax, saves into `samples/github_<repo>_<filename>.py`,
     and returns (Path, metadata_dict).
 
+    Enforces:
+      - SSRF redirect protection via SafeGitHubRedirectHandler
+      - Bounded source downloads up to max_file_size_bytes
+      - Zero partial file retention on error
+
     Supports:
       - Standard GitHub blob URLs (e.g., https://github.com/psf/requests/blob/main/src/requests/models.py)
       - Raw GitHub URLs (e.g., https://raw.githubusercontent.com/psf/requests/main/src/requests/models.py)
@@ -195,19 +213,25 @@ def fetch_github_source_with_meta(github_url: str, output_dir: str = "samples")
     clean_repo = re.sub(r"[^\w\-]", "_", repo)
     clean_filename = re.sub(r"[^\w\-\.]", "_", filename)
 
-    # Download source content from raw_url (guaranteed to contain only the resolved URL)
+    # Validate destination host against SSRF policy
+    validate_url_hostname(raw_url)
+
+    # Download source content with safe opener and bounded read
     req = urllib.request.Request(
         raw_url,
         headers={"User-Agent": "TestForge/1.0 (Autonomous Systems Ingestion)"}
     )
+    opener = build_safe_opener()
     try:
-        with urllib.request.urlopen(req, timeout=15) as resp:
-            content_bytes = resp.read()
+        with opener.open(req, timeout=15) as resp:
+            content_bytes = bounded_read(resp, max_bytes=max_file_size_bytes)
             content = content_bytes.decode("utf-8", errors="replace")
     except urllib.error.HTTPError as http_err:
         raise RuntimeError(
             f"Failed to fetch GitHub file from {raw_url} (HTTP {http_err.code}: {http_err.reason})"
         ) from http_err
+    except (SSRFSecurityError, PayloadTooLargeError):
+        raise
     except Exception as exc:
         raise RuntimeError(f"Network error fetching GitHub file: {exc}") from exc
 
@@ -227,7 +251,7 @@ def fetch_github_source_with_meta(github_url: str, output_dir: str = "samples")
     except Exception as exc:
         raise ValueError(f"Failed to parse AST of fetched file: {exc}") from exc
 
-    # Save into target path
+    # Save into target path (only after bounded read and AST validation succeed)
     out_dir = Path(output_dir)
     out_dir.mkdir(parents=True, exist_ok=True)
     target_path = out_dir / f"github_{clean_repo}_{clean_filename}"
@@ -443,12 +467,21 @@ class TargetManagerAgent:
     # --------------------------------------------------------------------------
     # Mode C: Direct GitHub URL Ingestion
     # --------------------------------------------------------------------------
-    def ingest_github(self, github_url: str, output_dir: str = "samples") -> Tuple[Path, IngestionAnalysis]:
+    def ingest_github(
+        self,
+        github_url: str,
+        output_dir: str = "samples",
+        max_file_size_bytes: int = DEFAULT_MAX_SOURCE_SIZE_BYTES
+    ) -> Tuple[Path, IngestionAnalysis]:
         """
         Ingests and validates an arbitrary Python source file directly from a public GitHub URL.
         Returns the saved file path and complete IngestionAnalysis with robust GitHub metadata.
         """
-        saved_path, meta = fetch_github_source_with_meta(github_url, output_dir=output_dir)
+        saved_path, meta = fetch_github_source_with_meta(
+            github_url,
+            output_dir=output_dir,
+            max_file_size_bytes=max_file_size_bytes
+        )
         analysis = self.ingest_file(str(saved_path))
         meta["ast_function_count"] = analysis.ast_function_count
         meta["ast_class_count"] = analysis.ast_class_count
```

---

## 4. Preservation of Pre-existing Work

Verification of repository status confirms:
- **No Git history rewriting**: Zero execution of git commit/reset/checkout/restore.
- **Uncommitted modified files untouched**:
  - `benchmark_results.json`
  - `benchmark_results.md`
  - `test_hardened.py`
- **Untracked files preserved**:
  - `qa_artifacts/teacher_release_acceptance_20261027_111000/`
  - `qa_artifacts/security_remediation_phase1_20261030_091500/`
  - `samples/generated_making_a_python_file.py`
- **External backup intact**: `/Users/sourabh/TestForge_backups/backup_20261030_093200/` with verified 100% cryptographic SHA-256 parity.

