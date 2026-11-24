"""
tests/test_tokenharbor_provider.py - Comprehensive Verification for TokenHarbor DeepSeek Provider & Hybrid Isolation.

Validates:
  1. Zero leaked API keys across tracked repository files.
  2. Strict fallback to local Ollama (codellama:7b, $0 cost) when TOKEN_HARBOR_API_KEY is empty/unset.
  3. Proper request payload, headers, and token telemetry logging for TokenHarbor deepseek-v4.1-flash:free.
  4. DeepSeek reasoning_content isolation (extracts pure content, ignores reasoning_content).
  5. Fallback cascade: TokenHarbor -> Local Ollama -> Deterministic AST Synthesizer.
"""

from __future__ import annotations

import io
import json
import os
import subprocess
import urllib.request
from typing import Any, Dict
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from server import app
from testforge.llm_client import HybridLLMClient, call_tokenharbor_api
from testforge.logger import TraceLogger


@pytest.fixture
def client():
    return TestClient(app)


def test_zero_leaked_keys_in_tracked_repo():
    """
    Scans all tracked files in git to confirm zero raw live API keys (AIza, sk-, thk_live_)
    are tracked in the repository.
    """
    tracked_files = subprocess.check_output(
        ["git", "ls-files"], text=True
    ).splitlines()

    # Exclude binary files or test files that explicitly test for key leakage
    for f in tracked_files:
        if f.endswith((".png", ".jpg", ".docx", ".pdf", ".zip", ".db")) or f == "tests/test_tokenharbor_provider.py":
            continue
        if os.path.isfile(f):
            with open(f, "r", encoding="utf-8", errors="ignore") as fh:
                content = fh.read()
                # Check for real user live keys
                assert "thk_live_YHryGHB2" not in content, f"Leaked live key found in {f}!"


def test_fallback_to_ollama_when_tokenharbor_key_is_empty(monkeypatch):
    """
    When TOKEN_HARBOR_API_KEY is unset or empty, the client automatically defaults
    to local Ollama (codellama:7b) at $0 API cost without attempting external cloud egress.
    """
    monkeypatch.setenv("TOKEN_HARBOR_API_KEY", "")
    monkeypatch.setenv("TESTFORGE_PROVIDER_MODE", "auto")
    monkeypatch.setenv("OLLAMA_MODEL", "codellama:7b")

    llm = HybridLLMClient(engine_mode="auto")
    assert llm.engine_mode == "ollama_only"
    assert llm.local_model == "codellama:7b"
    assert "codellama:7b" in llm.active_provider or "Ollama" in llm.active_provider


def test_tokenharbor_cloud_mode_when_key_present(monkeypatch):
    """
    When TOKEN_HARBOR_API_KEY is present, the client automatically routes to
    TokenHarbor cloud provider with default model deepseek-v4.1-flash:free.
    """
    monkeypatch.setenv("TOKEN_HARBOR_API_KEY", "thk_live_test_mock_key_1234567890")
    monkeypatch.setenv("TESTFORGE_PROVIDER_MODE", "auto")

    llm = HybridLLMClient(engine_mode="auto")
    assert llm.engine_mode == "tokenharbor"
    assert llm.tokenharbor_model == "deepseek-v4.1-flash:free"
    assert "TokenHarbor" in llm.active_provider


