import asyncio
import base64
import csv
import json
import os
import subprocess
import time
import urllib.request
from pathlib import Path
import websockets

ARTIFACTS_DIR = Path("/Users/sourabh/TestForge/qa_artifacts/baseline_verdict_consistency_20261027_095000")
SCREENSHOTS_DIR = ARTIFACTS_DIR / "screenshots"
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

CDP_HTTP_URL = "http://127.0.0.1:9222"
BASE_URL = "http://127.0.0.1:8000"

SAMPLE_FILES = [
    "discount.py",
    "banking.py",
    "inventory_pricing.py",
    "state_machine.py",
    "rate_limiter.py"
]

def activate_chrome():
    try:
        subprocess.run(["osascript", "-e", 'tell application "Google Chrome" to activate'], check=False)
        time.sleep(0.4)
    except Exception as e:
        print(f"Warning: Could not activate Google Chrome via osascript: {e}")

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
        print(f"[Screenshot] Saved: {filepath.name}")

def get_backend_status(job_id: str):
    url = f"{BASE_URL}/api/harden/status/{job_id}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))

async def run_verification():
    activate_chrome()
    tabs_raw = urllib.request.urlopen(f"{CDP_HTTP_URL}/json").read()
    tabs = json.loads(tabs_raw)
    target = next((t for t in tabs if t.get("type") == "page" and "8000" in t.get("url", "")), None)
    if not target:
        raise RuntimeError("Could not find TestForge tab on port 8000 in Chrome")

    print(f"Connecting to visible Chrome tab: {target['title']} ({target['id']})")
    cdp = CDPClient(target["webSocketDebuggerUrl"])
    await cdp.connect()

    await cdp.call("Page.enable")
    await cdp.call("Runtime.enable")

    print("Hard reloading visible Chrome...")
    await cdp.call("Page.reload", {"ignoreCache": True})
    await asyncio.sleep(2.5)
    activate_chrome()

    title = await cdp.eval("document.title")
    print(f"Page Title: {title}")

    metric_consistency_records = []

    for idx, filename in enumerate(SAMPLE_FILES, start=1):
        print(f"\n=======================================================")
        print(f"[{idx}/5] Verifying Sample: {filename}")
        print(f"=======================================================")
        activate_chrome()

        # Switch to Mode A (Workspace)
        await cdp.eval("window.__testforge ? window.__testforge.switchTab('tab-mode-a') : document.querySelector('#nav-mode-a').click()")
        await asyncio.sleep(0.5)

        # Select file and load sample
        select_script = f"""
        (() => {{
            const select = document.querySelector('#sample-file-select');
            select.value = '{filename}';
            select.dispatchEvent(new Event('change', {{ bubbles: true }}));
            document.querySelector('#btn-load-sample').click();
            return select.value;
        }})()
        """
        await cdp.eval(select_script)
        await asyncio.sleep(1.2)

        # Switch to Hardening Tab
        await cdp.eval("window.__testforge ? window.__testforge.switchTab('tab-hardening') : document.querySelector('#nav-hardening').click()")
        await asyncio.sleep(0.5)

        # Trigger Hardening
        old_job_id = await cdp.eval("window.__testforge ? window.__testforge.state.hardening.jobId : null")
        await cdp.eval("document.querySelector('#btn-run-hardening').click()")

        # Wait for fresh job ID
        job_id = None
        for _ in range(40):
            curr_id = await cdp.eval("window.__testforge ? window.__testforge.state.hardening.jobId : null")
            if curr_id and curr_id != old_job_id:
                job_id = curr_id
                break
            await asyncio.sleep(0.2)
        print(f"  • Running Job: {job_id}")

        # Poll for completion
        start_wait = time.time()
        completed = False
        while time.time() - start_wait < 140:
            activate_chrome()
            poll_info = await cdp.eval("""
            (() => {
                const btn = document.querySelector('#btn-run-hardening');
                const status = document.querySelector('#kpi-final-status') ? document.querySelector('#kpi-final-status').textContent.trim() : '';
                return {
                    disabled: btn ? btn.disabled : false,
                    status: status
                };
            })()
            """)
            if not poll_info["disabled"] and poll_info["status"] != "":
                completed = True
                break
            await asyncio.sleep(1.5)

        if not completed:
            print(f"  ❌ Timeout waiting for job {job_id}!")
            continue

        print(f"  ✓ Job {job_id} completed in {time.time() - start_wait:.1f}s")
        await asyncio.sleep(1.0)
        activate_chrome()

        # Read Rendered DOM Metrics across all 3 Rows
        dom_metrics = await cdp.eval("""
        (() => {
            return {
                baseGen: document.querySelector('#kpi-base-gen') ? document.querySelector('#kpi-base-gen').textContent.trim() : '',
                baseExec: document.querySelector('#kpi-base-exec') ? document.querySelector('#kpi-base-exec').textContent.trim() : '',
                basePass: document.querySelector('#kpi-base-pass') ? document.querySelector('#kpi-base-pass').textContent.trim() : '',
                baseFail: document.querySelector('#kpi-base-fail') ? document.querySelector('#kpi-base-fail').textContent.trim() : '',
                baseVerdict: document.querySelector('#kpi-base-verdict') ? document.querySelector('#kpi-base-verdict').textContent.trim() : '',
                linesCov: document.querySelector('#kpi-lines-cov') ? document.querySelector('#kpi-lines-cov').textContent.trim() : '',
                covPct: document.querySelector('#kpi-cov-pct') ? document.querySelector('#kpi-cov-pct').textContent.trim() : '',
                mutGen: document.querySelector('#kpi-mut-gen') ? document.querySelector('#kpi-mut-gen').textContent.trim() : '',
                mutExec: document.querySelector('#kpi-mut-exec') ? document.querySelector('#kpi-mut-exec').textContent.trim() : '',
                mutKill: document.querySelector('#kpi-mut-kill') ? document.querySelector('#kpi-mut-kill').textContent.trim() : '',
                mutSurv: document.querySelector('#kpi-mut-surv') ? document.querySelector('#kpi-mut-surv').textContent.trim() : '',
                mutErr: document.querySelector('#kpi-mut-err') ? document.querySelector('#kpi-mut-err').textContent.trim() : '',
                mutScore: document.querySelector('#kpi-mut-score') ? document.querySelector('#kpi-mut-score').textContent.trim() : '',
                cyclesDone: document.querySelector('#kpi-cycles-done') ? document.querySelector('#kpi-cycles-done').textContent.trim() : '',
                finalStatus: document.querySelector('#kpi-final-status') ? document.querySelector('#kpi-final-status').textContent.trim() : ''
            };
        })()
        """)

        # Fetch Backend Status
        backend_job = get_backend_status(job_id)
        fs = backend_job.get("final_state", {})

        b_base_gen = fs.get("baseline_tests_generated", 0)
        b_base_exec = fs.get("baseline_tests_executed", 0)
        b_base_pass = fs.get("baseline_tests_passed", 0)
        b_base_fail = fs.get("baseline_tests_failed", 0)
        b_base_verdict = "🟢 ALL PASSED" if fs.get("baseline_passed") else "🔴 HAS FAILURES"

        b_lines_cov = fs.get("lines_covered", 0)
        b_statements = fs.get("num_statements", 0)
        b_cov_pct = fs.get("baseline_line_coverage", 0.0)

        b_mut_gen = fs.get("mutants_generated", 0)
        b_mut_kill = fs.get("mutants_killed", 0)
        b_mut_surv = fs.get("mutants_survived", 0)
        b_mut_score = fs.get("final_mutation_score", 0.0)
        b_status = fs.get("final_hardening_status", backend_job.get("status"))

        # Verify Parity
        parity = (
            dom_metrics["basePass"] == str(b_base_pass) and
            dom_metrics["baseFail"] == str(b_base_fail) and
            dom_metrics["baseVerdict"] == b_base_verdict and
            dom_metrics["linesCov"] == f"{b_lines_cov} / {b_statements}" and
            dom_metrics["covPct"] == f"{b_cov_pct:.1f}%" and
            dom_metrics["mutGen"] == str(b_mut_gen) and
            dom_metrics["mutKill"] == str(b_mut_kill) and
            dom_metrics["mutSurv"] == str(b_mut_surv) and
            dom_metrics["mutScore"] == f"{b_mut_score:.1f}%" and
            dom_metrics["finalStatus"] == b_status
        )

        parity_str = "MATCH" if parity else "MISMATCH"
        print(f"  • Verified DOM Row 1 (Baseline Tests): Pass={dom_metrics['basePass']}, Fail={dom_metrics['baseFail']}, Verdict={dom_metrics['baseVerdict']}")
        print(f"  • Verified DOM Row 2 (Code Coverage):  Covered={dom_metrics['linesCov']} statements, Pct={dom_metrics['covPct']}")
        print(f"  • Verified DOM Row 2 (Mutations):      Gen={dom_metrics['mutGen']}, Kill={dom_metrics['mutKill']}, Surv={dom_metrics['mutSurv']}")
        print(f"  • Verified DOM Row 3 (Final Status):   Score={dom_metrics['mutScore']}, Status={dom_metrics['finalStatus']}")
        print(f"  • Overall DOM-to-Backend Parity:       {parity_str}")

        # Capture screenshot
        screenshot_path = SCREENSHOTS_DIR / f"{idx:02d}_{Path(filename).stem}_consistency_check.png"
        await cdp.screenshot(screenshot_path)

        metric_consistency_records.append({
            "job_id": job_id,
            "filename": filename,
            "baseline_tests_generated": b_base_gen,
            "baseline_tests_executed": b_base_exec,
            "baseline_tests_passed": b_base_pass,
            "baseline_tests_failed": b_base_fail,
            "baseline_clean_verdict": dom_metrics["baseVerdict"],
            "source_statements_total": b_statements,
            "source_statements_covered": b_lines_cov,
            "line_coverage_pct": dom_metrics["covPct"],
            "mutants_generated": b_mut_gen,
            "mutants_killed": b_mut_kill,
            "mutants_survived": b_mut_surv,
            "mutation_score": dom_metrics["mutScore"],
            "final_hardening_status": dom_metrics["finalStatus"],
            "dom_vs_backend_parity": parity_str,
            "screenshot": screenshot_path.name
        })

    # Write FINAL_METRIC_CONSISTENCY.csv
    csv_path = ARTIFACTS_DIR / "FINAL_METRIC_CONSISTENCY.csv"
    with open(csv_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "job_id", "filename", "baseline_tests_generated", "baseline_tests_executed",
            "baseline_tests_passed", "baseline_tests_failed", "baseline_clean_verdict",
            "source_statements_total", "source_statements_covered", "line_coverage_pct",
            "mutants_generated", "mutants_killed", "mutants_survived", "mutation_score",
            "final_hardening_status", "dom_vs_backend_parity", "screenshot"
        ])
        writer.writeheader()
        writer.writerows(metric_consistency_records)
    print(f"\n✓ Saved {csv_path.name}")

    await cdp.close()

if __name__ == "__main__":
    asyncio.run(run_verification())
