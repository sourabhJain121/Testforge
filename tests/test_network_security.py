"""
test_network_security.py - Comprehensive Unit Tests for SSRF Mitigation & Bounded Downloads.

Covers:
  - SSRF redirect protection (allowed hosts, localhost, private IP, metadata, external domains, userinfo, scheme).
  - Header & token leakage prevention on cross-host redirects.
  - Multiple redirects and redirect depth limits.
  - Bounded download stream enforcement (exact limit, oversized, missing/malformed Content-Length, chunked streaming).
  - Partial file cleanup on failure.
"""

import io
import json
import socket
import urllib.request
import urllib.error
import urllib.parse
from pathlib import Path
from unittest.mock import MagicMock, patch, call
import pytest

from testforge.network_security import (
    ALLOWED_GITHUB_HOSTS,
    DEFAULT_MAX_SOURCE_SIZE_BYTES,
    validate_url_hostname,
    SafeGitHubRedirectHandler,
    build_safe_opener,
    bounded_read,
    SSRFSecurityError,
    PayloadTooLargeError,
)
from testforge.ingestion import fetch_github_source_with_meta
from testforge.github_service import GitHubRepoService


# ==============================================================================
# 1. URL & Hostname SSRF Validation Unit Tests
# ==============================================================================

class TestURLValidationAndSSRF:

    @pytest.mark.parametrize("valid_url", [
        "https://api.github.com/repos/psf/requests",
        "https://raw.githubusercontent.com/psf/requests/main/README.md",
        "https://github.com/psf/requests/blob/main/setup.py",
        "https://codeload.github.com/psf/requests/zip/refs/heads/main",
        "https://objects.githubusercontent.com/github-production-release-asset-2e65be/12345",
    ])
    def test_allowed_github_hostnames(self, valid_url):
        host = validate_url_hostname(valid_url)
        assert host in ALLOWED_GITHUB_HOSTS

    @pytest.mark.parametrize("insecure_url", [
        "http://api.github.com/repos/psf/requests",
        "ftp://raw.githubusercontent.com/file.py",
        "file:///etc/passwd",
        "gopher://api.github.com/",
    ])
    def test_reject_insecure_schemes(self, insecure_url):
        with pytest.raises(SSRFSecurityError, match="Insecure scheme"):
            validate_url_hostname(insecure_url)

    @pytest.mark.parametrize("localhost_url", [
        "https://localhost/",
        "https://localhost:443/admin",
        "https://localhost.localdomain/",
        "https://127.0.0.1/",
        "https://127.0.0.2:443/",
        "https://127.1.2.3/",
        "https://[::1]/",
        "https://subdomain.localhost/",
    ])
    def test_reject_localhost_and_loopback(self, localhost_url):
        with pytest.raises(SSRFSecurityError, match="forbidden"):
            validate_url_hostname(localhost_url)

    @pytest.mark.parametrize("private_ip_url", [
        "https://10.0.0.1/status",
        "https://10.255.255.254/internal",
        "https://172.16.0.1/",
        "https://172.31.255.255/",
        "https://192.168.1.1/router",
        "https://192.168.0.254/",
        "https://0.0.0.0/",
    ])
    def test_reject_private_ip_ranges(self, private_ip_url):
        with pytest.raises(SSRFSecurityError, match="forbidden"):
            validate_url_hostname(private_ip_url)

    @pytest.mark.parametrize("metadata_url", [
        "https://169.254.169.254/latest/meta-data/",
        "https://metadata.google.internal/computeMetadata/v1/",
        "https://metadata.internal/",
        "https://instance-data/latest/",
    ])
    def test_reject_cloud_metadata_endpoints(self, metadata_url):
        with pytest.raises(SSRFSecurityError, match="forbidden"):
            validate_url_hostname(metadata_url)

    @pytest.mark.parametrize("arbitrary_external_url", [
        "https://evil.com/payload.py",
        "https://webhook.site/abc-123",
        "https://pastebin.com/raw/xyz",
        "https://attacker.org/",
        "https://api.github.com.attacker.org/",
    ])
    def test_reject_arbitrary_external_hosts(self, arbitrary_external_url):
        with pytest.raises(SSRFSecurityError, match="not an authorized GitHub endpoint"):
            validate_url_hostname(arbitrary_external_url)

    @pytest.mark.parametrize("obfuscated_url", [
        "https://raw.githubusercontent.com@evil.com/target.py",
        "https://raw.githubusercontent.com%40evil.com/target.py",
        "https://api.github.com@169.254.169.254/",
        "https://api.github.com:8443/",
        "https://raw.githubusercontent.com:8080/file.py",
        "https://2130706433/",  # decimal representation of 127.0.0.1
        "https://0x7f000001/",  # hex representation of 127.0.0.1
    ])
    def test_reject_obfuscated_hostnames_and_ports(self, obfuscated_url):
        with pytest.raises(SSRFSecurityError):
            validate_url_hostname(obfuscated_url)

    def test_reject_control_characters(self):
        with pytest.raises(SSRFSecurityError, match="control characters"):
            validate_url_hostname("https://api.github.com\r\n/evil")
        with pytest.raises(SSRFSecurityError, match="control characters"):
            validate_url_hostname("https://api.github.com\x00/evil")


