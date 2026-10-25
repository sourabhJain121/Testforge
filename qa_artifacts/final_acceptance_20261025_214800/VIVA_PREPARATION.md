# TESTFORGE — VIVA PREPARATION GUIDE (ARCHITECTURAL DEFENSE)

This guide provides direct, technically precise answers for viva questions and project defense.

---

### Q1: What is TestForge and what problem does it solve?
**Answer:** TestForge is an autonomous test hardening platform. Standard test suites often suffer from high line coverage but low defect detection. TestForge uses **AST mutation testing** combined with **agentic reflection (Generator-Critic loop)** to actively generate edge-case tests, execute them in an isolated sandbox, and prove that subtle defects (mutants) are detected.

---

### Q2: What is the Blackboard Architecture and why did you use it?
**Answer:** The Blackboard pattern separates the shared workspace (the Blackboard) from the autonomous agents (Knowledge Sources). In TestForge, the `Blackboard` holds the target code, AST call graph, generated test suites, and mutation results. When the `GoogleADKTestGenerator` produces tests, it writes them to the Blackboard. The `CrewAICriticAgent` then reads from the Blackboard to evaluate edge cases, and the `ASTMutator` tests the suite against mutants. It decouples the agents, allows asynchronous event monitoring, and supports checkpointing.

---

### Q3: How do you handle Checkpointing and Resumption?
**Answer:** We implement persistent checkpointing using SQLite with Write-Ahead Logging (WAL) in `testforge/persistence.py`. Each lifecycle step (AST parsed, tests generated, sandbox executed, mutants evaluated) creates a serialized JSON snapshot with a SHA-256 hash. If an agent crashes or the job is interrupted, TestForge can restore state from the last valid checkpoint and resume execution without repeating earlier phases.

---

### Q4: How is Model Context Protocol (MCP) integrated?
**Answer:** We run a real FastMCP server (`testforge/mcp_server.py`) exposing two genuine tools:
1. `validate_ast_syntax`: Validates Python syntax and flags dangerous AST nodes.
2. `run_isolated_pytest`: Executes test suites in a temporary sandbox.
The orchestrator uses an async MCP client (`testforge/mcp_client.py`) to discover and call these external tools over standard MCP protocol, with fallback resilience if external processes fail.

---

### Q5: How do CrewAI and Google ADK interact in your system?
**Answer:** 
- **Google ADK / GenAI:** Drives the `GoogleADKTestGenerator` to synthesize high-coverage test cases from target code specifications and call graphs.
- **CrewAI:** Wraps the `CrewAICriticAgent`, which takes the generated tests, assesses edge cases and boundary conditions, and returns structured Pydantic verdicts (`CriticVerdict`) suggesting hardening improvements before execution.

---

### Q6: What are Mutants, and what is the difference between Killed, Survived, and Equivalent mutants?
**Answer:**
- **Mutant:** A syntactically valid copy of the source code with a deliberate minor defect injected (e.g. changing `>=` to `>`).
- **Killed Mutant:** The test suite fails when run against the mutant, proving the tests can detect this defect.
- **Survived Mutant:** The test suite passes despite the defect, revealing a hole in test coverage.
- **Equivalent Mutant:** The mutation changes the syntax but leaves the program's runtime semantics identical (e.g., in `for i in range(0, 10)`, changing `range(0, 10)` to `range(10)`). No test can kill an equivalent mutant. TestForge uses heuristic AST equivalence checks to filter them out.

---

### Q7: What security protections and sandboxing guardrails are implemented?
**Answer:**
1. **AST Safety Filter:** Prohibits malicious code containing `__import__`, `os.system`, `subprocess`, or file deletion.
2. **Path Traversal Protection:** Validates that requested file paths strictly resolve within authorized workspace subdirectories.
3. **Subprocess Sandbox:** Tests run in subprocesses with strict execution timeouts (default 10s), process group killing (`killpg`), and stdout/stderr buffer limits to prevent resource exhaustion attacks.
4. **Secret Scrubbing:** Sensitive API keys (`AIza...`, `sk-or-...`) are automatically redacted from all telemetry traces and logs.

---

### Q8: What were the results of your empirical strategy comparison?
**Answer:** We evaluated three strategies on a controlled defect corpus of 5 realistic software modules:
1. **Baseline (heuristic/initial tests):** Low mutation score (~45–60%), leaves subtle boundary mutants undetected.
2. **Zero-Shot LLM:** Moderate mutation score (~75–80%), generates good happy paths but misses edge cases.
3. **Agentic Reflection (Critic-Mutator loop):** Highest mutation score (90–100%), systematically discovers and closes test coverage gaps through iterative reflection.
