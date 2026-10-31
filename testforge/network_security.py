"""
network_security.py - Network Security, SSRF Mitigation, and Bounded Payload Controls.

Author: TestForge Security Team
Course: CSE3101 - Agentic AI

Guarantees:
  1. SSRF Mitigation: Strict allowlist validation of GitHub hostnames across all requests
     and intermediate HTTP 301/302/307/308 redirects.
  2. Complete IP & Metadata Blocking: Prohibits loopback (127.0.0.1, localhost), RFC 1918
     private networks, link-local addresses, IPv6 representations, and cloud metadata endpoints.
  3. Credential Protection: Automatically purges sensitive Authorization and token headers
     whenever a redirect traverses across distinct hostnames.
  4. Bounded Source Downloads: Enforces strict chunked transfer limits and Content-Length
     bounds to protect against denial-of-service and memory exhaustion.
"""

from __future__ import annotations
import os
import re
import ipaddress
import logging
import urllib.request
import urllib.parse
from typing import Set, Optional, Tuple, Any

logger = logging.getLogger("testforge.network_security")

# Allowed GitHub hostnames for API and source ingestion
ALLOWED_GITHUB_HOSTS: Set[str] = {
    "api.github.com",
    "raw.githubusercontent.com",
    "codeload.github.com",
    "objects.githubusercontent.com",
    "github.com",
}

# Cloud metadata hostnames and endpoints
CLOUD_METADATA_HOSTS: Set[str] = {
    "169.254.169.254",
    "metadata.google.internal",
    "metadata.internal",
    "instance-data",
    "100.100.100.200",
}

# Localhost aliases
LOCALHOST_NAMES: Set[str] = {
    "localhost",
    "localhost.localdomain",
    "ip6-localhost",
    "ip6-loopback",
}

DEFAULT_MAX_SOURCE_SIZE_BYTES: int = 500 * 1024  # 500 KB default limit
DEFAULT_CHUNK_SIZE: int = 64 * 1024  # 64 KB read chunks
DEFAULT_REQUEST_TIMEOUT: float = 15.0  # seconds
DEFAULT_MAX_REDIRECTS: int = 5


class SSRFSecurityError(ValueError):
    """Raised when an SSRF or redirect security violation is detected."""
    pass


class PayloadTooLargeError(ValueError):
    """Raised when downloaded payload exceeds size limits."""
    pass


def is_ip_address(host: str) -> Tuple[bool, Optional[str]]:
    """
    Determines whether a host string represents an IP address (IPv4, IPv6, numeric, or hex).
    Returns (is_ip, reason).
    """
    clean_host = host.strip("[]")
    
    # 1. Standard IPv4 or IPv6 via ipaddress module
    try:
        ip = ipaddress.ip_address(clean_host)
        if ip.is_loopback:
            return True, f"Loopback IP address forbidden: {clean_host}"
        if ip.is_private:
            return True, f"Private IP address forbidden: {clean_host}"
        if ip.is_link_local:
            return True, f"Link-local / cloud metadata IP forbidden: {clean_host}"
        if ip.is_multicast:
            return True, f"Multicast IP forbidden: {clean_host}"
        if ip.is_unspecified:
            return True, f"Unspecified IP forbidden: {clean_host}"
        return True, f"Direct IP address access forbidden: {clean_host}"
    except ValueError:
        pass

    # 2. Integer or Decimal representation (e.g. 2130706433 -> 127.0.0.1)
    if clean_host.isdigit():
        return True, f"Decimal IP representation forbidden: {clean_host}"

    # 3. Hexadecimal representation (e.g. 0x7f000001)
    if re.match(r"^0x[0-9a-fA-F]+$", clean_host):
        return True, f"Hexadecimal IP representation forbidden: {clean_host}"

    # 4. Octal or mixed numeric representation (e.g. 0177.0.0.1)
    if re.match(r"^[0-9.]+$", clean_host):
        return True, f"Numeric IP representation forbidden: {clean_host}"

    return False, None


