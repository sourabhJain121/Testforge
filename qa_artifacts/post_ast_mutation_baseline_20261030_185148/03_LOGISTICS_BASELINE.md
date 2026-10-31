# Baseline Mutation Testing Report: Enterprise Logistics Engine

**Target File:** `samples/uploaded_logistics_engine.py`  
**Execution Date:** 2026-10-30  
**Artifact Directory:** `qa_artifacts/post_ast_mutation_baseline_20261030_185148/`  
**Database Checkpoint:** `logistics_baseline.db`  
**Exported Hardened Suite:** `test_hardened_logistics.py`  

---

## 1. Benchmark Execution Summary

| Metric | Measured Value | Target / Requirement | Status |
| :--- | :--- | :--- | :--- |
| **Total Execution Duration** | 20.04 seconds | < 60.0s | PASS |
| **Mutation Evaluation Time** | 18.02 seconds | Parallelized | PASS |
| **Worker Concurrency** | 8 worker processes | Auto-detected | PASS |
| **Baseline Tests Generated** | 3 | $\ge$ 1 | PASS |
| **Baseline Test Pass Rate** | 3 / 3 (100.0%) | 100% | PASS |
| **Statement Coverage** | 26.52% (35 / 132 statements) | Baseline | RECORDED |
| **Total Mutants Generated** | 258 | - | RECORDED |
| **Mutants Executed** | 258 | 258 | COMPLETE |
| **Mutants Killed** | 8 | - | RECORDED |
| **Mutants Survived** | 250 | - | RECORDED |
| **Timed Out / Errors** | 0 / 0 | 0 | CLEAN |
| **Mutation Score** | **3.10%** | Target 85.0% | **UNREACHED** |
| **Hardening Status** | `TARGET_SCORE_UNREACHED` | - | RECORDED |

---

## 2. Generated Test Suite Listing

```python
import os
import sys
sys.path.insert(0, os.path.abspath('.'))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

import pytest
from samples.uploaded_logistics_engine import calculate_item_discount

def test_calculate_item_discount_nominal():
    result = calculate_item_discount(10.0, 2)
    assert result is not None

def test_calculate_item_discount_boundary_nominal_alt():
    result = calculate_item_discount(20.0, 5)
    assert result is not None

def test_calculate_item_discount_adversarial_equal():
    result = calculate_item_discount(5.0, 5)
    assert result is not None
```

---

## 3. Coverage & Scope Analysis: The Single-Callable Bottleneck

The target file `samples/uploaded_logistics_engine.py` is a 270-line multi-component logistics module containing 6 top-level functions and 1 class:
1. `class WarehouseInventory` (lines 10–56)
2. `def calculate_item_discount(...)` (lines 59–95)
3. `def estimate_freight_cost(...)` (lines 98–140)
4. `def calculate_customs_duty(...)` (lines 143–165)
5. `def validate_tracking_number(...)` (lines 168–186)
6. `def compute_sla_deadline_hours(...)` (lines 189–205)
7. `def process_bulk_order(...)` (lines 208–265)

### Functional Distribution of Mutants vs Test Coverage

| Target Callable | Lines | Statements | Covered | Mutants Generated | Mutants Killed | Mutants Survived | Function Mutation Score |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `calculate_item_discount` | 59–95 | 35 | 35 (100%) | 42 | 8 | 34 | **19.05%** |
| `WarehouseInventory` | 10–56 | 28 | 0 (0%) | 38 | 0 | 38 | **0.00%** |
| `estimate_freight_cost` | 98–140 | 22 | 0 (0%) | 51 | 0 | 51 | **0.00%** |
| `calculate_customs_duty`| 143–165 | 14 | 0 (0%) | 34 | 0 | 34 | **0.00%** |
| `validate_tracking_number` | 168–186 | 10 | 0 (0%) | 22 | 0 | 22 | **0.00%** |
| `compute_sla_deadline_hours` | 189–205 | 9 | 0 (0%) | 20 | 0 | 20 | **0.00%** |
| `process_bulk_order` | 208–265 | 14 | 0 (0%) | 51 | 0 | 51 | **0.00%** |
| **Total Module** | **1–270** | **132** | **35 (26.52%)** | **258** | **8** | **250** | **3.10%** |

### The Root Cause Revealed:
- **216 out of 250 surviving mutants (86.4%)** reside in functions that were **never called** by the generated test suite.
- The generator currently extracts only `signatures[0]` (the first callable after imports, which happens to be `calculate_item_discount` when standalone functions are prioritized).
- All remaining business logic—freight estimation, customs valuation, SLA calculation, order processing, and inventory management—has **0 tests and 0% coverage**.

---

## 4. Killed Mutants Breakdown

The 8 mutants killed were all in `calculate_item_discount`:
1. `MUT_COND_INV_047` (Line 65, `if not unit_price <= 0.0:`): Raised `ValueError` on nominal price `10.0`, killing the mutant.
2. `MUT_COMP_OP_048` (Line 65, `if unit_price > 0.0:`): Raised `ValueError` on nominal price `10.0`, killing the mutant.
3. `MUT_COND_INV_053` (Line 67, `if not quantity < 1:`): Raised `ValueError` on nominal quantity `2`, killing the mutant.
4. `MUT_COMP_OP_054` (Line 67, `if quantity >= 1:`): Raised `ValueError` on nominal quantity `2`, killing the mutant.
5. `MUT_CONST_VAL_059` (Line 70, `valid_tiers = {"", ...}`): Raised `ValueError("Invalid customer tier: REGULAR")`, killing the mutant.
6. `MUT_COND_INV_064` (Line 72, `if tier_upper in valid_tiers:`): Raised `ValueError` on valid tier `REGULAR`, killing the mutant.
7. `MUT_COMP_OP_065` (Line 72, `if tier_upper not in valid_tiers:` flipped): Raised `ValueError`, killing the mutant.
8. `MUT_RETURN_VAL_089` (Line 94, `return min(...)` replaced): Caused exception or None assertion failure, killing the mutant.

Each killed mutant was caught because mutating the guard conditions caused a unexpected `ValueError` to abort test execution, which failed the test and killed the mutant.

