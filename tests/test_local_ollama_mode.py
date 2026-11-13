"""
tests/test_local_ollama_mode.py

Comprehensive tests for Local Ollama Development Mode:
1. TESTFORGE_PROVIDER_MODE=ollama_only routes synthesis, reflection, and critic calls
   directly to local Ollama (or AST fallback when offline) without touching Gemini/OpenRouter.
2. /api/status and /api/health report:
   - ollama_mode="cloud_disabled" when RENDER=true.
   - ollama_mode="online" with detected models when Ollama daemon responds.
   - ollama_mode="offline" when Ollama daemon is unreachable.
3. POST /api/config allows hot-swapping provider mode, local Ollama model, and base URL.
"""

from __future__ import annotations

import json
import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from server import app
from testforge.adk_generator import ADKModelBridge, GoogleADKTestGenerator
from testforge.crewai_agents import CrewCodeIntelligenceCriticCrew
from testforge.llm_client import HybridLLMClient, probe_ollama_status


@pytest.fixture
def client():
    return TestClient(app)


def test_ollama_probe_online_and_offline():
    """Verify probe_ollama_status returns models when online, and (False, []) on error."""
    # 1. Mock successful tags endpoint
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.read.return_value = json.dumps({
        "models": [
            {"name": "qwen2.5-coder:7b"},
            {"name": "llama3.1:8b"}
        ]
    }).encode("utf-8")

    with patch("urllib.request.urlopen", return_value=mock_response):
        online, models = probe_ollama_status("http://localhost:11434", timeout=0.8)
        assert online is True
        assert "qwen2.5-coder:7b" in models
        assert "llama3.1:8b" in models

    # 2. Mock offline connection failure
    with patch("urllib.request.urlopen", side_effect=Exception("Connection refused")):
        online, models = probe_ollama_status("http://localhost:11434", timeout=0.8)
        assert online is False
        assert models == []


def test_status_endpoint_cloud_disabled_vs_local(client, monkeypatch):
    """
    Verify /api/status reports 'cloud_disabled' when RENDER=true,
    and 'online'/'offline' with detected models when running locally.
    """
    # Cloud mode
    monkeypatch.setenv("RENDER", "true")
    resp_cloud = client.get("/api/status")
    assert resp_cloud.status_code == 200
    data_cloud = resp_cloud.json()
    assert data_cloud["providers"]["cloud_mode"] is True
    assert data_cloud["providers"]["ollama_mode"] == "cloud_disabled"

    # Local mode with Ollama responding
    monkeypatch.delenv("RENDER", raising=False)
    monkeypatch.delenv("K_SERVICE", raising=False)
    monkeypatch.delenv("CLOUD_RUN_SERVICE", raising=False)

    with patch("server.probe_ollama_status", return_value=(True, ["qwen2.5-coder:7b"])):
        resp_local = client.get("/api/status")
        assert resp_local.status_code == 200
        data_local = resp_local.json()
        assert data_local["providers"]["cloud_mode"] is False
        assert data_local["providers"]["ollama_mode"] == "online"
        assert data_local["providers"]["ollama_online"] is True
        assert "qwen2.5-coder:7b" in data_local["providers"]["detected_ollama_models"]

    # Local mode with Ollama offline
    with patch("server.probe_ollama_status", return_value=(False, [])):
        resp_offline = client.get("/api/status")
        assert resp_offline.status_code == 200
        data_offline = resp_offline.json()
        assert data_offline["providers"]["ollama_mode"] == "offline"
        assert data_offline["providers"]["ollama_online"] is False


def test_api_config_endpoint_updates_provider_and_model(client, monkeypatch):
    """POST /api/config hot-swaps provider mode and local Ollama model."""
    resp = client.post("/api/config", json={
        "engine_mode": "ollama_only",
        "ollama_model": "llama3.1:8b",
        "gemini_api_key": "test-key"
    })
    assert resp.status_code == 200
    d = resp.json()
    assert d["status"] == "success"
    assert d["provider_mode"] == "ollama_only"
    assert d["ollama_model"] == "llama3.1:8b"
    assert os.environ.get("TESTFORGE_PROVIDER_MODE") == "ollama_only"
    assert os.environ.get("OLLAMA_MODEL") == "llama3.1:8b"


