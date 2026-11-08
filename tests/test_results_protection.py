"""
Tests for F0: Benchmark Results Protection and Dashboard Provenance Badges.
Validates:
1. testforge benchmark writes to qa_artifacts/runs/<timestamp>/ by default.
2. Updating canonical MULTI_TARGET_BENCHMARK_RESULTS.json requires --publish.
3. Publishing is refused if fast_mode is true.
4. Publishing is refused if mock/fixture execution engine is used.
5. Dashboard benchmark view surfaces provenance badges (fast/mock, model, commit, timestamp).
"""

import argparse
import json
import os
import shutil
import tempfile
from pathlib import Path

import pytest
from starlette.testclient import TestClient

from server import app
from testforge.cli import handle_benchmark_command


def test_cli_default_path_writes_to_timestamped_run_folder(monkeypatch, tmp_path):
    """Verifies testforge benchmark writes to qa_artifacts/runs/<timestamp>/ by default."""
    runs_dir = tmp_path / "qa_artifacts" / "runs"
    canonical_json = tmp_path / "qa_artifacts" / "MULTI_TARGET_BENCHMARK_RESULTS.json"

    # Mock os.path and runs directory
    orig_join = os.path.join

    def mock_join(*args):
        if len(args) >= 2 and args[0] == "qa_artifacts" and args[1] == "runs":
            return str(runs_dir / args[2] if len(args) > 2 else runs_dir)
        if len(args) == 2 and args[0] == "qa_artifacts" and args[1] == "MULTI_TARGET_BENCHMARK_RESULTS.json":
            return str(canonical_json)
        return orig_join(*args)

    monkeypatch.setattr(os.path, "join", mock_join)

    args = argparse.Namespace(
        targets="discount",
        output=None,
        publish=False,
        fast=True,
        scenarios="baseline",
        engine_mode="local",
        model="heuristic",
    )

    ret = handle_benchmark_command(args)
    assert ret == 0

    # Ensure canonical file was NOT created or written
    assert not canonical_json.exists()

    # Ensure timestamped run directory WAS created
    assert runs_dir.exists()
    run_subdirs = list(runs_dir.iterdir())
    assert len(run_subdirs) >= 1
    run_file = run_subdirs[0] / "MULTI_TARGET_BENCHMARK_RESULTS.json"
    assert run_file.exists()


def test_publish_refused_on_fast_mode(monkeypatch, tmp_path):
    """Verifies --publish is refused when fast_mode is True."""
    args = argparse.Namespace(
        targets="discount",
        output=str(tmp_path / "out.json"),
        publish=True,
        fast=True,
        scenarios="baseline",
        engine_mode="local",
        model="heuristic",
    )

    ret = handle_benchmark_command(args)
    assert ret == 1, "Publishing must be refused if fast_mode is True"


def test_publish_refused_on_mock_engine(monkeypatch, tmp_path):
    """Verifies --publish is refused when mock/fixture execution engine is used."""
    args = argparse.Namespace(
        targets="discount",
        output=str(tmp_path / "out.json"),
        publish=True,
        fast=False,
        scenarios="baseline",
        engine_mode="mock",
        model="mock-model",
    )

    ret = handle_benchmark_command(args)
    assert ret == 1, "Publishing must be refused if engine_mode is mock"


def test_publish_refused_on_mock_in_model_name(monkeypatch, tmp_path):
    """Verifies --publish is refused if model name indicates fixture/mock."""
    args = argparse.Namespace(
        targets="discount",
        output=str(tmp_path / "out.json"),
        publish=True,
        fast=False,
        scenarios="baseline",
        engine_mode="auto",
        model="fixture-mock-v1",
    )

    ret = handle_benchmark_command(args)
    assert ret == 1, "Publishing must be refused if model name contains mock"


def test_dashboard_provenance_elements_and_api():
    """Verifies that the dashboard HTML includes provenance badge elements and API returns metadata."""
    html_path = Path("frontend/index.html")
    assert html_path.exists()
    html_content = html_path.read_text(encoding="utf-8")

    assert "multi-benchmark-provenance-bar" in html_content
    assert "badge-benchmark-status" in html_content
    assert "badge-benchmark-model" in html_content
    assert "badge-benchmark-commit" in html_content
    assert "badge-benchmark-timestamp" in html_content

    # API verification
    client = TestClient(app)
    resp = client.get("/api/benchmark/multi-target/summary")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "SUCCESS"
    res = data["results"]
    assert "commit" in res
    assert "model_name" in res
    assert "fast_mode" in res
    assert "is_mocked" in res
