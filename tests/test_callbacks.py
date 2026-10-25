"""
test_callbacks.py - Unit and Integration Tests for Lifecycle Callback Registry and TraceLogger Adapter.
"""

import pytest
import time
from testforge.callbacks import (
    CallbackRegistry,
    EventType,
    LifecycleEvent,
    OperationStartPayload,
    OperationCompletePayload,
    ToolStartPayload,
    ToolCompletePayload,
    StateChangePayload,
    FailoverPayload,
    ErrorPayload,
    TraceLoggerCallbackAdapter,
)
from testforge.logger import TraceLogger


class TestCallbackRegistry:
    def test_register_and_invoke_single_handler(self):
        registry = CallbackRegistry()
        received_events = []

        def handler(event: LifecycleEvent):
            received_events.append(event)

        sub_id = registry.register(handler, event_types=EventType.OPERATION_START)
        assert isinstance(sub_id, str)
        assert registry.subscription_count == 1

        event = LifecycleEvent(
            event_type=EventType.OPERATION_START,
            emitter="TestEmitter",
            payload={"operation": "test_op"},
        )
        records = registry.dispatch(event)

        assert len(received_events) == 1
        assert received_events[0].event_type == EventType.OPERATION_START
        assert received_events[0].emitter == "TestEmitter"
        assert len(records) == 1
        assert records[0].success is True

    def test_handler_filtering_by_event_type(self):
        registry = CallbackRegistry()
        op_events = []
        tool_events = []

        registry.register(lambda e: op_events.append(e), event_types=[EventType.OPERATION_START, EventType.OPERATION_COMPLETE])
        registry.register(lambda e: tool_events.append(e), event_types=EventType.TOOL_START)

        # Dispatch TOOL_START
        registry.dispatch(
            LifecycleEvent(
                event_type=EventType.TOOL_START,
                emitter="Agent1",
                payload={"tool": "pytest"},
            )
        )
        assert len(op_events) == 0
        assert len(tool_events) == 1

        # Dispatch OPERATION_START
        registry.dispatch(
            LifecycleEvent(
                event_type=EventType.OPERATION_START,
                emitter="Agent1",
                payload={"op": "harden"},
            )
        )
        assert len(op_events) == 1
        assert len(tool_events) == 1

    def test_wildcard_subscription(self):
        registry = CallbackRegistry()
        all_events = []

        # No event_types specified means subscribe to ALL
        registry.register(lambda e: all_events.append(e))

        registry.dispatch(LifecycleEvent(event_type=EventType.TOOL_START, emitter="test"))
        registry.dispatch(LifecycleEvent(event_type=EventType.FAILOVER, emitter="test"))
        registry.dispatch(LifecycleEvent(event_type=EventType.ERROR, emitter="test"))

        assert len(all_events) == 3

    def test_registration_and_unregistration(self):
        registry = CallbackRegistry()
        events = []

        sub_id = registry.register(lambda e: events.append(e))
        assert registry.subscription_count == 1

        registry.dispatch(LifecycleEvent(event_type=EventType.STATE_CHANGE, emitter="test"))
        assert len(events) == 1

        removed = registry.unregister(sub_id)
        assert removed is True
        assert registry.subscription_count == 0

        # Dispatch after unregistration should not invoke handler
        registry.dispatch(LifecycleEvent(event_type=EventType.STATE_CHANGE, emitter="test"))
        assert len(events) == 1

    def test_deterministic_execution_order_by_priority(self):
        registry = CallbackRegistry()
        call_sequence = []

        # Register handlers with different priorities
        registry.register(lambda e: call_sequence.append("low"), priority=10)
        registry.register(lambda e: call_sequence.append("highest"), priority=200)
        registry.register(lambda e: call_sequence.append("medium_1"), priority=100)
        registry.register(lambda e: call_sequence.append("medium_2"), priority=100)

        registry.dispatch(LifecycleEvent(event_type=EventType.OPERATION_START, emitter="test"))
        # Priority order: 200, 100 (first registered), 100 (second registered), 10
        assert call_sequence == ["highest", "medium_1", "medium_2", "low"]

    def test_handler_failure_isolation(self):
        registry = CallbackRegistry()
        success_calls = []

        def failing_handler(e: LifecycleEvent):
            raise RuntimeError("Intentional observer explosion")

        def normal_handler(e: LifecycleEvent):
            success_calls.append(e.event_id)

        # Register failing handler first, then normal handler
        registry.register(failing_handler, priority=200, name="broken_observer")
        registry.register(normal_handler, priority=100, name="healthy_observer")

        # Dispatch should NOT raise RuntimeError; healthy observer must still execute
        records = registry.dispatch(
            LifecycleEvent(event_type=EventType.OPERATION_COMPLETE, emitter="test")
        )

        assert len(records) == 2
        # Check failing record
        assert records[0].success is False
        assert "broken_observer" in records[0].handler_name
        assert "Intentional observer explosion" in records[0].error_message

        # Check healthy record
        assert records[1].success is True
        assert len(success_calls) == 1

        # Check registry error records
        assert len(registry.failed_records) == 1
        assert registry.failed_records[0].success is False

    def test_sensitive_event_data_scrubbing(self):
        registry = CallbackRegistry()
        captured_payloads = []

        registry.register(lambda e: captured_payloads.append(e.payload))

        sensitive_event = LifecycleEvent(
            event_type=EventType.OPERATION_START,
            emitter="AuthModule",
            payload={
                "username": "admin",
                "api_key": "sk-secret1234567890abcdef",
                "nested": {
                    "token": "bearer 1234567890abcdef1234567890",
                    "password": "supersecretpassword123",
                },
            },
        )

        registry.dispatch(sensitive_event)

        assert len(captured_payloads) == 1
        captured = captured_payloads[0]
        assert captured["username"] == "admin"
        assert "sk-secret1234567890abcdef" not in str(captured)
        assert "[REDACTED_SECRET]" in captured["api_key"]
        assert "1234567890abcdef1234567890" not in str(captured)
        assert "supersecretpassword123" not in str(captured)


