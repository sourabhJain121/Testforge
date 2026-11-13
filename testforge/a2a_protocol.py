"""
a2a_protocol.py - Official Agent2Agent (A2A) Protocol Interoperability Layer.

Author: TestForge Agentic Upgrade
Phase: Phase 4D - Official A2A Protocol Interoperability

This module establishes genuine protocol-compliant agent communication adhering
to the official A2A protocol specification (v0.3.0) via `a2a-sdk`.

Architecture:
  1. Agent Discovery:
     - Exposes an official `AgentCard` at `/.well-known/agent-card.json`.
     - Declares capabilities (`streaming=False`), transport (`jsonrpc`),
       and distinct skills (`unit-test-generation`, `mutation-critique`, `hardening-workflow`).
     - Strictly redacts credentials, file paths, or private configuration.
  2. A2A Server & Request Execution:
     - `TestForgeA2AExecutor(AgentExecutor)` converts protocol-valid incoming A2A `Message`
       requests into internal `A2AMessage` envelopes dispatched to `A2ABroker`.
     - Validates incoming prompt security via `SecurityGuardrail` before any agent dispatch.
     - Dispatches to Google ADK Generator (`agent:google-adk:generator`) and
       CrewAI Critic (`agent:crewai:critic`).
     - Emits standard A2A task lifecycle events:
       `TaskStatusUpdateEvent` (working, completed, failed) and `TaskArtifactUpdateEvent` (artifacts).
  3. Blackboard & Verification Preservation:
     - Validates generated test AST and syntax via `CodeSanitizer` before accepting output.
     - Only updates Blackboard `SuiteSpace` when generated code is syntactically valid and sanitized.
     - Retains previous Blackboard state upon execution failures without corrupting revisions.
  4. Client Boundary:
     - `TestForgeA2AClient` establishes standard A2A client sessions using `a2a.client`
       (`A2ACardResolver`, `ClientFactory`, `BaseClient`) over HTTP/ASGI JSON-RPC transport.
"""

from __future__ import annotations

import json
import logging
import os
import time
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import httpx
from a2a.client import A2ACardResolver, ClientConfig, ClientFactory
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.apps import A2AStarletteApplication
from a2a.server.events import EventQueue
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentProvider,
    AgentSkill,
    Artifact,
    DataPart,
    Message,
    Part,
    Role,
    Task,
    TaskArtifactUpdateEvent,
    TaskState,
    TaskStatus,
    TaskStatusUpdateEvent,
    TextPart,
    TransportProtocol,
)
from starlette.applications import Starlette
from starlette.responses import JSONResponse

from testforge.a2a import (
    A2ABroker,
    A2AMessage,
    A2APerformative,
)
from testforge.agents import CodeSanitizer
from testforge.callbacks import (
    CallbackRegistry,
    EventType,
    LifecycleEvent,
)
from testforge.security import SecurityGuardrail

logger = logging.getLogger("testforge.a2a_protocol")

OFFICIAL_A2A_PROTOCOL_VERSION = "0.3.0"
TESTFORGE_AGENT_NAME = "testforge-agent-system"
TESTFORGE_AGENT_VERSION = "1.0.0"


# ==============================================================================
# 1. Agent Discovery & Agent Card Specification
# ==============================================================================

