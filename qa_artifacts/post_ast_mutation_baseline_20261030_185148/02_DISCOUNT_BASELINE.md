# Baseline Mutation Testing Report: Discount Engine

**Target File:** `samples/discount.py`  
**Execution Date:** 2026-10-30  
**Artifact Directory:** `qa_artifacts/post_ast_mutation_baseline_20261030_185148/`  
**Database Checkpoint:** `discount_baseline.db`  
**Exported Hardened Suite:** `test_hardened_discount.py`  

---

## 1. Benchmark Execution Summary

| Metric | Measured Value | Target / Requirement | Status |
| :--- | :--- | :--- | :--- |
| **Total Execution Duration** | 7.59 seconds | < 60.0s | PASS |
| **Mutation Evaluation Time** | 1.10 seconds | - | PASS |
| **Baseline Tests Generated** | 2 | $\ge$ 1 | PASS |
| **Baseline Test Pass Rate** | 2 / 2 (100.0%) | 100% | PASS |
| **Statement Coverage** | 70.0% (7 / 10 statements) | Baseline | RECORDED |
| **Total Mutants Generated** | 19 | - | RECORDED |
| **Mutants Executed** | 19 | 19 | COMPLETE |
| **Mutants Killed** | 1 | - | RECORDED |
| **Mutants Survived** | 18 | - | RECORDED |
| **Timed Out / Errors** | 0 / 0 | 0 | CLEAN |
| **Mutation Score** | **5.26%** | Target 85.0% | **UNREACHED** |
| **Hardening Status** | `TARGET_SCORE_UNREACHED` | - | RECORDED |

---

## 2. Generated Test Suite Listing

The autonomous generator produced the following pytest suite:

```python
import os
import sys
sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import pytest
from samples.discount import calculate_discount

def test_calculate_discount_nominal():
    result = calculate_discount(10.0, 2, False)
    assert result is not None

def test_calculate_discount_multi_arg_scenario():
    result = calculate_discount(10.0, 2, False)
    assert result is not None
```

### Analysis of the Generated Tests
1. **Redundancy:** Both generated tests execute the exact same input tuple: `calculate_discount(10.0, 2, False)`.
2. **Weak Oracle:** Both tests assert only `assert result is not None`. No assertion verifies that `10.0 * (1.0 - 0.0) == 10.0`.
3. **Unexercised Branches:**
   - The volume discount branch `if quantity >= 5:` is never executed (`quantity = 2`).
   - The membership discount branch `if is_member:` is never executed (`is_member = False`).
   - The invalid/zero price check `if price <= 0.0:` is never tested with negative or zero price.

---

## 3. Mutant Classification & Execution Outcomes

| Mutant ID | Line | Operator | Mutated Syntax | Outcome | Killing Factor / Survival Reason |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `MUT_COND_INV_001` | 9 | `COND_INV` | `if not price <= 0.0:` | **SURVIVED** | Returned 0.0; `0.0 is not None` passed |
| `MUT_COMP_OP_002` | 9 | `COMP_OP` | `if price > 0.0:` | **SURVIVED** | Returned 0.0; `0.0 is not None` passed |
| `MUT_CONST_VAL_003` | 9 | `CONST_VAL` | `if price <= 1.0:` | **SURVIVED** | 10.0 <= 1.0 is False; branch skipped |
| `MUT_RETURN_VAL_004`| 10 | `RETURN_VAL` | `return 1.0` | **SURVIVED** | Line unreached with `price=10.0` |
| `MUT_CONST_VAL_005` | 12 | `CONST_VAL` | `discount_rate = 1.0` | **SURVIVED** | Returned 0.0; `0.0 is not None` passed |
| `MUT_COND_INV_006` | 13 | `COND_INV` | `if not quantity >= 5:` | **SURVIVED** | Added 10% discount; `9.0 is not None` passed |
| `MUT_COMP_OP_007` | 13 | `COMP_OP` | `if quantity < 5:` | **SURVIVED** | Added 10% discount; `9.0 is not None` passed |
| `MUT_CONST_VAL_008` | 13 | `CONST_VAL` | `if quantity >= 6:` | **SURVIVED** | Line condition unreached |
| `MUT_ARITH_OP_009` | 14 | `ARITH_OP` | `discount_rate - 0.10` | **SURVIVED** | Line unreached (`quantity=2`) |
| `MUT_CONST_VAL_010` | 14 | `CONST_VAL` | `discount_rate + 1.10` | **SURVIVED** | Line unreached (`quantity=2`) |
| `MUT_COND_INV_011` | 16 | `COND_INV` | `if not is_member:` | **SURVIVED** | Added 10% discount; `9.0 is not None` passed |
| `MUT_ARITH_OP_012` | 17 | `ARITH_OP` | `discount_rate - 0.10` | **SURVIVED** | Line unreached (`is_member=False`) |
| `MUT_CONST_VAL_013` | 17 | `CONST_VAL` | `discount_rate + 1.10` | **SURVIVED** | Line unreached (`is_member=False`) |
| `MUT_ARITH_OP_014` | 19 | `ARITH_OP` | `1.0 + discount_rate` | **SURVIVED** | Returned 10.0; `10.0 is not None` passed |
| `MUT_CONST_VAL_015` | 19 | `CONST_VAL` | `2.0 - discount_rate` | **SURVIVED** | Returned 20.0; `20.0 is not None` passed |
| `MUT_ARITH_OP_016` | 19 | `ARITH_OP` | `price / (1.0 - rate)` | **SURVIVED** | Returned 10.0; `10.0 is not None` passed |
| `MUT_RETURN_VAL_017`| 20 | `RETURN_VAL` | `return None` | **KILLED** | `assert result is not None` failed! |
| `MUT_CONST_VAL_018` | 20 | `CONST_VAL` | `round(final_price, 3)`| **SURVIVED** | Returned 10.0; `10.0 is not None` passed |
| `MUT_CONST_VAL_019` | 20 | `CONST_VAL` | `round(final_price, 1)`| **SURVIVED** | Returned 10.0; `10.0 is not None` passed |

---

## 4. Key Takeaways
- **Only 1 mutant was killed:** `MUT_RETURN_VAL_017` (`return None`), because the sole assertion in the suite is `assert result is not None`.
- All other 18 mutants survived either because they altered calculations without returning `None`, or because they existed inside unreached conditional branches.
- Demonstrates conclusively that **weak assertions** directly restrict mutation scores.

