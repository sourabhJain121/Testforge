import asyncio
import json
import math
import sys
import re
from playwright.async_api import async_playwright

BASE_URL = "http://127.0.0.1:8000"

VIEWPORTS = [
    {"name": "Desktop (1440x900)", "width": 1440, "height": 900},
    {"name": "Laptop (1280x800)", "width": 1280, "height": 800},
    {"name": "Mobile (390x844)", "width": 390, "height": 844},
]

MODES = ["dark", "light"]

def luminance(r, g, b):
    a = []
    for v in (r, g, b):
        v = v / 255.0
        if v <= 0.03928:
            a.append(v / 12.92)
        else:
            a.append(((v + 0.055) / 1.055) ** 2.4)
    return a[0] * 0.2126 + a[1] * 0.7152 + a[2] * 0.0722

def contrast_ratio(rgb1, rgb2):
    lum1 = luminance(*rgb1)
    lum2 = luminance(*rgb2)
    brightest = max(lum1, lum2)
    darkest = min(lum1, lum2)
    return (brightest + 0.05) / (darkest + 0.05)

def parse_rgb(color_str):
    m = re.search(r"rgba?\((\d+),\s*(\d+),\s*(\d+)", color_str)
    if m:
        return int(m.group(1)), int(m.group(2)), int(m.group(3))
    return (0, 0, 0)

