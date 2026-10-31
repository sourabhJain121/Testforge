# 03. Representative Mutant Deep-Dive Analysis

**Audit Identifier:** `TF-AUDIT-REPRESENTATIVE-MUTANTS-20261030-173000`  
**Target Code:** `samples/uploaded_logistics_engine.py`  
**Job ID:** `eaaa0e89` (Checkpoint `chk_3921cdba2556`)  

---

## 1. Case Study 1: Volume Discount Boundary Mutation

### A. Original Source Code (Lines 77–83)
```python
    # Volume tier calculation (boundary conditions at 5, 20, 50)
    if quantity >= 50:
        discount += 0.20
    elif quantity >= 20:
        discount += 0.12
    elif quantity >= 5:
        discount += 0.05
```

### B. Mutated Source Code (Mutant `MUT_COMP_OP_042`, Line 78)
```python
    # Comparison Operator Mutation: >= replaced with >
    if quantity > 50:
        discount += 0.20
    elif quantity >= 20:
        discount += 0.12
    elif quantity >= 5:
        discount += 0.05
```

### C. Test Assertion That Should Detect This Change
```python
def test_discount_exact_fifty_boundary():
    # An order of exactly 50 units must receive the 0.20 tier, not 0.12 tier
    rate = calculate_item_discount(unit_price=10.0, quantity=50, customer_tier="REGULAR")
    assert rate == 0.20, f"Expected 0.20 discount for 50 units, got {rate}"
```
- Under clean code: `quantity >= 50` $\to$ `True` $\to$ `rate = 0.20` (PASS).
- Under mutated code: `quantity > 50` $\to$ `False` $\to$ falls into `quantity >= 20` $\to$ `rate = 0.12` $\to$ **AssertionError** (KILLED).

### D. Actual Test Executed During Live Demo
```python
def test_generic_calculate_item_discount():
    try:
        res = calculate_item_discount(1, 1, 1)
        assert res is not None
    except Exception:
        pass
```

### E. Actual Execution Outcome & Classification
- **Pytest Exit Code:** 0
- **Pytest Output:** `test_generic_calculate_item_discount PASSED`
- **Recorded Status:** `SURVIVED`
- **Failure Mechanism:** The test invoked `calculate_item_discount(1, 1, 1)` with `quantity = 1`. This never reached line 78 (`quantity >= 50`). Furthermore, the `except Exception: pass` block would have swallowed an assertion failure even if triggered.

---

## 2. Case Study 2: Freight Handling Base Calculation Mutation

### A. Original Source Code (Line 104)
```python
    # Base formula: $12 flat handling + $0.85/kg + $0.08/km
    base_fee = 12.00 + (weight_kg * 0.85) + (distance_km * 0.08)
```

### B. Mutated Source Code (Mutant `MUT_ARITH_OP_071`, Line 104)
```python
    # Arithmetic Operator Mutation: + replaced with -
    base_fee = 12.00 - (weight_kg * 0.85) + (distance_km * 0.08)
```

### C. Test Assertion That Should Detect This Change
```python
def test_freight_cost_calculation():
    # Weight: 10 kg, Distance: 100 km
    # Expected fee = 12.00 + (10 * 0.85) + (100 * 0.08) = 12.00 + 8.50 + 8.00 = 28.50
    fee = estimate_freight_cost(weight_kg=10.0, distance_km=100.0, is_hazardous=False)
    assert fee == 28.50
```
- Under clean code: `fee = 28.50` (PASS).
- Under mutated code: `fee = 12.00 - 8.50 + 8.00 = 11.50` $\to$ **AssertionError** (KILLED).

### D. Actual Test Executed During Live Demo
```python
def test_generic_estimate_freight_cost():
    try:
        res = estimate_freight_cost(1, 1, 1)
        assert res is not None
    except Exception:
        pass
```

### E. Actual Execution Outcome & Classification
- **Pytest Exit Code:** 0
- **Pytest Output:** `test_generic_estimate_freight_cost PASSED`
- **Recorded Status:** `SURVIVED`
- **Failure Mechanism:** `assert res is not None` evaluates to `True` whether `res` is `28.50` or `11.50`! The assertion only checked that the return value was not `None`, completely ignoring the numeric output.

