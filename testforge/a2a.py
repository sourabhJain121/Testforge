"""
a2a.py - Typed, Validated Agent-to-Agent (A2A) Message Contract and Broker.

This module implements a custom in-process typed A2A message broker and contract
inspired by FIPA-ACL and modern multi-agent communication patterns, tailored for
TestForge's in-memory multi-framework pipeline. It is an internal agent contract
and message broker rather than an external HTTP wire protocol.

Architecture:
  1. A2APerformative: Formal communicative acts (REQUEST, INFORM, AGREE, REFUSE, FAILURE, PROPOSE).
  2. A2AMessage: Strongly-typed Pydantic message envelope preserving correlation IDs,
     trace metadata, sender/recipient identities, and deep-copy isolation.
  3. Typed Payloads: Constrained schemas for critique requests, structured directives,
     and failure mechanisms (e.g. CriticDirectivePayload, A2ACritiqueRequestPayload).
  4. A2ABroker: In-process message exchange with handler registration, sender/recipient
     authorization, AST/Prompt security guardrail inspection, bounded execution timeouts,
     lifecycle callback emission, and thread-safe Blackboard partition synchronization.
"""

from __future__ import annotations
import copy
import time
import uuid
import logging
import threading
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FuturesTimeoutError
from typing import Dict, Any, Optional, List, Callable, Set, Union
from pydantic import BaseModel, Field, ValidationError, model_validator

from testforge.security import SecurityGuardrail, redact_sensitive_data
from testforge.callbacks import (
    CallbackRegistry,
    LifecycleEvent,
    EventType,
    _scrub_value,
)

logger = logging.getLogger("testforge.a2a")


# ==============================================================================
# 1. Communicative Acts (Performatives) and Envelope
# ==============================================================================

class A2APerformative(str, Enum):
    """FIPA-ACL inspired communicative acts for agent deliberation."""
    REQUEST = "REQUEST"       # Sender requests recipient to execute an action
    INFORM = "INFORM"         # Sender provides verified results/facts
    AGREE = "AGREE"           # Recipient accepts request and commits to execute
    REFUSE = "REFUSE"         # Recipient or Broker refuses execution (auth, security, policy)
    FAILURE = "FAILURE"       # Execution failed during operation (timeout, exception, error)
    PROPOSE = "PROPOSE"       # Sender proposes candidate directives or assertions


class A2AMessage(BaseModel):
    """
    Standardized typed message envelope for inter-agent communication.
    Guarantees structural validation, immutable logging semantics, and correlation tracing.
    """
    message_id: str = Field(default_factory=lambda: f"msg_{uuid.uuid4().hex[:12]}")
    correlation_id: str = Field(..., description="Unique trace identifier spanning an entire reflection cycle")
    sender: str = Field(..., description="Identity URI of sending entity (e.g., 'agent:orchestrator', 'agent:crewai:critic')")
    recipient: str = Field(..., description="Identity URI of target entity (e.g., 'agent:crewai:critic', 'agent:adk:generator')")
    performative: A2APerformative = Field(..., description="Communicative act")
    timestamp: float = Field(default_factory=time.time, description="Unix timestamp of message creation")
    action: str = Field(..., description="Operational action identifier, e.g. 'diagnose_mutants', 'generate_tests'")
    payload: Dict[str, Any] = Field(default_factory=dict, description="Typed structured payload data")
    headers: Dict[str, Any] = Field(default_factory=dict, description="Operational headers, route flags, and credentials metadata")

    @model_validator(mode="before")
    @classmethod
    def deepcopy_containers(cls, data: Any) -> Any:
        if isinstance(data, dict):
            if "payload" in data and isinstance(data["payload"], (dict, list)):
                data["payload"] = copy.deepcopy(data["payload"])
            if "headers" in data and isinstance(data["headers"], (dict, list)):
                data["headers"] = copy.deepcopy(data["headers"])
        return data

    @model_validator(mode="after")
    def validate_non_empty_identifiers(self) -> "A2AMessage":
        for field_name in ("correlation_id", "sender", "recipient", "action"):
            val = getattr(self, field_name)
            if not isinstance(val, str) or not val.strip():
                raise ValueError(f"A2AMessage field '{field_name}' must be a non-empty string.")
        return self

    def create_response(
        self,
        performative: A2APerformative,
        payload: Dict[str, Any],
        action: Optional[str] = None,
        headers: Optional[Dict[str, Any]] = None,
    ) -> "A2AMessage":
        """
        Creates a properly correlated response envelope swapping sender and recipient.
        """
        resp_headers = dict(self.headers)
        if headers:
            resp_headers.update(headers)

        return A2AMessage(
            correlation_id=self.correlation_id,
            sender=self.recipient,
            recipient=self.sender,
            performative=performative,
            action=action or self.action,
            payload=copy.deepcopy(payload),
            headers=resp_headers,
        )

    def scrubbed_copy(self) -> "A2AMessage":
        """Returns a defensive copy with credentials and sensitive values redacted."""
        return A2AMessage(
            message_id=self.message_id,
            correlation_id=self.correlation_id,
            sender=self.sender,
            recipient=self.recipient,
            performative=self.performative,
            timestamp=self.timestamp,
            action=self.action,
            payload=_scrub_value(copy.deepcopy(self.payload)),
            headers=_scrub_value(copy.deepcopy(self.headers)),
        )


