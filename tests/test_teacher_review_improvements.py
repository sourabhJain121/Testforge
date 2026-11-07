"""
tests/test_teacher_review_improvements.py - Verification for Approved Teacher Review Improvements.

Verifies:
1. Improvement A: Real backend lifecycle progress and stage durations.
2. Improvement B: Live Blackboard partition summary (5 partitions, revision, statuses).
3. Improvement C: Safe FastMCP diagnostic tool execution with security boundary enforcement.
4. Improvement D: Safe A2A protocol diagnostic verification with SSRF guardrails.
"""

import pytest
from fastapi.testclient import TestClient

from server import JOB_LOCK, JOBS, app


@pytest.fixture
def client():
    return TestClient(app)


# ==============================================================================
# 1. Improvement C: FastMCP Diagnostic Tool Invocation & Security Guardrails
# ==============================================================================

class TestMCPDiagnosticAction:
    def test_mcp_list_directory_success(self, client):
        resp = client.post("/api/mcp/test", json={"tool_name": "list_directory", "path": "samples"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert data["protocol"] == "Model Context Protocol (FastMCP)"
        assert data["tool_name"] == "list_directory"
        assert data["elapsed_ms"] > 0
        assert isinstance(data["data"], list)
        names = [f["name"] for f in data["data"]]
        assert "discount.py" in names

    def test_mcp_get_file_info_success(self, client):
        resp = client.post("/api/mcp/test", json={"tool_name": "get_file_info", "path": "samples/discount.py"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert data["tool_name"] == "get_file_info"
        assert data["data"]["is_file"] is True
        assert data["data"]["size_bytes"] > 0
        assert "sha256" in data["data"]

    def test_mcp_path_traversal_rejected(self, client):
        resp = client.post("/api/mcp/test", json={"tool_name": "get_file_info", "path": "../server.py"})
        assert resp.status_code == 400
        assert "directory traversal" in resp.json()["detail"].lower()

    def test_mcp_sensitive_file_rejected(self, client):
        resp = client.post("/api/mcp/test", json={"tool_name": "get_file_info", "path": ".env"})
        assert resp.status_code == 400
        assert "sensitive credential" in resp.json()["detail"].lower()

    def test_mcp_disallowed_tool_rejected(self, client):
        resp = client.post("/api/mcp/test", json={"tool_name": "unwhitelisted_tool", "path": "samples"})
        assert resp.status_code == 422


# ==============================================================================
# 2. Improvement D: A2A Protocol Diagnostic Verification & SSRF Guardrails
# ==============================================================================

class TestA2ADiagnosticAction:
    def test_a2a_local_verification_success(self, client):
        resp = client.post("/api/a2a/test", json={"target_url": "http://127.0.0.1:8000/"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "success"
        assert data["protocol_version"] == "0.3.0"
        assert data["agent_name"] == "testforge-agent-system"
        assert data["schema_verified"] is True
        assert len(data["skills"]) == 3
        assert "Unit Test Generation" in data["skills"]

    def test_a2a_remote_ssrf_rejected(self, client):
        resp = client.post("/api/a2a/test", json={"target_url": "http://169.254.169.254/latest/meta-data"})
        assert resp.status_code == 400
        assert "restricted strictly to local" in resp.json()["detail"].lower()

    def test_a2a_external_domain_rejected(self, client):
        resp = client.post("/api/a2a/test", json={"target_url": "https://evil-attacker.com/agent.json"})
        assert resp.status_code == 400
        assert "restricted strictly to local" in resp.json()["detail"].lower()


# ==============================================================================
# 3. Improvement A & B: Blackboard Summary & Lifecycle in Job Status
# ==============================================================================

class TestJobStatusEnrichment:
    def test_blackboard_summary_in_completed_job(self, client):
        job_id = "test_bb_job_1"
        with JOB_LOCK:
            JOBS[job_id] = {
                "job_id": job_id,
                "status": "COMPLETED",
                "lifecycle_state": "COMPLETED",
                "final_state": {
                    "revision": 82,
                    "target_module_path": "samples/discount.py",
                    "target_metadata": {"functions": ["calculate_discount"]},
                    "blast_risk": "LOW",
                    "active_provider": "Google ADK Generator",
                    "hardened_test_code": "def test_hardened(): pass",
                    "mutants": [
                        {"mutant_id": "m1", "status": "KILLED"},
                        {"mutant_id": "m2", "status": "SURVIVED"}
                    ],
                    "critic_directives": ["Add boundary test"],
                    "history": [{"iteration": 1}],
                    "final_mutation_score": 50.0,
                    "final_hardening_status": "TARGET_SCORE_UNREACHED"
                }
            }

        resp = client.get(f"/api/harden/status/{job_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "COMPLETED"
        assert data["lifecycle_state"] == "COMPLETED"
        assert "blackboard_summary" in data

        bb = data["blackboard_summary"]
        assert bb["revision"] == 82
        spaces = bb["spaces"]
        assert "TargetSpace" in spaces
        assert spaces["TargetSpace"]["module"] == "samples/discount.py"
        assert spaces["TargetSpace"]["functions_count"] == 1

        assert "SuiteSpace" in spaces
        assert spaces["SuiteSpace"]["has_hardened"] is True

        assert "MutantSpace" in spaces
        assert spaces["MutantSpace"]["killed"] == 1
        assert spaces["MutantSpace"]["survived"] == 1
        assert spaces["MutantSpace"]["score"] == 50.0

        assert "CriticSpace" in spaces
        assert spaces["CriticSpace"]["directives_count"] == 1

        assert "MetricsSpace" in spaces
        assert spaces["MetricsSpace"]["iteration"] == 1
        assert spaces["MetricsSpace"]["status_val"] == "TARGET_SCORE_UNREACHED"