---

## 3. Case Study 3: Modulo-7 Tracking Number Validation Inversion

### A. Original Source Code (Lines 149–153)
```python
    serial_digits = match.group(2)
    check_digit = int(match.group(3))
    expected_check = sum(int(d) for d in serial_digits) % 7
    return check_digit == expected_check
```

### B. Mutated Source Code (Mutant `MUT_COMP_OP_112`, Line 153)
```python
    # Comparison Inversion: == replaced with !=
    return check_digit != expected_check
```

### C. Test Assertion That Should Detect This Change
```python
def test_tracking_number_modulo7_check():
    # Serial 123456: sum = 1+2+3+4+5+6 = 21. 21 % 7 = 0.
    valid_code = "TRK-EXP-123456-0"
    assert validate_tracking_number(valid_code) is True
```
- Under clean code: `0 == 0` $\to$ `True` (PASS).
- Under mutated code: `0 != 0` $\to$ `False` $\to$ **AssertionError** (KILLED).

### D. Actual Test Executed During Live Demo
```python
def test_generic_validate_tracking_number():
    try:
        res = validate_tracking_number(1)
        assert res is not None
    except Exception:
        pass
```

### E. Actual Execution Outcome & Classification
- **Pytest Exit Code:** 0
- **Pytest Output:** `test_generic_validate_tracking_number PASSED`
- **Recorded Status:** `SURVIVED`
- **Failure Mechanism:** When `validate_tracking_number(1)` was called with integer `1`, `re.match` raised a `TypeError` (expected string or bytes-like object). The `except Exception: pass` block silently caught the `TypeError` and exited cleanly with return code 0!

---

## 4. Case Study 4: SLA Deadline Minimum Cap Substitution

### A. Original Source Code (Lines 169–173)
```python
    # Minimum turnaround is 12 hours regardless of priority
    return max(12, int(total_hours))
```

### B. Mutated Source Code (Mutant `MUT_CONST_VAL_145`, Line 173)
```python
    # Constant Mutation: 12 replaced with 0
    return max(0, int(total_hours))
```

### C. Test Assertion That Should Detect This Change
```python
def test_sla_deadline_urgent_minimum_cap():
    # Priority 1 with 0.1 transit days = 2.4 hours -> capped at 12 hours
    assert compute_sla_deadline_hours(priority=1, transit_days=0.1) == 12
```
- Under clean code: `max(12, 2) == 12` (PASS).
- Under mutated code: `max(0, 2) == 2` $\to$ **AssertionError** (KILLED).

### D. Actual Test Executed During Live Demo
```python
def test_generic_compute_sla_deadline_hours():
    try:
        res = compute_sla_deadline_hours(1, 1)
        assert res is not None
    except Exception:
        pass
```

### E. Actual Execution Outcome & Classification
- **Pytest Exit Code:** 0
- **Pytest Output:** `test_generic_compute_sla_deadline_hours PASSED`
- **Recorded Status:** `SURVIVED`
- **Failure Mechanism:** The test merely checked `res is not None`. Because `12` is not `None` and `2` is not `None`, the mutated code satisfied the assertion.

---

## 5. Analytical Synthesis

| Case Study | Target Function | Mutation Type | Vulnerability in Test Suite | Result in Live Demo |
| :---: | :--- | :---: | :--- | :---: |
| **Case 1** | `calculate_item_discount` | `COMP_OP` | Input did not trigger boundary branch; `except` swallowed error | **SURVIVED** |
| **Case 2** | `estimate_freight_cost` | `ARITH_OP` | Assertion `is not None` ignored return calculation value | **SURVIVED** |
| **Case 3** | `validate_tracking_number` | `COMP_OP` | Bad argument type raised `TypeError`; swallowed by `except` | **SURVIVED** |
| **Case 4** | `compute_sla_deadline_hours` | `CONST_VAL` | Assertion `is not None` ignored numerical boundary value | **SURVIVED** |

**Conclusion:** In all 4 representative cases, the mutants produced genuine behavioral alterations. The 100% survival rate was caused exclusively by the fact that the executed test suite contained trivial `assert res is not None` checks wrapped in universal `except Exception: pass` blocks.

