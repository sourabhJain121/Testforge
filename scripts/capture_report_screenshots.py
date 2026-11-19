import asyncio
import os
import time
from playwright.async_api import async_playwright

SCREENSHOT_DIR = "docs/screenshots/report_assets"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

async def capture_all():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # 1440x900 viewport with crisp retina scale factor = 2
        context = await browser.new_context(
            viewport={"width": 1440, "height": 900},
            device_scale_factor=2
        )
        page = await context.new_page()

        print("[1/10] Navigating to http://127.0.0.1:8000/...")
        await page.goto("http://127.0.0.1:8000/", wait_until="networkidle")
        await page.wait_for_timeout(1000)

        # 1. Ingestion Cockpit
        print("[2/10] Loading sample target samples/discount.py...")
        # Select discount.py in sample dropdown
        sample_select = page.locator("#select-sample")
        if await sample_select.count() > 0:
            await sample_select.select_option("samples/discount.py")
            await page.wait_for_timeout(500)
            btn_load = page.locator("#btn-load-sample")
            if await btn_load.count() > 0:
                await btn_load.click()
                await page.wait_for_timeout(1000)

        await page.screenshot(path=f"{SCREENSHOT_DIR}/01_cockpit_ingestion.png")
        print(" -> Captured 01_cockpit_ingestion.png")

        # 2. Blast Radius
        print("[3/10] Switching to Blast Radius tab...")
        await page.click("#tab-btn-blast")
        await page.wait_for_timeout(800)
        await page.screenshot(path=f"{SCREENSHOT_DIR}/02_blast_radius.png")
        print(" -> Captured 02_blast_radius.png")

        # 3. Hardening Lab - Run hardening
        print("[4/10] Switching to Hardening Lab tab and running hardening...")
        await page.click("#tab-btn-lab")
        await page.wait_for_timeout(800)
        btn_run = page.locator("#btn-lab-run-hardening")
        if await btn_run.count() > 0 and await btn_run.is_visible():
            await btn_run.click()
            print(" -> Triggered hardening, waiting for completion...")
            # Wait up to 30s for completion or status FINALIZED
            for _ in range(60):
                await page.wait_for_timeout(1000)
                status_el = page.locator("#hardening-status-badge, .badge-success, #job-status-pill")
                text = await page.content()
                if "FINALIZED" in text or "COMPLETED" in text or "100.0%" in text or "94.74%" in text:
                    print(" -> Hardening finished or finalized!")
                    break

        await page.wait_for_timeout(1500)
        await page.screenshot(path=f"{SCREENSHOT_DIR}/03_hardening_lab_results.png")
        await page.screenshot(path=f"{SCREENSHOT_DIR}/03_hardening_lab.png")
        print(" -> Captured 03_hardening_lab_results.png")

        # 4. Multi-Agent Wiretap
        print("[5/10] Switching to Wiretap tab...")
        await page.click("#tab-btn-wiretap")
        await page.wait_for_timeout(800)
        # Refresh wiretap
        btn_wire = page.locator("#btn-refresh-wiretap")
        if await btn_wire.count() > 0 and await btn_wire.is_visible():
            await btn_wire.click()
            await page.wait_for_timeout(800)
        await page.screenshot(path=f"{SCREENSHOT_DIR}/04_multi_agent_wiretap.png")
        print(" -> Captured 04_multi_agent_wiretap.png")

        # 5. Observability / Telemetry
        print("[6/10] Switching to Observability tab...")
        await page.click("#tab-btn-observability")
        await page.wait_for_timeout(800)
        btn_otel = page.locator("#btn-refresh-otel-spans")
        if await btn_otel.count() > 0 and await btn_otel.is_visible():
            await btn_otel.click()
            await page.wait_for_timeout(800)
        await page.screenshot(path=f"{SCREENSHOT_DIR}/05_observability_traces.png")
        print(" -> Captured 05_observability_traces.png")

        # 6. Benchmarks
        print("[7/10] Switching to Benchmarks tab...")
        await page.click("#tab-btn-benchmarks")
        await page.wait_for_timeout(800)
        btn_bench = page.locator("#btn-refresh-multi-benchmark, #btn-refresh-benchmark")
        if await btn_bench.count() > 0 and await btn_bench.first.is_visible():
            await btn_bench.first.click()
            await page.wait_for_timeout(800)
        await page.screenshot(path=f"{SCREENSHOT_DIR}/06_benchmarks_ablation.png")
        print(" -> Captured 06_benchmarks_ablation.png")

        # 7. Checkpoints
        print("[8/10] Switching to Checkpoints tab...")
        await page.click("#tab-btn-checkpoints")
        await page.wait_for_timeout(800)
        btn_cp = page.locator("#btn-refresh-checkpoints")
        if await btn_cp.count() > 0 and await btn_cp.is_visible():
            await btn_cp.click()
            await page.wait_for_timeout(800)
        await page.screenshot(path=f"{SCREENSHOT_DIR}/07_checkpoints_diff.png")
        await page.screenshot(path=f"{SCREENSHOT_DIR}/07_checkpoints_timeline.png")
        print(" -> Captured 07_checkpoints_diff.png")

        # 8. Settings Modal
        print("[9/10] Opening Settings Modal...")
        await page.click("#btn-toggle-settings")
        await page.wait_for_timeout(800)
        await page.screenshot(path=f"{SCREENSHOT_DIR}/08_settings_modal.png")
        print(" -> Captured 08_settings_modal.png")
        await page.click("#btn-close-settings")
        await page.wait_for_timeout(500)

        # 9. A2A Agent Card Modal
        print("[10/11] Opening A2A Agent Card Modal...")
        await page.click("#btn-a2a-card")
        await page.wait_for_timeout(800)
        await page.screenshot(path=f"{SCREENSHOT_DIR}/09_a2a_agent_card.png")
        await page.screenshot(path=f"{SCREENSHOT_DIR}/09_a2a_agent_card_modal.png")
        print(" -> Captured 09_a2a_agent_card.png")
        await page.click("#btn-close-a2a-modal")
        await page.wait_for_timeout(500)

        # 10. FastMCP Studio Modal
        print("[11/11] Opening FastMCP Studio Modal...")
        await page.click("#btn-open-mcp-studio")
        await page.wait_for_timeout(800)
        await page.screenshot(path=f"{SCREENSHOT_DIR}/10_fastmcp_studio.png")
        await page.screenshot(path=f"{SCREENSHOT_DIR}/11_fastmcp_studio_modal.png")
        print(" -> Captured 10_fastmcp_studio.png")
        await page.click("#btn-close-mcp-studio")
        await page.wait_for_timeout(500)

        await browser.close()
        print("All high-resolution screenshots successfully captured!")

if __name__ == "__main__":
    asyncio.run(capture_all())
