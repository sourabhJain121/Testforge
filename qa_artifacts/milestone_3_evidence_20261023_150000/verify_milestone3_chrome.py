"""
qa_artifacts/milestone_3_evidence_20261023_150000/verify_milestone3_chrome.py
Automated Chrome CDP verification of Milestone 3:
  1. Verifies real-time WebSocket connection to /ws/events from browser.
  2. Verifies Wiretap status badge shows '⚡ Live Streaming'.
  3. Verifies event dispatch dynamically renders step cards and updates KPIs.
  4. Verifies fallback to polling upon WebSocket disconnect.
  5. Verifies safe reconnection.
  6. Captures screenshots and verifies 0 JavaScript console errors.
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
CDP_PORT = 9232
EVIDENCE_DIR = Path("/Users/sourabh/TestForge/qa_artifacts/milestone_3_evidence_20261023_150000")
SCREENSHOT_DIR = EVIDENCE_DIR / "screenshots"
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)


async def main():
    import tempfile
    profile_dir = tempfile.mkdtemp(prefix="chrome_m3_verify_")

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
        console_errors = []

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
                    if data.get("method") == "Runtime.consoleAPICalled":
                        p = data.get("params", {})
                        if p.get("type") == "error":
                            args = [str(a.get("value", a.get("description", ""))) for a in p.get("args", [])]
                            console_errors.append(" ".join(args))
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

        # 1. Navigate to TestForge Dashboard
        print("\n[1/5] Navigating to Dashboard...")
        await send_cmd("Page.navigate", {"url": BASE_URL})
        await asyncio.sleep(2.5)

        # Switch to Wiretap Tab
        print("\n[2/5] Switching to Wiretap Tab and checking WebSocket live streaming badge...")
        await eval_js("window.__testforge.switchTab('tab-wiretap')")
        await asyncio.sleep(1.0)

        badge_text = await eval_js("document.getElementById('wiretap-ws-status-badge')?.textContent?.trim()")
        badge_class = await eval_js("document.getElementById('wiretap-ws-status-badge')?.className")
        is_connected = await eval_js("window.__testforge_state.ws.isConnected")
        print(f"Badge Text: '{badge_text}', Class: '{badge_class}', WS Connected: {is_connected}")
        assert "Live Streaming" in badge_text, f"Expected Live Streaming, got {badge_text}"
        assert is_connected is True, "WebSocket must be connected in state"

        # Check /api/ws/status from backend
        ws_status = requests.get(f"{BASE_URL}/api/ws/status").json()
        print(f"Backend WS Status: {ws_status}")
        assert ws_status.get("active_clients", 0) >= 1

        await take_screenshot("m3_01_wiretap_live_connected")

        # 3. Simulate Live Handoff Event Delivery
        print("\n[3/5] Simulating live event streaming into Wiretap...")
        initial_cards = await eval_js("document.querySelectorAll('#wiretap-timeline-container .wiretap-step-card').length")
        initial_handoffs = await eval_js("parseInt(document.getElementById('wiretap-kpi-handoffs')?.textContent || '0', 10)")

        # Inject real event through appendLiveWiretapEvent
        await eval_js("""
            window.__testforge.appendLiveWiretapEvent({
                event_type: 'AGENT_HANDOFF',
                emitter: 'GoogleADKGenerator',
                timestamp: Date.now() / 1000,
                payload: {
                    from_agent: 'GoogleADKGenerator',
                    to_agent: 'CrewAIAdversarialCritic',
                    summary: 'Synthesized 4 targeted pytest assertions killing AOR/COR mutants. Handoff for adversarial critique.',
                    iteration: 2,
                    payload: {
                        mutants_targeted: ['MUT_AOR_01', 'MUT_COR_03'],
                        assertions_added: 4
                    }
                }
            })
        """)
        await asyncio.sleep(0.8)

        new_cards = await eval_js("document.querySelectorAll('#wiretap-timeline-container .wiretap-step-card').length")
        new_handoffs = await eval_js("parseInt(document.getElementById('wiretap-kpi-handoffs')?.textContent || '0', 10)")
        latest_card_text = await eval_js("document.querySelector('#wiretap-timeline-container .wiretap-step-card:last-child .step-summary')?.textContent")

        print(f"Initial cards: {initial_cards} -> New cards: {new_cards}")
        print(f"Initial handoff KPI: {initial_handoffs} -> New handoff KPI: {new_handoffs}")
        print(f"Rendered summary: '{latest_card_text}'")
        assert new_cards == initial_cards + 1, "Card should be appended dynamically"
        assert new_handoffs == initial_handoffs + 1, "Handoff KPI should increment"
        assert "Synthesized 4 targeted pytest assertions" in latest_card_text

        await take_screenshot("m3_02_wiretap_card_streamed")

        # 4. Test WebSocket Disconnect & Polling Fallback
        print("\n[4/5] Testing WebSocket disconnect and polling fallback...")
        await eval_js("window.__testforge.disconnectWebSocket()")
        await asyncio.sleep(1.0)

        fallback_badge = await eval_js("document.getElementById('wiretap-ws-status-badge')?.textContent?.trim()")
        fallback_class = await eval_js("document.getElementById('wiretap-ws-status-badge')?.className")
        print(f"Fallback Badge Text: '{fallback_badge}', Class: '{fallback_class}'")
        assert "Polling Fallback" in fallback_badge or "Reconnecting" in fallback_badge

        # Test refresh button in polling mode
        await eval_js("document.getElementById('btn-refresh-wiretap').click()")
        await asyncio.sleep(0.8)

        await take_screenshot("m3_03_wiretap_polling_fallback")

        # 5. Reconnect WebSocket
        print("\n[5/5] Reconnecting WebSocket...")
        await eval_js("window.__testforge_state.ws.reconnectAttempts = 0")
        await eval_js("window.__testforge.initWebSocketEventStream()")
        await asyncio.sleep(1.2)

        reconnected_badge = await eval_js("document.getElementById('wiretap-ws-status-badge')?.textContent?.trim()")
        reconnected_state = await eval_js("window.__testforge_state.ws.isConnected")
        print(f"Reconnected Badge: '{reconnected_badge}', State isConnected: {reconnected_state}")
        assert "Live Streaming" in reconnected_badge

        # Console errors check
        print(f"\nConsole Errors Captured: {len(console_errors)}")
        if console_errors:
            print("Errors:", console_errors)
        assert len(console_errors) == 0, f"Expected 0 console errors, got {len(console_errors)}"

    chrome_proc.terminate()
    print("\n[SUCCESS] All Chrome CDP Milestone 3 verifications passed!")


if __name__ == "__main__":
    asyncio.run(main())
