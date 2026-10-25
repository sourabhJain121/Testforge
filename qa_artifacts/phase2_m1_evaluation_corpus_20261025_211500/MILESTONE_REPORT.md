# TestForge Phase 2 — Milestone 2.1 Report
## Realistic Defect Evaluation Corpus and Reproducible Test-Quality Benchmark (GAP-04)

**Milestone Identifier:** `phase2_m1_evaluation_corpus_20261025_211500`  
**Execution Date:** October 25, 2026  
**Repository:** `/Users/sourabh/TestForge`  
**Target Gap:** GAP-04 (Realistic Defect Evaluation Corpus & Reproducible Benchmark Harness)  
**Status:** **COMPLETE & VERIFIED**

---

## 1. Executive Summary

Milestone 2.1 resolves **GAP-04** by building a deterministic, offline, and reproducible defect evaluation corpus consisting of five realistic software modules spanning distinct engineering domains. Each fixture is accompanied by formal function contracts, immutable cryptographic SHA-256 source fingerprinting, 100% baseline unit test suites, and three controlled defect variants (15 total defects). 

In addition, the milestone upgrades TestForge's benchmark harness to evaluate test generation strategies (`baseline`, `zeroshot`, and `agentic_reflection`) under identical conditions, providing precise defect attribution, rigorous AST mutation score accounting (distinguishing raw vs adjusted mutation scores and invalid mutants), and strict metric integrity (disallowing fabricated tokens or costs).

All 16 acceptance tests in `tests/test_evaluation_corpus.py` and 80 targeted regression tests in existing suites passed with zero failures.

---

## 2. Evaluation Corpus Architecture

The corpus contains five isolated, deterministic Python fixtures located in `testforge/corpus/fixtures/` and mirrored in `samples/`:

| Fixture ID | Domain | Module Path | Source SHA-256 | Tests | Defects |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `task_state_transition` | State Machine / RBAC | `samples/state_machine.py` | `60cdd1dc4281bfbb126831f88d4e8faa99836dcd4caa13daaec563af2ac4140a` | 9 | 3 |
| `token_bucket_rate_limiter` | Rate Limiter / Traffic | `samples/rate_limiter.py` | `526aeedc9eaa81dac8e7434ef763c153b3ffee47058036e1f4a27e86f665c945` | 8 | 3 |
| `inventory_pricing_calculator` | Commercial Pricing | `samples/inventory_pricing.py` | `2f1d24d285d360d04787878996270eae024e57f92249e0c2721ab8c693384497` | 9 | 3 |
| `banking_operations_module` | Banking Ledger | `samples/banking.py` | `392c0db3bf364c9d1d2f0efa9f4323e070308b03bbfe02a0161f722690ccc728` | 8 | 3 |
| `currency_converter` | Offline FX Triangulation | `samples/currency_converter.py` | `323534758ae93a42c4a7702a5ff7fb7c6837ad08e6955dadd72dec834a953cde` | 8 | 3 |

### Deterministic Integrity
- Reference code in `testforge/corpus/fixtures/` and `samples/` have identical SHA-256 hashes.
- All five fixtures run purely in-memory with zero network or external API dependencies (including `currency_converter` which uses a deterministic internal cross-rate matrix).
- Each fixture provides full docstrings, typed signatures, and explicit precondition/postcondition contracts.

---

## 3. Controlled Defect Variants & Precise Failure Attribution

Fifteen defect variants were created and verified across the five fixtures. Each defect variant exhibits a distinct SHA-256 hash and fails the designated assertion in the baseline test suite:

```
Defect Verification Matrix:
- DEFECT-SM-001 (RBAC Cancellation Bypass): Caught by test_customer_cancellation_unauthorized_from_processing
- DEFECT-SM-002 (Terminal State Leak): Caught by test_terminal_state_completed_has_no_outgoing_transitions
- DEFECT-SM-003 (High-Value Boundary Off-By-One): Caught by test_high_value_guest_payment_requires_verification
- DEFECT-RL-001 (Uncapped Capacity Accumulation): Caught by test_refill_capped_at_bucket_capacity
- DEFECT-RL-002 (Negative Elapsed Time Blindness): Caught by test_negative_elapsed_seconds_rejected
- DEFECT-RL-003 (Exact Balance Starvation > vs >=): Caught by test_exact_balance_boundary_request_granted
- DEFECT-IP-001 (50-Unit Bulk Cutoff Off-By-One): Caught by test_bulk_volume_incentive_exact_boundary_50_items
- DEFECT-IP-002 (Express Shipping Waiver Inversion): Caught by test_express_shipping_waiver_exact_boundary_500
- DEFECT-IP-003 (Silver Tier Discount Omission): Caught by test_silver_tier_5_pct_discount
- DEFECT-BK-001 (Minimum Reserve Invariant Breach): Caught by test_exact_balance_boundary_rejected_to_protect_reserve
- DEFECT-BK-002 (Transaction Condition Inversion): Caught by test_nominal_transaction_succeeds
- DEFECT-BK-003 (Negative Amount Validation Drop): Caught by test_negative_amount_rejected
- DEFECT-CC-001 (Identical Currency Spread Fee Leak): Caught by test_identical_currency_no_spread_or_fee
- DEFECT-CC-002 (Cross-Rate Matrix Ratio Inversion): Caught by test_usd_to_eur_conversion_nominal
- DEFECT-CC-003 (VIP Fee Waiver Condition Inversion): Caught by test_vip_customer_receives_reduced_spread_and_fee_waiver
```

