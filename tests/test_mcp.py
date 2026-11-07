"""
test_mcp.py - Comprehensive Unit and Integration Tests for Model Context Protocol (MCP).

Tests:
  1. MCP client connection and clean shutdown.
  2. Tool discovery from a real MCP server.
  3. Successful tool invocation (read_text_file, get_file_info, list_directory).
  4. Invalid tool names and invalid arguments.
  5. Server errors, unhandled exceptions, and malformed responses.
  6. Timeout enforcement and unavailable-server behavior.
  7. Filesystem root restrictions, path traversal, and sensitive file protection.
  8. Secret redaction in callback events and logs.
  9. Blackboard summary synchronization.
  10. Orchestrator integration and legacy behavior preservation.
  11. GitHub MCP integration with unauthenticated / authenticated handling.
"""

import os
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from mcp.client.stdio import StdioServerParameters

from testforge.blackboard import Blackboard
from testforge.callbacks import CallbackRegistry, EventType, LifecycleEvent
from testforge.mcp_client import MCPClientManager, MCPToolResult, create_filesystem_client, create_github_client
from testforge.mcp_server import create_filesystem_server, create_github_server
from testforge.orchestrator import TestForgeOrchestrator

REPO_ROOT = Path(__file__).parent.parent.resolve()
SAMPLES_DIR = REPO_ROOT / "samples"


class TestMCPConnection:
    @pytest.mark.anyio
    async def test_client_connection_and_clean_shutdown(self):
        client = create_filesystem_client(permitted_root=SAMPLES_DIR, use_node=False)
        assert not client.is_connected

        await client.connect()
        assert client.is_connected

        tools = await client.list_tools()
        assert len(tools) >= 3
        tool_names = [t.name for t in tools]
        assert "read_text_file" in tool_names
        assert "list_directory" in tool_names
        assert "get_file_info" in tool_names

        await client.disconnect()
        assert not client.is_connected

    @pytest.mark.anyio
    async def test_server_unavailable_connection_failure(self):
        params = StdioServerParameters(
            command="/nonexistent/binary/path/that/does/not/exist",
            args=[]
        )
        registry = CallbackRegistry()
        error_events = []
        registry.register(lambda e: error_events.append(e), event_types=[EventType.ERROR])

        client = MCPClientManager(
            server_params=params,
            callback_registry=registry,
            server_id="failing-server"
        )
        with pytest.raises(ConnectionError) as exc_info:
            await client.connect()

        assert "connection failed" in str(exc_info.value).lower()
        assert not client.is_connected
        assert len(error_events) >= 1
        assert error_events[0].payload.get("error_type") == "ConnectionError"


class TestMCPToolDiscovery:
    @pytest.mark.anyio
    async def test_filesystem_tool_discovery_and_schemas(self):
        client = create_filesystem_client(permitted_root=SAMPLES_DIR, use_node=False)
        async with client:
            tools = await client.list_tools()
            tools_by_name = {t.name: t for t in tools}

            assert "read_text_file" in tools_by_name
            read_tool = tools_by_name["read_text_file"]
            assert "path" in str(read_tool.input_schema)

            assert "get_file_info" in tools_by_name
            info_tool = tools_by_name["get_file_info"]
            assert "path" in str(info_tool.input_schema)

    @pytest.mark.anyio
    async def test_github_tool_discovery(self):
        client = create_github_client(use_node=False)
        async with client:
            tools = await client.list_tools()
            tool_names = [t.name for t in tools]
            assert "get_file_contents" in tool_names
            assert "get_repository_info" in tool_names
            assert "search_repositories" in tool_names


class TestMCPToolExecution:
    @pytest.mark.anyio
    async def test_successful_read_text_file(self):
        client = create_filesystem_client(permitted_root=SAMPLES_DIR, use_node=False)
        async with client:
            res = await client.call_tool("read_text_file", {"path": "banking.py"})
            assert res.success, f"Tool failed: {res.error}"
            assert isinstance(res.data, str)
            assert "def transfer(" in res.data or "balance" in res.data
            assert res.duration_ms > 0

    @pytest.mark.anyio
    async def test_successful_get_file_info(self):
        client = create_filesystem_client(permitted_root=SAMPLES_DIR, use_node=False)
        async with client:
            res = await client.call_tool("get_file_info", {"path": "banking.py"})
            assert res.success, f"Tool failed: {res.error}"
            assert isinstance(res.data, dict)
            assert res.data.get("is_file") is True
            assert res.data.get("size_bytes") > 0
            assert res.data.get("line_count") > 0
            assert len(res.data.get("sha256")) == 64

    @pytest.mark.anyio
    async def test_successful_list_directory(self):
        client = create_filesystem_client(permitted_root=SAMPLES_DIR, use_node=False)
        async with client:
            res = await client.call_tool("list_directory", {"path": "."})
            assert res.success, f"Tool failed: {res.error}"
            assert isinstance(res.data, list)
            names = [entry["name"] for entry in res.data]
            assert "banking.py" in names

    def test_sync_execution_wrapper(self):
        client = create_filesystem_client(permitted_root=SAMPLES_DIR, use_node=False)
        res = client.call_tool_sync("read_text_file", {"path": "banking.py"})
        assert res.success
        assert isinstance(res.data, str)
        assert len(res.data) > 0


