"""
tests/test_server_mcp_studio.py - Contract tests for FastMCP Protocol Studio backend API.
"""

from pathlib import Path
from fastapi.testclient import TestClient
import pytest

from server import app


@pytest.fixture(scope="module")
def client():
    return TestClient(app)


def test_mcp_execute_tool_ast_symbol_analyzer(client):
    """
    Test POST /api/mcp/execute-tool with mcp_ast_symbol_analyzer on samples/discount.py,
    asserting HTTP 200, transport, duration, and symbol list.
    """
    discount_path = Path("samples/discount.py")
    source_code = discount_path.read_text(encoding="utf-8")

    payload = {
        "tool_name": "mcp_ast_symbol_analyzer",
        "arguments": {
            "source_code": source_code,
        },
    }
    response = client.post("/api/mcp/execute-tool", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["tool"] == "mcp_ast_symbol_analyzer"
    assert data["transport"] in ("stdio", "in_process")
    assert "duration_ms" in data
    assert "result" in data
    assert "calculate_discount" in data["result"].get("symbols", [])


def test_mcp_execute_tool_mutant_generator(client):
    """
    Test POST /api/mcp/execute-tool with mcp_mutant_generator on samples/discount.py,
    asserting HTTP 200 and list of mutant records.
    """
    discount_path = Path("samples/discount.py")
    source_code = discount_path.read_text(encoding="utf-8")

    payload = {
        "tool_name": "mcp_mutant_generator",
        "arguments": {
            "source_code": source_code,
            "max_mutants": 10,
        },
    }
    response = client.post("/api/mcp/execute-tool", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert data["tool"] == "mcp_mutant_generator"
    assert isinstance(data["result"], list)
    assert len(data["result"]) > 0
    first = data["result"][0]
    assert "id" in first
    assert "diff" in first


def test_mcp_execute_tool_invalid_tool_name(client):
    """
    Test POST /api/mcp/execute-tool with invalid tool name returns HTTP 400.
    """
    payload = {
        "tool_name": "non_existent_tool_xyz",
        "arguments": {},
    }
    response = client.post("/api/mcp/execute-tool", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
    assert "Unknown tool" in data["detail"]


def test_mcp_execute_tool_missing_arguments(client):
    """
    Test POST /api/mcp/execute-tool with missing required argument returns HTTP 400.
    """
    payload = {
        "tool_name": "mcp_ast_symbol_analyzer",
        "arguments": {},
    }
    response = client.post("/api/mcp/execute-tool", json=payload)
    assert response.status_code == 400
    data = response.json()
    assert "detail" in data
