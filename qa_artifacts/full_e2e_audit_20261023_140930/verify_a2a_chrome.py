"""
verify_a2a_chrome.py - End-to-end Chrome CDP verification of the upgraded A2A Card button and modal.
"""

import sys
import json
import base64
import asyncio
import subprocess
import requests
import websockets
from pathlib import Path

CHROME_BIN = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
BASE_URL = "http://127.0.0.1:8000"
CDP_PORT = 9231
QA_DIR = Path("/Users/sourabh/TestForge/qa_artifacts/full_e2e_audit_20261023_140930")
SCREENSHOT_DIR = QA_DIR / "screenshots"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)

RESULTS = {}

async def main():
    import tempfile
    profile_dir = tempfile.mkdtemp(prefix="chrome_a2a_verify_")

    chrome_cmd = [
        CHROME_BIN,
        f"--remote-debugging-port={CDP_PORT}",
        f"--user-data-dir={profile_dir}",
        "--disable-gpu",
        "--no-first-run",
        "--no-default-browser-check",
        "--window-size=1440,900",
        "about:blank",
    ]
    print(f"[LAUNCH] Starting Chrome CDP on port {CDP_PORT}...")
    chrome_proc = subprocess.Popen(chrome_cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    await asyncio.sleep(2.0)

    ws_url = None
    for _ in range(30):
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
        raise RuntimeError("Failed to connect to Chrome CDP.")

    print(f"[CDP] Connected: {ws_url}")

    async with websockets.connect(ws_url, max_size=50 * 1024 * 1024, ping_interval=None) as ws:
        req_id = 0

        async def send_cmd(method, params=None, timeout=20):
            nonlocal req_id
            req_id += 1
            cmd_id = req_id
            msg = {"id": cmd_id, "method": method, "params": params or {}}
            await ws.send(json.dumps(msg))

            async def _wait():
                while True:
                    raw = await ws.recv()
                    data = json.loads(raw)
                    if data.get("id") == cmd_id:
                        return data
            return await asyncio.wait_for(_wait(), timeout=timeout)

        async def eval_js(expr):
            res = await send_cmd("Runtime.evaluate", {
                "expression": expr,
                "returnByValue": True,
                "awaitPromise": True
            })
            return res.get("result", {}).get("result", {}).get("value")

        async def take_screenshot(name):
            res = await send_cmd("Page.captureScreenshot", {"format": "png"})
            b64 = res.get("result", {}).get("data", "")
            if b64:
                dest = SCREENSHOT_DIR / f"{name}.png"
                dest.write_bytes(base64.b64decode(b64))
                print(f"  📸 Screenshot saved: {dest.name}")
                return str(dest)
            return None

        await send_cmd("Page.enable")
        await send_cmd("Runtime.enable")
        await send_cmd("DOM.enable")

        # 1. Navigate to Dashboard
        print("\n[1/6] Navigating to TestForge Dashboard...")
        await send_cmd("Page.navigate", {"url": BASE_URL})
        await asyncio.sleep(2.0)
        await take_screenshot("a2a_01_dashboard")

        btn_exists = await eval_js("!!document.getElementById('btn-a2a-card')")
        btn_tag = await eval_js("document.getElementById('btn-a2a-card').tagName")
        print(f"A2A Card Button: exists={btn_exists}, tag={btn_tag}")
        assert btn_exists and btn_tag == "BUTTON", "A2A button must be present as a semantic BUTTON"

        # 2. Click A2A Card Button
        print("\n[2/6] Clicking A2A Card button...")
        await eval_js("document.getElementById('btn-a2a-card').click()")
        await asyncio.sleep(1.2)

        modal_open = await eval_js("!document.getElementById('a2a-modal-backdrop').classList.contains('hidden')")
        content_visible = await eval_js("!document.getElementById('a2a-card-content').classList.contains('hidden')")
        print(f"Modal Open: {modal_open}, Content Visible: {content_visible}")
        assert modal_open and content_visible, "A2A modal and content must be visible"

        # Read rendered fields
        card_name = await eval_js("document.querySelector('#a2a-card-content h3')?.textContent")
        skills_count = await eval_js("document.querySelectorAll('#a2a-card-content h4 + div > div').length")
        raw_href = await eval_js("document.getElementById('btn-view-raw-a2a')?.getAttribute('href')")
        print(f"Rendered Name: '{card_name}', Skills Rendered: {skills_count}, Raw Link: '{raw_href}'")
        assert "testforge" in card_name.lower(), f"Unexpected name: {card_name}"
        assert skills_count >= 3, f"Expected at least 3 skills, got {skills_count}"
        assert raw_href == "/.well-known/agent-card.json", f"Unexpected raw link: {raw_href}"

        await take_screenshot("a2a_02_card_modal")

        # 3. Test Copy JSON Action
        print("\n[3/6] Testing Copy JSON button...")
        await eval_js("document.getElementById('btn-copy-a2a-json').click()")
        await asyncio.sleep(0.5)
        toast_msg = await eval_js("document.querySelector('.toast-message')?.textContent")
        print(f"Toast message after Copy click: '{toast_msg}'")

        # 4. Test Close Button
        print("\n[4/6] Testing Close Button...")
        await eval_js("document.getElementById('btn-close-a2a-modal').click()")
        await asyncio.sleep(0.4)
        modal_hidden = await eval_js("document.getElementById('a2a-modal-backdrop').classList.contains('hidden')")
        print(f"Modal hidden after close: {modal_hidden}")
        assert modal_hidden, "Modal should be hidden after clicking close button"

        # 5. Test Escape Key Dismiss
        print("\n[5/6] Testing Escape Key Dismiss...")
        await eval_js("window.__testforge.openA2aModal()")
        await asyncio.sleep(0.6)
        reopened = await eval_js("!document.getElementById('a2a-modal-backdrop').classList.contains('hidden')")
        assert reopened, "Modal should reopen"
        await send_cmd("Input.dispatchKeyEvent", {"type": "keyDown", "key": "Escape", "code": "Escape"})
        await asyncio.sleep(0.4)
        escaped_hidden = await eval_js("document.getElementById('a2a-modal-backdrop').classList.contains('hidden')")
        print(f"Modal hidden after Escape key: {escaped_hidden}")
        assert escaped_hidden, "Modal should close on Escape key"

        # 6. Capture Raw JSON Endpoint in Chrome
        print("\n[6/6] Navigating to Raw AgentCard Endpoint...")
        await send_cmd("Page.navigate", {"url": f"{BASE_URL}/.well-known/agent-card.json"})
        await asyncio.sleep(1.5)
        raw_text = await eval_js("document.body.innerText || document.body.textContent")
        print(f"Raw JSON Length: {len(raw_text)} chars")
        parsed = json.loads(raw_text)
        assert parsed.get("name") == "testforge-agent-system"
        await take_screenshot("a2a_03_raw_json_endpoint")

        # Return to Dashboard
        await send_cmd("Page.navigate", {"url": BASE_URL})
        await asyncio.sleep(1.5)
        await take_screenshot("a2a_04_dashboard_restored")

    chrome_proc.terminate()
    print("\n[SUCCESS] All Chrome A2A Card verifications passed!")

if __name__ == "__main__":
    asyncio.run(main())
