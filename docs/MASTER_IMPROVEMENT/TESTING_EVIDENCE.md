# TestForge Testing Evidence Register

**Last Updated:** November 5, 2026  
**Baseline Test Count:** 740 passed, 0 failures, 501 warnings (378.26s)

---

## Empirical Verification Log

| Test Run ID | Target Suite / Command | Total Tests | Passed | Failed | Warnings | Duration | Exit Code | Purpose / Notes |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| **RUN-000** | `.venv-release/bin/python3 -m pytest tests/ -q` | 740 | 740 | 0 | 501 | 378.26s | 0 | Phase 7 Baseline Verification |
| **RUN-001** | `pytest tests/test_sandbox.py tests/test_sandbox_security_isolation.py -v` | 8 | 8 | 0 | 0 | 5.20s | 0 | Sandbox Security & Environment Isolation Verification (Cycle 1) |
| **RUN-002** | `pytest tests/test_boundary_and_property_intelligence.py tests/test_adk_generator.py -v` | 18 | 18 | 0 | 14 | 4.55s | 0 | Boundary Partitioning & Property-Based Test Synthesis (Cycle 2) |
| **RUN-003** | `pytest tests/test_quality_score_and_minimization.py tests/test_crew_critic.py tests/test_mutation_quality_critic_agent.py -v` | 24 | 24 | 0 | 130 | 4.19s | 0 | Multi-Dimensional TQS & Suite Deduplication Verification (Cycle 3) |
| **RUN-004** | `pytest tests/test_concurrency_and_reliability.py -v` | 3 | 3 | 0 | 11 | 15.70s | 0 | Concurrency, Job Cancellation, Multi-job Isolation & SQLite WAL Checkpoint Verification (Cycle 4) |
| **RUN-005** | `pytest tests/test_agent_wiretap_integrity.py tests/test_a2a_card_ui_and_endpoint.py tests/test_wiretap_frontend_topology.py -v` | 14 | 14 | 0 | 8 | 19.88s | 0 | Multi-Agent Wiretap 8-Agent Dynamic Grid & Supervisor Timeline (Cycle 5) |
| **RUN-006** | `pytest tests/test_mutator_caching_and_performance.py tests/test_mutator.py -v` | 8 | 8 | 0 | 0 | 0.11s | 0 | AST Mutant Compilation Caching & Performance Verification (Cycle 6) |
| **RUN-007** | `.venv-release/bin/python3 -m pytest tests/ -q` | 765 | 765 | 0 | 503 | 411.45s | 0 | Full Repository Master Regression Suite Verification |

*(Subsequent test runs will be appended chronologically)*
