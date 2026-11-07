"""
tests/test_dynamic_model_identification.py - Automated Regression Suite
for Dynamic Model and Provider Identification, Scope-Aware Observability,
and Metadata Normalization.
"""

import json

import pytest
from fastapi.testclient import TestClient

from server import app
from testforge.logger import TraceLogger, determine_scope_execution_engine, resolve_dynamic_execution_engine


@pytest.fixture
def temp_trace_file(tmp_path):
    return str(tmp_path / "test_dynamic_models.jsonl")


class TestDynamicModelIdentification:
    """Verifies dynamic model identification across all supported execution modes."""

    def test_gemini_dynamic_identification(self, temp_trace_file):
        """1. Correct Gemini identification."""
        logger = TraceLogger(temp_trace_file)
        logger.log_llm_event(
            agent_name="TestGeneratorAgent",
            model_name="Cloud Gemini:gemini-3.6-flash",
            prompt="def add(a, b): return a + b",
            response_text="def test_add(): assert add(1, 2) == 3",
            prompt_tokens=100,
            completion_tokens=25,
            total_tokens=125,
            latency_sec=1.1,
            provider_type="Cloud Gemini",
            is_actual_llm=True,
            workflow_id="WF_GEMINI",
            correlation_id="WF_GEMINI",
        )

        summary = logger.get_token_summary(workflow_id="WF_GEMINI")
        assert summary["execution_engine_kpi"] == "Gemini – gemini-3.6-flash"
        assert summary["actual_llm_tokens"] == 125
        assert summary["actual_calls"] == 1
        assert "Gemini – gemini-3.6-flash" in summary["execution_engine_breakdown"]

        lbl, prov, mod = resolve_dynamic_execution_engine("Cloud Gemini:gemini-3.6-flash", "Cloud Gemini", True)
        assert lbl == "Gemini – gemini-3.6-flash"
        assert prov == "Google GenAI"
        assert mod == "gemini-3.6-flash"

    def test_ollama_dynamic_identification(self, temp_trace_file):
        """2. Correct Ollama identification for standard models."""
        logger = TraceLogger(temp_trace_file)
        logger.log_llm_event(
            agent_name="TestGeneratorAgent",
            model_name="Local Ollama:qwen2.5-coder:7b",
            prompt="def multiply(a, b): return a * b",
            response_text="def test_mul(): assert multiply(2, 3) == 6",
            prompt_tokens=80,
            completion_tokens=30,
            total_tokens=110,
            latency_sec=0.45,
            provider_type="Local Ollama",
            is_actual_llm=True,
            workflow_id="WF_OLLAMA",
            correlation_id="WF_OLLAMA",
        )

        summary = logger.get_token_summary(workflow_id="WF_OLLAMA")
        assert summary["execution_engine_kpi"] == "qwen2.5-coder:7b (Ollama / Local)"
        assert summary["actual_llm_tokens"] == 110
        assert summary["actual_calls"] == 1

        lbl, prov, mod = resolve_dynamic_execution_engine("Local Ollama:qwen2.5-coder:7b", "Local Ollama", True)
        assert lbl == "qwen2.5-coder:7b (Ollama / Local)"
        assert prov == "Local Ollama"
        assert mod == "qwen2.5-coder:7b"

    def test_codellama_dynamic_identification(self, temp_trace_file):
        """3. Correct CodeLlama identification."""
        logger = TraceLogger(temp_trace_file)
        logger.log_llm_event(
            agent_name="TestGeneratorAgent",
            model_name="Local Ollama:codellama:7b",
            prompt="def subtract(a, b): return a - b",
            response_text="def test_sub(): assert subtract(5, 2) == 3",
            prompt_tokens=90,
            completion_tokens=35,
            total_tokens=125,
            latency_sec=0.55,
            provider_type="Local Ollama",
            is_actual_llm=True,
            workflow_id="WF_CODELLAMA",
            correlation_id="WF_CODELLAMA",
        )

        summary = logger.get_token_summary(workflow_id="WF_CODELLAMA")
        assert summary["execution_engine_kpi"] == "CodeLlama (Ollama / Local)"
        assert summary["actual_llm_tokens"] == 125
        assert summary["actual_calls"] == 1

        lbl, prov, mod = resolve_dynamic_execution_engine("Local Ollama:codellama:7b", "Local Ollama", True)
        assert lbl == "CodeLlama (Ollama / Local)"
        assert prov == "Local Ollama"
        assert mod == "codellama:7b"

    def test_openrouter_dynamic_identification(self, temp_trace_file):
        """4. Correct OpenRouter identification."""
        logger = TraceLogger(temp_trace_file)
        logger.log_llm_event(
            agent_name="TestGeneratorAgent",
            model_name="OpenRouter:meta-llama/llama-3.3-70b-instruct",
            prompt="def divide(a, b): return a / b",
            response_text="def test_div(): assert divide(6, 2) == 3",
            prompt_tokens=120,
            completion_tokens=40,
            total_tokens=160,
            latency_sec=1.8,
            provider_type="OpenRouter Cloud",
            is_actual_llm=True,
            workflow_id="WF_OPENROUTER",
            correlation_id="WF_OPENROUTER",
        )

        summary = logger.get_token_summary(workflow_id="WF_OPENROUTER")
        assert summary["execution_engine_kpi"] == "meta-llama/llama-3.3-70b-instruct (OpenRouter)"
        assert summary["actual_llm_tokens"] == 160
        assert summary["actual_calls"] == 1

        lbl, prov, mod = resolve_dynamic_execution_engine("OpenRouter:meta-llama/llama-3.3-70b-instruct", "OpenRouter Cloud", True)
        assert lbl == "meta-llama/llama-3.3-70b-instruct (OpenRouter)"
        assert prov == "OpenRouter"
        assert mod == "meta-llama/llama-3.3-70b-instruct"

    def test_deterministic_ast_identification(self, temp_trace_file):
        """5. Correct deterministic AST identification."""
        logger = TraceLogger(temp_trace_file)
        logger.log_llm_event(
            agent_name="TestGeneratorAgent",
            model_name="AST Deterministic Synthesizer",
            prompt="def mod(a, b): return a % b",
            response_text="def test_mod(): assert mod(5, 2) == 1",
            prompt_tokens=150,
            completion_tokens=50,
            total_tokens=200,
            latency_sec=0.001,
            provider_type="Deterministic Synthesizer",
            is_actual_llm=False,
            workflow_id="WF_DET",
            correlation_id="WF_DET",
        )

        summary = logger.get_token_summary(workflow_id="WF_DET")
        assert summary["execution_engine_kpi"] == "Deterministic AST Synthesizer"
        assert summary["actual_llm_tokens"] == 0, "Deterministic runs must yield 0 actual tokens"
        assert summary["estimated_tokens"] == 200
        assert summary["deterministic_calls"] == 1
        assert summary["actual_calls"] == 0

        lbl, prov, mod = resolve_dynamic_execution_engine("AST Deterministic Synthesizer", "Deterministic Synthesizer", False)
        assert lbl == "Deterministic AST Synthesizer"
        assert prov is None
        assert mod is None

    def test_mixed_historical_engine_identification(self, temp_trace_file):
        """6. Correct mixed historical engine identification."""
        logger = TraceLogger(temp_trace_file)

        # Call 1: Gemini
        logger.log_llm_event(
            agent_name="TestGeneratorAgent",
            model_name="Cloud Gemini:gemini-3.6-flash",
            prompt="Prompt 1",
            response_text="Response 1",
            prompt_tokens=500,
            completion_tokens=100,
            total_tokens=600,
            latency_sec=1.0,
            is_actual_llm=True,
            workflow_id="WF_HIST_1",
        )

        # Call 2: Deterministic
        logger.log_llm_event(
            agent_name="TestGeneratorAgent",
            model_name="AST Deterministic Synthesizer",
            prompt="Prompt 2",
            response_text="Response 2",
            prompt_tokens=200,
            completion_tokens=40,
            total_tokens=240,
            latency_sec=0.001,
            is_actual_llm=False,
            workflow_id="WF_HIST_2",
        )

        # In overall scope (all historical records):
        summary = logger.get_token_summary()
        assert summary["execution_engine_kpi"] == "Mixed Execution Engines"
        assert "Gemini – gemini-3.6-flash" in summary["unique_execution_engines"]
        assert "Deterministic AST Synthesizer" in summary["unique_execution_engines"]
        assert summary["execution_engine_breakdown"]["Gemini – gemini-3.6-flash"] == 1
        assert summary["execution_engine_breakdown"]["Deterministic AST Synthesizer"] == 1

    def test_unknown_legacy_metadata_identification(self, temp_trace_file):
        """7. Unknown legacy metadata handling."""
        logger = TraceLogger(temp_trace_file)
        lbl, prov, mod = resolve_dynamic_execution_engine("UnknownModel", "Unknown", True)
        assert lbl == "Unknown / Legacy"
        assert prov == "Unknown / Legacy"
        assert mod == "Unknown / Legacy"

    def test_current_workflow_isolation(self, temp_trace_file):
        """8. Current workflow isolation from previous runs."""
        logger = TraceLogger(temp_trace_file)

        # Prior workflow with Gemini
        logger.log_llm_event(
            agent_name="TestGeneratorAgent",
            model_name="Cloud Gemini:gemini-3.6-flash",
            prompt="Prompt A",
            response_text="Response A",
            prompt_tokens=1000,
            completion_tokens=200,
            total_tokens=1200,
            latency_sec=1.2,
            is_actual_llm=True,
            workflow_id="WF_PRIOR",
        )

        # Current workflow with Deterministic
        logger.log_llm_event(
            agent_name="TestGeneratorAgent",
            model_name="AST Deterministic Synthesizer",
            prompt="Prompt B",
            response_text="Response B",
            prompt_tokens=300,
            completion_tokens=50,
            total_tokens=350,
            latency_sec=0.001,
            is_actual_llm=False,
            workflow_id="WF_CURRENT",
        )

        # Query only current workflow
        summary_curr = logger.get_token_summary(workflow_id="WF_CURRENT")
        assert summary_curr["execution_engine_kpi"] == "Deterministic AST Synthesizer"
        assert summary_curr["actual_llm_tokens"] == 0
        assert summary_curr["estimated_tokens"] == 350
        assert summary_curr["actual_calls"] == 0
        assert summary_curr["deterministic_calls"] == 1

    def test_model_switching_between_successive_workflows(self, temp_trace_file):
        """9. Model switching between successive workflows."""
        logger = TraceLogger(temp_trace_file)

        # WF 1: CodeLlama
        logger.log_llm_event(
            agent_name="TestGeneratorAgent",
            model_name="Local Ollama:codellama:7b",
            prompt="P1", response_text="R1",
            prompt_tokens=100, completion_tokens=20, total_tokens=120, latency_sec=0.5,
            is_actual_llm=True, workflow_id="WF_SWITCH_1"
        )
        # WF 2: Gemini
        logger.log_llm_event(
            agent_name="TestGeneratorAgent",
            model_name="Cloud Gemini:gemini-3.6-flash",
            prompt="P2", response_text="R2",
            prompt_tokens=200, completion_tokens=40, total_tokens=240, latency_sec=1.0,
            is_actual_llm=True, workflow_id="WF_SWITCH_2"
        )
        # WF 3: Deterministic
        logger.log_llm_event(
            agent_name="TestGeneratorAgent",
            model_name="AST Deterministic Synthesizer",
            prompt="P3", response_text="R3",
            prompt_tokens=80, completion_tokens=20, total_tokens=100, latency_sec=0.001,
            is_actual_llm=False, workflow_id="WF_SWITCH_3"
        )

        s1 = logger.get_token_summary(workflow_id="WF_SWITCH_1")
        assert s1["execution_engine_kpi"] == "CodeLlama (Ollama / Local)"

        s2 = logger.get_token_summary(workflow_id="WF_SWITCH_2")
        assert s2["execution_engine_kpi"] == "Gemini – gemini-3.6-flash"

        s3 = logger.get_token_summary(workflow_id="WF_SWITCH_3")
        assert s3["execution_engine_kpi"] == "Deterministic AST Synthesizer"

    def test_no_execution_state(self, temp_trace_file):
        """10. No execution state returns 'No Execution Yet'."""
        logger = TraceLogger(temp_trace_file)
        summary = logger.get_token_summary(workflow_id="WF_FRESH_EMPTY")
        assert summary["execution_engine_kpi"] == "No Execution Yet"
        assert summary["actual_llm_tokens"] == 0
        assert summary["estimated_tokens"] == 0
        assert summary["last_execution_model"] is None

        assert determine_scope_execution_engine([]) == "No Execution Yet"

    def test_actual_token_accounting(self, temp_trace_file):
        """11. Actual token accounting integrity."""
        logger = TraceLogger(temp_trace_file)
        logger.log_llm_event(
            agent_name="TestGeneratorAgent",
            model_name="Cloud Gemini:gemini-3.6-flash",
            prompt="P", response_text="R",
            prompt_tokens=800, completion_tokens=200, total_tokens=1000, latency_sec=1.1,
            is_actual_llm=True, workflow_id="WF_TOK_ACTUAL"
        )
        summary = logger.get_token_summary(workflow_id="WF_TOK_ACTUAL")
        assert summary["actual_llm_tokens"] == 1000
        assert summary["actual_prompt_tokens"] == 800
        assert summary["actual_completion_tokens"] == 200
        assert summary["estimated_tokens"] == 0

    def test_estimated_token_accounting(self, temp_trace_file):
        """12. Estimated token accounting integrity."""
        logger = TraceLogger(temp_trace_file)
        logger.log_llm_event(
            agent_name="TestGeneratorAgent",
            model_name="AST Deterministic Synthesizer",
            prompt="P", response_text="R",
            prompt_tokens=400, completion_tokens=100, total_tokens=500, latency_sec=0.002,
            is_actual_llm=False, workflow_id="WF_TOK_EST"
        )
        summary = logger.get_token_summary(workflow_id="WF_TOK_EST")
        assert summary["actual_llm_tokens"] == 0
        assert summary["estimated_tokens"] == 500
        assert summary["estimated_prompt_tokens"] == 400
        assert summary["estimated_completion_tokens"] == 100

    def test_correct_api_response_structure(self):
        """13. Correct API response structure with four separated concepts."""
        client = TestClient(app)
        res = client.get("/api/telemetry?scope=all")
        assert res.status_code == 200
        data = res.json()

        # 4 Concepts must be clearly separated
        assert "configured_model" in data, "Configured Model must be present"
        assert "active_provider" in data, "Active Provider must be present"
        assert "actual_execution_engine" in data, "Actual Execution Engine KPI must be present"
        assert "last_execution_model" in data, "Last Execution Model must be present"

        # Additional metadata fields
        assert "execution_engine_kpi" in data
        assert "execution_engine_breakdown" in data
        assert "execution_engines_used" in data
        assert isinstance(data["execution_engines_used"], list)
        assert isinstance(data["execution_engine_breakdown"], dict)

        # Invariant checks
        assert data["actual_llm_tokens_used"] == data["total_tokens_used"]
        assert data["combined_tokens_including_estimates"] == data["actual_llm_tokens_used"] + data["estimated_tokens_used"]

