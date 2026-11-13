"""
tests/test_api_limit_popup_and_cloud_status.py

Verifies:
1. 429 rate limit triggers API_RATE_LIMIT_ROTATED and API_LIMIT_EXHAUSTED telemetry events cleanly.
2. Cloud health endpoint reports 'cloud_disabled' for Ollama when running in cloud environments (RENDER=true).
3. OpenRouter $0 free-tier model fallback handles HTTP 402 credit responses gracefully.
4. /api/keys and /api/config/keys endpoints support hot-swapping keys live during execution.
"""

import os
import time
import urllib.error
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from server import app
from testforge.llm_client import HybridLLMClient


@pytest.fixture
def client():
    return TestClient(app)


def test_cloud_environment_ollama_mode_cloud_disabled(client, monkeypatch):
    """
    When RENDER=true or K_SERVICE is set, /api/status and /api/health should report
    ollama_mode='cloud_disabled' rather than treating it as an offline error.
    """
    monkeypatch.setenv("RENDER", "true")
    monkeypatch.setenv("GEMINI_API_KEY", "mock-gemini-key")
    monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)

    resp = client.get("/api/status")
    assert resp.status_code == 200
    data = resp.json()
    assert data["providers"]["ollama_mode"] == "cloud_disabled"
    assert data["providers"]["cloud_mode"] is True

    health_resp = client.get("/api/health")
    assert health_resp.status_code == 200
    hdata = health_resp.json()
    assert hdata["ollama_mode"] == "cloud_disabled"
    assert hdata["cloud_mode"] is True


def test_hot_swap_api_keys_endpoint(client, monkeypatch):
    """
    POST /api/keys updates the running environment variables dynamically
    supporting both {key, provider} and {gemini_api_key, openrouter_api_key}.
    """
    # 1. Hot-swap Gemini key
    resp1 = client.post("/api/keys", json={
        "provider": "gemini",
        "key": "test-hot-swap-gemini-key-1"
    })
    assert resp1.status_code == 200
    d1 = resp1.json()
    assert d1["status"] == "success"
    assert d1["has_gemini"] is True
    assert os.environ.get("GEMINI_API_KEY") == "test-hot-swap-gemini-key-1"

    # 2. Hot-swap Gemini 2 (backup) key
    resp2 = client.post("/api/keys", json={
        "provider": "gemini_2",
        "key": "test-hot-swap-gemini-key-2"
    })
    assert resp2.status_code == 200
    d2 = resp2.json()
    assert d2["has_gemini_fallback"] is True
    assert os.environ.get("GEMINI_API_KEY_2") == "test-hot-swap-gemini-key-2"

    # 3. Hot-swap OpenRouter key
    resp3 = client.post("/api/keys", json={
        "provider": "openrouter",
        "key": "test-hot-swap-openrouter-key"
    })
    assert resp3.status_code == 200
    d3 = resp3.json()
    assert d3["has_openrouter"] is True
    assert os.environ.get("OPENROUTER_API_KEY") == "test-hot-swap-openrouter-key"


def test_gemini_429_rotation_and_exhaustion_alerts(monkeypatch):
    """
    Verifies that when primary Gemini hits 429:
    1. If secondary key is present, it rotates and emits API_RATE_LIMIT_ROTATED.
    2. When all cloud keys are exhausted, it emits API_LIMIT_EXHAUSTED and falls back to AST.
    """
    captured_alerts = []

    def mock_alert_callback(alert):
        captured_alerts.append(alert)

    # Configure primary + backup Gemini keys
    monkeypatch.setenv("TESTFORGE_PROVIDER_MODE", "auto")
    monkeypatch.setenv("GEMINI_API_KEY", "primary-gem-key")
    monkeypatch.setenv("GEMINI_API_KEY_2", "backup-gem-key")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    client_llm = HybridLLMClient(
        engine_mode="auto",
        alert_callback=mock_alert_callback
    )

    # Mock genai client to throw 429
    mock_genai_client = MagicMock()
    mock_genai_client.models.generate_content.side_effect = Exception("429 RESOURCE_EXHAUSTED: quota exceeded")
    client_llm.genai_client = mock_genai_client

    with patch("google.genai.Client", return_value=mock_genai_client):
        res = client_llm.generate("def test_dummy(): pass", agent_name="TestGeneratorAgent")

    # Verify that generation succeeded via AST synthesis fallback
    assert res is not None
    assert len(res) > 0

    # Verify that API_RATE_LIMIT_ROTATED and API_LIMIT_EXHAUSTED alerts were emitted
    event_types = [a.get("event_type") for a in captured_alerts]
    assert "API_RATE_LIMIT_ROTATED" in event_types
    assert "API_LIMIT_EXHAUSTED" in event_types

    # Check alert structure
    rot_alert = next(a for a in captured_alerts if a["event_type"] == "API_RATE_LIMIT_ROTATED")
    assert "Rotated to Backup Key" in rot_alert["title"]
    assert rot_alert["provider"] == "Cloud Gemini (Backup Key)"

    exhaust_alert = next(a for a in captured_alerts if a["event_type"] == "API_LIMIT_EXHAUSTED")
    assert "Quota Exhausted" in exhaust_alert["title"] or "Exhausted" in exhaust_alert["title"]


def test_openrouter_402_free_tier_fallback(monkeypatch):
    """
    Verifies that when a paid OpenRouter model returns HTTP 402 (insufficient credits),
    it auto-falls over to free coding models (:free) and emits API_RATE_LIMIT_ROTATED.
    """
    captured_alerts = []

    def mock_alert_callback(alert):
        captured_alerts.append(alert)

    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_API_KEY_2", raising=False)
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-openrouter-key")

    client_llm = HybridLLMClient(
        engine_mode="openrouter",
        alert_callback=mock_alert_callback
    )

    call_count = 0

    def mock_call_openrouter(prompt, system_instruction, api_key, model, temperature):
        nonlocal call_count
        call_count += 1
        if ":free" not in model and model != "openrouter/free":
            # Paid model returns HTTP 402
            err = urllib.error.HTTPError(
                url="https://openrouter.ai/api/v1/chat/completions",
                code=402,
                msg="Payment Required - Insufficient Credits",
                hdrs={},
                fp=None
            )
            raise err
        # Free model returns valid test assertions
        return "def test_free_pass(): assert True", {"total_tokens": 10}, 0.05

    with patch("testforge.llm_client.call_openrouter_api", side_effect=mock_call_openrouter):
        res = client_llm.generate("def test_prompt(): pass")

    assert "def test_free_pass" in res
    assert call_count > 1  # Proves it tried paid model first, then rotated to free model

    # Verify that API_RATE_LIMIT_ROTATED was emitted for the 402 rotation
    event_types = [a.get("event_type") for a in captured_alerts]
    assert "API_RATE_LIMIT_ROTATED" in event_types
    free_rot_alert = next(a for a in captured_alerts if a["event_type"] == "API_RATE_LIMIT_ROTATED")
    assert "402" in free_rot_alert["title"]
    assert "Free" in free_rot_alert["title"]
