"""
tests/test_token_observability_audit.py - Regression and Verification Suite
for LLM Token Observability, Metrics Accounting, Deterministic vs LLM Isolation,
and Historical vs Current Run Aggregation.
"""

import json
import os

import pytest

from testforge.logger import TraceLogger


@pytest.fixture
def temp_trace_file(tmp_path):
    trace_path = tmp_path / "test_trace.jsonl"
    return str(trace_path)


class TestTokenObservabilityAccounting:
    """Validates rigorous token accounting, distinguishing real LLM from deterministic synthesis."""

    def test_deterministic_execution_produces_zero_actual_llm_tokens(self, temp_trace_file):
        """Deterministic execution must produce 0 actual LLM tokens, with heuristics categorized as estimated."""
        logger = TraceLogger(temp_trace_file)

        # Log a deterministic AST synthesizer event
        prompt = "def calculate_discount(price, rate): return price * rate"
        code = "def test_discount(): assert calculate_discount(100, 0.1) == 10"
        est_p = len(prompt) // 4
        est_c = len(code) // 4

        logger.log_llm_event(
            agent_name="TestGeneratorAgent",
            model_name="AST Deterministic Synthesizer",
            prompt=prompt,
            response_text=code,
            prompt_tokens=est_p,
            completion_tokens=est_c,
            total_tokens=est_p + est_c,
            latency_sec=0.002,
            iteration=1,
            is_valid_ast=True,
            provider_type="Deterministic Synthesizer",
            is_actual_llm=False,
            token_accounting_source="offline_heuristic_estimate",
        )

        summary = logger.get_token_summary()
        assert summary["actual_llm_tokens"] == 0, "Deterministic synthesis must never count towards actual LLM tokens"
        assert summary["actual_prompt_tokens"] == 0
        assert summary["actual_completion_tokens"] == 0
        assert summary["actual_calls"] == 0
        assert summary["deterministic_calls"] == 1
        assert summary["estimated_tokens"] == est_p + est_c
        assert summary["estimated_prompt_tokens"] == est_p
        assert summary["estimated_completion_tokens"] == est_c

        # get_total_tokens by default returns actual LLM tokens
        assert logger.get_total_tokens(actual_only=True) == 0
        assert logger.get_total_tokens(actual_only=False) == est_p + est_c

    def test_actual_llm_execution_records_provider_reported_tokens(self, temp_trace_file):
        """Actual LLM execution must record provider-reported prompt, completion, and total tokens."""
        logger = TraceLogger(temp_trace_file)

        logger.log_llm_event(
            agent_name="TestGeneratorAgent",
            model_name="Cloud Gemini:gemini-3.6-flash",
            prompt="Generate robust edge test cases for logistics dispatch",
            response_text="def test_logistics(): pass",
            prompt_tokens=1420,
            completion_tokens=380,
            total_tokens=1800,
            latency_sec=1.45,
            iteration=1,
            is_valid_ast=True,
            provider_type="Cloud Gemini",
            is_actual_llm=True,
            token_accounting_source="provider_reported",
        )

        summary = logger.get_token_summary()
        assert summary["actual_llm_tokens"] == 1800
        assert summary["actual_prompt_tokens"] == 1420
        assert summary["actual_completion_tokens"] == 380
        assert summary["actual_calls"] == 1
        assert summary["deterministic_calls"] == 0
        assert summary["estimated_tokens"] == 0
        assert logger.get_total_tokens(actual_only=True) == 1800

    def test_historical_vs_current_run_isolation(self, temp_trace_file):
        """Aggregator must isolate records by workflow/correlation ID and not mix historical with current runs."""
        logger = TraceLogger(temp_trace_file)

        # Historical Run 1 (WF_001)
        logger.log_llm_event(
            agent_name="TestGeneratorAgent",
            model_name="Cloud Gemini:gemini-3.6-flash",
            prompt="Prompt 1",
            response_text="Response 1",
            prompt_tokens=1000,
            completion_tokens=200,
            total_tokens=1200,
            latency_sec=1.1,
            workflow_id="WF_001",
            correlation_id="WF_001",
            is_actual_llm=True,
        )

        # Historical Run 2 (WF_002) - Deterministic
        logger.log_llm_event(
            agent_name="TestGeneratorAgent",
            model_name="AST Deterministic Synthesizer",
            prompt="Prompt 2",
            response_text="Response 2",
            prompt_tokens=300,
            completion_tokens=50,
            total_tokens=350,
            latency_sec=0.001,
            workflow_id="WF_002",
            correlation_id="WF_002",
            is_actual_llm=False,
        )

        # Current Active Run (WF_003)
        logger.log_llm_event(
            agent_name="TestGeneratorAgent",
            model_name="Cloud Gemini:gemini-3.6-flash",
            prompt="Prompt 3",
            response_text="Response 3",
            prompt_tokens=500,
            completion_tokens=150,
            total_tokens=650,
            latency_sec=0.8,
            workflow_id="WF_003",
            correlation_id="WF_003",
            is_actual_llm=True,
        )

        # Test full history aggregate
        all_summary = logger.get_token_summary()
        assert all_summary["actual_llm_tokens"] == 1850  # 1200 + 650
        assert all_summary["estimated_tokens"] == 350
        assert all_summary["actual_calls"] == 2
        assert all_summary["deterministic_calls"] == 1

        # Test isolated current run (WF_003)
        current_summary = logger.get_token_summary(workflow_id="WF_003")
        assert current_summary["actual_llm_tokens"] == 650
        assert current_summary["estimated_tokens"] == 0
        assert current_summary["actual_calls"] == 1
        assert current_summary["deterministic_calls"] == 0
        assert current_summary["is_isolated_run"] is True

        # Test isolated deterministic run (WF_002)
        det_summary = logger.get_token_summary(workflow_id="WF_002")
        assert det_summary["actual_llm_tokens"] == 0
        assert det_summary["estimated_tokens"] == 350
        assert det_summary["actual_calls"] == 0
        assert det_summary["deterministic_calls"] == 1

    def test_aggregate_values_strictly_match_individual_records(self, temp_trace_file):
        """Individual record token sums must match the aggregated total with zero drift."""
        logger = TraceLogger(temp_trace_file)

        calls_data = [
            ("Cloud Gemini:gemini-3.6-flash", 100, 50, True),
            ("AST Deterministic Synthesizer", 200, 40, False),
            ("Cloud Gemini:gemini-3.6-flash", 300, 80, True),
            ("AST Deterministic Synthesizer", 150, 30, False),
            ("OpenRouter:anthropic/claude", 450, 110, True),
        ]

        expected_actual = 0
        expected_estimated = 0

        for model, p, c, is_actual in calls_data:
            tot = p + c
            if is_actual:
                expected_actual += tot
            else:
                expected_estimated += tot

            logger.log_llm_event(
                agent_name="TestGeneratorAgent",
                model_name=model,
                prompt="prompt",
                response_text="code",
                prompt_tokens=p,
                completion_tokens=c,
                total_tokens=tot,
                latency_sec=0.5 if is_actual else 0.001,
                is_actual_llm=is_actual,
                token_accounting_source="provider_reported" if is_actual else "offline_heuristic_estimate",
            )

        traces = logger.read_traces()
        summary = logger.get_token_summary(traces=traces)

        # Verify sum from traces directly
        calculated_actual = sum(
            t["data"]["tokens"]["total_tokens"]
            for t in traces
            if t["data"]["is_actual_llm"]
        )
        calculated_estimated = sum(
            t["data"]["tokens"]["estimated_total_tokens"]
            for t in traces
            if not t["data"]["is_actual_llm"]
        )

        assert summary["actual_llm_tokens"] == expected_actual == calculated_actual
        assert summary["estimated_tokens"] == expected_estimated == calculated_estimated
        assert summary["total_tokens"] == expected_actual + expected_estimated

    def test_legacy_trace_records_are_safely_inferred_without_corruption(self, temp_trace_file):
        """Legacy JSONL records without is_actual_llm fields are correctly classified."""
        # Write legacy record without is_actual_llm
        legacy_records = [
            {
                "timestamp": 100.0,
                "iso_time": "2026-11-01 10:00:00",
                "event_type": "LLM_INFERENCE_TELEMETRY",
                "workflow_id": None,
                "correlation_id": None,
                "data": {
                    "agent": "TestGeneratorAgent",
                    "model": "AST Deterministic Synthesizer",
                    "provider_type": "Unknown",
                    "iteration": 0,
                    "tokens": {"prompt_tokens": 500, "completion_tokens": 50, "total_tokens": 550},
                    "latency_seconds": 0.0,
                    "is_valid_ast": True,
                },
                "metadata": {},
            },
            {
                "timestamp": 101.0,
                "iso_time": "2026-11-01 10:01:00",
                "event_type": "LLM_INFERENCE_TELEMETRY",
                "workflow_id": None,
                "correlation_id": None,
                "data": {
                    "agent": "TestGeneratorAgent",
                    "model": "Cloud Gemini:gemini-3.6-flash",
                    "provider_type": "Cloud Gemini",
                    "iteration": 1,
                    "tokens": {"prompt_tokens": 1200, "completion_tokens": 300, "total_tokens": 1500},
                    "latency_seconds": 1.2,
                    "is_valid_ast": True,
                },
                "metadata": {},
            },
        ]

        with open(temp_trace_file, "w", encoding="utf-8") as f:
            for r in legacy_records:
                f.write(json.dumps(r) + "\n")

        logger = TraceLogger(temp_trace_file)
        summary = logger.get_token_summary()

        assert summary["actual_llm_tokens"] == 1500, "Legacy Gemini record must be classified as actual"
        assert summary["estimated_tokens"] == 550, "Legacy AST record must be classified as estimated"
        assert summary["actual_calls"] == 1
        assert summary["deterministic_calls"] == 1


