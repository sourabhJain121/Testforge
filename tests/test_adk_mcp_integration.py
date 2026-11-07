"""
tests/test_adk_mcp_integration.py

Verification tests for Stage 2.1: Model Context Protocol (MCP) in Google ADK Agents.
Verifies:
  1. FastMCP tools adapt into Google ADK FunctionTool instances.
  2. ADK tools successfully read files within permitted project root.
  3. Path traversal attacks (../../etc/passwd) are blocked by MCP containment.
  4. Sensitive files (.env, keys) are blocked by MCP containment.
  5. qa_artifacts/MCP_ADK_INVOCATION_TRACE.json and docs/MCP_ADK_INTEGRATION.md exist.
"""

import json
from pathlib import Path
import pytest

from testforge.adk_mcp_adapter import ADKMCPToolRegistry, run_mcp_adk_demo_and_save_trace


def test_adk_mcp_tool_adapter_instantiation():
    root = Path(__file__).parent.parent.resolve()
    registry = ADKMCPToolRegistry(permitted_root=root)
    tools = registry.get_adk_tools()

    assert len(tools) == 3
    tool_names = [t.name for t in tools]
    assert "read_text_file" in tool_names
    assert "list_directory" in tool_names
    assert "get_file_info" in tool_names


def test_adk_mcp_path_containment_and_security():
    root = Path(__file__).parent.parent.resolve()
    registry = ADKMCPToolRegistry(permitted_root=root)

    # 1. Valid read
    content = registry.read_text_file("samples/discount.py")
    assert "calculate_discount" in content

    # 2. Directory traversal attack
    res_traversal = registry.read_text_file("../../etc/passwd")
    assert "Security Violation" in res_traversal or "escapes permitted" in res_traversal

    # 3. Sensitive file attack
    res_env = registry.read_text_file(".env")
    assert "Security Violation" in res_env or "forbidden" in res_env

    registry.close()


def test_adk_mcp_trace_artifact_and_documentation():
    trace_path = Path("qa_artifacts/MCP_ADK_INVOCATION_TRACE.json")
    assert trace_path.exists()

    with open(trace_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["results"]["valid_read_success"] is True
    assert data["results"]["traversal_attack_blocked"] is True
    assert data["results"]["sensitive_file_attack_blocked"] is True
    assert len(data["traces"]) >= 4

    doc_path = Path("docs/MCP_ADK_INTEGRATION.md")
    assert doc_path.exists()
    content = doc_path.read_text(encoding="utf-8")
    assert "FastMCP" in content
    assert "Google ADK" in content
    assert "Directory Traversal Attack" in content
