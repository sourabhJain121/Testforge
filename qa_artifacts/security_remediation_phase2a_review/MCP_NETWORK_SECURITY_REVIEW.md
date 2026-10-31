# TestForge — MCP Network Security Independent Review

**Audit Date:** 2026-10-30  
**Audited Modules:**  
- `testforge/mcp_server.py`  
- `testforge/mcp_client.py`  
- `testforge/github_service.py`  
- `testforge/ingestion.py`  
**Review Type:** Independent Read-Only Security Audit (Phase 2A)  

---

## 1. Executive Summary

This independent review evaluates network security and boundary enforcement across TestForge's Model Context Protocol (MCP) subsystem. Specifically, it assesses whether tools exposed via the FastMCP servers (`create_filesystem_server` and `create_github_server`) and managed by `MCPClientManager` adhere to the Phase 2A SSRF and bounded download controls, or whether they bypass them.

**Overall MCP Subsystem Verdict:** **FAIL (Critical Security Architecture Gap Identified in `testforge/mcp_server.py`)**

---

## 2. MCP Subsystem Verification Matrix

| Component & Function | Target File & Line | Security Mechanism Present | Status | Verdict |
|---|---|---|---|---|
| **Filesystem MCP Server Root Confinement** | `testforge/mcp_server.py:37-69` | `_is_path_safe()`: Resolves paths, prevents directory traversal (`../`), blocks symlinks and credentials (`.env`, `.pem`, `.key`). | Active | **PASS** |
| **Filesystem MCP Client Path Policy** | `testforge/mcp_client.py:245-250` | `_validate_security_policy()` checks filesystem parameters against `permitted_root`. | Active | **PASS** |
| **Destructive Tool Whitelist Enforcement** | `testforge/mcp_client.py:55-60, 238-244` | Blocks destructive tools (`write_file`, `create_issue`, etc.) and enforces read-only tool whitelist. | Active | **PASS** |
| **GitHub MCP Server Request Dispatcher** | `testforge/mcp_server.py:168-191` | Uses bare `urllib.request.urlopen(req, timeout=10.0)` without `SafeGitHubRedirectHandler` or hostname allowlist. | **MISSING** | **FAIL** |
| **GitHub MCP Server SSRF Redirect Validation** | `testforge/mcp_server.py:175` | Does not validate redirect targets. Allows redirection to arbitrary external hosts or private IP addresses. | **MISSING** | **FAIL** |
| **GitHub MCP Server Token Stripping on Redirect** | `testforge/mcp_server.py:173, 175` | Passes `Authorization: Bearer {token}` into bare `urlopen`. Standard urllib forwards headers on redirect. | **MISSING** | **FAIL** |
| **GitHub MCP Server Bounded Downloads** | `testforge/mcp_server.py:176` | Calls unbounded `resp.read().decode("utf-8")`. Does not use `bounded_read()`. | **MISSING** | **FAIL** |
| **GitHub MCP File Content Size Enforcement** | `testforge/mcp_server.py:218-225` | Decodes base64 content via `base64.b64decode(content_b64)` without any size threshold validation. | **MISSING** | **FAIL** |
| **GitHub MCP URL Coordinate Sanitization** | `testforge/mcp_server.py:197, 214, 232, 252` | Uses `urllib.parse.quote()` on inputs (`owner`, `repo`, `path`, `ref`), but preserves relative path slashes by default. | **PARTIAL** | **PARTIAL** |

---

## 3. Detailed Security Findings & Vulnerability Analysis

### 3.1 Defect MCP-001: Bare `urlopen` Without SSRF Protection in `mcp_server.py`
- **Location:** `testforge/mcp_server.py:168-191` (`create_github_server._make_github_request`)
- **Code:**
  ```python
  def _make_github_request(url: str) -> Dict[str, Any]:
      req = urllib.request.Request(url)
      req.add_header("User-Agent", "TestForge-Agentic-MCP/1.0")
      req.add_header("Accept", "application/vnd.github.v3+json")
      if token:
          req.add_header("Authorization", f"Bearer {token}")
      try:
          with urllib.request.urlopen(req, timeout=10.0) as resp:
              data = resp.read().decode("utf-8")
              return json.loads(data)
  ```
