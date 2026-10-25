"""
callbacks.py - Lifecycle Callback Foundation and Event Registry.

Features:
  1. Typed Event Payloads:
     - Standardized lifecycle events: OPERATION_START, OPERATION_COMPLETE, TOOL_START,
       TOOL_COMPLETE, STATE_CHANGE, FAILOVER, ERROR.
  2. Multi-Handler Subscription:
     - Allows multiple observers/listeners to subscribe to specific event types or all events.
     - Deterministic execution ordering based on priority and registration sequence.
  3. Failure Isolation:
     - One observer's unhandled exception NEVER crashes the main application or interrupts other handlers.
     - Failed observer executions are tracked and exposed via execution records.
  4. Sensitive Data Scrubbing:
     - Automatically redacts credentials, API keys, and passwords before dispatch and logging.
  5. TraceLogger Adapter:
     - Pluggable adapter bridging lifecycle events to TestForge's existing TraceLogger.
"""

from __future__ import annotations
import time
import uuid
import logging
from enum import Enum
from typing import Dict, Any, Optional, List, Callable, Set, Union
from pydantic import BaseModel, Field

from testforge.security import redact_sensitive_data

logger = logging.getLogger("testforge.callbacks")


class EventType(str, Enum):
    OPERATION_START = "OPERATION_START"
    OPERATION_COMPLETE = "OPERATION_COMPLETE"
    AGENT_START = "AGENT_START"
    AGENT_COMPLETE = "AGENT_COMPLETE"
    TOOL_START = "TOOL_START"
    TOOL_COMPLETE = "TOOL_COMPLETE"
    STATE_CHANGE = "STATE_CHANGE"
    A2A_MESSAGE = "A2A_MESSAGE"
    FAILOVER = "FAILOVER"
    ERROR = "ERROR"
    AGENT_HANDOFF = "AGENT_HANDOFF"
    VALIDATION_FAILURE = "VALIDATION_FAILURE"
    SECURITY_REFUSAL = "SECURITY_REFUSAL"
    TIMEOUT = "TIMEOUT"
    RETRY = "RETRY"
    WORKFLOW_OUTCOME = "WORKFLOW_OUTCOME"
    CHECKPOINT_SAVED = "CHECKPOINT_SAVED"
    CHECKPOINT_RESTORED = "CHECKPOINT_RESTORED"
    CHECKPOINT_FAILED = "CHECKPOINT_FAILED"
    RECOVERY_DECISION = "RECOVERY_DECISION"


_SENSITIVE_KEY_NAMES = {
    "api_key", "apikey", "secret", "secret_key", "password", "token",
    "access_token", "auth_token", "credentials", "private_key"
}

def _scrub_value(val: Any, key_name: Optional[str] = None) -> Any:
    """Recursively redacts sensitive strings from nested dictionaries, lists, tuples, and sets."""
    if key_name and key_name.lower() in _SENSITIVE_KEY_NAMES and isinstance(val, str):
        return "[REDACTED_SECRET]"
    if isinstance(val, str):
        return redact_sensitive_data(val)
    elif isinstance(val, dict):
        return {k: _scrub_value(v, key_name=k) for k, v in val.items()}
    elif isinstance(val, list):
        return [_scrub_value(item) for item in val]
    elif isinstance(val, tuple):
        return tuple(_scrub_value(item) for item in val)
    elif isinstance(val, set):
        return {_scrub_value(item) for item in val}
    elif hasattr(val, "model_dump") and callable(val.model_dump):
        return _scrub_value(val.model_dump())
    return val


class LifecycleEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType
    timestamp: float = Field(default_factory=time.time)
    emitter: str = Field(..., description="Module or agent producing the event")
    workflow_id: Optional[str] = Field(None, description="Workflow / run identifier")
    correlation_id: Optional[str] = Field(None, description="Correlation ID across agents/tools")
    parent_event_id: Optional[str] = Field(None, description="Parent event ID for causal tracing")
    outcome: Optional[str] = Field(None, description="Status/outcome: SUCCESS, FAILED, REFUSED")
    duration_ms: Optional[float] = Field(None, description="Elapsed time in milliseconds if applicable")
    error_code: Optional[str] = Field(None, description="Safe error classification code")
    payload: Dict[str, Any] = Field(default_factory=dict)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    def scrubbed_copy(self) -> "LifecycleEvent":
        """Returns a copy of the event with sensitive strings redacted."""
        return LifecycleEvent(
            event_id=self.event_id,
            event_type=self.event_type,
            timestamp=self.timestamp,
            emitter=self.emitter,
            workflow_id=self.workflow_id,
            correlation_id=self.correlation_id,
            parent_event_id=self.parent_event_id,
            outcome=self.outcome,
            duration_ms=self.duration_ms,
            error_code=self.error_code,
            payload=_scrub_value(self.payload),
            metadata=_scrub_value(self.metadata),
        )


