# 05 — Full Suite Regression Results

**Audit & Fix Timestamp:** `2026-10-30T18:45:36+05:30`  
**Execution Environment:** `/Users/sourabh/TestForge/.venv-release/bin/python` (Python 3.13.18)  
**Test Framework:** `pytest-9.1.1` | `pluggy-1.7.0` | `cov-7.1.0`

---

## 1. Regression Execution Summary

- **Exact Command:**
  ```bash
  .venv-release/bin/python -m pytest tests/ -q
  ```
- **Exit Code:** `0` (Success)
- **Total Tests Collected:** `542`
- **Passed Tests:** `542` (**100.0%**)
- **Failed Tests:** `0` (**0.0%**)
- **Skipped Tests:** `0`
- **Warnings:** `346` (upstream CrewAI deprecation warnings and Google Cloud Storage compatibility notices)
- **Total Execution Duration:** `354.81s` (5 minutes 54 seconds)

---

## 2. Comparison Across Recent Audit Cycles

| Dimension | Previous State (`20261030_181220`) | Current State (`20261030_184536`) | Delta / Improvement |
| :--- | :--- | :--- | :--- |
| **Total Tests** | 533 | **542** | +9 new AST regression tests |
| **Passed Tests** | 532 | **542** | **+10 passed tests** |
| **Failed Tests** | 1 (`test_hardening_pipeline_on_models`) | **0** | **-1 failure (Eliminated)** |
| **Exit Code** | `1` | **`0`** | **Full Regression Restored** |
| **Success Rate** | 99.81% | **100.00%** | **Perfect Pass Rate** |

---

## 3. Verified Test Modules (Complete Catalog)

All test suites across the repository passed cleanly:
1. `tests/test_ast_scope_extraction.py` (9/9 passed)
2. `tests/test_mode_c_ingestion.py` (8/8 passed, including `test_hardening_pipeline_on_models`)
3. `tests/test_post_demo_defect_fixes.py` (10/10 passed)
4. `tests/test_a2a.py` & `tests/test_a2a_protocol.py` (Passed)
5. `tests/test_a2a_card_ui_and_endpoint.py` (Passed)
6. `tests/test_adk_generator.py` (Passed)
7. `tests/test_adversarial_failure_injection.py` (Passed)
8. `tests/test_agentic_pipeline.py` (Passed)
9. `tests/test_ast_mutation_m2.py` (Passed)
10. `tests/test_benchmarking.py` & `tests/test_fast_benchmarking.py` (Passed)
11. `tests/test_blackboard.py` & `tests/test_blackboard_persistence.py` (Passed)
12. `tests/test_blast_and_adk.py` (Passed)
13. `tests/test_callbacks.py` (Passed)
14. `tests/test_cancellation.py` (Passed)
15. `tests/test_checkpoint_api_diff.py`, `test_checkpoint_diff.py`, `test_checkpoint_resumption.py` (Passed)
16. `tests/test_classifier.py` (Passed)
17. `tests/test_crew_critic.py` (Passed)
18. `tests/test_deployment.py` (Passed)
19. `tests/test_equivalent_mutants.py` (Passed)
20. `tests/test_evaluation_corpus.py` (Passed)
21. `tests/test_ingestion_and_llm.py` (Passed)
22. `tests/test_mcp.py`, `test_mcp_network_security.py`, `test_mcp_status_endpoint.py` (Passed)
23. `tests/test_messaging_benchmark.py` (Passed)
24. `tests/test_mutation_guided_repair.py`, `test_mutation_integration_m2.py`, `test_mutation_scores.py`, `test_mutator.py` (Passed)
25. `tests/test_network_security.py` (Passed)
26. `tests/test_observability.py` (Passed)
27. `tests/test_orchestration_mcp.py` (Passed)
28. `tests/test_prompt_injection_defense.py` (Passed)
29. `tests/test_sandbox.py` (Passed)
30. `tests/test_security.py` (Passed)
31. `tests/test_strategy_comparison.py` (Passed)
32. `tests/test_task_lifecycle.py` (Passed)
33. `tests/test_teacher_review_improvements.py` (Passed)
34. `tests/test_websocket_streaming.py` (Passed)

