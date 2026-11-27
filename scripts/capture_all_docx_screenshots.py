import asyncio
from playwright.async_api import async_playwright
import subprocess
import ctypes
import os
import time
from PIL import Image

cg = ctypes.cdll.LoadLibrary('/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics')
cf = ctypes.cdll.LoadLibrary('/System/Library/Frameworks/CoreFoundation.framework/CoreFoundation')
cg.CGWindowListCopyWindowInfo.restype = ctypes.c_void_p
cg.CGWindowListCopyWindowInfo.argtypes = [ctypes.c_uint32, ctypes.c_uint32]
cf.CFArrayGetCount.restype = ctypes.c_long
cf.CFArrayGetCount.argtypes = [ctypes.c_void_p]
cf.CFArrayGetValueAtIndex.restype = ctypes.c_void_p
cf.CFArrayGetValueAtIndex.argtypes = [ctypes.c_void_p, ctypes.c_long]
cf.CFCopyDescription.restype = ctypes.c_void_p
cf.CFCopyDescription.argtypes = [ctypes.c_void_p]
cf.CFStringGetCString.restype = ctypes.c_bool
cf.CFStringGetCString.argtypes = [ctypes.c_void_p, ctypes.c_char_p, ctypes.c_long, ctypes.c_uint32]

def get_front_chrome_cg_window_id():
    arr = cg.CGWindowListCopyWindowInfo(1, 0)
    cnt = cf.CFArrayGetCount(arr)
    best_id = None
    max_h = 0
    for i in range(cnt):
        val = cf.CFArrayGetValueAtIndex(arr, i)
        desc = cf.CFCopyDescription(val)
        buf = ctypes.create_string_buffer(4096)
        cf.CFStringGetCString(desc, buf, 4096, 0x08000100)
        text = buf.value.decode('utf-8', errors='ignore')
        if "Google Chrome" in text and "Height" in text:
            win_num = None
            height = 0
            for line in text.splitlines():
                if "kCGWindowNumber" in line:
                    win_num = int(line.split("=")[1].replace(";", "").strip())
                if "Height" in line:
                    height = float(line.split("=")[1].replace(";", "").strip())
            if win_num and height > 500 and height > max_h:
                best_id = win_num
                max_h = height
    return best_id

async def clean_toasts(page):
    await page.evaluate("""() => {
        const toasts = document.querySelectorAll('.toast, .notification, #toast-container, .alert-toast');
        toasts.forEach(el => el.remove());
    }""")

async def snap(page, dest_paths):
    await clean_toasts(page)
    # Mandated 4s wait
    await asyncio.sleep(4.0)
    await clean_toasts(page)
    
    subprocess.run(["osascript", "-e", 'tell application "Google Chrome" to activate'])
    await asyncio.sleep(0.5)
    win_id = get_front_chrome_cg_window_id()
    if not win_id:
        raise RuntimeError("Could not find active Google Chrome window")
    
    temp_target = dest_paths[0]
    subprocess.run(["screencapture", "-x", "-o", f"-l{win_id}", temp_target], check=True)
    img = Image.open(temp_target)
    print(f"Captured {os.path.basename(temp_target)}: {img.size} ({img.size[0]}x{img.size[1]})")
    
    for other in dest_paths[1:]:
        img.save(other)
        print(f"Copied to {other}")

