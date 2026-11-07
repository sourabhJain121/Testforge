"""
test_mcp_network_security.py - Integration Tests for MCP Server Network Security.

Tests real urllib request dispatching, redirect interception, credential stripping,
and bounded payload limits across FastMCP GitHub tools without over-mocking the security handlers.
"""

from __future__ import annotations

import base64
import email.message
import io
import json
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional

import pytest

from testforge.mcp_server import create_github_server
from testforge.network_security import (
    ALLOWED_GITHUB_HOSTS,
    DEFAULT_MAX_SOURCE_SIZE_BYTES,
    PayloadTooLargeError,
    SafeGitHubRedirectHandler,
    SSRFSecurityError,
)


class MockHTTPSTransport(urllib.request.BaseHandler):
    """
    A real urllib BaseHandler that simulates HTTP/HTTPS transport responses
    without connecting to the live internet.
    Enables testing real OpenerDirector dispatch, SafeGitHubRedirectHandler interception,
    and HTTPRedirectHandler loop/depth handling.
    """
    handler_order = 100

    def __init__(self):
        self.routes: Dict[str, Any] = {}
        self.dispatched_requests: List[Dict[str, Any]] = []

    def register_route(
        self,
        url: str,
        status_code: int = 200,
        body: bytes = b"",
        headers: Optional[Dict[str, str]] = None
    ):
        self.routes[url] = {
            "status": status_code,
            "body": body,
            "headers": headers or {}
        }

    def https_open(self, req: urllib.request.Request):
        url = req.full_url
        self.dispatched_requests.append({
            "url": url,
            "headers": {k.lower(): v for k, v in req.headers.items()},
            "unredirected_hdrs": {k.lower(): v for k, v in req.unredirected_hdrs.items()}
        })

        if url not in self.routes:
            # Return HTTP 404
            err_headers = email.message.Message()
            fp = io.BytesIO(b'{"message": "Not Found"}')
            return self.parent.error("http", req, fp, 404, "Not Found", err_headers)

        route = self.routes[url]
        code = route["status"]
        body = route["body"]
        msg_headers = email.message.Message()
        for k, v in route["headers"].items():
            msg_headers[k] = v

        stream = io.BytesIO(body)
        resp = urllib.response.addinfourl(stream, msg_headers, url, code)
        resp.code = code
        resp.msg = "OK" if code == 200 else ("Found" if code == 302 else "Status")

        if 300 <= code < 400:
            # Delegate to urllib's error chain, which invokes HTTPRedirectHandler
            return self.parent.error("http", req, resp, code, resp.msg, msg_headers)

        return resp


@pytest.fixture
def transport_and_opener():
    transport = MockHTTPSTransport()
    redirect_handler = SafeGitHubRedirectHandler(
        allowed_hosts={"api.github.com", "raw.githubusercontent.com", "objects.githubusercontent.com"}
    )
    opener = urllib.request.build_opener(redirect_handler, transport)
    return transport, opener


# ==============================================================================
# MCP Security Integration Tests
# ==============================================================================