# ==============================================================================
# 2. Typed Payloads
# ==============================================================================

class CriticDirectivePayload(BaseModel):
    """
    Structured critique output generated by the adversarial critic agent.
    Provides verified failure mechanisms and prescriptive test directives.
    """
    analysis: str = Field(..., description="Concise diagnostic reasoning on why mutants survived")
    target_mutants: List[str] = Field(default_factory=list, description="IDs of surviving mutants analyzed")
    directives: List[str] = Field(default_factory=list, description="Prescriptive assertions and boundary directives")
    failure_mechanisms: Dict[str, str] = Field(
        default_factory=dict,
        description="Mapping of mutant_id to root cause failure mechanism"
    )


# Alias for compatibility with design terminology
A2ACritiqueDirectivePayload = CriticDirectivePayload


class A2ACritiqueRequestPayload(BaseModel):
    """Payload sent to request mutant diagnosis from the adversarial critic."""
    target_source_code: str = Field(..., description="Clean Python source code under test")
    surviving_mutants: List[Dict[str, Any]] = Field(default_factory=list, description="Serialized surviving MutantRecords")
    surviving_diffs: List[str] = Field(default_factory=list, description="Unified AST diffs of surviving mutants")
    iteration: int = Field(default=1, ge=1, description="Current reflection iteration index")


class A2ACritiqueResponsePayload(BaseModel):
    """Envelope payload wrapping critique execution results."""
    directive: CriticDirectivePayload
    execution_time_sec: float = 0.0
    critic_agent: str = "agent:crewai:critic"


class GeneratedTestPayload(BaseModel):
    """
    Structured test generation output produced by the Google ADK Generator Agent.
    Strictly distinguishes intended mutant coverage from measured execution results.
    """
    test_code: str = Field(..., description="Syntactically valid Python Pytest test suite code")
    target_function: Optional[str] = Field(None, description="Primary function or behavior under test")
    covered_mutants: List[str] = Field(
        default_factory=list,
        description="IDs of supplied surviving mutants targeted by the generated tests"
    )
    test_rationale: str = Field(default="", description="Concise explanation of proposed test assertions and boundary checks")
    assumptions: List[str] = Field(default_factory=list, description="Assumptions made about input types and domain bounds")
    warnings: List[str] = Field(default_factory=list, description="Known test limitations or potential edge-case ambiguities")
    generation_metadata: Dict[str, Any] = Field(
        default_factory=dict,
        description="Non-sensitive metadata such as iteration, model, and AST verification status"
    )

    @model_validator(mode="after")
    def validate_test_code_not_empty(self) -> "GeneratedTestPayload":
        if not self.test_code or not self.test_code.strip():
            raise ValueError("Generated test_code cannot be empty or whitespace.")
        return self


class A2ATestGenerationRequestPayload(BaseModel):
    """Typed request payload sent to the Google ADK generator via A2A."""
    target_source_code: str = Field(..., description="Target Python source code under test")
    existing_test_code: Optional[str] = Field(None, description="Current Pytest code from SuiteSpace")
    surviving_diffs: List[str] = Field(default_factory=list, description="AST unified diffs of surviving mutants")
    surviving_mutants: List[Dict[str, Any]] = Field(default_factory=list, description="Serialized surviving MutantRecords")
    critic_directive: Optional[str] = Field(None, description="Adversarial directives from CrewAI critic")
    iteration: int = Field(default=1, ge=1, description="Current reflection iteration index")
    target_function: Optional[str] = Field(None, description="Specific target function name if localized")


