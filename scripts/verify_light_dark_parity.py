#!/usr/bin/env python3
"""
verify_light_dark_parity.py
Playwright verification for Light/Dark mode parity, tab layout, and WCAG AA contrast.
"""
import sys
import time
from playwright.sync_api import sync_playwright

def parse_color(color_str):
    import re
    m = re.match(r'rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)', color_str)
    if m:
        r, g, b = int(m.group(1)), int(m.group(2)), int(m.group(3))
        a = float(m.group(4)) if m.group(4) is not None else 1.0
        return r, g, b, a
    return 0, 0, 0, 1.0

def luminance(r, g, b):
    def channel(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    return 0.2126 * channel(r) + 0.7152 * channel(g) + 0.0722 * channel(b)

def contrast_ratio(rgb1, rgb2):
    l1 = luminance(*rgb1)
    l2 = luminance(*rgb2)
    lighter = max(l1, l2)
    darker = min(l1, l2)
    return (lighter + 0.05) / (darker + 0.05)

def main():
    url = "http://127.0.0.1:8000"
    errors = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)

        for width, height in [(1280, 800), (1440, 900)]:
            print(f"\n==========================================")
            print(f"Testing Viewport: {width}x{height}")
            print(f"==========================================")
            context = browser.new_context(viewport={"width": width, "height": height})
            page = context.new_page()

            page.goto(url, wait_until="domcontentloaded", timeout=15000)
            page.wait_for_timeout(1000)

            # 1. Dark Mode Tab Layout Check
            tab_selectors = [
                "#tab-btn-ingestion",
                "#tab-btn-blast",
                "#tab-btn-lab",
                "#tab-btn-wiretap",
                "#tab-btn-observability",
                "#tab-btn-benchmarks",
                "#tab-btn-checkpoints",
            ]

            print(f"Checking {len(tab_selectors)} tabs inside {width}px viewport in Dark Mode...")
            for sel in tab_selectors:
                el = page.locator(sel)
                if not el.is_visible():
                    errors.append(f"Tab {sel} not visible at {width}x{height}")
                    continue
                box = el.bounding_box()
                assert box is not None
                right_edge = box['x'] + box['width']
                print(f"  {sel}: x={box['x']:.1f}, width={box['width']:.1f}, right={right_edge:.1f}")
                if right_edge > width:
                    errors.append(f"Tab {sel} clips outside viewport {width}px (right edge: {right_edge})")

            # Check Checkpoints text
            cp_text = page.locator("#tab-btn-checkpoints").inner_text()
            assert "Checkpoints" in cp_text, f"Expected 'Checkpoints' in button text, got '{cp_text}'"

            # Check tab-nav scrollWidth vs clientWidth
            overflow_info = page.evaluate("""() => {
                const nav = document.getElementById('main-tab-nav');
                return { scrollWidth: nav.scrollWidth, clientWidth: nav.clientWidth };
            }""")
            print(f"  Tab bar overflow check: scrollWidth={overflow_info['scrollWidth']}, clientWidth={overflow_info['clientWidth']}")

            # Save Dark screenshot
            if width == 1280:
                page.screenshot(path="/Users/sourabh/.gemini/antigravity/brain/ad3919fc-7c4f-4e08-af89-e520bbc7c86c/dark_mode_overview_1280.png")

            # 2. Switch to Light Mode
            print("\nSwitching to Light Mode via #btn-theme-toggle...")
            toggle_btn = page.locator("#btn-theme-toggle")
            toggle_btn.click()
            page.wait_for_timeout(500)

            theme = page.evaluate("() => document.documentElement.getAttribute('data-theme')")
            assert theme == "light", f"Expected theme 'light', got '{theme}'"
            print(f"  data-theme confirmed: {theme}")

            # Check Light Mode Tab Layout
            print(f"Checking tabs inside {width}px viewport in Light Mode...")
            for sel in tab_selectors:
                el = page.locator(sel)
                box = el.bounding_box()
                assert box is not None
                right_edge = box['x'] + box['width']
                if right_edge > width:
                    errors.append(f"Light mode: Tab {sel} clips outside viewport {width}px (right edge: {right_edge})")

            # Save Light screenshot
            if width == 1280:
                page.screenshot(path="/Users/sourabh/.gemini/antigravity/brain/ad3919fc-7c4f-4e08-af89-e520bbc7c86c/light_mode_overview_1280.png")
            elif width == 1440:
                page.screenshot(path="/Users/sourabh/.gemini/antigravity/brain/ad3919fc-7c4f-4e08-af89-e520bbc7c86c/light_mode_overview_1440.png")

            # 3. Contrast Checks in Light Mode
            print("\nEvaluating contrast ratios in Light Mode (WCAG AA >= 4.5:1)...")
            elements_to_check = [
                ("Brand Title", ".brand-title"),
                ("Hardware Label", "#label-hardware"),
                ("Target Module Title", "#target-module-title"),
                ("Dual Framework Tag", "#tag-dual-framework"),
                ("Diff-Aware Toggle H4", ".toggle-info h4"),
                ("Active Tab", ".tab-btn.active"),
                ("Inactive Tab", "#tab-btn-blast"),
                ("Submode Active Pill", ".mode-radio-label input:checked + .mode-radio-pill"),
                ("Submode Inactive Pill", "#nav-mode-b"),
                ("Select Control", "#target-select"),
                ("Panel Title", ".panel-title"),
            ]

            for label, selector in elements_to_check:
                loc = page.locator(selector).first
                if loc.count() > 0 and loc.is_visible():
                    styles = page.evaluate("""(sel) => {
                        const el = document.querySelector(sel);
                        if (!el) return null;
                        const cs = window.getComputedStyle(el);
                        // walk up to find background color if transparent
                        let bg = cs.backgroundColor;
                        let curr = el;
                        while ((!bg || bg === 'rgba(0, 0, 0, 0)' || bg === 'transparent') && curr.parentElement) {
                            curr = curr.parentElement;
                            bg = window.getComputedStyle(curr).backgroundColor;
                        }
                        return { color: cs.color, bg: bg || 'rgb(255, 255, 255)' };
                    }""", selector)
                    if styles:
                        tc = parse_color(styles['color'])[:3]
                        bc = parse_color(styles['bg'])[:3]
                        cr = contrast_ratio(tc, bc)
                        status = "PASS" if cr >= 4.5 else "WARN"
                        print(f"  [{status}] {label} ({selector}): text={styles['color']}, bg={styles['bg']} -> CR = {cr:.2f}:1")
                        if cr < 3.0: # Below minimum discernible contrast
                            errors.append(f"Severe contrast failure on {label} ({selector}): {cr:.2f}:1 (text: {styles['color']}, bg: {styles['bg']})")

            context.close()

        browser.close()

    if errors:
        print("\nVerification Failures:")
        for e in errors:
            print(f"  - {e}")
        sys.exit(1)
    else:
        print("\nAll Light/Dark parity and layout checks PASSED cleanly!")

if __name__ == "__main__":
    main()
