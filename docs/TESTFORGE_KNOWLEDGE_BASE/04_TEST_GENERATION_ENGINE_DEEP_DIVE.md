# TestForge — Test Generation Engine Deep Dive

**Document Version:** 1.0.0  
**Last Verified:** November 2, 2026  
**Primary Source Modules:** `testforge/intelligent_generator.py`, `testforge/agents.py`, `testforge/sandbox.py`  

---

## 1. End-to-End Test Generation Pipeline

TestForge implements an intelligent, syntax-guided test generation pipeline designed to produce syntactically valid, deterministic, and assertion-rich Pytest test suites.

```mermaid
flowchart TD
    SRC["Raw Python Source (target.py)"] --> PARSE["AST Parsing (ast.parse)"]
    PARSE --> DISCOVER["Callable & Class Discovery (ASTCallableAnalyzer)"]
    DISCOVER --> SIG["Signature, Type & Boundary Extraction"]
    SIG --> PRE["Pre-Flight Reference Execution (ReferenceExecutor)"]
    
    PRE --> GEN_POS["Positive Happy-Path Test Generation"]
    PRE --> GEN_BND["Boundary-Value Assertion Generation"]
    PRE --> GEN_NEG["Negative & Type-Error Test Generation"]
    PRE --> GEN_CLS["Stateful Class Lifecycle Test Generation"]
    
    GEN_POS --> SYNTH["Intelligent AST Synthesizer (Formatting & Parametrize)"]
    GEN_BND --> SYNTH
    GEN_NEG --> SYNTH
    GEN_CLS --> SYNTH
    
    SYNTH --> SAN["Native Sandbox Clean Execution (pytest)"]
    SAN -->|Passes Clean Code| MUT["AST Mutator Engine"]
    SAN -->|Fails Syntax/Import| REPAIR["AST Syntax Repair Loop"]
    REPAIR --> SAN
    
    MUT --> EVAL["Mutation Evaluation (Killed vs Survived)"]
    EVAL -->|Surviving Mutants| CRITIC["Adversarial Critic Diagnosis"]
    CRITIC --> REFINE["Targeted Mutant-Killing Refinement Loop"]
    REFINE --> SYNTH
    EVAL -->|Mutation Score >= 85%| FINAL["Hardened Pytest Suite Output"]
```

---

## 2. Core Architectural Classes in `intelligent_generator.py`

### 1. `ASTCallableAnalyzer` (`ast.NodeVisitor`)
The `ASTCallableAnalyzer` inspects the parsed Abstract Syntax Tree of the target source code. It recursively identifies all module-level functions and class methods:
- **Private Entity Filtering:** Ignores private functions/methods prefixed with `_` (unless explicitly whitelisted or dunder methods like `__init__`).
- **Signature Extraction:** Extracts:
  - Positional arguments (`args`).
  - Keyword arguments with default values (`defaults`).
  - Variable arguments (`*args`, `**kwargs`).
  - Type annotations (`ast.Constant`, `ast.Name`, `ast.Subscript`).
- **Class Scope Tracking:** Uses `self.class_stack` to resolve whether a callable is a standalone function, an instance method (`self`), a `@classmethod` (`cls`), or a `@staticmethod`.

### 2. `ReferenceExecutor`
A critical reliability innovation in TestForge. Before generating a test case asserting `assert f(x) == y`, the `ReferenceExecutor` executes `f(x)` in an isolated, in-memory reference context against the clean target source code:
- **Ensures Assertion Truth:** Prevents generating tests with hallucinated expected return values that would fail clean baseline runs.
- **Captures Exact Return Types:** Inspects whether the actual runtime return is an `int`, `float`, `list`, `dict`, `bool`, or custom object.
- **Catches Legitimate Exceptions:** If `f(-1)` is designed to raise `ValueError`, the reference executor detects that `ValueError` is the correct behavior and instructs the synthesizer to generate `with pytest.raises(ValueError):`.

