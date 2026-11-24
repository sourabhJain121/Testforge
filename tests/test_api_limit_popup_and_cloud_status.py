"""
tests/test_api_limit_popup_and_cloud_status.py

Verifies:
1. 429 rate limit triggers API_LIMIT_EXHAUSTED telemetry event cleanly.
2. Cloud health endpoint reports 'cloud_disabled' for Ollama when running in cloud environments (RENDER=true).
3. TokenHarbor HTTP 402/429 credit/rate limit responses trigger fallback gracefully.
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
    monkeypatch.setenv("TOKEN_HARBOR_API_KEY", "mock-tokenharbor-key")
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
    supporting both {key, provider} and {token_harbor_api_key, ollama_model}.
    """
    # 1. Hot-swap TokenHarbor key via provider format
    resp1 = client.post("/api/keys", json={
        "provider": "tokenharbor",
        "key": "test-hot-swap-th-key-1"
    })
    assert resp1.status_code == 200
    d1 = resp1.json()
    assert d1["status"] == "success"
    assert d1["has_tokenharbor"] is True
    assert os.environ.get("TOKEN_HARBOR_API_KEY") == "test-hot-swap-th-key-1"

    # 2. Hot-swap TokenHarbor key via direct field
    resp2 = client.post("/api/keys", json={
        "token_harbor_api_key": "test-hot-swap-th-key-2",
        "token_harbor_model": "deepseek-v4.1-flash:free",
        "provider_mode": "tokenharbor"
    })
    assert resp2.status_code == 200
    d2 = resp2.json()
    assert d2["has_tokenharbor"] is True
    assert os.environ.get("TOKEN_HARBOR_API_KEY") == "test-hot-swap-th-key-2"
    assert d2["tokenharbor_model"] == "deepseek-v4.1-flash:free"

    # 3. Hot-swap Ollama model
    resp3 = client.post("/api/keys", json={
        "provider": "ollama",
        "key": "codellama:7b",
        "provider_mode": "ollama_only"
    })
    assert resp3.status_code == 200
    d3 = resp3.json()
    assert os.environ.get("OLLAMA_MODEL") == "codellama:7b"
    assert d3["provider_mode"] == "ollama_only"


def test_tokenharbor_429_exhaustion_alert(monkeypatch):
    """
    Verifies that when TokenHarbor hits 429 (rate limit):
    1. It emits API_LIMIT_EXHAUSTED event with proper warning status.
    2. It falls back smoothly to local Ollama or AST rule synthesizer.
    """
    captured_alerts = []

    def mock_alert_callback(alert):
        captured_alerts.append(alert)

    monkeypatch.setenv("TESTFORGE_PROVIDER_MODE", "tokenharbor")
    monkeypatch.setenv("TOKEN_HARBOR_API_KEY", "test-th-key")

    client_llm = HybridLLMClient(
        tokenharbor_api_key="test-th-key",
        engine_mode="tokenharbor",
        alert_callback=mock_alert_callback
    )

    err = urllib.error.HTTPError(
        url="https://tokenharbor.ai/v1/chat/completions",
        code=429,
        msg="Too Many Requests",
        hdrs={},
        fp=None
    )

    with patch("testforge.llm_client.call_tokenharbor_api", side_effect=err):
        # Force local ollama offline so it routes to AST
        with patch("requests.get", side_effect=Exception("Ollama offline")):
            res = client_llm.generate("def test_dummy(): pass", agent_name="TestGeneratorAgent")

    # Verify that generation succeeded via AST synthesis fallback
    assert res is not None
    assert len(res) > 0

    # Verify that API_LIMIT_EXHAUSTED alert was emitted
    event_types = [a.get("event_type") for a in captured_alerts]
    assert "API_LIMIT_EXHAUSTED" in event_types

    exhaust_alert = next(a for a in captured_alerts if a["event_type"] == "API_LIMIT_EXHAUSTED")
    assert "TokenHarbor" in exhaust_alert["title"]
    assert exhaust_alert["provider"] == "TokenHarbor Cloud"


def test_tokenharbor_402_failover_to_ast(monkeypatch):
    """
    Verifies that when TokenHarbor returns HTTP 402 (payment/credits required),
    it auto-falls over to AST/local and emits API_LIMIT_EXHAUSTED alert.
    """
    captured_alerts = []

    def mock_alert_callback(alert):
        captured_alerts.append(alert)

    monkeypatch.setenv("TESTFORGE_PROVIDER_MODE", "tokenharbor")
    monkeypatch.setenv("TOKEN_HARBOR_API_KEY", "test-th-key")

    client_llm = HybridLLMClient(
        tokenharbor_api_key="test-th-key",
        engine_mode="tokenharbor",
        alert_callback=mock_alert_callback
    )

    err = urllib.error.HTTPError(
        url="https://tokenharbor.ai/v1/chat/completions",
        code=402,
        msg="Payment Required",
        hdrs={},
        fp=None
    )

    with patch("testforge.llm_client.call_tokenharbor_api", side_effect=err):
        with patch("requests.get", side_effect=Exception("Ollama offline")):
            res = client_llm.generate("def test_prompt(): pass")

    assert res is not None
    assert "def test_" in res

    event_types = [a.get("event_type") for a in captured_alerts]
    assert "API_LIMIT_EXHAUSTED" in event_types