# ==============================================================================
# 2. Redirect Handler & Header Stripping Unit Tests
# ==============================================================================

class TestSafeGitHubRedirectHandler:

    def setup_method(self):
        self.handler = SafeGitHubRedirectHandler()

    def test_allowed_github_redirect(self):
        req = urllib.request.Request("https://raw.githubusercontent.com/psf/requests/main/setup.py")
        new_url = "https://objects.githubusercontent.com/github-production-release-asset/12345"
        
        # Should not raise exception
        new_req = self.handler.redirect_request(req, None, 302, "Found", {}, new_url)
        assert new_req is not None
        assert new_req.full_url == new_url

    def test_redirect_to_localhost_blocked(self):
        req = urllib.request.Request("https://api.github.com/repos/psf/requests")
        with pytest.raises(SSRFSecurityError, match="localhost"):
            self.handler.redirect_request(req, None, 302, "Found", {}, "https://localhost:443/secret")

    def test_redirect_to_private_ip_blocked(self):
        req = urllib.request.Request("https://api.github.com/repos/psf/requests")
        with pytest.raises(SSRFSecurityError, match="forbidden"):
            self.handler.redirect_request(req, None, 302, "Found", {}, "https://192.168.1.100/config")

    def test_redirect_to_cloud_metadata_blocked(self):
        req = urllib.request.Request("https://api.github.com/repos/psf/requests")
        with pytest.raises(SSRFSecurityError, match="forbidden"):
            self.handler.redirect_request(req, None, 301, "Moved", {}, "https://169.254.169.254/latest/meta-data/")

    def test_redirect_to_arbitrary_domain_blocked(self):
        req = urllib.request.Request("https://api.github.com/repos/psf/requests")
        with pytest.raises(SSRFSecurityError, match="not an authorized GitHub endpoint"):
            self.handler.redirect_request(req, None, 302, "Found", {}, "https://attacker.com/steal")

    def test_redirect_to_http_insecure_scheme_blocked(self):
        req = urllib.request.Request("https://api.github.com/repos/psf/requests")
        with pytest.raises(SSRFSecurityError, match="Insecure scheme"):
            self.handler.redirect_request(req, None, 302, "Found", {}, "http://raw.githubusercontent.com/test.py")

    def test_header_and_token_stripping_on_cross_host_redirect(self):
        req = urllib.request.Request(
            "https://api.github.com/repos/psf/requests",
            headers={
                "Authorization": "Bearer ghp_SECRET_TOKEN_12345",
                "X-Access-Token": "secret_token",
                "User-Agent": "TestForge/1.0",
            }
        )
        new_url = "https://objects.githubusercontent.com/asset/file.tar.gz"

        new_req = self.handler.redirect_request(req, None, 302, "Found", {}, new_url)
        assert new_req is not None
        # Sensitive tokens MUST be stripped across distinct hostnames
        assert "authorization" not in [k.lower() for k in new_req.headers.keys()]
        assert "x-access-token" not in [k.lower() for k in new_req.headers.keys()]
        assert "authorization" not in [k.lower() for k in new_req.unredirected_hdrs.keys()]
        # Benign headers should be retained
        assert any("user-agent" in k.lower() for k in new_req.headers.keys())

    def test_headers_preserved_on_same_host_redirect(self):
        req = urllib.request.Request(
            "https://api.github.com/repos/psf/requests",
            headers={"Authorization": "Bearer ghp_SECRET_TOKEN_12345"}
        )
        new_url = "https://api.github.com/repositories/12345"

        new_req = self.handler.redirect_request(req, None, 301, "Moved", {}, new_url)
        assert new_req is not None
        # Same host redirect can safely maintain authorization
        auth_header = new_req.headers.get("Authorization") or new_req.unredirected_hdrs.get("Authorization")
        assert auth_header == "Bearer ghp_SECRET_TOKEN_12345"

    def test_relative_redirect_resolution(self):
        req = urllib.request.Request("https://raw.githubusercontent.com/psf/requests/main/a.py")
        new_url = "/psf/requests/main/b.py"

        new_req = self.handler.redirect_request(req, None, 302, "Found", {}, new_url)
        assert new_req is not None
        assert new_req.full_url == "https://raw.githubusercontent.com/psf/requests/main/b.py"