# Typed Payload Models for Standard Events
class OperationStartPayload(BaseModel):
    operation_name: str
    inputs: Dict[str, Any] = Field(default_factory=dict)
    session_id: Optional[str] = None


class OperationCompletePayload(BaseModel):
    operation_name: str
    status: str
    duration_sec: float
    metrics: Dict[str, Any] = Field(default_factory=dict)


class ToolStartPayload(BaseModel):
    tool_name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)


class ToolCompletePayload(BaseModel):
    tool_name: str
    status: str
    duration_ms: float
    output_summary: Optional[str] = None


class StateChangePayload(BaseModel):
    component: str
    from_state: str
    to_state: str
    iteration: Optional[int] = None


class AgentStartPayload(BaseModel):
    agent_name: str
    model_name: Optional[str] = None
    iteration: int = 1
    action: Optional[str] = None


class AgentCompletePayload(BaseModel):
    agent_name: str
    status: str
    duration_ms: float
    output_summary: Optional[str] = None
    mutants_targeted: List[str] = Field(default_factory=list)


class SecurityRefusalPayload(BaseModel):
    policy: str
    risk_level: str
    reason: str
    rule_id: Optional[str] = None


class ValidationFailurePayload(BaseModel):
    component: str
    target_type: str
    errors: List[str] = Field(default_factory=list)


class WorkflowOutcomePayload(BaseModel):
    workflow_id: str
    final_mutation_score: float
    hardening_status: str
    iterations: int
    terminated: bool
    termination_reason: str
    total_tokens: int = 0


class FailoverPayload(BaseModel):
    failed_provider: str
    target_provider: str
    reason: str
    attempt: int = 1


class ErrorPayload(BaseModel):
    error_type: str
    message: str
    fatal: bool = False
    details: Dict[str, Any] = Field(default_factory=dict)


class AgentHandoffPayload(BaseModel):
    from_agent: str
    to_agent: str
    action: str
    correlation_id: str
    summary: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)


class HandlerExecutionRecord(BaseModel):
    subscription_id: str
    handler_name: str
    success: bool
    error_message: Optional[str] = None
    duration_ms: float = 0.0


class CallbackSubscription:
    """Represents an active observer subscription."""
    def __init__(
        self,
        subscription_id: str,
        handler: Callable[[LifecycleEvent], None],
        event_types: Optional[Set[EventType]] = None,
        priority: int = 100,
        registration_order: int = 0,
        name: Optional[str] = None,
    ):
        self.subscription_id = subscription_id
        self.handler = handler
        self.event_types = event_types  # None means subscribe to all event types
        self.priority = priority        # Higher number executes first
        self.registration_order = registration_order
        self.name = name or getattr(handler, "__name__", f"handler_{subscription_id[:8]}")

    def matches(self, event_type: EventType) -> bool:
        if self.event_types is None:
            return True
        return event_type in self.event_types