def build_testforge_agent_card(
    rpc_url: Optional[str] = None,
    name: str = TESTFORGE_AGENT_NAME,
    version: str = TESTFORGE_AGENT_VERSION,
) -> AgentCard:
    """
    Constructs an official, protocol-compliant A2A AgentCard describing TestForge's
    multi-agent hardening capabilities.

    Exposes:
      - Unit Test Generation (Google ADK)
      - Mutation Critique (CrewAI)
      - Full Hardening Workflow (Iterative Cycle)

    Guarantees that no internal credentials, absolute file paths, or private
    keys are present in the public card.
    """
    if not rpc_url:
        rpc_url = (
            os.environ.get("TESTFORGE_PUBLIC_URL")
            or os.environ.get("RENDER_EXTERNAL_URL")
            or "http://127.0.0.1:8000/"
        )
    clean_url = rpc_url.rstrip("/") + "/"
    skills = [
        AgentSkill(
            id="unit-test-generation",
            name="Unit Test Generation",
            description="Generates syntactically valid Python unit tests targeting surviving mutants using Google ADK.",
            tags=["testing", "adk", "generation", "python"],
        ),
        AgentSkill(
            id="mutation-critique",
            name="Mutation Critique",
            description="Performs adversarial critique of test suites and surviving mutation diffs using CrewAI.",
            tags=["critique", "crewai", "mutation-testing"],
        ),
        AgentSkill(
            id="hardening-workflow",
            name="Hardening Workflow",
            description="Executes a complete generator-critic hardening cycle updating the typed Blackboard.",
            tags=["hardening", "workflow", "blackboard"],
        ),
    ]

    provider = AgentProvider(
        organization="TestForge Autonomous Systems",
        url="https://github.com/sourabhJain121/Testforge",
    )

    card = AgentCard(
        name=name,
        description="Autonomous Agentic Unit Test Hardening System powered by Google ADK and CrewAI.",
        url=clean_url,
        version=version,
        protocol_version=OFFICIAL_A2A_PROTOCOL_VERSION,
        preferred_transport=TransportProtocol.jsonrpc,
        default_input_modes=["text", "json"],
        default_output_modes=["text", "json"],
        capabilities=AgentCapabilities(
            streaming=False,
            push_notifications=False,
        ),
        skills=skills,
        provider=provider,
    )
    return card


# ==============================================================================
# 2. A2A Agent Executor (Bridge to TestForge Agents & Blackboard)
# ==============================================================================

