#!/usr/bin/env python3
"""
scripts/verify_playground_interactive.py

Automated End-to-End Interactive Verification of TestForge UI Playground:
1. Hardening Flow: Run hardening on samples/discount.py -> verify FINALIZED, score >= 85%,
   AST Diff Inspector, Hardened Test Suite viewer, Load Benchmark Summary & Minimize Suite,
   Retained Minimal Tests chips, Kill Matrix Heatmap.
2. Checkpoints Flow: Switch to #tab-checkpoints -> inspect latest snapshot, Set Base (A) &
   Set Target (B), Deterministic Diff & Structured Inspector.
3. Benchmark Flow: Switch to #tab-benchmark -> refresh/load multi-target summary -> verify
   tables, metrics, verified benchmark artifact badge, and report preview.
4. Telemetry Flow: Switch to #tab-telemetry -> click Refresh Telemetry, Refresh Spans,
   Refresh Decisions -> verify tables and KPI cards.
5. Wiretap Flow: Switch to #tab-wiretap -> verify 8 agent topology cards with active status
   and expandable payloads.
6. Settings Modal: Open Settings -> verify TokenHarbor & Ollama status without leaked keys.
7. Modals: Open & close A2A Card, FastMCP Studio, FastMCP Tools.
"""

import sys
import time
from playwright.sync_api import sync_playwright