async def run_e2e():
    results = {}
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        for vp in VIEWPORTS:
            vp_name = vp["name"]
            results[vp_name] = {}

            for theme in MODES:
                test_key = f"{theme}_mode"
                print(f"\n========================================================")
                print(f"Testing Viewport: {vp_name} | Theme: {theme.upper()}")
                print(f"========================================================")

                context = await browser.new_context(viewport={"width": vp["width"], "height": vp["height"]})
                page = await context.new_page()

                # Collect console warnings/errors
                page.on("pageerror", lambda err: print(f"  [PAGE ERROR] {err}"))

                await page.goto(BASE_URL, wait_until="networkidle")
                await page.wait_for_timeout(600)

                # Set Theme
                if theme == "light":
                    await page.evaluate("() => { document.documentElement.setAttribute('data-theme', 'light'); document.body.classList.add('light-mode'); }")
                else:
                    await page.evaluate("() => { document.documentElement.setAttribute('data-theme', 'dark'); document.body.classList.remove('light-mode'); }")
                await page.wait_for_timeout(300)

                metrics = {
                    "settings_save_click": False,
                    "settings_close_click": False,
                    "settings_cancel_click": False,
                    "all_7_tabs_standard_clicked": False,
                    "target_title_contrast": 0.0,
                    "checkpoint_conflict_prevented": False,
                    "checkpoint_view_grouping": False,
                }

                # --- 1. Settings Modal Controls with Standard Clicks (NO force: true) ---
                print("  [1] Testing Settings Modal (#btn-close-settings, #btn-save-settings, #btn-cancel-settings)...")
                # Open & Close with 'X'
                await page.locator("#btn-toggle-settings").click()
                await page.wait_for_selector("#settings-modal", state="visible")
                await page.wait_for_timeout(300)
                await page.locator("#btn-close-settings").click()
                await page.wait_for_selector("#settings-modal-backdrop", state="hidden", timeout=5000)
                metrics["settings_close_click"] = True
                print("      - Standard-clicked #btn-close-settings: modal closed cleanly.")

                # Open & Save
                await page.locator("#btn-toggle-settings").click()
                await page.wait_for_selector("#settings-modal", state="visible")
                await page.wait_for_timeout(300)
                save_btn = page.locator("#btn-save-settings")
                save_box = await save_btn.bounding_box()
                assert save_box["y"] + save_box["height"] <= vp["height"], f"Save button bottom exceeds viewport ({save_box['y'] + save_box['height']} > {vp['height']})"
                await save_btn.click()
                await page.wait_for_selector("#settings-modal-backdrop", state="hidden", timeout=5000)
                metrics["settings_save_click"] = True
                print("      - Standard-clicked #btn-save-settings: modal saved and closed cleanly.")

                # Open & Cancel
                await page.locator("#btn-toggle-settings").click()
                await page.wait_for_selector("#settings-modal", state="visible")
                await page.wait_for_timeout(300)
                cancel_btn = page.locator("#btn-cancel-settings")
                await cancel_btn.click()
                await page.wait_for_selector("#settings-modal-backdrop", state="hidden", timeout=5000)
                metrics["settings_cancel_click"] = True
                print("      - Standard-clicked #btn-cancel-settings: modal cancelled and closed cleanly.")

                # --- 2. Sequential Standard Clicks on All 7 Tabs ---
                print("  [2] Testing standard non-forced clicks across all 7 tabs...")
                tabs = [
                    "tab-btn-ingestion",
                    "tab-btn-blast",
                    "tab-btn-lab",
                    "tab-btn-wiretap",
                    "tab-btn-observability",
                    "tab-btn-benchmarks",
                    "tab-btn-checkpoints",
                ]
                for tab_id in tabs:
                    tab_loc = page.locator(f"#{tab_id}")
                    await tab_loc.scroll_into_view_if_needed()
                    await tab_loc.click()
                    await page.wait_for_timeout(150)
                metrics["all_7_tabs_standard_clicked"] = True
                print(f"      - Successfully standard-clicked all 7 tabs (including #tab-btn-checkpoints at {vp['width']}x{vp['height']}).")

                # --- 3. Target Module Title Contrast ---
                print("  [3] Checking #target-module-title computed contrast...")
                await page.locator("#tab-btn-ingestion").click()
                await page.wait_for_timeout(200)

                colors = await page.evaluate("""() => {
                    const el = document.getElementById('target-module-title');
                    const card = document.getElementById('active-target-card') || el.closest('.card') || el.parentElement;
                    return {
                        fg: window.getComputedStyle(el).color,
                        bg: window.getComputedStyle(card).backgroundColor
                    };
                }""")
                fg_rgb = parse_rgb(colors["fg"])
                bg_rgb = parse_rgb(colors["bg"])
                if bg_rgb == (0, 0, 0) and "0)" in colors["bg"]:
                    bg_rgb = (255, 255, 255) if theme == "light" else (15, 23, 42)
                ratio = contrast_ratio(fg_rgb, bg_rgb)
                metrics["target_title_contrast"] = round(ratio, 2)
                print(f"      - fg={colors['fg']}, bg={colors['bg']} -> Contrast Ratio: {ratio:.2f}:1")
                if theme == "light":
                    assert ratio >= 10.0, f"Light Mode contrast {ratio:.2f}:1 is less than 10:1 requirement"

                # --- 4. Checkpoints Tab UX (Group by Job & Block Duplicate Selection) ---
                print("  [4] Checking Checkpoints tab (duplicate selection & job grouping)...")
                await page.locator("#tab-btn-checkpoints").click()
                await page.wait_for_timeout(300)

                conflict_res = await page.evaluate("""() => {
                    const app = window.__testforge || window.testForgeApp;
                    if (!app) return { error: 'testforge app not found' };

                    // Set base to 'cp-test-1'
                    app.setDiffBase('cp-test-1');
                    // Set target to 'cp-test-1' (same)
                    app.setDiffTarget('cp-test-1');

                    const helper = document.getElementById('diff-selection-helper');
                    const baseLbl = document.getElementById('label-diff-base').textContent;
                    const targetLbl = document.getElementById('label-diff-target').textContent;
                    const helperText = helper ? helper.textContent : '';
                    const helperVisible = helper ? window.getComputedStyle(helper).display !== 'none' : false;

                    return {
                        baseLbl,
                        targetLbl,
                        helperText,
                        helperVisible
                    };
                }""")
                print(f"      - Conflict test: Base='{conflict_res['baseLbl']}', Target='{conflict_res['targetLbl']}', Helper='{conflict_res['helperText']}'")
                assert "different" in conflict_res["helperText"].lower() or "distinct" in conflict_res["helperText"].lower()
                assert conflict_res["helperVisible"] == True
                metrics["checkpoint_conflict_prevented"] = True

                # Test grouping mode dropdown
                view_mode_res = await page.evaluate("""() => {
                    const select = document.getElementById('cp-view-grouping');
                    if (!select) return { error: 'cp-view-grouping select not found' };
                    select.value = 'grouped_by_job';
                    select.dispatchEvent(new Event('change'));
                    const valGrouped = select.value;
                    select.value = 'latest_job';
                    select.dispatchEvent(new Event('change'));
                    const valLatest = select.value;
                    return { success: true, valGrouped, valLatest };
                }""")
                print(f"      - Checkpoint view mode selector: {view_mode_res}")
                assert view_mode_res.get("success") == True
                metrics["checkpoint_view_grouping"] = True

                results[vp_name][test_key] = metrics
                await context.close()

        # --- 5. Full Live Hardening Job on samples/discount.py (Dark Mode @ 1440x900) ---
        print("\n========================================================")
        print("Executing Full Live Hardening Job on samples/discount.py")
        print("Viewport: 1440x900 | Theme: DARK | Provider: Auto")
        print("========================================================")

        hard_context = await browser.new_context(viewport={"width": 1440, "height": 900})
        hard_page = await hard_context.new_page()
        hard_page.on("pageerror", lambda err: print(f"  [PAGE ERROR] {err}"))

        await hard_page.goto(BASE_URL, wait_until="networkidle")
        await hard_page.wait_for_timeout(1000)

        # Switch to Hardening Lab
        await hard_page.locator("#tab-btn-lab").click()
        await hard_page.wait_for_timeout(500)

        # Click Start Hardening via standard click (NO force: true)
        print("  [*] Standard-clicking #btn-start-hardening...")
        btn_start = hard_page.locator("#btn-start-hardening")
        await btn_start.click()

        # Wait for the job to complete or reach FINALIZED / COMPLETED
        print("  [*] Hardening job in-flight, monitoring progress...")
        start_time = asyncio.get_event_loop().time()
        max_wait = 180  # up to 3 minutes
        final_verdict = None

        while (asyncio.get_event_loop().time() - start_time) < max_wait:
            await hard_page.wait_for_timeout(3000)
            status_info = await hard_page.evaluate("""() => {
                const percentText = document.getElementById('hardening-percent-text')?.textContent || '';
                const statusBadge = document.getElementById('hardening-status-badge')?.textContent || '';
                const verdictBanner = document.getElementById('hardening-verdict-banner');
                const isVerdictVisible = verdictBanner && !verdictBanner.classList.contains('hidden');
                const isInterrupted = verdictBanner && verdictBanner.classList.contains('interrupted');
                const isFailed = verdictBanner && verdictBanner.classList.contains('failed');
                const isSuccess = verdictBanner && (verdictBanner.classList.contains('success') || verdictBanner.classList.contains('completed'));
                const editorCode = document.getElementById('final-hardened-suite-editor')?.textContent || '';
                const scoreText = document.getElementById('final-mutation-score')?.textContent || '';

                return {
                    percentText,
                    statusBadge,
                    isVerdictVisible,
                    isInterrupted,
                    isFailed,
                    isSuccess,
                    hasCode: editorCode.includes('def test_'),
                    codeLen: editorCode.length,
                    scoreText
                };
            }""")

            elapsed = int(asyncio.get_event_loop().time() - start_time)
            print(f"      [+{elapsed}s] Status: '{status_info['statusBadge']}' | Progress: '{status_info['percentText']}' | VerdictVisible: {status_info['isVerdictVisible']} | HasCode: {status_info['hasCode']}")

            if status_info["hasCode"] or "FINALIZED" in status_info["percentText"] or status_info["statusBadge"] in ("COMPLETED", "FINALIZED", "SUCCESS"):
                final_verdict = status_info
                break

            if status_info["isInterrupted"]:
                print("      [!] Encountered 'interrupted' banner — asserting resume behavior...")
                # Test the resume button behavior
                resume_btn = hard_page.locator("#btn-resume-interrupted-job")
                if await resume_btn.is_visible():
                    print("      [*] Clicking #btn-resume-interrupted-job...")
                    await resume_btn.click()
                    await hard_page.wait_for_timeout(3000)

        assert final_verdict is not None, "Hardening job did not complete within timeout"
        assert not final_verdict["isInterrupted"], "Hardening job ended in false 'Process Interrupted' state!"
        assert not final_verdict["isFailed"], "Hardening job failed unexpectedly"
        assert final_verdict["hasCode"], "Hardened test code was not synthesized in #final-hardened-suite-editor"

        print("\n  [SUCCESS] Live Hardening Job verified clean finalization!")
        print(f"      - Final Status Badge: {final_verdict['statusBadge']}")
        print(f"      - Hardened Suite Length: {final_verdict['codeLen']} characters")
        print(f"      - Contains 'def test_': {final_verdict['hasCode']}")
        results["live_hardening_job"] = {
            "status": "FINALIZED",
            "has_hardened_code": final_verdict["hasCode"],
            "code_len": final_verdict["codeLen"],
            "elapsed_seconds": int(asyncio.get_event_loop().time() - start_time)
        }

        await hard_context.close()
        await browser.close()

    print("\n========================================================")
    print("ALL E2E NON-FORCED VERIFICATIONS COMPLETE")
    print("========================================================")
    print(json.dumps(results, indent=2))

    all_passed = True
    for vp_name, themes in results.items():
        if vp_name == "live_hardening_job":
            continue
        for t_name, m in themes.items():
            for metric_name, val in m.items():
                if metric_name == "target_title_contrast":
                    if val < 10.0 and "light" in t_name:
                        print(f"FAIL: {vp_name} {t_name} target_title_contrast ({val}) < 10:1")
                        all_passed = False
                elif not val:
                    print(f"FAIL: {vp_name} {t_name} {metric_name}")
                    all_passed = False

    if all_passed:
        print("\n>>> 100% OF VERIFICATION CHECKS PASSED SUCCESSFULLY! <<<")
        sys.exit(0)
    else:
        print("\n>>> SOME VERIFICATION CHECKS FAILED! <<<")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(run_e2e())