class TestForgeA2AExecutor(AgentExecutor):
    """
    Official A2A AgentExecutor implementation for TestForge.

    Translates wire-protocol A2A requests into internal A2AMessage envelopes,
    dispatches them through the A2ABroker to the Google ADK generator or CrewAI critic,
    validates generated test ASTs, applies security guardrails, updates the Blackboard,
    and returns standardized A2A task lifecycle events and artifacts.
    """
    __test__ = False

    def __init__(
        self,
        broker: A2ABroker,
        blackboard: Optional[Any] = None,
        guardrail: Optional[SecurityGuardrail] = None,
        callbacks: Optional[CallbackRegistry] = None,
    ):
        self.broker = broker
        self.blackboard = blackboard
        self.guardrail = guardrail or SecurityGuardrail()
        self.callbacks = callbacks

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        """
        Executes an incoming A2A message request and enqueues lifecycle events.
        """
        task_id = context.task_id or str(uuid.uuid4())
        context_id = context.context_id or str(uuid.uuid4())

        if not context.message:
            await self._enqueue_failure(
                event_queue=event_queue,
                task_id=task_id,
                context_id=context_id,
                error_message="A2A protocol request must include a message.",
            )
            return

        # 1. Extract message content and parameters
        raw_text, params = self._extract_content(context.message)

        # 2. Security Guardrail: Inspect input for prompt injections / unsafe payloads
        sec_res = self.guardrail.inspect_prompt(raw_text)
        if not sec_res.allowed:
            refusal_reason = sec_res.explanation or "Prompt injection or policy violation detected"
            logger.warning("Security refusal at A2A protocol boundary: %s", refusal_reason)
            if self.callbacks:
                self.callbacks.dispatch(LifecycleEvent(
                    event_type=EventType.ERROR,
                    emitter="a2a-protocol-gateway",
                    payload={"error_type": "SECURITY_VIOLATION", "reason": refusal_reason, "task_id": task_id},
                ))
            await self._enqueue_failure(
                event_queue=event_queue,
                task_id=task_id,
                context_id=context_id,
                error_message=f"Security Refusal: {refusal_reason}",
            )
            return

        # 3. Publish WORKING status event
        await event_queue.enqueue_event(
            TaskStatusUpdateEvent(
                task_id=task_id,
                context_id=context_id,
                status=TaskStatus(
                    state=TaskState.working,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                ),
                final=False,
            )
        )

        # 4. Route request based on skill or action
        action = (
            params.get("action")
            or params.get("skill_id")
            or (context.message.metadata.get("action") if context.message.metadata else None)
            or (context.message.metadata.get("skill_id") if context.message.metadata else None)
            or self._infer_action(raw_text, params)
        )

        try:
            if action in ("generate_tests", "unit-test-generation"):
                await self._handle_test_generation(context, event_queue, task_id, context_id, params)
            elif action in ("diagnose_mutants", "mutation-critique"):
                await self._handle_critique(context, event_queue, task_id, context_id, params)
            elif action in ("hardening-workflow", "workflow"):
                await self._handle_workflow(context, event_queue, task_id, context_id, params)
            else:
                await self._enqueue_failure(
                    event_queue=event_queue,
                    task_id=task_id,
                    context_id=context_id,
                    error_message=f"Unsupported action or skill '{action}'. Supported: 'unit-test-generation', 'mutation-critique', 'hardening-workflow'.",
                )
        except Exception as exc:
            logger.exception("Unexpected error in TestForgeA2AExecutor: %s", exc)
            await self._enqueue_failure(
                event_queue=event_queue,
                task_id=task_id,
                context_id=context_id,
                error_message=f"Internal agent execution error: {str(exc)}",
            )

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        """Handles task cancellation request."""
        task_id = context.task_id or str(uuid.uuid4())
        context_id = context.context_id or str(uuid.uuid4())
        await event_queue.enqueue_event(
            TaskStatusUpdateEvent(
                task_id=task_id,
                context_id=context_id,
                status=TaskStatus(
                    state=TaskState.canceled,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                ),
                final=True,
            )
        )

    # --------------------------------------------------------------------------
    # Handlers for Specific Capabilities
    # --------------------------------------------------------------------------

    async def _handle_test_generation(
        self,
        context: RequestContext,
        event_queue: EventQueue,
        task_id: str,
        context_id: str,
        params: Dict[str, Any],
    ) -> None:
        target_source = params.get("target_source_code") or params.get("source_code") or ""
        if not target_source.strip():
            await self._enqueue_failure(
                event_queue=event_queue,
                task_id=task_id,
                context_id=context_id,
                error_message="Missing required field 'target_source_code' for test generation.",
            )
            return

        internal_payload = {
            "target_source_code": target_source,
            "existing_test_code": params.get("existing_test_code"),
            "surviving_diffs": params.get("surviving_diffs", []),
            "surviving_mutants": params.get("surviving_mutants", []),
            "critic_directive": params.get("critic_directive"),
            "iteration": params.get("iteration", 1),
            "target_function": params.get("target_function"),
        }

        req_msg = A2AMessage(
            correlation_id=task_id,
            sender="agent:a2a-protocol:client",
            recipient="agent:google-adk:generator",
            performative=A2APerformative.REQUEST,
            action="generate_tests",
            payload=internal_payload,
        )

        resp_msg = self.broker.send_message(req_msg)

        if resp_msg.performative in (A2APerformative.FAILURE, A2APerformative.REFUSE):
            err_text = resp_msg.payload.get("error", "Generator failed to synthesize tests.")
            await self._enqueue_failure(
                event_queue=event_queue,
                task_id=task_id,
                context_id=context_id,
                error_message=err_text,
            )
            return

        # Validate structured test output
        test_code = resp_msg.payload.get("test_code", "")
        sanitizer = CodeSanitizer()
        is_valid, sanitized_code, validation_msg = sanitizer.extract_and_validate(test_code)

        if not is_valid:
            await self._enqueue_failure(
                event_queue=event_queue,
                task_id=task_id,
                context_id=context_id,
                error_message=f"Generated test code failed AST validation: {validation_msg}",
            )
            return

        # Update Blackboard SuiteSpace only upon valid AST
        if self.blackboard is not None:
            try:
                self.blackboard.update_suite_space(
                    current_test_code=sanitized_code,
                    hardened_test_code=sanitized_code,
                    active_provider="Google ADK",
                )
            except Exception as b_exc:
                logger.error("Failed to update Blackboard suite: %s", b_exc)

        # Enqueue Artifact and Completed Status
        artifact = Artifact(
            artifact_id=str(uuid.uuid4()),
            name="generated_test.py",
            parts=[Part(root=TextPart(text=sanitized_code))],
            metadata={
                "covered_mutants": resp_msg.payload.get("covered_mutants", []),
                "target_function": resp_msg.payload.get("target_function"),
                "test_rationale": resp_msg.payload.get("test_rationale", ""),
            },
        )
        await event_queue.enqueue_event(
            TaskArtifactUpdateEvent(
                task_id=task_id,
                context_id=context_id,
                last_chunk=True,
                artifact=artifact,
            )
        )
        await event_queue.enqueue_event(
            TaskStatusUpdateEvent(
                task_id=task_id,
                context_id=context_id,
                status=TaskStatus(
                    state=TaskState.completed,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                ),
                final=True,
            )
        )

    async def _handle_critique(
        self,
        context: RequestContext,
        event_queue: EventQueue,
        task_id: str,
        context_id: str,
        params: Dict[str, Any],
    ) -> None:
        target_source = params.get("target_source_code") or params.get("source_code") or ""
        if not target_source.strip():
            await self._enqueue_failure(
                event_queue=event_queue,
                task_id=task_id,
                context_id=context_id,
                error_message="Missing required field 'target_source_code' for critique.",
            )
            return

        internal_payload = {
            "target_source_code": target_source,
            "surviving_mutants": params.get("surviving_mutants", []),
            "surviving_diffs": params.get("surviving_diffs", []),
            "iteration": params.get("iteration", 1),
        }

        req_msg = A2AMessage(
            correlation_id=task_id,
            sender="agent:a2a-protocol:client",
            recipient="agent:crewai:critic",
            performative=A2APerformative.REQUEST,
            action="diagnose_mutants",
            payload=internal_payload,
        )

        resp_msg = self.broker.send_message(req_msg)

        if resp_msg.performative in (A2APerformative.FAILURE, A2APerformative.REFUSE):
            err_text = resp_msg.payload.get("error", "Critic failed to diagnose mutants.")
            await self._enqueue_failure(
                event_queue=event_queue,
                task_id=task_id,
                context_id=context_id,
                error_message=err_text,
            )
            return

        directive = resp_msg.payload.get("directive") or resp_msg.payload
        artifact = Artifact(
            artifact_id=str(uuid.uuid4()),
            name="critique_directive.json",
            parts=[Part(root=TextPart(text=json.dumps(directive, indent=2)))],
            metadata={"critic": "agent:crewai:critic"},
        )
        await event_queue.enqueue_event(
            TaskArtifactUpdateEvent(
                task_id=task_id,
                context_id=context_id,
                last_chunk=True,
                artifact=artifact,
            )
        )
        await event_queue.enqueue_event(
            TaskStatusUpdateEvent(
                task_id=task_id,
                context_id=context_id,
                status=TaskStatus(
                    state=TaskState.completed,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                ),
                final=True,
            )
        )

    async def _handle_workflow(
        self,
        context: RequestContext,
        event_queue: EventQueue,
        task_id: str,
        context_id: str,
        params: Dict[str, Any],
    ) -> None:
        target_source = params.get("target_source_code") or params.get("source_code") or ""
        if not target_source.strip():
            await self._enqueue_failure(
                event_queue=event_queue,
                task_id=task_id,
                context_id=context_id,
                error_message="Missing required field 'target_source_code' for workflow.",
            )
            return

        from testforge.adk_generator import GeneratorCriticWorkflow
        workflow = GeneratorCriticWorkflow(
            broker=self.broker,
            blackboard=self.blackboard,
            callbacks=self.callbacks,
            guardrail=self.guardrail,
        )

        result = workflow.run_iteration(
            source_code=target_source,
            existing_tests=params.get("existing_test_code"),
            surviving_diffs=params.get("surviving_diffs", []),
            surviving_mutants=params.get("surviving_mutants", []),
            iteration=params.get("iteration", 1),
        )

        if result.status == "FAILED" or not result.generated_tests:
            err_summary = "; ".join(result.errors) if result.errors else "Hardening cycle failed."
            await self._enqueue_failure(
                event_queue=event_queue,
                task_id=task_id,
                context_id=context_id,
                error_message=err_summary,
            )
            return

        artifact = Artifact(
            artifact_id=str(uuid.uuid4()),
            name="hardened_test_suite.py",
            parts=[Part(root=TextPart(text=result.generated_tests.test_code))],
            metadata={
                "status": result.status,
                "mutants_killed": result.mutants_killed,
                "surviving_mutants_count": result.surviving_mutants_count,
            },
        )
        await event_queue.enqueue_event(
            TaskArtifactUpdateEvent(
                task_id=task_id,
                context_id=context_id,
                last_chunk=True,
                artifact=artifact,
            )
        )
        await event_queue.enqueue_event(
            TaskStatusUpdateEvent(
                task_id=task_id,
                context_id=context_id,
                status=TaskStatus(
                    state=TaskState.completed,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                ),
                final=True,
            )
        )

    # --------------------------------------------------------------------------
    # Utility Helpers
    # --------------------------------------------------------------------------

    def _extract_content(self, message: Message) -> Tuple[str, Dict[str, Any]]:
        """Extracts text content and structured dictionary parameters from Message parts."""
        text_content = ""
        params: Dict[str, Any] = {}

        if message.parts:
            for part in message.parts:
                unwrapped = getattr(part, "root", part)
                if isinstance(unwrapped, TextPart):
                    text_content += unwrapped.text
                    # Attempt JSON parse of text part
                    stripped = unwrapped.text.strip()
                    if (stripped.startswith("{") and stripped.endswith("}")):
                        try:
                            parsed = json.loads(stripped)
                            if isinstance(parsed, dict):
                                params.update(parsed)
                        except Exception:
                            pass
                elif isinstance(unwrapped, DataPart):
                    if isinstance(unwrapped.data, dict):
                        params.update(unwrapped.data)

        if message.metadata:
            for k, v in message.metadata.items():
                if k not in params:
                    params[k] = v

        return text_content, params

    def _infer_action(self, text: str, params: Dict[str, Any]) -> str:
        """Infers requested action when not explicitly specified."""
        lower_text = text.lower()
        if "critique" in lower_text or "diagnose" in lower_text:
            return "diagnose_mutants"
        if "workflow" in lower_text or "cycle" in lower_text:
            return "hardening-workflow"
        return "generate_tests"

    async def _enqueue_failure(
        self,
        event_queue: EventQueue,
        task_id: str,
        context_id: str,
        error_message: str,
    ) -> None:
        """Publishes a terminal failure event conforming to A2A semantics."""
        await event_queue.enqueue_event(
            TaskStatusUpdateEvent(
                task_id=task_id,
                context_id=context_id,
                status=TaskStatus(
                    state=TaskState.failed,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    message=Message(
                        message_id=str(uuid.uuid4()),
                        role=Role.agent,
                        parts=[Part(root=TextPart(text=error_message))],
                    ),
                ),
                final=True,
            )
        )


