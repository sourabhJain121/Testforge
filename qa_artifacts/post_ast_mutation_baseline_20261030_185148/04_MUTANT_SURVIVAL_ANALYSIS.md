# In-Depth Mutant Survival Analysis & Taxonomy

**Execution Date:** 2026-10-30  
**Artifact Directory:** `qa_artifacts/post_ast_mutation_baseline_20261030_185148/`  
**Targets Audited:** `samples/discount.py` & `samples/uploaded_logistics_engine.py`  

---

## 1. Executive Summary

A mutation testing suite can only achieve a high mutation score when:
1. Every executable function is invoked (**Function Reachability**).
2. Every conditional branch and loop boundary is traversed (**Branch Coverage**).
3. Every test contains precise, concrete assertions on returned states, computed numbers, and raised exceptions (**Oracle Strength**).

Across both audited benchmarks, surviving mutants were systematically categorized into four distinct failure modes:

| Category | Description | Discount Count | Logistics Count | Total Survivors | % of Total |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Category A** | **Unreached Function Scope** (0 tests invoke the callable) | 0 | 216 | 216 | 80.6% |
| **Category B** | **Unreached Conditional Branches** (branches never taken) | 8 | 26 | 34 | 12.7% |
| **Category C** | **Weak Assertion / The Oracle Problem** (`assert result is not None`) | 6 | 8 | 14 | 5.2% |
| **Category D** | **Unchecked Boundary Inputs** (off-by-one or edge conditions) | 4 | 0 | 4 | 1.5% |
| **Total** | | **18** | **250** | **268** | **100.0%** |

---

## 2. Category A: Unreached Function Scope (The Scope Bottleneck)

In multi-function or object-oriented Python modules like `uploaded_logistics_engine.py`, the autonomous test generator currently generates tests only for the first signature (`signatures[0]`).

### Example Surviving Mutant in Unreached Function (`estimate_freight_cost`)

```diff
--- samples/uploaded_logistics_engine.py (original)
+++ samples/uploaded_logistics_engine.py (MUT_ARITH_OP_098)
@@ -107,3 +107,3 @@
     if is_hazardous:
-        base_cost *= 1.50
+        base_cost /= 1.50
     return round(base_cost, 2)
```

**Reason for Survival:**
No test in `test_hardened_logistics.py` ever imports or calls `estimate_freight_cost`. Because the line is never executed by any test, the mutated operator can never trigger a test failure.

**Solution:**
The generator must iterate through **all** public functions and classes discovered by the AST visitor, synthesizing dedicated test functions for each callable.

---

## 3. Category B: Unreached Conditional Branches

Within functions that *are* executed, many logical paths are bypassed because tests only pass nominal default arguments.

### Example Surviving Mutant in Unreached Branch (`calculate_discount`)

```diff
--- samples/discount.py (original)
+++ samples/discount.py (MUT_ARITH_OP_009)
@@ -13,2 +13,2 @@
     if quantity >= 5:
-        discount_rate = discount_rate + 0.10
+        discount_rate = discount_rate - 0.10
```

**Reason for Survival:**
The generated tests in `test_hardened_discount.py` only pass `quantity=2`. Thus, `quantity >= 5` evaluates to `False`, and line 14 is never executed. The mutated addition (`+` changed to `-`) has zero effect on the return value for `quantity=2`.

**Solution:**
Synthesize tests with inputs specifically designed to satisfy each branch condition (e.g. `calculate_discount(10.0, 5, False)` and `calculate_discount(10.0, 10, True)`).

---

## 4. Category C: Weak Assertion / The Oracle Problem

This is the most critical quality finding of the audit: **Tests execute mutated code, the mutation alters the computation, but the test passes anyway because the assertion is too weak.**

### Example Surviving Mutant Reached with Weak Assertion (`calculate_discount`)

```diff
--- samples/discount.py (original)
+++ samples/discount.py (MUT_CONST_VAL_015)
@@ -19,1 +19,1 @@
-    final_price = price * (1.0 - discount_rate)
+    final_price = price * (2.0 - discount_rate)
```

**What Happened During Execution:**
- Input: `calculate_discount(10.0, 2, False)`
- Original output: `10.0 * (1.0 - 0.0) = 10.0`
- Mutated output: `10.0 * (2.0 - 0.0) = 20.0`
- Test assertion: `assert result is not None`
- Evaluation: `20.0 is not None` $\rightarrow$ `True`!
- The test passed, and the mutant survived undetected!

**Solution:**
Replace existential checks (`is not None`) with exact or property-based assertions:
```python
# Instead of:
assert result is not None

# Generate:
assert result == 10.0
# Or for parameterized inputs:
assert result == pytest.approx(10.0, rel=1e-2)
```

---

## 5. Category D: Unchecked Boundary Inputs

Boundary conditions guard against invalid states or trigger tier upgrades at exact thresholds.

### Example Surviving Mutant on Boundary (`calculate_discount`)

```diff
--- samples/discount.py (original)
+++ samples/discount.py (MUT_COMP_OP_007)
@@ -13,1 +13,1 @@
-    if quantity >= 5:
+    if quantity < 5:
```

**Reason for Survival:**
At `quantity=2`, `2 < 5` is `True`, so `discount_rate` became `0.10` and `final_price` became `9.0`. Since `assert 9.0 is not None` is true, the inverted boundary condition survived!

**Solution:**
Generate boundary test cases at exact threshold values: $N-1$, $N$, and $N+1$ (e.g., `quantity=4`, `quantity=5`, `quantity=6`).

