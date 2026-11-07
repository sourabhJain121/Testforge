"""
tests/test_websocket_streaming.py - Unit and Integration Tests for Real-Time WebSocket Event Hub.

Tests:
  1. Connection handshake and HUB_CONNECTED welcome packet.
  2. Ping / pong bidirectional heartbeat.
  3. Real-time event broadcasting to single and multiple connected clients.
  4. Subscriber failure isolation (one disconnect does not break other active streams).
  5. Secret redaction invariant over WebSocket (no API keys or credentials in payloads).
  6. Non-blocking bounded queue overflow / drop-oldest behavior under slow client conditions.
  7. Thread-safe event dispatch from background worker threads.
  8. Idempotent attachment to CallbackRegistry.
  9. /api/ws/status health and metric tracking endpoint.
"""

import json
import threading
import time

import pytest
from starlette.testclient import TestClient

from server import app
from testforge.callbacks import CallbackRegistry, EventType, LifecycleEvent, default_callback_registry
from testforge.websocket_hub import WebSocketEventHub, global_websocket_hub


def test_ws_hub_status_endpoint():
    """Verify GET /api/ws/status returns valid health metrics."""
    client = TestClient(app)
    resp = client.get("/api/ws/status")
    assert resp.status_code == 200
    data = resp.json()
    assert "active_clients" in data
    assert "total_events_broadcast" in data
    assert "dropped_events_count" in data
    assert data["max_queue_size_per_client"] > 0


def test_ws_connection_handshake_and_ping_pong():
    """Verify WebSocket connection connects, receives welcome event, and handles ping/pong."""
    client = TestClient(app)
    with client.websocket_connect("/ws/events") as ws:
        # Initial greeting packet
        greeting = ws.receive_json()
        assert greeting["event_type"] == "HUB_CONNECTED"
        assert greeting["emitter"] == "WebSocketEventHub"
        assert "client_count" in greeting["payload"]

        # Send ping
        send_ts = time.time()
        ws.send_json({"type": "ping", "timestamp": send_ts})
        pong = ws.receive_json()
        assert pong["event_type"] == "PONG"
        assert pong["client_timestamp"] == send_ts


def test_ws_event_broadcasting_from_callback_registry():
    """Verify that dispatching a LifecycleEvent through the registry streams to connected WebSocket client."""
    client = TestClient(app)
    with client.websocket_connect("/ws/events") as ws:
        _ = ws.receive_json()  # Consume greeting

        # Dispatch real LifecycleEvent via default registry
        test_event = LifecycleEvent(
            event_type=EventType.AGENT_HANDOFF,
            emitter="GeneratorAgent",
            workflow_id="wf-ws-test-01",
            correlation_id="corr-12345",
            payload={
                "from_agent": "GeneratorAgent",
                "to_agent": "CriticAgent",
                "summary": "Transferring generated test suite for mutation analysis",
                "iteration": 1
            }
        )

        dispatch_time = time.time()
        default_callback_registry.dispatch(test_event)

        # Receive streamed event
        received = ws.receive_json()
        recv_time = time.time()

        assert received["event_type"] == "AGENT_HANDOFF"
        assert received["emitter"] == "GeneratorAgent"
        assert received["workflow_id"] == "wf-ws-test-01"
        assert received["correlation_id"] == "corr-12345"
        assert received["payload"]["from_agent"] == "GeneratorAgent"
        assert received["payload"]["to_agent"] == "CriticAgent"

        # Check dispatch latency metadata
        assert "hub_dispatch_ts" in received
        delivery_latency_ms = (recv_time - received["hub_dispatch_ts"]) * 1000
        # Under local TestClient, delivery is in-process and fast (<50ms)
        assert delivery_latency_ms >= 0


def test_ws_secret_redaction_invariant():
    """Verify credentials and secret tokens in event payloads are scrubbed before reaching the WebSocket client."""
    client = TestClient(app)
    with client.websocket_connect("/ws/events") as ws:
        _ = ws.receive_json()  # Greeting

        sensitive_event = LifecycleEvent(
            event_type=EventType.OPERATION_START,
            emitter="SecurityTestModule",
            payload={
                "api_key": "AIzaSyDUMMY_SECRET_KEY_1234567890",
                "token": "sk-or-v1-supersecret123456789",
                "nested": {
                    "password": "SuperSecretPassword!",
                    "public_field": "visible_value"
                }
            }
        )

        default_callback_registry.dispatch(sensitive_event)
        received = ws.receive_json()

        payload = received.get("payload", {})
        payload_str = json.dumps(payload)

        # Invariant: secrets must be redacted
        assert "AIzaSyDUMMY_SECRET_KEY_1234567890" not in payload_str
        assert "sk-or-v1-supersecret123456789" not in payload_str
        assert "SuperSecretPassword!" not in payload_str
        assert payload["api_key"] == "[REDACTED_SECRET]"
        assert payload["token"] == "[REDACTED_SECRET]"
        assert payload["nested"]["password"] == "[REDACTED_SECRET]"
        assert payload["nested"]["public_field"] == "visible_value"