# ==============================================================================
# 3. Server Factory
# ==============================================================================

def create_testforge_a2a_app(
    broker: A2ABroker,
    blackboard: Optional[Any] = None,
    guardrail: Optional[SecurityGuardrail] = None,
    callbacks: Optional[CallbackRegistry] = None,
    rpc_url: str = "http://127.0.0.1:8000/",
    agent_card: Optional[AgentCard] = None,
) -> Starlette:
    """
    Constructs a protocol-compliant Starlette application exposing the TestForge
    Agent-to-Agent (A2A) server endpoint.

    Endpoints:
      - `GET /.well-known/agent-card.json`: Official discovery document (AgentCard).
      - `GET /.well-known/agent.json`: Canonical discovery alias for compatibility.
      - `POST /`: JSON-RPC protocol endpoint for message execution (`message/send`).
      - `GET /health`: Health and protocol version check.
    """
    final_card = agent_card or build_testforge_agent_card(rpc_url=rpc_url)
    task_store = InMemoryTaskStore()

    agent_executor = TestForgeA2AExecutor(
        broker=broker,
        blackboard=blackboard,
        guardrail=guardrail,
        callbacks=callbacks,
    )

    request_handler = DefaultRequestHandler(
        agent_executor=agent_executor,
        task_store=task_store,
    )

    a2a_starlette_app = A2AStarletteApplication(
        agent_card=final_card,
        http_handler=request_handler,
    )

    app = Starlette()
    a2a_starlette_app.add_routes_to_app(app)

    # Health check endpoint
    async def health_check(request):
        return JSONResponse({
            "status": "healthy",
            "system": "TestForge",
            "protocol": "A2A",
            "protocol_version": OFFICIAL_A2A_PROTOCOL_VERSION,
            "agent_name": final_card.name,
            "timestamp": time.time(),
        })

    # Compatibility alias for .well-known/agent.json
    async def agent_json_alias(request):
        return JSONResponse(final_card.model_dump(by_alias=True, exclude_none=True))

    app.add_route("/health", health_check, methods=["GET"])
    app.add_route("/.well-known/agent.json", agent_json_alias, methods=["GET"])

    return app


