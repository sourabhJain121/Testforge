"""
tests/test_settings_key_hot_swap.py

Verifies:
1. POST /api/keys updates GEMINI_API_KEY, GEMINI_API_KEY_2 (and GEMINI_FALLBACK_API_KEY),
   and OPENROUTER_API_KEY in the live environment immediately.
2. Subsequent HybridLLMClient instances dynamically pick up the new keys without server restart.
3. Empty/blank fields in POST /api/keys preserve existing keys without overwriting them.
4. GET /api/status and POST /api/keys return masked key status for UI settings modal.
"""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from server import app
from testforge.llm_client import HybridLLMClient


@pytest.fixture
def client():
    return TestClient(app)


def test_hot_swap_keys_updates_environment_and_subsequent_instances(client, monkeypatch):
    """
    Calling POST /api/keys with new keys updates os.environ,
    and subsequent HybridLLMClient instantiations pick up the new keys.
    """
    # Initialize initial state
    monkeypatch.setenv("GEMINI_API_KEY", "initial-gem-key-1111")
    monkeypatch.setenv("GEMINI_API_KEY_2", "initial-backup-key-2222")
    monkeypatch.setenv("OPENROUTER_API_KEY", "initial-openrouter-key-3333")

    # Post new keys
    resp = client.post("/api/keys", json={
        "gemini_api_key": "AIzaSyNewGeminiPrimary12345",
        "gemini_api_key_2": "AIzaSyNewGeminiBackup67890",
        "openrouter_api_key": "sk-or-v1-NewOpenRouterSecret"
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["has_gemini"] is True
    assert data["has_gemini_fallback"] is True
    assert data["has_openrouter"] is True

    # Check masked previews
    assert "AIzaSy" in data["gemini_key_masked"]
    assert "..." in data["gemini_key_masked"]
    assert "sk-or-" in data["openrouter_key_masked"]

    # Verify environment was updated
    assert os.environ.get("GEMINI_API_KEY") == "AIzaSyNewGeminiPrimary12345"
    assert os.environ.get("GEMINI_API_KEY_2") == "AIzaSyNewGeminiBackup67890"
    assert os.environ.get("GEMINI_FALLBACK_API_KEY") == "AIzaSyNewGeminiBackup67890"
    assert os.environ.get("OPENROUTER_API_KEY") == "sk-or-v1-NewOpenRouterSecret"

    # Verify subsequent HybridLLMClient instantiation picks up the new keys immediately
    llm = HybridLLMClient(engine_mode="cloud")
    assert llm.api_key == "AIzaSyNewGeminiPrimary12345"
    assert llm.api_key_2 == "AIzaSyNewGeminiBackup67890"
    assert llm.openrouter_api_key == "sk-or-v1-NewOpenRouterSecret"


def test_empty_fields_preserve_existing_keys(client, monkeypatch):
    """
    Submitting blank or None fields in POST /api/keys must NOT overwrite or wipe
    previously configured server keys.
    """
    monkeypatch.setenv("GEMINI_API_KEY", "active-gemini-key-preserve")
    monkeypatch.setenv("GEMINI_API_KEY_2", "active-gemini-2-preserve")
    monkeypatch.setenv("OPENROUTER_API_KEY", "active-openrouter-preserve")

    # Submit empty strings for gemini keys and update only openrouter key
    resp = client.post("/api/keys", json={
        "gemini_api_key": "   ",
        "gemini_api_key_2": "",
        "openrouter_api_key": "sk-or-v1-fresh-key"
    })
    assert resp.status_code == 200
    data = resp.json()

    # Gemini keys must remain intact
    assert os.environ.get("GEMINI_API_KEY") == "active-gemini-key-preserve"
    assert os.environ.get("GEMINI_API_KEY_2") == "active-gemini-2-preserve"
    assert os.environ.get("OPENROUTER_API_KEY") == "sk-or-v1-fresh-key"
    assert data["has_gemini"] is True
    assert data["has_gemini_fallback"] is True
    assert data["has_openrouter"] is True


def test_status_endpoint_returns_masked_keys(client, monkeypatch):
    """
    GET /api/status returns masked key representations so UI Settings modal
    can render masked badges and placeholders without exposing secrets.
    """
    monkeypatch.setenv("GEMINI_API_KEY", "AIzaSyTestSecretKey4567")
    monkeypatch.setenv("GEMINI_API_KEY_2", "AIzaSyBackupSecretKey8910")
    monkeypatch.setenv("OPENROUTER_API_KEY", "sk-or-v1-OpenRouterSecretKey1234")

    resp = client.get("/api/status")
    assert resp.status_code == 200
    providers = resp.json().get("providers", {})

    assert providers["has_gemini"] is True
    assert providers["has_gemini_fallback"] is True
    assert providers["has_openrouter"] is True

    # Masked previews check
    assert providers["gemini_key_masked"].startswith("AIzaSy")
    assert providers["gemini_key_masked"].endswith("4567")
    assert "..." in providers["gemini_key_masked"]

    assert providers["gemini_key_2_masked"].startswith("AIzaSy")
    assert providers["gemini_key_2_masked"].endswith("8910")

    assert providers["openrouter_key_masked"].startswith("sk-or-")
    assert providers["openrouter_key_masked"].endswith("1234")


def test_reload_keys_on_existing_hybrid_client(monkeypatch):
    """
    Verifies that calling reload_keys() on an existing HybridLLMClient instance
    refreshes its internal keys from the updated os.environ immediately.
    """
    monkeypatch.setenv("GEMINI_API_KEY", "first-key")
    monkeypatch.delenv("GEMINI_API_KEY_2", raising=False)
    monkeypatch.delenv("GEMINI_FALLBACK_API_KEY", raising=False)
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)

    client = HybridLLMClient(engine_mode="cloud")
    assert client.api_key == "first-key"
    assert client.api_key_2 == ""

    # Update environment
    monkeypatch.setenv("GEMINI_API_KEY", "second-key")
    monkeypatch.setenv("GEMINI_API_KEY_2", "second-backup-key")
    monkeypatch.setenv("OPENROUTER_API_KEY", "second-openrouter-key")

    # Client reloads keys
    client.reload_keys()
    assert client.api_key == "second-key"
    assert client.api_key_2 == "second-backup-key"
    assert client.openrouter_api_key == "second-openrouter-key"
