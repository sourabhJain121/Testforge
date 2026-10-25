"""
cancellation_browser_audit.py - Automated Browser E2E Test for Hardening Cancellation.
Launches headless Chrome via CDP, navigates to TestForge, interacts with Hardening Lab,
exercises the Cancel Hardening flow, captures DOM states and screenshots.
"""

import os
import sys
import time
import json
import base64
import asyncio
import subprocess
import requests
import websockets
from pathlib import Path

CHROME_BIN = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
BASE_URL = "http://127.0.0.1:8000"
CDP_PORT = 9228
SCREENSHOT_DIR = Path("qa_artifacts/cancellation_verification_20261022/screenshots")
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)


async def run_browser_audit():
    import tempfile
    profile_dir = tempfile.mkdtemp(prefix="chrome_cdp_audit_")
    chrome_cmd = [
        CHROME_BIN,
        f"--remote-debugging-port={CDP_PORT}",
        f"--user-data-dir={profile_dir}",
        "--headless=new",
        "--disable-gpu",
        "--no-first-run",
        "--no-default-browser-check",
        "--window-size=1440,900",
        "about:blank",
    ]
    print(f"[1/7] Launching Chrome on port {CDP_PORT}...")
    chrome_proc = subprocess.Popen(chrome_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    await asyncio.sleep(1.5)

    # Retry loop to connect to CDP
    ws_url = None
    for _ in range(25):
        await asyncio.sleep(0.3)
        try:
            targets = requests.get(f"http://127.0.0.1:{CDP_PORT}/json/list", timeout=2).json()
            page_targets = [t for t in targets if t.get("type") == "page"]
            if page_targets:
                ws_url = page_targets[0]["webSocketDebuggerUrl"]
                break
        except Exception:
            pass

    if not ws_url:
        chrome_proc.terminate()
        raise RuntimeError(f"Could not connect to Chrome CDP on port {CDP_PORT}")

    results = {}
    try:
        print(f"[2/7] Connected to CDP WebSocket: {ws_url}")

        async with websockets.connect(ws_url, max_size=50 * 1024 * 1024, ping_interval=None) as ws:
            req_id = 0

            async def send_cmd(method, params=None, timeout=15):
                nonlocal req_id
                req_id += 1
                cmd_id = req_id
                msg = {"id": cmd_id, "method": method, "params": params or {}}
                await ws.send(json.dumps(msg))

                async def _wait_response():
                    while True:
                        raw = await ws.recv()
                        res = json.loads(raw)
                        if res.get("id") == cmd_id:
                            return res

                return await asyncio.wait_for(_wait_response(), timeout=timeout)

            async def eval_js(expr, timeout=10):
                res = await send_cmd(
                    "Runtime.evaluate",
                    {
                        "expression": expr,
                        "returnByValue": True,
                        "awaitPromise": True,
                    },
                    timeout=timeout
                )
                return res.get("result", {}).get("result", {}).get("value")

            async def capture_screenshot(filename: str):
                r = await send_cmd("Page.captureScreenshot", {"format": "png"}, timeout=15)
                b64_data = r.get("result", {}).get("data", "")
                if b64_data:
                    dest = SCREENSHOT_DIR / filename
                    dest.write_bytes(base64.b64decode(b64_data))
                    print(f"Captured screenshot: {dest} ({len(b64_data)//1024} KB)")

            # 1. Enable domains
            await send_cmd("Page.enable")
            await send_cmd("Runtime.enable")
            print(f"[3/7] Navigating to {BASE_URL}...")
            await send_cmd("Page.navigate", {"url": BASE_URL})

            # Wait for document to load completely
            for _ in range(40):
                await asyncio.sleep(0.3)
                try:
                    ready_state = await eval_js("document.readyState")
                    has_run_btn = await eval_js("!!document.getElementById('btn-run-hardening')")
                    if ready_state == "complete" and has_run_btn:
                        break
                except Exception:
                    pass

            title = await eval_js("document.title")
            print(f"Page title loaded: '{title}'")
            results["title"] = title

            # 2. Select Hardening Lab tab
            print("[4/7] Selecting Hardening Lab tab...")
            await eval_js("document.querySelector('[data-tab=\"tab-hardening\"]').click()")
            await asyncio.sleep(0.5)

            # Check initial button states
            cancel_btn_hidden = await eval_js("document.getElementById('btn-cancel-hardening').classList.contains('hidden')")
            run_btn_visible = await eval_js("!document.getElementById('btn-run-hardening').disabled")
            print(f"Initial state: cancel_btn_hidden={cancel_btn_hidden}, run_btn_visible={run_btn_visible}")
            results["initial_cancel_btn_hidden"] = cancel_btn_hidden
            results["initial_run_btn_enabled"] = run_btn_visible
            await capture_screenshot("01_hardening_lab_initial.png")

            # 3. Ensure a target module is loaded
            print("[5/7] Ensuring target module is loaded...")
            active_src = await eval_js("window.__testforge_state && window.__testforge_state.activeTarget ? window.__testforge_state.activeTarget.sourceCode : ''")
            if not active_src:
                await eval_js("document.querySelector('[data-tab=\"tab-ingest\"]').click()")
                await asyncio.sleep(0.5)
                await eval_js("document.getElementById('btn-load-sample').click()")
                await asyncio.sleep(1.5)
                await eval_js("document.querySelector('[data-tab=\"tab-hardening\"]').click()")
                await asyncio.sleep(0.5)

            active_target = await eval_js("window.__testforge_state.activeTarget ? window.__testforge_state.activeTarget.filePath : 'samples/discount.py'")
            print(f"Active target file: {active_target}")
            results["active_target"] = active_target

            # 4. Click Run Hardening
            print("[6/7] Triggering Run Hardening...")
            await eval_js("document.getElementById('btn-run-hardening').click()")

            # Wait until job ID is set and cancel button is visible
            job_id = None
            for _ in range(40):
                await asyncio.sleep(0.2)
                job_id = await eval_js("window.__testforge_state.hardening.jobId")
                cancel_visible = await eval_js("!document.getElementById('btn-cancel-hardening').classList.contains('hidden')")
                if job_id and cancel_visible:
                    break

            cancel_btn_revealed = await eval_js("!document.getElementById('btn-cancel-hardening').classList.contains('hidden')")
            cancel_btn_text = await eval_js("document.getElementById('btn-cancel-hardening').innerText.trim()")
            print(f"Active run started: jobId={job_id}, cancel_btn_revealed={cancel_btn_revealed}, text='{cancel_btn_text}'")
            results["job_id"] = job_id
            results["cancel_btn_revealed"] = cancel_btn_revealed
            results["cancel_btn_text"] = cancel_btn_text
            await capture_screenshot("02_hardening_active_with_cancel_btn.png")

            # 5. Click Cancel Hardening
            print("[7/7] Clicking Cancel Hardening button...")
            await eval_js("document.getElementById('btn-cancel-hardening').click()")
            await asyncio.sleep(0.3)

            cancelling_btn_disabled = await eval_js("document.getElementById('btn-cancel-hardening').disabled")
            cancelling_text = await eval_js("document.getElementById('btn-cancel-hardening').innerText.trim()")
            print(f"Cancelling state: disabled={cancelling_btn_disabled}, text='{cancelling_text}'")
            results["cancelling_disabled"] = cancelling_btn_disabled
            results["cancelling_text"] = cancelling_text
            await capture_screenshot("03_cancellation_requested.png")

            # 6. Wait for job to reach CANCELLED terminal state and update UI
            print("Polling for CANCELLED terminal status and verdict banner...")
            for i in range(120):
                await asyncio.sleep(0.5)
                h_status = await eval_js("window.__testforge_state.hardening.status")
                banner_hidden = await eval_js("document.getElementById('hardening-verdict-banner').classList.contains('hidden')")
                if (i + 1) % 5 == 0 or h_status == "CANCELLED":
                    print(f"Poll #{i+1}: hardening.status='{h_status}', banner_hidden={banner_hidden}")
                if h_status == "CANCELLED" and not banner_hidden:
                    break

            banner_visible = await eval_js("!document.getElementById('hardening-verdict-banner').classList.contains('hidden')")
            banner_class = await eval_js("document.getElementById('hardening-verdict-banner').className")
            banner_html = await eval_js("document.getElementById('hardening-verdict-banner').innerHTML")
            run_btn_re_enabled = await eval_js("!document.getElementById('btn-run-hardening').disabled")
            cancel_btn_hidden_final = await eval_js("document.getElementById('btn-cancel-hardening').classList.contains('hidden')")

            print(f"Terminal verdict observed:")
            print(f"  banner_visible={banner_visible}")
            print(f"  banner_class='{banner_class}'")
            print(f"  run_btn_re_enabled={run_btn_re_enabled}")
            print(f"  cancel_btn_hidden_final={cancel_btn_hidden_final}")

            results["banner_visible"] = banner_visible
            results["banner_class"] = banner_class
            results["banner_has_cancelled_text"] = "Cancelled" in banner_html or "cancelled" in banner_html.lower()
            results["run_btn_re_enabled"] = run_btn_re_enabled
            results["cancel_btn_hidden_final"] = cancel_btn_hidden_final
            await capture_screenshot("04_cancellation_completed_verdict.png")

            # Save json results
            res_json_path = SCREENSHOT_DIR.parent / "browser_audit_results.json"
            res_json_path.write_text(json.dumps(results, indent=2), encoding="utf-8")
            print(f"\nBrowser E2E Verification Results Summary written to {res_json_path}")
            print(json.dumps(results, indent=2))

            assert results["initial_cancel_btn_hidden"] is True, "Cancel button was not initially hidden"
            assert results["cancel_btn_revealed"] is True, "Cancel button was not revealed when hardening started"
            assert results["banner_visible"] is True, "Verdict banner was not visible after cancellation"
            assert "cancelled" in results["banner_class"], "Verdict banner did not receive .cancelled class"
            assert results["run_btn_re_enabled"] is True, "Run button was not re-enabled after cancellation"
            assert results["cancel_btn_hidden_final"] is True, "Cancel button was not hidden after cancellation"
            print("\n>>> ALL BROWSER UI CHECKS PASSED SUCCESSFULLY! <<<")

    finally:
        chrome_proc.terminate()
        try:
            chrome_proc.wait(timeout=3)
        except Exception:
            chrome_proc.kill()


if __name__ == "__main__":
    asyncio.run(run_browser_audit())
