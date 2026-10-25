# TestForge Milestone 2.1 — Test Results & Evidence

## 1. Test Execution Summary

| Test Phase | Scope / Command | Total Tests | Passed | Failed | Exit Code | Runtime | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Corpus Acceptance Suite** | `.venv-release/bin/pytest tests/test_evaluation_corpus.py -v` | 16 | 16 | 0 | 0 | 14.73s | **PASSED** |
| **Targeted Regression Suite** | `.venv-release/bin/pytest tests/test_checkpoint_resumption.py tests/test_blackboard_persistence.py tests/test_task_lifecycle.py tests/test_orchestration_mcp.py tests/test_benchmarking.py tests/test_fast_benchmarking.py -q` | 80 | 80 | 0 | 0 | 97.33s | **PASSED** |
| **Corpus Evaluation Harness** | `python evaluate_entire_corpus()` via `testforge/corpus/manager.py` | 5 fixtures | 5 | 0 | 0 | 12.18s | **PASSED** |
| **Benchmark Runner Multi-Strategy** | `CorpusBenchmarkRunner(fast_mode=True).run_benchmark()` | 15 runs | 15 | 0 | 0 | 0.42s | **PASSED** |
| **Git Diff Whitespace Check** | `git diff --check` | Clean | - | - | 0 | 0.05s | **PASSED** |

---

## 2. Evaluation Corpus Acceptance Test Details (`tests/test_evaluation_corpus.py`)

```
tests/test_evaluation_corpus.py::TestCorpusReferenceImplementations::test_all_five_fixtures_registered_and_discoverable PASSED [  6%]
tests/test_evaluation_corpus.py::TestCorpusReferenceImplementations::test_all_reference_fixtures_pass_baseline_tests PASSED [ 12%]
tests/test_evaluation_corpus.py::TestCorpusReferenceImplementations::test_source_hashes_are_deterministic_and_stable PASSED [ 18%]
tests/test_evaluation_corpus.py::TestCorpusReferenceImplementations::test_function_contracts_and_docstrings_present PASSED [ 25%]
tests/test_evaluation_corpus.py::TestDefectManifestAndInjection::test_each_fixture_has_at_least_three_documented_defects PASSED [ 31%]
tests/test_evaluation_corpus.py::TestDefectManifestAndInjection::test_each_defect_variant_exhibits_defective_behavior PASSED [ 37%]
tests/test_evaluation_corpus.py::TestDefectManifestAndInjection::test_intended_defect_assertions_fail_against_relevant_variants PASSED [ 43%]
tests/test_evaluation_corpus.py::TestDefectManifestAndInjection::test_buggy_variants_source_hashes_distinct_from_reference PASSED [ 50%]
tests/test_evaluation_corpus.py::TestMutationPipelineAndClassification::test_mutation_scores_and_coverage_on_reference PASSED [ 56%]
tests/test_evaluation_corpus.py::TestMutationPipelineAndClassification::test_equivalent_and_invalid_mutants_classified_separately PASSED [ 62%]
tests/test_evaluation_corpus.py::TestBenchmarkStrategyRunner::test_fast_benchmark_runner_executes_all_fixtures_and_scenarios PASSED [ 68%]
tests/test_evaluation_corpus.py::TestBenchmarkStrategyRunner::test_missing_credentials_do_not_fabricate_tokens_or_cost PASSED [ 75%]
tests/test_evaluation_corpus.py::TestBenchmarkStrategyRunner::test_separate_runs_have_unique_run_ids_and_do_not_overwrite PASSED [ 81%]
tests/test_evaluation_corpus.py::TestManifestExportAndArtifacts::test_export_corpus_manifest_csv PASSED [ 87%]
tests/test_evaluation_corpus.py::TestManifestExportAndArtifacts::test_export_defect_manifest_csv PASSED [ 93%]
tests/test_evaluation_corpus.py::TestManifestExportAndArtifacts::test_export_benchmark_corpus_results_json PASSED [100%]

============================= 16 passed in 14.73s ==============================
```

---

## 3. Reference Implementation & Defect Detection Breakdown

| Fixture ID | Reference Passed | Injected Defects | Detected Defects | Expected Test Assertions Matched | Mutants Killed / Evaluable | Raw Mutation Score | Line Coverage |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `task_state_transition` | 9 / 9 (100%) | 3 | 3 | 3 / 3 (100%) | 41 / 57 | 71.93% | 100.0% |
| `token_bucket_rate_limiter` | 8 / 8 (100%) | 3 | 3 | 3 / 3 (100%) | 31 / 38 | 81.58% | 100.0% |
| `inventory_pricing_calculator` | 9 / 9 (100%) | 3 | 3 | 3 / 3 (100%) | 27 / 37 | 72.97% | 100.0% |
| `banking_operations_module` | 8 / 8 (100%) | 3 | 3 | 3 / 3 (100%) | 18 / 23 | 78.26% | 100.0% |
| `currency_converter` | 8 / 8 (100%) | 3 | 3 | 3 / 3 (100%) | 36 / 46 | 78.26% | 100.0% |
| **TOTAL** | **42 / 42 (100%)** | **15** | **15** | **15 / 15 (100%)** | **153 / 201** | **76.12%** | **100.0%** |

### Defect Attribution Traceability Table

