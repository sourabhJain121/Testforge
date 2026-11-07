"""
tests/test_privacy_mode.py

Comprehensive Verification Suite for Zero-Egress Privacy Mode & PII Scrubbing (Sub-Task 4.1).
Covers:
1. PrivacyModeManager enable/disable lifecycle and status.
2. ZeroEgressSocketInterceptor blocking external outbound connections.
3. Allowed local loopback and Ollama connections.
4. API keys, secrets, and PII sanitization.
5. Model routing redirection (cloud -> local air-gapped).
6. FastAPI REST endpoints: GET /api/privacy/status, POST /api/privacy/toggle.
"""

import os
import socket
import pytest
from starlette.testclient import TestClient

from server import app
from testforge.privacy_mode import (
    ALLOWED_LOCAL_HOSTS,
    PrivacyModeManager,
    PrivacySecurityError,
    ZeroEgressSocketInterceptor,
)


@pytest.fixture(autouse=True)
def reset_privacy_state():
    """Ensures Privacy Mode is cleanly uninstalled and reset before and after each test."""
    mgr = PrivacyModeManager.get_instance()
    mgr.disable()
    ZeroEgressSocketInterceptor.clear_blocked_attempts()
    yield
    mgr.disable()
    ZeroEgressSocketInterceptor.clear_blocked_attempts()


def test_privacy_manager_lifecycle():
    mgr = PrivacyModeManager.get_instance()
    assert not mgr.is_enabled()
    assert not ZeroEgressSocketInterceptor._active

    mgr.enable()
    assert mgr.is_enabled()
    assert ZeroEgressSocketInterceptor._active
    assert os.environ.get("TESTFORGE_PRIVACY_MODE") == "true"

    status = mgr.get_status()
    assert status["privacy_mode_enabled"] is True
    assert status["zero_egress_active"] is True
    assert "qwen2.5-coder:7b" in status["enforced_model_fallback"]

    mgr.disable()
    assert not mgr.is_enabled()
    assert not ZeroEgressSocketInterceptor._active
    assert os.environ.get("TESTFORGE_PRIVACY_MODE") == "false"


def test_zero_egress_blocks_external_socket():
    mgr = PrivacyModeManager.get_instance()
    mgr.enable()

    # Attempt connection to an external address
    with pytest.raises(PrivacySecurityError) as exc_info:
        socket.create_connection(("8.8.8.8", 53), timeout=1)

    assert "Zero-egress Privacy Mode is ACTIVE" in str(exc_info.value)
    assert "8.8.8.8:53" in str(exc_info.value)

    blocked = ZeroEgressSocketInterceptor.get_blocked_attempts()
    assert len(blocked) >= 1
    assert any(b["target"] == "8.8.8.8:53" for b in blocked)


def test_zero_egress_allows_loopback():
    mgr = PrivacyModeManager.get_instance()
    mgr.enable()

    # Create a local listening socket
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.bind(("127.0.0.1", 0))
    server_sock.listen(1)
    port = server_sock.getsockname()[1]

    try:
        # Client connect to loopback must NOT raise PrivacySecurityError
        client_sock = socket.create_connection(("127.0.0.1", port), timeout=2)
        client_sock.close()
    finally:
        server_sock.close()

    # Blocked list should still be empty
    assert len(ZeroEgressSocketInterceptor.get_blocked_attempts()) == 0


def test_secret_and_pii_scrubbing():
    mgr = PrivacyModeManager.get_instance()

    raw_prompt = (
        "Here is my Gemini key: AIzaSyD9876543210abcdefghijklmnop\n"
        "Here is my OpenRouter key: sk-or-v1-abcdef0123456789abcdef0123456789\n"
        "User SSN is 123-45-6789 and user email is test.user@enterprise.org"
    )

    scrubbed, count = mgr.scrub_prompt(raw_prompt)
    assert count >= 3
    assert "AIzaSy" not in scrubbed
    assert "sk-or-v1-" not in scrubbed
    assert "123-45-6789" not in scrubbed
    assert "[REDACTED_API_KEY_GEMINI]" in scrubbed
    assert "[REDACTED_API_KEY_OPENROUTER]" in scrubbed
    assert "[REDACTED_PII_SSN]" in scrubbed


def test_model_selection_rerouting():
    mgr = PrivacyModeManager.get_instance()
    mgr.disable()
    # In normal mode, cloud model is preserved
    assert mgr.validate_model_selection("gemini-3.6-flash") == "gemini-3.6-flash"

    # In Privacy Mode, cloud models are rerouted to local Ollama
    mgr.enable()
    assert mgr.validate_model_selection("gemini-3.6-flash") == "qwen2.5-coder:7b"
    assert mgr.validate_model_selection("gpt-4o") == "qwen2.5-coder:7b"
    assert mgr.validate_model_selection("claude-3-opus") == "qwen2.5-coder:7b"
    assert mgr.validate_model_selection("openrouter/auto") == "qwen2.5-coder:7b"

    # Local model is retained
    assert mgr.validate_model_selection("qwen2.5-coder:7b") == "qwen2.5-coder:7b"


def test_privacy_api_endpoints():
    client = TestClient(app)

    # 1. GET status
    resp = client.get("/api/privacy/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "privacy_mode_enabled" in data
    assert "zero_egress_active" in data

    # 2. POST toggle to enable
    resp = client.post("/api/privacy/toggle", json={"enabled": True})
    assert resp.status_code == 200
    assert resp.json()["privacy_mode_enabled"] is True
    assert resp.json()["zero_egress_active"] is True

    # 3. POST toggle without body (flips state)
    resp = client.post("/api/privacy/toggle")
    assert resp.status_code == 200
    assert resp.json()["privacy_mode_enabled"] is False
    assert resp.json()["zero_egress_active"] is False

    # 4. POST toggle back to False
    resp = client.post("/api/privacy/toggle", json={"enabled": False})
    assert resp.status_code == 200
    assert resp.json()["privacy_mode_enabled"] is False