class TestTelemetryEndpointAudit:
    """Validates the /api/telemetry API contracts, field schemas, and deterministic labeling."""

    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient

        from server import app
        return TestClient(app)

    def test_telemetry_endpoint_contract_and_distinction(self, client):
        """Verifies /api/telemetry returns distinct actual LLM tokens and offline estimates."""
        res = client.get("/api/telemetry?limit=10")
        assert res.status_code == 200
        data = res.json()

        # Schema keys required
        assert "actual_llm_tokens_used" in data
        assert "estimated_tokens_used" in data
        assert "total_tokens_used" in data
        assert "combined_tokens_including_estimates" in data
        assert "total_actual_llm_calls" in data
        assert "total_deterministic_calls" in data
        assert "recent_llm_calls" in data

        # Crucial invariant: total_tokens_used MUST equal actual_llm_tokens_used, never inflated with estimates
        assert data["total_tokens_used"] == data["actual_llm_tokens_used"]
        assert data["combined_tokens_including_estimates"] == data["actual_llm_tokens_used"] + data["estimated_tokens_used"]

        # Check call normalization
        for call in data["recent_llm_calls"]:
            d = call.get("data", {})
            assert "is_actual_llm" in d
            assert "token_accounting_source" in d
            assert "actual_total_tokens" in d
            assert "estimated_total_tokens" in d
            assert "execution_engine" in d
            assert "ast_valid" in d

            if not d["is_actual_llm"]:
                assert d["actual_total_tokens"] == 0, "Deterministic runs must report 0 actual tokens"
                assert "Deterministic" in d["execution_engine"] or "AST" in d["execution_engine"]

    def test_telemetry_scope_parameter(self, client):
        """Verifies scope parameter supports 'all' and 'current' run isolation."""
        res_all = client.get("/api/telemetry?scope=all")
        assert res_all.status_code == 200
        data_all = res_all.json()
        assert data_all["scope"] == "all"

        res_curr = client.get("/api/telemetry?scope=current")
        assert res_curr.status_code == 200
        data_curr = res_curr.json()
        assert data_curr["scope"] == "current"

