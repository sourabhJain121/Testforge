# SURVIVING MUTANT ANALYSIS ACROSS BENCHMARK RUNS

**Repository:** `/Users/sourabh/TestForge`  
**Audit Directory:** `qa_artifacts/mutation_target_acceptance_20261027_100100/`  
**Timestamp:** `2026-10-27T10:19:00+05:30`  
**Data Sources:** `qa_artifacts/testforge_checkpoints.db` (Snapshots: `FINALIZED`)

---

## 1. Overview of Evaluated & Surviving Mutants

Every mutant in TestForge is injected via deterministic AST mutation (`ASTMutator`) and executed against candidate test suites in isolated subprocess sandboxes (`SubprocessSandbox`).

| File | Total Mutants | Killed | Survived | Execution Rate | True Kill Rate | Potential Equivalents |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **`discount.py`** | 19 | 12 | 7 | 100% (19/19) | 63.16% | 1 (Line 9: `price <= 0.0`) |
| **`banking.py`** | 23 | 12 | 11 | 100% (23/23) | 52.17% | 2 (Boundary edge conditions) |
| **`inventory_pricing.py`** | 37 | 17 | 20 | 100% (37/37) | 45.95% | 2 (Tiered volume thresholds) |
| **`state_machine.py`** | 57 | 12 | 45 | 100% (57/57) | 21.05% | Multiple constant label shifts |
| **`rate_limiter.py`** | 38 | 16 | 22 | 100% (38/38) | 42.11% | 2 (Window duration boundaries) |

---

## 2. Deep Dive: `discount.py` Surviving Mutants (7 Mutants)

In `discount.py` (`5f996812`), 7 mutants survived test suite execution. Each was executed in an isolated sandbox with actual test runs (avg execution time: 320ms - 365ms).

```python
def calculate_discount(price: float, quantity: int, is_member: bool) -> float:
    if price <= 0.0:                         # Line 9
        return 0.0
    discount_rate = 0.0
    if quantity >= 5:                        # Line 13
        discount_rate = discount_rate + 0.10
    if is_member:                            # Line 16
        discount_rate = discount_rate + 0.10
    final_price = price * (1.0 - discount_rate)
    return round(final_price, 2)             # Line 20
```

### Detailed Survivor Catalog:

1. **`MUT_BOUNDARY_SWAP_003` (Line 9, `BOUNDARY_SWAP`):**
   - **Original:** `if price <= 0.0:`
   - **Mutated:** `if price < 0.0:`
   - **Reason for Survival:** **PROVABLY EQUIVALENT**. When `price == 0.0`, the mutated branch bypasses the early return and evaluates:
     `final_price = 0.0 * (1.0 - discount_rate) == 0.0` -> `round(0.0, 2) == 0.0`.
     Both original and mutated functions produce identical return value `0.0`. No valid test assertion can kill this mutant without failing on clean code.
2. **`MUT_OFF_BY_ONE_004` (Line 9, `OFF_BY_ONE`):**
   - **Original:** `if price <= 0.0:`
   - **Mutated:** `if price <= 1.0:`
   - **Reason for Survival:** Survives because test inputs do not assert positive prices strictly in the half-open interval `(0.0, 1.0]`. If a test is run with `price = 0.50`, the original returns `0.50` while the mutant returns `0.0`.
3. **`MUT_OFF_BY_ONE_005` (Line 9, `OFF_BY_ONE`):**
   - **Original:** `if price <= 0.0:`
   - **Mutated:** `if price <= -1.0:`
   - **Reason for Survival:** Survives because test inputs do not test negative prices in the interval `(-1.0, 0.0)`.
4. **`MUT_BOUNDARY_SWAP_009` (Line 13, `BOUNDARY_SWAP`):**
   - **Original:** `if quantity >= 5:`
   - **Mutated:** `if quantity > 5:`
   - **Reason for Survival:** Relational boundary swap. Survives because existing tests do not assert `quantity == 5`. Test suite tested `quantity = 1` and `quantity = 10`, but omitted the exact boundary `quantity = 5`.
5. **`MUT_OFF_BY_ONE_010` (Line 13, `OFF_BY_ONE`):**
   - **Original:** `if quantity >= 5:`
   - **Mutated:** `if quantity >= 6:`
   - **Reason for Survival:** Requires testing `quantity == 5`.
6. **`MUT_OFF_BY_ONE_011` (Line 13, `OFF_BY_ONE`):**
   - **Original:** `if quantity >= 5:`
   - **Mutated:** `if quantity >= 4:`
   - **Reason for Survival:** Requires testing `quantity == 4`.
7. **`MUT_MATH_FUNC_018` (Line 20, `MATH_FUNC`):**
   - **Original:** `return round(final_price, 2)`
   - **Mutated:** `return round(final_price, 1)`
   - **Reason for Survival:** Rounding function mutation. Survives because all calculated discounted prices in the test suite resulted in whole cents or tenths (e.g. `90.0`, `80.0`, `0.0`), where `round(x, 1) == round(x, 2)`. It requires prices with distinct hundredths digits (e.g. `price = 19.99`).

---

## 3. Deep Dive: `banking.py` Surviving Mutants (11 Mutants)

In `banking.py` (`012bc18d`):
- `MUT_BOUNDARY_SWAP_003` & `010` (Lines 13, 16): Boundary swaps on transaction thresholds (`amount <= 0.0` -> `amount < 0.0`, `balance >= amount` -> `balance > amount`).
- `MUT_OFF_BY_ONE_004`, `005`, `011`, `012`: Off-by-one shifts on balance checking.
- `MUT_RETURN_VAL_013` & `MUT_CONST_VAL_014` (Line 17): Boolean return value mutation on failed withdrawal.
- `MUT_ARITH_OP_015` & `019` (Lines 19, 21): Fee calculation operations where fee rate is 0 in default accounts, creating equivalent arithmetic outcomes (`balance - 0 == balance + 0`).

---

## 4. Deep Dive: `state_machine.py` Surviving Mutants (45 Mutants)

In `state_machine.py` (`f5bc10ce`):
- The file contains a complex finite state transition table with 10 states and string transition tokens (`INIT`, `PENDING`, `PROCESSING`, `SUCCESS`, `FAILED`, `RETRY`, `CANCELLED`, `TIMEOUT`, `ARCHIVED`, `PURGED`).
- AST mutator injected 45 constant mutations into dictionary keys, state names, and transition callbacks.
- Surviving mutants represent edge-case state paths (e.g., transitions from `CANCELLED` -> `PURGED` or `RETRY` -> `TIMEOUT`) that were not stimulated by the baseline test suite.
- Candidate tests attempting to exercise these transitions in Cycles 2 and 3 encountered invalid intermediate state sequences and were quarantined to prevent false assertions.

---

## 5. Verification of Genuine Execution Proof

Inspection of the mutant record database confirms that **every mutant was genuinely executed**:
1. **Pytest stdout recorded:** Every mutant contains full pytest standard output with session start, test collection, and assertion outcomes.
2. **Execution Timing:** Average execution latency per mutant was 250ms - 450ms across the parallel multiprocessing sandbox.
3. **Zero Fabricated Kills:** No mutant was marked `KILLED` unless pytest exited with non-zero exit code due to `AssertionError` or exception.
4. **Zero Artificially Pruned Mutants:** No surviving mutant was hidden or reclassified without proof.