class A2AErrorPayload(BaseModel):
    """Standardized error payload returned on refusal or execution failure."""
    error: str = Field(..., description="Human-readable description of error or refusal")
    refusal_reason: Optional[str] = Field(None, description="Standardized refusal code (e.g. UNAUTHORIZED, PROMPT_INJECTION)")
    details: Dict[str, Any] = Field(default_factory=dict, description="Diagnostic metadata")


# ==============================================================================
# 3. Agent Handler Registration Model
# ==============================================================================

class AgentHandlerRegistration:
    """Internal registration model for named A2A agent handlers."""
    def __init__(
        self,
        agent_id: str,
        handler: Callable[[A2AMessage], A2AMessage],
        allowed_actions: Optional[Set[str]] = None,
        allowed_senders: Optional[Set[str]] = None,
        description: str = "",
    ):
        self.agent_id = agent_id
        self.handler = handler
        self.allowed_actions = allowed_actions
        self.allowed_senders = allowed_senders
        self.description = description

    def is_action_allowed(self, action: str) -> bool:
        if self.allowed_actions is None:
            return True
        return action in self.allowed_actions

    def is_sender_allowed(self, sender: str) -> bool:
        if self.allowed_senders is None:
            return True
        return sender in self.allowed_senders


# ==============================================================================
# 4. A2A Message Broker Implementation
# ==============================================================================