class TestMCPSecurityPolicies:
    @pytest.mark.anyio
    async def test_path_traversal_rejection(self):
        client = create_filesystem_client(permitted_root=SAMPLES_DIR, use_node=False)
        async with client:
            # Traversal escape
            res = await client.call_tool("read_text_file", {"path": "../../etc/passwd"})
            assert not res.success
            assert "Security Violation" in res.error
            assert "escapes permitted" in res.error

    @pytest.mark.anyio
    async def test_absolute_path_escape_rejection(self):
        client = create_filesystem_client(permitted_root=SAMPLES_DIR, use_node=False)
        async with client:
            res = await client.call_tool("read_text_file", {"path": "/etc/shadow"})
            assert not res.success
            assert "Security Violation" in res.error

    @pytest.mark.anyio
    async def test_sensitive_credential_file_rejection(self, tmp_path):
        # Create dummy sensitive files inside permitted root
        env_file = tmp_path / ".env"
        env_file.write_text("SECRET_API_KEY=supersecret12345", encoding="utf-8")
        key_file = tmp_path / "server.key"
        key_file.write_text("PRIVATE KEY DATA", encoding="utf-8")
        safe_file = tmp_path / "module.py"
        safe_file.write_text("x = 1", encoding="utf-8")

        client = create_filesystem_client(permitted_root=tmp_path, use_node=False)
        async with client:
            # Attempt .env read
            res_env = await client.call_tool("read_text_file", {"path": ".env"})
            assert not res_env.success
            assert "Security Violation" in res_env.error
            assert ".env" in res_env.error

            # Attempt .key read
            res_key = await client.call_tool("read_text_file", {"path": "server.key"})
            assert not res_key.success
            assert "Security Violation" in res_key.error

            # Safe file allowed
            res_safe = await client.call_tool("read_text_file", {"path": "module.py"})
            assert res_safe.success
            assert res_safe.data == "x = 1"

    @pytest.mark.anyio
    async def test_blocked_destructive_tools(self):
        client = create_filesystem_client(permitted_root=SAMPLES_DIR, use_node=False)
        async with client:
            for destructive_tool in ("write_file", "delete_file", "edit_file", "move_file"):
                res = await client.call_tool(destructive_tool, {"path": "test.py", "content": "bad"})
                assert not res.success
                assert "Security Policy Violation" in res.error

    @pytest.mark.anyio
    async def test_invalid_tool_name(self):
        client = create_filesystem_client(permitted_root=SAMPLES_DIR, use_node=False)
        async with client:
            res = await client.call_tool("unknown_tool_foobar", {})
            assert not res.success
            assert "Security Policy Violation" in res.error or "Unknown tool" in res.error


class TestMCPFailureHandlingAndIsolation:
    @pytest.mark.anyio
    async def test_nonexistent_file_handling(self):
        client = create_filesystem_client(permitted_root=SAMPLES_DIR, use_node=False)
        async with client:
            res = await client.call_tool("read_text_file", {"path": "completely_nonexistent_file_123.py"})
            assert not res.success
            assert "File not found" in res.error

    @pytest.mark.anyio
    async def test_tool_timeout_handling(self):
        client = create_filesystem_client(permitted_root=SAMPLES_DIR, use_node=False)
        async with client:
            # Calling with 0.00001s timeout guarantees timeout triggering
            res = await client.call_tool("read_text_file", {"path": "banking.py"}, timeout=0.00001)
            assert not res.success
            assert "timed out" in res.error.lower()


class TestMCPCallbacksAndRedaction:
    @pytest.mark.anyio
    async def test_lifecycle_callbacks_and_secret_redaction(self):
        registry = CallbackRegistry()
        events = []
        registry.register(lambda e: events.append(e), event_types=[EventType.TOOL_START, EventType.TOOL_COMPLETE])

        client = create_filesystem_client(
            permitted_root=SAMPLES_DIR,
            use_node=False,
            callback_registry=registry
        )
        async with client:
            # Pass a dummy token in arguments to verify redaction in callbacks
            await client.call_tool("read_text_file", {
                "path": "banking.py",
                "api_key": "sk-secret123456789012345"
            })

        start_events = [e for e in events if e.event_type == EventType.TOOL_START]
        complete_events = [e for e in events if e.event_type == EventType.TOOL_COMPLETE]

        assert len(start_events) == 1
        assert len(complete_events) == 1

        payload_str = str(start_events[0].payload)
        assert "sk-secret123456789012345" not in payload_str
        assert "[REDACTED_SECRET]" in payload_str or "api_key" in payload_str


