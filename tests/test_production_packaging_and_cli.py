"""
test_production_packaging_and_cli.py - Verification suite for Handout Feature F8 & F9:
Production Deployment, Standalone CLI, Containerization, and CI/CD Automation.
"""

import os
import sys
import json
import yaml
import tempfile
import argparse
import xml.etree.ElementTree as ET
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Ensure CrewAI runs in headless test mode
os.environ["CREWAI_TESTING"] = "true"
os.environ["CREWAI_TRACING_ENABLED"] = "false"

from server import app
from testforge.export import generate_junit_xml, generate_sarif_report
from testforge.persistence import SQLiteBlackboardStorage, CheckpointRecord, CheckpointMetadata
from testforge.cli import (
    handle_harden_command,
    handle_benchmark_command,
    handle_export_command,
    export_job_report,
)


def test_server_healthz_and_readyz_probes():
    """Verifies standard Docker/K8s liveness and readiness probe endpoints."""
    client = TestClient(app)

    # 1. Healthz probe
    resp_health = client.get("/healthz")
    assert resp_health.status_code == 200
    data_health = resp_health.json()
    assert data_health["status"] == "healthy"
    assert "version" in data_health
    assert "timestamp" in data_health

    # 2. Readyz probe
    resp_ready = client.get("/readyz")
    assert resp_ready.status_code == 200
    data_ready = resp_ready.json()
    assert data_ready["status"] == "ready"
    assert data_ready["db_accessible"] is True
    assert "subsystems" in data_ready
    assert data_ready["subsystems"].get("ast_mutator") == "operational"
    assert data_ready["subsystems"].get("blackboard") == "operational"


def test_cli_help_and_subparsers(monkeypatch):
    """Verifies that the standalone CLI exposes harden, benchmark, and export subcommands."""
    import subprocess

    # Run `python -m testforge.cli --help`
    res = subprocess.run(
        [sys.executable, "-m", "testforge.cli", "--help"],
        capture_output=True,
        text=True,
    )
    assert res.returncode == 0
    assert "harden" in res.stdout
    assert "benchmark" in res.stdout
    assert "export" in res.stdout


def test_cli_harden_subcommand(tmp_path, monkeypatch):
    """Verifies that `testforge.cli harden` ingests target and exports hardened test suite."""
    from testforge.state import TestForgeState

    out_file = tmp_path / "hardened_discount.py"
    mock_state = TestForgeState(
        task_id="task_harden_001",
        target_module_path="samples/discount.py",
        baseline_line_coverage_pct=100.0,
        baseline_branch_coverage_pct=100.0,
        final_mutation_score=92.5,
        adjusted_mutation_score=95.0,
    )

    def fake_run(self):
        return mock_state

    def fake_export(self, output_path):
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("def test_discount_mock(): assert True\n")

    monkeypatch.setattr("testforge.orchestrator.TestForgeOrchestrator.run", fake_run)
    monkeypatch.setattr("testforge.orchestrator.TestForgeOrchestrator.export_hardened_suite", fake_export)

    args = argparse.Namespace(
        target_path="samples/discount.py",
        target_score=85.0,
        max_iterations=2,
        output_dir=str(tmp_path),
        output=str(out_file),
        model="gemini-3.6-flash",
        engine_mode="auto",
        tests=None,
    )
    ret = handle_harden_command(args)
    assert ret == 0
    assert out_file.exists()
    assert "test_discount_mock" in out_file.read_text(encoding="utf-8")


def test_cli_harden_coverage_metrics_fallback(tmp_path, monkeypatch, capsys):
    """Verifies that `testforge.cli harden` reads coverage from Blackboard and ExecutionSpace when state is 0.0."""
    from testforge.state import TestForgeState
    from testforge.blackboard import Blackboard

    out_file = tmp_path / "hardened_discount_fallback.py"
    bb = Blackboard()
    bb._metrics.statement_coverage = 94.2
    bb._metrics.branch_coverage = 88.0
    bb._metrics.adjusted_mutation_score = 91.5
    bb._execution.line_coverage_pct = 94.2
    bb._execution.branch_coverage = 88.0

    mock_state = TestForgeState(
        task_id="task_harden_002",
        target_module_path="samples/discount.py",
        baseline_line_coverage=0.0,
        baseline_branch_coverage=0.0,
        final_mutation_score=85.0,
        adjusted_mutation_score=None,
    )

    def fake_run(self):
        self.blackboard = bb
        self.state = mock_state
        return mock_state

    def fake_export(self, output_path):
        with open(output_path, "w", encoding="utf-8") as f:
            f.write("def test_discount_mock(): assert True\n")

    monkeypatch.setattr("testforge.orchestrator.TestForgeOrchestrator.run", fake_run)
    monkeypatch.setattr("testforge.orchestrator.TestForgeOrchestrator.export_hardened_suite", fake_export)

    args = argparse.Namespace(
        target_path="samples/discount.py",
        target_score=85.0,
        max_iterations=1,
        output_dir=str(tmp_path),
        output=str(out_file),
        model="gemini-3.6-flash",
        engine_mode="auto",
        tests=None,
    )
    ret = handle_harden_command(args)
    assert ret == 0
    captured = capsys.readouterr()
    assert "Line Cov: 94.2%" in captured.out
    assert "Branch Cov: 88.0%" in captured.out
    assert "Adj: 91.5%" in captured.out