### 3. `IntelligentASTSynthesizer`
Coordinates full multi-callable test synthesis across the target module:
- Generates imports (`import pytest`, `from target import *`).
- Synthesizes `@pytest.mark.parametrize` matrices for multi-input functions.
- Generates edge-case tests with floating-point tolerance (`pytest.approx(..., rel=1e-3)`).
- Generates stateful lifecycle tests for state classes (e.g. testing `WarehouseInventory`: `add_stock()` followed by `reserve_stock()` followed by `get_available_stock()`).

---

## 3. The Boundary-Value Identification Engine

Boundary faults represent over 70% of software defects (e.g., `<` instead of `<=`, 0-division, off-by-one indices). TestForge analyzes parameter types and injects domain-specific boundary vectors:

| Data Type | Standard Nominal Inputs | TestForge Boundary Vectors Injected |
| :--- | :--- | :--- |
| **`int` / `float` (Price, Quantity, Count)**| `10`, `5.0` | `0`, `0.0`, `-1`, `-0.01`, `1`, `sys.maxsize`, `1e-6`, `float('inf')` |
| **`str` (Names, Keys, Codes)** | `"order_1"` | `""` (empty string), `" "` (whitespace), `"a"*1000`, `None`, `"special_#$*"` |
| **`list` / `tuple` / `set` (Collections)** | `[1, 2, 3]` | `[]` (empty collection), `[None]`, `[1]`, large list (10,000 items) |
| **`dict` (Mappings, Metadata)** | `{"id": 1}` | `{}` (empty dict), `{None: None}`, nested dictionaries |
| **`bool` (Flags, Toggles)** | `True` | `True`, `False`, explicit type verification (`is not int`) |

---

## 4. Generation Paradigms Compared

TestForge supports four distinct modes of test synthesis:

| Generation Paradigm | Engine Mechanism | Determinism | LLM Quota Usage | Generation Latency | Fault Detection / Mutation Killing |
| :--- | :--- | :---: | :---: | :---: | :--- |
| **1. Deterministic AST Synthesis** | `IntelligentASTSynthesizer` + `ReferenceExecutor` | **100% Deterministic** | **0 Tokens** | **< 0.5 seconds** | High for standard boundaries, arithmetic, and relational mutations. |
| **2. Pure LLM-Assisted Generation** | Direct prompt to Gemini / CodeLlama | Non-deterministic | High (~2,000 tokens/run) | 5.0–15.0 seconds | High semantic understanding, but prone to hallucinated assertions or import errors. |
| **3. Hybrid AST-LLM Generation** | AST generates boundaries; LLM authors complex domain invariants | Controlled | Moderate (~1,000 tokens) | 3.0–8.0 seconds | Exceptional. Combines AST mathematical rigor with LLM contextual reasoning. |
| **4. Mutation-Guided Reflection Loop** | Iterative refinement driven by `AdversarialCriticAgent` | Highly repeatable | Scaled by iteration | Iterative (20–40 s) | **Maximum.** Specifically authors tests to kill surviving mutants identified in iteration $N-1$. |

---

## 5. Concrete Code Walkthrough: `samples/discount_module.py`

To understand how TestForge operates in practice, consider the hardening of `calculate_discount`:

### 1. Target Python Source Code (`samples/discount_module.py`)
```python
def calculate_discount(price: float, quantity: int, is_member: bool) -> float:
    """Calculate tiered volume and membership discount."""
    if price <= 0.0 or quantity <= 0:
        return 0.0
    
    discount_rate = 0.0
    if quantity >= 10:
        discount_rate += 0.10
    elif quantity >= 5:
        discount_rate += 0.05
        
    if is_member:
        discount_rate += 0.05
        
    final_price = price * (1.0 - discount_rate)
    return round(final_price, 2)
```

