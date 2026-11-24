# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Users
Software engineers, QA automation leads, empirical software researchers, and security auditors who generate, evaluate, and harden Python test suites against mutation faults.

## Product Purpose
TestForge is an autonomous agentic test hardening platform that exposes latent logic faults in software by coupling AST mutation analysis with multi-agent test synthesis (Google ADK Generator + CrewAI Critic) and set-cover suite minimization.

## Positioning
Conventional coverage tools only check whether lines executed, ignoring weak or missing assertions. TestForge executes active semantic mutation to stress-test assertions, eliminating surviving mutants through closed-loop reflection while bounding compute costs via local Ollama and TokenHarbor cloud models.

## Operating Context
- Web application running on FastAPI backend and vanilla JavaScript/CSS dashboard.
- Dual execution environments: Local Apple Silicon / Linux workstations with local Ollama (`codellama:7b`), and containerized serverless cloud (Azure Container Apps, Google Cloud Run) utilizing TokenHarbor (`deepseek-v4.1-flash:free`).
- Live WebSocket event stream delivering real-time telemetry, agent thoughts, mutant kill statuses, and circuit-breaker alerts.

## Capabilities and Constraints
- Autonomous test generation with AST boundary synthesis and prompt-injection guardrails.
- High-throughput AST mutation engine supporting AOR, LCR, ROR, CRP, and SBR mutation operators.
- Greedy set-cover test suite minimizer with interactive kill-matrix heatmap.
- FastMCP diagnostic tool inspector and Agent-to-Agent (A2A) schema discovery.
- Strict $0 offline capability via local Ollama and AST synthesizer fallback.

## Brand Commitments
- Name: TestForge
- Aesthetic: Precision developer laboratory — calm, dark, high-contrast, scan-friendly, devoid of generic AI tropes (no neon gradients, no glow halos, no floating decorative grids).

## Evidence on Hand
- Real mutation benchmarks across standard algorithms (`samples/discount.py`, `samples/lru_cache.py`, `samples/mergesort.py`, `samples/run_length.py`).
- Precomputed set-cover minimization benchmarks and real-time execution telemetry.

## Product Principles
1. **Empirical Verification:** Every assertion, mutant kill, and token metric is grounded in observable code execution.
2. **Resilience & Continuity:** Guaranteed multi-tier fallback (Cloud LLM -> Local Ollama -> Deterministic AST Synthesizer) prevents deadlocks.
3. **Calm Precision:** Interface designed for high-density information architecture without decorative distraction or sensory fatigue.
