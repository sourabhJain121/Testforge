# TestForge Metric Definitions & Mathematical Formulations (GAP-05)

## 1. Overview of Metric Categorization

In accordance with strict test-quality and empirical benchmarking standards, every metric recorded by TestForge is categorized into one of three tiers:
1. **Measured:** Direct physical observations from OS timers, compiler exit codes, sandbox execution results, or provider API telemetry headers.
2. **Calculated:** Deterministic mathematical transformations derived strictly from measured metrics.
3. **Estimated:** Projected values based on published external models (e.g. published per-token pricing tables).

---

## 2. Core Metrics & Mathematical Formulations

### 1. Defect Detection Rate ($DDR$)
- **Category:** Calculated
- **Definition:** The percentage of known, controlled defect variants in the fixture manifest that are caught by at least one failing test assertion in the test suite.
- **Formula:**
  $$DDR = \frac{|\mathcal{D}_{\text{detected}}|}{|\mathcal{D}_{\text{total}}|} \times 100\%$$
- **Note:** An arbitrary failure does not constitute detection; the harness traces that the expected contract assertion fails.

### 2. Mutation Score — Raw ($MS_{\text{raw}}$)
- **Category:** Calculated
- **Definition:** The ratio of killed and timed-out mutants to the total evaluable mutant pool.
- **Formula:**
  $$MS_{\text{raw}} = \frac{K + T}{M_{\text{eval}}} \times 100\%$$
  where:
  - $K$: Count of mutants killed by test suite assertion failures or errors.
  - $T$: Count of mutants causing execution timeouts (e.g., infinite loops).
  - $M_{\text{eval}} = K + S + T + E$ (evaluable mutants).
  - $S$: Mutants surviving all test executions.
  - $E$: Verified or potentially equivalent mutants.
- **Critical Exclusion:** Invalid mutants ($I$), which fail compilation or introduce syntax errors, are **strictly excluded** from $M_{\text{eval}}$.

### 3. Mutation Score — Adjusted ($MS_{\text{adj}}$)
- **Category:** Calculated
- **Definition:** The mutation score after removing verified equivalent mutants from the evaluable denominator.
- **Formula:**
  $$MS_{\text{adj}} = \frac{K + T}{M_{\text{eval}} - E} \times 100\%$$
- **Note:** If all evaluable mutants are equivalent and none were killed, $MS_{\text{adj}} = 100.0\%$.

### 4. Valid Generated Test Count ($T_{\text{valid}}$)
- **Category:** Measured
- **Definition:** The number of syntactically valid pytest test functions collected by the sandbox runner (`tests_collected`).

### 5. False Positive Rate ($FPR$)
- **Category:** Calculated
- **Definition:** The proportion of generated tests that fail when executed against the **correct, unmutated reference code**.
- **Formula:**
  $$FPR = \frac{T_{\text{failed\_ref}}}{T_{\text{collected}}} \times 100\%$$
- **Significance:** A high mutation score accompanied by a high false positive rate indicates that the test generator wrote hallucinated or incorrect assertions rather than genuine specification tests.

### 6. Test Generation Success Rate
- **Category:** Calculated
- **Definition:** Proportion of generation attempts that result in syntactically parseable, executable Python test suites without fatal engine crashes.

### 7. Runtime & Timeout Accounting
- **Category:** Measured
- **Runtime ($t_{\text{wall}}$):** Monotonic wall-clock elapsed time measured via `time.perf_counter()`.
- **Timeouts ($T$):** Count of individual mutant evaluations or suite executions that exceed the sandbox hard timeout (default: 5.0 seconds). Treated as killed mutants ($K + T$) in mutation score calculations.

### 8. Iterations & Retries
- **Category:** Measured
- **Reflection Iterations ($I_{\text{refl}}$):** Total passes through the generator-critic feedback loop (0 for baseline, 1 for single-pass zero-shot, 2 for reflective hardening).
- **Retries ($R$):** Count of re-prompting attempts due to transient provider rate limits (HTTP 429) or transient 503 errors.

### 9. Token Accounting & Estimated Cost
- **Category:** Measured (Tokens) & Estimated (Cost)
- **Tokens ($N_{\text{prompt}}$, $N_{\text{comp}}$):** Exact integer counts of prompt and completion tokens reported by provider telemetry. In offline deterministic modes, tokens are strictly recorded as $0$.
- **Estimated Cost ($C_{\text{USD}}$):** Derived from published pricing rates per 1,000,000 tokens:
  $$C_{\text{USD}} = \frac{N_{\text{prompt}}}{10^6} \times P_{\text{prompt}} + \frac{N_{\text{comp}}}{10^6} \times P_{\text{comp}}$$
  Published rates:
  - Gemini 3.6 Flash / 2.5 Flash: $P_{\text{prompt}} = \$0.075$, $P_{\text{comp}} = \$0.30$.
  - Gemini 1.5 Pro: $P_{\text{prompt}} = \$1.25$, $P_{\text{comp}} = \$5.00$.

---

## 3. Treatment of Mutants and Equivalence

| Mutant State | Description | In Evaluable Denominator? | In Numerator? |
| :--- | :--- | :--- | :--- |
| **KILLED** | Failed assertion or exception under test suite | **YES** | **YES** |
| **TIMEOUT** | Sandbox timeout (infinite loop / recursion) | **YES** | **YES** |
| **SURVIVED** | All tests passed; mutant undetected | **YES** | **NO** |
| **EQUIVALENT** | Semantically identical to reference (AST dead code, identity) | **YES** (Raw) / **NO** (Adjusted) | **NO** |
| **INVALID** | Syntax error or compilation failure | **NO** (Excluded) | **NO** |
