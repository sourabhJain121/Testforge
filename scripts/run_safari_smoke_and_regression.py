import os
import sys
import time
import shutil
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

OUTPUT_DIR = Path("/tmp/testforge_safari_audit")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

ARTIFACT_DIR = Path("/Users/sourabh/.gemini/antigravity/brain/ad3919fc-7c4f-4e08-af89-e520bbc7c86c")

def run_safari_smoke_test():
    print("=== Starting Comprehensive Safari Engine (WebKit) Smoke Test ===")
    base_url = "http://127.0.0.1:8000"
    
    issues_found = []
    console_errors = []
    page_errors = []
    failed_requests = []

    with sync_playwright() as p:
        print("Launching WebKit (Safari engine) at 1440x900...")
        browser = p.webkit.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        page.on("pageerror", lambda exc: page_errors.append(str(exc)))
        page.on("console", lambda msg: console_errors.append(f"[{msg.type}] {msg.text}") if msg.type == "error" else None)
        
        def handle_response(resp):
            if resp.status >= 400 and "/api/checkpoints/diff" not in resp.url and "/api/status" not in resp.url:
                failed_requests.append(f"{resp.status} {resp.url}")
        page.on("response", handle_response)

        # Helper functions
        def set_theme(theme: str):
            page.evaluate(f"document.documentElement.setAttribute('data-theme', '{theme}')")
            time.sleep(0.4)

        def snap(filename: str):
            path = OUTPUT_DIR / filename
            page.screenshot(path=str(path), full_page=False)
            dest_artifact = ARTIFACT_DIR / filename
            shutil.copy2(path, dest_artifact)
            print(f"Captured: {filename}")

        # Sequence 1: Boot and Ingest Code File
        print("\n--- Sequence 1: Ingest Code File (Tab 1) ---")
        page.goto(base_url)
        page.wait_for_load_state("domcontentloaded")
        time.sleep(1.5)

        # Verify Tab 1 button active
        page.locator("#tab-btn-ingestion").click()
        time.sleep(0.5)

        # Select discount.py and click Load Sample
        target_select = page.locator("#target-select")
        if target_select.count() > 0:
            target_select.select_option("discount.py")
            page.locator("#btn-load-sample").click()
            time.sleep(1.2)

        # Check AST Inspection Box
        ast_code = page.locator("#mode-a-code-display, #code-viewer, .code-viewer-container").first.inner_text()
        if "def calculate_discount" not in ast_code:
            issues_found.append("Tab 1: AST Code viewer did not display calculate_discount source code")

        # Capture Tab 1 in Dark & Light
        set_theme("dark")
        snap("safari_01_dark_ingestion.png")
        set_theme("light")
        snap("01_light_ingestion_safari.png")

        # Sequence 2: Move to Blast Radius & Call Graph (Tab 2)
        print("\n--- Sequence 2: Blast Radius & Call Graph (Tab 2) ---")
        page.locator("#tab-btn-blast").click()
        time.sleep(1.0)
        
        # Verify Call Graph elements
        blast_text = page.locator("#tab-blast").inner_text()
        if "calculate_discount" not in blast_text:
            issues_found.append("Tab 2: Blast Radius call graph does not list calculate_discount")
        if "round" not in blast_text:
            issues_found.append("Tab 2: Blast Radius call graph missing callee 'round'")

        set_theme("dark")
        snap("safari_02_dark_blast_radius.png")
        set_theme("light")
        snap("02_light_blast_radius_safari.png")

        # Sequence 3: Move to Hardening Lab & Results (Tab 3)
        print("\n--- Sequence 3: Hardening Lab & Results (Tab 3) ---")
        page.locator("#tab-btn-lab").click()
        time.sleep(0.6)

        # Click Run Hardening
        print("Triggering hardening pipeline via #btn-lab-run-hardening...")
        run_btn = page.locator("#btn-lab-run-hardening, #btn-start-hardening, #btn-global-run-hardening").first
        run_btn.click()

        # Wait for hardening completion
        print("Waiting for pipeline convergence (max 180s)...")
        start_t = time.time()
        completed = False
        while time.time() - start_t < 180.0:
            verdict = page.locator("#hardening-verdict-banner:not(.hidden)")
            pct_text = page.locator("#hardening-percent-text")
            badge = page.locator("#hardening-status-badge")
            is_badge_done = badge.count() > 0 and badge.inner_text().strip().upper() in ("COMPLETED", "SUCCESS")
            is_verdict_done = verdict.count() > 0
            is_pct_done = pct_text.count() > 0 and "FINALIZED" in pct_text.inner_text().upper()

            if is_pct_done or is_verdict_done or is_badge_done:
                time.sleep(1.5)
                completed = True
                print("Pipeline convergence confirmed!")
                break
            time.sleep(1.0)

        if not completed:
            issues_found.append("Tab 3: Hardening pipeline did not complete within 90s")

        # Verify generated test suite editor
        suite_editor = page.locator("#final-hardened-suite-editor").inner_text()
        if "def test_" not in suite_editor:
            issues_found.append("Tab 3: Final hardened suite editor does not contain synthesized 'def test_' functions")

        # Exercise Load Benchmark Summary + Minimize Suite
        if page.locator("#btn-load-minimizer-summary").is_visible():
            print("Clicking Load Benchmark Summary...")
            page.locator("#btn-load-minimizer-summary").click()
            time.sleep(1.0)
        if page.locator("#btn-run-minimizer").is_visible():
            print("Clicking Minimize Suite...")
            page.locator("#btn-run-minimizer").click()
            time.sleep(1.0)

        # Verify Set Cover Minimal Tests
        retained_chips = page.locator("#minimizer-retained-list .badge, #minimizer-retained-list span, #retained-minimal-tests-container .chip, #retained-minimal-tests-container span")
        print(f"Retained minimal test chips: {retained_chips.count()}")
        if retained_chips.count() == 0:
            issues_found.append("Tab 3: Retained minimal tests chips are empty after minimization")

        set_theme("dark")
        snap("safari_03_dark_hardening.png")
        set_theme("light")
        snap("03_light_hardening_safari.png")

        # Sequence 4: Move to Multi-Agent Wiretap (Tab 4)
        print("\n--- Sequence 4: Multi-Agent Wiretap (Tab 4) ---")
        page.locator("#tab-btn-wiretap").click()
        time.sleep(1.0)

        # Verify 8 Agents
        agent_cards = page.locator(".agent-topo-card")
        print(f"Agent topology cards found: {agent_cards.count()}")
        if agent_cards.count() != 8:
            issues_found.append(f"Tab 4: Expected 8 agent topology cards, found {agent_cards.count()}")

        # Verify heading text visibility in light mode
        set_theme("light")
        heading_color = page.evaluate("() => window.getComputedStyle(document.getElementById('wiretap-topology-heading')).color")
        print(f"Light mode wiretap heading computed color: {heading_color}")

        # Expand contract payload
        first_details = page.locator("details.payload-details summary").first
        if first_details.count() > 0:
            first_details.click()
            time.sleep(0.3)

        snap("04_light_wiretap_safari.png")
        set_theme("dark")
        snap("safari_04_dark_wiretap.png")

        # Sequence 5: Move to Observability Trace (Tab 5)
        print("\n--- Sequence 5: Observability Trace (Tab 5) ---")
        page.locator("#tab-btn-observability").click()
        time.sleep(0.8)

        if page.locator("#btn-refresh-telemetry").is_visible():
            page.locator("#btn-refresh-telemetry").click()
            time.sleep(0.4)
        if page.locator("#btn-refresh-otel-spans").is_visible():
            page.locator("#btn-refresh-otel-spans").click()
            time.sleep(0.4)
        if page.locator("#btn-refresh-supervisor-decisions").is_visible():
            page.locator("#btn-refresh-supervisor-decisions").click()
            time.sleep(0.4)

        # Verify telemetry table
        telemetry_rows = page.locator("#telemetry-table-body tr")
        print(f"Telemetry table rows: {telemetry_rows.count()}")

        set_theme("dark")
        snap("safari_05_dark_telemetry.png")
        set_theme("light")
        snap("05_light_telemetry_safari.png")

        # Sequence 6: Move to Benchmarks & Ablation (Tab 6)
        print("\n--- Sequence 6: Benchmarks & Ablation (Tab 6) ---")
        page.locator("#tab-btn-benchmarks").click()
        time.sleep(1.0)

        if page.locator("#btn-refresh-multi-benchmark").is_visible():
            page.locator("#btn-refresh-multi-benchmark").click()
            time.sleep(0.8)

        bench_body = page.locator("#multi-target-benchmark-table-body").inner_text()
        if "discount.py" not in bench_body:
            issues_found.append("Tab 6: Empirical multi-target table missing discount.py")

        set_theme("dark")
        snap("safari_06_dark_benchmark.png")
        set_theme("light")
        snap("06_light_benchmark_safari.png")

        # Sequence 7: Move to Checkpoints (Tab 7)
        print("\n--- Sequence 7: Checkpoints (Tab 7) ---")
        page.locator("#tab-btn-checkpoints").click()
        time.sleep(1.0)

        if page.locator("#btn-refresh-checkpoints").is_visible():
            page.locator("#btn-refresh-checkpoints").click()
            time.sleep(0.5)

        cp_rows = page.locator("#cp-history-list .checkpoint-card, #cp-history-list .checkpoint-row, #cp-history-list > div")
        print(f"Checkpoints listed: {cp_rows.count()}")
        if cp_rows.count() > 0:
            cp_rows.first.click()
            time.sleep(0.5)

        set_theme("dark")
        snap("safari_07_dark_checkpoints.png")
        set_theme("light")
        snap("07_light_checkpoints_safari.png")

        # Sequence 8: Modals Audit
        print("\n--- Sequence 8: Modals Audit ---")
        # Settings Modal
        page.locator("#btn-toggle-settings").click()
        time.sleep(0.5)
        set_theme("dark")
        snap("safari_08_dark_modal_settings.png")
        set_theme("light")
        snap("08_light_modal_settings_safari.png")
        page.locator("#btn-close-settings, #btn-cancel-settings").first.click()
        time.sleep(0.4)

        # A2A Card Modal
        set_theme("dark")
        if page.locator("#btn-a2a-card").is_visible():
            page.locator("#btn-a2a-card").click()
            time.sleep(0.5)
            snap("safari_09_dark_modal_a2a.png")
            page.locator("#btn-close-a2a-modal, #btn-close-a2a-footer").first.click()
            time.sleep(0.4)

        # FastMCP Tools Modal
        if page.locator("#btn-mcp-status").is_visible():
            page.locator("#btn-mcp-status").click()
            time.sleep(0.5)
            snap("safari_10_dark_modal_mcp_tools.png")
            page.locator("#btn-close-mcp-modal, #btn-close-mcp-footer").first.click()
            time.sleep(0.4)

        # FastMCP Studio Modal
        if page.locator("#btn-open-mcp-studio").is_visible():
            page.locator("#btn-open-mcp-studio").click()
            time.sleep(0.5)
            snap("safari_11_dark_modal_mcp_studio.png")
            page.locator("#btn-close-mcp-studio, #btn-mcp-studio-footer-close").first.click()
            time.sleep(0.4)

        # Mutant Diff Modal
        page.locator("#tab-btn-lab").click()
        time.sleep(0.5)
        if page.locator("#btn-open-mutant-diff-modal").is_visible():
            page.locator("#btn-open-mutant-diff-modal").click()
            time.sleep(0.6)
            set_theme("dark")
            snap("safari_12_dark_modal_mutant_diff.png")
            set_theme("light")
            snap("12_light_modal_mutant_diff_safari.png")
            page.locator("#btn-close-mutant-diff-modal, #btn-close-mutant-diff-footer").first.click()
            time.sleep(0.4)

        browser.close()

    print("\n=== Safari Engine Smoke Test Results ===")
    print(f"Console Errors: {len(console_errors)}")
    for c in console_errors:
        print(f"  Console: {c}")
    print(f"Page Errors: {len(page_errors)}")
    for pe in page_errors:
        print(f"  Page: {pe}")
    print(f"Failed HTTP Requests: {len(failed_requests)}")
    for fr in failed_requests:
        print(f"  HTTP: {fr}")
    print(f"Functional/UI Issues Logged: {len(issues_found)}")
    for iss in issues_found:
        print(f"  Issue: {iss}")

    report = {
        "console_errors": console_errors,
        "page_errors": page_errors,
        "failed_requests": failed_requests,
        "issues_found": issues_found
    }
    with open(OUTPUT_DIR / "smoke_test_report.json", "w") as f:
        json.dump(report, f, indent=2)

if __name__ == "__main__":
    run_safari_smoke_test()