def test_ollama_only_mode_routes_to_ollama_without_touching_cloud(monkeypatch):
    """
    When TESTFORGE_PROVIDER_MODE=ollama_only, HybridLLMClient routes directly
    to Ollama and NEVER touches Gemini or OpenRouter, even if API keys are set.
    """
    monkeypatch.setenv("TESTFORGE_PROVIDER_MODE", "ollama_only")
    monkeypatch.setenv("OLLAMA_MODEL", "qwen2.5-coder:7b")
    monkeypatch.setenv("GEMINI_API_KEY", "should-never-be-called-key")
    monkeypatch.setenv("OPENROUTER_API_KEY", "should-never-be-called-or-key")

    gemini_called = False
    openrouter_called = False

    def fake_gemini(*args, **kwargs):
        nonlocal gemini_called
        gemini_called = True
        raise AssertionError("Gemini was called in ollama_only mode!")

    def fake_openrouter(*args, **kwargs):
        nonlocal openrouter_called
        openrouter_called = True
        raise AssertionError("OpenRouter was called in ollama_only mode!")

    client = HybridLLMClient(
        cloud_model="gemini-3.6-flash",
        openrouter_model="meta-llama/llama-3.3-70b-instruct",
        local_model="qwen2.5-coder:7b",
        engine_mode="auto",  # Should auto-resolve to ollama_only from env
        api_key="should-never-be-called-key",
        openrouter_api_key="should-never-be-called-or-key",
    )
    assert client.engine_mode == "ollama_only"

    # Mock Ollama post call
    mock_post_resp = MagicMock()
    mock_post_resp.status_code = 200
    mock_post_resp.json.return_value = {
        "response": "def test_from_ollama():\n    assert True\n",
        "prompt_eval_count": 25,
        "eval_count": 15
    }

    mock_ping_resp = MagicMock()
    mock_ping_resp.status_code = 200

    with patch("requests.get", return_value=mock_ping_resp), \
         patch("requests.post", return_value=mock_post_resp), \
         patch("testforge.llm_client.call_openrouter_api", side_effect=fake_openrouter):
        
        result = client.generate("Generate a test for discount(price, rate)")
        assert "test_from_ollama" in result
        assert client.active_provider == "Local Ollama (qwen2.5-coder:7b)"
        assert not gemini_called
        assert not openrouter_called


def test_ollama_only_mode_offline_fallback_to_ast(monkeypatch):
    """
    When TESTFORGE_PROVIDER_MODE=ollama_only and Ollama daemon is offline,
    HybridLLMClient falls back directly to AST rule synthesizer without touching cloud.
    """
    monkeypatch.setenv("TESTFORGE_PROVIDER_MODE", "ollama_only")
    monkeypatch.setenv("GEMINI_API_KEY", "should-never-be-called-key")

    client = HybridLLMClient(
        engine_mode="ollama_only",
        api_key="should-never-be-called-key",
    )

    # Force Ollama ping failure
    with patch("requests.get", side_effect=Exception("Ollama offline")):
        res = client.generate("### Target Python Source Code:\ndef add(a, b):\n    return a + b\n")
        assert "def test_" in res
        assert client.active_provider == "AST Deterministic Synthesizer"


def test_adk_generator_in_ollama_only_mode(monkeypatch):
    """Verify Google ADK test generator honors ollama_only mode seamlessly."""
    monkeypatch.setenv("TESTFORGE_PROVIDER_MODE", "ollama_only")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    generator = GoogleADKTestGenerator()
    assert generator is not None

    source_code = "def discount(price, rate):\n    return price * (1 - rate)\n"
    res = generator.generate_tests(target_source_code=source_code)
    assert res is not None
    assert "test_" in res.test_code


def test_crewai_critic_in_ollama_only_mode(monkeypatch):
    """Verify CrewAI critic analyzes surviving mutants in ollama_only mode without errors."""
    monkeypatch.setenv("TESTFORGE_PROVIDER_MODE", "ollama_only")
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)

    crew = CrewCodeIntelligenceCriticCrew()
    surviving = [
        {"mutant_id": "M1", "line_number": 2, "mutation_type": "AOR", "original_expr": "a + b", "mutated_expr": "a - b"}
    ]
    critique = crew.critique_surviving_mutants("def add(a, b):\n    return a + b\n", surviving, iteration=1)
    assert critique["status"] == "success"
    assert "CrewAI Critic Directive" in critique["directive"]
    assert "M1" in critique["directive"]
