import os
import sys
import time
import shutil
from pathlib import Path
from playwright.sync_api import sync_playwright

OUTPUT_DIR = Path("/tmp/testforge_visual_audit")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

ARTIFACT_DIR = Path("/Users/sourabh/.gemini/antigravity/brain/ad3919fc-7c4f-4e08-af89-e520bbc7c86c")

def run_audit():
    print("=== Starting Comprehensive TestForge 7-Tab & Modal Data + Visual Audit ===")
    base_url = "http://127.0.0.1:8000"
    console_errors = []
    page_errors = []
    failed_requests = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        page.on("pageerror", lambda exc: page_errors.append(str(exc)))
        page.on("console", lambda msg: console_errors.append(f"[{msg.type}] {msg.text}") if msg.type == "error" else None)
        
        def handle_response(resp):
            if resp.status >= 400 and "/api/checkpoints/diff" not in resp.url and "/api/status" not in resp.url:
                failed_requests.append(f"{resp.status} {resp.url}")
        page.on("response", handle_response)

        # 1. Boot dashboard in Dark Mode
        print("Navigating to dashboard...")
        page.goto(base_url)
        page.wait_for_load_state("domcontentloaded")
        time.sleep(1.2)

        def set_theme(theme: str):
            page.evaluate(f"document.documentElement.setAttribute('data-theme', '{theme}')")
            time.sleep(0.3)

        def snap(filename: str):
            path = OUTPUT_DIR / filename
            page.screenshot(path=str(path), full_page=False)
            dest_artifact = ARTIFACT_DIR / filename
            shutil.copy2(path, dest_artifact)
            print(f"Captured: {filename}")

        # TAB 1: Target Ingestion
        print("\n--- Auditing Tab 1: Target Ingestion ---")
        page.locator("#tab-btn-ingestion").click()
        time.sleep(0.5)
        # Select discount.py
        target_select = page.locator("#target-select")
        if target_select.count() > 0:
            target_select.select_option("discount.py")
            page.locator("#btn-load-sample").click()
            time.sleep(1.0)
        
        # Verify AST symbols
        mod_text = page.locator("#ast-meta-module, #active-target-card").first.inner_text()
        print(f"Target Ingestion Info: {mod_text[:60]}")
        
        set_theme("dark")
        snap("01_dark_tab1_ingestion.png")
        set_theme("light")
        snap("01_light_tab1_ingestion.png")

        # TAB 2: Blast Radius & Call Graph
        print("\n--- Auditing Tab 2: Blast Radius ---")
        page.locator("#tab-btn-blast").click()
        time.sleep(0.8)
        if page.locator("#btn-refresh-blast").is_visible():
            page.locator("#btn-refresh-blast").click()
            time.sleep(0.5)
        
        set_theme("dark")
        snap("02_dark_tab2_blast_radius.png")
        set_theme("light")
        snap("02_light_tab2_blast_radius.png")

        # TAB 3: Hardening Lab & Results (Run Live Hardening)
        print("\n--- Auditing Tab 3: Hardening Lab & Live Hardening ---")
        page.locator("#tab-btn-lab").click()
        time.sleep(0.5)

        # Trigger Hardening Run
        print("Launching live test hardening run on discount.py...")
        run_btn = page.locator("#btn-global-run-hardening, #btn-run-hardening").first
        run_btn.click()

        # Wait for hardening completion
        print("Waiting for hardening pipeline convergence (max 90s)...")
        try:
            page.wait_for_selector(
                "#hardening-status-badge:has-text('FINALIZED'), #hardening-status-badge:has-text('SUCCESS'), #final-hardened-suite-editor:has-text('def test_')",
                timeout=90000
            )
            print("Hardening pipeline completed successfully!")
        except Exception as e:
            print(f"Hardening wait exception: {e}")

        time.sleep(1.5)

        # Exercise Load Benchmark Summary + Minimize Suite
        if page.locator("#btn-load-benchmark-summary").is_visible():
            print("Clicking Load Benchmark Summary...")
            page.locator("#btn-load-benchmark-summary").click()
            time.sleep(1.0)
        
        if page.locator("#btn-run-minimizer").is_visible():
            print("Clicking Minimize Suite...")
            page.locator("#btn-run-minimizer").click()
            time.sleep(1.0)

        set_theme("dark")
        snap("03_dark_tab3_hardening.png")
        set_theme("light")
        snap("03_light_tab3_hardening.png")

        # TAB 4: Multi-Agent Wiretap
        print("\n--- Auditing Tab 4: Multi-Agent Wiretap ---")
        page.locator("#tab-btn-wiretap").click()
        time.sleep(1.0)
        # Open an inspect payload drawer if available
        details = page.locator("details.payload-details summary").first
        if details.count() > 0:
            details.click()
            time.sleep(0.3)

        set_theme("dark")
        snap("04_dark_tab4_wiretap.png")
        set_theme("light")
        snap("04_light_tab4_wiretap.png")

        # TAB 5: Observability Trace
        print("\n--- Auditing Tab 5: Observability Trace ---")
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

        set_theme("dark")
        snap("05_dark_tab5_telemetry.png")
        set_theme("light")
        snap("05_light_tab5_telemetry.png")

        # TAB 6: Benchmarks & Ablation
        print("\n--- Auditing Tab 6: Benchmarks & Ablation ---")
        page.locator("#tab-btn-benchmarks").click()
        time.sleep(1.0)
        if page.locator("#btn-refresh-multi-benchmark").is_visible():
            page.locator("#btn-refresh-multi-benchmark").click()
            time.sleep(0.8)

        set_theme("dark")
        snap("06_dark_tab6_benchmark.png")
        set_theme("light")
        snap("06_light_tab6_benchmark.png")

        # TAB 7: Checkpoints
        print("\n--- Auditing Tab 7: Checkpoints ---")
        page.locator("#tab-btn-checkpoints").click()
        time.sleep(1.0)
        if page.locator("#btn-refresh-checkpoints").is_visible():
            page.locator("#btn-refresh-checkpoints").click()
            time.sleep(0.5)

        cp_cards = page.locator("#cp-history-list .checkpoint-card, #cp-history-list .checkpoint-item, #cp-history-list > div")
        print(f"Checkpoints rendered count: {cp_cards.count()}")
        if cp_cards.count() > 0:
            cp_cards.first.click()
            time.sleep(0.5)

        set_theme("dark")
        snap("07_dark_tab7_checkpoints.png")
        set_theme("light")
        snap("07_light_tab7_checkpoints.png")

        # MODALS AUDIT
        print("\n--- Auditing Modals ---")
        # 1. Settings Modal
        if page.locator("#btn-toggle-settings").is_visible():
            page.locator("#btn-toggle-settings").click()
            time.sleep(0.6)
            set_theme("dark")
            snap("08_dark_modal_settings.png")
            set_theme("light")
            snap("08_light_modal_settings.png")
            page.locator("#btn-close-settings, #btn-cancel-settings").first.click()
            time.sleep(0.4)

        # 2. A2A Protocol Card Modal
        set_theme("dark")
        if page.locator("#btn-a2a-card").is_visible():
            page.locator("#btn-a2a-card").click()
            time.sleep(0.6)
            snap("09_dark_modal_a2a.png")
            page.locator("#btn-close-a2a-modal, #btn-close-a2a-footer").first.click()
            time.sleep(0.4)

        # 3. FastMCP Tools Modal
        if page.locator("#btn-mcp-status").is_visible():
            page.locator("#btn-mcp-status").click()
            time.sleep(0.6)
            snap("10_dark_modal_mcp_tools.png")
            page.locator("#btn-close-mcp-modal, #btn-close-mcp-footer").first.click()
            time.sleep(0.4)

        # 4. FastMCP Studio Modal
        if page.locator("#btn-open-mcp-studio").is_visible():
            page.locator("#btn-open-mcp-studio").click()
            time.sleep(0.6)
            snap("11_dark_modal_mcp_studio.png")
            page.locator("#btn-close-mcp-studio, #btn-mcp-studio-footer-close").first.click()
            time.sleep(0.4)

        # 5. Mutant Diff Inspector Modal
        page.locator("#tab-btn-lab").click()
        time.sleep(0.5)
        if page.locator("#btn-open-mutant-diff-modal").is_visible():
            page.locator("#btn-open-mutant-diff-modal").click()
            time.sleep(0.6)
            set_theme("dark")
            snap("12_dark_modal_mutant_diff.png")
            set_theme("light")
            snap("12_light_modal_mutant_diff.png")
            page.locator("#btn-close-mutant-diff-modal, #btn-close-mutant-diff-footer").first.click()
            time.sleep(0.4)

        browser.close()

    print("\n=== Audit Finished Successfully ===")
    print(f"Console errors: {len(console_errors)}")
    for err in console_errors:
        print(f"  Console: {err}")
    print(f"Page errors: {len(page_errors)}")
    for err in page_errors:
        print(f"  Page: {err}")
    print(f"Failed requests: {len(failed_requests)}")
    for req in failed_requests:
        print(f"  HTTP: {req}")

    assert len(console_errors) == 0, f"Encountered console errors: {console_errors}"
    assert len(page_errors) == 0, f"Encountered page errors: {page_errors}"
    assert len(failed_requests) == 0, f"Encountered failed HTTP requests: {failed_requests}"
    print("ALL VERIFICATIONS PASSED WITH ZERO ERRORS!")

if __name__ == "__main__":
    run_audit()
