"""
tests/test_settings_key_hot_swap.py

Verifies:
1. POST /api/keys updates TOKEN_HARBOR_API_KEY in the live environment immediately.
2. Subsequent HybridLLMClient instances dynamically pick up the new key without server restart.
3. Empty/blank fields in POST /api/keys preserve existing keys without overwriting them.
4. GET /api/status and POST /api/keys return masked key status for UI settings modal.
"""

from __future__ import annotations

import os

import pytest
from fastapi.testclient import TestClient

from server import app
from testforge.llm_client import HybridLLMClient


@pytest.fixture
def client():
    return TestClient(app)


def test_hot_swap_tokenharbor_key_updates_environment_and_subsequent_instances(client, monkeypatch):
    """
    Calling POST /api/keys with a new TokenHarbor key updates os.environ,
    and subsequent HybridLLMClient instantiations pick up the new key.
    """
    monkeypatch.setenv("TOKEN_HARBOR_API_KEY", "thk_live_initial_key_111111111111")

    resp = client.post("/api/keys", json={
        "token_harbor_api_key": "thk_live_new_secret_key_999999999999"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["has_tokenharbor"] is True
    assert "thk_li..." in data["tokenharbor_key_masked"]

    assert os.environ.get("TOKEN_HARBOR_API_KEY") == "thk_live_new_secret_key_999999999999"

    llm = HybridLLMClient()
    assert llm.tokenharbor_api_key == "thk_live_new_secret_key_999999999999"
    assert llm.engine_mode == "tokenharbor"


def test_empty_fields_preserve_existing_keys(client, monkeypatch):
    """
    Submitting blank or None fields in POST /api/keys must NOT overwrite or wipe
    previously configured server keys.
    """
    monkeypatch.setenv("TOKEN_HARBOR_API_KEY", "thk_live_preserve_key_12345678")

    resp = client.post("/api/keys", json={
        "token_harbor_api_key": "   ",
        "provider_mode": "tokenharbor"
    })
    assert resp.status_code == 200
    data = resp.json()

    assert os.environ.get("TOKEN_HARBOR_API_KEY") == "thk_live_preserve_key_12345678"
    assert data["has_tokenharbor"] is True


def test_status_endpoint_returns_masked_keys(client, monkeypatch):
    """
    GET /api/status returns masked key representations so UI Settings modal
    can render masked badges and placeholders without exposing secrets.
    """
    monkeypatch.setenv("TOKEN_HARBOR_API_KEY", "thk_live_secret_token_1234567890")

    resp = client.get("/api/status")
    assert resp.status_code == 200
    providers = resp.json().get("providers", {})

    assert providers["has_tokenharbor"] is True
    assert providers["tokenharbor_key_masked"].startswith("thk_li")
    assert providers["tokenharbor_key_masked"].endswith("7890")
    assert "..." in providers["tokenharbor_key_masked"]


def test_reload_keys_on_existing_hybrid_client(monkeypatch):
    """
    Verifies that calling reload_keys() on an existing HybridLLMClient instance
    refreshes its internal keys from the updated os.environ immediately.
    """
    monkeypatch.setenv("TOKEN_HARBOR_API_KEY", "thk_live_first_key_111111")

    client = HybridLLMClient()
    assert client.tokenharbor_api_key == "thk_live_first_key_111111"
    assert client.engine_mode == "tokenharbor"

    monkeypatch.setenv("TOKEN_HARBOR_API_KEY", "thk_live_second_key_222222")
    client.reload_keys()
    assert client.tokenharbor_api_key == "thk_live_second_key_222222"
