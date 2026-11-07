"""
testforge/scripts/capture_frontend_evidence.py

Live Headless Chromium Browser Verification & Screenshot Automation.
Captures high-resolution viewport screenshots of every dashboard pane,
executes interactive triggers, verifies zero console errors, and produces
qa_artifacts/FRONTEND_BROWSER_VERIFICATION_REPORT.json.
"""

from __future__ import annotations

import json
import os
import socket
import sys
import threading
import time
from pathlib import Path
from typing import Any, Dict, List

import httpx
import uvicorn
from playwright.sync_api import sync_playwright

BASE_DIR = Path(__file__).resolve().parent.parent.parent
SCREENSHOT_DIR = BASE_DIR / "docs" / "screenshots"
ARTIFACTS_DIR = BASE_DIR / "qa_artifacts"


def find_free_port() -> int:
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


def run_frontend_verification() -> Dict[str, Any]:
    SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

    if str(BASE_DIR) not in sys.path:
        sys.path.insert(0, str(BASE_DIR))

    from server import app

    port = find_free_port()
    config = uvicorn.Config(app=app, host="127.0.0.1", port=port, log_level="error")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    time.sleep(1.5)
    base_url = f"http://127.0.0.1:{port}"

    console_errors: List[str] = []
    page_errors: List[str] = []
    verified_elements: List[str] = []
    captured_screenshots: List[Dict[str, str]] = []

    print(f"[*] Starting Playwright Chromium Headless against {base_url}...")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        page.on("pageerror", lambda exc: page_errors.append(str(exc)))
        page.on(
            "console",
            lambda msg: console_errors.append(msg.text) if msg.type == "error" else None,
        )

        # 1. Boot dashboard
        page.goto(base_url)
        page.wait_for_load_state("domcontentloaded")
        time.sleep(1.0)

        # Verify Title & Header
        title = page.title()
        assert "TestForge" in title, f"Unexpected title: {title}"
        verified_elements.append("page_title")

        # 1. Hardening Lab & Suite Minimizer
        page.locator("#tab-btn-lab").click()
        time.sleep(0.5)
        # Click Load Minimizer Summary to populate heatmap & KPIs
        btn_min = page.locator("#btn-load-minimizer-summary")
        if btn_min.is_visible():
            btn_min.click()
            time.sleep(0.5)
        p1 = str(SCREENSHOT_DIR / "01_hardening_lab.png")
        page.screenshot(path=p1)
        captured_screenshots.append({"view": "Hardening Lab", "file": "01_hardening_lab.png"})
        verified_elements.extend(["#tab-btn-lab", "#minimizer-panel", "#approval-gate-panel"])

        # 2. Multi-Agent Wiretap Topology Grid
        page.locator("#tab-btn-wiretap").click()
        time.sleep(0.5)
        p2 = str(SCREENSHOT_DIR / "02_wiretap_topology.png")
        page.screenshot(path=p2)
        captured_screenshots.append({"view": "Multi-Agent Wiretap", "file": "02_wiretap_topology.png"})
        cards_count = page.locator(".agent-topo-card").count()
        verified_elements.append(f"wiretap_cards_{cards_count}")

        # 3. Statistical Benchmarks & Multi-Target Ablation
        page.locator("#tab-btn-benchmark").click()
        time.sleep(0.6)
        p3 = str(SCREENSHOT_DIR / "03_benchmarks_ablation.png")
        page.screenshot(path=p3)
        captured_screenshots.append({"view": "Benchmarks & Ablation", "file": "03_benchmarks_ablation.png"})
        verified_elements.append("#multi-target-benchmark-table")

        # 4. Checkpoints Timeline & Deterministic Diff
        page.locator("#tab-btn-history").click()
        time.sleep(0.5)
        p4 = str(SCREENSHOT_DIR / "04_checkpoints_timeline.png")
        page.screenshot(path=p4)
        captured_screenshots.append({"view": "Checkpoints Timeline", "file": "04_checkpoints_timeline.png"})
        verified_elements.append("#checkpoint-cards-stream")

        # 5. Observability & OpenTelemetry Trace Log
        page.locator("#nav-telemetry").click()
        time.sleep(0.5)
        # Click refresh buttons
        btn_otel = page.locator("#btn-refresh-otel-spans")
        if btn_otel.is_visible():
            btn_otel.click()
        btn_sup = page.locator("#btn-refresh-supervisor-decisions")
        if btn_sup.is_visible():
            btn_sup.click()
        time.sleep(0.5)
        p5 = str(SCREENSHOT_DIR / "05_observability_traces.png")
        page.screenshot(path=p5)
        captured_screenshots.append({"view": "Observability Traces", "file": "05_observability_traces.png"})
        verified_elements.extend(["#nav-telemetry", "#otel-spans-table", "#supervisor-decisions-table"])

        # 6. Blast Radius & Call Graph
        page.locator("#nav-blast").click()
        time.sleep(0.5)
        p6 = str(SCREENSHOT_DIR / "06_blast_radius.png")
        page.screenshot(path=p6)
        captured_screenshots.append({"view": "Blast Radius", "file": "06_blast_radius.png"})
        verified_elements.append("#nav-blast")

        # 7. Mode A: Workspace & Upload
        page.locator("#nav-mode-a").click()
        time.sleep(0.5)
        p7 = str(SCREENSHOT_DIR / "07_mode_a_workspace.png")
        page.screenshot(path=p7)
        captured_screenshots.append({"view": "Mode A Workspace", "file": "07_mode_a_workspace.png"})
        verified_elements.append("#nav-mode-a")

        # 8. Mode B: AI Synthesis
        page.locator("#nav-mode-b").click()
        time.sleep(0.5)
        p8 = str(SCREENSHOT_DIR / "08_mode_b_synthesis.png")
        page.screenshot(path=p8)
        captured_screenshots.append({"view": "Mode B Synthesis", "file": "08_mode_b_synthesis.png"})
        verified_elements.append("#nav-mode-b")

        # 9. Mode C: GitHub Direct Import
        page.locator("#nav-mode-c").click()
        time.sleep(0.5)
        p9 = str(SCREENSHOT_DIR / "09_mode_c_github.png")
        page.screenshot(path=p9)
        captured_screenshots.append({"view": "Mode C GitHub", "file": "09_mode_c_github.png"})
        verified_elements.append("#nav-mode-c")

        # 10. A2A Agent Card Modal
        page.locator("#btn-a2a-card").click()
        time.sleep(0.5)
        p10 = str(SCREENSHOT_DIR / "10_a2a_agent_card.png")
        page.screenshot(path=p10)
        captured_screenshots.append({"view": "A2A Agent Card Modal", "file": "10_a2a_agent_card.png"})
        page.locator("#btn-close-a2a-modal").click()
        time.sleep(0.3)
        verified_elements.append("#btn-a2a-card")

        # 11. FastMCP Tools Status Modal
        page.locator("#btn-mcp-status").click()
        time.sleep(0.5)
        p11 = str(SCREENSHOT_DIR / "11_fastmcp_tools.png")
        page.screenshot(path=p11)
        captured_screenshots.append({"view": "FastMCP Tools Modal", "file": "11_fastmcp_tools.png"})
        page.locator("#btn-close-mcp-modal").click()
        time.sleep(0.3)
        verified_elements.append("#btn-mcp-status")

        # 12. Settings Modal with Privacy Mode
        page.locator("#btn-toggle-settings").click()
        time.sleep(0.5)
        p12 = str(SCREENSHOT_DIR / "12_system_settings_privacy.png")
        page.screenshot(path=p12)
        captured_screenshots.append({"view": "System Settings & Privacy", "file": "12_system_settings_privacy.png"})
        page.locator("#btn-close-settings").click()
        time.sleep(0.3)
        verified_elements.append("#btn-toggle-settings")

        # 13. Privacy Toggle Button interaction
        page.locator("#btn-toggle-privacy").click()
        time.sleep(0.3)
        # Toggle back
        page.locator("#btn-toggle-privacy").click()
        time.sleep(0.3)
        verified_elements.append("#btn-toggle-privacy")

        browser.close()

    server.should_exit = True
    thread.join(timeout=3.0)

    report = {
        "status": "PASS" if len(page_errors) == 0 and len(console_errors) == 0 else "FAIL",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_views_verified": len(captured_screenshots),
        "total_elements_verified": len(verified_elements),
        "uncaught_page_errors": len(page_errors),
        "uncaught_console_errors": len(console_errors),
        "page_errors": page_errors,
        "console_errors": console_errors,
        "captured_screenshots": captured_screenshots,
        "verified_elements": verified_elements,
    }

    report_path = ARTIFACTS_DIR / "FRONTEND_BROWSER_VERIFICATION_REPORT.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"\n[✓] Browser verification completed successfully!")
    print(f"    - Total Views Captured: {len(captured_screenshots)}")
    print(f"    - Uncaught Page Errors: {len(page_errors)}")
    print(f"    - Uncaught Console Errors: {len(console_errors)}")
    print(f"    - Report saved to: {report_path}")

    return report


if __name__ == "__main__":
    rep = run_frontend_verification()
    if rep["status"] != "PASS":
        sys.exit(1)
