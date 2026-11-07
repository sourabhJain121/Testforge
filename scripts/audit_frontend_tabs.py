"""
Comprehensive Frontend Automation Audit Script for TestForge.
Visits every tab, tests controls, modals, and captures screenshots into qa_artifacts/final_ui_audit/screenshots/.
"""

import json
from pathlib import Path
from playwright.sync_api import sync_playwright

OUTPUT_DIR = Path("qa_artifacts/final_ui_audit/screenshots")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

TABS = [
    ("tab-mode-a", "nav-mode-a", "02_tab_mode_a_workspace.png"),
    ("tab-mode-b", "nav-mode-b", "03_tab_mode_b_synthesis.png"),
    ("tab-mode-c", "nav-mode-c", "04_tab_mode_c_github.png"),
    ("tab-blast", "nav-blast", "05_tab_blast_radius.png"),
    ("tab-hardening", "nav-hardening", "06_tab_hardening_cockpit.png"),
    ("tab-wiretap", "nav-wiretap", "07_tab_wiretap_stream.png"),
    ("tab-telemetry", "nav-telemetry", "08_tab_telemetry_traces.png"),
    ("tab-benchmark", "nav-benchmark", "09_tab_benchmark_engine.png"),
    ("tab-checkpoints", "nav-checkpoints", "10_tab_checkpoints_timeline.png"),
]

def run_tab_audit():
    results = []
    console_errors = []
    failed_requests = []

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        # Monitor console and network
        page.on("console", lambda msg: console_errors.append(f"[{msg.type}] {msg.text}") if msg.type in ["error", "warning"] else None)
        page.on("requestfailed", lambda req: failed_requests.append(f"{req.method} {req.url}: {req.failure}"))

        # Navigate to application
        page.goto("http://127.0.0.1:8000/", wait_until="networkidle")
        page.wait_for_timeout(1000)

        # 1. Header Modals Audit
        print("Auditing Header Modals...")
        # A2A Card Modal
        page.click("#btn-a2a-card")
        page.wait_for_timeout(500)
        page.screenshot(path=OUTPUT_DIR / "11_modal_a2a_card.png")
        a2a_visible = page.is_visible("#modal-a2a")
        page.click("#btn-close-a2a-modal")
        page.wait_for_timeout(300)
        results.append({"control": "btn-a2a-card", "modal": "modal-a2a", "visible": a2a_visible, "screenshot": "11_modal_a2a_card.png"})

        # MCP Status Modal
        page.click("#btn-mcp-status")
        page.wait_for_timeout(500)
        page.screenshot(path=OUTPUT_DIR / "12_modal_mcp_status.png")
        mcp_visible = page.is_visible("#modal-mcp")
        page.click("#btn-close-mcp-modal")
        page.wait_for_timeout(300)
        results.append({"control": "btn-mcp-status", "modal": "modal-mcp", "visible": mcp_visible, "screenshot": "12_modal_mcp_status.png"})

        # Settings Modal
        page.click("#btn-toggle-settings")
        page.wait_for_timeout(500)
        page.screenshot(path=OUTPUT_DIR / "13_modal_settings.png")
        settings_visible = page.is_visible("#modal-settings")
        page.click("#btn-close-settings")
        page.wait_for_timeout(300)
        results.append({"control": "btn-toggle-settings", "modal": "modal-settings", "visible": settings_visible, "screenshot": "13_modal_settings.png"})

        # 2. Main Navigation Tabs Audit
        print("Auditing Main Navigation Tabs...")
        for tab_id, nav_id, filename in TABS:
            print(f"  Visiting {tab_id} via #{nav_id}...")
            page.click(f"#{nav_id}")
            page.wait_for_timeout(800)
            
            # Check if tab pane is active
            is_active = page.eval_on_selector(f"#{tab_id}", "el => el.classList.contains('active')")
            
            # Capture full page / viewport screenshot
            page.screenshot(path=OUTPUT_DIR / filename)
            
            # Inspect tab specific elements
            tab_data = {
                "tab_id": tab_id,
                "nav_id": nav_id,
                "is_active": is_active,
                "screenshot": filename,
            }
            results.append(tab_data)

        # 3. Test interactive controls on Mode A
        print("Testing Mode A sample loader...")
        page.click("#nav-mode-a")
        page.wait_for_timeout(500)
        # Select sample dropdown
        sample_options = page.eval_on_selector("#sample-select", "sel => Array.from(sel.options).map(o => o.value)")
        print("  Available samples in dropdown:", sample_options)
        if sample_options:
            page.select_option("#sample-select", sample_options[0])
            page.click("#btn-load-sample")
            page.wait_for_timeout(1000)
            editor_content = page.eval_on_selector("#mode-a-editor", "el => el.value")
            page.screenshot(path=OUTPUT_DIR / "14_mode_a_sample_loaded.png")
            print(f"  Loaded sample {sample_options[0]} into editor ({len(editor_content)} chars)")

        # 4. Test Observability & Telemetry Refresh
        print("Testing Telemetry tab refresh...")
        page.click("#nav-telemetry")
        page.wait_for_timeout(500)
        page.click("#btn-refresh-telemetry")
        page.wait_for_timeout(1000)
        page.screenshot(path=OUTPUT_DIR / "15_telemetry_refreshed.png")

        # 5. Test Wiretap Refresh
        print("Testing Wiretap tab refresh...")
        page.click("#nav-wiretap")
        page.wait_for_timeout(500)
        page.click("#btn-refresh-wiretap")
        page.wait_for_timeout(1000)
        page.screenshot(path=OUTPUT_DIR / "16_wiretap_refreshed.png")

        # 6. Test Checkpoints Timeline
        print("Testing Checkpoints tab...")
        page.click("#nav-checkpoints")
        page.wait_for_timeout(500)
        page.click("#btn-refresh-checkpoints")
        page.wait_for_timeout(1000)
        checkpoint_cards = page.eval_on_selector_all(".checkpoint-card, .timeline-item", "els => els.length")
        print(f"  Rendered checkpoint cards: {checkpoint_cards}")
        page.screenshot(path=OUTPUT_DIR / "17_checkpoints_loaded.png")

        browser.close()

    print("\n=== AUDIT SUMMARY ===")
    print("Screenshots saved to:", OUTPUT_DIR)
    print("Console errors count:", len(console_errors))
    for err in console_errors:
        print("  Console:", err)
    print("Failed network requests count:", len(failed_requests))
    for req in failed_requests:
        print("  Network:", req)

    # Save structured audit results
    audit_data = {
        "tabs_and_modals": results,
        "console_errors": console_errors,
        "failed_requests": failed_requests,
    }
    with open("qa_artifacts/final_ui_audit/tab_audit_results.json", "w") as f:
        json.dump(audit_data, f, indent=2)

if __name__ == "__main__":
    run_tab_audit()