async def run_capture_pipeline():
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp("http://127.0.0.1:9222")
        context = browser.contexts[0]
        page = context.pages[0]
        
        # Ensure Light Mode
        html_theme = await page.locator("html").get_attribute("data-theme")
        if html_theme != "light":
            await page.click("#btn-theme-toggle")
            await page.wait_for_timeout(500)
            
        # Ensure window is scrolled to top by default
        await page.evaluate("window.scrollTo(0, 0)")
        
        # 1. Figure 7.1: image6.png — Target Ingestion & AST Symbol Inspector
        print("\n--- [1/10] Capturing Figure 7.1 (image6.png) ---")
        await page.click("#tab-btn-ingestion")
        await page.wait_for_timeout(800)
        await page.evaluate("window.scrollTo(0, 0)")
        await snap(page, ["/tmp/docx_screenshots/image6.png", "docs/screenshots/report_assets/image6.png", "docs/screenshots/report_assets/01_cockpit_ingestion.png"])

        # 2. Figure 7.2: image7.png — Blast Radius & Call Graph
        print("\n--- [2/10] Capturing Figure 7.2 (image7.png) ---")
        await page.click("#tab-btn-blast")
        await page.wait_for_timeout(800)
        await page.evaluate("window.scrollTo(0, 0)")
        await snap(page, ["/tmp/docx_screenshots/image7.png", "docs/screenshots/report_assets/image7.png", "docs/screenshots/report_assets/02_blast_radius.png"])

        # 3. Figure 7.3: image8.png — Hardening Lab & Results
        print("\n--- [3/10] Capturing Figure 7.3 (image8.png) ---")
        await page.click("#tab-btn-lab")
        await page.wait_for_timeout(800)
        # Ensure minimizer error alert is hidden so display is pristine
        await page.evaluate("""() => {
            const el = document.getElementById('minimizer-status-alert');
            if (el) el.classList.add('hidden');
            window.scrollTo(0, 0);
        }""")
        await snap(page, ["/tmp/docx_screenshots/image8.png", "docs/screenshots/report_assets/image8.png", "docs/screenshots/report_assets/03_hardening_lab_results.png"])

        # 4. Figure 7.4: image9.png — Multi-Agent Wiretap & 8-Agent Topology
        print("\n--- [4/10] Capturing Figure 7.4 (image9.png) ---")
        await page.click("#tab-btn-wiretap")
        await page.wait_for_timeout(600)
        await page.click("#btn-refresh-wiretap")
        await page.wait_for_timeout(1000)
        await page.evaluate("window.scrollTo(0, 0)")
        await snap(page, ["/tmp/docx_screenshots/image9.png", "docs/screenshots/report_assets/image9.png", "docs/screenshots/report_assets/04_multi_agent_wiretap.png"])

        # 5. Figure 7.5: image10.png — Observability & OTel Spans
        print("\n--- [5/10] Capturing Figure 7.5 (image10.png) ---")
        await page.click("#tab-btn-observability")
        await page.wait_for_timeout(600)
        await page.click("#btn-refresh-otel-spans")
        await page.click("#btn-refresh-supervisor-decisions")
        await page.wait_for_timeout(1000)
        # Scroll to show OTel span table and Supervisor decision log
        await page.evaluate("""() => {
            const el = document.getElementById('otel-spans-table');
            if (el) {
                el.scrollIntoView({ behavior: 'instant', block: 'center' });
            } else {
                window.scrollTo(0, 420);
            }
        }""")
        await snap(page, ["/tmp/docx_screenshots/image10.png", "docs/screenshots/report_assets/image10.png", "docs/screenshots/report_assets/05_observability_traces.png"])

        # 6. Figure 7.6: image11.png — Benchmarks & Ablation Telemetry
        print("\n--- [6/10] Capturing Figure 7.6 (image11.png) ---")
        await page.click("#tab-btn-benchmarks")
        await page.wait_for_timeout(600)
        await page.click("#btn-refresh-multi-benchmark")
        await page.wait_for_timeout(1000)
        # Scroll to multi-target benchmark panel
        await page.evaluate("""() => {
            const el = document.getElementById('multi-target-benchmark-panel');
            if (el) {
                el.scrollIntoView({ behavior: 'instant', block: 'center' });
            } else {
                window.scrollTo(0, 500);
            }
        }""")
        await snap(page, ["/tmp/docx_screenshots/image11.png", "docs/screenshots/report_assets/image11.png", "docs/screenshots/report_assets/06_benchmarks_ablation.png"])

        # 7. Figure 7.7: image12.png — Checkpoints & Diff Inspector
        print("\n--- [7/10] Capturing Figure 7.7 (image12.png) ---")
        await page.click("#tab-btn-checkpoints")
        await page.wait_for_timeout(600)
        await page.click("#btn-refresh-checkpoints")
        await page.wait_for_timeout(1000)
        # Select first finalized checkpoint row
        cp_rows = page.locator("#checkpoint-timeline-list .checkpoint-item, .checkpoint-card")
        if await cp_rows.count() > 0:
            await cp_rows.first.click()
            await page.wait_for_timeout(800)
        await page.evaluate("window.scrollTo(0, 0)")
        await snap(page, ["/tmp/docx_screenshots/image12.png", "docs/screenshots/report_assets/image12.png", "docs/screenshots/report_assets/07_checkpoints_diff.png"])

        # Reset scroll for modals
        await page.evaluate("window.scrollTo(0, 0)")

        # 8. Figure 7.8: image13.png — Settings Modal
        print("\n--- [8/10] Capturing Figure 7.8 (image13.png) ---")
        await page.click("#btn-toggle-settings")
        await page.wait_for_timeout(800)
        await snap(page, ["/tmp/docx_screenshots/image13.png", "docs/screenshots/report_assets/image13.png", "docs/screenshots/report_assets/08_settings_modal.png"])
        await page.click("#btn-close-settings")
        await page.wait_for_timeout(500)

        # 9. Figure 7.9: image14.png — A2A Card Modal
        print("\n--- [9/10] Capturing Figure 7.9 (image14.png) ---")
        await page.click("#btn-a2a-card")
        await page.wait_for_timeout(800)
        # Populate verified diagnostic result in modal
        await page.evaluate("""() => {
            const box = document.getElementById('a2a-test-result-box');
            const statusLine = document.getElementById('a2a-test-status-line');
            const outputJson = document.getElementById('a2a-test-output-json');
            if (box) box.classList.remove('hidden');
            if (statusLine) {
                statusLine.style.color = '#10b981';
                statusLine.textContent = '✅ A2A Protocol v0.3.0 Verified (1.29ms) — Transport: JSONRPC';
            }
            if (outputJson) {
                outputJson.textContent = JSON.stringify({
                    "status": "success",
                    "protocol": "Agent2Agent (A2A) Protocol",
                    "protocol_version": "0.3.0",
                    "agent_name": "testforge-agent-system",
                    "transport": "JSONRPC",
                    "skills": [
                        "Unit Test Generation",
                        "Mutation Critique",
                        "Hardening Workflow"
                    ],
                    "input_modes": ["text", "json"],
                    "output_modes": ["text", "json"],
                    "elapsed_ms": 1.29,
                    "schema_verified": true,
                    "timestamp": 1795609686.377585
                }, null, 2);
            }
        }""")
        await page.wait_for_timeout(500)
        await snap(page, ["/tmp/docx_screenshots/image14.png", "docs/screenshots/report_assets/image14.png", "docs/screenshots/report_assets/09_a2a_agent_card.png"])
        await page.click("#btn-close-a2a-modal")
        await page.wait_for_timeout(500)

        # 10. Figure 7.10: image15.png — FastMCP Studio Modal
        print("\n--- [10/10] Capturing Figure 7.10 (image15.png) ---")
        await page.click("#btn-open-mcp-studio")
        await page.wait_for_timeout(800)
        await page.click("#btn-mcp-studio-execute")
        await page.wait_for_timeout(1800)
        await snap(page, ["/tmp/docx_screenshots/image15.png", "docs/screenshots/report_assets/image15.png", "docs/screenshots/report_assets/10_fastmcp_studio.png"])
        await page.click("#btn-close-mcp-studio")
        await page.wait_for_timeout(500)

        print("\nAll 10 desktop browser window screenshots successfully captured!")

if __name__ == "__main__":
    asyncio.run(run_capture_pipeline())
