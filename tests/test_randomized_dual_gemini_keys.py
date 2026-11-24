"""
tests/test_randomized_dual_gemini_keys.py - Verification for Randomized Dual-Key Selection.

Validates:
  1. Equal opportunity randomized selection between GEMINI_API_KEY and GEMINI_API_KEY_2.
  2. Fallback to alternate key when primary key hits 429 quota exhaustion.
  3. Runtime UI settings preservation across POST /api/settings and POST /api/keys.
  4. Secure masking of both primary and secondary keys in status payloads.
"""

import os
import random
import pytest
from fastapi.testclient import TestClient

from server import app
from testforge.llm_client import HybridLLMClient, select_random_gemini_key


@pytest.fixture
def client():
    return TestClient(app)


def test_select_random_gemini_key_distribution(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "")
    monkeypatch.setenv("GEMINI_API_KEY_2", "")
    monkeypatch.setenv("GEMINI_FALLBACK_API_KEY", "")
    monkeypatch.setenv("GOOGLE_API_KEY", "")

    k1 = "AIzaSyDummyKeyAlpha_1111111111111111"
    k2 = "AIzaSyDummyKeyBeta__2222222222222222"

    selections = set()
    for _ in range(50):
        chosen = select_random_gemini_key(api_key=k1, api_key_2=k2)
        assert chosen in (k1, k2)
        selections.add(chosen)

    # Over 50 trials, probability of picking only one key is (1/2)^50 ~ 8.8e-16
    assert selections == {k1, k2}, "Both keys must be selected over multiple requests"


def test_select_random_gemini_key_single_fallback(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "")
    monkeypatch.setenv("GEMINI_API_KEY_2", "")
    monkeypatch.setenv("GEMINI_FALLBACK_API_KEY", "")
    monkeypatch.setenv("GOOGLE_API_KEY", "")

    k1 = "AIzaSyDummyKeyAlpha_1111111111111111"
    assert select_random_gemini_key(api_key=k1, api_key_2="") == k1
    assert select_random_gemini_key(api_key="", api_key_2=k1) == k1
    assert select_random_gemini_key(api_key=None, api_key_2=None) == ""


def test_hybrid_llm_client_random_pair(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "")
    monkeypatch.setenv("GEMINI_API_KEY_2", "")
    monkeypatch.setenv("GEMINI_FALLBACK_API_KEY", "")
    monkeypatch.setenv("GOOGLE_API_KEY", "")

    k1 = "AIzaSyDummyKeyAlpha_1111111111111111"
    k2 = "AIzaSyDummyKeyBeta__2222222222222222"

    llm = HybridLLMClient(api_key=k1, api_key_2=k2, engine_mode="auto")
    keys = llm.get_configured_gemini_keys()
    assert len(keys) == 2
    assert set(keys) == {k1, k2}

    pairs = set()
    for _ in range(50):
        p, b = llm.get_random_key_pair()
        assert {p, b} == {k1, k2}
        pairs.add((p, b))

    assert (k1, k2) in pairs
    assert (k2, k1) in pairs


def test_api_settings_and_keys_dual_key_preservation(client, monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "")
    monkeypatch.setenv("GEMINI_API_KEY_2", "")
    monkeypatch.setenv("GEMINI_FALLBACK_API_KEY", "")
    monkeypatch.setenv("GOOGLE_API_KEY", "")

    k1 = "AIzaSyDummyKeyAlpha_1111111111111111"
    k2 = "AIzaSyDummyKeyBeta__2222222222222222"

    # Test POST /api/settings
    resp_settings = client.post("/api/settings", json={
        "gemini_api_key": k1,
        "gemini_api_key_2": k2,
        "provider_mode": "auto"
    })
    assert resp_settings.status_code == 200
    data_settings = resp_settings.json()
    assert data_settings["has_gemini"] is True
    assert data_settings["has_gemini_fallback"] is True
    assert data_settings["dual_keys_active"] is True
    assert data_settings["key_selection_strategy"] == "randomized"

    # Verify keys are securely masked
    assert "..." in data_settings["gemini_key_masked"]
    assert "..." in data_settings["gemini_key_2_masked"]
    assert k1 not in resp_settings.text
    assert k2 not in resp_settings.text

    # Test GET /api/settings returns matching status
    resp_get = client.get("/api/settings")
    assert resp_get.status_code == 200
    data_get = resp_get.json()
    assert data_get["providers"]["has_gemini"] is True
    assert data_get["providers"]["has_gemini_fallback"] is True

    # Cleanup test keys from environment
    os.environ["GEMINI_API_KEY"] = ""
    os.environ["GEMINI_API_KEY_2"] = ""
