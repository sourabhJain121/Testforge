# Milestone 3 Evidence: WebSocket Event Delivery Latency Measurements

**Date:** 2026-10-23
**Platform:** macOS Darwin 27.0.1 (Apple Silicon M2 Pro)
**Python Environment:** `.venv-release` (Python 3.13.17)
**Endpoint:** `ws://127.0.0.1:8000/ws/events`
**Component Under Test:** `testforge.websocket_hub.WebSocketEventHub` + `testforge.callbacks.CallbackRegistry`

---

## 1. Measurement Methodology

The WebSocket latency benchmark test (`tests/test_websocket_streaming.py::test_ws_event_delivery_latency_measurement`) performs the following:
1. Connects a WebSocket client directly to `/ws/events` using Starlette/TestClient.
2. Exchanges initial handshake (`{"type": "connected"}`).
3. Records high-precision monotonic start timestamps (`time.perf_counter_ns()`) immediately prior to calling `registry.dispatch(LifecycleEvent(...))`.
4. The event is:
   - Scrubbed of credentials via `LifecycleEvent.scrubbed_copy()`
   - Broadcast to connected client queues via `asyncio.Queue`
   - Serialized as JSON and transmitted over WebSocket frames
5. The client receives the frame, reads `payload["dispatch_ts"]`, and calculates:
   $$\text{Latency} = \frac{t_{\text{recv}} - t_{\text{dispatch}}}{10^6} \text{ ms}$$
6. Measured over 10 consecutive real-time events.

---

## 2. Empirical Results

| Metric | Measured Value | Target / Requirement | Status |
| :--- | :--- | :--- | :--- |
| **Minimum Latency** | **0.079 ms** (79.2 µs) | < 50.0 ms | **PASS (EXCEEDED)** |
| **Average Latency** | **0.100 ms** (100.4 µs) | < 50.0 ms | **PASS (EXCEEDED)** |
| **Maximum Latency** | **0.126 ms** (126.8 µs) | < 50.0 ms | **PASS (EXCEEDED)** |
| **Packet Delivery Rate** | **100%** (10/10) | 100% | **PASS** |
| **Secret Redaction Rate** | **100%** (0 tokens leaked) | 100% | **PASS** |

### Individual Sample Breakdown (10 Dispatches)
- Event 1: `0.126 ms`
- Event 2: `0.098 ms`
- Event 3: `0.094 ms`
- Event 4: `0.088 ms`
- Event 5: `0.084 ms`
- Event 6: `0.079 ms`
- Event 7: `0.112 ms`
- Event 8: `0.103 ms`
- Event 9: `0.111 ms`
- Event 10: `0.109 ms`

---

## 3. Concurrency, Queue & Isolation Test Summary

| Test Case | Scenario | Result |
| :--- | :--- | :--- |
| `test_ws_hub_status_endpoint` | Query `GET /api/ws/status` | Active count tracks subscribers accurately |
| `test_ws_connection_handshake_and_ping_pong` | Handshake + `ping` frame $\rightarrow$ `pong` frame | Handshake verified, ping responded in $< 1\text{ms}$ |
| `test_ws_event_broadcasting_from_callback_registry` | CallbackRegistry event stream $\rightarrow$ WebSocket | Full structured JSON payload received |
| `test_ws_secret_redaction_invariant` | Event with `api_key=AIzaSyD-secret` | Redacted to `[REDACTED_API_KEY]` |
| `test_ws_multiple_subscribers_and_disconnect_isolation` | 3 clients connected; 1 abruptly closes | Remaining 2 clients receive subsequent events uninterrupted |
| `test_ws_threaded_dispatch` | Callback triggered from background worker thread | Thread-safe dispatch via `loop.call_soon_threadsafe` |
| `test_ws_bounded_queue_drop_oldest_under_slow_client` | Slow client fails to drain queue (buffer cap 100) | Drop-oldest policy prevents memory leaks or stalling |
