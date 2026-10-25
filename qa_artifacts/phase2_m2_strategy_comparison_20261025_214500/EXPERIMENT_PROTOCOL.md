# TestForge Empirical Strategy Comparison — Experiment Protocol (GAP-05)

## 1. Experimental Objective & Principles

This protocol defines the comparative experimental framework for **Milestone 2.2 (GAP-05)**: an empirical, reproducible, and mathematically rigorous comparison of three automated software testing strategies:
1. **Baseline (`baseline`):** Documented, human-written baseline unit test suites from the evaluation corpus.
2. **Zero-Shot Synthesis (`zeroshot`):** Single-pass autonomous test generation without iterative refinement or critic feedback.
3. **Agentic Reflection (`agentic_reflection`):** Multi-agent mutation-guided reflection loop (Generator + Adversarial Critic), with intermediate test execution and iterative AST fault refinement.

### Core Scientific Principles:
- **Fairness & Uniformity:** Every strategy is evaluated against identical source code, identical defect variants, identical AST mutation pools, and in the identical execution sandbox with uniform timeouts (5.0s per test execution).
- **No Pre-Ordained Superiority:** The experiment does not assume *a priori* that agentic reflection outperforms other methods. Metrics are gathered objectively.
- **Genuine Path Distinction:** Each strategy exercises an independent code path with distinct prompt structures and iteration depths. Simulated results are never labeled as measured.
- **Zero Fabrication Policy:** When running offline or when provider API credentials are unauthorized or absent, token counts and costs are strictly recorded as 0 with explicit disclaimers.

---

## 2. Strategy Execution Specifications

### Strategy 1: Baseline (`baseline`)
- **Source:** Static unit test suite accompanying each corpus fixture (`fixture.baseline_test_code`).
- **Prompt Variant:** `baseline-handwritten-v1`
- **Reflection Iterations:** 0
- **Execution Mechanism:** Evaluated directly in the sandbox against clean reference code, defect variants, and AST mutants.
- **Cost & Tokens:** Always 0 tokens, $0.00 cost.

### Strategy 2: Zero-Shot Synthesis (`zeroshot`)
- **Source:** Autonomous generation via `TestGeneratorAgent(iteration=0)`.
- **Prompt Variant:** `zero-shot-synthesis-v1`
- **Reflection Iterations:** 1 (single-pass synthesis)
- **Feedback Mechanism:** None. Generates assertions based on static function signatures, docstrings, and blast radius without inspecting mutant survival diffs.
- **Cost & Tokens:** Live provider tokens when authorized; 0 tokens and $0.00 cost when executing via offline deterministic synthesis.

### Strategy 3: Agentic Reflection (`agentic_reflection`)
- **Source:** Iterative multi-agent generation loop (`TestGeneratorAgent` + sandbox execution feedback).
- **Prompt Variant:** `multi-agent-reflection-v1`
- **Reflection Iterations:** 2 (Initial pass $\to$ intermediate mutant execution $\to$ surviving mutant AST diff extraction $\to$ refined pass targeting surviving faults).
- **Feedback Mechanism:** Surviving mutant diffs and missing branch logs are fed back into the generator's context.
- **Cost & Tokens:** Cumulative tokens across all iterations when live; 0 tokens and $0.00 cost when running offline.

---

## 3. Evaluation Targets & Fixture Set

Experiments run across the five validated evaluation corpus fixtures:

| Fixture ID | Domain | Module Path | Source SHA-256 | Mutants Pool | Injected Defects |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `task_state_transition` | Finite State Machine / RBAC | `samples/state_machine.py` | `60cdd1dc4281bfbb126831f88d4e8faa99836dcd4caa13daaec563af2ac4140a` | 57 | 3 |
| `token_bucket_rate_limiter` | Rate Limiter / Traffic Shaping | `samples/rate_limiter.py` | `526aeedc9eaa81dac8e7434ef763c153b3ffee47058036e1f4a27e86f665c945` | 38 | 3 |
| `inventory_pricing_calculator` | Commercial Volume Pricing | `samples/inventory_pricing.py` | `2f1d24d285d360d04787878996270eae024e57f92249e0c2721ab8c693384497` | 37 | 3 |
| `banking_operations_module` | Banking Ledger Invariants | `samples/banking.py` | `392c0db3bf364c9d1d2f0efa9f4323e070308b03bbfe02a0161f722690ccc728` | 23 | 3 |
| `currency_converter` | Offline FX Triangulation | `samples/currency_converter.py` | `323534758ae93a42c4a7702a5ff7fb7c6837ad08e6955dadd72dec834a953cde` | 46 | 3 |
| **Total Corpus** | **5 Distinct Engineering Domains** | - | - | **201 Mutants** | **15 Defects** |

---

## 4. Execution Controls & Pilot Scoping

To ensure reproducible execution and prevent unbudgeted API expenditure:
- **Fast Mock Mode (`--fast`):** Deterministic, sub-second AST simulations for CI/CD checks and syntax regression testing. Labeled `SIMULATED_FAST_MOCK` with `is_simulated=True`.
- **Pilot Mode (`--pilot`, `--max-cases N`):** Limits execution to the first $N$ fixtures (e.g. $N=1$ or $2$) to calibrate sandbox timings and observe model behavior before full campaigns.
- **Live Execution Gate (`--force-live`):** Live cloud API generation requires explicit CLI authorization. When not set, the harness defaults to local offline execution (`DETERMINISTIC_BASELINE` and `OFFLINE_DETERMINISTIC_SYNTHESIS`).

---

## 5. Statistical Aggregation & Paired Differences

For repeated runs across fixtures:
- **Descriptive Statistics:** For each strategy, calculate Mean, Median, Min, Max, and sample standard deviation ($s = \sqrt{\frac{1}{n-1}\sum(x_i - \bar{x})^2}$) across defect detection rates, mutation scores, coverage, latency, and false positive rates.
- **Paired Comparisons:** Evaluate paired differences against the baseline strategy on the identical fixture and repetition index:
  $$\Delta MS = MS_{\text{strat}} - MS_{\text{baseline}}$$
  $$\Delta DDR = DDR_{\text{strat}} - DDR_{\text{baseline}}$$
- **Sample Size Disclosure:** With $N=5$ fixtures, asymptotic parametric normality (e.g. standard Student's t-test) cannot be assumed. Paired comparisons are reported with non-parametric caution.
