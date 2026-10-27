# TestForge — Benchmark & Empirical Ablation Validity Audit

**Audit Date:** 2026-10-27 01:22:45 IST  
**Audit Directory:** `qa_artifacts/autonomous_e2e_acceptance_20261027_004800/`  

---

## 1. Benchmark Integrity & Historical Grounding

TestForge provides a 3-way empirical ablation study comparing:
1. **Handwritten Baseline (`baseline`):** Expert human-authored unit tests.
2. **Zero-Shot LLM (`zeroshot`):** Single-pass prompt test generation without adversarial critique or reflection.
3. **Multi-Pass Agentic Reflection (`agentic_reflection`):** Evaluator-Optimizer loop combining Google ADK test generation, AST mutation feedback, and CrewAI diagnostic directives.

---

## 2. Verified Benchmark Metrics Across 5 Standard Fixtures

Based on repeatable empirical execution across the 5 reference fixtures (`task_state_transition`, `token_bucket_rate_limiter`, `inventory_pricing_calculator`, `banking_operations_module`, `currency_converter`):

| Metric | Baseline (Handwritten) | Zero-Shot LLM | Agentic Reflection |
|---|:---:|:---:|:---:|
| **Mean Mutation Score** | **76.62%** | **28.34%** | **28.84%** |
| **Defect Detection Rate** | **100.0%** | **26.66%** | **26.66%** |
| **Mean Line Coverage** | **100.0%** | **49.64%** | **42.86%** |
| **False-Positive Candidate Rate (Clean Code Failure)** | **0.0%** | **64.78%** | **71.28%** |
| **Mean Wall-Clock Runtime** | **3.31 s** | **37.35 s** | **90.30 s** |
| **Total Injected Mutants** | 201 | 201 | 201 |
| **Total Verified Genuine Kills** | 153 | 50 | 55 |

---

## 3. Methodological Rigor & Audit Invariants

1. **Granular Clean-Reference Quarantine:**
   - Any candidate test that fails on clean unmutated reference code is quarantined immediately as a false positive.
   - Prevents the historical defect where broken tests were falsely credited with killing 100% of mutants.
2. **True Mutant Kill Condition:**
   - A mutant is logged as `KILLED` if and only if the test suite passes on the clean reference and fails on the mutant.
3. **Zero Financial Spend:**
   - Benchmarking evaluated over local deterministic/Ollama execution mode with exact $0.00 cloud API spend.
4. **Historical Artifact Preservation:**
   - Historical records (`benchmark_results.json`, `qa_artifacts/phase4_m3_benchmark_validity_20261026_125000/`) remain untouched in their original state.
