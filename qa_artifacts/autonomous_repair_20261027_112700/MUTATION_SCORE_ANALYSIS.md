# Mutation Score & Target Attainment Analysis

**Audit Directory:** `qa_artifacts/autonomous_repair_20261027_112700/`  
**Repository:** `/Users/sourabh/TestForge`  
**Configured Target Mutation Score:** `85.0%`  
**Reflection Budget:** `max_iterations = 3`

---

## 1. Independent Investigation of `TARGET_SCORE_UNREACHED`

During live runs across all five benchmark modules (`discount.py`, `banking.py`, `inventory_pricing.py`, `state_machine.py`, `rate_limiter.py`), jobs terminate with the status:
```text
TARGET_SCORE_UNREACHED
```
An independent investigation was conducted across raw backend JSON responses, AST mutation engines, and clean-code validators.

### Representative Results Matrix:
| Target Sample | Generated Mutants | Mutants Killed | Mutants Survived | Equivalent Mutants | Raw Score | Target Score | Reflection Cycles | Stopping Condition |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :--- |
| `discount.py` | 19 | 12 | 7 | 0 | **63.16%** | 85.0% | 3 / 3 | Max iterations reached |
| `banking.py` | 23 | 12 | 11 | 0 | **52.17%** | 85.0% | 3 / 3 | Max iterations reached |
| `inventory_pricing.py` | 37 | 17 | 20 | 0 | **45.95%** | 85.0% | 3 / 3 | Max iterations reached |
| `state_machine.py` | 57 | 12 | 45 | 0 | **21.05%** | 85.0% | 3 / 3 | Max iterations reached |
| `rate_limiter.py` | 38 | 16 | 22 | 0 | **42.11%** | 85.0% | 3 / 3 | Max iterations reached |

---

## 2. Root Cause Analysis of Mutation Score Plateau

1. **Clean Code Quarantine Protection**:
   In reflection cycles 2 and 3, Google ADK Generator generated candidate assertions targeting surviving mutants. When candidate tests failed on the clean, unmutated source code, TestForge's clean-code validator quarantined them to guarantee 100% Pass@1 clean code integrity.
2. **Semantic Equivalence Invariants**:
   Inspection of surviving mutants in `discount.py` revealed:
   - `MUT_BOUNDARY_SWAP_003` (Line 9: `price <= 0.0` -> `price < 0.0`): When `price == 0.0`, computing `0.0 * (1.0 - rate)` yields `0.0`. Thus, mutating `<=` to `<` produces identical output for non-negative inputs, creating a semantically equivalent mutant that cannot be killed by any valid test.
   - `MUT_BOUNDARY_SWAP_009` (Line 13: `quantity >= 5` -> `quantity > 5`): Requires testing exact boundary `quantity == 5`.
   - `MUT_OFF_BY_ONE_010` & `011` (Line 13: `quantity >= 6` and `quantity >= 4`).
   - `MUT_MATH_FUNC_018` (Line 20: `round(final_price, 2)` -> `round(final_price, 1)`): Requires prices with 2 non-zero decimal fractions.
3. **Finite Reflection Ceiling**:
   Because the orchestrator enforces `max_iterations = 3`, the loop terminated gracefully when the iteration ceiling was reached without reaching 85.0%.

---

## 3. Mathematical Formula Validation

TestForge computes scores using the standard mutation testing definition:
$$\text{Raw Mutation Score} = \left(\frac{\text{Mutants Killed}}{\text{Mutants Generated}}\right) \times 100$$
$$\text{Adjusted Mutation Score} = \left(\frac{\text{Mutants Killed}}{\text{Mutants Generated} - \text{Equivalent Mutants}}\right) \times 100$$

For `discount.py`:
$$\frac{12}{19} \times 100 = 63.15789...\% \rightarrow \mathbf{63.2\%}$$
The UI and backend mathematical values match with 100% precision.

---

## 4. UI Presentation & Honest Acceptance

To avoid misleading users:
- **No Unearned Green Banners**: The UI presents an amber warning banner:  
  `⚠️ Pipeline Completed — Mutation Target Unreached`
- **Tripartite Badging**:
  1. `Baseline: 100% Passed` (Clean code integrity preserved).
  2. `Pipeline: Finished` (Completed all 3 reflection cycles).
  3. `Target: Unreached` (63.2% vs 85.0% target).
- **Surviving Mutant Diagnosis**: The UI explains the boundary condition and potential equivalence of surviving mutants directly in the AST diff modal.
