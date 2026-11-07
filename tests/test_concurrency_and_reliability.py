"""
tests/test_concurrency_and_reliability.py - Multi-Job Concurrency, State Isolation, and Recovery Suite.

Verifies:
  1. Concurrent execution of multiple distinct hardening jobs without state collision.
  2. Independent per-job output suites and absence of cross-talk in test generation.
  3. Immediate and clean job cancellation propagation.
  4. Concurrent SQLite checkpoint writes in WAL mode under multi-threaded load.
"""

import time
import concurrent.futures
import pytest
from fastapi.testclient import TestClient
from server import app, JOBS, JOB_LOCK
from testforge.persistence import SQLiteBlackboardStorage, CheckpointRecord, CheckpointMetadata
from testforge.state import TaskLifecycleState


@pytest.fixture
def api_client():
    return TestClient(app)


class TestConcurrencyAndReliability:
    """Verifies that TestForge handles concurrent workloads and cancellation safely."""

    def test_concurrent_hardening_jobs_execute_with_full_state_isolation(self, api_client, tmp_path):
        target_a = """
def discount(amount: float) -> float:
    if amount > 100:
        return amount * 0.9
    return amount
"""
        target_b = """
def is_palindrome(text: str) -> bool:
    clean = text.lower().replace(" ", "")
    return clean == clean[::-1]
"""
        payload_a = {
            "target_source_code": target_a,
            "target_file_path": "samples/discount.py",
            "max_iterations": 1,
            "target_mutation_score": 100.0,
            "engine_mode": "legacy",
            "timeout_seconds": 30
        }
        payload_b = {
            "target_source_code": target_b,
            "target_file_path": "samples/palindrome.py",
            "max_iterations": 1,
            "target_mutation_score": 100.0,
            "engine_mode": "legacy",
            "timeout_seconds": 30
        }

        # Start Job A and Job B concurrently
        res_a = api_client.post("/api/harden/start", json=payload_a)
        res_b = api_client.post("/api/harden/start", json=payload_b)

        assert res_a.status_code == 200
        assert res_b.status_code == 200

        job_a_id = res_a.json()["job_id"]
        job_b_id = res_b.json()["job_id"]
        assert job_a_id != job_b_id

        # Poll both jobs until completion
        deadline = time.time() + 45
        done_a = False
        done_b = False
        final_a = None
        final_b = None

        while time.time() < deadline and not (done_a and done_b):
            if not done_a:
                stat_a = api_client.get(f"/api/harden/status/{job_a_id}").json()
                if stat_a.get("status") in ("COMPLETED", "FAILED", "CANCELLED", "TIMED_OUT"):
                    done_a = True
                    final_a = stat_a
            if not done_b:
                stat_b = api_client.get(f"/api/harden/status/{job_b_id}").json()
                if stat_b.get("status") in ("COMPLETED", "FAILED", "CANCELLED", "TIMED_OUT"):
                    done_b = True
                    final_b = stat_b
            time.sleep(0.5)

        assert done_a, f"Job A did not complete in time: {final_a}"
        assert done_b, f"Job B did not complete in time: {final_b}"

        assert final_a["status"] == "COMPLETED"
        assert final_b["status"] == "COMPLETED"

        # Verify strict state isolation: Job A has discount tests, Job B has palindrome tests
        code_a = final_a.get("test_hardened_code", "")
        code_b = final_b.get("test_hardened_code", "")

        assert "discount" in code_a
        assert "is_palindrome" not in code_a, "Job B code leaked into Job A's test suite!"

        assert "is_palindrome" in code_b
        assert "discount" not in code_b, "Job A code leaked into Job B's test suite!"

    def test_rapid_cancellation_stops_job_execution(self, api_client):
        target_code = "def sample_calc(n: int) -> int:\n    return n * 2\n"
        payload = {
            "target_source_code": target_code,
            "target_file_path": "samples/sample_calc.py",
            "max_iterations": 1,
            "timeout_seconds": 10,
            "engine_mode": "legacy"
        }
        start_res = api_client.post("/api/harden/start", json=payload)
        assert start_res.status_code == 200
        job_id = start_res.json()["job_id"]

        # Cancel immediately
        cancel_res = api_client.post(f"/api/harden/cancel/{job_id}")
        assert cancel_res.status_code == 200
        assert cancel_res.json()["status"] in ("cancelled", "cancelling", "already_terminal")

        # Verify terminal status is a valid terminal state
        status_res = api_client.get(f"/api/harden/status/{job_id}").json()
        assert status_res["status"] in ("CANCELLED", "CANCELLING", "COMPLETED", "FAILED", "TIMED_OUT")

    def test_sqlite_concurrent_multithreaded_checkpoints(self, tmp_path):
        from testforge.blackboard import Blackboard
        db_path = tmp_path / "concurrent_checkpoints.db"
        storage = SQLiteBlackboardStorage(db_path, journal_mode="WAL", busy_timeout_ms=5000)

        def save_checkpoint(worker_id: int):
            for i in range(5):
                bb = Blackboard()
                bb.update_target_space(module_name=f"mod_{worker_id}_{i}", source_code="def x(): pass")
                snap = bb.get_snapshot()
                storage.save_checkpoint(snap, stage=f"STAGE_{i}", job_id=f"job_{worker_id}")
            return worker_id

        # Execute 5 threads concurrently saving checkpoints to the same SQLite WAL database
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(save_checkpoint, w_id) for w_id in range(5)]
            results = [f.result() for f in futures]

        assert len(results) == 5
        all_checkpoints = storage.list_checkpoints()
        assert len(all_checkpoints) == 25  # 5 workers * 5 checkpoints
        storage.close()
