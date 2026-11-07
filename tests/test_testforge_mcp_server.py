"""
tests/test_testforge_mcp_server.py

Verification tests for Stage 2.2: TestForge as Native MCP Server.
Verifies:
  1. TestForge FastMCP server starts and connects over stdio.
  2. Tools (harden_module, get_report, list_jobs) are discovered.
  3. harden_module on samples/discount.py executes hardening and records metrics.
  4. get_report returns the job execution report.
  5. list_jobs returns all executed jobs.
  6. Path traversal and unauthorized paths are safely rejected.
  7. Claude desktop configuration exists and is valid.
"""

import json
from pathlib import Path

import pytest

from testforge.mcp_client import create_testforge_client


@pytest.mark.anyio
async def test_testforge_mcp_server_lifecycle_and_tools():
    root = Path(__file__).parent.parent.resolve()
    client = create_testforge_client(permitted_root=root)
    assert not client.is_connected

    await client.connect()
    assert client.is_connected

    tools = await client.list_tools()
    tool_names = [t.name for t in tools]
    assert "harden_module" in tool_names
    assert "get_report" in tool_names
    assert "list_jobs" in tool_names

    # 1. Execute harden_module
    harden_res = await client.call_tool("harden_module", {"file_path": "samples/discount.py"})
    assert harden_res.success is True
    job_data = harden_res.data
    assert "job_id" in job_data
    assert job_data["status"] == "COMPLETED"
    assert job_data["raw_mutation_score"] > 80.0
    assert job_data["total_mutants"] > 0
    job_id = job_data["job_id"]

    # 2. Query get_report
    report_res = await client.call_tool("get_report", {"job_id": job_id})
    assert report_res.success is True
    report_data = report_res.data
    assert report_data["job_id"] == job_id
    assert report_data["status"] == "COMPLETED"
    assert "full_test_code" in report_data

    # 3. Query list_jobs
    list_res = await client.call_tool("list_jobs", {})
    assert list_res.success is True
    jobs_data = list_res.data
    assert "jobs" in jobs_data
    assert isinstance(jobs_data["jobs"], list)
    assert any(j.get("job_id") == job_id for j in jobs_data["jobs"])

    # 4. Path traversal attack
    bad_res = await client.call_tool("harden_module", {"file_path": "../../etc/passwd"})
    # Either intercepted by client policy or server policy
    assert bad_res.success is False or "ERROR" in str(bad_res.data)

    await client.disconnect()
    assert not client.is_connected


def test_claude_desktop_config():
    config_path = Path("docs/claude_desktop_config.json")
    assert config_path.exists()

    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    assert "mcpServers" in config
    assert "testforge" in config["mcpServers"]
    tf_entry = config["mcpServers"]["testforge"]
    assert "command" in tf_entry
    assert "args" in tf_entry
    assert "testforge.mcp_server" in tf_entry["args"]