class TestTypedPayloads:
    def test_typed_payload_models(self):
        op_start = OperationStartPayload(operation_name="baseline_test_gen", inputs={"func": "add"})
        assert op_start.operation_name == "baseline_test_gen"

        op_complete = OperationCompletePayload(operation_name="baseline_test_gen", status="SUCCESS", duration_sec=1.5)
        assert op_complete.duration_sec == 1.5

        tool_start = ToolStartPayload(tool_name="ast_mutator", arguments={"max_mutants": 10})
        assert tool_start.tool_name == "ast_mutator"

        tool_complete = ToolCompletePayload(tool_name="pytest", status="PASS", duration_ms=250.0)
        assert tool_complete.status == "PASS"

        state_change = StateChangePayload(component="orchestrator", from_state="INIT", to_state="MUTATION_LOOP", iteration=1)
        assert state_change.from_state == "INIT"

        failover = FailoverPayload(failed_provider="gemini", target_provider="groq", reason="429 RateLimit")
        assert failover.failed_provider == "gemini"

        err = ErrorPayload(error_type="SandboxError", message="Test execution failed")
        assert err.fatal is False


class TestTraceLoggerAdapter:
    def test_trace_logger_adapter_integration(self, tmp_path):
        log_file = tmp_path / "callback_trace.jsonl"
        trace_logger = TraceLogger(str(log_file))
        adapter = TraceLoggerCallbackAdapter(trace_logger)

        registry = CallbackRegistry()
        registry.register(adapter)

        event = LifecycleEvent(
            event_type=EventType.FAILOVER,
            emitter="MultiProviderAgent",
            payload={
                "failed_provider": "gemini-3.6-flash",
                "target_provider": "llama-3.3-70b-versatile",
                "secret_key": "api_key='secret123456789'",
            },
            metadata={"iteration": 2},
        )
        registry.dispatch(event)

        assert log_file.exists()
        content = log_file.read_text(encoding="utf-8")
        assert "LIFECYCLE_FAILOVER" in content
        assert "MultiProviderAgent" in content
        assert "llama-3.3-70b-versatile" in content
        # Ensure secret key is redacted
        assert "secret123456789" not in content
        assert "[REDACTED_SECRET]" in content

    def test_callback_fail_fast_and_raise_on_error(self):
        reg = CallbackRegistry(fail_fast=True)
        def broken_handler(e):
            raise ValueError("Forced test error")
        reg.register(broken_handler)

        event = LifecycleEvent(event_type=EventType.OPERATION_START, emitter="test")
        with pytest.raises(ValueError, match="Forced test error"):
            reg.dispatch(event)

        assert reg.get_last_error() is not None
        assert "Forced test error" in reg.get_last_error().error_message

    def test_scrubbing_nested_tuples_and_sets(self):
        reg = CallbackRegistry()
        captured = []
        reg.register(lambda e: captured.append(e.payload))

        event = LifecycleEvent(
            event_type=EventType.OPERATION_START,
            emitter="test",
            payload={
                "tuple_data": ("safe", "api_key='sk-1234567890abcdef'"),
                "set_data": {"password='mysecretpassword'"}
            }
        )
        reg.dispatch(event)
        assert len(captured) == 1
        t_data = captured[0]["tuple_data"]
        assert isinstance(t_data, tuple)
        assert "[REDACTED_SECRET]" in t_data[1]

    def test_orchestrator_lifecycle_events_dispatched(self, tmp_path):
        from testforge.orchestrator import TestForgeOrchestrator
        events = []
        reg = CallbackRegistry()
        reg.register(lambda e: events.append(e))

        target_code = "def add(a, b): return a + b\n"
        initial_test = "from target import add\ndef test_add(): assert add(1, 2) == 3\n"
        trace_file = str(tmp_path / "orch_trace.jsonl")

        orch = TestForgeOrchestrator(
            target_source_code=target_code,
            initial_test_code=initial_test,
            max_iterations=1,
            target_mutation_score=50.0,
            trace_log_path=trace_file,
            callbacks=reg
        )
        orch.run()

        event_types = [e.event_type for e in events]
        assert EventType.OPERATION_START in event_types
        assert EventType.OPERATION_COMPLETE in event_types
        assert any(e.emitter == "TestForgeOrchestrator" for e in events)
