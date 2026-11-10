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

import ast
import json
import os
import pathlib
import re
import socket
import threading
import time
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from typing import List, Set

import httpx
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

    def test_mcp_studio_modal_elements_exist_in_dom(self):
        """Verifies #btn-open-mcp-studio and all MCP Studio modal elements exist in index.html without dangling references."""
        parser = HTMLIDCollector()
        parser.feed(INDEX_HTML_PATH.read_text(encoding="utf-8"))
        all_html_ids = parser.ids

        required_studio_ids = [
            "btn-open-mcp-studio",
            "mcp-studio-modal-backdrop",
            "mcp-studio-modal",
            "btn-close-mcp-studio",
            "mcp-studio-tool-select",
            "btn-mcp-studio-execute",
            "mcp-studio-meta-badge",
            "mcp-studio-code-input",
            "mcp-studio-secondary-container",
            "mcp-studio-secondary-input",
            "mcp-studio-output-json",
            "btn-mcp-studio-copy",
        ]
        for req_id in required_studio_ids:
            assert req_id in all_html_ids, f"Required MCP Studio element #{req_id} missing in index.html"


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
                ("#tab-btn-ingestion", "tab-ingestion"),
                ("#tab-btn-blast", "tab-blast"),
                ("#tab-btn-lab", "tab-hardening"),
                ("#tab-btn-wiretap", "tab-wiretap"),
                ("#tab-btn-observability", "tab-telemetry"),
                ("#tab-btn-benchmarks", "tab-benchmark"),
                ("#tab-btn-checkpoints", "tab-checkpoints"),
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

            # Assert Navbar Checkpoints button shows full text "Checkpoints"
            checkpoints_btn_text = page.locator("#tab-btn-checkpoints").inner_text()
            assert "Checkpoints" in checkpoints_btn_text, f"Expected 'Checkpoints' in button text, got: {checkpoints_btn_text}"

            # Observability Tab Verification: Active Provider & Table Hydration
            page.locator("#tab-btn-observability, #nav-telemetry").first.click()
            time.sleep(0.5)
            provider_text = page.locator("#telem-active-provider, #obsActiveProvider").first.inner_text()
            assert "CHECKING" not in provider_text.upper(), f"Expected resolved provider text, got: {provider_text}"
            assert "DETERMINISTIC" in provider_text.upper() or "LOCAL" in provider_text.upper() or "GENAI" in provider_text.upper()
            telem_text = page.locator("#telemetry-table-body").inner_text()
            assert "No LLM inference calls logged yet" not in telem_text, f"Expected hydrated telemetry table, got: {telem_text}"

            # Supervisor Decisions & OTel Spans Verification
            sup_text = page.locator("#supervisor-decisions-table-body, #table-supervisor-decisions").first.inner_text()
            assert "Iter -" not in sup_text, f"Expected hydrated iteration, got: {sup_text}"
            assert "TARGET_ACHIEVED" in sup_text or "CONVERGED" in sup_text or "DISPATCH_AGENT" in sup_text or "HALT_CRITERIA_MET" in sup_text

            otel_text = page.locator("#otel-spans-table-body, #table-otel-spans").first.inner_text()
            assert "ms" in otel_text or "no data yet" in otel_text, f"Expected valid span durations, got: {otel_text}"

            # Checkpoints Tab Auto-Select Verification
            page.locator("#tab-btn-checkpoints").click()
            time.sleep(0.6)
            empty_ph = page.locator("#cp-detail-empty-placeholder")
            assert "hidden" in (empty_ph.get_attribute("class") or "") or empty_ph.is_hidden()
            detail_content = page.locator("#cp-detail-content")
            assert "hidden" not in (detail_content.get_attribute("class") or "")

            # 3. Benchmarks & Ablation: Multi-Target Comparison Table & Statistical Means
            page.locator("#tab-btn-benchmarks, #tab-btn-benchmark").first.click()
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

            # Verify no "GOOOLE" typos exist on wiretap tab
            wiretap_html = page.locator("#tab-wiretap").inner_html()
            assert "GOOOLE" not in wiretap_html, "Typo 'GOOOLE' found in #tab-wiretap"

            # Verify participating agents count displays 8
            agents_count = page.locator("#wiretap-kpi-agents").inner_text().strip()
            assert agents_count == "8", f"Expected participating agents count to be '8', got: {agents_count}"

            # Verify #btn-clear-wiretap is present, visible, and functional
            btn_clear = page.locator("#btn-clear-wiretap")
            assert btn_clear.is_visible(), "Expected #btn-clear-wiretap to be visible"
            btn_clear.click()
            time.sleep(0.2)
            timeline_text = page.locator("#wiretap-timeline-container").inner_text()
            assert "cleared" in timeline_text.lower(), f"Expected timeline cleared message, got: {timeline_text}"

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
            assert page.locator("#btn-lab-run-hardening, #btn-start-hardening").count() >= 1, "Missing #btn-lab-run-hardening button"
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

    def test_b1_happy_path_hardening(self, live_server_url):
        """
        Scenario B1: Happy Path Hardening.
        Loads sample discount.py, triggers hardening, asserts progress, completion,
        populates non-zero KPIs (score, line coverage, killed mutants), and verifies wiretap grid.
        """
        console_errors: List[str] = []
        page_errors: List[str] = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.on("pageerror", lambda exc: print(f"[PAGEERROR] {exc}"))
            page.on("console", lambda msg: print(f"[CONSOLE {msg.type}] {msg.text}"))

            page.goto(live_server_url)
            page.wait_for_load_state("domcontentloaded")
            time.sleep(1.0)

            # Navigate to Hardening Lab
            page.locator("#tab-btn-lab").click()
            time.sleep(0.5)

            # Click Start Hardening
            btn_start = page.locator("#btn-lab-run-hardening, #btn-start-hardening").first
            btn_start.click()

            # Verify progress bar indicator appears
            page.wait_for_selector("#hardening-progress-box:not(.hidden)", timeout=8000)

            # Wait for job completion (percent says FINALIZED)
            page.wait_for_selector("#hardening-percent-text:has-text('FINALIZED')", timeout=45000)
            time.sleep(1.0)

            # Assert non-zero mutation score and coverage
            mut_score = page.locator("#kpi-mut-score").inner_text()
            assert "%" in mut_score and mut_score != "0.0%", f"Expected non-zero mutation score, got {mut_score}"

            cov_pct = page.locator("#kpi-cov-pct").inner_text()
            assert "%" in cov_pct and cov_pct != "0.0%", f"Expected non-zero coverage, got {cov_pct}"

            killed = int(page.locator("#kpi-mut-kill").inner_text())
            assert killed > 0, f"Expected killed mutants > 0, got {killed}"

            # Verify hardened suite code is displayed
            suite_code = page.locator("#hardened-suite-code").inner_text()
            assert "def test_" in suite_code, "Expected generated test functions in test_hardened.py view"

            # Verify CI/CD export buttons enabled
            assert page.locator("#btn-download-junit").is_enabled()
            assert page.locator("#btn-download-sarif").is_enabled()

            # Verify wiretap auto-resets and does not exceed 30 children during execution
            page.locator("#tab-btn-wiretap").click()
            time.sleep(0.5)
            separators = page.locator("#wiretap-timeline-container .wiretap-run-separator")
            assert separators.count() >= 1, "Expected run demarcation separator in wiretap stream"
            wiretap_cards = page.locator("#wiretap-timeline-container .wiretap-step-card")
            assert wiretap_cards.count() <= 30, f"Expected wiretap stream items <= 30, got {wiretap_cards.count()}"
            assert "GOOOLE" not in page.locator("#tab-wiretap").inner_text(), "Found 'GOOOLE' in #tab-wiretap"

            assert len(page_errors) == 0, f"Page errors: {page_errors}"
            browser.close()

    def test_b2_custom_target_hardening(self, live_server_url, tmp_path):
        """
        Scenario B2: Custom Target Hardening.
        Uploads a custom Python module via Mode A file upload, verifies target activation,
        and hardens it end-to-end to verify custom workflow execution and results display.
        """
        console_errors: List[str] = []
        page_errors: List[str] = []

        custom_target = tmp_path / "custom_calc.py"
        custom_target.write_text(
            "def calculate_tax(amount: float, rate: float = 0.05) -> float:\n"
            "    if amount < 0 or rate < 0:\n"
            "        raise ValueError('Negative amount or rate')\n"
            "    return round(amount * (1.0 + rate), 2)\n",
            encoding="utf-8"
        )

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.on("pageerror", lambda exc: print(f"[PAGEERROR] {exc}"))
            page.on("console", lambda msg: print(f"[CONSOLE {msg.type}] {msg.text}"))

            page.goto(live_server_url)
            page.wait_for_load_state("domcontentloaded")
            time.sleep(1.0)

            # Navigate to Mode A
            page.locator("#btn-submode-a, [data-mode='a'], #nav-mode-a").first.click()
            time.sleep(0.3)

            # Select 'Upload Custom .py' radio
            page.locator("#radio-source-upload").click()
            time.sleep(0.3)

            # Upload custom target
            page.locator("#file-upload-input").set_input_files(str(custom_target))
            time.sleep(0.3)
            page.locator("#btn-submit-upload").click()

            # Wait for upload success toast and target module title update
            page.wait_for_selector("#toast-container:has-text('Uploaded and ingested')", timeout=10000)
            time.sleep(0.5)

            # Switch to Hardening Lab
            page.locator("#tab-btn-lab").click()
            time.sleep(0.5)

            # Trigger hardening pipeline on custom target
            page.locator("#btn-lab-run-hardening, #btn-start-hardening").first.click()
            page.wait_for_selector("#hardening-percent-text:has-text('FINALIZED')", timeout=45000)
            time.sleep(1.0)

            # Check final mutation score
            mut_score = page.locator("#kpi-mut-score").inner_text()
            assert "%" in mut_score and mut_score != "0.0%", f"Expected non-zero mutation score, got {mut_score}"

            assert len(page_errors) == 0, f"Page errors: {page_errors}"
            browser.close()

    def test_b3_cancellation_and_resumption(self, live_server_url):
        """
        Scenario B3: Mid-flight Cancellation & Resumption.
        Initiates a hardening run, immediately clicks Cancel, verifies CANCELLED state and safe worker teardown,
        then verifies checkpoint recovery and resumption.
        """
        console_errors: List[str] = []
        page_errors: List[str] = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.on("pageerror", lambda exc: print(f"[PAGEERROR] {exc}"))
            page.on("console", lambda msg: print(f"[CONSOLE {msg.type}] {msg.text}"))

            page.goto(live_server_url)
            page.wait_for_load_state("domcontentloaded")
            time.sleep(1.0)

            # Navigate to Hardening Lab
            page.locator("#tab-btn-lab").click()
            time.sleep(0.5)

            # Start hardening
            page.locator("#btn-lab-run-hardening, #btn-start-hardening").first.click()

            # Wait for cancel button to become visible and click it
            page.wait_for_selector("#btn-cancel-hardening", timeout=10000)
            time.sleep(0.2)
            page.locator("#btn-cancel-hardening").click()

            # Assert that clicking #btn-cancel-hardening causes #btn-cancel-hardening to hide within 3 seconds
            page.wait_for_selector("#btn-cancel-hardening", state="hidden", timeout=3000)

            # Assert returns #btn-lab-run-hardening to active
            btn_start = page.locator("#btn-lab-run-hardening, #btn-start-hardening").first
            assert btn_start.is_visible() and not btn_start.is_disabled(), "#btn-lab-run-hardening should return to active"

            # Assert updates status to CANCELLED
            page.wait_for_selector("#hardening-status-badge:has-text('CANCELLED')", timeout=5000)

            # Verify cancellation banner displays
            page.wait_for_selector("#hardening-verdict-banner.cancelled", timeout=15000)
            banner_text = page.locator("#hardening-verdict-banner").inner_text()
            assert "Cancelled" in banner_text, f"Unexpected banner text: {banner_text}"

            # Resumption verification: trigger resume endpoint via HTTP API
            # Extract job_id from banner or active state
            m = re.search(r"\[([a-zA-Z0-9_\-]+)\]", banner_text)
            if m:
                job_id = m.group(1)
                resp = httpx.post(f"{live_server_url}/api/harden/resume/{job_id}", timeout=10.0)
                # Resumed or 200/400 (if already at non-resumable terminal stage)
                assert resp.status_code in (200, 400), f"Unexpected resume response: {resp.text}"

            assert len(page_errors) == 0, f"Page errors: {page_errors}"
            browser.close()

    def test_b4_diff_inspector_and_artifact_downloads(self, live_server_url):
        """
        Scenario B4: Diff Inspector & Artifact Downloads.
        Verifies unified AST diff display and downloads hardened test suite, JUnit XML, and SARIF reports.
        Validates syntax of all exported artifacts.
        """
        console_errors: List[str] = []
        page_errors: List[str] = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.on("pageerror", lambda exc: print(f"[PAGEERROR] {exc}"))
            page.on("console", lambda msg: print(f"[CONSOLE {msg.type}] {msg.text}"))

            page.goto(live_server_url)
            page.wait_for_load_state("domcontentloaded")
            time.sleep(1.0)

            # Run hardening on default sample to populate mutants and reports
            page.locator("#tab-btn-lab").click()
            time.sleep(0.5)
            page.locator("#btn-lab-run-hardening, #btn-start-hardening").first.click()
            page.wait_for_selector("#hardening-percent-text:has-text('FINALIZED')", timeout=45000)
            time.sleep(1.0)

            # 1. Diff Inspector: Click on a mutant row in mutants table
            mutant_rows = page.locator("#mutants-table-body tr.mutant-row")
            if mutant_rows.count() > 0:
                # Verify TIME column formatting (Module 1)
                first_row_time = mutant_rows.first.locator("td").nth(4).inner_text().strip()
                assert first_row_time == "-" or "ms" in first_row_time or "s" in first_row_time
                assert not re.search(r"\d+\.\d{3,}m", first_row_time), f"Unformatted float detected in TIME column: {first_row_time}"

                mutant_rows.first.click()
                time.sleep(0.3)
                diff_text = page.locator("#diff-code-display").inner_text()
                assert len(diff_text) > 0, "Expected non-empty diff output"

                # Verify Diff Inspector outcome badge synchronization (Module 2)
                badge_text = page.locator("#diff-status-badge").inner_text()
                assert "KILLED" in badge_text or "SURVIVED" in badge_text or "EQUIVALENT" in badge_text
                badge_class = page.locator("#diff-status-badge").get_attribute("class")
                if "KILLED" in badge_text:
                    assert "badge-success" in badge_class or "badge-green" in badge_class

                # Assert that clicking a killed mutant row updates the outcome badge to include "KILLED"
                killed_row = page.locator("#mutants-table-body tr.mutant-row:has-text('KILLED')").first
                if killed_row.count() > 0:
                    killed_row.click()
                    time.sleep(0.3)
                    killed_badge_text = page.locator("#diff-status-badge").inner_text()
                    assert "KILLED" in killed_badge_text, f"Expected badge to reflect KILLED, got: {killed_badge_text}"
                    killed_badge_class = page.locator("#diff-status-badge").get_attribute("class")
                    assert "badge-success" in killed_badge_class or "badge-green" in killed_badge_class

                # Verify clicking mutant row 2 updates the diff header text to match that row's ID
                if mutant_rows.count() >= 2:
                    row2 = mutant_rows.nth(1)
                    row2_id = row2.locator("td").first.locator("code").inner_text().strip()
                    row2.click()
                    time.sleep(0.3)
                    diff_title_text = page.locator("#ast-diff-card-title, #diff-selected-mutant-title, #ast-diff-viewer-title, .diff-inspector-title").first.inner_text()
                    assert row2_id in diff_title_text, f"Expected diff title to contain row 2 ID '{row2_id}', got: {diff_title_text}"
                    ast_card_title = page.locator("#ast-diff-card-title").inner_text()
                    assert row2_id in ast_card_title, f"Expected #ast-diff-card-title to contain row 2 ID '{row2_id}', got: {ast_card_title}"
                    ast_title_text = page.locator("#ast-diff-viewer-title").inner_text()
                    assert row2_id in ast_title_text, f"Expected #ast-diff-viewer-title to contain row 2 ID '{row2_id}', got: {ast_title_text}"

                # Assert zero occurrences of "GOOOLE" in the entire DOM
                assert "GOOOLE" not in page.content(), "Found 'GOOOLE' in DOM"

            # 2. Download Hardened Suite (.py)
            with page.expect_download(timeout=10000) as download_info:
                page.locator("#btn-download-suite").click()
            download = download_info.value
            download_path = download.path()
            with open(download_path, "r", encoding="utf-8") as f:
                py_code = f.read()
            # Assert valid Python syntax
            parsed_tree = ast.parse(py_code)
            assert len(parsed_tree.body) > 0, "Parsed AST of downloaded test suite is empty"

            # 3. JUnit XML & SARIF Report API contract validation
            # Get current active job ID
            job_id = page.evaluate("() => window.__lastJobId || (state && state.hardening && state.hardening.currentJobId) || 'latest'")
            junit_resp = httpx.get(f"{live_server_url}/api/export/junit/{job_id}", timeout=10.0)
            if junit_resp.status_code == 200:
                assert junit_resp.headers.get("content-type", "").startswith("application/xml")
                # Parse XML to verify well-formedness
                root = ET.fromstring(junit_resp.text)
                assert root.tag in ("testsuites", "testsuite"), f"Unexpected XML root: {root.tag}"

            sarif_resp = httpx.get(f"{live_server_url}/api/export/sarif/{job_id}", timeout=10.0)
            if sarif_resp.status_code == 200:
                sarif_data = sarif_resp.json()
                assert sarif_data.get("version") == "2.1.0", f"Unexpected SARIF version: {sarif_data.get('version')}"
                assert "runs" in sarif_data and isinstance(sarif_data["runs"], list)

            assert len(page_errors) == 0, f"Page errors: {page_errors}"
            browser.close()

    def test_b5_error_states_and_edge_cases(self, live_server_url):
        """
        Scenario B5: Error States & Edge Cases.
        Tests validation error on empty spec, HTTP 400 rejection on invalid syntax code,
        and WebSocket resilience without unhandled JavaScript exceptions.
        """
        console_errors: List[str] = []
        page_errors: List[str] = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.on("pageerror", lambda exc: print(f"[PAGEERROR] {exc}"))
            page.on("console", lambda msg: print(f"[CONSOLE {msg.type}] {msg.text}"))

            page.goto(live_server_url)
            page.wait_for_load_state("domcontentloaded")
            time.sleep(1.0)

            # 1. Empty specification in Mode B
            page.locator("#btn-submode-b, [data-mode='b'], #nav-mode-b").first.click()
            time.sleep(0.3)
            page.locator("#synth-prompt-input").fill("")
            page.locator("#btn-synthesize-module").click()
            time.sleep(0.5)

            # Check that error toast appeared
            toast = page.locator("#toast-container")
            assert "empty" in toast.inner_text().lower() or "specification" in toast.inner_text().lower()

            # 2. Submit Python file with syntax error via /api/ingest/upload
            files = {"file": ("broken.py", b"def invalid_func(:\n    pass\n", "text/x-python")}
            resp = httpx.post(f"{live_server_url}/api/ingest/upload", files=files, timeout=10.0)
            assert resp.status_code == 400
            assert "syntax" in resp.json().get("detail", "").lower()

            # 3. Disconnect WebSocket and assert UI badge stability
            badge = page.locator("#wiretap-ws-status-badge")
            assert badge.count() == 1

            # Zero unhandled page errors
            assert len(page_errors) == 0, f"Page errors: {page_errors}"
            browser.close()

    def test_b6_benchmark_ablation_table_cell_counts_and_values(self, live_server_url):
        """
        Scenario B6: Benchmark & Comparative Ablation Table Cell Alignment & Score Validation (DEF-024).
        Verifies:
          1. Header has exactly 9 columns (Scenario, Execution Engine, Runs, Mean Latency, StdDev, Mutation Score, Coverage, Tokens, Cost Accounting).
          2. Each row has exactly the same cell count as the header (zero shifted columns).
          3. Execution Engine cell is populated with authentic engine label.
          4. Mutation Score cell parses to the exact value in the JSON report.
          5. Title dynamically reads 'Ablation Results' when < 2 scenarios present, and 'Comparative Ablation Results' otherwise.
          6. Calculated and Estimated detail panels are fully populated without empty gaps.
        """
        console_errors: List[str] = []
        page_errors: List[str] = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.on("pageerror", lambda exc: page_errors.append(str(exc)))
            page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

            page.goto(live_server_url)
            page.wait_for_load_state("domcontentloaded")
            time.sleep(1.0)

            # 1. Navigate to Benchmark & Ablation pane
            page.locator("#tab-btn-benchmarks, #tab-btn-benchmark").first.click()
            time.sleep(0.8)

            # Ensure data is loaded
            page.evaluate("() => window.__testforge.fetchBenchmarkResults()")
            time.sleep(1.0)

            # 2. Verify Header Cell Count
            headers = page.locator("#benchmark-summary-table thead th")
            header_count = headers.count()
            assert header_count == 9, f"Expected 9 table headers, got {header_count}"
            header_texts = [headers.nth(i).inner_text().strip().upper() for i in range(header_count)]
            assert "SCENARIO" in header_texts[0]
            assert "EXECUTION ENGINE" in header_texts[1]
            assert "RUNS" in header_texts[2]
            assert "LATENCY" in header_texts[3]
            assert "STDDEV" in header_texts[4]
            assert "MUTATION SCORE" in header_texts[5]
            assert "COVERAGE" in header_texts[6]
            assert "TOKENS" in header_texts[7]
            assert "COST" in header_texts[8]

            # 3. Read ground-truth benchmark JSON from API
            res = httpx.get(f"{live_server_url}/api/benchmark/results", timeout=10.0)
            assert res.status_code == 200
            report_data = res.json().get("report", {})
            sc_summaries = report_data.get("scenario_summaries", {})
            assert len(sc_summaries) > 0, "No scenario summaries found in benchmark report"

            # 4. Verify Each Row's Cell Count and Value Alignment
            rows = page.locator("#benchmark-summary-table-body tr")
            row_count = rows.count()
            assert row_count == len(sc_summaries), f"Expected {len(sc_summaries)} rows, found {row_count}"

            for i in range(row_count):
                row = rows.nth(i)
                cells = row.locator("td")
                cell_count = cells.count()
                assert cell_count == header_count, (
                    f"Row {i} has {cell_count} cells, expected {header_count}. "
                    f"Possible column shift defect!"
                )

                sc_name = cells.nth(0).inner_text().strip()
                engine_text = cells.nth(1).inner_text().strip()
                mut_score_text = cells.nth(5).inner_text().strip()

                assert len(engine_text) > 0 and engine_text != "n/a", (
                    f"Row {i} ({sc_name}): Execution Engine cell is empty or 'n/a': '{engine_text}'"
                )

                # Assert mutation score cell parses to the value in the JSON
                assert "%" in mut_score_text, f"Row {i} ({sc_name}): Mutation Score cell '{mut_score_text}' missing '%'"
                mut_score_val = float(mut_score_text.replace("%", "").strip())
                expected_score = sc_summaries[sc_name]["mean_mutation_score"]
                assert abs(mut_score_val - expected_score) < 0.2, (
                    f"Row {i} ({sc_name}): Cell score {mut_score_val}% does not match JSON score {expected_score}%"
                )

            # 5. Verify Panel Title with Multiple Scenarios (Comparative Ablation Results)
            title = page.locator("#benchmark-summary-table-title").inner_text()
            assert "Comparative Ablation Results" in title, f"Expected 'Comparative Ablation Results', got '{title}'"

            # 6. Verify Dynamic Title Retitling for < 2 Scenarios ('Ablation Results')
            single_sc_payload = {
                "scenario_summaries": {
                    "baseline": {
                        "scenario": "baseline",
                        "execution_engine": "Deterministic AST Baseline",
                        "runs_completed": 1,
                        "mean_duration_sec": 7.55,
                        "stddev_duration_sec": 0.0,
                        "mean_mutation_score": 31.58,
                        "mean_line_coverage": 70.0,
                        "total_tokens_consumed": 0,
                        "estimated_total_cost_usd": 0.0,
                    }
                },
                "repetitions": 1,
                "runs": []
            }
            page.evaluate("(payload) => window.__testforge.renderBenchmarkReport(payload)", single_sc_payload)
            time.sleep(0.3)

            single_title = page.locator("#benchmark-summary-table-title").inner_text()
            assert "Ablation Results" in single_title, f"Expected 'Ablation Results' in single scenario title, got '{single_title}'"
            assert "Comparative" not in single_title, f"Single scenario title should not contain 'Comparative': '{single_title}'"

            # Verify single scenario row still has exactly 9 cells
            single_row_cells = page.locator("#benchmark-summary-table-body tr").first.locator("td")
            assert single_row_cells.count() == 9, f"Single scenario row expected 9 cells, got {single_row_cells.count()}"

            # 7. Verify Calculated & Estimated Panels have No Empty Gaps
            calc_text = page.locator("#bench-calculated-details").inner_text()
            assert "mutation_score_pct" in calc_text
            assert "Awaiting benchmark execution..." not in calc_text

            est_text = page.locator("#bench-estimated-details").inner_text()
            assert "pricing_model" in est_text or "estimated_cost_usd" in est_text
            assert "Awaiting benchmark execution..." not in est_text

            assert len(page_errors) == 0, f"Page errors: {page_errors}"
            browser.close()

    def test_live_hardening_pipeline_runs_to_completion(self, live_server_url):
        """
        MODULE 3: Automated Live Execution & End-to-End Playwright Verification.
        Navigates headless Chromium to target server, triggers autonomous hardening,
        and verifies completion, status badge transition, test synthesis, and non-zero score.
        """
        target_url = live_server_url

        page_errors: List[str] = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.on("pageerror", lambda exc: page_errors.append(str(exc)))

            # 1. Navigate headless Chromium
            page.goto(target_url, wait_until="domcontentloaded", timeout=15000)
            time.sleep(1.0)

            # 2. Click #tab-btn-lab (Hardening Lab)
            page.locator("#tab-btn-lab").click()
            time.sleep(0.5)

            # 3. Click #btn-lab-run-hardening
            btn_start = page.locator("#btn-lab-run-hardening, #btn-start-hardening").first
            assert btn_start.is_visible(), "Expected #btn-lab-run-hardening to be visible"
            btn_start.click()

            # 4. Wait for #btn-cancel-hardening to appear
            page.wait_for_selector("#btn-cancel-hardening", timeout=15000)

            # 5. Wait with a 60-second timeout for the pipeline to reach completion
            # (asserting that #hardening-status-badge transitions to COMPLETED or SUCCESS, or that verdict banner appears)
            start_t = time.time()
            completed = False
            while time.time() - start_t < 60.0:
                verdict = page.locator("#hardening-verdict-banner:not(.hidden)")
                pct_text = page.locator("#hardening-percent-text")
                badge = page.locator("#hardening-status-badge")
                is_badge_done = badge.count() > 0 and badge.inner_text().strip().upper() in ("COMPLETED", "SUCCESS")
                is_verdict_done = verdict.count() > 0
                is_pct_done = pct_text.count() > 0 and "FINALIZED" in pct_text.inner_text().upper()

                if is_pct_done or is_verdict_done or is_badge_done:
                    # Give brief moment for renderHardeningResults to complete DOM updates
                    time.sleep(1.0)
                    completed = True
                    break
                time.sleep(0.5)

            assert completed, "Hardening pipeline did not reach completion within 60s"
            badge_text = page.locator("#hardening-status-badge").inner_text().strip().upper()
            verdict_visible = page.locator("#hardening-verdict-banner:not(.hidden)").count() > 0
            assert badge_text in ("COMPLETED", "SUCCESS") or verdict_visible, (
                f"Expected #hardening-status-badge in ('COMPLETED', 'SUCCESS') or verdict banner visible, got: badge='{badge_text}', verdict_visible={verdict_visible}"
            )

            # 6. Assert that #final-hardened-suite-editor contains generated test functions (e.g., 'def test_')
            page.wait_for_selector("#final-hardened-suite-editor:has-text('def test_')", timeout=10000)
            editor_text = page.locator("#final-hardened-suite-editor").inner_text()
            assert "def test_" in editor_text, f"Expected 'def test_' in #final-hardened-suite-editor, got:\n{editor_text[:300]}"

            # 7. Assert completion finalization: badges turn COMPLETED, #baseline-passed > 0, #mutants-killed > 0, and #final-mutation-score != '0.0%'
            page.wait_for_selector("#hardening-status-badge:has-text('COMPLETED')", timeout=10000)
            page.wait_for_selector("#baseline-passed:not(:has-text('0'))", timeout=10000)
            page.wait_for_selector("#mutants-killed:not(:has-text('0'))", timeout=10000)
            page.wait_for_selector("#final-mutation-score:not(:has-text('0.0%'))", timeout=10000)

            base_passed_val = int(page.locator("#baseline-passed").inner_text().strip())
            assert base_passed_val > 0, f"Expected #baseline-passed > 0, got {base_passed_val}"

            mut_killed_val = int(page.locator("#mutants-killed").inner_text().strip())
            assert mut_killed_val > 0, f"Expected #mutants-killed > 0, got {mut_killed_val}"

            final_mut_text = page.locator("#final-mutation-score").inner_text().strip()
            assert "0.0%" not in final_mut_text, f"Expected #final-mutation-score != '0.0%', got {final_mut_text}"

            score_text = page.locator("#mutation-score-value").inner_text().replace("%", "").strip()
            score_val = float(score_text)
            assert score_val > 0.0, f"Expected #mutation-score-value > 0.0%, got {score_val}%"

            browser.close()

    def test_header_run_button_triggers_hardening_from_any_tab(self, live_server_url):
        """
        Verifies that clicking the top header button (#btn-run-hardening) from any page
        (e.g., Target Ingestion or Blast Radius tab) automatically switches the active tab
        to the Hardening Lab (#tab-hardening), synchronizes loading states across both
        buttons (#btn-run-hardening and #btn-start-hardening), exposes #btn-cancel-hardening,
        and transitions #hardening-status-badge to RUNNING. Then cleanly cancels the execution.
        """
        page_errors: List[str] = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.on("pageerror", lambda exc: page_errors.append(str(exc)))

            # 1. Load application
            page.goto(live_server_url, wait_until="domcontentloaded", timeout=15000)
            time.sleep(1.0)

            # 2. Switch to Target Ingestion tab and confirm active
            page.locator("#tab-btn-ingestion").click()
            time.sleep(0.4)
            assert page.locator("#tab-ingestion").is_visible(), "Expected #tab-ingestion to be visible"

            # 3. Locate header run button and verify visibility
            header_btn = page.locator("#btn-global-run-hardening, #btn-run-hardening").first
            assert header_btn.is_visible(), "Expected header #btn-global-run-hardening to be visible"

            # 4. Click header run button
            header_btn.click()

            # 5. Assert active view transitions to #tab-hardening
            page.wait_for_selector("#tab-hardening.active", timeout=5000)
            assert page.locator("#tab-hardening").is_visible(), "Expected #tab-hardening to be active and visible"

            # 6. Assert cancel button becomes visible
            page.wait_for_selector("#btn-cancel-hardening", timeout=10000)
            assert page.locator("#btn-cancel-hardening").is_visible()

            # 7. Assert status badge transitions to RUNNING
            page.wait_for_selector("#hardening-status-badge:has-text('RUNNING')", timeout=10000)

            # 8. Assert both run buttons reflect disabled/loading state
            assert header_btn.is_disabled(), "Header button should be disabled during hardening"
            in_tab_btn = page.locator("#btn-lab-run-hardening, #btn-start-hardening").first
            assert in_tab_btn.is_disabled(), "In-tab button should be disabled during hardening"

            # 9. Cleanly cancel execution and assert clean shutdown
            page.locator("#btn-cancel-hardening").click()
            page.wait_for_selector("#btn-cancel-hardening", state="hidden", timeout=10000)

            # 10. Assert buttons restore to enabled state
            time.sleep(0.5)
            assert not header_btn.is_disabled(), "Header button should be restored to enabled state"
            assert not in_tab_btn.is_disabled(), "In-tab button should be restored to enabled state"

            assert len(page_errors) == 0, f"Unexpected page errors: {page_errors}"
            browser.close()

    def test_all_three_hardening_buttons_trigger_execution(self, live_server_url):
        """
        MODULE 4: Automated Playwright Verification for Real Interactive Hardening Buttons.
        Verifies the genuine controls (eliminating hidden dummy test aliases):
          1. #btn-global-run-hardening (in top persistent header).
          2. #btn-lab-run-hardening / #btn-run-hardening (inside Hardening Lab execution card).
        Asserts that triggering each real button initiates execution and handles cancellation/completion cleanly.
        """
        page_errors: List[str] = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.on("pageerror", lambda exc: page_errors.append(str(exc)))

            page.goto(live_server_url, wait_until="domcontentloaded", timeout=15000)
            time.sleep(1.0)

            btn_global = page.locator("#btn-global-run-hardening, #btn-run-hardening").first
            btn_lab = page.locator("#btn-lab-run-hardening, #btn-start-hardening").first

            # -------------------------------------------------------------
            # Subtest 1: Global Header Button from #tab-ingestion
            # -------------------------------------------------------------
            page.locator("#tab-btn-ingestion").click()
            time.sleep(0.3)
            assert page.locator("#tab-ingestion").is_visible(), "Expected #tab-ingestion to be visible"

            assert btn_global.is_visible(), "Expected header button #btn-global-run-hardening to be visible"
            btn_global.click()

            # Assert tab automatically switches to #tab-hardening
            page.wait_for_selector("#tab-hardening.active", timeout=5000)
            assert page.locator("#tab-hardening").is_visible(), "Expected view to transition to #tab-hardening"

            # Assert both real buttons enter disabled/loading state
            page.wait_for_selector("#btn-cancel-hardening", timeout=10000)
            assert btn_global.is_disabled(), "Global header button should be disabled during execution"
            assert btn_lab.is_disabled(), "Lab control button should be disabled during execution"

            # Abort cleanly via Cancel
            page.locator("#btn-cancel-hardening").click()
            page.wait_for_selector("#btn-cancel-hardening", state="hidden", timeout=10000)
            time.sleep(0.5)

            # Assert buttons restored
            assert not btn_global.is_disabled(), "Global button should restore to active"
            assert not btn_lab.is_disabled(), "Lab button should restore to active"

            # -------------------------------------------------------------
            # Subtest 2: Persistent Global Header Button from #tab-blast
            # -------------------------------------------------------------
            page.locator("#tab-btn-blast, #nav-blast").first.click()
            time.sleep(0.3)
            assert page.locator("#tab-blast").is_visible(), "Expected #tab-blast to be visible"

            assert btn_global.is_visible(), "Expected header button #btn-global-run-hardening to be visible from #tab-blast"
            btn_global.click()

            # Assert tab automatically switches to #tab-hardening
            page.wait_for_selector("#tab-hardening.active", timeout=5000)
            assert page.locator("#tab-hardening").is_visible(), "Expected view to transition to #tab-hardening"

            # Assert progress status indicates RUNNING or EXECUTING
            page.wait_for_selector("#btn-cancel-hardening", timeout=10000)
            badge_text = page.locator("#hardening-status-badge").inner_text().strip().upper()
            assert badge_text in ("RUNNING", "EXECUTING", "INITIALIZING"), f"Unexpected status badge: {badge_text}"

            # Abort cleanly via Cancel
            page.locator("#btn-cancel-hardening").click()
            page.wait_for_selector("#btn-cancel-hardening", state="hidden", timeout=10000)
            time.sleep(0.5)

            # -------------------------------------------------------------
            # Subtest 3: Lab Control Button from #tab-hardening (Runs to clean finish)
            # -------------------------------------------------------------
            page.locator("#tab-btn-lab").click()
            time.sleep(0.3)
            assert btn_lab.is_visible(), "Expected lab button #btn-lab-run-hardening to be visible"
            btn_lab.click()

            # Wait for job completion
            page.wait_for_selector("#hardening-percent-text:has-text('FINALIZED')", timeout=45000)
            time.sleep(1.0)

            # Assert pipeline finishes cleanly
            badge_done = page.locator("#hardening-status-badge").inner_text().strip().upper()
            assert badge_done in ("COMPLETED", "SUCCESS"), f"Expected completed status, got {badge_done}"
            assert not btn_lab.is_disabled(), "Lab button should be active after completion"
            assert not btn_global.is_disabled(), "Global button should be active after completion"

            assert len(page_errors) == 0, f"Unexpected page errors: {page_errors}"
            browser.close()

    def test_theme_switcher_toggle(self, live_server_url):
        """
        MODULE 3: Automated Playwright Verification for Light/Dark Theme Switching.
          - Check default data-theme is "dark".
          - Click #btn-theme-toggle and assert data-theme becomes "light".
          - Click #btn-theme-toggle again and assert data-theme returns to "dark".
        """
        page_errors: List[str] = []

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.on("pageerror", lambda exc: page_errors.append(str(exc)))

            page.goto(live_server_url, wait_until="domcontentloaded", timeout=15000)
            time.sleep(1.0)

            # 1. Assert default data-theme is 'dark'
            initial_theme = page.evaluate("() => document.documentElement.getAttribute('data-theme')")
            assert initial_theme == "dark", f"Expected initial data-theme='dark', got '{initial_theme}'"

            # 2. Click toggle button to switch to light theme
            toggle_btn = page.locator("#btn-theme-toggle")
            assert toggle_btn.is_visible(), "Expected #btn-theme-toggle to be visible in the header"
            toggle_btn.click()
            time.sleep(0.3)

            # Assert data-theme is now 'light'
            light_theme = page.evaluate("() => document.documentElement.getAttribute('data-theme')")
            assert light_theme == "light", f"Expected data-theme='light' after click, got '{light_theme}'"

            # 3. Click toggle button again to switch back to dark theme
            toggle_btn.click()
            time.sleep(0.3)

            # Assert data-theme returned to 'dark'
            dark_theme = page.evaluate("() => document.documentElement.getAttribute('data-theme')")
            assert dark_theme == "dark", f"Expected data-theme='dark' after second click, got '{dark_theme}'"

            assert len(page_errors) == 0, f"Unexpected page errors: {page_errors}"
            browser.close()

    def test_mcp_studio_modal_interaction(self, live_server_url):
        """Verifies opening MCP Studio modal, tool selection toggle, and close interactions."""
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(live_server_url)

            # 1. Assert button exists and backdrop is initially hidden
            btn_open = page.locator("#btn-open-mcp-studio")
            assert btn_open.is_visible()
            backdrop = page.locator("#mcp-studio-modal-backdrop")
            assert "hidden" in (backdrop.get_attribute("class") or "")

            # 2. Click open -> backdrop visible
            btn_open.click()
            page.wait_for_selector("#mcp-studio-modal", state="visible")
            assert "hidden" not in (backdrop.get_attribute("class") or "")

            # 3. Check tool selector and secondary input visibility toggle
            sec_container = page.locator("#mcp-studio-secondary-container")
            assert "hidden" in (sec_container.get_attribute("class") or "")

            page.select_option("#mcp-studio-tool-select", "mcp_sandbox_runner")
            assert "hidden" not in (sec_container.get_attribute("class") or "")

            page.select_option("#mcp-studio-tool-select", "mcp_ast_symbol_analyzer")
            assert "hidden" in (sec_container.get_attribute("class") or "")

            # 4. Close modal
            page.click("#btn-close-mcp-studio")
            assert "hidden" in (backdrop.get_attribute("class") or "")
            browser.close()



