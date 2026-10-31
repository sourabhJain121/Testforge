# TestForge: 5-Minute Last-Minute VIVA Cheat Sheet

**Read this document right before entering your oral defense room.**

---

## 1. Key Numbers to Memorize (Quick Facts)

- **Total Regression Suite:** **542 passed, 0 failed** in 277 seconds.
- **`discount.py` Metrics:**
  - 11 generated tests (100% Pass@1).
  - 100.0% statement coverage (10/10 lines).
  - 19 mutants: 17 killed, 2 survived.
  - **89.47%** raw score, **94.44%** adjusted score, **94.7%** live UI score (18/19 killed with LLM).
- **`uploaded_logistics_engine.py` Metrics:**
  - 10/10 eligible callables covered (100.0% callable coverage, 0 skipped).
  - 64 generated tests (100% Pass@1).
  - 90.15% statement coverage (119/132 lines).
  - 258 mutants: 176 killed, 82 survived.
  - **68.22%** raw score, **75.21%** adjusted score (24 equivalent mutants excluded).
- **Active Database:** `qa_artifacts/testforge_checkpoints.db` (**195.36 MB, 1,104 checkpoints across 210 distinct jobs**).
- **Root 0-Byte DBs:** Empty placeholder files; active path set in `server.py:100`.
- **Ports:** Port 8000 (FastAPI active), Port 8501 (Streamlit disabled).

---

## 2. The 30-Second Elevator Pitch

> *"Code coverage only measures execution reachability—not whether your tests actually check anything. A test suite can have 100% line coverage but a 0% mutation score if assertions are empty. TestForge systematically injects synthetic faults into program ASTs and coordinates Google ADK and CrewAI agents over a thread-safe Blackboard to generate value-aware, boundary-driven tests that catch those bugs. Across our benchmarks, TestForge raised mutation scores from 5% to over 89%, backed by 542 passed regression tests and cryptographic SHA-256 suite provenance."*

---

## 3. Core Formulas to Write on the Whiteboard

1. **Statement Coverage:**
   $$\text{Coverage} = \left( \frac{\text{Covered Statements}}{\text{Total Statements}} \right) \times 100\%$$

2. **Raw Mutation Score:**
   $$MS_{\text{raw}} = \left( \frac{M_{\text{killed}}}{M_{\text{total}}} \right) \times 100\%$$

3. **Adjusted (Effective) Mutation Score:**
   $$MS_{\text{adj}} = \left( \frac{M_{\text{killed}}}{M_{\text{total}} - M_{\text{equivalent}}} \right) \times 100\%$$

---

## 4. Key Buzzwords & Instant Definitions

- **AST (Abstract Syntax Tree):** Tree representation of code structure used by compilers to analyze syntax nodes (`ast.Compare`, `ast.If`).
- **Mutation Testing:** Evaluating test suite quality by injecting deliberate syntax faults and checking if tests fail (kill the mutant).
- **RIP Model:** Reachability, Infection, Propagation. Statement coverage only tests Reachability; mutation testing tests all three.
- **Reference Execution:** Safely running clean code in an isolated memory namespace to derive ground-truth return values without LLM hallucinations.
- **Boundary-Value Analysis (BVA):** Generating inputs on the threshold ($T$) and off-by-one ($T-1, T+1$) where bugs cluster.
- **Equivalent Mutant:** A mutant syntactically altered but mathematically identical in behavior to clean code. Cannot be killed by any test.
- **Unreached Mutant:** A mutant on a line never executed. Can be killed if new tests reach it. **Never deduct from adjusted score!**
- **FastMCP:** Anthropic's Model Context Protocol (v1.28.0) exposing tools with path traversal guards (`is_relative_to(SAMPLES_DIR)`).
- **A2A (Agent-to-Agent):** Standardized protocol (v0.3.0) with AgentCards at `/.well-known/agent.json` for inter-agent communication.
- **Blackboard:** Centralized, thread-safe memory space partitioned into 5 domains (`target`, `suite`, `mutant`, `critic`, `metrics`).

---

## 5. The Top 3 Examiner Traps & Exact Rebuttals

### Trap 1: "Isn't reference execution just circular tautology?"
- **Trap:** The examiner claims that testing code against its own output proves nothing.
- **Your Rebuttal:**
  > *"No. The circularity criticism only applies if the clean code is buggy. In automated testing, the current code is the specification, and the test suite's purpose is to act as a **regression barrier**. When mutations alter arithmetic, boundaries, or logic, our tests fail immediately, proving they are sensitive defect detectors, not circular tautologies."*

---

### Trap 2: "Why didn't you achieve 100% mutation score on logistics?"
- **Trap:** The examiner asks why the score was 68.22% instead of 100%.
- **Your Rebuttal:**
  > *"Because real-world code contains equivalent mutants and unreached paths. In logistics, 24 mutants altered rounding precision on whole numbers, making them provably equivalent. When equivalent mutants are deducted, our score is **75.21%**, exceeding our target. Crucially, we refused to deduct the 13 unreached error paths from the denominator because they represent genuine coverage gaps, maintaining scientific integrity."*

---

### Trap 3: "Why is `checkpoints.db` in your root folder 0 bytes?"
- **Trap:** The examiner suspects your database was wiped or lost.
- **Your Rebuttal:**
  > *"That root file is a harmless untracked dummy file from an early script. As defined in `server.py:100`, our active production database is `qa_artifacts/testforge_checkpoints.db`. It is **195 MB** and contains **1,104 immutable checkpoints** spanning 210 distinct jobs, which anyone can inspect live in SQLite or our UI Checkpoints tab."*