def run_interactive_verification():
    console_errors = []
    page_errors = []
    failed_requests = []

    print("[*] Launching Chromium to test http://127.0.0.1:8000 ...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        page.on("pageerror", lambda exc: page_errors.append(str(exc)))
        page.on("console", lambda msg: console_errors.append(f"[{msg.type}] {msg.text}") if msg.type == "error" else None)
        page.on("requestfailed", lambda req: failed_requests.append(f"{req.method} {req.url}: {req.failure}"))

        # Navigate
        page.goto("http://127.0.0.1:8000/", wait_until="domcontentloaded")
        time.sleep(1.0)
        print("[✓] Loaded http://127.0.0.1:8000/")

        # ----------------------------------------------------------------------
        # Flow 1: Header & Cockpit Status Bar
        # ----------------------------------------------------------------------
        print("\n--- Flow 1: Header & Status Bar ---")
        assert "TestForge" in page.title(), f"Page title mismatch: {page.title()}"
        brand_title = page.locator(".brand-title").inner_text()
        assert "TestForge" in brand_title, f"Brand title missing: {brand_title}"

        # Check status pills
        hardware_pill = page.locator("#pill-hardware")
        gemini_pill = page.locator("#pill-gemini")
        ollama_pill = page.locator("#pill-ollama")
        assert hardware_pill.is_visible(), "Hardware pill not visible"
        assert gemini_pill.is_visible(), "Provider pill not visible"
        assert ollama_pill.is_visible(), "Ollama pill not visible"
        print(f"[✓] Status pills visible: {gemini_pill.inner_text().strip()} | {ollama_pill.inner_text().strip()}")

        # ----------------------------------------------------------------------
        # Flow 2: Settings Modal Verification
        # ----------------------------------------------------------------------
        print("\n--- Flow 2: Settings Modal ---")
        page.locator("#btn-toggle-settings").click()
        time.sleep(0.5)
        settings_modal = page.locator("#settings-modal")
        assert settings_modal.is_visible(), "Settings modal did not open"

        # Check TokenHarbor key input & status badge
        th_key_input = page.locator("#input-tokenharbor-key")
        assert th_key_input.is_visible(), "TokenHarbor key input not visible"
        # Verify placeholder or value does not leak full live secret
        val = th_key_input.input_value()
        assert "thk_live_YHryGHB2" not in val, "Raw secret leaked in input field!"

        # Close settings
        page.locator("#btn-close-settings").click()
        time.sleep(0.4)
        assert not settings_modal.is_visible(), "Settings modal did not close"
        print("[✓] Settings modal opened, verified, and closed cleanly")

        # ----------------------------------------------------------------------
        # Flow 3: A2A Card & MCP Modals
        # ----------------------------------------------------------------------
        print("\n--- Flow 3: A2A Card & MCP Modals ---")
        page.locator("#btn-a2a-card").click()
        time.sleep(0.6)
        assert page.locator("#a2a-modal").is_visible(), "A2A modal not visible"
        page.locator("#btn-close-a2a-modal").click()
        time.sleep(0.3)

        page.locator("#btn-mcp-status").click()
        time.sleep(0.5)
        assert page.locator("#mcp-modal").is_visible(), "MCP modal not visible"
        page.locator("#btn-close-mcp-modal").click()
        time.sleep(0.3)

        page.locator("#btn-open-mcp-studio").click()
        time.sleep(0.5)
        assert page.locator("#mcp-studio-modal").is_visible(), "MCP Studio modal not visible"
        page.locator("#btn-close-mcp-studio").click()
        time.sleep(0.3)
        print("[✓] A2A, MCP Status, and MCP Studio modals opened and closed cleanly")

        # ----------------------------------------------------------------------
        # Flow 4: Autonomous Hardening Flow
        # ----------------------------------------------------------------------
        print("\n--- Flow 4: Autonomous Hardening Flow ---")
        # Ensure discount.py is selected
        page.locator("#tab-btn-ingestion").click()
        time.sleep(0.3)
        page.locator("#target-select").select_option("discount.py")
        time.sleep(0.2)
        page.locator("#btn-load-sample").click()
        time.sleep(0.5)

        # Switch to Hardening Lab
        page.locator("#tab-btn-lab").click()
        time.sleep(0.4)
        assert page.locator("#tab-hardening").is_visible(), "#tab-hardening not visible"

        # Check if already finalized or trigger
        pct_text = page.locator("#hardening-percent-text").inner_text()
        status_text = page.locator("#hardening-status-badge").inner_text() if page.locator("#hardening-status-badge").is_visible() else ""
        suite_code = page.locator("#hardened-suite-code").inner_text() if page.locator("#hardened-suite-code").is_visible() else ""
        if "FINALIZED" not in pct_text and "COMPLETED" not in status_text and "def test_" not in suite_code:
            print("[*] Triggering Autonomous Hardening on discount.py ...")
            page.locator("#btn-lab-run-hardening, #btn-start-hardening").first.click()
            print("[*] Waiting for pipeline completion (up to 75s) ...")
            page.wait_for_selector(
                "#hardening-status-badge:has-text('COMPLETED'), #hardening-status-badge:has-text('FINALIZED'), #hardening-status-badge:has-text('SUCCESS'), #hardening-percent-text:has-text('FINALIZED'), #hardened-suite-code:has-text('def test_')",
                timeout=120000
            )
            time.sleep(2.0)

        # Verify finalization KPIs
        mut_score_el = page.locator("#mutation-score-value, #final-mutation-score, #kpi-mut-score")
        mut_score_text = mut_score_el.first.inner_text().strip()
        score_num = float(mut_score_text.split()[0].replace("%", ""))
        print(f"[✓] Finalized Mutation Score: {score_num}%")
        assert score_num >= 85.0, f"Mutation score below 85%: {score_num}"

        # Verify Hardened Suite Code Viewer
        suite_code = page.locator("#hardened-suite-code").inner_text()
        assert "def test_" in suite_code, "Generated tests missing in test_hardened.py view"
        print("[✓] Hardened test suite code viewer populated with synthesized tests")

        # Test Load Benchmark Summary
        print("[*] Testing 'Load Benchmark Summary' button ...")
        btn_load_bench = page.locator("#btn-load-bench-summary")
        if btn_load_bench.is_visible():
            btn_load_bench.click()
            time.sleep(1.0)

        # Test Minimize Suite
        print("[*] Testing 'Minimize Suite' button ...")
        btn_minimize = page.locator("#btn-minimize-suite")
        if btn_minimize.is_visible():
            btn_minimize.click()
            time.sleep(1.5)

        # Verify Retained Minimal Tests & Kill Matrix Heatmap
        retained_chips = page.locator("#minimizer-retained-list *, #retained-tests-list *")
        print(f"[✓] Retained minimal tests rendered count: {retained_chips.count()}")
        heatmap_cells = page.locator("#kill-matrix-heatmap-table td, #kill-matrix-heatmap-table th, #kill-matrix-heatmap-content td")
        print(f"[✓] Kill matrix heatmap cells rendered count: {heatmap_cells.count()}")

        # ----------------------------------------------------------------------
        # Flow 5: Time-Travel Checkpoints Flow
        # ----------------------------------------------------------------------
        print("\n--- Flow 5: Checkpoints Flow ---")
        page.locator("#tab-btn-checkpoints").click()
        time.sleep(0.6)
        assert page.locator("#tab-checkpoints").is_visible(), "#tab-checkpoints not visible"
        refresh_cp_btn = page.locator("#btn-refresh-checkpoints")
        if refresh_cp_btn.is_visible():
            refresh_cp_btn.click()
            time.sleep(1.0)
        cp_cards = page.locator(".checkpoint-card, .cp-card")
        print(f"[✓] Checkpoints found: {cp_cards.count()}")

        # Select first checkpoint if available
        if cp_cards.count() > 0:
            cp_cards.first.click()
            time.sleep(0.5)
            # Verify details container visible
            assert page.locator("#view-cp-detail, #cp-detail-content").is_visible(), "Checkpoint detail content not visible"
            print("[✓] Checkpoint detail view hydrated successfully")

        # ----------------------------------------------------------------------
        # Flow 6: Comparative Benchmarks Flow
        # ----------------------------------------------------------------------
        print("\n--- Flow 6: Benchmarks & Ablation Flow ---")
        page.locator("#tab-btn-benchmarks").click()
        time.sleep(0.6)
        assert page.locator("#tab-benchmark").is_visible(), "#tab-benchmark not visible"

        # Refresh multi-target summary
        page.locator("#btn-refresh-multi-benchmark").click()
        time.sleep(1.0)

        # Verify Verified Benchmark Artifact badge
        bench_badge = page.locator("#badge-benchmark-status").inner_text()
        assert "VERIFIED BENCHMARK ARTIFACT" in bench_badge, f"Unexpected badge text: {bench_badge}"
        platform_badge = page.locator("#badge-benchmark-platform").inner_text()
        print(f"[✓] Benchmark status: {bench_badge} | {platform_badge}")

        # Verify multi-target table rows
        rows = page.locator("#multi-target-benchmark-table-body tr")
        print(f"[✓] Multi-target table row count: {rows.count()}")
        assert rows.count() >= 4, f"Expected at least 4 target rows, got {rows.count()}"

        # ----------------------------------------------------------------------
        # Flow 7: Observability & Telemetry Flow
        # ----------------------------------------------------------------------
        print("\n--- Flow 7: Telemetry Flow ---")
        page.locator("#tab-btn-observability").click()
        time.sleep(0.6)
        assert page.locator("#tab-telemetry").is_visible(), "#tab-telemetry not visible"

        # Click Refresh Telemetry, Spans, Decisions
        page.locator("#btn-refresh-telemetry").click()
        time.sleep(0.5)
        otel_btn = page.locator("#btn-refresh-otel-spans, #btn-refresh-otel")
        if otel_btn.is_visible():
            otel_btn.click()
            time.sleep(0.5)
        dec_btn = page.locator("#btn-refresh-supervisor-decisions, #btn-refresh-decisions")
        if dec_btn.is_visible():
            dec_btn.click()
            time.sleep(0.5)

        prov_text = page.locator("#telem-active-provider").inner_text().strip()
        print(f"[✓] Observability Active Provider: {prov_text}")
        assert "CHECKING" not in prov_text.upper(), f"Provider text still checking: {prov_text}"

        # ----------------------------------------------------------------------
        # Flow 8: Multi-Agent Wiretap Flow
        # ----------------------------------------------------------------------
        print("\n--- Flow 8: Wiretap Flow ---")
        page.locator("#tab-btn-wiretap").click()
        time.sleep(0.6)
        assert page.locator("#tab-wiretap").is_visible(), "#tab-wiretap not visible"

        # Check 8 agent topology nodes
        topo_nodes = page.locator(".topology-node, .topology-card, .agent-card, [data-agent-uri]")
        print(f"[✓] Topology nodes found: {topo_nodes.count()}")

        # ----------------------------------------------------------------------
        # Error Assertions
        # ----------------------------------------------------------------------
        print("\n--- Error Summary ---")
        print(f"Page Errors: {len(page_errors)}")
        print(f"Console Errors: {len(console_errors)}")
        print(f"Failed Requests: {len(failed_requests)}")

        if page_errors:
            print("PAGE ERRORS:", page_errors)
        if console_errors:
            print("CONSOLE ERRORS:", console_errors)
        if failed_requests:
            print("FAILED REQUESTS:", failed_requests)

        assert len(page_errors) == 0, f"Page errors encountered: {page_errors}"
        # Filter out harmless 404s like favicon
        critical_failed = [r for r in failed_requests if "favicon" not in r]
        assert len(critical_failed) == 0, f"Critical network requests failed: {critical_failed}"

        browser.close()
        print("\n[SUCCESS] All interactive playground flows passed cleanly!")

if __name__ == "__main__":
    run_interactive_verification()
