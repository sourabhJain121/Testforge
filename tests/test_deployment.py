"""
test_deployment.py - Verification Suite for Deployment Readiness & Health Probes.

Validates:
  1. FastAPI application startup and route registration.
  2. Liveness probe (`GET /healthz`) responds 200 OK.
  3. Readiness probe (`GET /readyz`) verifies AST mutator, blackboard, and filesystem.
  4. Discovery probe (`GET /.well-known/agent-card.json`) returns valid A2A AgentCard.
  5. Status endpoint (`GET /api/status`) reflects hardware and provider topology.
  6. Dockerfile and docker-compose.yml configuration structure integrity.
"""

import pytest
import os
import yaml
from pathlib import Path
from fastapi.testclient import TestClient

from server import app


@pytest.fixture
def client():
    return TestClient(app)


class TestDeploymentHealthProbes:
    def test_liveness_probe_healthz(self, client):
        resp = client.get("/healthz")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "healthy"
        assert data["service"] == "testforge-backend"
        assert "timestamp" in data

    def test_readiness_probe_readyz(self, client):
        resp = client.get("/readyz")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ready"
        assert data["subsystems"]["ast_mutator"] == "operational"
        assert data["subsystems"]["blackboard"] == "operational"
        assert data["subsystems"]["sandbox_storage"] == "operational"

    def test_a2a_agent_card_discovery_endpoints(self, client):
        for path in ("/.well-known/agent-card.json", "/.well-known/agent.json"):
            resp = client.get(path)
            assert resp.status_code == 200
            data = resp.json()
            assert "name" in data
            assert data["name"] == "testforge-agent-system"
            proto_ver = data.get("protocolVersion") or data.get("protocol_version")
            assert proto_ver == "0.3.0"

    def test_api_status_endpoint(self, client):
        resp = client.get("/api/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "hardware" in data
        assert "providers" in data
        assert data["hardware"]["cpu_count"] > 0


class TestContainerConfigurationIntegrity:
    def test_dockerfile_present_and_configured(self):
        dockerfile_path = Path("Dockerfile")
        assert dockerfile_path.exists(), "Dockerfile must exist at repository root"
        content = dockerfile_path.read_text(encoding="utf-8")
        assert "FROM python:3.13-slim" in content
        assert "HEALTHCHECK" in content
        assert "/healthz" in content
        assert "EXPOSE 8000" in content
        assert "USER testforge" in content

    def test_docker_compose_valid_structure(self):
        compose_path = Path("docker-compose.yml")
        assert compose_path.exists(), "docker-compose.yml must exist at repository root"
        content = compose_path.read_text(encoding="utf-8")
        parsed = yaml.safe_load(content)
        assert "services" in parsed
        assert "backend" in parsed["services"]
        assert "dashboard" in parsed["services"]
        assert "8000:8000" in parsed["services"]["backend"]["ports"]
        assert "8501:8501" in parsed["services"]["dashboard"]["ports"]
        assert "testforge-net" in parsed["networks"]

    def test_dockerignore_present(self):
        dockerignore_path = Path(".dockerignore")
        assert dockerignore_path.exists()
        content = dockerignore_path.read_text(encoding="utf-8")
        assert ".venv" in content
        assert ".git" in content
        assert "__pycache__" in content


class TestBenchmarkEndpoints:
    def test_get_benchmark_results_initial_or_cached(self, client):
        resp = client.get("/api/benchmark/results")
        assert resp.status_code == 200
        data = resp.json()
        assert "exists" in data

    def test_run_benchmark_sync_baseline(self, client):
        payload = {
            "target_file_path": "samples/discount.py",
            "scenarios": ["baseline"],
            "repetitions": 1,
            "engine_mode": "auto"
        }
        resp = client.post("/api/benchmark/run", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "COMPLETED"
        assert "report" in data
        rep = data["report"]
        assert "scenario_summaries" in rep
        assert "baseline" in rep["scenario_summaries"]
        baseline_summary = rep["scenario_summaries"]["baseline"]
        assert baseline_summary["runs_completed"] == 1
        assert "hardware_summary" in rep
        assert "markdown" in data

    def test_get_benchmark_results_and_markdown(self, client):
        resp = client.get("/api/benchmark/results")
        assert resp.status_code == 200
        data = resp.json()
        assert data["exists"] is True
        assert data["report"] is not None

        md_resp = client.get("/api/benchmark/markdown")
        assert md_resp.status_code == 200
        assert "Benchmark" in md_resp.text

    def test_start_benchmark_async_and_poll_job(self, client):
        payload = {
            "target_file_path": "samples/discount.py",
            "scenarios": ["baseline"],
            "repetitions": 1,
        }
        resp = client.post("/api/benchmark/start", json=payload)
        assert resp.status_code == 200
        data = resp.json()
        job_id = data["job_id"]
        assert data["status"] == "RUNNING"

        # Check job status endpoint
        job_resp = client.get(f"/api/benchmark/job/{job_id}")
        assert job_resp.status_code == 200
        job_data = job_resp.json()
        assert job_data["job_id"] == job_id
        assert job_data["status"] in ("RUNNING", "COMPLETED")

