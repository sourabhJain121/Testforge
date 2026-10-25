"""
tests/test_a2a_card_ui_and_endpoint.py - Verification tests for A2A Card endpoint and UI contracts.
"""

import re
import json
import pytest
from pathlib import Path
from starlette.testclient import TestClient

from server import app
from testforge.a2a_protocol import build_testforge_agent_card


client = TestClient(app)


def test_a2a_agent_card_endpoint_schema():
    """Verify /.well-known/agent-card.json returns valid 200 JSON adhering to A2A specification."""
    resp = client.get("/.well-known/agent-card.json")
    assert resp.status_code == 200
    assert "application/json" in resp.headers["content-type"]
    
    data = resp.json()
    assert isinstance(data, dict)
    assert data["name"] == "testforge-agent-system"
    assert data["protocolVersion"] == "0.3.0"
    assert data["version"] == "1.0.0"
    assert "description" in data
    assert data["url"] == "http://127.0.0.1:8000/"
    assert data["preferredTransport"] == "JSONRPC"
    
    # Capabilities
    assert "capabilities" in data
    assert data["capabilities"].get("streaming") is False
    assert data["capabilities"].get("pushNotifications") is False
    
    # Provider
    assert "provider" in data
    assert data["provider"].get("organization") == "TestForge Autonomous Systems"
    assert "github.com" in data["provider"].get("url", "")
    
    # Skills
    assert "skills" in data
    assert len(data["skills"]) >= 3
    skill_ids = [s["id"] for s in data["skills"]]
    assert "unit-test-generation" in skill_ids
    assert "mutation-critique" in skill_ids
    assert "hardening-workflow" in skill_ids


def test_a2a_agent_card_dual_discovery_endpoint():
    """Verify /.well-known/agent.json returns matching schema."""
    resp = client.get("/.well-known/agent.json")
    assert resp.status_code == 200
    data = resp.json()
    assert data["protocolVersion"] == "0.3.0"
    assert data["name"] == "testforge-agent-system"


def test_a2a_agent_card_redaction_invariants():
    """Verify no secret keys, environment tokens, or private paths appear in the public card."""
    resp = client.get("/.well-known/agent-card.json")
    raw = resp.text
    assert "AIzaSy" not in raw
    assert "sk-or-v1" not in raw
    assert "PRIVATE KEY" not in raw
    assert "/Users/sourabh" not in raw


def test_frontend_index_html_a2a_modal_structure():
    """Verify frontend/index.html includes the semantic button and accessible modal structure."""
    html = Path("frontend/index.html").read_text(encoding="utf-8")
    
    # Button
    assert 'id="btn-a2a-card"' in html
    assert '<button type="button"' in html
    
    # Modal backdrop & modal
    assert 'id="a2a-modal-backdrop"' in html
    assert 'id="a2a-modal"' in html
    assert 'id="a2a-modal-title"' in html
    assert 'id="btn-close-a2a-modal"' in html
    
    # Body states
    assert 'id="a2a-loading-state"' in html
    assert 'id="a2a-error-state"' in html
    assert 'id="a2a-empty-state"' in html
    assert 'id="a2a-card-content"' in html
    
    # Footer actions
    assert 'id="btn-view-raw-a2a"' in html
    assert 'href="/.well-known/agent-card.json"' in html
    assert 'target="_blank"' in html
    assert 'id="btn-copy-a2a-json"' in html
    assert 'id="btn-close-a2a-footer"' in html


def test_frontend_app_js_a2a_implementation():
    """Verify frontend/app.js handles opening, closing, loading, safe rendering, and clipboard actions."""
    js = Path("frontend/app.js").read_text(encoding="utf-8")
    
    # DOM and State registrations
    assert "btnA2aCard: document.getElementById('btn-a2a-card')" in js
    assert "a2aModalBackdrop: document.getElementById('a2a-modal-backdrop')" in js
    assert "btnViewRawA2a: document.getElementById('btn-view-raw-a2a')" in js
    assert "btnCopyA2aJson: document.getElementById('btn-copy-a2a-json')" in js
    
    # Modal management functions
    assert "function openA2aModal" in js or "async function openA2aModal" in js
    assert "function closeA2aModal" in js
    assert "async function fetchAndRenderA2aCard" in js
    assert "function renderA2aCard" in js
    assert "async function copyA2aJson" in js
    
    # Safe rendering invariant: ensure textContent is used for server strings in renderA2aCard
    # Extract renderA2aCard body
    match = re.search(r"function renderA2aCard\(card\)\s*\{(.*?)\n\s*async function copyA2aJson", js, re.DOTALL)
    assert match is not None, "renderA2aCard function body not found"
    body = match.group(1)
    
    # Invariant: innerHTML must NOT be assigned untrusted dynamic card variables in renderA2aCard
    assert "cardContent.innerHTML" not in body
    assert "nameEl.textContent = card.name" in body
    assert "descEl.textContent = card.description" in body
    assert "val.textContent = f.val" in body
    assert "sTitle.textContent = skill.name" in body
    assert "sDesc.textContent = skill.description" in body
    
    # Escape key listener
    assert "dom.a2aModalBackdrop" in js
    assert "closeA2aModal()" in js