**Attribution Rate:** 15 / 15 (100.0%) intended defect assertions failed against their target variants.

---

## 4. AST Mutation Testing & Denominator Accounting

The evaluation harness was integrated with TestForge's AST mutation engine (`testforge/mutator.py`) and equivalence classifier (`testforge/equivalence.py`).

### Overall Corpus Mutation Performance on Baseline Suites:
- Total Mutants Generated: 201
- Mutants Killed: 153
- Mutants Survived: 48
- Invalid Mutants: 0
- Potentially Equivalent Mutants: 0
- Overall Raw Mutation Score: **76.12%**
- Reference Test Suite Coverage: **100.0% line coverage** across all five fixtures.

### Denominator Rigor:
- $M_{\text{eval}} = \text{Killed} + \text{Survived} + \text{Timed Out} + \text{Equivalent}$.
- Invalid mutants ($I$) are strictly excluded from $M_{\text{eval}}$.
- Raw Score = $\frac{\text{Killed} + \text{Timed Out}}{M_{\text{eval}}} \times 100\%$.
- Adjusted Score = $\frac{\text{Killed} + \text{Timed Out}}{M_{\text{eval}} - \text{Equivalent}} \times 100\%$.

---

## 5. Benchmark Strategy Integration

The runner module `testforge/corpus/runner.py` executes strategy comparisons (`baseline`, `zeroshot`, and `agentic_reflection`) across all five corpus fixtures.
- Integrated into `run_benchmark.py` via the new CLI flag:
  `python run_benchmark.py --corpus [--fast]`
- Fully backward compatible with legacy targets (e.g., `python run_benchmark.py -t samples/discount.py`).
- Distinct run identifiers (`uuid4()`) and execution timestamps prevent overwriting past evidence.
- Transparent metric accounting: missing model credentials output zero tokens and \$0.00 cost, strictly avoiding fabricated metrics.

---

## 6. Verification & Test Evidence

### 1. Acceptance Suite (`tests/test_evaluation_corpus.py`)
```bash
.venv-release/bin/pytest tests/test_evaluation_corpus.py -v
```
**Outcome:** 16 passed in 14.73s (100% pass rate).

### 2. Regression Suites
```bash
.venv-release/bin/pytest tests/test_checkpoint_resumption.py tests/test_blackboard_persistence.py tests/test_task_lifecycle.py tests/test_orchestration_mcp.py tests/test_benchmarking.py tests/test_fast_benchmarking.py -q
```
**Outcome:** 80 passed in 97.33s (100% pass rate).

### 3. Syntax and Compilation
```bash
python3 -m py_compile testforge/corpus/models.py testforge/corpus/manager.py testforge/corpus/runner.py testforge/corpus/__init__.py testforge/corpus/fixtures/*.py
```
**Outcome:** Clean (exit code 0).

### 4. Git Diff & Tree Cleanliness
```bash
git diff --check
```
**Outcome:** Clean, no whitespace errors or merge conflicts.

---

## 7. Artifact Manifest

All artifacts are persisted in:
`/Users/sourabh/TestForge/qa_artifacts/phase2_m1_evaluation_corpus_20261025_211500/`

- `MILESTONE_REPORT.md`: This milestone completion and evidence report.
- `CORPUS_MANIFEST.csv`: Detailed metadata for all five fixtures with SHA-256 hashes and function contracts.
- `DEFECT_MANIFEST.csv`: Detailed manifest of all 15 injected defect variants.
- `BENCHMARK_METHODOLOGY.md`: Evaluation strategy, metric classification, and statistical guidelines.
- `TEST_RESULTS.md`: Detailed test run logs, assertion failure tracing, and strategy benchmark outputs.
- `benchmark_corpus_results.json`: Machine-readable output of full corpus evaluation.
- `benchmark_strategy_comparison.json`: Machine-readable output of multi-strategy benchmark runner.
- `IMPLEMENTATION_TRACEABILITY.csv`: Traceability matrix mapping requirements to test methods.
- `KNOWN_LIMITATIONS.md`: Boundaries, offline mock limits, and items deferred to Milestone 2.2.

---

## 8. Milestone Conclusion & Stop Condition

Milestone 2.1 is **COMPLETE**. The evaluation corpus and reproducible evaluation harness are established, verified, and ready for empirical multi-run strategy comparison in Milestone 2.2.