def validate_url_hostname(url: str, allowed_hosts: Optional[Set[str]] = None) -> str:
    """
    Validates that a URL's destination is safe from SSRF:
      1. Scheme must be strictly 'https'.
      2. Rejects control characters, newlines, and non-printable bytes.
      3. Rejects userinfo (@) and backslashes in authority.
      4. Rejects localhost, IP addresses, and cloud metadata endpoints.
      5. Rejects non-standard HTTPS ports (only 443 or default permitted).
      6. Enforces exact membership in approved hostname set.
    
    Returns the normalized, validated lowercase hostname.
    """
    if not isinstance(url, str):
        raise SSRFSecurityError("URL must be a string.")

    cleaned = url.strip()
    if not cleaned:
        raise SSRFSecurityError("URL cannot be empty.")

    # Reject control characters and non-printable characters
    for ch in cleaned:
        if ord(ch) < 32 or ord(ch) >= 127:
            raise SSRFSecurityError(
                f"URL contains invalid control characters or non-printable bytes: {repr(ch)}"
            )

    # Detect percent-encoded obfuscation before parsing
    unquoted = urllib.parse.unquote(cleaned)

    parsed = urllib.parse.urlparse(cleaned)
    parsed_unquoted = urllib.parse.urlparse(unquoted)

    # 1. Strict HTTPS scheme enforcement
    if parsed.scheme.lower() != "https" or parsed_unquoted.scheme.lower() != "https":
        raise SSRFSecurityError(
            f"Security Violation: Insecure scheme '{parsed.scheme}'. Only 'https' is permitted."
        )

    # 2. Reject userinfo tricks (@) in netloc
    if "@" in (parsed.netloc or "") or "@" in (parsed_unquoted.netloc or "") or parsed.username or parsed.password:
        raise SSRFSecurityError(
            "Security Violation: Userinfo (@) in URL authority is strictly forbidden."
        )

    # 3. Reject backslashes in netloc
    if "\\" in (parsed.netloc or "") or "\\" in (parsed_unquoted.netloc or ""):
        raise SSRFSecurityError(
            "Security Violation: Backslash in URL authority is strictly forbidden."
        )

    # 4. Hostname extraction and normalization
    host_raw = (parsed.hostname or "").strip(".").lower()
    host_unquoted = (parsed_unquoted.hostname or "").strip(".").lower()

    if not host_raw or not host_unquoted:
        raise SSRFSecurityError("Security Violation: URL missing a valid hostname.")

    # 5. Localhost and cloud metadata checks
    if host_raw in LOCALHOST_NAMES or host_unquoted in LOCALHOST_NAMES or host_raw.endswith(".localhost"):
        raise SSRFSecurityError(f"Security Violation: Access to localhost forbidden: '{host_raw}'.")

    if host_raw in CLOUD_METADATA_HOSTS or host_unquoted in CLOUD_METADATA_HOSTS:
        raise SSRFSecurityError(f"Security Violation: Access to cloud metadata forbidden: '{host_raw}'.")

    # 6. Direct and encoded IP checks
    for h in (host_raw, host_unquoted):
        is_ip, reason = is_ip_address(h)
        if is_ip:
            raise SSRFSecurityError(f"Security Violation: {reason}")

    # 7. Non-standard port check
    if parsed.port is not None and parsed.port != 443:
        raise SSRFSecurityError(
            f"Security Violation: Non-standard HTTPS port {parsed.port} forbidden. Only standard HTTPS (443) is permitted."
        )

    # 8. Strict allowlist match
    effective_allowed = allowed_hosts if allowed_hosts is not None else ALLOWED_GITHUB_HOSTS
    if host_raw not in effective_allowed or host_unquoted not in effective_allowed:
        raise SSRFSecurityError(
            f"Security Violation: Target host '{host_raw}' is not an authorized GitHub endpoint. Allowed: {sorted(list(effective_allowed))}"
        )

    return host_raw


