# TestForge — Phase 2A.1: MCP SSRF Remediation Report

**Date:** 2026-10-30  
**Phase:** 2A.1 (MCP Network Security Remediation)  
**Target Module:** `testforge/mcp_server.py`  
**Status:** REMEDIATED & VERIFIED  

---

## 1. Vulnerability Background

The independent security review for Phase 2A identified that `create_github_server` in `testforge/mcp_server.py` dispatched HTTP requests using bare `urllib.request.urlopen()`. This bypassed the network protections established in Phase 2A:
1. Destination URLs were not validated against approved hostnames.
2. HTTP 301, 302, 303, 307, and 308 redirects were followed unconditionally by default handlers, enabling SSRF targeting `localhost`, private subnets (RFC 1918), and cloud metadata endpoints (`169.254.169.254`).
3. Sensitive `Authorization: Bearer {token}` credentials were leaked across domain boundaries during multi-hop redirects.

---

## 2. Remediation Implementation

Rather than duplicating network security logic, `testforge/mcp_server.py` now directly reuses the existing, audited infrastructure from `testforge/network_security.py`:
- `validate_url_hostname`
- `build_safe_opener`
- `SafeGitHubRedirectHandler`
- `ALLOWED_GITHUB_HOSTS`
- `SSRFSecurityError`

### 2.1 Secure Opener Architecture in `create_github_server`
- **Location:** `testforge/mcp_server.py:163-176`
- **Mechanism:**
  `create_github_server()` now instantiates a dedicated `safe_opener` configured with `SafeGitHubRedirectHandler`:
  ```python
  safe_opener = opener if opener is not None else build_safe_opener(
      allowed_hosts={"api.github.com", "raw.githubusercontent.com", "objects.githubusercontent.com"}
  )
  ```
  This allows dependency injection for integration testing with custom simulated transport handlers while defaulting to secure HTTPS dispatch in production.

### 2.2 Proactive URL Validation
- **Location:** `testforge/mcp_server.py:180-182`
- **Mechanism:**
  Before initializing the `urllib.request.Request` object, `_make_github_request()` validates the initial destination URL:
  ```python
  validate_url_hostname(url, allowed_hosts={"api.github.com", "raw.githubusercontent.com"})
  ```
  This immediately fails closed if the URL contains:
  - Non-HTTPS schemes (`http://`, `ftp://`, `file://`, etc.)
  - Control characters, newlines, or non-printable ASCII bytes (`ord < 32 or ord >= 127`)
  - Userinfo credentials (`user:pass@host`) or backslashes (`\`)
  - Direct or obfuscated IP addresses (decimal, hex, octal, loopback, private RFC 1918, link-local, cloud metadata)
  - Non-standard HTTPS ports (`!= 443`)

### 2.3 Safe Redirect Interception & Credential Stripping
- **Handler:** `SafeGitHubRedirectHandler` (subclassed from `urllib.request.HTTPRedirectHandler`)
- **Behaviors:**
  1. *Destination Validation:* Every redirect location is validated against `ALLOWED_GITHUB_HOSTS` before following. Redirects to unauthorized external domains, `localhost`, or private IPs raise `SSRFSecurityError`.
  2. *Depth Limit Enforcement:* Enforces `DEFAULT_MAX_REDIRECTS = 5`. Exceeding this threshold terminates with a redirect error.
  3. *Credential Stripping:* On cross-hostname redirects (e.g. `api.github.com` $\rightarrow$ `objects.githubusercontent.com`), sensitive headers (`Authorization`, `X-Access-Token`, `X-OAuth-Basic`, `Proxy-Authorization`, `Cookie`) are purged from both `headers` and `unredirected_hdrs`.
  4. *Same-Host Retention:* Preserves authentication headers when redirecting within the same domain (e.g. `api.github.com` $\rightarrow$ `api.github.com`).

---

## 3. Verification & Test Evidence

Tested via `tests/test_mcp_network_security.py` using real `urllib` opener dispatch and mocked HTTPS transport (zero mocking of security handlers):
- `test_legitimate_github_api_request`: **PASSED** (200 OK handled cleanly)
- `test_redirect_to_unauthorized_host_blocked`: **PASSED** (`SSRFSecurityError` raised)
- `test_redirect_to_localhost_blocked`: **PASSED** (`SSRFSecurityError` raised)
- `test_redirect_to_private_ip_blocked`: **PASSED** (`SSRFSecurityError` raised)
- `test_multiple_redirect_attempts_exceeding_limit`: **PASSED** (`HTTPError: redirect error` raised on $> 5$ hops)
- `test_credential_stripping_across_host_changes`: **PASSED** (`Authorization` stripped on CDN transition)

Existing MCP tools (`tests/test_mcp.py`, 22 tests) continue to pass without regression.

