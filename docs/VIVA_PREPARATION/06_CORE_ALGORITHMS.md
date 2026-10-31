# TestForge: Core Algorithms & Theoretical Foundations

**Document Purpose:** Clear, beginner-friendly explanations backed by rigorous mathematical formulas and source code examples for oral examination (VIVA).  
**Primary Fixtures Used:** `samples/discount.py` and `samples/uploaded_logistics_engine.py`.  

---

## 1. Abstract Syntax Trees (AST) & Static Analysis

### 1.1 What is an AST?
An **Abstract Syntax Tree (AST)** is the hierarchical, tree-structured representation of source code produced by a compiler parser. Instead of viewing Python code as a raw string of text, Python's built-in `ast` module parses it into semantic syntax nodes (e.g. `FunctionDef`, `If`, `Compare`, `BinOp`, `Return`).

```
Source Code:              AST Hierarchy:
if price <= 0.0:          If(
    return 0.0                test=Compare(
                                  left=Name(id='price'),
                                  ops=[LtE()],
                                  comparators=[Constant(value=0.0)]
                              ),
                              body=[Return(value=Constant(value=0.0))]
                          )
```

### 1.2 How TestForge Uses the AST
In `testforge/intelligent_generator.py`:
- `ast.parse(source_code)` builds the syntax tree.
- `ASTCallableAnalyzer(ast.NodeVisitor)` walks through the tree to discover:
  - Function and method signatures (`CallableInfo`).
  - Parameter annotations (`int`, `float`, `str`, `bool`).
  - Comparison operators (`<`, `<=`, `>`, `>=`, `==`, `in`).
  - Numerical thresholds (e.g. quantity $5$, customs value $\$800$).
  - Guard clauses ending in `Raise` (e.g. `raise ValueError`).

---

## 2. Callable Discovery & Signature Extraction

### 2.1 Top-Level Functions vs. Class Methods
A common pitfall in naive test generators is failing to distinguish between module-level functions and class methods:
- **Module Function:** Called directly: `calculate_discount(100.0, 5, False)`.
- **Instance Method:** Requires creating an instance receiver first:
  ```python
  inv = WarehouseInventory(total_stock=100)
  inv.reserve_stock(quantity=10)
  ```
- **Class / Static Method:** Invoked on the class directly: `ShippingTier.classify(...)`.

### 2.2 Algorithm: AST Method Classification
In `IntelligentASTSynthesizer._parse_callable()`:
1. Checks `decorator_list`: `@staticmethod` $\implies$ `staticmethod`, `@classmethod` $\implies$ `classmethod`.
2. Checks first argument:
   - If argument is `self` $\implies$ classify as `instance` method (strip `self` from callable parameter list).
   - If argument is `cls` $\implies$ classify as `classmethod` (strip `cls`).
3. Dunder methods (`__init__`, `__repr__`) and private methods (`_internal`) are filtered out with explicit ineligibility reasons.

---

## 3. Boundary-Value Analysis (BVA) & Input Synthesis

### 3.1 The Boundary-Value Hypothesis
Bugs in software cluster overwhelmingly around **decision boundaries** (relational conditions like `<` vs `<=`, off-by-one errors).

For any relational threshold $T$ extracted from an AST condition (`if x >= T`):
- **On-Boundary ($T$):** The exact threshold value.
- **Off-Boundary ($T - 1$):** Immediately below the threshold.
- **Off-Boundary ($T + 1$):** Immediately above the threshold.
- **Extreme / Edge:** $0$, $-1$, empty string `""`, empty list `[]`.

### 3.2 Real TestForge Example from `discount.py`
In `discount.py`:
```python
if quantity >= 5:
    discount_rate = discount_rate + 0.10
```
`ASTCallableAnalyzer` extracts threshold $T = 5$ on parameter `quantity`. The generator automatically synthesizes:
1. `test_calculate_discount_threshold_quantity_5`: Tests $quantity = 5 \implies$ verifies 10% discount applied.
2. `test_calculate_discount_threshold_quantity_4`: Tests $quantity = 4 \implies$ verifies 0% discount (kills boundary swap mutants).
3. `test_calculate_discount_threshold_quantity_6`: Tests $quantity = 6 \implies$ verifies 10% discount.

---

## 4. Safe Pre-Flight Reference Execution (`ReferenceExecutor`)

### 4.1 The LLM Oracle Hallucination Problem
When an ordinary LLM generates tests, it frequently **hallucinates expected values** (e.g. guessing that freight shipping cost is `$45.00` when the actual formula returns `$47.15`). If the assertion is wrong, the test fails on clean code!

### 4.2 TestForge's Solution
TestForge implements `ReferenceExecutor` in `testforge/intelligent_generator.py`:
1. Compiles the target code in an isolated dictionary:
   ```python
   exec(compile(source_code, "<reference_target>", "exec"), clean_env)
   ```
2. Executes candidate inputs against the **clean reference implementation** in memory before emitting the test code.
3. If the clean code returns a value $V$, the test emits `assert res == V` (or `pytest.approx(V)` for floats).
4. If the clean code raises an expected exception $E$, the test emits `with pytest.raises(E):`.

