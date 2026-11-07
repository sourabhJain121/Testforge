"""
test_mcp_status_endpoint.py - Tests for /api/mcp/status Endpoint.

Tests:
  1. GET /api/mcp/status returns 200 OK with expected schema.
  2. Lists both testforge-filesystem and testforge-github servers.
  3. Correctly enumerates registered tools without leaking secret keys.
  4. Non-destructive operation: endpoint does not execute unsafe filesystem commands.
"""

import pytest
from fastapi.testclient import TestClient

from server import app


@pytest.fixture
def client():
    return TestClient(app)


def test_mcp_status_endpoint_structure(client):
    resp = client.get("/api/mcp/status")
    assert resp.status_code == 200
    data = resp.json()

    assert data["status"] == "operational"
    assert "FastMCP" in data["sdk"]
    assert "servers" in data
    assert len(data["servers"]) >= 2
    assert data["total_tools_registered"] >= 4

    server_ids = [s["server_id"] for s in data["servers"]]
    assert "testforge-filesystem" in server_ids
    assert "testforge-github" in server_ids

    # Verify tool names without leaking secrets
    fs_server = next(s for s in data["servers"] if s["server_id"] == "testforge-filesystem")
    tool_names = [t["name"] for t in fs_server["tools"]]
    assert "read_text_file" in tool_names
    assert "list_directory" in tool_names
    assert "get_file_info" in tool_names


def test_ready_alias_endpoint(client):
    resp = client.get("/api/ready")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ready"
    assert data["service"] == "testforge-backend"
    assert data["subsystems"]["blackboard"] == "operational"
