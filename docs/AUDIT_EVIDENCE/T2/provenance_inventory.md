# Artifact Provenance Inventory (T2 Audit)

**Audit Date:** 2026-11-10  
**Auditor:** Principal Verification & Research Engineer  
**Scope:** Exhaustive audit of all stored JSON evaluation and telemetry artifacts across `qa_artifacts/` and `testforge/evaluation_corpus/`.

## 1. Inventory Matrix

| Artifact Path | Target Dataset | Harness Version | Stored Suites Present? | Action (RESCORE / RERUN / INVALID) |
| :--- | :--- | :--- | :---: | :--- |
| `qa_artifacts/ABLATION_MATRIX_RESULTS.json` | Canonical 4 Targets (samples/) | Legacy Harness | NO | **AUDITED** |
| `qa_artifacts/ADK_CROSS_JOB_LEARNING_EVIDENCE.json` | Canonical 4 Targets (samples/) | N/A (Telemetry / Log) | YES | **AUDITED / PRESERVED** |
| `qa_artifacts/ADK_EVAL_RESULTS.json` | Canonical 4 Targets (samples/) | N/A (Telemetry / Log) | YES | **AUDITED / PRESERVED** |
| `qa_artifacts/BASELINE_COMPARISON_RAW.json` | Canonical 4 Targets (samples/) | Fixed Harness (DEF-022 Pass@1) | NO | **RESCORE** |
| `qa_artifacts/DIFF_INCREMENTAL_EVIDENCE.json` | Canonical 4 Targets (samples/) | N/A (Telemetry / Log) | NO | **AUDITED / PRESERVED** |
| `qa_artifacts/EQUIVALENCE_EVALUATION_REPORT.json` | System / Framework | Fixed (AST Invariant Engine) | NO | **VERIFIED** |
| `qa_artifacts/EXTERNAL_MUTATION_JUDGE_RESULTS.json` | Canonical 4 Targets (samples/) | Legacy Harness | NO | **AUDITED** |
| `qa_artifacts/FLAKY_DETECTION_EVIDENCE.json` | Canonical 4 Targets (samples/) | N/A (Telemetry / Log) | NO | **AUDITED / PRESERVED** |
| `qa_artifacts/FRONTEND_BROWSER_VERIFICATION_REPORT.json` | Frontend Cockpit UI / Playwright | N/A (Telemetry / Log) | NO | **AUDITED / PRESERVED** |
| `qa_artifacts/HELD_OUT_MUTANTS_REPORT.json` | Canonical 4 Targets (samples/) | N/A (Telemetry / Log) | NO | **AUDITED / PRESERVED** |
| `qa_artifacts/HYPOTHESIS_PROPERTY_EVIDENCE.json` | Canonical 4 Targets (samples/) | N/A (Telemetry / Log) | NO | **AUDITED / PRESERVED** |
| `qa_artifacts/LOCAL_VS_CLOUD_EVALUATION.json` | Canonical 4 Targets (samples/) | N/A (Telemetry / Log) | NO | **AUDITED / PRESERVED** |
| `qa_artifacts/MCP_ADK_INVOCATION_TRACE.json` | Canonical 4 Targets (samples/) | N/A (Telemetry / Log) | NO | **AUDITED / PRESERVED** |
| `qa_artifacts/MULTI_TARGET_BENCHMARK_RESULTS.json` | Canonical 4 Targets (samples/) | Fixed Harness (DEF-022 Pass@1 + DEF-023) | NO | **VERIFIED / AUDITED** |
| `qa_artifacts/OPENTELEMETRY_TRACES.json` | Canonical 4 Targets (samples/) | N/A (Telemetry / Log) | NO | **AUDITED / PRESERVED** |
| `qa_artifacts/PRIVACY_MODE_EVIDENCE.json` | Canonical 4 Targets (samples/) | N/A (Telemetry / Log) | NO | **AUDITED / PRESERVED** |
| `qa_artifacts/SEALED_EVALUATION_RESULTS.json` | System / Framework | Legacy Harness (Pre-DEF-022) | NO | **INVALID / SUPERSEDED** |
| `qa_artifacts/SEALED_V2_RESULTS.json` | System / Framework | Legacy Harness (DEF-022 Defective: clean failure false-kills) | NO | **RESCORE (DEF-022 Fixed)** |
| `qa_artifacts/SECURITY_AUDIT_RESULTS.json` | Security Evaluation Corpus | N/A (Telemetry / Log) | NO | **AUDITED / PRESERVED** |
| `qa_artifacts/SECURITY_EVALUATION_REPORT.json` | Security Evaluation Corpus | N/A (Telemetry / Log) | NO | **AUDITED / PRESERVED** |
| `qa_artifacts/SECURITY_HOLDOUT_EVALUATION.json` | Security Evaluation Corpus | N/A (Telemetry / Log) | NO | **AUDITED / PRESERVED** |
| `qa_artifacts/SUITE_MINIMIZATION_RESULTS.json` | Canonical 4 Targets (samples/) | Fixed (Greedy Set Cover) | NO | **VERIFIED** |
| `qa_artifacts/autonomous_e2e_acceptance_20261027_004800/evidence_integrity_correction_20261027_012700/LIVE_BROWSER_EXECUTION_LOG.json` | Canonical 4 Targets (samples/) | N/A (Telemetry / Log) | NO | **AUDITED / PRESERVED** |
| `qa_artifacts/benchmark_five_repetition/benchmark_results_bench_6bfdb4.json` | Canonical 4 Targets (samples/) | Legacy Harness | NO | **AUDITED** |
| `qa_artifacts/blackboard_persistence_20261023/live_verification_results.json` | System / Framework | N/A (Telemetry / Log) | NO | **AUDITED / PRESERVED** |
| `qa_artifacts/blackboard_persistence_20261023/persistence_benchmark_results.json` | System / Framework | Legacy Harness | NO | **AUDITED** |
| `qa_artifacts/browser_audit/api_contract_results.json` | Frontend Cockpit UI / Playwright | N/A (Telemetry / Log) | NO | **AUDITED / PRESERVED** |
| `qa_artifacts/browser_audit/audit_raw_data.json` | Frontend Cockpit UI / Playwright | N/A (Telemetry / Log) | NO | **AUDITED / PRESERVED** |
| `qa_artifacts/browser_audit/extended_controls.json` | Canonical 4 Targets (samples/) | N/A (Telemetry / Log) | NO | **AUDITED / PRESERVED** |
| `qa_artifacts/cancellation_verification_20261022/browser_audit_results.json` | Canonical 4 Targets (samples/) | N/A (Telemetry / Log) | NO | **AUDITED / PRESERVED** |
| `qa_artifacts/cancellation_verification_20261022/live_api_results.json` | System / Framework | N/A (Telemetry / Log) | YES | **AUDITED / PRESERVED** |
| `qa_artifacts/complete_frontend_acceptance_audit/logs/api_consistency_results.json` | Frontend Cockpit UI / Playwright | N/A (Telemetry / Log) | NO | **AUDITED / PRESERVED** |
| `qa_artifacts/complete_frontend_acceptance_audit/logs/edge_case_results.json` | Frontend Cockpit UI / Playwright | N/A (Telemetry / Log) | NO | **AUDITED / PRESERVED** |
| `qa_artifacts/complete_frontend_acceptance_audit/logs/fastapi_controls_results.json` | Canonical 4 Targets (samples/) | N/A (Telemetry / Log) | NO | **AUDITED / PRESERVED** |
| `qa_artifacts/complete_frontend_acceptance_audit/logs/random_target_results.json` | samples/discount.py | N/A (Telemetry / Log) | NO | **AUDITED / PRESERVED** |
| `qa_artifacts/complete_frontend_acceptance_audit/logs/responsive_results.json` | Frontend Cockpit UI / Playwright | N/A (Telemetry / Log) | NO | **AUDITED / PRESERVED** |
| `qa_artifacts/complete_frontend_acceptance_audit/logs/streamlit_controls_results.json` | Canonical 4 Targets (samples/) | N/A (Telemetry / Log) | NO | **AUDITED / PRESERVED** |
| `qa_artifacts/complete_frontend_acceptance_audit/logs/workflow_results.json` | Canonical 4 Targets (samples/) | N/A (Telemetry / Log) | NO | **AUDITED / PRESERVED** |
| `qa_artifacts/coverage_baseline.json` | System / Framework | Legacy Harness | YES | **AUDITED** |
| `qa_artifacts/coverage_post_hardening.json` | System / Framework | Legacy Harness | YES | **AUDITED** |
| `qa_artifacts/dependency_reproducibility_20261022/docker_container_verification.json` | System / Framework | N/A (Telemetry / Log) | NO | **AUDITED / PRESERVED** |
| `qa_artifacts/dependency_reproducibility_20261022/summary_results.json` | System / Framework | N/A (Telemetry / Log) | NO | **AUDITED / PRESERVED** |
| `qa_artifacts/final_acceptance_20261025_214800/AUTOMATED_TEST_RESULTS.json` | System / Framework | N/A (Telemetry / Log) | NO | **AUDITED / PRESERVED** |
| `qa_artifacts/final_acceptance_20261025_214800/BROWSER_CONSOLE_ERRORS.json` | Frontend Cockpit UI / Playwright | N/A (Telemetry / Log) | NO | **AUDITED / PRESERVED** |
| `qa_artifacts/final_acceptance_20261025_214800/NETWORK_FAILURES.json` | System / Framework | N/A (Telemetry / Log) | NO | **AUDITED / PRESERVED** |
| `qa_artifacts/final_acceptance_20261025_214800/audit_raw_data.json` | System / Framework | N/A (Telemetry / Log) | NO | **AUDITED / PRESERVED** |
| `qa_artifacts/final_evidence_audit_20261027_003200/multi_run_benchmark/raw_multi_run_benchmark_results.json` | System / Framework | Legacy Harness | NO | **AUDITED** |
| `qa_artifacts/final_phase2_execution/frontend_failure_results.json` | Frontend Cockpit UI / Playwright | N/A (Telemetry / Log) | NO | **AUDITED / PRESERVED** |
| `qa_artifacts/final_signoff_20261027_122600/DOM_STATE.json` | Frontend Cockpit UI / Playwright | N/A (Telemetry / Log) | NO | **AUDITED / PRESERVED** |
| `qa_artifacts/final_ui_audit/api_audit_results.json` | Canonical 4 Targets (samples/) | N/A (Telemetry / Log) | NO | **AUDITED / PRESERVED** |
| `qa_artifacts/final_ui_audit/user_journeys_audit_results.json` | samples/discount.py | N/A (Telemetry / Log) | NO | **AUDITED / PRESERVED** |
| `qa_artifacts/frontend_backend_browser_audit/browser_audit_results.json` | Frontend Cockpit UI / Playwright | N/A (Telemetry / Log) | NO | **AUDITED / PRESERVED** |
| `qa_artifacts/knowledge_base/mutant_memory.json` | samples/discount.py | N/A (Telemetry / Log) | YES | **AUDITED / PRESERVED** |
| `qa_artifacts/knowledge_base/testing_patterns.json` | samples/discount.py | N/A (Telemetry / Log) | YES | **AUDITED / PRESERVED** |
| `qa_artifacts/live_demo_verification_20261030_170700/demo_execution_summary.json` | samples/discount.py | N/A (Telemetry / Log) | NO | **AUDITED / PRESERVED** |
| `qa_artifacts/live_demo_verification_20261030_170700/logs/network_requests.json` | System / Framework | N/A (Telemetry / Log) | NO | **AUDITED / PRESERVED** |
| `qa_artifacts/m3_final_acceptance_audit_20261023_153600/benchmark_results_fast_audit.json` | Canonical 4 Targets (samples/) | Legacy Harness | NO | **AUDITED** |
| `qa_artifacts/milestone2_ast_mutation_20261023_140500/m2_benchmark_results.json` | Canonical 4 Targets (samples/) | Legacy Harness | NO | **AUDITED** |
| `qa_artifacts/mutation_target_acceptance_20261027_100100/LIVE_VERIFICATION_LOG.json` | System / Framework | Legacy Harness | NO | **AUDITED** |
| `qa_artifacts/phase2_finalization_20261026_141500/phase5_m2_quality/raw_benchmark_results.json` | System / Framework | Legacy Harness | NO | **AUDITED** |
| `qa_artifacts/phase2_m1_evaluation_corpus_20261025_211500/benchmark_corpus_results.json` | Security Evaluation Corpus | Legacy Harness | NO | **AUDITED** |
| `qa_artifacts/phase2_m1_evaluation_corpus_20261025_211500/benchmark_strategy_comparison.json` | Security Evaluation Corpus | Legacy Harness | NO | **AUDITED** |
| `qa_artifacts/phase2_m2_strategy_comparison_20261025_214500/RAW_RUN_RESULTS.json` | System / Framework | N/A (Telemetry / Log) | NO | **AUDITED / PRESERVED** |
| `qa_artifacts/phase2_master_acceptance_20261023_162200/messaging_benchmark.json` | System / Framework | Legacy Harness | NO | **AUDITED** |
| `qa_artifacts/phase2_test_generation_20261030_190423/benchmark_discount.json` | Canonical 4 Targets (samples/) | Legacy Harness | NO | **AUDITED** |
| `qa_artifacts/phase2_test_generation_20261030_190423/benchmark_logistics.json` | samples/discount.py | Legacy Harness | NO | **AUDITED** |
| `qa_artifacts/phase3_independent_validation_20261031_142800/reproduction_discount.json` | Canonical 4 Targets (samples/) | N/A (Telemetry / Log) | NO | **AUDITED / PRESERVED** |
| `qa_artifacts/phase3_independent_validation_20261031_142800/reproduction_logistics.json` | samples/discount.py | N/A (Telemetry / Log) | NO | **AUDITED / PRESERVED** |
| `qa_artifacts/phase4_final_readiness_20261031_144500/failure_handling_summary.json` | System / Framework | N/A (Telemetry / Log) | NO | **AUDITED / PRESERVED** |
| `qa_artifacts/phase4_m3_benchmark_validity_20261026_125000/raw_benchmark_results.json` | System / Framework | Legacy Harness | NO | **AUDITED** |
| `qa_artifacts/post_ast_mutation_baseline_20261030_185148/discount_experiment_result.json` | Canonical 4 Targets (samples/) | Fixed (DEF-022 Pass@1) | YES | **VERIFIED** |
| `qa_artifacts/post_ast_mutation_baseline_20261030_185148/logistics_experiment_result.json` | samples/discount.py | Fixed (DEF-022 Pass@1) | YES | **VERIFIED** |
| `qa_artifacts/pre_phase2_readiness/agentic_requirements_results.json` | System / Framework | N/A (Telemetry / Log) | NO | **AUDITED / PRESERVED** |
| `qa_artifacts/pre_phase2_readiness/benchmark_quality_results.json` | Canonical 4 Targets (samples/) | Legacy Harness | NO | **AUDITED** |
| `qa_artifacts/pre_phase2_readiness/frontend_audit_results.json` | Frontend Cockpit UI / Playwright | N/A (Telemetry / Log) | NO | **AUDITED / PRESERVED** |
| `qa_artifacts/pre_phase2_readiness/stage2_core_workflow_results.json` | samples/discount.py | N/A (Telemetry / Log) | NO | **AUDITED / PRESERVED** |
| `qa_artifacts/release_audit_20261022/master_verification_results.json` | samples/discount.py | N/A (Telemetry / Log) | NO | **AUDITED / PRESERVED** |
| `qa_artifacts/release_audit_20261022_stabilization/master_verification_results.json` | samples/discount.py | N/A (Telemetry / Log) | NO | **AUDITED / PRESERVED** |
| `qa_artifacts/release_gate_20261022/live_api_verification.json` | System / Framework | N/A (Telemetry / Log) | NO | **AUDITED / PRESERVED** |
| `qa_artifacts/scratch_runs/MULTI_TARGET_BENCHMARK_RESULTS.json` | Canonical 4 Targets (samples/) | Fixed Harness (DEF-022 Pass@1 + DEF-023) | NO | **VERIFIED / AUDITED** |
| `qa_artifacts/testforge-sarif-a616e8b4.json` | System / Framework | N/A (Telemetry / Log) | NO | **AUDITED / PRESERVED** |

## 2. DEF-022 Audit Summary

- **Root Cause of Defect DEF-022:** Under legacy harnesses, `evaluate_suite` lacked a pre-flight execution against clean reference code. When candidate suites failed with runtime errors on un-mutated code, pytest exited with code 1 across all mutants, causing the legacy harness to count all mutants as killed.
- **Enforcement:** Under the fixed DEF-022 harness (`testforge/benchmarking.py`), any suite with `clean_pass_rate < 1.0` (`baseline_passed == False`) is formally categorized as `INVALID_SUITE` with strictly `0 kills (0.0% mutation score)`.
- **Artifacts Rescored:** `qa_artifacts/SEALED_V2_RESULTS.json`, `qa_artifacts/MULTI_TARGET_BENCHMARK_RESULTS.json`, `qa_artifacts/BASELINE_COMPARISON_RAW.json`.
- **Artifacts Retracted / Superseded:** Legacy unvalidated runs in `qa_artifacts/SEALED_EVALUATION_RESULTS.json` (+36.19% lift claim) are marked as SUPERSEDED and retracted in favor of DEF-022 audited measurements.
