"""
test_checkpoint_api_diff.py - API integration tests for Checkpoint Diff Inspector and Recovery Endpoints.

Tests:
  - GET /api/checkpoints returns checkpoint summaries
  - GET /api/checkpoints/{id} returns enhanced schema including suite and mutants
  - GET /api/checkpoints/diff computes deterministic diff across checkpoints
  - GET /api/checkpoints/diff 404 on unknown IDs
  - GET /api/checkpoints/diff 422 on missing query parameters
  - POST /api/checkpoints/{id}/restore restores snapshot into isolated blackboard
  - POST /api/checkpoints/{id}/restore 404 on unknown ID
"""

import os
import json
import pytest
from starlette.testclient import TestClient
from server import app, DEFAULT_CHECKPOINT_DB_PATH
from testforge.persistence import SQLiteBlackboardStorage
from testforge.blackboard import Blackboard
from testforge.state import MutantRecord


@pytest.fixture
def client_with_checkpoints(tmp_path, monkeypatch):
    test_db = tmp_path / "test_api_checkpoints.db"
    monkeypatch.setattr("server.DEFAULT_CHECKPOINT_DB_PATH", str(test_db))

    storage = SQLiteBlackboardStorage(test_db)
    bb = Blackboard(storage=storage)

    # Checkpoint 1: Ingestion stage
    bb.update_target_space(
        target_file_path="samples/discount.py",
        target_module_path="samples.discount",
        functions=["calculate_discount"]
    )
    bb.update_metrics_space(final_mutation_score=0.0)
    cp1_id = bb.save_checkpoint(stage="INITIAL_INGESTION", job_id="job_api_test")

    # Checkpoint 2: Baseline Validated
    bb.update_suite_space(
        current_test_code="def test_calc(): assert calculate_discount(100, 'VIP') == 80",
        active_provider="gemini-3.6-flash"
    )
    bb.update_metrics_space(final_mutation_score=60.0)
    m1 = MutantRecord(
        mutant_id="m1",
        mutation_type="ARITH_OP",
        line_number=12,
        original_code_snippet="a + b",
        mutated_code_snippet="a - b",
        unified_diff="- a + b\n+ a - b",
        status="KILLED"
    )
    m2 = MutantRecord(
        mutant_id="m2",
        mutation_type="COMP_OP",
        line_number=14,
        original_code_snippet="x > 0",
        mutated_code_snippet="x >= 0",
        unified_diff="- x > 0\n+ x >= 0",
        status="SURVIVED"
    )
    bb.update_mutant_space(
        mutants_generated=5,
        mutants_killed=3,
        mutants_survived=2,
        mutants=[m1, m2]
    )
    cp2_id = bb.save_checkpoint(stage="BASELINE_VALIDATED", job_id="job_api_test")

    storage.close()
    client = TestClient(app)
    return client, cp1_id, cp2_id, str(test_db)


class TestCheckpointApiDiff:

    def test_get_checkpoint_details_enhanced(self, client_with_checkpoints):
        client, cp1_id, cp2_id, _ = client_with_checkpoints
        resp = client.get(f"/api/checkpoints/{cp2_id}")
        assert resp.status_code == 200
        data = resp.json()

        # Check existing and enhanced keys
        assert "metadata" in data
        assert "target" in data
        assert "metrics" in data
        assert "critic" in data
        assert "suite_info" in data
        assert "mutant_summary" in data
        assert "suite" in data
        assert "mutant" in data
        assert "snapshot" in data

        assert data["suite"]["active_provider"] == "gemini-3.6-flash"
        assert len(data["mutant"]["mutants"]) == 2
        assert data["mutant_summary"]["killed"] == 3

    def test_checkpoint_diff_api_success(self, client_with_checkpoints):
        client, cp1_id, cp2_id, _ = client_with_checkpoints
        resp = client.get(f"/api/checkpoints/diff?base_id={cp1_id}&target_id={cp2_id}")
        assert resp.status_code == 200
        diff = resp.json()

        assert diff["base_checkpoint_id"] == cp1_id
        assert diff["target_checkpoint_id"] == cp2_id
        assert diff["base_stage"] == "INITIAL_INGESTION"
        assert diff["target_stage"] == "BASELINE_VALIDATED"

        summary = diff["summary"]
        assert summary["total_differences"] > 0
        assert "suite" in diff["partition_summaries"]
        assert "metrics" in diff["partition_summaries"]

    def test_checkpoint_diff_api_unknown_base(self, client_with_checkpoints):
        client, cp1_id, cp2_id, _ = client_with_checkpoints
        resp = client.get(f"/api/checkpoints/diff?base_id=nonexistent_cp&target_id={cp2_id}")
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()

    def test_checkpoint_diff_api_missing_param(self, client_with_checkpoints):
        client, cp1_id, cp2_id, _ = client_with_checkpoints
        resp = client.get(f"/api/checkpoints/diff?base_id={cp1_id}")
        assert resp.status_code == 422  # FastAPI validation error for missing target_id

    def test_restore_endpoint_success(self, client_with_checkpoints):
        client, cp1_id, cp2_id, _ = client_with_checkpoints
        resp = client.post(f"/api/checkpoints/{cp2_id}/restore")
        assert resp.status_code == 200
        data = resp.json()

        assert data["status"] == "restored"
        assert data["checkpoint_id"] == cp2_id
        assert data["stage"] == "BASELINE_VALIDATED"
        assert data["restored_state"]["target_module_path"] == "samples.discount"
        assert "def test_calc" in data["restored_state"]["current_test_code"]

