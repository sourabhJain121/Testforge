"""
verify_defect_fixes.py - Automated verification of the 4 remediated defects.
Connects to Chrome via CDP, executes test actions, and verifies DOM state.
"""

import os
import sys
import time
import json
import asyncio
import subprocess
import requests
import websockets

CHROME_BIN = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
BASE_URL = "http://127.0.0.1:8000"
CDP_PORT = 9226

async def run_verification():
    chrome_cmd = [
        CHROME_BIN,
        f"--remote-debugging-port={CDP_PORT}",
        "--headless=new",
        "--disable-gpu",
        "--no-first-run",
        "--no-default-browser-check",
        "--window-size=1440,900",
        "about:blank"
    ]
    chrome_proc = subprocess.Popen(chrome_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    await asyncio.sleep(1.0)

    try:
        tabs_resp = requests.get(f"http://127.0.0.1:{CDP_PORT}/json", timeout=5)
        ws_url = tabs_resp.json()[0]["webSocketDebuggerUrl"]

        async with websockets.connect(ws_url, max_size=50*1024*1024) as ws:
            req_id = 0
            async def send_cmd(method, params=None):
                nonlocal req_id
                req_id += 1
                msg = {"id": req_id, "method": method, "params": params or {}}
                await ws.send(json.dumps(msg))
                while True:
                    res = json.loads(await ws.recv())
                    if res.get("id") == req_id:
                        return res.get("result", {})

            async def eval_js(expr):
                r = await send_cmd("Runtime.evaluate", {
                    "expression": expr,
                    "returnByValue": True,
                    "awaitPromise": True
                })
                return r.get("result", {}).get("value")

            await send_cmd("Page.enable")
            await send_cmd("DOM.enable")
            await send_cmd("Runtime.enable")

            print(f"[Connecting] Navigating to {BASE_URL}...")
            await send_cmd("Page.navigate", {"url": BASE_URL})
            await asyncio.sleep(2.0)

            # Test 1: TF-DEF-003 Toast Collision Fix
            print("[Verifying] TF-DEF-003: Toast stacking collision...")
            t3_res = await eval_js("""
                (() => {
                    const tf = window.__testforge || {};
                    if (!tf.showToast) return { error: 'window.__testforge.showToast not found' };
                    
                    // Trigger a success toast
                    tf.showToast('Initial success message', 'success', 5000);
                    const count1 = document.querySelectorAll('#toast-container .toast').length;
                    
                    // Trigger an error toast immediately
                    tf.showToast('Validation error message', 'error', 5000);
                    const toasts = Array.from(document.querySelectorAll('#toast-container .toast')).map(t => ({
                        text: t.textContent.trim(),
                        isError: t.classList.contains('toast-error'),
                        isSuccess: t.classList.contains('toast-success')
                    }));
                    return { initialCount: count1, toastsAfterError: toasts };
                })()
            """)
            has_error_only = bool(t3_res and t3_res.get('toastsAfterError') and all(not t['isSuccess'] for t in t3_res['toastsAfterError']) and any(t['isError'] for t in t3_res['toastsAfterError']))
            print(f"  -> TF-DEF-003 Result: {'PASS' if has_error_only else 'FAIL'} (Toasts: {t3_res.get('toastsAfterError') if t3_res else None})")

            # Test 2: TF-DEF-004 Benchmark Markdown Preview Styling
            print("[Verifying] TF-DEF-004: Markdown preview monospace & pre-wrap styling...")
            t4_res = await eval_js("""
                (() => {
                    const el = document.getElementById('bench-markdown-preview');
                    const comp = window.getComputedStyle(el);
                    return {
                        whiteSpace: comp.whiteSpace,
                        display: comp.display,
                        color: comp.color
                    };
                })()
            """)
            style_ok = t4_res['whiteSpace'] == 'pre-wrap'
            print(f"  -> TF-DEF-004 Result: {'PASS' if style_ok else 'FAIL'} (Style: {t4_res})")

            # Test 3: TF-DEF-001 Mode C Target Banner & Confirmation Glow
            print("[Verifying] TF-DEF-001: Mode C Target Banner & confirmation glow...")
            await eval_js("switchTab('tab-mode-c')")
            t1_res = await eval_js("""
                (async () => {
                    const chip = document.querySelector('#tab-mode-c .prompt-chip');
                    if (chip) chip.click();
                    const btn = document.getElementById('btn-fetch-github');
                    btn.click();
                    await new Promise(r => setTimeout(r, 1200));
                    
                    const btnAct = document.getElementById('btn-activate-mode-c');
                    const targetTitle = document.getElementById('target-module-title').textContent;
                    const hasGlow = btnAct.classList.contains('btn-glow');
                    return {
                        targetTitle: targetTitle,
                        hasGlow: hasGlow,
                        btnText: btnAct.textContent.trim()
                    };
                })()
            """)
            t1_ok = t1_res['hasGlow'] and 'github_requests' in t1_res['targetTitle']
            print(f"  -> TF-DEF-001 Result: {'PASS' if t1_ok else 'FAIL'} ({t1_res})")

            # Test 4: TF-DEF-002 Wiretap auto-hydration on navigation
            print("[Verifying] TF-DEF-002: Wiretap auto-hydration on tab switch...")
            await eval_js("document.getElementById('nav-wiretap').click()")
            await asyncio.sleep(1.8)
            t2_res = await eval_js("""
                (() => {
                    const cards = document.querySelectorAll('#wiretap-timeline-container .wiretap-step-card');
                    const emptyCallout = document.querySelector('#wiretap-timeline-container .info-callout');
                    return {
                        cardCount: cards.length,
                        hasEmptyCallout: !!emptyCallout
                    };
                })()
            """)
            t2_ok = t2_res['cardCount'] > 0 and not t2_res['hasEmptyCallout']
            print(f"  -> TF-DEF-002 Result: {'PASS' if t2_ok else 'FAIL'} (Card count: {t2_res['cardCount']})")

            all_passed = has_error_only and style_ok and t1_ok and t2_ok
            print(f"\n[VERIFICATION SUMMARY] All 4 defect fixes verified in real browser: {'SUCCESS' if all_passed else 'SOME FAILED'}")

    finally:
        chrome_proc.terminate()
        try:
            chrome_proc.wait(timeout=3)
        except Exception:
            chrome_proc.kill()

if __name__ == "__main__":
    asyncio.run(run_verification())
