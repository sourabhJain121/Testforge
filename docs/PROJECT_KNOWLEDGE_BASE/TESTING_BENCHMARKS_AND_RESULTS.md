# TESTFORGE — TESTING, BENCHMARKS & EMPIRICAL RESULTS
## Comprehensive Regression Results, Benchmark Metrics, Mutation Score Jumps & Suite Topology

**Document Version:** 2.0.0  
**Target Audience:** Evaluators, Quality Engineers, Benchmark Researchers  
**Authoritative Location:** `docs/PROJECT_KNOWLEDGE_BASE/TESTING_BENCHMARKS_AND_RESULTS.md`

---

## 1. TEST SUITE TOPOLOGY & REGRESSION EXECUTION

The TestForge test repository comprises **43 test files** containing **523 tests** testing unit logic, multi-agent interactions, external protocols, security guardrails, and SQLite persistence:

```
================================================================================
523 passed, 345 warnings in 351.31s (0:05:51)
Execution Environment: macOS Darwin 24.3.0 (arm64 Apple Silicon)
Python Version: Python 3.13.18 (.venv-release)
Exit Code: 0 (100.0% Pass Rate)
================================================================================
```

### Breakdown of the 523 Tests by Domain

| Category / Domain | Primary Test Files | Count | Status | Notes |
| :--- | :--- | :---: | :---: | :--- |
| **Security & Guardrails** | `test_network_security.py`, `test_mcp_network_security.py`, `test_prompt_injection_defense.py`, `test_security.py` | 92 | **PASSED** | Socket interception, SSRF defense, prompt framing, AST import blacklists. |
| **Pipeline & Multi-Agent** | `test_agentic_pipeline.py`, `test_crew_critic.py`, `test_adk_generator.py`, `test_task_lifecycle.py` | 56 | **PASSED** | End-to-end orchestration, CrewAI Critic tasks, Google ADK tool registries. |
| **Blackboard & State** | `test_blackboard.py`, `test_blackboard_persistence.py`, `test_checkpoint_resumption.py`, `test_checkpoint_diff.py` | 58 | **PASSED** | 5-space state transitions, SQLite persistence, rollback, diffing. |
| **Mutation Engine** | `test_mutator.py`, `test_ast_mutation_m2.py`, `test_equivalent_mutants.py`, `test_mutation_scores.py` | 64 | **PASSED** | First-order AST transformations, operator replacement, equivalence heuristics. |
| **Protocols (MCP & A2A)** | `test_mcp.py`, `test_mcp_status_endpoint.py`, `test_orchestration_mcp.py`, `test_a2a.py`, `test_a2a_protocol.py` | 42 | **PASSED** | FastMCP filesystem & GitHub servers, Linux Foundation A2A v0.3.0 card. |
| **Test Quality & Repair** | `test_mutation_guided_repair.py`, `test_mode_c_ingestion.py` | 41 | **PASSED** | Granular scenario synthesis, class method handling, multi-file sequential ingestion. |
| **API & Server Control** | `test_server.py` equivalents, `test_cancellation.py`, `test_websocket_streaming.py` | 45 | **PASSED** | REST endpoints, WebSocket streaming, cooperative job cancellation. |
| **Benchmarking & Corpus** | `test_benchmarking.py`, `test_fast_benchmarking.py`, `test_evaluation_corpus.py` | 42 | **PASSED** | Baseline evaluation corpus and metric consistency. |
| **Sandbox & System** | `test_sandbox.py`, `test_classifier.py`, `test_observability.py`, `test_deployment.py` | 83 | **PASSED** | Subprocess execution bounds, telemetry logger, Docker deployment sanity. |
| **Total** | **43 Test Modules** | **523** | **PASSED** | **100% Pass Rate** |

---

## 2. BENCHMARK SUITE RESULTS ACROSS ALL TARGETS

TestForge has been evaluated against six standard benchmark targets located in `samples/`:

| Target Benchmark | Physical Lines | Callables | Baseline Score | Hardened Score | Score Jump ($\Delta$) | Tests Synthesized | Test Pass Rate |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `samples/banking.py` | 55 | 3 | 0.0% | **52.2%** | **+52.2%** | 3 | **100%** |
| `samples/discount.py` | 42 | 2 | 0.0% | **63.2%** | **+63.2%** | 4 | **100%** |
| `samples/currency_converter.py` | 48 | 2 | 0.0% | **64.0%** | **+64.0%** | 4 | **100%** |
| `samples/inventory_pricing.py` | 60 | 4 | 0.0% | **60.0%** | **+60.0%** | 3 | **100%** |
| `samples/rate_limiter.py` | 50 | 2 | 0.0% | **28.0%** | **+28.0%** | 2 | **100%** |
| `samples/logistics_engine.py` | 240 | 6 | 0.0% | **52.0%** | **+52.0%** | 18 | **100%** |

### Benchmark Analysis & Findings:
1. **Business Logic & Pricing (`discount.py`, `currency_converter.py`):** Achieved highest mutation scores (63.2% and 64.0%) because discrete numerical thresholds (e.g. `order_amount >= 100.0`) are directly addressed by boundary scenario synthesis.
2. **Stateful Multi-Class Engine (`logistics_engine.py`):** 240-line real-world module featuring `ShippingTier` enums and a stateful `WarehouseInventory` class. Baseline test suite killed 0 mutants. TestForge synthesized 18 granular tests covering class instantiations, inventory reservations, restocking, and dispatch eligibility, killing 13 of 25 sampled mutants (**+52.0% jump**).
3. **Temporal Logic (`rate_limiter.py`):** Achieved 28.0% mutation score. Time-dependent code (token bucket algorithms depending on `time.time()`) requires temporal mocks; mutants altering sliding window math survived unless precise sleep intervals were simulated.

---

## 3. HISTORICAL VS. FINAL VERIFIED METRICS

To maintain intellectual honesty, the following table clarifies historical intermediate results vs. the final verified numbers:

| Metric | Historical Interim (Oct 22–27) | Final Verified State (Oct 30) | Explanation |
| :--- | :---: | :---: | :--- |
| **Supported Frontends** | Dual (FastAPI 8000 + Streamlit 8501) | **Single FastAPI (Port 8000)** | Streamlit permanently disabled to resolve state fragmentation. |
| **Test Suite Pass Count** | 482 passed | **523 passed** | Expanded security and regression tests. |
| **Generator Synthesis** | Monolithic functions / hollow stubs | **Granular scenario functions** | Fixed `try...except: pass` stubs that killed 0% mutants on classes. |
| **Logistics Engine Score** | 0.0% | **52.0%** | Added class method detection (`is_method`) and domain modeling. |
| **Active Job Cancellation** | Intermittent UI polling desync | **100% Cooperative CancellationToken** | Verified across 8 automated failure tests. |