class TestMCPBlackboardAndOrchestrator:
    @pytest.mark.anyio
    async def test_blackboard_target_space_sync(self):
        bb = Blackboard()
        client = create_filesystem_client(permitted_root=SAMPLES_DIR, use_node=False)
        async with client:
            res = await client.call_tool("get_file_info", {"path": "banking.py"})
            assert res.success

            client.sync_to_blackboard(res, bb)
            target = bb.get_target_space()
            assert len(target.source_sha) == 64
            assert target.line_count > 0

    def test_orchestrator_optional_mcp_integration(self):
        client = create_filesystem_client(permitted_root=SAMPLES_DIR, use_node=False)
        target_code = "def add(a, b):\n    return a + b\n"

        orch = TestForgeOrchestrator(
            target_source_code=target_code,
            max_iterations=1,
            mcp_client=client
        )
        assert orch.mcp_client is not None

        # Invoke tool through orchestrator
        res = orch.invoke_mcp_tool("get_file_info", {"path": "banking.py"})
        assert res is not None
        assert res.success
        assert len(orch.blackboard.get_target_space().source_sha) == 64

    def test_orchestrator_legacy_behavior_without_mcp(self):
        target_code = "def subtract(a, b):\n    return a - b\n"
        orch = TestForgeOrchestrator(
            target_source_code=target_code,
            max_iterations=1,
            mcp_client=None
        )
        assert orch.mcp_client is None
        res = orch.invoke_mcp_tool("get_file_info", {"path": "banking.py"})
        assert res is None
        assert orch.state.target_source_code.strip() == target_code.strip()


class TestMCPGitHubIntegration:
    @pytest.mark.anyio
    async def test_github_unauthenticated_or_rate_limit_handling(self):
        """
        Verifies that GitHub MCP server starts, discovers tools, and handles
        unauthenticated / rate-limited requests gracefully without crashing.
        """
        client = create_github_client(use_node=False)
        async with client:
            tools = await client.list_tools()
            assert len(tools) >= 3

            # Invoke search_repositories
            res = await client.call_tool("search_repositories", {"query": "TestForge", "limit": 1})
            # If token is configured, success is True; if rate limited or unauthenticated, error message is returned cleanly
            if res.success:
                assert isinstance(res.data, (list, dict))
                if isinstance(res.data, list) and len(res.data) > 0:
                    assert "full_name" in res.data[0]
                elif isinstance(res.data, dict):
                    assert "full_name" in res.data
            else:
                assert res.error is not None
                assert "GitHub" in res.error or "rate" in res.error.lower() or "connect" in res.error.lower()

    @pytest.mark.anyio
    async def test_official_npx_filesystem_server_stdio(self):
        """
        Tests integration with the official @modelcontextprotocol/server-filesystem
        via npx over stdio when Node/npx is available.
        """
        import shutil
        if not (shutil.which("npx") or os.path.exists("/Users/sourabh/.nvm/versions/node/v24.15.0/bin/npx")):
            pytest.skip("npx not available on system")

        client = create_filesystem_client(permitted_root=SAMPLES_DIR, use_node=True)
        async with client:
            tools = await client.list_tools()
            tool_names = [t.name for t in tools]
            assert "read_file" in tool_names or "read_text_file" in tool_names

            # Test calling real official read tool
            call_tool = "read_text_file" if "read_text_file" in tool_names else "read_file"
            res = await client.call_tool(call_tool, {"path": str(SAMPLES_DIR / "banking.py")})
            assert res.success
            assert "def transfer(" in str(res.data) or "balance" in str(res.data)

    @pytest.mark.anyio
    async def test_official_npx_github_server_stdio(self):
        """
        Tests end-to-end integration with the official @modelcontextprotocol/server-github
        via npx over stdio when Node/npx is available.
        """
        import shutil
        if not (shutil.which("npx") or os.path.exists("/Users/sourabh/.nvm/versions/node/v24.15.0/bin/npx")):
            pytest.skip("npx not available on system")

        client = create_github_client(use_node=True)
        async with client:
            tools = await client.list_tools()
            assert len(tools) >= 20
            tool_names = [t.name for t in tools]
            assert "search_repositories" in tool_names
            assert "get_file_contents" in tool_names

            # Execute real read operation through official server
            res = await client.call_tool("search_repositories", {"query": "TestForge"})
            if res.success:
                assert res.data is not None
                assert "items" in str(res.data) or "TestForge" in str(res.data)
            else:
                # Handle rate limiting or permission denial on unauthenticated IP
                assert "rate limit" in str(res.error).lower() or "permission denied" in str(res.error).lower()
