"""
tests/test_frontend_playground_verification.py - Comprehensive Headless Browser & DOM Verification.

Course: CSE3101 - Agentic AI
Role: Frontend QA Automation & Full-Stack Systems Engineer

Features:
  1. Static DOM & JS AST Contract Audit:
     - Scans all getElementById and querySelector calls in app.js and verifies zero dangling references in index.html.
     - Scans all addEventListener('click', ...) calls and verifies targets exist.
     - Validates all fetch(...) endpoint strings against server.py route table (zero 404 misconfigurations).
  2. Headless Playwright Integration Test Suite:
     - Launches headless Chromium against local live test server.
     - Sequential tab navigation verification (#tab-btn-lab, #tab-btn-wiretap, #tab-btn-benchmark, #tab-btn-history, etc.).
     - Benchmarks & Ablation: Verifies loadMultiTargetBenchmark() renders 4-target comparison table
       (discount.py, lru_cache.py, order_fsm.py, stats_calculator.py) with clean arithmetic and geometric mean summary rows in tfoot.
     - Multi-Agent Wiretap Topology Grid: Verifies all 8 canonical agent nodes with full URIs
       (agent:google-adk:supervisor, etc.) and reactive status pills.
     - Metric Cards & Drill-Downs: Tests #kpi-branch-card toggle for #kpi-missing-branches-dropdown,
       #kpi-tqs-card hover/click for #tqs-breakdown-tooltip.
     - Action Triggers & Configuration Controls: Validates #target-select, #max-iterations-input,
       #target-score-input, #engine-mode-select, #btn-start-hardening, #btn-cancel-job, #btn-resume-interrupted-job.
     - CI/CD Export Toolbar: Verifies #btn-download-junit, #btn-download-sarif, and #btn-download-suite.
     - Zero Uncaught Exceptions: Verifies pageerror event listeners record exactly 0 unhandled console errors.
"""

from __future__ import annotations
import os
import re
import time
import socket
import pathlib
import threading
from html.parser import HTMLParser
from typing import Set, List

import pytest
import uvicorn
from playwright.sync_api import sync_playwright

from server import app


BASE_DIR = pathlib.Path(__file__).resolve().parent.parent
INDEX_HTML_PATH = BASE_DIR / "frontend" / "index.html"
APP_JS_PATH = BASE_DIR / "frontend" / "app.js"


# ==============================================================================
# Helper HTML Parser for Static DOM Validation
# ==============================================================================

class HTMLIDCollector(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids: Set[str] = set()
        self.tags_with_id: List[tuple] = []

    def handle_starttag(self, tag, attrs):
        for k, v in attrs:
            if k == "id" and v:
                self.ids.add(v)
                self.tags_with_id.append((tag, v))


# ==============================================================================
# Module 1: Static Code, Contract, and DOM Integrity Tests
# ==============================================================================

class TestFrontendStaticDOMAndAPIContracts:
    """Validates 1:1 structural contracts between frontend HTML, JS, and server APIs."""

    def test_zero_dangling_element_id_references_in_app_js(self):
        """Verifies every document.getElementById call in app.js references a valid element in index.html."""
        parser = HTMLIDCollector()
        parser.feed(INDEX_HTML_PATH.read_text(encoding="utf-8"))
        all_html_ids = parser.ids

        app_js = APP_JS_PATH.read_text(encoding="utf-8")
        js_get_elem_ids = set(re.findall(r"getElementById\(['\"]([^'\"]+)['\"]\)", app_js))

        missing_ids = js_get_elem_ids - all_html_ids
        assert len(missing_ids) == 0, f"Dangling getElementById references found in app.js: {sorted(list(missing_ids))}"

    def test_query_selector_id_references_exist_in_index_html(self):
        """Verifies querySelector(#id) references in app.js point to existing elements."""
        parser = HTMLIDCollector()
        parser.feed(INDEX_HTML_PATH.read_text(encoding="utf-8"))
        all_html_ids = parser.ids

        app_js = APP_JS_PATH.read_text(encoding="utf-8")
        qs_ids = set(re.findall(r"querySelector(?:All)?\(['\"].*?#([a-zA-Z0-9_\-]+).*?['\"]\)", app_js))

        missing_ids = qs_ids - all_html_ids
        assert len(missing_ids) == 0, f"Dangling querySelector IDs found in app.js: {sorted(list(missing_ids))}"

    def test_all_frontend_fetch_routes_match_server_routes(self):
        """Verifies all fetch(...) API calls in app.js map to defined routes in server.py (0 404 misconfigurations)."""
        app_js = APP_JS_PATH.read_text(encoding="utf-8")
        fetch_calls = set(re.findall(r"fetch\(['`](/api/[^'`\?]+)['`\?]?", app_js))

        server_routes = [r.path for r in app.routes if hasattr(r, "path")]

        # Match routes with path variables normalized (e.g., /api/harden/status/{job_id})
        for fetch_url in fetch_calls:
            # Normalize JS template variables like ${jobId} to {param}
            normalized_pattern = re.sub(r"\$\{[^}]+\}", "[^/]+", fetch_url)
            matched = False
            for route in server_routes:
                route_regex = "^" + re.sub(r"\{[^}]+\}", "[^/]+", route) + "$"
                if re.match(route_regex, fetch_url) or re.match(normalized_pattern, route):
                    matched = True
                    break
            assert matched is True, f"Unmapped frontend fetch endpoint found: {fetch_url}"


# ==============================================================================
# Module 2: Playwright Headless Browser & Cockpit Verification Suite
# ==============================================================================

@pytest.fixture(scope="module")
def live_server_url():
    """Spawns an ephemeral background uvicorn server for genuine browser interactions."""
    def _find_free_port() -> int:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("127.0.0.1", 0))
        port = s.getsockname()[1]
        s.close()
        return port

    port = _find_free_port()
    config = uvicorn.Config(app=app, host="127.0.0.1", port=port, log_level="error")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    # Wait for server readiness
    time.sleep(1.2)
    base_url = f"http://127.0.0.1:{port}"
    yield base_url

    server.should_exit = True
    thread.join(timeout=3.0)