- **Vulnerability Description:**
  1. *Unprotected Dispatch:* Unlike `testforge/github_service.py` and `testforge/ingestion.py`, `mcp_server.py` does not import or use `testforge/network_security.py`.
  2. *Blind Redirection:* `urllib.request.urlopen()` uses default handlers that blindly follow HTTP 301, 302, 303, and 307 redirects to any target location, including internal networks (`10.0.0.0/8`, `192.168.0.0/16`), loopback (`127.0.0.1`), or cloud metadata endpoints (`169.254.169.254`).
  3. *Credential Leakage Risk:* Because `SafeGitHubRedirectHandler` is not attached to this request dispatcher, if an upstream GitHub API or poisoned endpoint returns an HTTP 302 redirecting to an attacker-controlled external host, `urllib` will include the sensitive GitHub Personal Access Token in the redirected request.
- **Classification:** **FAIL**

### 3.2 Defect MCP-002: Unbounded Downloads and Memory Exhaustion in `mcp_server.py`
- **Location:** `testforge/mcp_server.py:176`, `testforge/mcp_server.py:218-225`
- **Code:**
  ```python
  data = resp.read().decode("utf-8")
  ...
  @server.tool()
  def get_file_contents(owner: str, repo: str, path: str, ref: str = "main") -> Dict[str, Any]:
      url = f"https://api.github.com/repos/{urllib.parse.quote(owner)}/{urllib.parse.quote(repo)}/contents/{urllib.parse.quote(path)}?ref={urllib.parse.quote(ref)}"
      data = _make_github_request(url)
      content_b64 = data.get("content", "")
      import base64
      decoded_bytes = base64.b64decode(content_b64)
      return {
          "name": data.get("name"),
          "path": data.get("path"),
          "sha": data.get("sha"),
          "size": data.get("size"),
          "content": decoded_bytes.decode("utf-8", errors="replace")
      }
  ```
- **Vulnerability Description:**
  1. *Unbounded HTTP Response Read:* `resp.read()` reads until EOF without checking `Content-Length` or enforcing streaming chunk thresholds.
  2. *Unbounded Base64 Decoding:* `base64.b64decode(content_b64)` decodes the entire base64 string directly into memory without comparing against a maximum file size limit (such as 500 KB).
  3. An agent invoking `get_file_contents` or `get_repository_tree` on an unusually large repository or asset can trigger memory exhaustion in the MCP server process.
- **Classification:** **FAIL**

### 3.3 Defect MCP-003: Disconnected Security Architectures Between MCP and Ingestion
- **Location:** Architectural boundary between `testforge/mcp_server.py` and `testforge/github_service.py`
- **Root Cause:**
  When Phase 2A was implemented, network security fixes were applied exclusively to `testforge/github_service.py` and `testforge/ingestion.py`. The FastMCP server implementation in `testforge/mcp_server.py` was created as an independent service with its own standalone HTTP client rather than delegating repository operations to `GitHubRepoService`.
- **Classification:** **FAIL**

---

## 4. Remediation Architecture Plan for MCP Subsystem

To bring the MCP subsystem into 100% compliance with Phase 2A security standards, the following modifications must be scheduled prior to Phase 2B deployment:

1. **Refactor `create_github_server` Dispatcher (`testforge/mcp_server.py`)**:
   - Replace the standalone `_make_github_request()` in `testforge/mcp_server.py` with `build_safe_opener()` and `bounded_read()`, or refactor `create_github_server` to delegate repository calls directly to `GitHubRepoService`.
2. **Apply Size Limits in `get_file_contents`**:
   - Add size verification before base64 decoding and enforce `DEFAULT_MAX_SOURCE_SIZE_BYTES` (500 KB).
3. **Add Automated MCP Security Tests**:
   - Expand `tests/test_mcp.py` to test redirect blocking, token stripping, and payload limits on FastMCP tools.

---

## 5. Summary & Status

- **Filesystem MCP Tools:** **PASS** (Protected by `_is_path_safe` and `permitted_root`)
- **Tool Policy & Whitelist:** **PASS** (Protected by `_validate_security_policy`)
- **GitHub MCP Tools:** **FAIL** (Unprotected by Phase 2A controls; uses bare `urlopen` and unbounded reads)

