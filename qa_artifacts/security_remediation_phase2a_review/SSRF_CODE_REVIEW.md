# TestForge — SSRF Protection Independent Code Review

**Audit Date:** 2026-10-30  
**Audited Modules:**  
- `testforge/network_security.py`  
- `testforge/github_service.py`  
- `testforge/ingestion.py`  
**Review Type:** Independent Read-Only Security Audit (Phase 2A)  

---

## 1. Executive Summary

This independent review evaluates the Server-Side Request Forgery (SSRF) and redirect mitigation mechanisms introduced in Phase 2A. The inspection examines URL syntax parsing, IP canonicalization, redirect handler dispatching, credential isolation, and fail-closed behaviors under adversarial scenarios.

**Overall SSRF Subsystem Verdict:** **PASS (with 1 Architectural Note on DNS Rebinding)**

---

## 2. Granular Verification Matrix

| Verification Objective | Target File & Line | Implementation Details | Classification |
|---|---|---|---|
| **Every redirect validated before following** | `testforge/network_security.py:213-228` | `SafeGitHubRedirectHandler.redirect_request` intercepts HTTP 301, 302, 303, 307, 308. Calls `validate_url_hostname(newurl)` *before* returning `new_req` to `urllib.request`. | **PASS** |
| **Strict HTTPS scheme enforcement** | `testforge/network_security.py:142-146` | Both raw `url` and unquoted URL parsed via `urllib.parse.urlparse`. Rejects schemes `!= "https"`. | **PASS** |
| **Approved GitHub hostname whitelist** | `testforge/network_security.py:30-36, 186-191` | Enforces exact membership in `ALLOWED_GITHUB_HOSTS` (`api.github.com`, `raw.githubusercontent.com`, `codeload.github.com`, `objects.githubusercontent.com`, `github.com`). | **PASS** |
| **Hostname parsing bypass protection (@, \\)** | `testforge/network_security.py:148-159` | Explicitly checks for `@` (userinfo) and `\` (backslash) in `parsed.netloc` and `parsed_unquoted.netloc`, plus `parsed.username`/`parsed.password`. | **PASS** |
| **Control & Non-ASCII character rejection** | `testforge/network_security.py:129-134` | Rejects any character where `ord(ch) < 32 or ord(ch) >= 127`. Eliminates CR/LF injection, null bytes (`%00`), and Unicode/IDN homograph spoofing. | **PASS** |
| **IPv4, IPv6 & Obfuscated IP blocking** | `testforge/network_security.py:71-107, 174-179` | `is_ip_address()` detects standard IPv4/IPv6, integer/decimal IPs (e.g. `2130706433`), hex (`0x7f000001`), and octal/mixed numeric formats. Blocks loopback, private, link-local, multicast, and unspecified IPs. | **PASS** |
| **Localhost & Cloud Metadata Blocking** | `testforge/network_security.py:38-53, 167-172` | Explicitly blocks `localhost`, `localhost.localdomain`, `ip6-localhost`, `*.localhost`, `169.254.169.254`, `metadata.google.internal`, `metadata.internal`, `instance-data`, `100.100.100.200`. | **PASS** |
| **Non-standard HTTPS port blocking** | `testforge/network_security.py:180-184` | Rejects explicit ports other than 443 (`parsed.port is not None and parsed.port != 443`). | **PASS** |
| **Redirect loops and excessive hops** | `testforge/network_security.py:202-211` | `SafeGitHubRedirectHandler` inherits from `urllib.request.HTTPRedirectHandler` with `max_redirections = 5`. `HTTPRedirectHandler` tracks `redirect_dict` and raises `HTTPError` on loops or limit breaches. | **PASS** |
| **Credential leakage across domain boundaries** | `testforge/network_security.py:230-252` | If `orig_host != new_host`, purges `authorization`, `x-access-token`, `x-oauth-basic`, `proxy-authorization`, and `cookie` from both `headers` and `unredirected_hdrs`. | **PASS** |
| **Same-host credential preservation** | `testforge/network_security.py:238` | Preserves `Authorization` headers when redirecting within the same host (e.g. `api.github.com` -> `api.github.com`). | **PASS** |
| **Relative redirect resolution** | `testforge/network_security.py:218-220` | Resolves relative URLs (`/path/file.py`) against `req.full_url` using `urllib.parse.urljoin` before validating against hostname policy. | **PASS** |
| **Malformed Location header handling** | `testforge/network_security.py:122-135` | Fails closed: raises `SSRFSecurityError` on empty, malformed, non-string, or non-printable targets, preventing request continuation. | **PASS** |
| **Legitimate GitHub request compatibility** | `testforge/github_service.py:276-293`, `testforge/ingestion.py:217-227` | Standard requests to `api.github.com` and `raw.githubusercontent.com` proceed normally; verified by full regression test suite (501 tests pass). | **PASS** |
| **DNS Rebinding & TOCTOU Resolution** | `testforge/network_security.py:110-193` | Validates hostname string against static allowlist. Does not resolve or pin IP address prior to socket creation. | **PARTIAL** |

---

## 3. Deep-Dive Code Inspection

### 3.1 Hostname Validation Architecture (`validate_url_hostname`)
- **Code Reference:** `testforge/network_security.py:110-193`
- **Strengths:**
  1. *Dual-Pass Inspection:* Normalizes and parses both the raw URL and `urllib.parse.unquote(cleaned)`. This effectively neutralizes multi-layer percent-encoded evasion vectors (such as `%2540` -> `%40` -> `@`).
  2. *Strict Byte Whitelisting:* Rejecting `ord(ch) >= 127` completely eliminates Unicode normalization vulnerabilities (e.g. IDNA UTS #46 mapping tricks, fullwidth characters, or lookalike domain attacks).
  3. *Zero False Acceptance on Port Tricks:* By rejecting all non-standard ports, an attacker cannot direct requests to high-port internal services (e.g., `https://api.github.com:8443/`).
