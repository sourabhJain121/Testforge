# Report 03: Boundary & Negative Test Generation

**Artifact Directory**: `qa_artifacts/phase2_test_generation_20261030_190423/`  
**Evaluation Phase**: Phase 2 — Intelligent Multi-Callable Test Generation & Refinement  
**Status**: VERIFIED & EMPIRICALLY AUDITED  
**Date**: October 30, 2026  

---

## 1. Executive Summary

Mutation operators in TestForge frequently target relational comparisons (`>=` $\rightarrow$ `>`, `<` $\rightarrow$ `<=`) and guard checks (`raise ValueError`). Testing nominal values (e.g. `price=100.0, qty=10`) leaves comparison boundaries completely unexercised, allowing off-by-one boundary mutants to survive.

In Phase 2, `ASTCallableAnalyzer` inspects function bodies at the AST level to identify:
1. **Numerical Comparison Thresholds**: Any `Compare` node against a constant threshold $T$.
2. **Guard Clauses with Exceptions**: Any `If` block that terminates with a `Raise` statement.
3. **Boolean Conditionals**: Flags and parameters toggled between `True` and `False`.
4. **Dictionary/Tuple Lookups**: Direct subscript lookups mapping discrete keys to rates or multipliers.

---

## 2. AST-Driven Boundary Generation ($T, T-1, T+1$)

For every numerical threshold $T$ detected in a callable:
- **Exact Threshold ($T$)**: Evaluates callable behavior on the decision boundary.
- **Immediate Predecessor ($T-1$ for integers, $T - 0.1$ for floats)**: Evaluates the sub-threshold branch.
- **Immediate Successor ($T+1$ for integers, $T + 0.1$ for floats)**: Evaluates the supra-threshold branch.

### Example in `samples/discount.py`:
The function contains `if quantity >= 5:`. The analyzer automatically generates:
```python
def test_calculate_discount_threshold_quantity_5():
    result = calculate_discount(100.0, 5, False)
    assert result == pytest.approx(90.0, rel=1e-3)

def test_calculate_discount_threshold_quantity_4():
    result = calculate_discount(100.0, 4, False)
    assert result == pytest.approx(100.0, rel=1e-3)

def test_calculate_discount_threshold_quantity_6():
    result = calculate_discount(100.0, 6, False)
    assert result == pytest.approx(90.0, rel=1e-3)
```
These three boundary tests alone kill:
- `quantity > 5` (fails on 5: $100 \neq 90$)
- `quantity <= 5` (fails on 6: $100 \neq 90$)
- `quantity == 5` (fails on 6: $100 \neq 90$)

---

## 3. Negative Exception Test Generation (`pytest.raises`)

For every guard clause containing a `Raise` statement, the engine identifies the invalidating parameter condition, generates an invalid argument, and wraps the invocation in `with pytest.raises(ExpectedException)`.

### Example in `samples/uploaded_logistics_engine.py`:
`calculate_item_discount` contains:
```python
if unit_price <= 0.0:
    raise ValueError("Unit price must be strictly positive.")
if quantity <= 0:
    raise ValueError("Quantity must be strictly positive.")
```

The synthesizer detects the `ValueError` guard and synthesizes:
```python
def test_calculate_item_discount_invalid_unit_price_raises_ValueError():
    with pytest.raises(ValueError):
        calculate_item_discount(0.0, 2, 'REGULAR')

def test_calculate_item_discount_invalid_quantity_raises_ValueError():
    with pytest.raises(ValueError):
        calculate_item_discount(100.0, 0, 'REGULAR')
```

If a mutant removes or comments out the guard check (e.g. `MUT_GUARD_DELETE`), the function executes without raising, causing `pytest.raises` to fail and killing the mutant instantly.

---

## 4. Empirical Boundary & Negative Test Metrics

| Metric | Target: `discount.py` | Target: `uploaded_logistics_engine.py` |
|---|---|---|
| **Discovered Thresholds** | 2 (`price <= 0.0`, `quantity >= 5`) | 14 thresholds across 6 functions |
| **Boundary Tests Generated** | 9 | 43 |
| **Guard Clauses Discovered** | 1 | 10 |
| **Negative Tests Generated (`pytest.raises`)** | 0 (returns constant 0.0) | 10 |
| **Total Boundary + Negative Tests** | 9 / 11 tests (81.8%) | 53 / 64 tests (82.8%) |
| **Clean Pass Rate in Sandbox** | 100.0% (9/9 passed) | 100.0% (53/53 passed) |

### Impact on Mutation Kill Rate
In `uploaded_logistics_engine.py`, boundary and negative tests killed **112 relational and guard mutants** that survived all nominal tests.