class A2ABroker:
    """
    In-process A2A Message Broker for multi-agent coordination.

    Features:
      - Validates all incoming and outgoing envelopes via Pydantic.
      - Authorizes sender, recipient, and action permissions.
      - Enforces input security guardrails (prompt injection inspection).
      - Executes agent handlers inside bounded timeouts.
      - Emits typed lifecycle callback events for handoffs and errors.
      - Synchronizes validated critique results to Blackboard CriticSpace.
      - Guarantees deep-copy isolation preventing accidental message mutation.
      - Redacts credentials and sensitive tokens from history and logs.
    """
    def __init__(
        self,
        blackboard: Optional[Any] = None,
        callback_registry: Optional[CallbackRegistry] = None,
        security_guardrail: Optional[SecurityGuardrail] = None,
        default_timeout_sec: float = 45.0,
    ):
        self._blackboard = blackboard
        self._callbacks = callback_registry
        self._security = security_guardrail or SecurityGuardrail()
        self._default_timeout_sec = default_timeout_sec
        self._handlers: Dict[str, AgentHandlerRegistration] = {}
        self._history: List[A2AMessage] = []
        self._lock = threading.RLock()

    # --------------------------------------------------------------------------
    # Registration Management
    # --------------------------------------------------------------------------

    def register_handler(
        self,
        agent_id: str,
        handler: Callable[[A2AMessage], A2AMessage],
        allowed_actions: Optional[Union[List[str], Set[str]]] = None,
        allowed_senders: Optional[Union[List[str], Set[str]]] = None,
        description: str = "",
    ) -> None:
        """Registers a named agent handler with authorization policies."""
        if not agent_id or not isinstance(agent_id, str):
            raise ValueError("agent_id must be a non-empty string.")
        if not callable(handler):
            raise TypeError(f"Handler for agent '{agent_id}' must be callable.")

        actions_set = set(allowed_actions) if allowed_actions is not None else None
        senders_set = set(allowed_senders) if allowed_senders is not None else None

        with self._lock:
            self._handlers[agent_id] = AgentHandlerRegistration(
                agent_id=agent_id,
                handler=handler,
                allowed_actions=actions_set,
                allowed_senders=senders_set,
                description=description,
            )
            logger.info(f"Registered A2A agent handler: '{agent_id}' (actions={actions_set})")

    def unregister_handler(self, agent_id: str) -> bool:
        """Unregisters a previously registered agent handler."""
        with self._lock:
            if agent_id in self._handlers:
                del self._handlers[agent_id]
                logger.info(f"Unregistered A2A agent handler: '{agent_id}'")
                return True
            return False

    def list_handlers(self) -> List[str]:
        """Returns registered agent handler IDs."""
        with self._lock:
            return list(self._handlers.keys())

    # --------------------------------------------------------------------------
    # Message Dispatch & Execution
    # --------------------------------------------------------------------------

    def send_message(
        self,
        message: A2AMessage,
        timeout_sec: Optional[float] = None,
    ) -> A2AMessage:
        """
        Dispatches an A2AMessage through authorization, security inspection,
        handler execution with timeout, and Blackboard synchronization.
        """
        if not isinstance(message, A2AMessage):
            raise TypeError(f"Expected A2AMessage instance, got {type(message).__name__}")

        timeout = timeout_sec if timeout_sec is not None else self._default_timeout_sec

        # 1. Store defensive copy of incoming request
        in_msg = message.model_copy(deep=True)
        self._record_message(in_msg)

        # 2. Authorize Recipient
        with self._lock:
            registration = self._handlers.get(in_msg.recipient)

        if not registration:
            err_msg = f"Recipient agent '{in_msg.recipient}' is not registered."
            logger.warning(err_msg)
            self._dispatch_callback(
                EventType.ERROR,
                emitter="broker",
                payload={"error": err_msg, "recipient": in_msg.recipient},
            )
            resp = in_msg.create_response(
                performative=A2APerformative.REFUSE,
                payload=A2AErrorPayload(
                    error=err_msg,
                    refusal_reason="UNREGISTERED_RECIPIENT",
                ).model_dump(),
                action=in_msg.action,
            )
            self._record_message(resp)
            return resp

        # 3. Authorize Sender
        if not registration.is_sender_allowed(in_msg.sender):
            err_msg = f"Sender '{in_msg.sender}' is not authorized to contact '{in_msg.recipient}'."
            logger.warning(err_msg)
            self._dispatch_callback(
                EventType.ERROR,
                emitter="broker",
                payload={"error": err_msg, "sender": in_msg.sender, "recipient": in_msg.recipient},
            )
            resp = in_msg.create_response(
                performative=A2APerformative.REFUSE,
                payload=A2AErrorPayload(
                    error=err_msg,
                    refusal_reason="UNAUTHORIZED_SENDER",
                ).model_dump(),
                action=in_msg.action,
            )
            self._record_message(resp)
            return resp

        # 4. Authorize Action
        if not registration.is_action_allowed(in_msg.action):
            err_msg = f"Action '{in_msg.action}' is not permitted for recipient '{in_msg.recipient}'."
            logger.warning(err_msg)
            self._dispatch_callback(
                EventType.ERROR,
                emitter="broker",
                payload={"error": err_msg, "action": in_msg.action, "recipient": in_msg.recipient},
            )
            resp = in_msg.create_response(
                performative=A2APerformative.REFUSE,
                payload=A2AErrorPayload(
                    error=err_msg,
                    refusal_reason="UNAUTHORIZED_ACTION",
                ).model_dump(),
                action=in_msg.action,
            )
            self._record_message(resp)
            return resp

        # 5. Security Guardrail Inspection (Prompt Injection)
        prompt_inspection_text = self._extract_text_for_security_scan(in_msg.payload)
        if prompt_inspection_text:
            sec_res = self._security.inspect_prompt(prompt_inspection_text)
            if not sec_res.allowed:
                reason = f"Security guardrail rejected message payload: {sec_res.explanation}"
                logger.warning(f"A2ABroker blocked message due to security violation: {reason}")
                findings_dump = [f.model_dump() for f in sec_res.findings]
                self._dispatch_callback(
                    EventType.ERROR,
                    emitter="broker:security",
                    payload={"error": reason, "findings": findings_dump},
                )
                resp = in_msg.create_response(
                    performative=A2APerformative.REFUSE,
                    payload=A2AErrorPayload(
                        error=reason,
                        refusal_reason="PROMPT_INJECTION_DETECTED",
                        details={"findings": findings_dump, "risk_level": sec_res.risk_level.value},
                    ).model_dump(),
                    action=in_msg.action,
                )
                self._record_message(resp)
                return resp

        # 6. Dispatch AGENT_HANDOFF start event
        self._dispatch_callback(
            EventType.AGENT_HANDOFF,
            emitter="broker",
            payload={
                "from_agent": in_msg.sender,
                "to_agent": in_msg.recipient,
                "action": in_msg.action,
                "correlation_id": in_msg.correlation_id,
                "summary": f"Dispatching '{in_msg.action}' to '{in_msg.recipient}'",
            },
        )

        # 7. Execute Handler with Bounded Timeout
        t0 = time.perf_counter()
        raw_response: Optional[A2AMessage] = None

        try:
            with ThreadPoolExecutor(max_workers=1) as executor:
                future = executor.submit(registration.handler, in_msg.model_copy(deep=True))
                raw_response = future.result(timeout=timeout)
        except FuturesTimeoutError:
            err_msg = f"Handler execution for '{in_msg.recipient}' timed out after {timeout:.2f}s."
            logger.error(err_msg)
            self._dispatch_callback(
                EventType.ERROR,
                emitter="broker",
                payload={"error": err_msg, "timeout_sec": timeout},
            )
            resp = in_msg.create_response(
                performative=A2APerformative.FAILURE,
                payload=A2AErrorPayload(
                    error=err_msg,
                    refusal_reason="TIMEOUT",
                    details={"timeout_sec": timeout},
                ).model_dump(),
                action=in_msg.action,
            )
            self._record_message(resp)
            return resp
        except Exception as exc:
            safe_err = redact_sensitive_data(str(exc))
            err_msg = f"Handler for '{in_msg.recipient}' raised unhandled exception: {safe_err}"
            logger.error(err_msg, exc_info=True)
            self._dispatch_callback(
                EventType.ERROR,
                emitter="broker",
                payload={"error": err_msg},
            )
            resp = in_msg.create_response(
                performative=A2APerformative.FAILURE,
                payload=A2AErrorPayload(
                    error=err_msg,
                    refusal_reason="HANDLER_EXCEPTION",
                ).model_dump(),
                action=in_msg.action,
            )
            self._record_message(resp)
            return resp

        elapsed_sec = time.perf_counter() - t0

        # 8. Validate Response Envelope
        if not isinstance(raw_response, A2AMessage):
            err_msg = f"Handler returned invalid object of type {type(raw_response).__name__}, expected A2AMessage."
            logger.error(err_msg)
            resp = in_msg.create_response(
                performative=A2APerformative.FAILURE,
                payload=A2AErrorPayload(
                    error=err_msg,
                    refusal_reason="INVALID_RESPONSE_TYPE",
                ).model_dump(),
                action=in_msg.action,
            )
            self._record_message(resp)
            return resp

        # Guarantee correlation ID match
        if raw_response.correlation_id != in_msg.correlation_id:
            logger.warning(
                f"Handler changed correlation_id from '{in_msg.correlation_id}' to "
                f"'{raw_response.correlation_id}'. Overriding to enforce correlation invariant."
            )
            raw_response.correlation_id = in_msg.correlation_id

        # 9. Blackboard Partition Synchronization (CriticSpace & SuiteSpace)
        if (
            self._blackboard is not None
            and raw_response.performative == A2APerformative.INFORM
        ):
            if in_msg.recipient == "agent:crewai:critic":
                self._sync_critique_to_blackboard(raw_response)
            elif in_msg.recipient in ("agent:google-adk:generator", "agent:adk:generator"):
                self._sync_generator_to_blackboard(raw_response)

        # 10. Dispatch Success Event
        self._dispatch_callback(
            EventType.OPERATION_COMPLETE,
            emitter="broker",
            payload={
                "operation_name": f"a2a_{in_msg.action}",
                "status": raw_response.performative.value,
                "duration_sec": elapsed_sec,
                "correlation_id": in_msg.correlation_id,
            },
        )

        resp_copy = raw_response.model_copy(deep=True)
        self._record_message(resp_copy)
        return resp_copy

    # --------------------------------------------------------------------------
    # Internal Helpers
    # --------------------------------------------------------------------------

    def _sync_critique_to_blackboard(self, response: A2AMessage) -> None:
        """Validates critique payload and safely updates Blackboard CriticSpace."""
        try:
            # Check if payload contains CriticDirectivePayload directly or nested
            payload_data = response.payload
            if "directive" in payload_data and isinstance(payload_data["directive"], dict):
                directive_obj = CriticDirectivePayload.model_validate(payload_data["directive"])
            else:
                directive_obj = CriticDirectivePayload.model_validate(payload_data)

            # Format directive string
            primary_directive = directive_obj.analysis
            if directive_obj.directives:
                directives_list = "\n".join(f"- {d}" for d in directive_obj.directives)
                primary_directive = f"{primary_directive}\n\nPrescribed Directives:\n{directives_list}"

            # Safely fetch existing critic space
            existing_critic = self._blackboard.get_critic_space()
            new_directives = list(existing_critic.critic_directives)
            if primary_directive:
                new_directives.append(primary_directive)

            new_mechanisms = dict(existing_critic.failure_mechanisms)
            new_mechanisms.update(directive_obj.failure_mechanisms)

            new_notes = list(existing_critic.reflection_notes)
            new_notes.append(
                f"CrewAI Critic analyzed {len(directive_obj.target_mutants)} mutant(s) "
                f"(correlation: {response.correlation_id})"
            )

            # Update Blackboard CriticSpace atomically
            self._blackboard.update_critic_space(
                latest_directive=primary_directive,
                critic_directives=new_directives,
                failure_mechanisms=new_mechanisms,
                reflection_notes=new_notes,
            )
            logger.info("Synchronized validated CrewAI critique to Blackboard CriticSpace.")
        except ValidationError as val_err:
            logger.error(f"Failed to validate CriticDirectivePayload for Blackboard sync: {val_err}")
        except Exception as exc:
            logger.error(f"Unexpected error synchronizing critique to Blackboard: {exc}", exc_info=True)

    def _sync_generator_to_blackboard(self, response: A2AMessage) -> None:
        """Validates generated test payload and safely updates Blackboard SuiteSpace."""
        try:
            from testforge.agents import CodeSanitizer
            payload_data = response.payload
            test_code = payload_data.get("test_code", "")
            if not test_code or not isinstance(test_code, str):
                logger.error("Generated test payload missing 'test_code' string for Blackboard sync.")
                return

            is_valid, sanitized_code, err = CodeSanitizer.extract_and_validate(test_code, enforce_security=True)
            if not is_valid:
                logger.error(f"Generated test code failed AST validation/security inspection: {err}")
                return

            existing_current = self._blackboard.get_suite_space().current_test_code
            updates = {
                "candidate_test_code": sanitized_code,
                "active_provider": "Google ADK Generator",
            }
            # Only populate current_test_code if no accepted suite exists yet (initial baseline).
            # If an accepted suite already exists, it must NOT be overwritten until validated.
            if not existing_current or not existing_current.strip():
                updates["current_test_code"] = sanitized_code

            self._blackboard.update_suite_space(**updates)
            logger.info("Synchronized candidate Google ADK test code to Blackboard SuiteSpace.")
        except Exception as exc:
            logger.error(f"Unexpected error synchronizing generator output to Blackboard: {exc}", exc_info=True)

    def _extract_text_for_security_scan(self, payload: Dict[str, Any]) -> str:
        """Extracts text candidate fields from payload to inspect for prompt injection."""
        text_parts = []
        for key in ("target_source_code", "analysis", "directive", "prompt", "text", "context"):
            val = payload.get(key)
            if isinstance(val, str):
                text_parts.append(val)
        # Also inspect directive lists
        directives = payload.get("directives")
        if isinstance(directives, list):
            for d in directives:
                if isinstance(d, str):
                    text_parts.append(d)
        return "\n\n".join(text_parts)

    def _dispatch_callback(self, event_type: EventType, emitter: str, payload: Dict[str, Any]) -> None:
        """Safely dispatches lifecycle callbacks without allowing subscriber exceptions to escape."""
        if not self._callbacks:
            return
        try:
            event = LifecycleEvent(
                event_type=event_type,
                emitter=emitter,
                payload=_scrub_value(copy.deepcopy(payload)),
            )
            self._callbacks.dispatch(event)
        except Exception as exc:
            logger.warning(f"A2ABroker failed to dispatch callback event {event_type}: {exc}")

    def _record_message(self, msg: A2AMessage) -> None:
        """Records scrubbed message into broker history."""
        with self._lock:
            self._history.append(msg.scrubbed_copy())

    def get_history(self) -> List[A2AMessage]:
        """Returns deep-copied immutable history of dispatched messages."""
        with self._lock:
            return [m.model_copy(deep=True) for m in self._history]

    def clear_history(self) -> None:
        """Clears message history."""
        with self._lock:
            self._history.clear()