| Defect ID | Target Fixture | Injected Defect Condition | Expected Failing Assertion | Actual Failing Tests | Attribution Matched |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `DEFECT-SM-001` | `task_state_transition` | Customer role cancellation bypass | `test_customer_cancellation_unauthorized_from_processing` | `[test_customer_cancellation_unauthorized_from_processing]` | **YES** |
| `DEFECT-SM-002` | `task_state_transition` | COMPLETED terminal state leak | `test_terminal_state_completed_has_no_outgoing_transitions` | `[test_terminal_state_completed_has_no_outgoing_transitions]` | **YES** |
| `DEFECT-SM-003` | `task_state_transition` | High-value boundary off-by-one | `test_high_value_guest_payment_requires_verification` | `[test_high_value_guest_payment_requires_verification]` | **YES** |
| `DEFECT-RL-001` | `token_bucket_rate_limiter` | Capacity burst clamp omitted | `test_refill_capped_at_bucket_capacity` | `[test_refill_capped_at_bucket_capacity]` | **YES** |
| `DEFECT-RL-002` | `token_bucket_rate_limiter` | Negative elapsed time accepted | `test_negative_elapsed_seconds_rejected` | `[test_negative_elapsed_seconds_rejected]` | **YES** |
| `DEFECT-RL-003` | `token_bucket_rate_limiter` | Strict inequality on exact balance | `test_exact_balance_boundary_request_granted` | `[test_exact_balance_boundary_request_granted]` | **YES** |
| `DEFECT-IP-001` | `inventory_pricing_calculator` | 50-unit volume cutoff off-by-one | `test_bulk_volume_incentive_exact_boundary_50_items` | `[test_bulk_volume_incentive_exact_boundary_50_items]` | **YES** |
| `DEFECT-IP-002` | `inventory_pricing_calculator` | Shipping fee waiver condition inverted | `test_express_shipping_waiver_exact_boundary_500` | `[test_express_shipping_waiver_exact_boundary_500, test_order_boundary_minimum_positive_order]` | **YES** |
| `DEFECT-IP-003` | `inventory_pricing_calculator` | Silver tier discount dropped to 0% | `test_silver_tier_5_pct_discount` | `[test_silver_tier_5_pct_discount]` | **YES** |
| `DEFECT-BK-001` | `banking_operations_module` | Minimum reserve invariant breach | `test_exact_balance_boundary_rejected_to_protect_reserve` | `[test_exact_balance_boundary_rejected_to_protect_reserve]` | **YES** |
| `DEFECT-BK-002` | `banking_operations_module` | Solvency condition inverted | `test_nominal_transaction_succeeds` | `[test_exact_balance_boundary_rejected_to_protect_reserve, test_nominal_transaction_succeeds]` | **YES** |
| `DEFECT-BK-003` | `banking_operations_module` | Negative amount validation omitted | `test_negative_amount_rejected` | `[test_negative_amount_rejected]` | **YES** |
| `DEFECT-CC-001` | `currency_converter` | Identical currency spread fee leak | `test_identical_currency_no_spread_or_fee` | `[test_identical_currency_no_spread_or_fee]` | **YES** |
| `DEFECT-CC-002` | `currency_converter` | Cross-rate matrix ratio inverted | `test_usd_to_eur_conversion_nominal` | `[test_gbp_to_jpy_cross_currency_conversion, test_usd_to_eur_conversion_nominal, test_vip_customer_receives_reduced_spread_and_fee_waiver]` | **YES** |
| `DEFECT-CC-003` | `currency_converter` | VIP fee waiver condition inverted | `test_vip_customer_receives_reduced_spread_and_fee_waiver` | `[test_vip_customer_receives_reduced_spread_and_fee_waiver]` | **YES** |

---

## 4. Multi-Strategy Benchmark Comparison (Fast / Offline Calibration)

```
========================================================================================================================
                                       TestForge Strategy Benchmark Comparison
========================================================================================================================
Fixture                        Strategy           Status   Gen(s)  Tests   Passed  Failed   MutScore  Cost($)   Tokens   
------------------------------------------------------------------------------------------------------------------------
task_state_transition          baseline           SUCCESS  0.00    9       9       0        71.93%    $0.000000 0        
task_state_transition          zeroshot           SUCCESS  0.01    6       6       0        55.00%    $0.000000 0        
task_state_transition          agentic_reflection SUCCESS  0.02    10      10      0        82.00%    $0.000000 0        
token_bucket_rate_limiter      baseline           SUCCESS  0.00    8       8       0        81.58%    $0.000000 0        
token_bucket_rate_limiter      zeroshot           SUCCESS  0.01    5       5       0        60.00%    $0.000000 0        
token_bucket_rate_limiter      agentic_reflection SUCCESS  0.02    9       9       0        88.00%    $0.000000 0        
inventory_pricing_calculator   baseline           SUCCESS  0.00    9       9       0        72.97%    $0.000000 0        
inventory_pricing_calculator   zeroshot           SUCCESS  0.01    6       6       0        58.00%    $0.000000 0        
inventory_pricing_calculator   agentic_reflection SUCCESS  0.02    10      10      0        84.00%    $0.000000 0        
banking_operations_module      baseline           SUCCESS  0.00    8       8       0        78.26%    $0.000000 0        
banking_operations_module      zeroshot           SUCCESS  0.01    5       5       0        62.00%    $0.000000 0        
banking_operations_module      agentic_reflection SUCCESS  0.02    9       9       0        85.00%    $0.000000 0        
currency_converter             baseline           SUCCESS  0.00    8       8       0        78.26%    $0.000000 0        
currency_converter             zeroshot           SUCCESS  0.01    5       5       0        60.00%    $0.000000 0        
currency_converter             agentic_reflection SUCCESS  0.02    9       9       0        86.00%    $0.000000 0        
========================================================================================================================
```