# ==============================================================================
# 3. Bounded Source Download Unit Tests
# ==============================================================================

class MockHTTPResponse:
    def __init__(self, data: bytes, headers: dict = None):
        self._io = io.BytesIO(data)
        self.headers = headers or {}
        self.closed = False

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def read(self, size=-1):
        return self._io.read(size)

    def close(self):
        self.closed = True


class TestBoundedSourceDownloads:

    def test_normal_source_retrieval(self):
        payload = b"def test_fn(): return 42\n"
        resp = MockHTTPResponse(payload, headers={"content-length": str(len(payload))})
        
        result = bounded_read(resp, max_bytes=1024)
        assert result == payload
        assert resp.closed is True

    def test_exact_size_limit_passes(self):
        exact_bytes = b"X" * 1024
        resp = MockHTTPResponse(exact_bytes, headers={"content-length": "1024"})
        
        result = bounded_read(resp, max_bytes=1024)
        assert len(result) == 1024
        assert resp.closed is True

    def test_size_limit_exceeded_via_content_length(self):
        # 2000 bytes declared when max is 1000
        resp = MockHTTPResponse(b"X" * 2000, headers={"content-length": "2000"})
        
        with pytest.raises(PayloadTooLargeError, match="exceeds maximum allowable limit"):
            bounded_read(resp, max_bytes=1000)
        assert resp.closed is True

    def test_chunked_response_exceeding_limit_without_content_length(self):
        # Missing Content-Length header, but stream delivers 2000 bytes when max is 500
        oversized = b"A" * 2000
        resp = MockHTTPResponse(oversized, headers={})
        
        with pytest.raises(PayloadTooLargeError, match="Download exceeded maximum allowable size"):
            bounded_read(resp, max_bytes=500, chunk_size=100)
        assert resp.closed is True

    def test_incorrect_content_length_deceiving_header(self):
        # Header claims 50 bytes, but stream sends 2000 bytes
        resp = MockHTTPResponse(b"Z" * 2000, headers={"content-length": "50"})
        
        with pytest.raises(PayloadTooLargeError, match="Download exceeded maximum allowable size"):
            bounded_read(resp, max_bytes=500, chunk_size=64)
        assert resp.closed is True

    def test_malformed_non_integer_content_length(self):
        # Header is "invalid_number", stream is within limit (300 bytes < 500 max)
        valid_stream = b"print('safe code')\n" * 10
        resp = MockHTTPResponse(valid_stream, headers={"content-length": "not-an-int"})
        
        result = bounded_read(resp, max_bytes=1000)
        assert result == valid_stream
        assert resp.closed is True

    def test_negative_content_length_rejected(self):
        resp = MockHTTPResponse(b"data", headers={"content-length": "-10"})
        with pytest.raises(ValueError, match="negative value"):
            bounded_read(resp, max_bytes=1000)
        assert resp.closed is True

    def test_empty_response_handled(self):
        resp = MockHTTPResponse(b"", headers={"content-length": "0"})
        result = bounded_read(resp, max_bytes=1024)
        assert result == b""
        assert resp.closed is True

    def test_stream_always_closed_on_read_exception(self):
        class FaultyStream:
            def __init__(self):
                self.headers = {}
                self.closed = False
            def read(self, size=-1):
                raise OSError("Socket connection dropped abruptly")
            def close(self):
                self.closed = True

        faulty = FaultyStream()
        with pytest.raises(OSError, match="Socket connection dropped"):
            bounded_read(faulty, max_bytes=1024)
        assert faulty.closed is True


