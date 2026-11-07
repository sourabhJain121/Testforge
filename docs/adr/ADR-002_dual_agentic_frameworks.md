# ADR-002: Dual Agentic Frameworks (Google ADK + CrewAI via A2A Broker)

## Status
Accepted

## Context
Production agent systems frequently need to combine different framework strengths. Google Agent Development Kit (ADK) excels at low-level session management, native runners, structured memory services, and lifecycle security callbacks. Meanwhile, CrewAI provides specialized role-playing abstractions and task delegation ideal for adversarial evaluation. Running a single monolithic framework restricts architectural flexibility and limits evaluation of real-world multi-agent protocols.

## Decision
We implemented a **Dual-Framework Agentic Architecture**:
1. **Google ADK (`google-adk==1.14.1`)**: Powers the primary orchestration engine (`SupervisorAgent`, `TestPlanningAgent`, `TestGeneratorAgent`, `ReflectionRepairAgent`). Uses ADK native `Runner`, `BaseSessionService` (`DatabaseSessionService`), `MemoryService` (`InMemoryMemoryService`), and model/tool callbacks.
2. **CrewAI (`crewai==0.102.0`)**: Powers the `MutationQualityCriticAgent`, acting as an adversarial specialist assessing test quality and formulation of repair directives.
3. **Agent2Agent (A2A v0.3.0) Protocol Broker**: Provides standardized wire dispatch between the Google ADK orchestrator and the CrewAI critic. Supports both in-process performative routing and distributed cross-process execution over HTTP/stdio.

## Consequences

### Positive
- **Specialization**: Each framework is deployed where its design is strongest: ADK for deterministic pipeline execution, state machine transitions, and memory; CrewAI for persona-driven adversarial critique.
- **Protocol Compliance**: Directly satisfies coursework mandates for genuine multi-framework integration and official A2A wire protocol compliance.
- **Fail-safe Fallback**: If the remote CrewAI worker process fails or disconnects, the broker automatically falls back to an in-process critic without pipeline interruption.

### Negative / Trade-offs
- Managing dependencies across both `google-adk` and `crewai` requires careful version pinning to avoid conflicting transitive dependencies (e.g., Pydantic v2 constraints).

