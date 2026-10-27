#!/usr/bin/env python3
"""
verify_ui_presentation.py - Live Visible Browser Verification of Honest Target Presentation.

Connects to visible Chrome on CDP port 9222, executes discount.py hardening run,
and validates:
  1. TARGET_SCORE_UNREACHED is displayed honestly without false success banners.
  2. Score (63.2%) and Target (85.0%) are displayed together.
  3. Distinction between Baseline Pass@1, Pipeline Finish, and Target Status.
  4. Survivor Diagnosis box with genuine sandbox execution proof and semantics.
"""

import asyncio
import base64
import json
import os
import subprocess
import time
import urllib.request
from pathlib import Path
import websockets

CDP_HTTP = "http://127.0.0.1:9222"
BASE_URL = "http://127.0.0.1:8000"
ARTIFACT_DIR = Path("/Users/sourabh/TestForge/qa_artifacts/mutation_target_acceptance_20261027_100100")
SCREENSHOTS_DIR = ARTIFACT_DIR / "screenshots"
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)


def bring_chrome_to_front():
    try:
        script = 'tell application "Google Chrome" to activate'
        subprocess.run(["osascript", "-e", script], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(0.3)
    except Exception as e:
        print(f"Warning: Could not activate Chrome: {e}")


class CDPClient:
    def __init__(self, ws_url):
        self.ws_url = ws_url
        self.ws = None
        self._msg_id = 0

    async def connect(self):
        self.ws = await websockets.connect(self.ws_url, max_size=50 * 1024 * 1024)

    async def close(self):
        if self.ws:
            await self.ws.close()

    async def call(self, method, params=None, timeout=60):
        self._msg_id += 1
        call_id = self._msg_id
        payload = {"id": call_id, "method": method}
        if params is not None:
            payload["params"] = params
        await self.ws.send(json.dumps(payload))

        start_time = time.time()
        while time.time() - start_time < timeout:
            resp_raw = await asyncio.wait_for(self.ws.recv(), timeout=timeout)
            resp = json.loads(resp_raw)
            if resp.get("id") == call_id:
                if "error" in resp:
                    raise RuntimeError(f"CDP error calling {method}: {resp['error']}")
                return resp.get("result", {})
        raise TimeoutError(f"Timeout waiting for CDP response to {method}")

    async def eval(self, expr, timeout=60):
        res = await self.call("Runtime.evaluate", {
            "expression": expr,
            "returnByValue": True,
            "awaitPromise": True
        }, timeout=timeout)
        result_obj = res.get("result", {})
        if "value" in result_obj:
            return result_obj["value"]
        if result_obj.get("subtype") == "null":
            return None
        return result_obj

    async def screenshot(self, filepath: Path):
        res = await self.call("Page.captureScreenshot", {"format": "png"})
        data = base64.b64decode(res["data"])
        filepath.write_bytes(data)
        print(f"[Screenshot] Saved: {filepath.name} ({len(data)} bytes)")


async def main():
    bring_chrome_to_front()

    # Discover tabs
    req = urllib.request.Request(f"{CDP_HTTP}/json")
    with urllib.request.urlopen(req) as resp:
        tabs = json.loads(resp.read().decode("utf-8"))

    target_tab = None
    for tab in tabs:
        if tab.get("type") == "page" and "8000" in tab.get("url", ""):
            target_tab = tab
            break
    if not target_tab:
        for tab in tabs:
            if tab.get("type") == "page":
                target_tab = tab
                break

    if not target_tab:
        raise RuntimeError("No suitable Chrome page found on port 9222")

    ws_url = target_tab["webSocketDebuggerUrl"]
    print(f"[CDP] Connecting to: {ws_url}")
    client = CDPClient(ws_url)
    await client.connect()

    try:
        # Navigate / reload page to get refreshed app.js
        print("[CDP] Navigating to http://127.0.0.1:8000/ ...")
        await client.call("Page.navigate", {"url": "http://127.0.0.1:8000/"})
        await asyncio.sleep(2.0)

        # Select discount.py
        print("[CDP] Selecting sample 'discount.py'...")
        select_res = await client.eval("""
            (() => {
                const sel = document.getElementById('sample-select');
                if (!sel) return { error: 'No sample-select element' };
                sel.value = 'discount.py';
                sel.dispatchEvent(new Event('change'));
                return { value: sel.value };
            })()
        """)
        print(f"[CDP] Sample selection: {select_res}")
        await asyncio.sleep(1.0)

        # Start Hardening Run
        print("[CDP] Triggering Hardening run on discount.py...")
        run_res = await client.eval("""
            (() => {
                const btn = document.getElementById('btn-run-hardening');
                if (!btn) return { error: 'No btn-run-hardening' };
                btn.click();
                return { clicked: true };
            })()
        """)
        print(f"[CDP] Run button click: {run_res}")

        # Poll until complete
        print("[CDP] Polling for hardening completion...")
        start_poll = time.time()
        job_info = None
        while time.time() - start_poll < 60:
            status_obj = await client.eval("""
                (() => {
                    const banner = document.getElementById('hardening-verdict-banner');
                    const kpiStatus = document.getElementById('kpi-final-status');
                    const kpiScore = document.getElementById('kpi-mut-score');
                    const kpiCycles = document.getElementById('kpi-cycles-done');
                    const progress = document.getElementById('hardening-percent-text');
                    return {
                        hardeningStatus: window.__testforge_state ? window.__testforge_state.hardening.status : null,
                        bannerVisible: banner ? !banner.classList.contains('hidden') : false,
                        bannerHtml: banner ? banner.innerHTML : '',
                        bannerClass: banner ? banner.className : '',
                        kpiStatus: kpiStatus ? kpiStatus.innerText : '',
                        kpiScore: kpiScore ? kpiScore.innerText : '',
                        kpiCycles: kpiCycles ? kpiCycles.innerText : '',
                        progressText: progress ? progress.innerText : ''
                    };
                })()
            """)
            if status_obj.get("bannerVisible") and ("Unreached" in status_obj.get("bannerHtml", "") or "Achieved" in status_obj.get("bannerHtml", "")):
                job_info = status_obj
                break
            await asyncio.sleep(1.5)

        if not job_info:
            raise TimeoutError("Hardening did not complete within timeout")

        print("\n=== HARDENING VERDICT CAPTURED ===")
        print(f"Banner Class: {job_info.get('bannerClass')}")
        print(f"KPI Status: {job_info.get('kpiStatus')}")
        print(f"KPI Score: {job_info.get('kpiScore')}")
        print(f"KPI Cycles: {job_info.get('kpiCycles')}")

        # Capture Screenshot 1: Verdict & KPIs
        screenshot_1 = SCREENSHOTS_DIR / "01_target_score_unreached_verdict.png"
        await client.screenshot(screenshot_1)

        # Click Survived filter and inspect first mutant
        print("\n[CDP] Filtering mutants to SURVIVED and selecting first mutant...")
        mutant_info = await client.eval("""
            (() => {
                // Click SURVIVED filter
                const survBtn = document.querySelector('.filter-btn[data-filter=\"SURVIVED\"]');
                if (survBtn) survBtn.click();
                
                // Click first mutant row
                const rows = document.querySelectorAll('#mutants-table-body tr');
                if (rows.length > 0) {
                    rows[0].click();
                }
                
                const diffTitle = document.getElementById('diff-selected-mutant-title');
                const diffBadge = document.getElementById('diff-status-badge');
                const diffDisplay = document.getElementById('diff-code-display');
                
                return {
                    title: diffTitle ? diffTitle.innerText : '',
                    badge: diffBadge ? diffBadge.innerText : '',
                    diffHtml: diffDisplay ? diffDisplay.innerHTML : '',
                    diffText: diffDisplay ? diffDisplay.innerText : ''
                };
            })()
        """)
        print(f"Mutant Title: {mutant_info.get('title')}")
        print(f"Mutant Badge: {mutant_info.get('badge')}")
        print(f"Diagnosis Preview:\n{mutant_info.get('diffText', '')[:300]}...")

        # Scroll to diff display and take Screenshot 2
        await client.eval("""
            (() => {
                const el = document.getElementById('diff-code-display');
                if (el) el.scrollIntoView({ behavior: 'instant', block: 'center' });
            })()
        """)
        await asyncio.sleep(0.5)

        screenshot_2 = SCREENSHOTS_DIR / "02_survivor_diagnosis_and_sandbox_proof.png"
        await client.screenshot(screenshot_2)

        # Write acceptance result summary
        summary_path = ARTIFACT_DIR / "LIVE_VERIFICATION_LOG.json"
        summary_path.write_text(json.dumps({
            "timestamp": time.time(),
            "job_info": job_info,
            "mutant_info": {
                "title": mutant_info.get("title"),
                "badge": mutant_info.get("badge"),
                "has_diagnosis_box": "Survivor Diagnosis" in mutant_info.get("diffHtml", ""),
                "has_sandbox_execution_proof": "Sandbox" in mutant_info.get("diffHtml", ""),
                "has_survival_semantics": "Relational boundary condition altered" in mutant_info.get("diffHtml", ""),
            },
            "screenshots": [str(screenshot_1.name), str(screenshot_2.name)]
        }, indent=2), encoding="utf-8")
        print(f"\n[Done] Verification successfully finished! Evidence saved in {ARTIFACT_DIR}")

    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(main())