**Result:** Zero hallucinated expected values. 100% Pass@1 pass rate on clean code.

---

## 5. Mutation Operators & Fault Injection

An **AST Mutation Operator** is a syntactic rule that systematically transforms a clean AST node into a faulty AST node.

TestForge implements 9 operator classes in `testforge/mutator.py`:

| Operator Class | Original AST Node | Mutated AST Node | Real Example from TestForge |
| :--- | :--- | :--- | :--- |
| **`ARITH_OP`** | `+`, `-`, `*`, `/` | Binary arithmetic swapped | `self.reserved += qty` $\to$ `self.reserved -= qty` |
| **`COMP_OP`** | `<`, `<=`, `>`, `>=` | Relational operator swapped | `quantity <= 0` $\to$ `quantity < 0` |
| **`BOUNDARY_SWAP`**| `<=` $\leftrightarrow$ `<`, `>=` $\leftrightarrow$ `>` | Exact boundary boundary shifted | `price <= 0.0` $\to$ `price < 0.0` |
| **`COND_INV`** | `if condition:` | `if not (condition):` | `if is_member:` $\to$ `if not (is_member):` |
| **`LOGICAL_CONN`** | `and` $\leftrightarrow$ `or` | Short-circuit connector inverted | `w <= 0 or d <= 0` $\to$ `w <= 0 and d <= 0` |
| **`CONST_VAL`** | `Constant(val)` | Perturbed numeric value | `max(0, stock)` $\to$ `max(1, stock)` |
| **`MATH_FUNC`** | `round(val, 2)` | Precision altered | `round(val, 2)` $\to$ `round(val, 1)` |
| **`OFF_BY_ONE`** | `x <= 0` | `x <= 1` | Off-by-one boundary shift |
| **`RETURN_VAL`** | `return True` | `return False` | Inverted boolean return |

---

## 6. Mutation Score Formulas: Raw vs. Adjusted

### 6.1 Raw Mutation Score ($MS_{\text{raw}}$)

$$MS_{\text{raw}} = \left( \frac{M_{\text{killed}}}{M_{\text{total}}} \right) \times 100\%$$

Where:
- $M_{\text{killed}}$ = Number of mutants that caused at least one test in the suite to fail.
- $M_{\text{total}}$ = Total number of syntactically valid mutants injected.

### 6.2 Adjusted (Effective) Mutation Score ($MS_{\text{adj}}$)
In academic literature (Jia & Harman, 2011), **equivalent mutants** cannot be killed by any test because they do not change the program's output semantics. They must be deducted from the denominator:

$$MS_{\text{adj}} = \left( \frac{M_{\text{killed}}}{M_{\text{total}} - M_{\text{equivalent}}} \right) \times 100\%$$

---

## 7. Equivalent Mutants vs. Unreached Mutants

A critical distinction required during oral evaluation:

```
┌────────────────────────────────────────────────────────────────────────┐
│                   Mutant Classification Hierarchy                     │
├───────────────────────────────┬────────────────────────────────────────┤
│ Equivalent Mutant             │ Unreached Mutant                       │
├───────────────────────────────┼────────────────────────────────────────┤
│ Syntactically different, but  │ Mutated line was never executed by the │
│ semantically identical to the │ test suite (statement coverage gap).   │
│ original code.                │                                        │
│ Cannot be killed by any test! │ Can be killed if new tests cover it!   │
│ Deducted from denominator in  │ KEPT in denominator! Cannot be called  │
│ adjusted score.               │ equivalent!                            │
└───────────────────────────────┴────────────────────────────────────────┘
```

### Empirical Proof for `MUT_BOUNDARY_SWAP_003` in `discount.py`
In `discount.py`:
- Original: `if price <= 0.0: return 0.0`
- Mutated: `if price < 0.0: return 0.0`
- **Case 1: $price < 0.0$:** Both return `0.0`.
- **Case 2: $price > 0.0$:** Both execute downstream code identically.
- **Case 3: $price = 0.0$:**
  - Original condition `0.0 <= 0.0` is True $\implies$ returns `0.0`.
  - Mutated condition `0.0 < 0.0` is False $\implies$ executes:
    `final_price = 0.0 * (1.0 - 0.0) = 0.0` $\implies$ returns `round(0.0, 2) = 0.0`.
- **Mathematical Conclusion:** $\forall price \in \mathbb{R}, f_{\text{mutant}}(price) = f_{\text{original}}(price)$. The mutant is **provably equivalent**.

---

## 8. Cryptographic Suite Provenance via SHA-256

To prevent human test editing or synthetic tampering:
1. When candidate test code is generated, TestForge computes:
   $$\text{Hash} = \text{SHA256}(\text{test\_code.encode('utf-8')})$$
2. Invariant enforced by `Orchestrator`:
   $$\text{Candidate Hash} = \text{Validated Hash} = \text{Exported Hash} = \text{Sandbox Hash}$$
3. Any alteration to whitespace, variable names, or assertions changes the 64-character hex digest, triggering an immediate security provenance failure.

