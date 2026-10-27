# TestForge — Visible Copy Corrections & Claim Precision

**Audit Date:** 2026-10-27 01:16:30 IST  
**Reference:** Phase 5 — Independent Claim Verification  

---

## 1. Principles of Precision

In accordance with strict acceptance standards:
- Overbroad marketing statements must be replaced with accurate, verifiable descriptions of actual system boundaries and capabilities.
- Local deterministic fallback behavior must never be conflated with live multi-turn cloud LLM inference.
- Hardware optimizations and security guardrails must be documented with precise implementation details.

---

## 2. Claim Corrections Table

| Original Visible Claim | Location | Audit Finding | Corrected Precision Text | Implementation Source |
|---|---|---|---|---|
| "Fully secure sandbox" | UI Settings / Docs | Executed in local temporary directory subprocess with AST filtering and timeouts; does not provide microVM hardware isolation. | *"Isolated subprocess execution with AST-based pre-execution filters and process timeouts. This is not a hardened microVM."* | `testforge/security.py`, `testforge/sandbox.py` |
| "Zero false positives" | Hardening Lab | Clean-reference testing (`pass@1`) catches and quarantines invalid candidate tests before mutation testing begins. | *"Zero candidate test failures observed against unmutated reference code in evaluated benchmarks (failing tests quarantined)."* | `testforge/corpus/runner.py`, `testforge/orchestrator.py` |
| "Google ADK & CrewAI Fully Operational" | Wiretap / Settings | Dual-agent framework is implemented via local SDK abstractions with deterministic fallback when API keys are absent. | *"Google ADK and CrewAI SDK architectures implemented; local synthesis operational with external API enablement via configuration."* | `testforge/adk_generator.py`, `testforge/crew_critic.py` |
| "Real-time Progress" | Progress Bar | Progress reflects actual discrete lifecycle events (`TaskLifecycleState`) emitted by the backend FSM. | *"Progress dynamically updated from discrete backend state transitions and stage duration metrics."* | `testforge/state.py`, `server.py` |
| "100% Mutation Score" | Benchmark Summary | 100% is achieved on specific small fixtures (e.g. `discount.py` handwritten baseline); mean agentic reflection achieves 45% - 76%. | *"Per-fixture scores vary from 21% to 100%; aggregate pooled mutation score is explicitly distinguished from arithmetic mean."* | `benchmark_results.json`, `testforge/benchmarking.py` |
| "Apple Silicon Neural Engine Acceleration" | Footer | Platform detection configures thread pools and MPS/MLX optimizations when available. | *"Hardware profile detects Apple Silicon arm64, configuring 8 parallel CPU sandbox workers and Apple MPS/MLX acceleration."* | `testforge/accel.py` |