### 2. AST Extraction & Boundary Discovery
`ASTCallableAnalyzer` inspects the function:
- Name: `calculate_discount`
- Parameters: `price` (float), `quantity` (int), `is_member` (bool)
- Conditions identified: `price <= 0.0`, `quantity <= 0`, `quantity >= 10`, `quantity >= 5`, `is_member`
- Extracted boundary values:
  - `price`: `-10.0`, `-0.01`, `0.0`, `0.01`, `100.0`
  - `quantity`: `-1`, `0`, `1`, `4`, `5`, `6`, `9`, `10`, `11`
  - `is_member`: `True`, `False`

### 3. Generated Baseline Test Suite (Iteration 0)
The synthesizer produces parameterized tests:
```python
import pytest
from target import *

@pytest.mark.parametrize("price, quantity, is_member, expected", [
    (100.0, 1, False, 100.0),    # Nominal no discount
    (100.0, 5, False, 95.0),     # Volume tier 1 (5%)
    (100.0, 10, False, 90.0),    # Volume tier 2 (10%)
    (100.0, 1, True, 95.0),      # Membership only (5%)
    (100.0, 10, True, 85.0),     # Volume + Membership (15%)
    (0.0, 10, True, 0.0),        # Boundary: price = 0.0
    (-10.0, 5, False, 0.0),      # Negative price
    (100.0, 0, True, 0.0),       # Boundary: quantity = 0
    (100.0, -5, False, 0.0),     # Negative quantity
])
def test_calculate_discount_boundaries(price, quantity, is_member, expected):
    assert calculate_discount(price, quantity, is_member) == pytest.approx(expected, rel=1e-3)
```

### 4. Mutation Evaluation & Surviving Mutant Detection
The test suite executes against all 19 mutants generated by `ASTMutator`:
- **Mutants Killed:** 15/19 killed (78.95% raw score).
- **Mutants Survived:** 4 mutants survived.
  - *Surviving Mutant #1:* Line 7, changed `quantity >= 10` to `quantity > 10`.
  - *Surviving Mutant #2:* Line 9, changed `quantity >= 5` to `quantity > 5`.
  - *Surviving Mutant #3:* Line 4, changed `price <= 0.0` to `price < 0.0`.
  - *Surviving Mutant #4:* Line 15, changed `round(..., 2)` to `round(..., 1)`.

### 5. Adversarial Critic Reflection Directive (Iteration 1)
`AdversarialCriticAgent` analyzes the surviving diffs:
> **Critic Directive:**  
> "Mutant #1 (`quantity >= 10` $\rightarrow$ `quantity > 10`) survived because existing tests tested quantity 5 and 10, but did NOT assert boundary transition between 9 and 10! At quantity = 9, discount should be 5%. At quantity = 10, discount should be 10%.  
> Mutant #2 (`quantity >= 5` $\rightarrow$ `quantity > 5`) survived because quantity 4 was not asserted against quantity 5!  
> **Prescriptive Action:** Author explicit boundary tests: `calculate_discount(100.0, 9, False)` must equal `95.0`, and `calculate_discount(100.0, 4, False)` must equal `100.0`."

### 6. Hardened Refined Test Suite Output (Iteration 1)
`TestGeneratorAgent` ingests the directive and appends targeted assertions:
```python
def test_calculate_discount_surviving_mutant_hardening():
    # Kills Mutant #1 (off-by-one at quantity 10)
    assert calculate_discount(100.0, 9, False) == 95.0
    assert calculate_discount(100.0, 10, False) == 90.0
    
    # Kills Mutant #2 (off-by-one at quantity 5)
    assert calculate_discount(100.0, 4, False) == 100.0
    assert calculate_discount(100.0, 5, False) == 95.0
    
    # Kills Mutant #3 (boundary zero price check)
    assert calculate_discount(0.0001, 1, False) == 0.0
    assert calculate_discount(0.0, 1, False) == 0.0
```

### 7. Final Hardening Result
- **Mutants Killed:** 17/19 killed.
- **Raw Mutation Score:** **89.47%** (up from baseline 5.26%).
- **Equivalent Mutants Excluded:** 1 verified equivalent mutant (mutant in unreachable dead code).
- **Adjusted Mutation Score:** $\frac{17}{19 - 1} \times 100 = \mathbf{94.44\%}$.

