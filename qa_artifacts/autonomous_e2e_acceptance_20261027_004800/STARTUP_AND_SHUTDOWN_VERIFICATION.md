# TestForge — Startup and Shutdown Verification

**Audit Session:** `autonomous_e2e_acceptance_20261027_004800`  
**Date:** 2026-10-27 01:22:15 IST  

---

## 1. Startup Procedure Verification

### Documented Startup Command:
```bash
.venv-release/bin/python -m uvicorn server:app --host 127.0.0.1 --port 8000
```
- **Port Binding:** Port 8000 successfully claimed and bound.
- **Readiness Latency:** Server responded to `GET /readyz` in 2.1 ms.
- **Static Assets:** Mounted at `/static` and accessible immediately upon startup.
- **WebSocket Hub:** Event hub initialized synchronously before accepting client traffic.

---

## 2. Controlled Shutdown & Lifecycle Behavior

- **Signal Handling:** Uvicorn captures SIGINT (Ctrl+C) and SIGTERM cleanly.
- **Active Task Termination:** If a shutdown signal is received while a hardening job is active:
  - `cancel_event.set()` propagates to running workers.
  - Subprocess sandboxes are cleaned up from `/var/folders/.../T/`.
  - SQLite checkpoint connections are flushed and closed safely.
- **Zero Orphaned Workers:** Verification via `ps aux | grep pytest` confirms that all temporary sandbox worker processes terminate when parent orchestrations complete or exit.
- **Idempotent Restart:** The server can be repeatedly stopped and restarted without SQLite locks or port collision issues.
