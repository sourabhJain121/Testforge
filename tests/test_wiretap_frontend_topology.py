"""
tests/test_wiretap_frontend_topology.py

Verifies the integration of the Canonical Eight-Agent Architecture Topology
in the Multi-Agent Wiretap API and Cockpit UI.
"""

import pathlib

import pytest
from starlette.testclient import TestClient

from server import app

BASE_DIR = pathlib.Path(__file__).resolve().parent.parent

CANONICAL_EIGHT = [
    "SupervisorAgent",
    "CodeIntelligenceAgent",
    "TestPlanningAgent",
    "TestGeneratorAgent",
    "TestExecutionAgent",
    "MutationQualityCriticAgent",
    "SecurityAgent",
    "ReflectionRepairAgent",
]


class TestWiretapFrontendTopology:
    """Verifies Wiretap API response contracts and frontend visualizer assets."""

    @pytest.fixture
    def client(self):
        return TestClient(app)

    def test_wiretap_api_returns_complete_eight_agent_status_matrix(self, client):
        """Verifies that /api/wiretap returns eight_agents_status with all canonical 8 agents."""
        res = client.get("/api/wiretap")
        assert res.status_code == 200
        data = res.json()

        assert "eight_agents_status" in data, "eight_agents_status missing in wiretap response"
        eight_status = data["eight_agents_status"]

        for agent in CANONICAL_EIGHT:
            assert agent in eight_status, f"{agent} missing in eight_agents_status"
            st = eight_status[agent]
            assert st["name"] == agent
            assert st["registered"] is True
            assert st["instantiated"] is True
            assert isinstance(st["participating"], bool)

    def test_frontend_html_contains_topology_grid_container(self):
        """Verifies frontend/index.html includes the eight-agent dynamic grid element."""
        index_html = (BASE_DIR / "frontend" / "index.html").read_text(encoding="utf-8")
        assert 'id="wiretap-eight-agents-grid"' in index_html
        assert "Canonical Eight-Agent Architecture Topology" in index_html
        assert "wiretap-kpi-agents" in index_html

    def test_frontend_app_js_implements_dynamic_rendering_for_all_eight_agents(self):
        """Verifies frontend/app.js defines metadata and rendering for all eight agents."""
        app_js = (BASE_DIR / "frontend" / "app.js").read_text(encoding="utf-8")
        assert "renderEightAgentsGrid" in app_js
        assert "CANONICAL_EIGHT_META" in app_js
        for agent in CANONICAL_EIGHT:
            assert agent in app_js, f"Agent {agent} not referenced in app.js"
        assert "wiretapEightAgentsGrid" in app_js
        assert "step-supervisor" in app_js

    def test_frontend_style_css_defines_supervisor_and_topology_card_styles(self):
        """Verifies frontend/style.css defines styles for supervisor step and agent cards."""
        style_css = (BASE_DIR / "frontend" / "style.css").read_text(encoding="utf-8")
        assert ".wiretap-step-card.step-supervisor::before" in style_css
        assert ".agent-topo-card:hover" in style_css

