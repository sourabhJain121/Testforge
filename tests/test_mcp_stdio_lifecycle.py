"""
tests/test_mcp_stdio_lifecycle.py - End-to-end integration tests for FastMCP
stdio subprocess transport lifecycle, tool discovery, RPC calls, fallback resilience,
and clean process termination.
"""

from pathlib import Path
import pytest

from testforge.mcp_client import FastMCPStdioClient
from testforge.observability import TestForgeOtelTracer


def test_stdio_subprocess_startup_and_tool_discovery():
    """
    Starts FastMCPStdioClient, verifies child subprocess PID > 0, checks is_alive(),
    calls list_tools(), and asserts all 4 protocol tools are discovered.
    """
    client = FastMCPStdioClient()
    try:
        client.start()
        assert client.pid is not None
        assert client.pid > 0
        assert client.is_alive()

        tools = client.list_tools()
        assert isinstance(tools, list)
        tool_names = [t["name"] for t in tools]
        expected_tools = [
            "mcp_ast_symbol_analyzer",
            "mcp_mutant_generator",
            "mcp_sandbox_runner",
            "mcp_equivalence_classifier",
        ]
        for expected in expected_tools:
            assert expected in tool_names, f"Expected {expected} in discovered tools: {tool_names}"
    finally:
        client.close()
        assert not client.is_alive()


def test_stdio_ast_symbol_analyzer_call():
    """
    Calls mcp_ast_symbol_analyzer on samples/discount.py source code over stdio,
    asserting valid AST output (symbols, cyclomatic complexity).
    """
    discount_path = Path("samples/discount.py")
    source_code = discount_path.read_text(encoding="utf-8")

    client = FastMCPStdioClient()
    try:
        client.start()
        res = client.call_tool("mcp_ast_symbol_analyzer", {"source_code": source_code})

        assert res.success is True
        assert res.error is None
        assert isinstance(res.data, dict)
        assert res.data.get("status") == "SUCCESS"
        assert "calculate_discount" in res.data.get("symbols", [])
        assert res.data.get("cyclomatic_complexity", 0) >= 3
    finally:
        client.close()


def test_stdio_mutant_generator_call():
    """
    Calls mcp_mutant_generator on samples/discount.py source code over stdio,
    asserting list of mutant dicts containing id, type, and diff.
    """
    discount_path = Path("samples/discount.py")
    source_code = discount_path.read_text(encoding="utf-8")

    client = FastMCPStdioClient()
    try:
        client.start()
        res = client.call_tool("mcp_mutant_generator", {"source_code": source_code, "max_mutants": 15})

        assert res.success is True
        assert res.error is None
        assert isinstance(res.data, list)
        assert len(res.data) > 0
        for m in res.data:
            assert "id" in m
            assert "type" in m
            assert "diff" in m
    finally:
        client.close()


def test_stdio_graceful_shutdown_and_fallback():
    """
    Verifies client.close() cleanly terminates subprocess with no zombies,
    and calling tool after process termination triggers MCP_STDIO_FALLBACK_TRIGGERED
    and returns a valid in-process result.
    """
    tracer = TestForgeOtelTracer.get_instance()
    tracer.clear()

    client = FastMCPStdioClient()
    client.start()
    pid = client.pid
    assert pid is not None
    assert client.is_alive()

    # Gracefully shut down
    client.close()
    assert client.is_alive() is False
    assert client.process is None

    # Call tool after process closure - must trigger fallback
    discount_path = Path("samples/discount.py")
    source_code = discount_path.read_text(encoding="utf-8")

    res = client.call_tool("mcp_ast_symbol_analyzer", {"source_code": source_code})

    # Assert fallback succeeded in-process
    assert res.success is True
    assert res.error is None
    assert "calculate_discount" in res.data.get("symbols", [])

    # Check telemetry span / fallback event recorded
    traces = tracer.get_traces_summary()
    span_names = [t["name"] for t in traces]
    assert "MCP_STDIO_FALLBACK_TRIGGERED" in span_names, f"Expected fallback event in traces: {span_names}"