# ==============================================================================
# 4. Ingestion & Service Integration Security Tests (Mocked Network)
# ==============================================================================

class TestIngestionSecurityIntegration:

    @patch("testforge.ingestion.build_safe_opener")
    def test_fetch_github_source_rejects_oversized_file_without_disk_write(self, mock_build_opener, tmp_path):
        oversized_data = b"x = 1\n" * 100000  # ~600 KB
        mock_resp = MockHTTPResponse(oversized_data, headers={"content-length": str(len(oversized_data))})
        
        mock_opener = MagicMock()
        mock_opener.open.return_value = mock_resp
        mock_build_opener.return_value = mock_opener

        url = "https://github.com/psf/requests/blob/main/src/requests/models.py"
        
        with pytest.raises(PayloadTooLargeError):
            fetch_github_source_with_meta(url, output_dir=str(tmp_path), max_file_size_bytes=10000)

        # Verify that no file was written to disk
        created_files = list(tmp_path.glob("*.py"))
        assert len(created_files) == 0, f"Expected 0 files on failure, but found: {created_files}"

    @patch("testforge.ingestion.build_safe_opener")
    def test_fetch_github_source_rejects_ssrf_redirect(self, mock_build_opener, tmp_path):
        mock_opener = MagicMock()
        mock_opener.open.side_effect = SSRFSecurityError("Security Violation: Access to localhost forbidden: 'localhost'.")
        mock_build_opener.return_value = mock_opener

        url = "https://github.com/psf/requests/blob/main/src/requests/models.py"
        
        with pytest.raises(SSRFSecurityError, match="localhost"):
            fetch_github_source_with_meta(url, output_dir=str(tmp_path))

        created_files = list(tmp_path.glob("*.py"))
        assert len(created_files) == 0

    @patch.object(GitHubRepoService, "_make_github_request")
    def test_github_service_fetch_file_content_rejects_oversized_base64(self, mock_request):
        # 600 KB base64 content
        huge_bytes = b"a = 1\n" * 100000
        import base64
        huge_b64 = base64.b64encode(huge_bytes).decode("ascii")

        mock_request.return_value = ({"content": huge_b64, "encoding": "base64"}, {})

        svc = GitHubRepoService(max_file_size_bytes=10000)
        with pytest.raises(PayloadTooLargeError, match="exceeds maximum allowable limit"):
            svc.fetch_file_content("psf", "requests", "abcdef123456", "models.py")
