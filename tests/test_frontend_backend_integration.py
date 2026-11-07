"""
tests/test_frontend_backend_integration.py

End-to-End Verification and Frontend-Backend Integration Test Suite
Connecting GAP-001 through GAP-010 to the Cockpit Dashboard UI.
Verifies DOM element bindings, CSS styling rules, export endpoints,
and multi-target benchmark integration without NPM or build tools.
"""

import json
import pathlib
import pytest
from starlette.testclient import TestClient

from server import app, JOBS, JOB_LOCK


BASE_DIR = pathlib.Path(__file__).resolve().parent.parent


class TestFrontendBackendIntegration:
    """Verifies complete end-to-end alignment between frontend cockpit and backend APIs."""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_frontend_index_html_contains_all_gap_ui_elements(self):
        """Verifies frontend/index.html includes all GAP-001 through GAP-010 UI containers and widgets."""
        index_html = (BASE_DIR / "frontend" / "index.html").read_text(encoding="utf-8")

        # GAP-003: Branch Coverage & Missing Branch Arcs dropdown
        assert 'id="kpi-branch-card"' in index_html, "Missing #kpi-branch-card container"
        assert 'id="kpi-branch-pct"' in index_html, "Missing #kpi-branch-pct display"
        assert 'id="kpi-branch-sub"' in index_html, "Missing #kpi-branch-sub arc count"
        assert 'id="kpi-missing-branches-dropdown"' in index_html, "Missing #kpi-missing-branches-dropdown"

        # GAP-005: Calibrated TQS Quality Card & Tooltip
        assert 'id="kpi-tqs-card"' in index_html, "Missing #kpi-tqs-card container"
        assert 'id="kpi-tqs-score"' in index_html, "Missing #kpi-tqs-score display"
        assert 'id="kpi-tqs-sub"' in index_html, "Missing #kpi-tqs-sub badge"
        assert 'id="tqs-breakdown-tooltip"' in index_html, "Missing #tqs-breakdown-tooltip container"

        # GAP-010: Enterprise CI/CD Export Toolbar
        assert 'id="btn-download-junit"' in index_html, "Missing #btn-download-junit button"
        assert 'id="btn-download-sarif"' in index_html, "Missing #btn-download-sarif button"

        # GAP-009: Multi-Target Empirical Benchmark Explorer
        assert 'id="multi-target-benchmark-panel"' in index_html, "Missing #multi-target-benchmark-panel"
        assert 'id="multi-target-benchmark-table"' in index_html, "Missing #multi-target-benchmark-table"
        assert 'id="btn-refresh-multi-benchmark"' in index_html, "Missing #btn-refresh-multi-benchmark"
        assert 'id="btn-run-multi-benchmark"' in index_html, "Missing #btn-run-multi-benchmark"
        assert 'id="multi-target-benchmark-table-body"' in index_html, "Missing #multi-target-benchmark-table-body"
        assert 'id="multi-target-benchmark-table-foot"' in index_html, "Missing #multi-target-benchmark-table-foot"

    def test_frontend_style_css_defines_hud_grid_and_tooltip_styles(self):
        """Verifies frontend/style.css defines essential HUD layout and widget classes."""
        style_css = (BASE_DIR / "frontend" / "style.css").read_text(encoding="utf-8")

        # Responsive HUD Grids
        assert ".kpi-grid-8" in style_css, "Missing .kpi-grid-8 responsive layout"
        assert ".kpi-grid-4" in style_css, "Missing .kpi-grid-4 responsive layout"

        # Interactive Badges & Tooltips
        assert ".kpi-sub" in style_css, "Missing .kpi-sub styling"
        assert ".missing-branches-box" in style_css, "Missing .missing-branches-box styling"
        assert ".tqs-tooltip" in style_css, "Missing .tqs-tooltip styling"
        assert ".tqs-dimension-row" in style_css, "Missing .tqs-dimension-row styling"

        # Interrupted Job Resumption Banner (GAP-007)
        assert ".verdict-banner.interrupted" in style_css, "Missing .verdict-banner.interrupted styling"

    def test_frontend_app_js_implements_dom_bindings_and_event_wiring(self):
        """Verifies frontend/app.js implements reactive bindings for all features."""
        app_js = (BASE_DIR / "frontend" / "app.js").read_text(encoding="utf-8")

        # DOM mappings
        assert "kpiBranchPct" in app_js
        assert "kpiBranchSub" in app_js
        assert "kpiMissingBranchesDropdown" in app_js
        assert "kpiTqsCard" in app_js
        assert "kpiTqsScore" in app_js
        assert "tqsBreakdownTooltip" in app_js
        assert "btnDownloadJunit" in app_js
        assert "btnDownloadSarif" in app_js
        assert "btnRunMultiBenchmark" in app_js
        assert "multiTargetBenchmarkTableBody" in app_js

        # GAP-007: Interrupted Job State Resumption
        assert "job.status === 'INTERRUPTED'" in app_js
        assert "/api/harden/resume/" in app_js
        assert "btn-resume-interrupted-job" in app_js

        # GAP-010: Export Toolbar Handlers
        assert "/api/export/junit/" in app_js
        assert "/api/export/sarif/" in app_js

        # GAP-009: Multi-Target Benchmark Suite Callers
        assert "loadMultiTargetBenchmark" in app_js
        assert "renderMultiTargetBenchmark" in app_js
        assert "/api/benchmark/multi-target/summary" in app_js
        assert "/api/benchmark/multi-target/run" in app_js

    def test_junit_xml_export_endpoint(self, client):
        """Verifies GET /api/export/junit/{job_id} generates valid JUnit XML with test and mutant cases."""
        test_job_id = "test_int_junit_001"
        with JOB_LOCK:
            JOBS[test_job_id] = {
                "job_id": test_job_id,
                "status": "COMPLETED",
                "duration": 4.5,
                "final_state": {
                    "baseline_run": {"tests_executed": 3, "tests_passed": 3, "tests_failed": 0},
                    "test_suite": ["def test_nominal(): pass", "def test_boundary(): pass"],
                    "mutants": [
                        {"mutant_id": "mut_1", "operator": "ARITH_OP", "status": "KILLED", "line_number": 12},
                        {"mutant_id": "mut_2", "operator": "COND_INV", "status": "SURVIVED", "line_number": 15},
                    ]
                }
            }

        res = client.get(f"/api/export/junit/{test_job_id}")
        assert res.status_code == 200
        assert "application/xml" in res.headers["content-type"]
        xml_text = res.text
        assert "<?xml version=" in xml_text
        assert f'<testsuites name="TestForge Hardening - {test_job_id}"' in xml_text
        assert '<testsuite name="unit_tests"' in xml_text
        assert '<testsuite name="mutation_evaluations"' in xml_text
        assert 'name="mut_1_line_12"' in xml_text
        assert '<failure message="Mutant mut_2 survived at line 15 without being detected."' in xml_text

    def test_sarif_v210_export_endpoint(self, client):
        """Verifies GET /api/export/sarif/{job_id} produces standard OASIS SARIF v2.1.0 JSON."""
        test_job_id = "test_int_sarif_001"
        with JOB_LOCK:
            JOBS[test_job_id] = {
                "job_id": test_job_id,
                "status": "COMPLETED",
                "final_state": {
                    "target_module_path": "samples/discount.py",
                    "mutants": [
                        {"mutant_id": "mut_vuln_1", "operator": "COND_INV", "status": "SURVIVED", "line_number": 10, "diff": "- if x > 0:\n+ if x <= 0:"}
                    ]
                }
            }

        res = client.get(f"/api/export/sarif/{test_job_id}")
        assert res.status_code == 200
        assert "application/sarif+json" in res.headers["content-type"]
        sarif = res.json()
        assert sarif["version"] == "2.1.0"
        assert "$schema" in sarif
        assert len(sarif["runs"]) == 1
        run = sarif["runs"][0]
        assert run["tool"]["driver"]["name"] == "TestForge"
        assert len(run["results"]) == 1
        result = run["results"][0]
        assert result["ruleId"] == "MUTATION_SURVIVED"
        assert result["locations"][0]["physicalLocation"]["artifactLocation"]["uri"] == "samples/discount.py"

    def test_multi_target_benchmark_summary_endpoint(self, client):
        """Verifies GET /api/benchmark/multi-target/summary returns aggregated cross-target metrics."""
        res = client.get("/api/benchmark/multi-target/summary")
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "SUCCESS"
        assert "results" in data
        results = data["results"]
        assert "targets" in results
        assert "cross_target_summary" in results
        assert len(results["targets"]) >= 2
        for mod, tdata in results["targets"].items():
            assert "module_name" in tdata
            assert "loc" in tdata
            assert "discovered_callables" in tdata
            assert "scenarios" in tdata
