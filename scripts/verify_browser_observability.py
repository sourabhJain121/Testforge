import asyncio
import os
import sys
from playwright.async_api import async_playwright

async def run_browser_verification():
    output_dir = os.path.abspath("qa_artifacts/dynamic_model_observability")
    os.makedirs(output_dir, exist_ok=True)
    
    console_errors = []
    network_errors = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(viewport={"width": 1440, "height": 900})
        page = await context.new_page()

        # Capture console messages and network errors
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type in ["error"] else None)
        page.on("requestfailed", lambda req: network_errors.append(f"{req.method} {req.url} - {req.failure}"))

        print("Navigating to http://127.0.0.1:8000 ...")
        await page.goto("http://127.0.0.1:8000", wait_until="networkidle")
        await asyncio.sleep(2)

        # Click Observability & Telemetry tab
        print("Clicking Observability tab...")
        tab_button = page.locator("button[data-tab='tab-telemetry']")
        await tab_button.click()
        await asyncio.sleep(2)

        # 1. Historical Mixed Scope Screenshot
        print("Capturing 01_historical_mixed_engines.png...")
        scope_select = page.locator("#telem-scope-select")
        await scope_select.select_option("all")
        await page.locator("#btn-refresh-telemetry").click()
        await asyncio.sleep(2)
        
        # Verify KPI text
        kpi_engine_text = await page.locator("#telem-kpi-engine").inner_text()
        actual_tokens_text = await page.locator("#telem-kpi-actual-tokens").inner_text()
        est_tokens_text = await page.locator("#telem-kpi-est-tokens").inner_text()
        print(f"Historical Scope -> KPI Engine: '{kpi_engine_text}', Actual Tokens: '{actual_tokens_text}', Est Tokens: '{est_tokens_text}'")
        
        await page.screenshot(path=os.path.join(output_dir, "01_historical_mixed_engines.png"), full_page=False)

        # 2. Current Scope Screenshot
        print("Capturing 02_current_run_deterministic.png...")
        await scope_select.select_option("current")
        await page.locator("#btn-refresh-telemetry").click()
        await asyncio.sleep(2)
        current_kpi_text = await page.locator("#telem-kpi-engine").inner_text()
        print(f"Current Scope -> KPI Engine: '{current_kpi_text}'")
        await page.screenshot(path=os.path.join(output_dir, "02_current_run_deterministic.png"), full_page=False)

        # 3. Deterministic AST Run Screenshot
        print("Capturing 02b_deterministic_ast_run.png...")
        await scope_select.select_option("wf_29dacc90bd25")
        await page.locator("#btn-refresh-telemetry").click()
        await asyncio.sleep(2)
        det_kpi_text = await page.locator("#telem-kpi-engine").inner_text()
        det_actual = await page.locator("#telem-kpi-actual-tokens").inner_text()
        det_est = await page.locator("#telem-kpi-est-tokens").inner_text()
        print(f"Deterministic Scope -> KPI Engine: '{det_kpi_text}', Actual Tokens: '{det_actual}', Est Tokens: '{det_est}'")
        await page.screenshot(path=os.path.join(output_dir, "02b_deterministic_ast_run.png"), full_page=False)

        # 4. CodeLlama Scope Screenshot
        print("Capturing 03_codellama_scope.png...")
        await scope_select.select_option("wf_test_codellama_7e79a7")
        await page.locator("#btn-refresh-telemetry").click()
        await asyncio.sleep(2)
        cl_kpi_text = await page.locator("#telem-kpi-engine").inner_text()
        cl_actual = await page.locator("#telem-kpi-actual-tokens").inner_text()
        print(f"CodeLlama Scope -> KPI Engine: '{cl_kpi_text}', Actual Tokens: '{cl_actual}'")
        await page.screenshot(path=os.path.join(output_dir, "03_codellama_scope.png"), full_page=False)

        # 5. Qwen Scope Screenshot
        print("Capturing 04_qwen_scope.png...")
        await scope_select.select_option("wf_test_qwen_616b46")
        await page.locator("#btn-refresh-telemetry").click()
        await asyncio.sleep(2)
        qwen_kpi_text = await page.locator("#telem-kpi-engine").inner_text()
        qwen_actual = await page.locator("#telem-kpi-actual-tokens").inner_text()
        print(f"Qwen Scope -> KPI Engine: '{qwen_kpi_text}', Actual Tokens: '{qwen_actual}'")
        await page.screenshot(path=os.path.join(output_dir, "04_qwen_scope.png"), full_page=False)

        await browser.close()

    print("\n--- Playwright Verification Summary ---")
    print(f"Console errors: {len(console_errors)}")
    for err in console_errors:
        print(f"  [ERROR] {err}")
    print(f"Network errors: {len(network_errors)}")
    for err in network_errors:
        print(f"  [NET ERROR] {err}")
    print("Screenshots captured successfully.")

if __name__ == "__main__":
    asyncio.run(run_browser_verification())

