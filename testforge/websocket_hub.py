"""
testforge/websocket_hub.py - Real-Time WebSocket Event Hub & Lifecycle Callback Bridge.

Provides:
  1. Thread-safe asynchronous broadcasting of LifecycleEvents to multiple WebSocket clients.
  2. Isolated bounded queues per connected client to prevent memory leaks or blocking on slow clients.
  3. Non-blocking bridging from synchronous agent worker threads via loop.call_soon_threadsafe.
  4. Automatic credential and secret redaction using LifecycleEvent.scrubbed_copy().
  5. Idempotent registration with the default CallbackRegistry.
"""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any, Dict, Optional

from starlette.websockets import WebSocket, WebSocketDisconnect

from testforge.callbacks import CallbackRegistry, LifecycleEvent, default_callback_registry

logger = logging.getLogger("testforge.websocket_hub")


class WebSocketEventHub:
    """
    Manages active WebSocket connections and broadcasts LifecycleEvents with
    per-client isolation, bounded queues, and thread safety.
    """

    def __init__(self, max_queue_size: int = 100):
        self.max_queue_size = max_queue_size
        self._clients: Dict[WebSocket, asyncio.Queue] = {}
        self._lock = asyncio.Lock()
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._subscription_id: Optional[str] = None
        self._total_events_broadcast: int = 0
        self._dropped_events_count: int = 0

    def set_event_loop(self, loop: asyncio.AbstractEventLoop) -> None:
        """Sets the active asyncio event loop for threadsafe dispatches."""
        self._loop = loop

    @property
    def client_count(self) -> int:
        return len(self._clients)

    @property
    def total_events_broadcast(self) -> int:
        return self._total_events_broadcast

    @property
    def dropped_events_count(self) -> int:
        return self._dropped_events_count

    async def register_client(self, websocket: WebSocket) -> asyncio.Queue:
        """Registers a newly connected WebSocket client and allocates an isolated bounded queue."""
        queue: asyncio.Queue = asyncio.Queue(maxsize=self.max_queue_size)
        async with self._lock:
            self._clients[websocket] = queue
            if self._loop is None:
                self._loop = asyncio.get_running_loop()
        logger.debug(f"Client connected. Active WebSocket clients: {len(self._clients)}")
        return queue

    async def unregister_client(self, websocket: WebSocket) -> None:
        """Unregisters a disconnecting WebSocket client."""
        async with self._lock:
            if websocket in self._clients:
                del self._clients[websocket]
        logger.debug(f"Client disconnected. Active WebSocket clients: {len(self._clients)}")

    def serialize_event(self, event: LifecycleEvent) -> Dict[str, Any]:
        """
        Creates a scrubbed, JSON-serializable dictionary representation of the event
        augmented with high-resolution dispatch timing for latency tracking.
        """
        scrubbed = event.scrubbed_copy()
        etype = scrubbed.event_type.value if hasattr(scrubbed.event_type, "value") else str(scrubbed.event_type)
        return {
            "event_id": scrubbed.event_id,
            "event_type": etype,
            "timestamp": scrubbed.timestamp,
            "hub_dispatch_ts": time.time(),
            "emitter": scrubbed.emitter,
            "workflow_id": scrubbed.workflow_id,
            "correlation_id": scrubbed.correlation_id,
            "parent_event_id": scrubbed.parent_event_id,
            "outcome": scrubbed.outcome,
            "duration_ms": scrubbed.duration_ms,
            "error_code": scrubbed.error_code,
            "payload": scrubbed.payload,
            "metadata": scrubbed.metadata,
        }

    def on_lifecycle_event(self, event: LifecycleEvent) -> None:
        """
        Callback handler invoked by CallbackRegistry.
        Can be called from the main thread or worker threads.
        """
        try:
            payload = self.serialize_event(event)
        except Exception as exc:
            logger.error(f"Error serializing event {event.event_id}: {exc}")
            return

        if not self._clients:
            return

        loop = self._loop
        if loop is None:
            try:
                loop = asyncio.get_running_loop()
                self._loop = loop
            except RuntimeError:
                loop = None

        if loop and loop.is_running():
            loop.call_soon_threadsafe(self._enqueue_to_all_clients, payload)
        else:
            # Fallback for sync or test environments
            self._enqueue_to_all_clients(payload)

    def _enqueue_to_all_clients(self, payload: Dict[str, Any]) -> None:
        """Enqueues payload into each active client's queue with drop-oldest policy."""
        self._total_events_broadcast += 1
        for ws, queue in list(self._clients.items()):
            try:
                if queue.full():
                    try:
                        queue.get_nowait()
                        self._dropped_events_count += 1
                    except asyncio.QueueEmpty:
                        pass
                queue.put_nowait(payload)
            except Exception as exc:
                logger.warning(f"Failed to enqueue to client {ws}: {exc}")

    def broadcast_event(self, data: Dict[str, Any]) -> None:
        """Directly broadcasts any dictionary payload to all active WebSocket clients."""
        if not self._clients:
            return
        if "timestamp" not in data:
            data["timestamp"] = time.time()
        if "hub_dispatch_ts" not in data:
            data["hub_dispatch_ts"] = time.time()
        loop = self._loop
        if loop is None:
            try:
                loop = asyncio.get_running_loop()
                self._loop = loop
            except RuntimeError:
                loop = None

        if loop and loop.is_running():
            loop.call_soon_threadsafe(self._enqueue_to_all_clients, data)
        else:
            self._enqueue_to_all_clients(data)

    def attach_to_registry(
        self,
        registry: CallbackRegistry = default_callback_registry,
        priority: int = 50
    ) -> str:
        """
        Idempotently attaches the hub to a CallbackRegistry.
        Returns the subscription_id.
        """
        if self._subscription_id is not None:
            return self._subscription_id

        self._subscription_id = registry.register(
            handler=self.on_lifecycle_event,
            priority=priority,
            name="WebSocketEventHub",
        )
        logger.info(f"WebSocketEventHub attached to CallbackRegistry (sub_id={self._subscription_id})")
        return self._subscription_id

    def detach_from_registry(
        self,
        registry: CallbackRegistry = default_callback_registry
    ) -> bool:
        """Detaches from CallbackRegistry."""
        if self._subscription_id is None:
            return False
        res = registry.unregister(self._subscription_id)
        if res:
            self._subscription_id = None
        return res

    async def handle_websocket_connection(self, websocket: WebSocket) -> None:
        """
        Handles the complete lifecycle of a single WebSocket connection:
        accept -> queue allocation -> send/recv loop -> unregister upon disconnect.
        """
        await websocket.accept()
        queue = await self.register_client(websocket)

        # Send initial connection acknowledgment
        try:
            await websocket.send_json({
                "event_type": "HUB_CONNECTED",
                "timestamp": time.time(),
                "hub_dispatch_ts": time.time(),
                "emitter": "WebSocketEventHub",
                "payload": {"message": "Connected to TestForge Real-Time Event Hub", "client_count": self.client_count}
            })
        except Exception:
            await self.unregister_client(websocket)
            return

        async def send_worker():
            try:
                while True:
                    msg = await queue.get()
                    await websocket.send_json(msg)
                    queue.task_done()
            except asyncio.CancelledError:
                pass
            except Exception as send_err:
                logger.debug(f"WebSocket send loop exited: {send_err}")

        async def recv_worker():
            try:
                while True:
                    text = await websocket.receive_text()
                    try:
                        cmd = json.loads(text)
                        if isinstance(cmd, dict) and cmd.get("type") == "ping":
                            await websocket.send_json({
                                "event_type": "PONG",
                                "timestamp": time.time(),
                                "client_timestamp": cmd.get("timestamp"),
                                "emitter": "WebSocketEventHub"
                            })
                    except json.JSONDecodeError:
                        pass
            except asyncio.CancelledError:
                pass
            except (WebSocketDisconnect, ConnectionResetError):
                pass
            except Exception as recv_err:
                logger.debug(f"WebSocket recv loop exited: {recv_err}")

        send_task = asyncio.create_task(send_worker())
        recv_task = asyncio.create_task(recv_worker())

        try:
            # Wait until either sender or receiver terminates (usually disconnect)
            done, pending = await asyncio.wait(
                [send_task, recv_task],
                return_when=asyncio.FIRST_COMPLETED
            )
            for task in pending:
                task.cancel()
        finally:
            await self.unregister_client(websocket)
            try:
                await websocket.close()
            except Exception:
                pass


# Global singleton hub instance
global_websocket_hub = WebSocketEventHub()
global_websocket_hub.attach_to_registry(default_callback_registry)

