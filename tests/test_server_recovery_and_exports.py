"""
tests/test_server_recovery_and_exports.py - Tests for GAP-007 (Server Job Recovery & Resumption)
and GAP-010 (CI/CD JUnit XML & SARIF v2.1.0 Report Exports).
"""

import os
import time
import json
import sqlite3
import tempfile
import xml.etree.ElementTree as ET
import pytest
from fastapi.testclient import TestClient

from server import (
    app,
    JOB_LOCK,
    JOBS,
    DEFAULT_CHECKPOINT_DB_PATH,
    recover_interrupted_jobs_on_startup,
    generate_junit_xml,
    generate_sarif_report,
)
from testforge.persistence import SQLiteBlackboardStorage
from testforge.blackboard import Blackboard


class TestServerRecoveryGAP007:
    """Verifies unfinalized job recovery on startup and POST /api/harden/resume/{job_id}."""

    def test_server_startup_marks_unfinalized_jobs_interrupted(self):
        """Startup scan marks jobs left in non-terminal states as INTERRUPTED."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = os.path.join(tmpdir, "test_checkpoints.db")
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE checkpoints (
                    checkpoint_id TEXT PRIMARY KEY,
                    schema_version INTEGER NOT NULL,
                    job_id TEXT,
                    workflow_id TEXT,
                    stage TEXT NOT NULL,
                    revision INTEGER NOT NULL,
                    created_at REAL NOT NULL,
                    status TEXT NOT NULL,
                    metrics_summary_json TEXT NOT NULL,
                    snapshot_json TEXT NOT NULL
                );
            """)

            # 1. Interrupted in-flight job
            cursor.execute("""
                INSERT INTO checkpoints VALUES (
                    'chk_inflight_01', 2, 'job_inflight_100', 'wf_100',
                    'BASELINE_SYNTHESIS', 5, 1700000000.0, 'IN_PROGRESS',
                    '{}', '{"target": {"target_module_path": "samples/discount.py"}}'
                );
            """)

            # 2. Already finalized job
            cursor.execute("""
                INSERT INTO checkpoints VALUES (
                    'chk_completed_02', 2, 'job_completed_200', 'wf_200',
                    'FINALIZED', 10, 1700000005.0, 'SUCCESS',
                    '{}', '{"target": {"target_module_path": "samples/discount.py"}}'
                );
            """)
            conn.commit()
            conn.close()

            # Run recovery hook
            interrupted = recover_interrupted_jobs_on_startup(db_path)
            assert "job_inflight_100" in interrupted
            assert "job_completed_200" not in interrupted

            # Verify database record updated
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            row = conn.cursor().execute("SELECT status FROM checkpoints WHERE checkpoint_id='chk_inflight_01'").fetchone()
            assert row["status"] == "INTERRUPTED"
            conn.close()

            # Verify in-memory state updated
            with JOB_LOCK:
                assert "job_inflight_100" in JOBS
                assert JOBS["job_inflight_100"]["status"] == "INTERRUPTED"
                assert JOBS["job_inflight_100"]["resumable"] is True
                JOBS.pop("job_inflight_100", None)

    def test_resume_job_execution_endpoint_success(self):
        """POST /api/harden/resume/{job_id} successfully reconstitutes pipeline from checkpoint."""
        client = TestClient(app)
        test_job_id = "job_unit_resume_test"

        # Save a valid checkpoint for this job
        bb = Blackboard(checkpoint_db_path=DEFAULT_CHECKPOINT_DB_PATH)
        bb.update_target_space(
            target_source_code="def calc(x): return x * 2\n",
            target_module_path="samples/calc.py"
        )
        bb.record_coverage(
            line_coverage_pct=100.0,
            lines_covered=2,
            lines_total=2,
            branch_coverage=100.0,
            total_branches=0,
            covered_branches=0,
        )

        cp = bb.save_checkpoint(
            stage="BASELINE_VALIDATED",
            job_id=test_job_id,
            workflow_id="wf_resume_unit",
            status="IN_PROGRESS"
        )
        assert cp is not None

        # Execute resume request
        resp = client.post(f"/api/harden/resume/{test_job_id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "RESUMED"
        assert data["job_id"] == test_job_id
        assert data["resumed_stage"] in ("BASELINE_SYNTHESIS", "BASELINE_VALIDATED", "MUTATION_ANALYSIS", "REFLECTION_LOOP")
        assert "poll_url" in data

        # Clean up job record
        with JOB_LOCK:
            JOBS.pop(test_job_id, None)

    def test_resume_non_existent_job_returns_404(self):
        """POST /api/harden/resume/{job_id} returns 404 for unknown job."""
        client = TestClient(app)
        resp = client.post("/api/harden/resume/non_existent_job_xyz_999")
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()


class TestCIExportGAP010:
    """Verifies JUnit XML and SARIF v2.1.0 enterprise CI/CD export endpoints."""

    def test_export_junit_xml_validity(self):
        """GET /api/export/junit/{job_id} produces well-formed, standard JUnit XML."""
        client = TestClient(app)
        jid = "job_junit_test_01"

        mock_job = {
            "job_id": jid,
            "target_file_path": "samples/discount.py",
            "duration": 4.52,
            "final_state": {
                "target_module_path": "samples/discount.py",
                "baseline_run": {
                    "tests_executed": 3,
                    "tests_passed": 2,
                    "tests_failed": 1,
                },
                "test_results": [
                    {"name": "test_discount_zero", "duration": 0.02, "status": "PASSED"},
                    {"name": "test_discount_member", "duration": 0.03, "status": "PASSED"},
                    {"name": "test_discount_negative", "duration": 0.05, "status": "FAILED", "error_message": "AssertionError: 0.0 != -10.0"},
                ],
                "mutants": [
                    {"mutant_id": "MUT_01", "mutation_type": "COMPARISON_REVERSAL", "line_number": 9, "status": "KILLED", "execution_time_ms": 25.0},
                    {"mutant_id": "MUT_02", "mutation_type": "ARITHMETIC_INVERSION", "line_number": 14, "status": "SURVIVED", "diff": "- 0.10\n+ 0.15", "execution_time_ms": 30.0},
                    {"mutant_id": "MUT_03", "mutation_type": "DEAD_CODE", "line_number": 17, "status": "EQUIVALENT", "execution_time_ms": 15.0},
                ]
            }
        }

        with JOB_LOCK:
            JOBS[jid] = mock_job

        try:
            resp = client.get(f"/api/export/junit/{jid}")
            assert resp.status_code == 200
            assert "application/xml" in resp.headers["content-type"]
            assert f'filename="testforge-junit-{jid}.xml"' in resp.headers["content-disposition"]

            # Parse and validate XML
            root = ET.fromstring(resp.content)
            assert root.tag == "testsuites"
            assert int(root.attrib["tests"]) > 0
            assert int(root.attrib["failures"]) >= 1

            suites = root.findall("testsuite")
            assert len(suites) == 2
            suite_names = [s.attrib["name"] for s in suites]
            assert "unit_tests" in suite_names
            assert "mutation_evaluations" in suite_names

            # Verify mutation failure detail
            mut_suite = next(s for s in suites if s.attrib["name"] == "mutation_evaluations")
            tc_failed = mut_suite.find(".//failure")
            assert tc_failed is not None
            assert "MUT_02" in tc_failed.attrib["message"]
        finally:
            with JOB_LOCK:
                JOBS.pop(jid, None)

    def test_export_sarif_schema_validity(self):
        """GET /api/export/sarif/{job_id} generates compliant OASIS SARIF v2.1.0 JSON."""
        client = TestClient(app)
        jid = "job_sarif_test_01"

        mock_job = {
            "job_id": jid,
            "target_file_path": "samples/discount.py",
            "final_state": {
                "target_module_path": "samples/discount.py",
                "mutants": [
                    {
                        "mutant_id": "MUT_05",
                        "mutation_type": "LOGICAL_OPERATOR_REPLACEMENT",
                        "line_number": 12,
                        "status": "SURVIVED",
                        "diff": "--- original\n+++ mutant\n@@ -12 +12 @@\n- if is_member and quantity > 5:\n+ if is_member or quantity > 5:",
                    }
                ],
                "security_space": {
                    "findings": [
                        {
                            "description": "Subprocess network socket call blocked by security guardrails",
                            "line_number": 25,
                            "risk_level": "HIGH",
                            "category": "NETWORK_SOCKET"
                        }
                    ]
                }
            }
        }

        with JOB_LOCK:
            JOBS[jid] = mock_job

        try:
            resp = client.get(f"/api/export/sarif/{jid}")
            assert resp.status_code == 200
            assert "application/sarif+json" in resp.headers["content-type"]
            assert f'filename="testforge-sarif-{jid}.json"' in resp.headers["content-disposition"]

            sarif = resp.json()
            assert sarif["version"] == "2.1.0"
            assert "$schema" in sarif
            assert "runs" in sarif
            assert len(sarif["runs"]) == 1

            run = sarif["runs"][0]
            assert run["tool"]["driver"]["name"] == "TestForge"
            assert len(run["tool"]["driver"]["rules"]) >= 2

            results = run["results"]
            assert len(results) == 2

            mutant_result = next(r for r in results if r["ruleId"] == "MUTATION_SURVIVED")
            assert mutant_result["level"] == "warning"
            assert mutant_result["locations"][0]["physicalLocation"]["region"]["startLine"] == 12
            assert mutant_result["locations"][0]["physicalLocation"]["artifactLocation"]["uri"] == "samples/discount.py"

            sec_result = next(r for r in results if r["ruleId"] == "SECURITY_GUARDRAIL_ALERT")
            assert sec_result["level"] == "error"
            assert sec_result["locations"][0]["physicalLocation"]["region"]["startLine"] == 25
        finally:
            with JOB_LOCK:
                JOBS.pop(jid, None)

    def test_export_non_existent_job_returns_404(self):
        """Export endpoints return 404 for non-existent job."""
        client = TestClient(app)
        resp_xml = client.get("/api/export/junit/non_existent_job_99999")
        assert resp_xml.status_code == 404

        resp_sarif = client.get("/api/export/sarif/non_existent_job_99999")
        assert resp_sarif.status_code == 404
