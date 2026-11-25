import asyncio
import json
import math
import sys
from playwright.async_api import async_playwright

BASE_URL = "http://127.0.0.1:8000"

VIEWPORTS = [
    {"name": "Desktop (1440x900)", "width": 1440, "height": 900},
    {"name": "Laptop (1280x800)", "width": 1280, "height": 800},
    {"name": "Mobile (390x844)", "width": 390, "height": 844},
]

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
    import re
    m = re.search(r"rgba?\((\d+),\s*(\d+),\s*(\d+)", color_str)
    if m:
        return int(m.group(1)), int(m.group(2)), int(m.group(3))
    return (0, 0, 0)

async def run_checks():
    results = {}
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        for vp in VIEWPORTS:
            vp_name = vp["name"]
            print(f"\n==========================================")
            print(f"Testing Viewport: {vp_name}")
            print(f"==========================================")
            context = await browser.new_context(viewport={"width": vp["width"], "height": vp["height"]})
            page = await context.new_page()

            # Navigate
            await page.goto(BASE_URL, wait_until="networkidle")
            await page.wait_for_timeout(1000)

            vp_results = {
                "settings_modal_footer_click": False,
                "mcp_studio_footer_click": False,
                "tab_nav_a11y": False,
                "tab_nav_no_page_overflow": False,
                "target_title_light_contrast": 0.0,
                "target_title_dark_contrast": 0.0,
                "checkpoint_conflict_swap": False,
            }

            # --- 1. Settings Modal Footer Click (NO force: true) ---
            print("[1] Testing Settings Modal Footer Click (non-forced standard click)...")
            btn_settings = page.locator("#btn-toggle-settings")
            await btn_settings.click()
            await page.wait_for_selector("#settings-modal", state="visible")
            await page.wait_for_timeout(400)

            # Check that modal footer and save button are inside viewport
            save_btn = page.locator("#btn-save-settings")
            is_save_visible = await save_btn.is_visible()
            save_box = await save_btn.bounding_box()
            print(f"    Save button bounding box: {save_box}")
            assert save_box is not None, "Save button bounding box is None"
            assert save_box["y"] + save_box["height"] <= vp["height"], f"Save button bottom ({save_box['y'] + save_box['height']}) exceeds viewport height ({vp['height']})"

            # Click save settings WITHOUT force
            await save_btn.click()
            await page.wait_for_selector("#settings-modal-backdrop", state="hidden", timeout=5000)
            is_backdrop_hidden = await page.locator("#settings-modal-backdrop").evaluate("el => el.classList.contains('hidden')")
            print(f"    Settings modal closed successfully: {is_backdrop_hidden}")
            vp_results["settings_modal_footer_click"] = is_backdrop_hidden

            # --- 2. MCP Studio Modal Footer Click (NO force: true) ---
            print("[2] Testing MCP Studio Modal Footer Click (non-forced standard click)...")
            btn_mcp_studio = page.locator("#btn-open-mcp-studio")
            await btn_mcp_studio.click()
            await page.wait_for_selector("#mcp-studio-modal", state="visible")
            await page.wait_for_timeout(400)

            close_mcp_btn = page.locator("#btn-mcp-studio-footer-close")
            close_box = await close_mcp_btn.bounding_box()
            print(f"    MCP Studio close button bounding box: {close_box}")
            assert close_box is not None, "MCP Studio close button bounding box is None"
            assert close_box["y"] + close_box["height"] <= vp["height"], f"MCP Studio close button bottom ({close_box['y'] + close_box['height']}) exceeds viewport height ({vp['height']})"

            # Click close button WITHOUT force
            await close_mcp_btn.click()
            await page.wait_for_selector("#mcp-studio-modal-backdrop", state="hidden", timeout=5000)
            is_mcp_hidden = await page.locator("#mcp-studio-modal-backdrop").evaluate("el => el.classList.contains('hidden')")
            print(f"    MCP Studio modal closed successfully: {is_mcp_hidden}")
            vp_results["mcp_studio_footer_click"] = is_mcp_hidden

            # --- 3. Tab Nav Accessibility & Mobile Overflow ---
            print("[3] Testing Tab Strip aria-controls and mobile scrolling...")
            tabs_info = await page.evaluate("""() => {
                const tabs = Array.from(document.querySelectorAll('#main-tab-nav [role="tab"]'));
                return tabs.map(t => ({
                    id: t.id,
                    ariaControls: t.getAttribute('aria-controls'),
                    text: t.textContent.trim(),
                    targetExists: !!document.getElementById(t.getAttribute('aria-controls'))
                }));
            }""")
            all_a11y_valid = len(tabs_info) == 7 and all(t["ariaControls"] and t["targetExists"] for t in tabs_info)
            print(f"    All 7 tabs have matching aria-controls: {all_a11y_valid}")
            for t in tabs_info:
                print(f"      - {t['id']} -> aria-controls='{t['ariaControls']}' (exists: {t['targetExists']})")
            vp_results["tab_nav_a11y"] = all_a11y_valid

            # Page horizontal overflow check: document.documentElement.scrollWidth <= viewport width
            doc_scroll_width, vp_inner_width = await page.evaluate("() => [document.documentElement.scrollWidth, window.innerWidth]")
            no_overflow = doc_scroll_width <= vp_inner_width + 1  # allow 1px rounding
            print(f"    Viewport width: {vp_inner_width}, Document scroll width: {doc_scroll_width}, No horizontal page overflow: {no_overflow}")
            vp_results["tab_nav_no_page_overflow"] = no_overflow

            # Can click all tabs in mobile viewport
            for t in tabs_info:
                tab_el = page.locator(f"#{t['id']}")
                await tab_el.scroll_into_view_if_needed()
                await tab_el.click()
                await page.wait_for_timeout(100)

            # --- 4. Contrast Ratio of #target-module-title in Light and Dark Mode ---
            print("[4] Testing Contrast Ratio for #target-module-title...")
            # Navigate to Ingestion tab
            await page.locator("#tab-btn-ingestion").click()
            await page.wait_for_timeout(300)

            # Test Dark Mode first (default or ensure dark mode)
            await page.evaluate("() => { document.documentElement.setAttribute('data-theme', 'dark'); document.body.classList.remove('light-mode'); }")
            await page.wait_for_timeout(200)

            dark_colors = await page.evaluate("""() => {
                const el = document.getElementById('target-module-title');
                const card = document.getElementById('active-target-card') || el.closest('.card') || el.parentElement;
                const fg = window.getComputedStyle(el).color;
                const bg = window.getComputedStyle(card).backgroundColor;
                return { fg, bg };
            }""")
            dark_fg_rgb = parse_rgb(dark_colors["fg"])
            dark_bg_rgb = parse_rgb(dark_colors["bg"])
            # If bg is transparent or rgba(..., 0), fallback to canvas
            if dark_bg_rgb == (0, 0, 0) and "0)" in dark_colors["bg"]:
                dark_bg_rgb = (10, 10, 10)
            ratio_dark = contrast_ratio(dark_fg_rgb, dark_bg_rgb)
            print(f"    Dark Mode: fg={dark_colors['fg']}, bg={dark_colors['bg']} -> Contrast Ratio: {ratio_dark:.2f}:1")
            vp_results["target_title_dark_contrast"] = round(ratio_dark, 2)

            # Test Light Mode
            await page.evaluate("() => { document.documentElement.setAttribute('data-theme', 'light'); document.body.classList.add('light-mode'); }")
            await page.wait_for_timeout(300)

            light_colors = await page.evaluate("""() => {
                const el = document.getElementById('target-module-title');
                const card = document.getElementById('active-target-card') || el.closest('.card') || el.parentElement;
                const fg = window.getComputedStyle(el).color;
                const bg = window.getComputedStyle(card).backgroundColor;
                return { fg, bg };
            }""")
            light_fg_rgb = parse_rgb(light_colors["fg"])
            light_bg_rgb = parse_rgb(light_colors["bg"])
            if light_bg_rgb == (0, 0, 0) and "0)" in light_colors["bg"]:
                light_bg_rgb = (255, 255, 255)
            ratio_light = contrast_ratio(light_fg_rgb, light_bg_rgb)
            print(f"    Light Mode: fg={light_colors['fg']}, bg={light_colors['bg']} -> Contrast Ratio: {ratio_light:.2f}:1")
            vp_results["target_title_light_contrast"] = round(ratio_light, 2)

            # --- 5. Checkpoint Selection Conflict & Helper Message ---
            print("[5] Testing Checkpoint Selection Conflict & Helper Message...")
            # Switch to Checkpoints tab
            await page.locator("#tab-btn-checkpoints").click()
            await page.wait_for_timeout(300)

            conflict_test_res = await page.evaluate("""() => {
                const app = window.__testforge || window.testForgeApp;
                if (!app || !app.setDiffBase || !app.setDiffTarget) {
                    return { success: false, reason: 'testForgeApp diff functions not found' };
                }

                // 1. Set Base to 'cp-100'
                app.setDiffBase('cp-100');
                const b1 = document.getElementById('label-diff-base').textContent;
                const t1 = document.getElementById('label-diff-target').textContent;
                const h1 = document.getElementById('diff-selection-helper').textContent;
                const h1_vis = window.getComputedStyle(document.getElementById('diff-selection-helper')).display !== 'none';

                // 2. Set Target to 'cp-200' (distinct)
                app.setDiffTarget('cp-200');
                const b2 = document.getElementById('label-diff-base').textContent;
                const t2 = document.getElementById('label-diff-target').textContent;
                const h2_vis = window.getComputedStyle(document.getElementById('diff-selection-helper')).display !== 'none';

                // 3. Set Base to 'cp-200' (same as Target)
                // Expectation: Target is cleared, helper warning is displayed
                app.setDiffBase('cp-200');
                const b3 = document.getElementById('label-diff-base').textContent;
                const t3 = document.getElementById('label-diff-target').textContent;
                const h3 = document.getElementById('diff-selection-helper').textContent;
                const h3_vis = window.getComputedStyle(document.getElementById('diff-selection-helper')).display !== 'none';

                // 4. Set Target to 'cp-200' (same as Base)
                // Expectation: Base is cleared, helper warning is displayed
                app.setDiffTarget('cp-200');
                const b4 = document.getElementById('label-diff-base').textContent;
                const t4 = document.getElementById('label-diff-target').textContent;
                const h4 = document.getElementById('diff-selection-helper').textContent;
                const h4_vis = window.getComputedStyle(document.getElementById('diff-selection-helper')).display !== 'none';

                return {
                    success: true,
                    b1, t1, h1_vis,
                    b2, t2, h2_vis,
                    b3, t3, h3, h3_vis,
                    b4, t4, h4, h4_vis
                };
            }""")

            print(f"    Conflict test result: {conflict_test_res}")
            assert conflict_test_res["success"], "Checkpoint conflict helper test failed execution"
            assert conflict_test_res["t3"] == "None selected", f"Expected t3 to be 'None selected', got {conflict_test_res['t3']}"
            assert conflict_test_res["h3"] == "Select two distinct checkpoints to compare", f"Expected helper text, got {conflict_test_res['h3']}"
            assert conflict_test_res["h3_vis"] == True, "Expected helper text to be visible on conflict"
            assert conflict_test_res["b4"] == "None selected", f"Expected b4 to be 'None selected', got {conflict_test_res['b4']}"
            assert conflict_test_res["h4_vis"] == True, "Expected helper text to be visible on conflict"
            vp_results["checkpoint_conflict_swap"] = True

            results[vp_name] = vp_results
            await context.close()

        await browser.close()

    print("\n==========================================")
    print("FINAL MULTI-VIEWPORT VERIFICATION SUMMARY")
    print("==========================================")
    print(json.dumps(results, indent=2))
    
    # Assert all passes
    all_passed = True
    for vp_name, r in results.items():
        if not r["settings_modal_footer_click"]:
            print(f"FAIL: {vp_name} settings_modal_footer_click")
            all_passed = False
        if not r["mcp_studio_footer_click"]:
            print(f"FAIL: {vp_name} mcp_studio_footer_click")
            all_passed = False
        if not r["tab_nav_a11y"]:
            print(f"FAIL: {vp_name} tab_nav_a11y")
            all_passed = False
        if not r["tab_nav_no_page_overflow"]:
            print(f"FAIL: {vp_name} tab_nav_no_page_overflow")
            all_passed = False
        if r["target_title_light_contrast"] < 7.0:
            print(f"FAIL: {vp_name} target_title_light_contrast ({r['target_title_light_contrast']}) < 7.0")
            all_passed = False
        if not r["checkpoint_conflict_swap"]:
            print(f"FAIL: {vp_name} checkpoint_conflict_swap")
            all_passed = False

    if all_passed:
        print("\n>>> ALL MULTI-VIEWPORT CHECKS PASSED WITH 100% SUCCESS! <<<")
        sys.exit(0)
    else:
        print("\n>>> SOME MULTI-VIEWPORT CHECKS FAILED! <<<")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(run_checks())