- **Residual Risk (PARTIAL Finding):**
  - **DNS Rebinding:** String validation assumes that `api.github.com` resolves to legitimate GitHub infrastructure. If the runtime operating system has a poisoned `/etc/hosts` or compromised DNS resolver, requests to `api.github.com` could resolve to loopback/private IPs.
  - *Risk Assessment:* **LOW**. In cloud and container environments where public DNS is utilized, an attacker supplying a repository URL cannot control the resolution of `api.github.com`. However, true defense-in-depth would resolve the IP via `socket.getaddrinfo` and verify that the destination IP does not fall into RFC 1918 / loopback ranges.

### 3.2 Redirect Handler & Token Stripping (`SafeGitHubRedirectHandler`)
- **Code Reference:** `testforge/network_security.py:196-254`
- **Strengths:**
  1. *Subclassed Standard Handler:* Integrating into Python's native `HTTPRedirectHandler` guarantees that all redirects triggered by `opener.open()` are routed through `redirect_request()`.
  2. *Complete Dictionary Scrubbing:* Python's `urllib.request.Request` stores headers in two distinct dictionaries: `.headers` and `.unredirected_hdrs`. The implementation scrubs both data structures:
     ```python
     for hdr in list(new_req.headers.keys()):
         if hdr.lower() in sensitive_headers:
             del new_req.headers[hdr]
     for hdr in list(new_req.unredirected_hdrs.keys()):
         if hdr.lower() in sensitive_headers:
             del new_req.unredirected_hdrs[hdr]
     ```
  3. *Compatibility with AWS S3 / CDN Storage:* GitHub API redirects large assets to `objects.githubusercontent.com` (backed by AWS S3 pre-signed URLs). Stripping `Authorization` prevents AWS S3 authentication collision errors (`InvalidArgument: Only one auth mechanism allowed`).

### 3.3 Integration in Ingestion Services
- **Code Reference:** `testforge/github_service.py:276-293`, `testforge/ingestion.py:217-227`
- Both `GitHubRepoService._make_github_request()` and `fetch_github_source_with_meta()` use `build_safe_opener()` instead of bare `urllib.request.urlopen()`.
- Initial targets are validated prior to request initiation, and redirect destinations are validated prior to being followed.

---

## 4. Adversarial Edge Case Assessment

1. **Protocol-Relative Redirect (`//attacker.com/evil.py`)**:
   - `SafeGitHubRedirectHandler:219` detects that it does not start with `http://` or `https://` and joins with `req.full_url`, producing `https://attacker.com/evil.py`.
   - `validate_url_hostname` detects `attacker.com` is not in `ALLOWED_GITHUB_HOSTS` and raises `SSRFSecurityError`. **Mitigated.**
2. **Userinfo Bypass (`https://api.github.com@127.0.0.1/`)**:
   - `validate_url_hostname:149` detects `@` in `parsed.netloc` and raises `SSRFSecurityError`. **Mitigated.**
3. **Backslash Host Spoofing (`https://api.github.com\\attacker.com/`)**:
   - `validate_url_hostname:155` detects `\\` in `parsed.netloc` and raises `SSRFSecurityError`. **Mitigated.**
4. **Integer/Hex IP Redirect (`https://2130706433/`)**:
   - `is_ip_address:96` flags decimal IP representation and raises `SSRFSecurityError`. **Mitigated.**
5. **CRLF Header Injection (`https://api.github.com\r\nSet-Cookie: evil`)**:
   - `validate_url_hostname:130` detects ASCII control bytes `< 32` and raises `SSRFSecurityError`. **Mitigated.**

---

## 5. Summary & Status

- **SSRF Code Review Classification:** **PASS**
- **Identified Action Items for Future Hardening:**
  - In Phase 3 / production release, consider adding custom SSL socket IP pinning to verify resolved IP addresses against RFC 1918 ranges to eliminate DNS rebinding vectors.