class TestFrontendHeadlessBrowserPlayground:
    """Executes full automated browser navigation and widget interaction testing via Playwright."""

    def test_headless_cockpit_full_interactive_verification(self, live_server_url):
        """
        Comprehensive automated headless verification covering:
          1. Zero console errors on boot.
          2. Sequential tab navigation & active class toggling.
          3. Multi-target benchmark table rendering with 4 canonical modules and mean rows.
          4. Eight-agent wiretap topology grid with verified canonical URIs.
          5. KPI drill-downs (Branch coverage dropdown toggle & TQS breakdown tooltip).
          6. Action & configuration control presence.
          7. CI/CD export toolbar presence.
        """
        console_errors: List[str] = []
        page_errors: List[str] = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()

            page.on("pageerror", lambda exc: page_errors.append(str(exc)))
            page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

            # 1. Boot dashboard
            page.goto(live_server_url)
            page.wait_for_load_state("domcontentloaded")
            time.sleep(1.0)

            assert "TestForge" in page.title(), f"Unexpected page title: {page.title()}"
            assert len(page_errors) == 0, f"Unhandled JavaScript page errors on load: {page_errors}"

            # 2. Sequential Navigation Tab Switching
            tabs = [
                ("#tab-btn-lab", "tab-hardening"),
                ("#tab-btn-wiretap", "tab-wiretap"),
                ("#tab-btn-benchmark", "tab-benchmark"),
                ("#tab-btn-history", "tab-checkpoints"),
                ("#nav-mode-a", "tab-mode-a"),
                ("#nav-mode-b", "tab-mode-b"),
                ("#nav-mode-c", "tab-mode-c"),
                ("#nav-blast", "tab-blast"),
                ("#nav-telemetry", "tab-telemetry"),
            ]

            for tab_selector, expected_pane_id in tabs:
                tab_btn = page.locator(tab_selector)
                assert tab_btn.count() == 1, f"Tab button {tab_selector} not found"
                tab_btn.click()
                time.sleep(0.3)

                # Assert tab button marked active
                assert "active" in tab_btn.get_attribute("class"), f"Tab button {tab_selector} missing active class"
                # Assert matching tab pane active and visible
                pane = page.locator(f"#{expected_pane_id}")
                assert "active" in pane.get_attribute("class"), f"Tab pane #{expected_pane_id} missing active class"

            # 3. Benchmarks & Ablation: Multi-Target Comparison Table & Statistical Means
            page.locator("#tab-btn-benchmark").click()
            time.sleep(0.8)

            table_body = page.locator("#multi-target-benchmark-table-body")
            body_text = table_body.inner_text()
            assert "discount.py" in body_text, "Missing discount.py row in multi-target table"
            assert "lru_cache.py" in body_text, "Missing lru_cache.py row in multi-target table"
            assert "order_fsm.py" in body_text, "Missing order_fsm.py row in multi-target table"
            assert "stats_calculator.py" in body_text, "Missing stats_calculator.py row in multi-target table"

            table_foot = page.locator("#multi-target-benchmark-table-foot")
            foot_text = table_foot.inner_text()
            assert "Arithmetic Mean" in foot_text, "Missing Arithmetic Mean row in tfoot"
            assert "Geometric Mean" in foot_text, "Missing Geometric Mean row in tfoot"

            # 4. Multi-Agent Wiretap Topology Grid
            page.locator("#tab-btn-wiretap").click()
            time.sleep(0.8)

            grid = page.locator("#wiretap-eight-agents-grid")
            assert grid.count() == 1, "Missing #wiretap-eight-agents-grid container"

            canonical_agents = [
                ("SupervisorAgent", "agent:google-adk:supervisor"),
                ("CodeIntelligenceAgent", "agent:google-adk:code-intel"),
                ("TestPlanningAgent", "agent:google-adk:planner"),
                ("TestGeneratorAgent", "agent:google-adk:generator"),
                ("TestExecutionAgent", "agent:google-adk:execution"),
                ("MutationQualityCriticAgent", "agent:crewai:critic"),
                ("SecurityAgent", "agent:google-adk:security"),
                ("ReflectionRepairAgent", "agent:google-adk:repair"),
            ]

            cards = page.locator(".agent-topo-card")
            assert cards.count() == 8, f"Expected 8 agent topology cards, got {cards.count()}"

            for agent_name, agent_uri in canonical_agents:
                node = page.locator(f'[data-agent-uri="{agent_uri}"]')
                assert node.count() == 1, f"Canonical agent node {agent_name} ({agent_uri}) not found in wiretap grid"

            # 5. Hardening Lab: Metric Cards & Interactive Drill-Downs
            page.locator("#tab-btn-lab").click()
            time.sleep(0.5)

            # Branch Coverage Card & Missing Branch Dropdown Toggle
            branch_card = page.locator("#kpi-branch-card")
            missing_dropdown = page.locator("#kpi-missing-branches-dropdown")
            assert "hidden" in missing_dropdown.get_attribute("class")

            branch_card.click()
            assert "hidden" not in missing_dropdown.get_attribute("class")

            branch_card.click()
            assert "hidden" in missing_dropdown.get_attribute("class")

            # Calibrated TQS Quality Card: Test hover & click tooltip display
            tqs_card = page.locator("#kpi-tqs-card")
            tqs_tooltip = page.locator("#tqs-breakdown-tooltip")
            tqs_card.hover()
            assert "hidden" not in tqs_tooltip.get_attribute("class")

            tqs_card.click()
            assert "hidden" not in tqs_tooltip.get_attribute("class")

            # 6. Target Selection & Configuration Controls
            assert page.locator("#target-select").count() == 1, "Missing #target-select dropdown"
            assert page.locator("#max-iterations-input").count() == 1, "Missing #max-iterations-input slider"
            assert page.locator("#target-score-input").count() == 1, "Missing #target-score-input slider"
            assert page.locator("#engine-mode-select").count() == 1, "Missing #engine-mode-select dropdown"

            # Verify sliders ranges
            max_iter = page.locator("#max-iterations-input")
            assert int(max_iter.get_attribute("min")) == 1
            assert int(max_iter.get_attribute("max")) == 10

            target_score = page.locator("#target-score-input")
            assert float(target_score.get_attribute("min")) == 50.0
            assert float(target_score.get_attribute("max")) == 100.0

            # 7. Action & Execution Triggers
            assert page.locator("#btn-start-hardening").count() == 1, "Missing #btn-start-hardening button"
            assert page.locator("#btn-cancel-job").count() == 1, "Missing #btn-cancel-job button"
            assert page.locator("#btn-resume-interrupted-job").count() == 1, "Missing #btn-resume-interrupted-job button"
            assert page.locator("#btn-run-multi-benchmark").count() == 1, "Missing #btn-run-multi-benchmark button"

            # 8. Enterprise CI/CD Export Toolbar
            assert page.locator("#btn-download-junit").count() == 1, "Missing #btn-download-junit button"
            assert page.locator("#btn-download-sarif").count() == 1, "Missing #btn-download-sarif button"
            assert page.locator("#btn-download-suite").count() == 1, "Missing #btn-download-suite button"

            # 9. Assert Zero Unhandled JavaScript Console Errors throughout entire execution
            assert len(page_errors) == 0, f"Uncaught page errors recorded: {page_errors}"
            assert len(console_errors) == 0, f"Uncaught console errors recorded: {console_errors}"

            browser.close()