# ==============================================================================
# 4. Official Protocol Client Adapter
# ==============================================================================

class TestForgeA2AClient:
    """
    Official A2A protocol client adapter for interacting with TestForge.

    Communicates exclusively using official A2A primitives (`AgentCard`,
    `A2ACardResolver`, `ClientFactory`, `Message`, `Task`, `Artifact`).
    """
    __test__ = False

    def __init__(
        self,
        base_url: str = "http://testserver",
        http_client: Optional[httpx.AsyncClient] = None,
        app: Optional[Starlette] = None,
    ):
        self.base_url = base_url.rstrip("/")
        self._owned_client = False
        if http_client is not None:
            self.http_client = http_client
        elif app is not None:
            self.http_client = httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app),
                base_url=self.base_url,
            )
            self._owned_client = True
        else:
            self.http_client = httpx.AsyncClient(base_url=self.base_url)
            self._owned_client = True

        self._card: Optional[AgentCard] = None

    async def __aenter__(self) -> "TestForgeA2AClient":
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.close()

    async def close(self) -> None:
        if self._owned_client and not self.http_client.is_closed:
            await self.http_client.aclose()

    async def discover_card(self) -> AgentCard:
        """Discovers the remote agent card via official A2ACardResolver."""
        resolver = A2ACardResolver(self.http_client, self.base_url)
        self._card = await resolver.get_agent_card()
        return self._card

    async def send_protocol_message(
        self,
        message: Message,
        card: Optional[AgentCard] = None,
    ) -> Task:
        """
        Sends an official A2A `Message` over JSON-RPC and consumes the resulting `Task`.
        """
        active_card = card or self._card
        if active_card is None:
            active_card = await self.discover_card()

        factory = ClientFactory(ClientConfig(
            httpx_client=self.http_client,
            streaming=False,
        ))
        client = factory.create(active_card)

        last_task: Optional[Task] = None
        async for event in client.send_message(message):
            if isinstance(event, tuple) and len(event) > 0 and isinstance(event[0], Task):
                last_task = event[0]
            elif isinstance(event, Task):
                last_task = event

        if last_task is None:
            raise RuntimeError("A2A protocol exchange did not produce a valid Task.")
        return last_task

    async def generate_tests(
        self,
        source_code: str,
        existing_test_code: Optional[str] = None,
        surviving_diffs: Optional[List[str]] = None,
        surviving_mutants: Optional[List[Dict[str, Any]]] = None,
        iteration: int = 1,
    ) -> Tuple[Task, Optional[str]]:
        """
        High-level helper to invoke 'unit-test-generation' capability via A2A protocol.
        Returns the protocol Task and extracted test code string.
        """
        payload = {
            "action": "generate_tests",
            "target_source_code": source_code,
            "existing_test_code": existing_test_code,
            "surviving_diffs": surviving_diffs or [],
            "surviving_mutants": surviving_mutants or [],
            "iteration": iteration,
        }
        msg = Message(
            message_id=str(uuid.uuid4()),
            role=Role.user,
            parts=[Part(root=TextPart(text=json.dumps(payload)))],
            metadata={"skill_id": "unit-test-generation"},
        )
        task = await self.send_protocol_message(msg)

        extracted_code: Optional[str] = None
        if task.artifacts:
            for art in task.artifacts:
                if art.parts:
                    for part in art.parts:
                        unwrapped = getattr(part, "root", part)
                        if isinstance(unwrapped, TextPart):
                            extracted_code = unwrapped.text
                            break
        return task, extracted_code

    async def request_critique(
        self,
        source_code: str,
        surviving_diffs: Optional[List[str]] = None,
        surviving_mutants: Optional[List[Dict[str, Any]]] = None,
        iteration: int = 1,
    ) -> Tuple[Task, Optional[Dict[str, Any]]]:
        """
        High-level helper to invoke 'mutation-critique' capability via A2A protocol.
        Returns the protocol Task and extracted critique directive dictionary.
        """
        payload = {
            "action": "diagnose_mutants",
            "target_source_code": source_code,
            "surviving_diffs": surviving_diffs or [],
            "surviving_mutants": surviving_mutants or [],
            "iteration": iteration,
        }
        msg = Message(
            message_id=str(uuid.uuid4()),
            role=Role.user,
            parts=[Part(root=TextPart(text=json.dumps(payload)))],
            metadata={"skill_id": "mutation-critique"},
        )
        task = await self.send_protocol_message(msg)

        directive_dict: Optional[Dict[str, Any]] = None
        if task.artifacts:
            for art in task.artifacts:
                if art.parts:
                    for part in art.parts:
                        unwrapped = getattr(part, "root", part)
                        if isinstance(unwrapped, TextPart):
                            try:
                                directive_dict = json.loads(unwrapped.text)
                            except Exception:
                                pass
        return task, directive_dict
