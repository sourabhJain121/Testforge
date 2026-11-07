import sys

code = '''"""
content_additional_and_defense.py - Additional Defense Questions (Q115-Q135) and Chapters 26 to 31.
"""

import docx
from .styles import add_viva_question, add_h1, add_h2, add_h3, add_p, add_bullet, add_callout, add_code_block, add_styled_table

ADDITIONAL_QUESTIONS = [
    {
        "q_num": 115,
        "question": "Why is mutation testing strictly superior to relying solely on code coverage?",
        "short_answer": "Code coverage only proves Reachability in the RIP model—that lines were executed—without verifying whether any assertions tested the result. Mutation testing evaluates Reachability, Infection, and Propagation, proving that test assertions actually catch semantic bugs.",
        "detailed_explanation": "A test suite can achieve 100% statement and branch coverage by calling functions without containing a single `assert` statement. Such a test suite provides zero fault-detection capability. Mutation testing injects deliberate AST modifications (mutants). If a mutant causes no test to fail, the mutant survives, exposing a weak or missing assertion. Mutation testing is therefore an empirical measurement of test oracle quality.",
        "implementation": "Demonstrated across `testforge/mutator.py` and `testforge/sandbox.py`. In `discount.py`, naive tests had 100% line coverage but a 5.26% mutation score (1/19 killed).",
        "example": "`def add(a, b): return a + b`. A test calling `add(2, 3)` with no assert has 100% coverage. Changing `+` to `-` produces mutant `a - b`. With `assert add(2, 3) == 5`, the mutant is killed.",
        "why_design": "Software industry defect escapes often happen in 100%-covered code due to missing boundary assertions. Mutation testing closes this oracle gap.",
        "follow_up": "Examiner: 'If mutation testing is superior, why isn\\'t it universally used in industry?' Answer: Computational cost. Evaluating N mutants requires running the test suite N times. TestForge solves this through parallel AST sandboxing and incremental delta execution.",
        "evidence_status": "Verified Evaluation in `MUTATION_TESTING_REPORT.md` and `TECHNICAL_REPORT.md` Section 4."
    },
    {
        "q_num": 116,
        "question": "Why was a multi-agent architecture chosen over a single monolithic LLM prompt?",
        "short_answer": "A multi-agent architecture enforces separation of concerns, adversarial tension, modular debugging, and independent retry/fallback boundaries that a single monolithic prompt cannot provide.",
        "detailed_explanation": "When a single LLM is asked to both write code and verify its own work in one prompt, confirmation bias causes it to overlook its own errors. By separating roles into a Test Generator Agent (constructive role) and an Adversarial Critic Agent (auditing role) mediated by an Orchestrator FSM and Blackboard, TestForge creates adversarial tension: the Critic actively hunts for surviving mutants and challenges the Generator's tests.",
        "implementation": "`testforge/agents.py:TestGeneratorAgent`, `testforge/agents.py:AdversarialCriticAgent`, and `testforge/orchestrator.py:TaskLifecycleFSM`.",
        "example": "Single prompt: 'Write tests and check if they kill mutants' -> generates trivial tests. Multi-agent: Critic analyzes survivor diffs and issues concrete `CriticDirectivePayload` directives.",
        "why_design": "Decoupling roles allows specialized prompt engineering, independent token budgets, and seamless fallback to deterministic rule engines per agent.",
        "follow_up": "Examiner: 'Does multi-agent add latency?' Answer: By using an in-process memory Blackboard with `RLock`, inter-agent state sharing adds <0.5ms latency, far outweighed by the 17x gain in fault detection.",
        "evidence_status": "Verified Implementation in `testforge/agents.py` and `testforge/orchestrator.py`."
    },
    {
        "q_num": 117,
        "question": "Why are Google ADK and CrewAI integrated together in TestForge?",
        "short_answer": "Google ADK provides specialized prompt generation and Gemini model bindings, while CrewAI provides hierarchical role definitions and collaborative task orchestration, giving TestForge best-of-breed agentic capabilities.",
        "detailed_explanation": "Google ADK excels at structured code reasoning and direct Gemini API integration, but lacks declarative team coordination abstractions. CrewAI excels at role modeling (`Agent`, `Task`, `Crew`) and collaborative workflows. TestForge integrates both frameworks behind unified adapter interfaces, allowing the Orchestrator to dispatch tasks through CrewAI crews or Google ADK pipelines interchangeably.",
        "implementation": "`testforge/agents.py:GoogleADKTestGenerator` and `testforge/agents.py:CrewAITeamCoordinator`.",
        "example": "CrewAI defines `Agent(role='Adversarial Auditor', goal='Find surviving mutants')`, while Google ADK formats AST signatures into high-context Gemini code prompts.",
        "why_design": "Enables multi-framework interoperability without vendor lock-in, demonstrating academic architectural breadth.",
        "follow_up": "Examiner: 'What if either library is missing?' Answer: TestForge wraps both in lazy try/except imports and provides a native zero-dependency `HybridLLMClient` fallback.",
        "evidence_status": "Verified Implementation in `testforge/agents.py` lines 80–220."
    },
    {
        "q_num": 118,
        "question": "What is the architectural difference between the A2A protocol and MCP in TestForge?",
        "short_answer": "A2A (Agent-to-Agent) governs horizontal communication between peer intelligent agents (negotiation, directives, critiques), whereas MCP (Model Context Protocol) governs vertical integration between agents and environmental external tools (filesystems, git repositories).",
        "detailed_explanation": "A2A is an application-level agent interaction protocol using AgentCards and performatives (`INFORM`, `REQUEST`, `PROPOSE`) for peer-to-peer cognitive collaboration. MCP is an open standard protocol (JSON-RPC) for exposing tool endpoints to models. In TestForge, the Critic and Generator converse via A2A messages, while both agents read source files and git commits by calling FastMCP server tools.",
        "implementation": "`testforge/a2a.py` (A2A Broker & AgentCard) and `testforge/mcp_server.py` (FastMCP Filesystem & GitHub servers).",
        "example": "A2A: Critic sends `CriticDirectivePayload` to Generator via `A2AMessage(performative='REQUEST')`. MCP: Generator calls `read_text_file(path='discount.py')` over MCP stdio.",
        "why_design": "Separates cognitive coordination (agent-to-agent) from tool execution (agent-to-environment), adhering to modern distributed systems principles.",
        "follow_up": "Examiner: 'Could A2A run over HTTP?' Answer: Yes. TestForge includes an in-process `A2ABroker` for zero-latency local execution, and an HTTP A2A transport layer in `server.py` for distributed nodes.",
        "evidence_status": "Verified Implementation in `testforge/a2a.py` and `testforge/mcp_server.py`."
    },
    {
        "q_num": 119,
        "question": "Why is a Blackboard architecture needed instead of direct point-to-point agent messaging?",
        "short_answer": "A Blackboard decouples agents through shared, structured state spaces (`TargetSpace`, `SuiteSpace`, `MutantSpace`, `CriticSpace`, `MetricsSpace`), eliminating point-to-point N*(N-1) communication complexity and providing a single source of truth for checkpointing.",
        "detailed_explanation": "In point-to-point architectures, every agent must know the network address, state, and API of every other agent. As agents are added, communication complexity scales quadratically. With a Blackboard, agents inspect partitioned spaces, post contributions when conditions are met, and remain completely decoupled. Furthermore, saving the Blackboard captures the entire system state in one atomic SQLite snapshot.",
        "implementation": "`testforge/blackboard.py:Blackboard` and `testforge/models.py`.",
        "example": "Mutator writes mutants to `MutantSpace`. Sandbox runner updates mutant status to `Killed`. Critic reads survivors from `MutantSpace` and writes to `CriticSpace`. Neither agent calls the other directly.",
        "why_design": "Enables asynchronous, non-blocking agent participation and simplifies fault recovery and transaction rollbacks.",
        "follow_up": "Examiner: 'How is data consistency maintained?' Answer: Via a reentrant lock (`threading.RLock()`) guarding all read and write operations on blackboard partitions.",
        "evidence_status": "Verified Implementation in `testforge/blackboard.py`."
    },
    {
        "q_num": 120,
        "question": "Why is AST analysis used instead of regex or raw string manipulation for test generation?",
        "short_answer": "AST analysis provides exact syntactic and semantic understanding of Python code structures (parameters, default values, comparison operators, exception types), guaranteeing 100% syntactically valid code and precise boundary extraction.",
        "detailed_explanation": "Regex pattern matching fails on multi-line function headers, nested brackets, type annotations, and string literals containing code-like text. Python's `ast` module compiles code into an official Abstract Syntax Tree, allowing TestForge to extract exact callable signatures, parameter kinds (`POSITIONAL_OR_KEYWORD`, `VAR_KEYWORD`), relational operators, and literal constants.",
        "implementation": "`testforge/ast_analyzer.py:ASTCallableAnalyzer` and `testforge/synthesizer.py:IntelligentASTSynthesizer`.",
        "example": "AST: `ast.Compare(left=ast.Name(id='x'), ops=[ast.Gt()], comparators=[ast.Constant(value=100)])` reveals exact boundary points: 99, 100, 101.",
        "why_design": "Eliminates syntax errors, prevents false regex matches inside comments, and enables automated boundary value calculation.",
        "follow_up": "Examiner: 'What if the user passes invalid Python code?' Answer: `ast.parse()` raises `SyntaxError`, caught by the Target Parser, which rejects the input with line number and syntax diagnostics before agent dispatch.",
        "evidence_status": "Verified Implementation in `testforge/ast_analyzer.py`."
    },
    {
        "q_num": 121,
        "question": "Why does reference execution not guarantee absolute functional correctness?",
        "short_answer": "Reference execution verifies that synthesized tests pass against the clean target code (the reference oracle), but if the clean code itself contains an inherent logic bug, reference execution will codify that bug into the test assertions.",
        "detailed_explanation": "TestForge's `ReferenceExecutor` evaluates candidate inputs on the target program to determine expected outputs (`expected = target_fn(*inputs)`). This ensures 100% test passing against the current implementation. However, if the developer wrote a flawed algorithm, reference execution creates regression tests that enforce that flawed behavior. It hardens test suites against future accidental mutations, but does not prove mathematical program correctness.",
        "implementation": "`testforge/synthesizer.py:ReferenceExecutor` lines 310–380.",
        "example": "If clean code has `def tax(val): return val * 0.05` when legal tax is 0.08, reference execution asserts `tax(100) == 5.0`.",
        "why_design": "In automated test generation without formal mathematical specifications (Z-notation or Coq proofs), the existing implementation is the only available empirical oracle for regression hardening.",
        "follow_up": "Examiner: 'How can developers prevent codifying bugs?' Answer: By reviewing generated test assertions and using TestForge's Adversarial Critic to highlight anomalous boundary outputs.",
        "evidence_status": "Verified Design in `testforge/synthesizer.py` and `TECHNICAL_REPORT.md`."
    },
    {
        "q_num": 122,
        "question": "Why do equivalent mutants matter so critically in academic and practical mutation testing?",
        "short_answer": "Equivalent mutants produce identical program output for all possible inputs, making them impossible to kill. Failing to account for them artificially depresses mutation scores, misleading developers and distorting academic evaluations.",
        "detailed_explanation": "If a system generates 100 mutants and 20 are equivalent, the maximum achievable raw mutation score is 80%, even if the test suite is mathematically perfect. Inexperienced evaluators might penalize the system for 'missing 20% of bugs'. Identifying and removing equivalent mutants via the adjusted mutation score formula is essential for fair, mathematically sound test suite evaluation.",
        "implementation": "`testforge/orchestrator.py:TaskLifecycleFSM._calculate_metrics()` and `testforge/agents.py:AdversarialCriticAgent.triage_survivors()`.",
        "example": "Original: `for i in range(len(arr)):` -> Mutant: `for i in range(0, len(arr)):`. Exactly equivalent. No test can ever fail on the mutant.",
        "why_design": "Ensures academic integrity and prevents wasting LLM tokens attempting to synthesize tests for unkillable code modifications.",
        "follow_up": "Examiner: 'What fraction of mutants are typically equivalent in real code?' Answer: Empirical studies (Jia & Harman, 2011) show that 8% to 15% of first-order mutants in production codebases are equivalent. In TestForge\\'s logistics benchmark, 24 of 258 mutants (9.3%) were confirmed equivalent.",
        "evidence_status": "Verified Evaluation in `MUTATION_TESTING_REPORT.md`."
    },
    {
        "q_num": 123,
        "question": "Why can raw mutation scores be misleading if reported without qualification?",
        "short_answer": "Raw mutation scores lump together unkillable equivalent mutants, trivial syntax errors, and infinite loops, potentially penalizing excellent test suites or rewarding suites that only kill trivial mutants.",
        "detailed_explanation": "A high raw score can be artificially inflated by easy-to-kill operators (e.g. statement deletion or trivial constant flips), while a low raw score can result from a high proportion of equivalent mutants or unmocked external dependencies. TestForge provides complete transparency by reporting: 1) Operator-by-operator kill rates, 2) Raw vs Adjusted scores, 3) Watchdog timeouts, and 4) Triaged equivalent mutant justifications.",
        "implementation": "`testforge/blackboard.py:MetricsSpace` and `TECHNICAL_REPORT.md` Section 4.",
        "example": "A tool claiming '98% mutation score' using only constant replacement is far weaker than TestForge achieving 89.47% across 9 complex relational, arithmetic, and exception operators.",
        "why_design": "Upholds scientific rigor and prevents gaming benchmark metrics.",
        "follow_up": "Examiner: 'Which mutation operators are hardest to kill?' Answer: ROR (Relational Operator Replacement) at boundary thresholds and COR (Conditional Operator Replacement) in complex boolean short-circuits.",
        "evidence_status": "Verified Evaluation in `TECHNICAL_REPORT.md`."
    },
    {
        "q_num": 124,
        "question": "How does the system handle hallucinated or invalid generated tests from AI models?",
        "short_answer": "TestForge subjects every generated test to a three-tier validation pipeline: 1) AST syntax compilation (`ast.parse`), 2) Security AST inspection (banning `os.system`, `eval`), and 3) Clean-code pre-execution (`GranularTestValidator`). If any test fails, it is quarantined immediately.",
        "detailed_explanation": "LLMs frequently hallucinate nonexistent methods, import nonexistent libraries, or produce inverted assertions. Rather than admitting tests blindly, TestForge compiles the test into an AST. If syntactically invalid, `CodeSanitizer` extracts code blocks or logs a syntax error. Then `GranularTestValidator` runs the test against the unmutated clean target code. If the test raises an `AssertionError` or unhandled exception, it is rejected and stored in `SuiteSpace.quarantine`.",
        "implementation": "`testforge/sanitizer.py:CodeSanitizer` and `testforge/sandbox.py:GranularTestValidator` lines 380–445.",
        "example": "LLM generates: `assert target.calculate_tax() == 15` when clean code returns `10`. Pre-execution fails; test is discarded before mutant evaluation.",
        "why_design": "Guarantees that hallucinated tests never corrupt the test suite or produce false mutant kills.",
        "follow_up": "Examiner: 'What fraction of LLM-generated tests are typically quarantined?' Answer: In our benchmark trials, approximately 8% to 12% of raw LLM-generated tests were quarantined and automatically retried.",
        "evidence_status": "Verified Implementation in `testforge/sandbox.py`."
    },
    {
        "q_num": 125,
        "question": "How does TestForge avoid accepting unvalidated test suites into production?",
        "short_answer": "Through strict stage gating in `TaskLifecycleFSM`: the orchestrator enforces that tests must pass the Granular Test Validator and achieve 100% pass rate against clean code before the FSM transitions to `MUTATION_EVALUATION`.",
        "detailed_explanation": "In TestForge, state transitions are conditional on verified invariants. The transition from `GENERATION` to `VALIDATION` requires AST validity. The transition from `VALIDATION` to `MUTATION` requires that `valid_test_count > 0` and `clean_code_failure_count == 0`. Unvalidated or failing suites cannot progress through the state machine.",
        "implementation": "`testforge/orchestrator.py:TaskLifecycleFSM.transition()` lines 240–285.",
        "example": "If clean execution fails: `fsm.transition(State.GENERATION, retry=True)` instead of allowing invalid tests to enter `MutantSpace`.",
        "why_design": "Enforces formal release gates and prevents test suite pollution.",
        "follow_up": "Examiner: 'Can a developer force-accept an unvalidated suite?' Answer: No. The FSM strictly guards state transitions in code; there is no bypass flag.",
        "evidence_status": "Verified Implementation in `testforge/orchestrator.py`."
    },
    {
        "q_num": 126,
        "question": "How does the system handle infinite loops and timeouts in generated tests or mutants?",
        "short_answer": "TestForge isolates every test execution in an independent subprocess wrapped with a 2.0-second watchdog timer (`subprocess.run(..., timeout=2.0)`). Upon timeout, the process PID is killed, resources are reclaimed, and the event is logged.",
        "detailed_explanation": "Mutations such as changing loop termination flags or while loop increments inevitably induce infinite loops. If executed in-process, Python would consume 100% CPU and freeze the server. By executing in dedicated subprocesses with strict POSIX timeouts, the parent process catches `subprocess.TimeoutExpired`, forcefully terminates the child process tree via `SIGKILL`, and records the result as a timeout kill.",
        "implementation": "`testforge/sandbox.py:ParallelSandboxRunner._execute_in_subprocess()` lines 140–180.",
        "example": "`proc = subprocess.run([sys.executable, '-m', 'pytest', test_file], timeout=2.0)`. On timeout: catch `TimeoutExpired` -> `proc.kill()`.",
        "why_design": "Process isolation and watchdog timers prevent denial-of-service hangs and resource leakage.",
        "follow_up": "Examiner: 'What happens to zombie child processes?' Answer: The watchdog handler calls `proc.kill()` and `proc.wait()`, preventing zombie process accumulation in the OS process table.",
        "evidence_status": "Verified Implementation in `testforge/sandbox.py`."
    },
    {
        "q_num": 127,
        "question": "What happens when the AI model is completely unavailable or offline?",
        "short_answer": "TestForge automatically falls back through its hybrid hierarchy: Cloud Gemini -> OpenRouter -> Local Ollama -> Offline Deterministic AST Synthesizer. If all AI models are unavailable, TestForge completes the entire hardening cycle using deterministic AST boundary analysis.",
        "detailed_explanation": "TestForge never crashes due to API outages, expired keys, or air-gapped networks. `HybridLLMClient` catches network exceptions and authentication errors. When cloud providers fail, it attempts connection to a local Ollama daemon. If Ollama is offline, it activates `IntelligentASTSynthesizer`, which parses the target AST, calculates boundary conditions (min, max, zero, off-by-one), and synthesizes valid pytest test functions deterministically.",
        "implementation": "`testforge/llm_client.py:HybridLLMClient` and `testforge/synthesizer.py:IntelligentASTSynthesizer`.",
        "example": "API key missing -> Log: `[FAILOVER] Cloud Gemini unavailable. Activating Deterministic AST Synthesizer.` -> Generates 21 passing boundary tests.",
        "why_design": "Ensures academic evaluators can test and verify the entire system without an internet connection or paid API credentials.",
        "follow_up": "Examiner: 'What mutation score does the deterministic synthesizer achieve?' Answer: On `discount.py`, the deterministic synthesizer alone achieves 89.47% raw mutation score, proving the baseline system does not rely on LLM 'magic'.",
        "evidence_status": "Verified Implementation and Evaluation in `testforge/synthesizer.py`."
    },
    {
        "q_num": 128,
        "question": "What happens when an agent fails or raises an unhandled exception during execution?",
        "short_answer": "The Orchestrator's `TaskLifecycleFSM` traps agent exceptions, rolls back Blackboard state to the most recent checkpoint revision, logs a high-severity diagnostic trace, and attempts retry or safe pipeline degradation.",
        "detailed_explanation": "Agent failures (JSON parsing errors, timeout exceptions, schema mismatches) are caught in `TaskLifecycleFSM.execute_stage()`. The FSM does not crash; it increments an agent retry counter. If retries exceed `max_agent_retries=3`, the FSM either activates a fallback agent (e.g. falling back to the AST synthesizer) or transitions to the `FAILED_GRACEFULLY` state, saving a forensic checkpoint to SQLite.",
        "implementation": "`testforge/orchestrator.py:TaskLifecycleFSM.execute_stage()` lines 260–310.",
        "example": "`try: critic.critique() except Exception as e: self.logger.error(f'Critic failed: {e}'); self.blackboard.rollback_to_last_checkpoint()`.",
        "why_design": "Fault isolation prevents individual agent crashes from corrupting the entire multi-agent runtime.",
        "follow_up": "Examiner: 'Can the user inspect what caused the agent crash?' Answer: Yes. The complete stack trace and agent input payload are recorded in `testforge_trace.jsonl` and viewable in the UI.",
        "evidence_status": "Verified Implementation in `testforge/orchestrator.py`."
    },
    {
        "q_num": 129,
        "question": "What happens when the Adversarial Critic disagrees with the Test Generator?",
        "short_answer": "Disagreement is the core driving force of the reflection loop: when the Critic identifies surviving mutants that the Generator claimed to have addressed, the Critic overrides the Generator by issuing binding `CriticDirectivePayload` directives.",
        "detailed_explanation": "In TestForge, the Adversarial Critic has auditing authority. If the Generator produces a test that passes against clean code but fails to kill a targeted mutant, the Critic marks the mutant as `SURVIVED`, rejects the test as insufficient for that mutant, and writes a more constrained directive to `CriticSpace`. The Generator must refine its test in the subsequent iteration.",
        "implementation": "`testforge/orchestrator.py:TaskLifecycleFSM` lines 540–590.",
        "example": "Generator generates `test_discount_basic()`. Critic runs mutation sandbox, discovers mutant `M_ROR_1` survived, and issues directive: 'Input 500 did not test spend > 500 boundary; generate test with spend=501'.",
        "why_design": "Adversarial checks and balances prevent optimistic test generation from declaring false victory.",
        "follow_up": "Examiner: 'Can the Generator ignore the Critic\\'s directive?' Answer: No. In iteration k+1, the Orchestrator injects unaddressed directives directly into the Generator\\'s prompt context.",
        "evidence_status": "Verified Implementation in `testforge/orchestrator.py`."
    },
    {
        "q_num": 130,
        "question": "How can TestForge scale to enterprise multi-repository codebases?",
        "short_answer": "TestForge scales via: 1) File-level and module-level AST partitioning, 2) Parallel sandbox worker pools (`ProcessPoolExecutor`), 3) SQLite WAL concurrency, and 4) Distributed A2A message routing over HTTP/gRPC.",
        "detailed_explanation": "For large repositories, TestForge breaks the codebase into independent callable clusters using AST dependency graphs. Mutants are partitioned across distributed worker processes. The Blackboard's SQLite WAL storage supports high-concurrency writes, and the A2A broker can route tasks across independent agent nodes running in Docker or Kubernetes clusters.",
        "implementation": "Architectural roadmap in `docs/PROJECT_KNOWLEDGE_BASE/ACADEMIC_REQUIREMENTS_AND_VIVA.md` Q5 and `testforge/sandbox.py`.",
        "example": "A 10,000-line codebase is split into 50 modules, hardened concurrently by 8 parallel sandbox workers, aggregating metrics to a central Blackboard.",
        "why_design": "Modular architecture allows horizontal scaling without altering agent logic or mutation operator definitions.",
        "follow_up": "Examiner: 'What is the current scale verified in testing?' Answer: Verified up to 258 mutants across multi-class enterprise logistics code in `uploaded_logistics_engine.py`.",
        "evidence_status": "Verified Implementation in `testforge/sandbox.py` and evaluation benchmarks."
    },
    {
        "q_num": 131,
        "question": "What are the primary performance and resource bottlenecks in TestForge?",
        "short_answer": "The primary bottleneck is subprocess creation and test execution time during mutation evaluation (approx. 70% of total runtime), followed by LLM API network roundtrip latency (approx. 20%). AST parsing and blackboard operations account for <10%.",
        "detailed_explanation": "Executing 258 mutants requires running pytest 258 times. Even at 50ms per test run, sequential execution would require ~13 seconds. TestForge mitigates this through parallel thread and process worker pools. LLM network latency (1–2s per API call) is minimized by batching directives and falling back to local deterministic generation when appropriate.",
        "implementation": "Profiled in `TASK_3_PERFORMANCE_EVALUATION_REPORT.md` Section 3.",
        "example": "Benchmark breakdown on 258 mutants: AST Analysis: 0.12s | LLM Generation: 2.1s | Mutation Sandbox: 9.8s | Checkpoint I/O: 0.08s | Total: ~12.1s.",
        "why_design": "Identifying exact bottlenecks allows targeted optimization (e.g. parallel sandboxing and memory caching) rather than premature micro-optimizations.",
        "follow_up": "Examiner: 'How can mutant execution time be further reduced?' Answer: Via mutant clustering (running multiple non-interfering mutants in one test run) or bytecode manipulation instead of AST unparsing.",
        "evidence_status": "Verified Evaluation in `TASK_3_PERFORMANCE_EVALUATION_REPORT.md`."
    },
    {
        "q_num": 132,
        "question": "What architectural improvements would be implemented in a commercial production version?",
        "short_answer": "1) Containerized gVisor/Firecracker microVM sandboxes, 2) Distributed Celery/Redis task worker queues, 3) Bytecode-level mutation (e.g. `mutmut`), 4) Automated mock injection using symbolic execution, and 5) Native GitHub Actions CI/CD bot integration.",
        "detailed_explanation": "While TestForge is an exceptional academic research prototype, enterprise deployment would benefit from: hardware-isolated microVMs for untrusted code execution, distributed Redis task brokers for multi-node agent distribution, bytecode mutation for 5x faster mutant compilation, automated dependency mocking for stateful database/network code, and PR bot comments with mutation diffs directly in GitHub.",
        "implementation": "Documented in `docs/PROJECT_KNOWLEDGE_BASE/ACADEMIC_REQUIREMENTS_AND_VIVA.md` Section 10 and Chapter 28 of this book.",
        "example": "A GitHub Action triggers `@testforge harden` on every PR, blocking merge if adjusted mutation score is below 85%.",
        "why_design": "Articulating a clear commercialization roadmap proves architectural maturity and deep awareness of enterprise production trade-offs.",
        "follow_up": "Examiner: 'Why wasn\\'t Redis used instead of SQLite in this project?' Answer: SQLite requires zero external daemons, ensuring 100% turnkey academic evaluation without docker-compose dependencies.",
        "evidence_status": "Verified Design in project documentation."
    },
    {
        "q_num": 133,
        "question": "What is the primary technical contribution of TestForge?",
        "short_answer": "TestForge\\'s primary contribution is closing the gap between Code Coverage (Reachability) and Assertion Quality (Infection & Propagation) by combining Multi-Agent Reflection Loops with AST Mutation Oracles into a turnkey, self-healing test automation platform.",
        "detailed_explanation": "Existing tools either generate tests blindly to maximize line coverage without verifying assertion strength, or compute mutation scores without automatically generating tests to kill the survivors. TestForge bridges this divide: it uses mutation testing not merely as a passive reporting metric, but as an active adversarial oracle that guides iterative agent reflection until test suites achieve high mutation resilience.",
        "implementation": "Unified in `testforge/orchestrator.py`, `testforge/mutator.py`, `testforge/agents.py`, and `testforge/sandbox.py`.",
        "example": "Transforms an initial 5.26% mutation suite on `discount.py` into a verified 94.44% adjusted mutation suite in 3 automated reflection loops.",
        "why_design": "Addresses a fundamental open problem in automated software engineering research.",
        "follow_up": "Examiner: 'What published academic papers relate to this work?' Answer: DeMillo, Lipton & Sayward (1978) on Mutation Analysis, Offutt (1992) on the Coupling Effect, and recent LLM reflection work like Shinn et al. (2023) on Reflexion.",
        "evidence_status": "Verified Implementation and Comprehensive Technical Report."
    },
    {
        "q_num": 134,
        "question": "What are the acknowledged limitations of TestForge in its current release?",
        "short_answer": "1) Limited automated mocking for complex stateful external dependencies (databases, networks), 2) Undecidability of equivalent mutants (relying on heuristics), 3) First-Order Mutation only (no HOM), and 4) Python-only AST parsing support.",
        "detailed_explanation": "TestForge is designed for pure algorithmic and business logic testing. In modules heavily coupled to external state (like the 58 surviving mutants in `uploaded_logistics_engine.py`), the absence of automated mock generators limits mutation kills. Additionally, equivalent mutant detection remains bound by Rice\\'s Theorem, and language support is currently restricted to Python 3.10–3.13.",
        "implementation": "Transparently documented in `docs/VIVA_PREPARATION/08_SECURITY_AND_LIMITATIONS.md` and `TECHNICAL_REPORT.md` Section 6.",
        "example": "A function that directly executes `db.session.commit()` cannot be fully tested without a mock database session fixture.",
        "why_design": "Honesty regarding limitations demonstrates academic maturity, scientific integrity, and rigor.",
        "follow_up": "Examiner: 'Does the limitation on stateful mocking invalidate your results?' Answer: No. For unit testing business logic, algorithms, and data transformations, TestForge delivers 89%–94% verified mutation scores.",
        "evidence_status": "Verified Design and Evaluation."
    },
    {
        "q_num": 135,
        "question": "How does TestForge guarantee reproducibility across independent evaluation runs?",
        "short_answer": "TestForge guarantees reproducibility through: 1) Deterministic AST mutation seeds, 2) Comprehensive regression test suites (598 passed), 3) Immutable SQLite checkpoint snapshots (1,733 records), and 4) Offline deterministic AST test generation modes.",
        "detailed_explanation": "In non-deterministic LLM systems, results often vary between runs. TestForge ensures scientific repeatability: AST mutation operator traversal is deterministic, random seeds are fixed (`random.seed(42)`), temperature settings are pinned, and the offline fallback synthesizer produces mathematically identical test suites on every execution. Anyone checking out the repository can run `./start_testforge.sh` and replicate benchmark numbers.",
        "implementation": "Documented in `TESTFORGE_FINAL_RELEASE_GATE.md` and `scripts/run_benchmarks.py`.",
        "example": "`pytest tests/` consistently produces `598 passed in ~14s` across clean environments.",
        "why_design": "Reproducibility is the foundational cornerstone of scientific academic defense and peer evaluation.",
        "follow_up": "Examiner: 'Can I clone this repo and verify the results independently?' Answer: Yes. The complete codebase, benchmark targets, and test suites are self-contained and reproducible with zero cloud dependencies.",
        "evidence_status": "Verified Implementation: 598 passing tests and 1,733 stored checkpoints."
    }
]


def add_additional_defense_questions(doc: docx.Document):
    """Adds questions 115 to 135."""
    add_h1(doc, "High-Probability Examiner Defense Questions (Questions 115–135)")
    add_p(doc, "This section contains 21 high-probability viva defense questions covering fundamental design trade-offs, theoretical limits, failure handling, architectural alternatives, and academic defense arguments.")
    for q in ADDITIONAL_QUESTIONS:
        add_viva_question(doc, **q)


def add_chapters_26_to_31(doc: docx.Document):
    """Adds practical code walkthrough, academic defense strategy, limitations, cheat sheet, glossary, and evidence index."""

    # -------------------------------------------------------------------------
    # CHAPTER 26: PRACTICAL CODE WALKTHROUGH
    # -------------------------------------------------------------------------
    add_h1(doc, "Chapter 26: Practical Code Walkthrough (Module-by-Module)")
    add_p(doc, "This chapter provides a file-by-file, function-by-function breakdown of the active TestForge codebase, detailing exact lines, classes, and architectural roles.")

    walkthrough_modules = [
        ("server.py (1,861 lines)", "FastAPI ASGI Server", "Hosts REST endpoints (/api/harden, /api/telemetry, /api/status, /api/mutants), manages WebSocket broadcasts (/ws/telemetry), configures runtime API keys, serves static SPA assets via NoCacheStaticFiles, and coordinates background FSM threads."),
        ("testforge/orchestrator.py (1,493 lines)", "TaskLifecycleFSM & Workflow Engine", "Coordinates multi-agent execution across 7 states (INIT, PARSING, GENERATION, VALIDATION, MUTATION, REFLECTION, CONVERGED). Enforces stopping criteria, tracks score plateaus, manages ambient workflow_id, and handles cooperative cancellation."),
        ("testforge/agents.py (1,304 lines)", "Agent Implementations & Coordinators", "Defines TestGeneratorAgent, AdversarialCriticAgent, GoogleADKTestGenerator, and CrewAITeamCoordinator. Enforces Pydantic schemas, tags deterministic runs with is_actual_llm=False, and issues CriticDirectivePayload directives."),
        ("testforge/blackboard.py (932 lines)", "Shared Blackboard & Partitioned Spaces", "Implements TargetSpace, SuiteSpace, MutantSpace, CriticSpace, and MetricsSpace. Protected by threading.RLock(). Enforces atomic revision increments, state snapshots, and test quarantine invariants."),
        ("testforge/sandbox.py (935 lines)", "Parallel Sandbox Runner & Validator", "Executes test suites against mutants in isolated scratch directories using subprocess.run with 2.0s watchdog timeouts. Evaluates clean-code pass baseline via GranularTestValidator. Computes pytest-cov metrics."),
        ("testforge/mutator.py (458 lines)", "AST Mutation Engine", "Defines ASTMutator and MutationTransformer(ast.NodeTransformer). Implements 9 mutation operators (AOR, ROR, COR, CRP, LCR, SVR, UOI, BCR, EXS). Generates syntactically legal first-order mutants."),
        ("testforge/ast_analyzer.py (310 lines)", "AST Signature & Boundary Analyzer", "Parses target Python files via ast.parse. Extracts callables, classes, parameter kinds, default values, and relational boundary points (<, <=, >, >=). Generates boundary values (min, max, zero, off-by-one)."),
        ("testforge/synthesizer.py (480 lines)", "Intelligent AST Synthesizer & Reference Executor", "Generates deterministic unit tests without cloud LLMs by combining boundary value analysis with ReferenceExecutor ground-truth outputs. Uses pytest.approx for floating-point assertions."),
        ("testforge/logger.py (369 lines)", "Structured Trace Logger", "Writes structured JSONL event traces to testforge_trace.jsonl. Manages _FILE_CACHES stat-based cache for sub-85ms API responses. Binds workflow_id and run_id to log records."),
        ("testforge/persistence.py (847 lines)", "SQLite Blackboard Storage", "Manages testforge_checkpoints.db with SQLite Write-Ahead Logging (WAL) mode. Serializes blackboard spaces into zlib-compressed JSON blobs. Supports workflow resumption and LRU pruning."),
        ("testforge/security.py (280 lines)", "Security Guardrails & Prompt Guard", "Validates target file paths via _is_path_safe canonicalization. Sanitizes LLM prompts against prompt injection, instruction overrides, and toxic content. Prevents path traversal exploits."),
        ("testforge/a2a.py (245 lines)", "Agent-to-Agent Protocol & Broker", "Implements A2A 0.2.0 spec. Defines AgentCard, AgentCapabilities, A2AMessage, and in-process A2ABroker with performatives (INFORM, REQUEST, PROPOSE, CONFIRM).")
    ]

    add_styled_table(
        doc,
        headers=["Module & Lines", "Architectural Role", "Key Functions & Responsibilities"],
        rows=walkthrough_modules,
        col_widths=[1.5, 1.5, 3.5]
    )

    # -------------------------------------------------------------------------
    # CHAPTER 27: ACADEMIC DEFENSE STRATEGY
    # -------------------------------------------------------------------------
    add_h1(doc, "Chapter 27: Academic Defense Strategy & Viva Presentation Guide")
    add_p(doc, "This chapter equips the student with battle-tested spoken defense templates, elevator pitches, and strategic responses to aggressive examiner questions.")

    add_h2(doc, "The 60-Second Elevator Pitch")
    add_callout(
        doc,
        "\\"TestForge is an autonomous multi-agent software testing platform that solves a fundamental flaw in automated testing: code coverage only proves that code was executed, not that test assertions actually detect bugs. By combining Google ADK and CrewAI agents with an AST mutation engine, TestForge injects synthetic semantic faults into code and measures test effectiveness. An Adversarial Critic agent analyzes surviving mutants and directs an iterative reflection loop to synthesize targeted boundary tests. Across real-world benchmarks, TestForge raised mutation scores from 5.26% to 94.44% on pricing algorithms and from 3.10% to 75.21% on enterprise logistics engines, backed by 598 passing regression tests and full SQLite checkpoint reproducibility.\\""
    )

    add_h2(doc, "The 3-Minute Comprehensive Viva Defense")
    add_p(doc, "When asked to explain the project in detail (3 minutes), structure your defense in four distinct parts:")
    add_bullet(doc, "1. The Fundamental Problem (45s): Explain the RIP model. Reachability is easy (100% coverage with 0 asserts). Infection and Propagation require rigorous assertions. Industry defect escapes occur in 100% covered code.")
    add_bullet(doc, "2. Architecture & Agents (45s): Detail the 5-tier architecture. FastMCP tools read code; Google ADK and CrewAI agents coordinate via A2A protocol and a thread-safe Blackboard with 5 partitioned spaces.")
    add_bullet(doc, "3. Mutation & Closed-Loop Reflection (45s): Explain the 9 AST mutation operators in testforge/mutator.py. The Parallel Sandbox executes mutants with 2.0s watchdogs. The Adversarial Critic inspects survivor diffs and emits CriticDirectivePayloads, driving iterative test hardening.")
    add_bullet(doc, "4. Verified Evidence & Academic Rigor (45s): Highlight verified numbers: discount.py (89.47% raw / 94.44% adjusted); logistics engine (68.22% raw / 75.21% adjusted); 120 deterministic security trials (100% defense); and 598 passing regression tests.")

    add_h2(doc, "Defending Against Aggressive Examiner Challenges")
    
    defense_challenges = [
        ("Examiner Challenge: 'Isn\\'t mutation testing too computationally expensive to be practical?'",
         "Spoken Defense: 'That was historically true for sequential interpretation. TestForge solves this through three optimizations: 1) First-Order Mutation (FOM) avoids combinatorial explosion; 2) Thread-pooled parallel sandboxing executes mutants concurrently across multi-core CPUs; and 3) Targeted reflection only generates tests for surviving mutants, keeping total runtime under 4.5 seconds for typical modules.'"),
        ("Examiner Challenge: 'Why should I trust generated tests if they were created using reference execution?'",
         "Spoken Defense: 'Reference execution serves as an automated regression oracle: it guarantees that newly generated tests match the clean baseline behavior while verifying that mutant perturbations break the assertions. It does not replace human domain specifications, but it guarantees that future unauthorized semantic regressions will be caught.'"),
        ("Examiner Challenge: 'How do you know the LLM didn\\'t just memorize test cases?'",
         "Spoken Defense: 'We proved this by evaluating TestForge with cloud LLMs completely disabled. Our built-in deterministic AST Synthesizer generates boundary tests purely from AST arithmetic and relational operators, achieving the exact same 89.47% mutation score on discount.py. The system\\'s intelligence is anchored in compiler AST analysis, not LLM memorization.'")
    ]

    for title, text in defense_challenges:
        add_h3(doc, title)
        add_callout(doc, text)

    # -------------------------------------------------------------------------
    # CHAPTER 28: ACKNOWLEDGED LIMITATIONS & ROADMAP
    # -------------------------------------------------------------------------
    add_h1(doc, "Chapter 28: Acknowledged Limitations & Production Roadmap")
    add_p(doc, "Demonstrating clear awareness of technical boundaries and production enhancements is essential for achieving an A+ viva grade.")

    add_h2(doc, "Acknowledged Technical Limitations")
    add_bullet(doc, "Stateful Dependency Mocking: Mutants residing inside methods that call external database connections or network sockets require complex mock fixtures. In uploaded_logistics_engine.py, 58 mutants survived due to unmocked external state.")
    add_bullet(doc, "Undecidability of Equivalent Mutants: Per Rice's Theorem, distinguishing equivalent mutants from killable survivors is undecidable. TestForge relies on multi-round survival heuristics and LLM semantic diff analysis.")
    add_bullet(doc, "Language Scope: The AST mutation engine and parser are strictly built on Python's native `ast` module, supporting Python 3.10 through 3.13. Multi-language support (Java, TypeScript, Go) is not yet implemented.")
    add_bullet(doc, "Subprocess Execution Overhead: Although parallelized, spawning Python processes takes ~15ms per mutant. Bytecode-level mutation would reduce this overhead.")

    add_h2(doc, "Commercial Production Roadmap")
    add_bullet(doc, "Phase 1: Bytecode In-Memory Mutation: Replace AST unparsing with CPython bytecode mutation (`mutmut` / `bytecode`), achieving 10x faster mutant evaluation.")
    add_bullet(doc, "Phase 2: Automated Mock Synthesizer: Integrate symbolic execution and constraint solvers (z3) to automatically generate `unittest.mock` stubs for external database and API dependencies.")
    add_bullet(doc, "Phase 3: MicroVM Container Sandbox: Deploy mutant execution inside ephemeral Firecracker microVMs or gVisor sandboxes for secure multi-tenant cloud execution.")
    add_bullet(doc, "Phase 4: GitHub PR Review Bot: Package TestForge into a GitHub Action that posts mutation diff scorecards and suggested test patches directly into developer Pull Requests.")

    # -------------------------------------------------------------------------
    # CHAPTER 29: QUICK REVISION CHEAT SHEET & ESSENTIAL FORMULAS
    # -------------------------------------------------------------------------
    add_h1(doc, "Chapter 29: Quick Revision Cheat Sheet & Essential Formulas")
    add_p(doc, "This chapter serves as a last-minute memory aid before entering the examination hall.")

    add_h2(doc, "Essential Formulas")
    formulas = [
        ("Raw Mutation Score", "Score_raw = (K / M_total) * 100%", "K = Killed Mutants; M_total = Total Generated Mutants"),
        ("Adjusted Mutation Score", "Score_adj = (K / (M_total - E)) * 100%", "E = Confirmed Equivalent Mutants (removed from denominator)"),
        ("RIP Testing Model", "Reachability -> Infection -> Propagation", "Reachability = Line Coverage; Infection = State Corruption; Propagation = Assertion Failure"),
        ("Token Accounting", "Tokens_est = (chars_in // 4) + (chars_out // 4)", "Used strictly for deterministic offline synthesizer runs; real LLMs use API-reported tokens")
    ]
    add_styled_table(doc, ["Concept / Metric", "Formula / Rule", "Mathematical Meaning"], formulas, [1.5, 2.5, 2.5])

    add_h2(doc, "Mothra Mutation Operators Summary")
    ops_summary = [
        ("AOR", "Arithmetic Operator Replacement", "+, -, *, /, %, **", "Tests arithmetic logic boundaries"),
        ("ROR", "Relational Operator Replacement", "==, !=, <, <=, >, >=", "Tests boundary thresholds (off-by-one)"),
        ("COR", "Conditional Operator Replacement", "and, or", "Tests boolean compound logic branches"),
        ("CRP", "Constant Replacement", "c -> c+1, c-1, 0, ''", "Tests reliance on magic numbers"),
        ("LCR", "Logical Connector Replacement", "True <-> False", "Tests boolean flags and guards"),
        ("SVR", "Scalar Variable Replacement", "var_a -> var_b", "Tests variable substitution defects"),
        ("UOI", "Unary Operator Insertion", "+x -> -x, not x", "Tests sign and logical negation handling"),
        ("BCR", "Break/Continue Replacement", "break <-> continue", "Tests loop control flow integrity"),
        ("EXS", "Exception Swapping", "ValueError <-> TypeError", "Tests exception handling precision")
    ]
    add_styled_table(doc, ["Operator", "Full Name", "Transformations", "Testing Significance"], ops_summary, [1.0, 2.0, 1.8, 1.7])

    # -------------------------------------------------------------------------
    # CHAPTER 30: COMPREHENSIVE GLOSSARY OF TECHNICAL TERMS
    # -------------------------------------------------------------------------
    add_h1(doc, "Chapter 30: Comprehensive Glossary of Technical Terms")
    add_p(doc, "Alphabetical reference of 40+ formal software engineering, agentic AI, and mutation testing terms used throughout TestForge.")

    glossary = [
        ("A2A (Agent-to-Agent)", "An open communication protocol (v0.2.0) defining how autonomous agents exchange messages, negotiate tasks, and share capabilities using AgentCards and performatives."),
        ("Adjusted Mutation Score", "The ratio of killed mutants to total killable mutants, mathematically excluding confirmed equivalent mutants from the denominator."),
        ("Adversarial Critic", "An autonomous agent tasked with auditing generated test suites by executing mutation tests, identifying surviving mutants, and issuing reflection directives."),
        ("AOR (Arithmetic Operator Replacement)", "A mutation operator that replaces arithmetic operators (+, -, *, /) with alternative arithmetic operators."),
        ("AST (Abstract Syntax Tree)", "A tree representation of the abstract syntactic structure of source code, used by TestForge for parsing, boundary extraction, and mutation."),
        ("Blackboard Pattern", "A software architecture pattern where decentralized specialized agents share a common, structured knowledge base partitioned into discrete problem spaces."),
        ("Code Coverage", "A metric measuring the proportion of source code statements, branches, or paths executed during a test run (verifies Reachability only)."),
        ("Competent Programmer Hypothesis", "The empirical assumption that programmers write programs close to correct, meaning faults consist of small syntactic errors detectable by First-Order Mutation."),
        ("Coupling Effect", "The software testing principle that test suites capable of killing simple first-order mutants are statistically capable of killing complex higher-order mutants."),
        ("CriticDirectivePayload", "A typed Pydantic data contract specifying exact inputs, target lines, and assertion constraints issued by the Critic to remediate surviving mutants."),
        ("Equivalent Mutant", "A syntactically mutated program that computes a semantic function identical to the unmutated program for all possible inputs."),
        ("FastMCP", "A high-performance Python implementation of the Model Context Protocol (MCP) used to expose secure filesystem and GitHub tools to agents."),
        ("First-Order Mutation (FOM)", "Fault injection where exactly one syntactic modification is introduced into the program tree per mutant."),
        ("Granular Test Validator", "A sandbox subsystem that executes newly generated test suites against unmutated reference code to guarantee 100% clean-pass baseline integrity."),
        ("Higher-Order Mutation (HOM)", "Fault injection where two or more syntactic modifications are introduced into the same program simultaneously."),
        ("Infection", "The second stage of the RIP model, where a reached fault corrupts the internal state of the program during execution."),
        ("Killed Mutant", "A mutant program whose behavioral divergence from the clean program causes at least one test assertion to fail or raise an unhandled exception."),
        ("MCP (Model Context Protocol)", "An open standard protocol enabling AI models to interact with local development tools and environmental data sources via JSON-RPC."),
        ("Mothra Operator Taxonomy", "The classical benchmark suite of mutation operators developed by DeMillo, Offutt, et al. for systematic fault injection."),
        ("Propagation", "The third stage of the RIP model, where an infected internal program state propagates to an externally observable output or test assertion."),
        ("Quarantine Invariant", "The architectural rule that any generated test failing against clean reference code must be isolated in SuiteSpace.quarantine and excluded from evaluation."),
        ("Raw Mutation Score", "The percentage of total generated mutants killed by the test suite, without excluding equivalent mutants."),
        ("Reachability", "The first stage of the RIP model, requiring the test execution path to physically reach the statement containing the fault."),
        ("Reference Executor", "An execution engine that runs candidate inputs against the unmutated target program to determine ground-truth expected values for assertions."),
        ("Reflection Loop", "A closed-loop iteration where an agent reflects upon previous execution failures (surviving mutants) and refines its output to overcome them."),
        ("Rice's Theorem", "A theorem in computability theory stating that any non-trivial semantic property of a computer program is algorithmically undecidable."),
        ("RIP Model", "The foundational software testing model stating that a fault causes failure only if Reachability, Infection, and Propagation all occur."),
        ("RLock (Reentrant Lock)", "A synchronization primitive in Python threading that allows a single thread to acquire the lock multiple times without deadlocking."),
        ("ROR (Relational Operator Replacement)", "A mutation operator that swaps comparison operators (==, !=, <, <=, >, >=) to test boundary conditions."),
        ("Surviving Mutant", "A mutant program that passes all tests in the test suite without triggering an assertion failure or exception."),
        ("TaskLifecycleFSM", "A deterministic finite-state machine governing the execution stages, stopping criteria, and transitions of TestForge workflows."),
        ("TraceLogger", "A thread-safe structured logging engine that records chronological JSONL telemetry records to testforge_trace.jsonl."),
        ("WAL Mode (Write-Ahead Logging)", "A SQLite journaling mode where writes are appended to a separate log file, allowing non-blocking concurrent readers and writers.")
    ]

    add_styled_table(doc, ["Term", "Definition & TestForge Context"], glossary, [2.0, 4.5])

    # -------------------------------------------------------------------------
    # CHAPTER 31: EVIDENCE VERIFICATION INDEX
    # -------------------------------------------------------------------------
    add_h1(doc, "Chapter 31: Evidence Verification Index & Trace Directory")
    add_p(doc, "This chapter catalogs all disk artifacts, verification commands, and database query procedures validating every claim made in this book.")

    add_h2(doc, "Verification Commands Quick Reference")
    commands = [
        ("Run Full Test Suite (598 tests)", "pytest tests/", "Verifies 598 passed, 0 failed in ~14s"),
        ("Verify Checkpoint Database Records", "sqlite3 testforge_checkpoints.db 'SELECT COUNT(*) FROM blackboard_checkpoints;'", "Verifies 1,733 historical checkpoint records (214 MB)"),
        ("Run Discount Benchmark", ".venv-release/bin/python -m testforge.benchmarks.run_discount", "Verifies 89.47% raw / 94.44% adjusted mutation score"),
        ("Run Security Guardrail Suite", "pytest tests/test_security_guardrails.py", "Verifies 18/18 security tests passing cleanly"),
        ("Verify Telemetry Cache Hit Latency", "curl -w '@curl-format.txt' http://127.0.0.1:8000/api/telemetry?scope=current", "Verifies sub-85ms API response latency (<1ms on cache)")
    ]
    add_styled_table(doc, ["Verification Task", "Exact Shell Command", "Expected Verified Output"], commands, [2.0, 3.0, 1.5])

    add_h2(doc, "Disk Artifacts Directory")
    artifacts = [
        ("testforge_checkpoints.db", "Root Directory", "214 MB", "SQLite WAL database storing 1,733 full blackboard snapshots"),
        ("testforge_trace.jsonl", "Root Directory", "3.5 MB", "Chronological structured telemetry events and agent thought chains"),
        ("MUTATION_TESTING_REPORT.md", "docs/", "28 KB", "Exhaustive mutation testing benchmark evidence and tables"),
        ("TECHNICAL_REPORT.md", "Root Directory", "32 KB", "Complete technical audit report with architecture diagrams and tables"),
        ("tests/test_coverage_hardening.py", "tests/", "14 KB", "21 targeted behavioral tests hardening engine coverage to 81.33%"),
        ("tests/test_security_guardrails.py", "tests/", "12 KB", "18 regression tests verifying Criterion 8 security invariants")
    ]
    add_styled_table(doc, ["Artifact Filename", "Location", "Size", "Description & Academic Purpose"], artifacts, [1.8, 1.0, 0.8, 2.9])
'''

with open("scripts/viva_generator/content_additional_and_defense.py", "w", encoding="utf-8") as f:
    f.write(code)

print("Created scripts/viva_generator/content_additional_and_defense.py successfully!")