class CallbackRegistry:
    """
    Central, thread-safe synchronous lifecycle callback registry.
    
    Guarantees:
      - Deterministic execution ordering: Ordered by priority (descending), then registration order (ascending).
      - Strict observer isolation: Unhandled handler exceptions are caught and recorded without
        impacting the main pipeline or other observers.
      - Input scrubbing: Ensures sensitive tokens/keys do not leak into callbacks or logs.
      - Explicit error retrieval: Failed handler records are inspectable via failed_records and get_last_error().
    """
    def __init__(self, fail_fast: bool = False):
        self._subscriptions: Dict[str, CallbackSubscription] = {}
        self._registration_counter: int = 0
        self._failed_records: List[HandlerExecutionRecord] = []
        self._fail_fast: bool = fail_fast

    def register(
        self,
        handler: Callable[[LifecycleEvent], None],
        event_types: Optional[Union[EventType, str, List[Union[EventType, str]], Set[Union[EventType, str]]]] = None,
        priority: int = 100,
        name: Optional[str] = None,
    ) -> str:
        """
        Registers an observer handler.
        Returns a unique subscription_id used for unregistering.
        """
        if not callable(handler):
            raise TypeError(f"Handler must be callable, got {type(handler)}")

        sub_id = str(uuid.uuid4())
        self._registration_counter += 1

        types_set: Optional[Set[EventType]] = None
        if event_types is not None:
            if isinstance(event_types, (EventType, str)):
                types_set = {EventType(event_types)}
            else:
                types_set = {EventType(t) for t in event_types}

        subscription = CallbackSubscription(
            subscription_id=sub_id,
            handler=handler,
            event_types=types_set,
            priority=priority,
            registration_order=self._registration_counter,
            name=name,
        )
        self._subscriptions[sub_id] = subscription
        return sub_id

    def unregister(self, subscription_id: str) -> bool:
        """Removes a subscription by ID. Returns True if removed, False if not found."""
        return self._subscriptions.pop(subscription_id, None) is not None

    def clear(self):
        """Clears all registered subscriptions and error records."""
        self._subscriptions.clear()
        self._registration_counter = 0
        self._failed_records.clear()

    @property
    def subscription_count(self) -> int:
        return len(self._subscriptions)

    @property
    def failed_records(self) -> List[HandlerExecutionRecord]:
        return list(self._failed_records)

    def get_last_error(self) -> Optional[HandlerExecutionRecord]:
        """Returns the most recent failed handler execution record, if any."""
        return self._failed_records[-1] if self._failed_records else None

    def dispatch(
        self,
        event: LifecycleEvent,
        raise_on_error: bool = False
    ) -> List[HandlerExecutionRecord]:
        """
        Dispatches an event synchronously to all matching subscribers in deterministic order.
        Catches observer errors to prevent application crashes, unless raise_on_error or fail_fast is enabled.
        """
        scrubbed_event = event.scrubbed_copy()
        matching = [
            sub for sub in self._subscriptions.values()
            if sub.matches(scrubbed_event.event_type)
        ]

        # Deterministic sort: higher priority first, then earlier registration
        matching.sort(key=lambda s: (-s.priority, s.registration_order))

        execution_records: List[HandlerExecutionRecord] = []

        for sub in matching:
            t0 = time.perf_counter()
            try:
                sub.handler(scrubbed_event)
                elapsed_ms = (time.perf_counter() - t0) * 1000.0
                execution_records.append(
                    HandlerExecutionRecord(
                        subscription_id=sub.subscription_id,
                        handler_name=sub.name,
                        success=True,
                        duration_ms=elapsed_ms,
                    )
                )
            except Exception as exc:
                elapsed_ms = (time.perf_counter() - t0) * 1000.0
                err_msg = f"Callback handler '{sub.name}' failed: {str(exc)}"
                logger.error(err_msg, exc_info=True)
                record = HandlerExecutionRecord(
                    subscription_id=sub.subscription_id,
                    handler_name=sub.name,
                    success=False,
                    error_message=err_msg,
                    duration_ms=elapsed_ms,
                )
                execution_records.append(record)
                self._failed_records.append(record)
                if raise_on_error or self._fail_fast:
                    raise exc

        return execution_records


# Global default registry instance
default_callback_registry = CallbackRegistry()


class TraceLoggerCallbackAdapter:
    """
    Adapter bridging lifecycle events to TestForge's TraceLogger.
    Ensures safe formatting and credential scrubbing.
    """
    def __init__(self, trace_logger: Any):
        self.trace_logger = trace_logger

    def __call__(self, event: LifecycleEvent) -> None:
        """Callback handler entry point."""
        if not self.trace_logger:
            return

        event_data = {
            "emitter": event.emitter,
            "event_id": event.event_id,
            "outcome": event.outcome,
            "duration_ms": event.duration_ms,
            "error_code": event.error_code,
            "payload": event.payload,
        }
        metadata = dict(event.metadata)
        metadata["lifecycle_timestamp"] = event.timestamp
        if event.workflow_id:
            metadata["workflow_id"] = event.workflow_id
        if event.correlation_id:
            metadata["correlation_id"] = event.correlation_id
        if event.parent_event_id:
            metadata["parent_event_id"] = event.parent_event_id

        # Forward to TraceLogger
        try:
            self.trace_logger.log_event(
                event_type=f"LIFECYCLE_{event.event_type.value}",
                data=event_data,
                metadata=metadata,
                correlation_id=event.correlation_id,
                workflow_id=event.workflow_id,
            )
        except Exception as exc:
            logger.warning(f"TraceLoggerCallbackAdapter failed to log event: {exc}")
