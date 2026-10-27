# TestForge — Baseline Runtime & Environment Status

**Date:** 2026-10-27 08:34:30 IST  
**Environment:** macOS Apple Silicon (arm64, Darwin 24.6.0)  
**Backend:** FastAPI / Uvicorn listening on `http://127.0.0.1:8000` (PID: 17886)  
**Visible Browser:** Google Chrome v156.0.8078.48 (Headed, visible window on Mac display, CDP remote port: 9222)  
**Artifact Directory:** `qa_artifacts/visible_browser_playground_20261027_083200/`  

---

## 1. Process & Port Status

- **ASGI Server PID:** 17886 (`.venv-release/bin/python -m uvicorn server:app --host 127.0.0.1 --port 8000`)
- **Listening Address:** `127.0.0.1:8000`
- **Readiness Probe (`GET /readyz`):**
  ```json
  {
    "status": "ready",
    "service": "testforge-backend",
    "subsystems": {
      "ast_mutator": "operational",
      "blackboard": "operational",
      "sandbox_storage": "operational",
      "sqlite_persistence": "operational"
    }
  }
  ```
- **WebSocket Streaming Hub:** Initialized and bound to `ws://127.0.0.1:8000/ws`

---

## 2. Visible Browser State

- **Browser Executable:** `/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`
- **Window Mode:** Headed (visible window on user desktop)
- **Debugging Transport:** Chrome DevTools Protocol over WebSocket (`ws://127.0.0.1:9222/devtools/page/...`)
- **Active URL:** `http://127.0.0.1:8000/`
- **Active Target Document Title:** `TestForge — Autonomous Agentic Test Hardening`