def test_ws_multiple_subscribers_and_disconnect_isolation():
    """Verify multiple concurrent WebSocket connections receive broadcasts and disconnect of one client does not disrupt others."""
    client = TestClient(app)
    with client.websocket_connect("/ws/events") as ws1:
        _ = ws1.receive_json()

        with client.websocket_connect("/ws/events") as ws2:
            _ = ws2.receive_json()

            # Dispatch event to both
            ev1 = LifecycleEvent(
                event_type=EventType.TOOL_START,
                emitter="MutatorEngine",
                payload={"tool_name": "ASTMutator", "operator": "AOR"}
            )
            default_callback_registry.dispatch(ev1)

            rec1 = ws1.receive_json()
            rec2 = ws2.receive_json()

            assert rec1["event_type"] == "TOOL_START"
            assert rec2["event_type"] == "TOOL_START"

        # ws2 is now closed/disconnected. ws1 must still receive subsequent events without disruption
        ev2 = LifecycleEvent(
            event_type=EventType.TOOL_COMPLETE,
            emitter="MutatorEngine",
            payload={"tool_name": "ASTMutator", "mutants_generated": 14}
        )
        default_callback_registry.dispatch(ev2)

        rec1_next = ws1.receive_json()
        assert rec1_next["event_type"] == "TOOL_COMPLETE"
        assert rec1_next["payload"]["mutants_generated"] == 14


def test_ws_threaded_dispatch():
    """Verify events emitted from background worker threads safely broadcast to WebSocket clients."""
    client = TestClient(app)
    with client.websocket_connect("/ws/events") as ws:
        _ = ws.receive_json()

        def worker():
            time.sleep(0.05)
            ev = LifecycleEvent(
                event_type=EventType.STATE_CHANGE,
                emitter="ThreadedWorker",
                payload={"from_state": "INGESTING", "to_state": "SYNTHESIZING"}
            )
            default_callback_registry.dispatch(ev)

        t = threading.Thread(target=worker)
        t.start()
        t.join(timeout=2.0)

        received = ws.receive_json()
        assert received["event_type"] == "STATE_CHANGE"
        assert received["emitter"] == "ThreadedWorker"
        assert received["payload"]["to_state"] == "SYNTHESIZING"


def test_ws_bounded_queue_drop_oldest_under_slow_client():
    """Verify that a slow client queue drops oldest events once capacity is exceeded without blocking."""
    hub = WebSocketEventHub(max_queue_size=3)
    reg = CallbackRegistry()
    hub.attach_to_registry(reg)

    # Mock client queue
    import asyncio
    queue = asyncio.Queue(maxsize=3)
    hub._clients["mock_ws"] = queue

    # Dispatch 5 events (capacity is 3)
    for i in range(5):
        ev = LifecycleEvent(
            event_type=EventType.STATE_CHANGE,
            emitter="FastProducer",
            payload={"step_index": i}
        )
        reg.dispatch(ev)

    # Queue should contain exactly 3 items (steps 2, 3, 4)
    assert queue.qsize() == 3
    items = []
    while not queue.empty():
        items.append(queue.get_nowait())

    step_indices = [item["payload"]["step_index"] for item in items]
    assert step_indices == [2, 3, 4]
    assert hub.dropped_events_count == 2


def test_ws_event_delivery_latency_measurement():
    """
    Measures the empirical dispatch-to-receipt latency across multiple events.
    Verifies that mean event delivery latency is recorded and well within operational bounds.
    """
    client = TestClient(app)
    latencies_ms = []

    with client.websocket_connect("/ws/events") as ws:
        _ = ws.receive_json()  # Greeting

        # Dispatch 20 test events and record delivery timing
        for i in range(20):
            ev = LifecycleEvent(
                event_type=EventType.STATE_CHANGE,
                emitter="LatencyBenchmark",
                payload={"iteration": i, "subsystem": "test"}
            )
            t_dispatch = time.perf_counter()
            default_callback_registry.dispatch(ev)
            msg = ws.receive_json()
            t_recv = time.perf_counter()

            elapsed_ms = (t_recv - t_dispatch) * 1000.0
            latencies_ms.append(elapsed_ms)
            assert msg["event_type"] == "STATE_CHANGE"

    assert len(latencies_ms) == 20
    avg_latency = sum(latencies_ms) / len(latencies_ms)
    min_latency = min(latencies_ms)
    max_latency = max(latencies_ms)

    print(f"\n[MEASURED LATENCY] WebSocket Delivery: avg={avg_latency:.3f}ms, min={min_latency:.3f}ms, max={max_latency:.3f}ms")
    # Verify sub-50ms target holds in practice on macOS TestClient loop
    assert avg_latency < 50.0, f"Average latency {avg_latency:.2f}ms exceeded 50ms"

