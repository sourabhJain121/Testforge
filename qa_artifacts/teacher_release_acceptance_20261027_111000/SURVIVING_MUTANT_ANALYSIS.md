# TESTFORGE — SURVIVING MUTANT IN-DEPTH ANALYSIS

**Audit Date**: October 27, 2026  
**Audit Directory**: `qa_artifacts/teacher_release_acceptance_20261027_111000/`  
**Targets Analyzed**: `discount.py`, `banking.py`, `inventory_pricing.py`, `state_machine.py`, `rate_limiter.py`

---

## 1. Overview of AST Mutation Operators in TestForge

TestForge mutates source code directly at the Python AST level using standard mutation operators:
- **`MUT_BOUNDARY_SWAP`**: Swapping relational operators (`<` $\leftrightarrow$ `<=`, `>` $\leftrightarrow$ `>=`).
- **`MUT_OFF_BY_ONE`**: Incrementing or decrementing integer/float literals by 1.
- **`MUT_MATH_FUNC`**: Altering math function parameters or operators (`round(x, 2)` $\rightarrow$ `round(x, 1)`, `+` $\rightarrow$ `-`).
- **`MUT_BOOLEAN_INVERT`**: Inverting logical operators (`and` $\leftrightarrow$ `or`, `True` $\leftrightarrow$ `False`).
- **`MUT_RETURN_VALUE`**: Altering returned literals (e.g., returning `None` or negated values).

Across all 5 benchmark runs, every generated mutant was executed in an isolated subprocess sandbox. Mutants that survived 3 reflection cycles fall into three distinct structural categories:

---

## 2. Classification of Surviving Mutants

### Category A: Semantically Equivalent Mutants
These mutants change the AST without changing the observable input-output behavior of the function. No black-box test can kill them without violating clean-code invariants.

- **Example 1 (`discount.py` — `MUT_BOUNDARY_SWAP_003`)**:
  ```diff
  --- Clean Code (Line 9)
  +++ Mutated Code
  - if price <= 0.0:
  + if price < 0.0:
        return 0.0
  ```
  *Behavioral Analysis*: When `price == 0.0`, the clean code returns `0.0`. Under the mutant, the condition evaluates to `False`, execution proceeds to the calculation `price * (1.0 - rate)`, which evaluates to `0.0 * (1.0 - rate) = 0.0`. The returned value is identical in both cases. This mutant is mathematically equivalent.

- **Example 2 (`banking.py` — Balance check on zero deposit)**:
  ```diff
  --- Clean Code (Line 18)
  +++ Mutated Code
  - if amount <= 0:
  + if amount < 0:
        raise ValueError("Invalid amount")
  ```
  *Behavioral Analysis*: In a system where depositing `0` neither credits nor debits the account, if a zero-deposit is permitted by the mutant, the resulting account balance remains completely unchanged. Unless a specific assertion tests that an exception is raised on zero, this mutant survives.

---

### Category B: Unexercised Strict Boundary Conditions
These mutants alter boundary thresholds by exactly 1 unit or flip strict inequality to non-strict. They require precise boundary values to be killed.

- **Example 1 (`discount.py` — `MUT_BOUNDARY_SWAP_009`)**:
  ```diff
  --- Clean Code (Line 13)
  +++ Mutated Code
  - elif quantity >= 5:
  + elif quantity > 5:
        rate = 0.10
  ```
  *Killing Requirement*: Must execute `calculate_discount(..., quantity=5)`. Baseline tests tested `quantity=1` and `quantity=10`, leaving `quantity=5` untested.
- **Example 2 (`discount.py` — `MUT_OFF_BY_ONE_010`)**:
  ```diff
  --- Clean Code (Line 13)
  +++ Mutated Code
  - elif quantity >= 5:
  + elif quantity >= 6:
        rate = 0.10
  ```
  *Killing Requirement*: Requires testing `quantity=5`.

---

### Category C: Rounding and Precision Shifts
- **Example (`discount.py` — `MUT_MATH_FUNC_018`)**:
  ```diff
  --- Clean Code (Line 20)
  +++ Mutated Code
  - return round(final_price, 2)
  + return round(final_price, 1)
  ```
  *Killing Requirement*: Requires input prices that produce values where the second decimal digit is non-zero (e.g., `$19.99` with 15% discount $= \$16.9915 \rightarrow \$16.99$ vs $\$17.0$). If baseline or generated tests use round prices (e.g., `$100.00`, `$50.00`), rounding to 1 or 2 decimals produces identical results (`$85.0` vs `$85.00`).

---

## 3. Summary of Survivors by Benchmark File

| Benchmark File | Total Generated | Total Survived | Equivalent (Est.) | Boundary Gaps | Precision Shifts | Primary Cause of Survival |
| :--- | :---: | :---: | :---: | :---: | :---: | :--- |
| `discount.py` | 19 | 7 | 2 | 4 | 1 | Boundary inputs at $q=5, q=10$ and decimal precision |
| `banking.py` | 23 | 11 | 3 | 6 | 2 | Overdraft edge limits and zero-value transaction guards |
| `inventory_pricing.py` | 37 | 20 | 5 | 11 | 4 | Multi-tier bulk pricing thresholds and volume cutoffs |
| `state_machine.py` | 57 | 45 | 12 | 25 | 8 | Complex state transition guards and event payload edge cases |
| `rate_limiter.py` | 38 | 22 | 4 | 14 | 4 | Microsecond timestamp boundary cutoffs and token leak math |

---

## 4. Engineering Recommendations

1. **Static AST Equivalence Reduction**: Implement an AST rewrite rule engine that detects idempotent boundary operations (e.g., zero-multiplication and empty collections) and marks them `EQUIVALENT` prior to scoring.
2. **SMT Boundary Synthesizer**: Connect the reflection critic to a symbolic execution or SMT solver (e.g., Z3) to synthesize exact boundary inputs (e.g., solving `quantity == 5`) when LLM prompting misses pinpoint integers.
3. **Dynamic Iteration Budgets**: Allow higher iteration budgets (e.g., 5–7 cycles) for complex modules like `state_machine.py` with large mutant pools.