def test_cli_export_subcommand(tmp_path):
    """Verifies that `testforge.cli export` reads SQLite checkpoints directly without web server."""
    from testforge.blackboard import Blackboard
    from testforge.state import MutantRecord

    db_file = tmp_path / "test_checkpoints.db"
    storage = SQLiteBlackboardStorage(str(db_file))

    job_id = "test_job_export_001"
    bb = Blackboard()
    bb._target.target_module_path = "samples/discount.py"
    bb._suite.baseline_tests_executed = 5
    bb._suite.baseline_tests_passed = 5
    bb._suite.baseline_tests_failed = 0
    bb._mutant.mutants = [
        MutantRecord(
            mutant_id="MUT_01",
            mutation_type="AOR",
            line_number=12,
            status="KILLED",
            original_code_snippet="a + b",
            mutated_code_snippet="a - b",
            unified_diff="--- orig\n+++ mut\n- a + b\n+ a - b",
        ),
        MutantRecord(
            mutant_id="MUT_02",
            mutation_type="ROR",
            line_number=18,
            status="SURVIVED",
            original_code_snippet="if x > 0:",
            mutated_code_snippet="if x >= 0:",
            unified_diff="--- original\n+++ mutant\n@@ -18,1 +18,1 @@\n- if x > 0:\n+ if x >= 0:",
        ),
    ]

    storage.save_checkpoint(
        snapshot=bb.get_snapshot(),
        stage="FINALIZED",
        job_id=job_id,
        status="CONVERGED",
        checkpoint_id="cp_test_01",
    )
    storage.close()

    # 1. Export JUnit XML
    junit_out = tmp_path / "report.xml"
    args_junit = argparse.Namespace(
        job_id=job_id,
        format="junit",
        output=str(junit_out),
        db_path=str(db_file),
    )
    ret_junit = handle_export_command(args_junit)
    assert ret_junit == 0
    assert junit_out.exists()
    junit_tree = ET.parse(str(junit_out))
    root = junit_tree.getroot()
    assert root.tag == "testsuites"
    assert int(root.attrib["tests"]) >= 2

    # 2. Export SARIF JSON
    sarif_out = tmp_path / "report.sarif"
    args_sarif = argparse.Namespace(
        job_id=job_id,
        format="sarif",
        output=str(sarif_out),
        db_path=str(db_file),
    )
    ret_sarif = handle_export_command(args_sarif)
    assert ret_sarif == 0
    assert sarif_out.exists()
    with open(sarif_out, "r", encoding="utf-8") as f:
        sarif_data = json.load(f)
    assert sarif_data["version"] == "2.1.0"
    assert len(sarif_data["runs"]) > 0
    assert sarif_data["runs"][0]["tool"]["driver"]["name"] == "TestForge"
    # Surviving mutant MUT_02 should be present
    results = sarif_data["runs"][0]["results"]
    assert any(r["ruleId"] == "MUTATION_SURVIVED" for r in results)


def test_cli_benchmark_subcommand(tmp_path):
    """Verifies that `testforge.cli benchmark` runs the benchmark suite in fast mode."""
    bench_out = tmp_path / "BENCH_RESULTS.json"
    args_bench = argparse.Namespace(
        targets="discount",
        output=str(bench_out),
        fast=True,
        scenarios="baseline",
        engine_mode="local",
        model="heuristic-mock",
    )

    ret = handle_benchmark_command(args_bench)
    assert ret == 0
    assert bench_out.exists()
    with open(bench_out, "r", encoding="utf-8") as f:
        bench_data = json.load(f)
    assert "targets" in bench_data or "summary" in bench_data


def test_container_and_config_manifests_integrity():
    """Verifies Dockerfile, docker-compose.yml, GitHub Actions workflow, and .env.example."""
    # 1. Dockerfile
    dockerfile_path = Path("Dockerfile")
    assert dockerfile_path.exists()
    dockerfile_content = dockerfile_path.read_text(encoding="utf-8")
    assert "FROM python:3.13-slim" in dockerfile_content
    assert "EXPOSE 8000" in dockerfile_content
    assert "HEALTHCHECK" in dockerfile_content
    assert "useradd" in dockerfile_content
    assert "testforge" in dockerfile_content

    # 2. docker-compose.yml
    compose_path = Path("docker-compose.yml")
    assert compose_path.exists()
    with open(compose_path, "r", encoding="utf-8") as f:
        compose_data = yaml.safe_load(f)
    services = compose_data.get("services", {})
    assert "backend" in services or "testforge-backend" in services
    assert "ollama" in services
    backend_service = services.get("backend") or services.get("testforge-backend")
    backend_ports = backend_service.get("ports", [])
    assert any("8000:8000" in p for p in backend_ports)

    # 3. GitHub Actions PR check workflow
    gh_workflow_path = Path(".github/workflows/testforge_pr_check.yml")
    assert gh_workflow_path.exists()
    with open(gh_workflow_path, "r", encoding="utf-8") as f:
        wf_data = yaml.safe_load(f)
    on_trigger = wf_data.get("on") or wf_data.get(True) or {}
    assert "pull_request" in on_trigger
    jobs = wf_data.get("jobs", {})
    assert "testforge-ci" in jobs
    steps = jobs["testforge-ci"].get("steps", [])
    step_names = [s.get("name", "") for s in steps]
    assert any("Checkout" in n for n in step_names)
    assert any("Python" in n for n in step_names)
    assert any("Hardening" in n for n in step_names)

    # 4. .env.example
    env_example_path = Path(".env.example")
    assert env_example_path.exists()
    env_text = env_example_path.read_text(encoding="utf-8")
    assert "GEMINI_API_KEY=" in env_text
    assert "TESTFORGE_CHECKPOINT_DB=" in env_text
    assert "OLLAMA_BASE_URL=" in env_text

    # 5. pyproject.toml
    pyproject_path = Path("pyproject.toml")
    assert pyproject_path.exists()
    pyproject_text = pyproject_path.read_text(encoding="utf-8")
    assert "[project.scripts]" in pyproject_text
    assert 'testforge = "testforge.cli:main"' in pyproject_text