class TestMCPNetworkSecurityIntegration:

    def test_legitimate_github_api_request(self, transport_and_opener):
        transport, opener = transport_and_opener
        api_url = "https://api.github.com/repos/psf/requests"
        repo_data = {
            "full_name": "psf/requests",
            "description": "Python HTTP for Humans.",
            "default_branch": "main",
            "stargazers_count": 52000,
            "open_issues_count": 120,
            "topics": ["python", "http", "requests"]
        }
        transport.register_route(
            api_url,
            status_code=200,
            body=json.dumps(repo_data).encode("utf-8"),
            headers={"Content-Type": "application/json", "Content-Length": str(len(json.dumps(repo_data)))}
        )

        server = create_github_server(github_token="test-token", opener=opener)
        info_tool = server._tool_manager.get_tool("get_repository_info")
        result = info_tool.fn(owner="psf", repo="requests")

        assert result["full_name"] == "psf/requests"
        assert result["default_branch"] == "main"
        assert result["stargazers_count"] == 52000
        assert len(transport.dispatched_requests) == 1
        assert transport.dispatched_requests[0]["url"] == api_url

    def test_redirect_to_unauthorized_host_blocked(self, transport_and_opener):
        transport, opener = transport_and_opener
        api_url = "https://api.github.com/repos/psf/requests"
        transport.register_route(
            api_url,
            status_code=302,
            body=b"Redirecting...",
            headers={"Location": "https://attacker.com/evil_steal"}
        )

        server = create_github_server(github_token="test-token", opener=opener)
        info_tool = server._tool_manager.get_tool("get_repository_info")

        with pytest.raises(SSRFSecurityError, match="not an authorized GitHub endpoint"):
            info_tool.fn(owner="psf", repo="requests")

    def test_redirect_to_localhost_blocked(self, transport_and_opener):
        transport, opener = transport_and_opener
        api_url = "https://api.github.com/repos/psf/requests"
        transport.register_route(
            api_url,
            status_code=302,
            body=b"Redirecting to local...",
            headers={"Location": "https://localhost:443/secret"}
        )

        server = create_github_server(github_token="test-token", opener=opener)
        info_tool = server._tool_manager.get_tool("get_repository_info")

        with pytest.raises(SSRFSecurityError, match="localhost"):
            info_tool.fn(owner="psf", repo="requests")

    def test_redirect_to_private_ip_blocked(self, transport_and_opener):
        transport, opener = transport_and_opener
        api_url = "https://api.github.com/repos/psf/requests"
        transport.register_route(
            api_url,
            status_code=302,
            body=b"Redirecting to internal network...",
            headers={"Location": "https://192.168.1.1/admin"}
        )

        server = create_github_server(github_token="test-token", opener=opener)
        info_tool = server._tool_manager.get_tool("get_repository_info")

        with pytest.raises(SSRFSecurityError, match="forbidden"):
            info_tool.fn(owner="psf", repo="requests")

    def test_multiple_redirect_attempts_exceeding_limit(self, transport_and_opener):
        transport, opener = transport_and_opener
        # Register a chain of 7 redirects exceeding max_redirections (5)
        for i in range(7):
            curr_url = f"https://api.github.com/repos/psf/hop{i}"
            next_url = f"https://api.github.com/repos/psf/hop{i+1}"
            transport.register_route(
                curr_url,
                status_code=302,
                body=b"Hop...",
                headers={"Location": next_url}
            )

        server = create_github_server(github_token="test-token", opener=opener)
        info_tool = server._tool_manager.get_tool("get_repository_info")

        with pytest.raises((urllib.error.HTTPError, RuntimeError), match="redirect error"):
            info_tool.fn(owner="psf", repo="hop0")

    def test_credential_stripping_across_host_changes(self, transport_and_opener):
        transport, opener = transport_and_opener
        api_url = "https://api.github.com/repos/psf/requests"
        cdn_url = "https://objects.githubusercontent.com/asset/file.tar.gz"

        transport.register_route(
            api_url,
            status_code=302,
            body=b"Redirecting to asset CDN...",
            headers={"Location": cdn_url}
        )
        transport.register_route(
            cdn_url,
            status_code=200,
            body=b'{"full_name": "psf/requests", "default_branch": "main"}',
            headers={"Content-Length": "56"}
        )

        server = create_github_server(github_token="ghp_SECRET_TOKEN_4321", opener=opener)
        info_tool = server._tool_manager.get_tool("get_repository_info")
        res = info_tool.fn(owner="psf", repo="requests")

        assert res["full_name"] == "psf/requests"
        assert len(transport.dispatched_requests) == 2

        # 1st request (api.github.com): MUST contain Authorization
        req1 = transport.dispatched_requests[0]
        assert req1["url"] == api_url
        assert "authorization" in req1["headers"] or "authorization" in req1["unredirected_hdrs"]

        # 2nd request (objects.githubusercontent.com): Authorization MUST be stripped
        req2 = transport.dispatched_requests[1]
        assert req2["url"] == cdn_url
        assert "authorization" not in req2["headers"]
        assert "authorization" not in req2["unredirected_hdrs"]
        # User-Agent preserved
        assert any("user-agent" in k for k in req2["headers"])

    def test_oversized_response_with_content_length(self, transport_and_opener):
        transport, opener = transport_and_opener
        api_url = "https://api.github.com/repos/psf/huge"
        transport.register_route(
            api_url,
            status_code=200,
            body=b"X" * 20000,
            headers={"Content-Length": "20000"}
        )

        # Configured with max_total_bytes = 5000 (< 20000)
        server = create_github_server(
            github_token="token",
            max_total_bytes=5000,
            opener=opener
        )
        info_tool = server._tool_manager.get_tool("get_repository_info")

        with pytest.raises(PayloadTooLargeError, match="exceeds maximum allowable limit"):
            info_tool.fn(owner="psf", repo="huge")

    def test_oversized_response_without_content_length(self, transport_and_opener):
        transport, opener = transport_and_opener
        api_url = "https://api.github.com/repos/psf/stream_huge"
        # No Content-Length header, but body exceeds limit
        transport.register_route(
            api_url,
            status_code=200,
            body=b"Z" * 15000,
            headers={}
        )

        server = create_github_server(
            github_token="token",
            max_total_bytes=5000,
            opener=opener
        )
        info_tool = server._tool_manager.get_tool("get_repository_info")

        with pytest.raises(PayloadTooLargeError, match="exceeded maximum allowable size"):
            info_tool.fn(owner="psf", repo="stream_huge")

    def test_base64_payload_exceeding_limit(self, transport_and_opener):
        transport, opener = transport_and_opener
        contents_url = "https://api.github.com/repos/psf/requests/contents/huge_file.py?ref=main"
        # Payload of 3000 bytes encoded in base64
        huge_raw = b"val = 1\n" * 400
        encoded = base64.b64encode(huge_raw).decode("ascii")
        json_resp = {
            "name": "huge_file.py",
            "path": "huge_file.py",
            "sha": "abcdef12345",
            "size": len(huge_raw),
            "content": encoded,
            "encoding": "base64"
        }
        transport.register_route(
            contents_url,
            status_code=200,
            body=json.dumps(json_resp).encode("utf-8"),
            headers={"Content-Length": str(len(json.dumps(json_resp)))}
        )

        # Cap file size at 500 bytes (payload is ~3200 bytes)
        server = create_github_server(
            github_token="token",
            max_file_size_bytes=500,
            opener=opener
        )
        contents_tool = server._tool_manager.get_tool("get_file_contents")

        with pytest.raises(PayloadTooLargeError, match="exceeds"):
            contents_tool.fn(owner="psf", repo="requests", path="huge_file.py", ref="main")

    def test_normal_base64_file_retrieval(self, transport_and_opener):
        transport, opener = transport_and_opener
        contents_url = "https://api.github.com/repos/psf/requests/contents/safe.py?ref=main"
        code = b"def calculate(a, b):\n    return a + b\n"
        encoded = base64.b64encode(code).decode("ascii")
        json_resp = {
            "name": "safe.py",
            "path": "safe.py",
            "sha": "11223344",
            "size": len(code),
            "content": encoded,
            "encoding": "base64"
        }
        transport.register_route(
            contents_url,
            status_code=200,
            body=json.dumps(json_resp).encode("utf-8"),
            headers={"Content-Length": str(len(json.dumps(json_resp)))}
        )

        server = create_github_server(
            github_token="token",
            max_file_size_bytes=DEFAULT_MAX_SOURCE_SIZE_BYTES,
            opener=opener
        )
        contents_tool = server._tool_manager.get_tool("get_file_contents")
        res = contents_tool.fn(owner="psf", repo="requests", path="safe.py", ref="main")

        assert res["name"] == "safe.py"
        assert res["path"] == "safe.py"
        assert "def calculate(" in res["content"]
        assert res["size"] == len(code)

    def test_response_cleanup_on_failure(self):
        class ClosableStream:
            def __init__(self, data: bytes):
                self._io = io.BytesIO(data)
                self.closed = False
                self.headers = {"content-length": "200000"}
            def read(self, size=-1):
                return self._io.read(size)
            def close(self):
                self.closed = True

        from testforge.network_security import bounded_read
        stream = ClosableStream(b"data" * 100)
        with pytest.raises(PayloadTooLargeError):
            bounded_read(stream, max_bytes=1000)

        assert stream.closed is True

    def test_existing_mcp_functionality_remains_operational(self, transport_and_opener):
        transport, opener = transport_and_opener
        # 1. Search repos
        search_url = "https://api.github.com/search/repositories?q=testforge&per_page=5"
        search_data = {
            "items": [
                {"full_name": "sourabh/TestForge", "description": "Agentic test hardening", "stargazers_count": 42, "html_url": "https://github.com/sourabh/TestForge"}
            ]
        }
        transport.register_route(
            search_url,
            status_code=200,
            body=json.dumps(search_data).encode("utf-8"),
            headers={"Content-Length": str(len(json.dumps(search_data)))}
        )

        # 2. Git tree
        tree_url = "https://api.github.com/repos/sourabh/TestForge/git/trees/main?recursive=1"
        tree_data = {
            "sha": "main-tree-sha",
            "truncated": False,
            "tree": [
                {"path": "testforge/orchestrator.py", "mode": "100644", "type": "blob", "size": 12000, "sha": "sha1"}
            ]
        }
        transport.register_route(
            tree_url,
            status_code=200,
            body=json.dumps(tree_data).encode("utf-8"),
            headers={"Content-Length": str(len(json.dumps(tree_data)))}
        )

        server = create_github_server(github_token="token", opener=opener)
        search_tool = server._tool_manager.get_tool("search_repositories")
        search_res = search_tool.fn(query="testforge", limit=5)
        assert len(search_res) == 1
        assert search_res[0]["full_name"] == "sourabh/TestForge"

        tree_tool = server._tool_manager.get_tool("get_repository_tree")
        tree_res = tree_tool.fn(owner="sourabh", repo="TestForge", ref="main", recursive=True)
        assert tree_res["sha"] == "main-tree-sha"
        assert len(tree_res["tree"]) == 1
        assert tree_res["tree"][0]["path"] == "testforge/orchestrator.py"
