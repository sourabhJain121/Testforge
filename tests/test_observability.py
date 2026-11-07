"""
tests/test_observability.py

Unit and API tests for OpenTelemetry (OTel) Observability and Supervisor Decision Logging (Sub-Task 3.4):
- OpenTelemetry span collection and semantic attribute validation.
- Per-job trace correlation and duration tracking.
- Supervisor orchestration decision logging.
- FastAPI endpoints /api/observability/traces and /api/observability/supervisor-decisions.
"""

import json
import os

import pytest
from starlette.testclient import TestClient

from server import app
from testforge.observability import TestForgeOtelTracer


class TestOpenTelemetryTracer:
    def setup_method(self):
        TestForgeOtelTracer.get_instance().clear()

    def test_job_and_agent_span_recording(self):
        tracer = TestForgeOtelTracer.get_instance()
        job_id = "job_unit_trace_01"

        # 1. Create root job trace
        job_trace = tracer.create_job_trace(
            job_id=job_id,
            target_path="samples/discount.py",
            iterations=2,
            mutation_score=85.0,
            tokens_consumed=2000,
            cost_usd=0.0002,
            duration_ms=1500.0,
        )
        assert job_trace["job_id"] == job_id
        assert len(job_trace["trace_id"]) == 32

        # 2. Record agent turn span
        tracer.record_agent_span(
            job_id=job_id,
            agent_name="GoogleADKTestGenerator",
            iteration=1,
            duration_ms=500.0,
            tokens_consumed=1200,
            cost_usd=0.0001,
            status="OK",
            metadata={"generated_tests": 4},
        )

        # 3. Verify collected spans
        spans = tracer.get_traces_summary(job_id=job_id)
        assert len(spans) == 2
        root = next(s for s in spans if "job" in s["name"])
        agent = next(s for s in spans if "agent" in s["name"])

        assert root["attributes"]["testforge.job_id"] == job_id
        assert root["attributes"]["testforge.mutation_score"] == 85.0
        assert agent["attributes"]["testforge.agent_name"] == "GoogleADKTestGenerator"
        assert agent["attributes"]["testforge.meta.generated_tests"] == 4

    def test_supervisor_decision_logging(self):
        tracer = TestForgeOtelTracer.get_instance()
        job_id = "job_decision_check"

        dec = tracer.record_supervisor_decision(
            job_id=job_id,
            iteration=1,
            supervisor_agent="SupervisorAgent",
            target_agent="MutationQualityCriticAgent",
            decision_type="DISPATCH_CRITIC",
            reasoning="Surviving mutants detected on iteration 1",
            metrics_snapshot={"survivors": 3},
        )
        assert dec.decision_type == "DISPATCH_CRITIC"
        assert dec.job_id == job_id

        decisions = tracer.get_supervisor_decisions(job_id=job_id)
        assert len(decisions) == 1
        assert decisions[0]["target_agent"] == "MutationQualityCriticAgent"

    def test_export_evidence_to_disk(self, tmp_path):
        tracer = TestForgeOtelTracer.get_instance()
        out_file = tmp_path / "traces.json"

        tracer.create_job_trace("job_exp", "samples/discount.py")
        tracer.record_supervisor_decision("job_exp", 1, "Sup", "Gen", "HALT", "Converged")

        evidence = tracer.export_evidence(str(out_file))
        assert os.path.exists(out_file)
        assert evidence["total_spans_collected"] >= 1
        assert evidence["total_supervisor_decisions"] >= 1


class TestObservabilityAPI:
    def setup_method(self):
        TestForgeOtelTracer.get_instance().clear()

    def test_api_traces_and_decisions_endpoints(self):
        tracer = TestForgeOtelTracer.get_instance()
        job_id = "job_api_otel_99"

        tracer.create_job_trace(job_id, "samples/discount.py")
        tracer.record_supervisor_decision(job_id, 1, "SupervisorAgent", "Critic", "DISPATCH", "Low score")

        client = TestClient(app)

        # 1. GET /api/observability/traces
        res_traces = client.get("/api/observability/traces")
        assert res_traces.status_code == 200
        data_traces = res_traces.json()
        assert data_traces["total_spans"] >= 1
        assert any(s["attributes"].get("testforge.job_id") == job_id for s in data_traces["spans"])

        # 2. GET /api/observability/supervisor-decisions
        res_dec = client.get("/api/observability/supervisor-decisions")
        assert res_dec.status_code == 200
        data_dec = res_dec.json()
        assert data_dec["total_decisions"] >= 1
        assert data_dec["decisions"][0]["job_id"] == job_id
