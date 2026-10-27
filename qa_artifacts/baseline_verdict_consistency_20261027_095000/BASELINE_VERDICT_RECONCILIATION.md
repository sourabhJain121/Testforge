# Baseline Verdict Reconciliation & Metric Disambiguation

**Audit Run**: `qa_artifacts/baseline_verdict_consistency_20261027_095000/`  
**Date**: 2026-10-27  
**Scope**: Inconsistency analysis between apparent test ratios (`9/10`, `15/21`, etc.) and the `🟢 ALL PASSED` Clean Code Verdict.  

---

## 1. The Core Question Investigated

In historical audit summaries, the following figures were reported side-by-side:
- `discount.py`: `10/10`, ALL PASSED
- `banking.py`: `9/10`, ALL PASSED
- `inventory_pricing.py`: `15/21`, ALL PASSED
- `state_machine.py`: `9/14`, ALL PASSED
- `rate_limiter.py`: `9/11`, ALL PASSED

The user raised a critical engineering inquiry:
> *"Determine precisely what the numerator and denominator represent. Establish whether these are baseline test results, generated-test counts, iteration metrics, or another metric. Do not assume that 9/10 necessarily means baseline failure until the field definitions are confirmed."*

---

## 2. Investigation Findings from Source Code & Raw Backend Responses

By inspecting [testforge/state.py](file:///Users/sourabh/TestForge/testforge/state.py), [frontend/index.html](file:///Users/sourabh/TestForge/frontend/index.html), [frontend/app.js](file:///Users/sourabh/TestForge/frontend/app.js), and querying the raw JSON response of `/api/harden/status/{job_id}` for each job, the exact definitions were established with 100% certainty:

### A. The 3 Distinct Rows in the TestForge KPI Architecture

1. **Row 1: Baseline Test Suite Execution (Pass@1 Integrity)**
   - Element `#kpi-base-gen`: `final_state["baseline_tests_generated"]` (Integer: count of test modules generated, e.g. `1`)
   - Element `#kpi-base-exec`: `final_state["baseline_tests_executed"]` (Integer: count of test modules executed in sandbox, e.g. `1`)
   - Element `#kpi-base-pass`: `final_state["baseline_tests_passed"]` (Integer: count of test modules passed, e.g. `1`)
   - Element `#kpi-base-fail`: `final_state["baseline_tests_failed"]` (Integer: count of test modules failed, e.g. `0`)
   - Element `#kpi-base-verdict`: `final_state["baseline_passed"]` (`🟢 ALL PASSED` if `tests_failed === 0 && tests_passed > 0`, otherwise `🔴 HAS FAILURES`)

2. **Row 2: Mutation Hardening & Line Coverage Analysis**
   - Element `#kpi-lines-cov`: `final_state["lines_covered"] / final_state["num_statements"]` (Statements covered out of executable AST statements!)
   - Element `#kpi-cov-pct`: `final_state["baseline_line_coverage"]` (Float percentage, e.g. `90.0%`)
   - Element `#kpi-mut-gen`: `final_state["mutants_generated"]`
   - Element `#kpi-mut-kill`: `final_state["mutants_killed"]`
   - Element `#kpi-mut-surv`: `final_state["mutants_survived"]`

3. **Row 3: Hardening Status & Reflection Cycles**
   - Element `#kpi-mut-score`: `final_state["final_mutation_score"]`
   - Element `#kpi-cycles-done`: Reflection Iterations
   - Element `#kpi-final-status`: Pipeline terminal status

---

## 3. Disambiguation Table: Statement Coverage vs. Test Execution

The fractions `10/10`, `9/10`, `15/21`, `9/14`, `9/11` represent **Executable AST Statements Covered**, NOT test cases passed!

| Sample File | Executable Statements (`num_statements`) | Statements Covered (`lines_covered`) | Line Coverage % (`baseline_line_coverage`) | Baseline Tests Executed | Baseline Tests Passed | Baseline Tests Failed | Clean Code Verdict (`baseline_passed`) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **discount.py** | **10** | **10** | **100.0%** | 1 | 1 | 0 | **🟢 ALL PASSED** |
| **banking.py** | **10** | **9** | **90.0%** | 1 | 1 | 0 | **🟢 ALL PASSED** |
| **inventory_pricing.py** | **21** | **15** | **71.4%** | 1 | 1 | 0 | **🟢 ALL PASSED** |
| **state_machine.py** | **14** | **9** | **64.3%** | 1 | 1 | 0 | **🟢 ALL PASSED** |
| **rate_limiter.py** | **11** | **9** | **81.8%** | 1 | 1 | 0 | **🟢 ALL PASSED** |

### Why Did the Summary Look Inconsistent?
In earlier summary tables, the column heading was compressed to "Line Coverage" with values written as `90.0% (9/10)`, placed immediately beside the column "Clean Code Verdict: 🟢 ALL PASSED". 

A reader unfamiliar with the internal DOM layout could easily misinterpret `(9/10)` as "9 tests passed out of 10 tests executed", and immediately ask why 9/10 is labeled `ALL PASSED`.

In reality:
- **100% of the baseline tests passed** (1 test module executed, 1 passed, 0 failed).
- That single comprehensive test module executed 9 out of 10 executable lines in `banking.py` (90.0% statement coverage).
- Therefore, the verdict `🟢 ALL PASSED` is **100% mathematically and operationally correct**.

---

## 4. Remediation for Unambiguous Reporting

In all future tables and reports, the columns are explicitly labeled:
- `Baseline Test Results`: `1 / 1 Passed (0 Failed) -> 🟢 ALL PASSED`
- `Code Statement Coverage`: `9 / 10 Statements Covered (90.0%)`

This completely eliminates confusion and preserves 100% metric accuracy.