class SafeGitHubRedirectHandler(urllib.request.HTTPRedirectHandler):
    """
    Subclasses HTTPRedirectHandler to intercept all HTTP redirect responses (301, 302, 303, 307, 308).
    Enforces SSRF validation on the destination URL and strips authentication headers
    on cross-hostname transitions.
    """
    max_redirections = DEFAULT_MAX_REDIRECTS

    def __init__(
        self,
        allowed_hosts: Optional[Set[str]] = None,
        max_redirects: int = DEFAULT_MAX_REDIRECTS
    ):
        super().__init__()
        self.allowed_hosts = allowed_hosts if allowed_hosts is not None else ALLOWED_GITHUB_HOSTS
        self.max_redirections = max_redirects

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        """
        Validates redirect destination, strips sensitive headers across domains,
        and fails closed on security violations.
        """
        # Resolve relative redirects against request base
        if not (newurl.startswith("http://") or newurl.startswith("https://")):
            newurl = urllib.parse.urljoin(req.full_url, newurl)

        # 1. Validate destination URL against SSRF policy (raises SSRFSecurityError if invalid)
        validate_url_hostname(newurl, allowed_hosts=self.allowed_hosts)

        # 2. Construct redirected request
        new_req = super().redirect_request(req, fp, code, msg, headers, newurl)
        if new_req is None:
            return None

        # 3. Credential leakage prevention:
        # If redirected to a different host (e.g. api.github.com -> objects.githubusercontent.com),
        # strip sensitive Authorization and token headers.
        orig_parsed = urllib.parse.urlparse(req.full_url)
        new_parsed = urllib.parse.urlparse(newurl)
        orig_host = (orig_parsed.hostname or "").lower()
        new_host = (new_parsed.hostname or "").lower()

        if orig_host != new_host:
            sensitive_headers = {
                "authorization",
                "x-access-token",
                "x-oauth-basic",
                "proxy-authorization",
                "cookie",
            }
            for hdr in list(new_req.headers.keys()):
                if hdr.lower() in sensitive_headers:
                    del new_req.headers[hdr]
            for hdr in list(new_req.unredirected_hdrs.keys()):
                if hdr.lower() in sensitive_headers:
                    del new_req.unredirected_hdrs[hdr]

        return new_req


def build_safe_opener(
    allowed_hosts: Optional[Set[str]] = None,
    max_redirects: int = DEFAULT_MAX_REDIRECTS
) -> urllib.request.OpenerDirector:
    """
    Builds an OpenerDirector configured with SafeGitHubRedirectHandler and default SSL context.
    """
    handler = SafeGitHubRedirectHandler(allowed_hosts=allowed_hosts, max_redirects=max_redirects)
    return urllib.request.build_opener(handler)


def bounded_read(
    resp: Any,
    max_bytes: int = DEFAULT_MAX_SOURCE_SIZE_BYTES,
    chunk_size: int = DEFAULT_CHUNK_SIZE
) -> bytes:
    """
    Reads data from an open HTTP response stream up to `max_bytes`:
      1. Inspects Content-Length header if present; rejects oversized or negative values before reading.
      2. Reads body incrementally in bounded chunks; stops immediately if max_bytes is exceeded.
      3. Handles missing or malformed Content-Length headers gracefully via chunk counting.
      4. Guarantees stream closure on both success and error.
    """
    try:
        # 1. Content-Length check
        headers = getattr(resp, "headers", None)
        if headers is not None:
            cl_raw = headers.get("content-length")
            if cl_raw is not None:
                try:
                    cl_val = int(str(cl_raw).strip())
                    if cl_val < 0:
                        raise ValueError(f"Invalid Content-Length header: negative value ({cl_val})")
                    if cl_val > max_bytes:
                        raise PayloadTooLargeError(
                            f"File size from Content-Length ({cl_val} bytes) exceeds maximum allowable limit of {max_bytes} bytes."
                        )
                except ValueError as ve:
                    if isinstance(ve, PayloadTooLargeError) or "negative value" in str(ve):
                        raise
                    # Non-integer Content-Length; do not trust it, log and let chunked reading enforce cap
                    logger.warning(
                        f"Malformed Content-Length header '{cl_raw}'; falling back to stream chunk enforcement."
                    )

        # 2. Chunked stream reading
        buffer = bytearray()
        total_read = 0
        while True:
            chunk = resp.read(chunk_size)
            if not chunk:
                break
            total_read += len(chunk)
            if total_read > max_bytes:
                raise PayloadTooLargeError(
                    f"Download exceeded maximum allowable size of {max_bytes} bytes during stream transfer."
                )
            buffer.extend(chunk)

        return bytes(buffer)
    finally:
        if hasattr(resp, "close") and callable(resp.close):
            resp.close()

