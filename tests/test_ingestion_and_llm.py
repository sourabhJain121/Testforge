"""
test_ingestion_and_llm.py - Tests for GitHub Ingestion and OpenRouter LLM Failover.
"""

import os

import pytest

from testforge.ingestion import TargetManagerAgent, fetch_github_source
from testforge.llm_client import HybridLLMClient, call_openrouter_api


def test_github_blob_url_conversion():
    # Valid blob URL from a stable public repository
    url = "https://github.com/psf/requests/blob/main/src/requests/status_codes.py"
    saved = fetch_github_source(url)
    assert saved.exists()
    assert "github_requests_status_codes.py" in str(saved)
    with open(saved) as f:
        assert len(f.read()) > 100


def test_github_invalid_url():
    with pytest.raises(ValueError):
        fetch_github_source("https://example.com/not-github.py")


def test_openrouter_cascade_mode():
    client = HybridLLMClient(
        engine_mode="openrouter",
        openrouter_api_key="mock_invalid_key_for_test"
    )
    # Should attempt OpenRouter, fail on auth, and engage tier 4 fallback
    with pytest.raises(RuntimeError) as exc_info:
        client.generate("test prompt")
    assert "Tier 4 Fallback Engaged" in str(exc_info.value)