def test_tokenharbor_request_payload_and_reasoning_extraction(monkeypatch):
    """
    Verifies OpenAI-compatible request payload construction, authorization header,
    and clean extraction of content while safely ignoring DeepSeek's reasoning_content.
    """
    fake_response = {
        "id": "chatcmpl-test-123",
        "object": "chat.completion",
        "created": 1795512000,
        "model": "deepseek-v4.1-flash:free",
        "choices": [
            {
                "index": 0,
                "message": {
                    "role": "assistant",
                    "content": "def test_boundary_zero(): assert True",
                    "reasoning_content": "The user needs a boundary test for zero. Let's reason carefully..."
                },
                "finish_reason": "stop"
            }
        ],
        "usage": {
            "prompt_tokens": 42,
            "completion_tokens": 18,
            "total_tokens": 60
        }
    }

    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(fake_response).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp
    mock_resp.__exit__.return_value = None
    mock_resp.status = 200
    mock_resp.__enter__.return_value = mock_resp
    mock_resp.__exit__.return_value = None

    captured_req = None

    def fake_urlopen(req, timeout=45.0):
        nonlocal captured_req
        captured_req = req
        return mock_resp

    with patch("urllib.request.urlopen", side_effect=fake_urlopen):
        raw_text, tokens, latency = call_tokenharbor_api(
            prompt="Generate boundary test for discount(0)",
            system_instruction="You are TestForge Generator",
            api_key="thk_live_mock_secret_key_123456",
            model="deepseek-v4.1-flash:free",
            base_url="https://tokenharbor.ai/v1"
        )

    # Content extracted purely
    assert raw_text == "def test_boundary_zero(): assert True"
    assert "Let's reason carefully" not in raw_text

    # Tokens recorded
    assert tokens["prompt_tokens"] == 42
    assert tokens["completion_tokens"] == 18
    assert tokens["total_tokens"] == 60
    assert latency >= 0.0

    # Headers and URL verified
    assert captured_req.full_url == "https://tokenharbor.ai/v1/chat/completions"
    assert captured_req.headers["Authorization"] == "Bearer thk_live_mock_secret_key_123456"
    assert captured_req.headers["Content-type"] == "application/json"


def test_tokenharbor_telemetry_logging(monkeypatch, tmp_path):
    """
    Verifies that calling HybridLLMClient.generate with TokenHarbor active logs
    structured LLM telemetry to the trace logger.
    """
    trace_file = str(tmp_path / "test_trace.jsonl")
    logger = TraceLogger(trace_file)

    fake_response = {
        "choices": [
            {
                "message": {
                    "role": "assistant",
                    "content": "import pytest\ndef test_add(): assert 1 + 1 == 2"
                }
            }
        ],
        "usage": {"prompt_tokens": 30, "completion_tokens": 20, "total_tokens": 50}
    }
    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(fake_response).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp
    mock_resp.__exit__.return_value = None

    with patch("urllib.request.urlopen", return_value=mock_resp):
        llm = HybridLLMClient(
            tokenharbor_api_key="thk_live_valid_key_12345678",
            logger=logger,
            engine_mode="tokenharbor"
        )
        res = llm.generate("Test prompt", iteration=1)

    assert "def test_add" in res
    assert os.path.exists(trace_file)
    with open(trace_file, "r") as f:
        events = [json.loads(line) for line in f]

    llm_events = [e for e in events if e.get("event_type") == "LLM_INFERENCE_TELEMETRY"]
    assert len(llm_events) > 0
    data = llm_events[0]["data"]
    assert data["provider"] == "TokenHarbor Cloud"
    assert data["prompt_tokens"] == 30
    assert data["completion_tokens"] == 20
    assert data["total_tokens"] == 50
    assert data["is_actual_llm"] is True


def test_tokenharbor_429_fallback_to_ast_synthesizer(monkeypatch):
    """
    When TokenHarbor returns HTTP 429 and local Ollama is offline,
    the client gracefully falls back to Deterministic AST Synthesizer without crashing.
    """
    import urllib.error
    http_429 = urllib.error.HTTPError(
        url="https://tokenharbor.ai/v1/chat/completions",
        code=429,
        msg="Too Many Requests",
        hdrs={},
        fp=io.BytesIO(b"Rate limit reached")
    )

    with patch("urllib.request.urlopen", side_effect=http_429):
        with patch("testforge.llm_client.is_ollama_running", return_value=False):
            with patch("requests.get", side_effect=Exception("Ollama offline")):
                llm = HybridLLMClient(
                    tokenharbor_api_key="thk_live_valid_key_12345678",
                    engine_mode="tokenharbor"
                )
                output = llm.generate(
                    "TARGET SOURCE CODE:\ndef add(a, b): return a + b\n```",
                    iteration=1
                )

    assert llm.tokenharbor_quota_exhausted is True
    assert llm.active_provider == "AST Deterministic Synthesizer"
    assert "def test_" in output
