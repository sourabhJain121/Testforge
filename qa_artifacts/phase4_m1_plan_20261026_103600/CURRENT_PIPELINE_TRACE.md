# TestForge Phase 4.1 — Current Pipeline Trace & Architectural Mapping

**Timestamp**: 2026-10-26T10:36:00+05:30  
**Repository**: `/Users/sourabh/TestForge`  
**Purpose**: Code-level inspection and execution tracing of the TestForge test generation, mutation analysis, reflection, and benchmarking pipeline.

---

## 1. End-to-End Execution Flow

The TestForge pipeline follows a structured, multi-agent, blackboard-mediated architecture orchestrated primarily by `TestForgeOrchestrator` in `testforge/orchestrator.py`.

```mermaid
graph TD
    A[Input Source Code / Target File] --> B[SecurityGuardrail & CodeIngestionService]
    B --> C[AST Analysis & BlastRadiusAnalyzer]
    C --> D[Target Space on Blackboard]
    D --> E[Initial Candidate Test Synthesis (ADK / Generator)]
    E --> F[Sandbox Clean Validation (pass@1 check)]
    F --> G[ASTMutator: Generate Deterministic Mutants]
    G --> H[ParallelSandboxRunner: Evaluate Mutants]
    H --> I[EquivalenceChecker & calculate_mutation_scores]
    I --> J{Score >= Target OR Iterations Max?}
    J -- No --> K[AdversarialCriticAgent / CrewAICriticService]
    K --> L[Critic Directives on Blackboard]
    L --> M[TestGeneratorAgent / ADK Mutation-Guided Repair]
    M --> N[Sandbox Clean Target Check]
    N -- PASS --> O[Update Suite Space & Loop]
    N -- FAIL --> P[Retain Previous Suite & Loop]
    J -- Yes --> Q[Final State & Checkpoint Persistence]
```

---

## 2. Component-by-Component Architectural Inventory

### 2.1 Source Ingestion & AST Analysis
- **Primary Source Files**:
  - `testforge/ingestion.py`
  - `testforge/blast_analyzer.py`
  - `testforge/git_diff.py`
  - `testforge/diff_inspector.py`
- **Key Classes & Functions**:
  - `CodeIngestionService`: Ingests Python source, cleans formatting, resolves imports.
  - `BlastRadiusAnalyzer.analyze_impact(func_name, source_code)`: Builds AST dependency graph and calculates blast radius risk (`LOW`, `MEDIUM`, `HIGH`, `CRITICAL`).
  - `extract_function_signatures(source_code)`: Extracts function names, arguments, type annotations, and docstrings via AST parsing.
  - `GitDiffInspector`: Analyzes targeted lines for differential test generation.
- **Relevant Tests**:
  - `tests/test_mode_c_ingestion.py`
  - `tests/test_blast_and_adk.py`

### 2.2 Agent Orchestration & Blackboard State
- **Primary Source Files**:
  - `testforge/orchestrator.py`
  - `testforge/blackboard.py`
  - `testforge/persistence.py`
  - `testforge/state.py`
  - `testforge/a2a.py` & `testforge/a2a_protocol.py`
- **Key Classes & Functions**:
  - `TestForgeOrchestrator`: Master workflow coordinator (`run()`, `_execute_pipeline()`).
  - `Blackboard`: Central thread-safe state container partitioned into `TargetSpace`, `SuiteSpace`, `MutantSpace`, `CriticSpace`, and `MetricsSpace`.
  - `PersistentBlackboardStore`: SQLite-backed checkpoint manager storing full state snapshots and enabling deterministic resumption.
  - `A2ABroker` & `A2AMessage`: Protocol for strongly typed inter-agent handoffs with correlation IDs and JSONL telemetry.
- **Relevant Tests**:
  - `tests/test_blackboard.py`
  - `tests/test_blackboard_persistence.py`
  - `tests/test_checkpoint_resumption.py`
  - `tests/test_a2a.py`

### 2.3 Test Generation & Critic / Repair Logic
- **Primary Source Files**:
  - `testforge/agents.py`
  - `testforge/crew_critic.py`
  - `testforge/adk_engine.py` & `testforge/adk_generator.py`
- **Key Classes & Functions**:
  - `TestGeneratorAgent.generate_tests(source_code, surviving_diffs, critic_feedback, iteration)`: Generates pytest suites via Google GenAI Live (or local Ollama / fallback).
  - `TestGeneratorAgent._synthesize_ast_aware_tests(...)`: Deterministic fallback synthesizer generating parameter-driven assertions from function AST signatures.
  - `AdversarialCriticAgent.analyze_surviving_mutants(target_code, surviving_mutant_diffs, iteration)`: Generates targeted critique directives explaining which code behaviors are untested.
  - `CrewAICriticService`: High-order multi-agent critique service orchestrating defect diagnosis.
- **Relevant Tests**:
  - `tests/test_crew_critic.py`
  - `tests/test_agentic_pipeline.py`
  - `tests/test_adk_generator.py`

### 2.4 Sandbox Execution & Test Result Collection
- **Primary Source Files**:
  - `testforge/sandbox.py`
- **Key Classes & Functions**:
  - `SubprocessSandbox.run_single(test_code, target_code)`: Executes pytest in an isolated subprocess with timeout and memory guards; captures stdout, stderr, and exit codes.
  - `ParallelSandboxRunner.evaluate_mutants_parallel(test_code, mutants)`: Spawns a `ProcessPoolExecutor` across available CPU cores to evaluate multiple mutants concurrently.
  - `SubprocessSandbox.measure_coverage(test_code, target_code)`: Executes tests with `pytest-cov` to extract line coverage percentage, covered lines, and total statement count.
- **Relevant Tests**:
  - `tests/test_cancellation.py`
  - `tests/test_fast_benchmarking.py`

### 2.5 Mutation Generation & Mutant Classification
- **Primary Source Files**:
  - `testforge/mutator.py`
  - `testforge/equivalence.py`
- **Key Classes & Functions**:
  - `ASTMutator.mutate(source_code, target_lines)`: Uses AST node visitors to discover mutation sites and apply deterministic operator mutations.
  - `MutationTransformer`: Applies mutation operators:
    - `COMP_OP`: Inverts comparison operators (`<` to `<=`, `==` to `!=`, etc.).
    - `BOUNDARY_SWAP`: Boundary relational swaps (`<` to `<=`, `>` to `>=`).
    - `BIN_OP`: Swaps arithmetic operators (`+` to `-`, `*` to `/`).
    - `LOGICAL_OP`: Swaps logical operators (`and` to `or`).
    - `NEGATE_COND`: Inverts condition booleans.
    - `RETURN_SWAP`: Modifies return statements.
  - `EquivalenceChecker.classify_mutant(mutant, source_code)`: Static AST pattern matcher identifying mathematically equivalent mutants.
  - `calculate_mutation_scores(mutants)`: Computes `raw_mutation_score` and `adjusted_mutation_score` (excluding verified equivalent mutants from denominator).
- **Relevant Tests**:
  - `tests/test_ast_mutation_m2.py`
  - `tests/test_mutation_scores.py`
  - `tests/test_equivalent_mutants.py`

### 2.6 Benchmark Aggregation & Evaluation Corpus
- **Primary Source Files**:
  - `testforge/benchmarking.py`
  - `testforge/corpus/manager.py`
  - `testforge/corpus/runner.py`
  - `run_benchmark.py`
- **Key Classes & Functions**:
  - `CORPUS_REGISTRY`: The 5 standardized evaluation fixtures:
    1. `task_state_transition` (Finite State Machine, 3 controlled defects, 48 lines)
    2. `token_bucket_rate_limiter` (Token Bucket Algorithm, 3 controlled defects, 50 lines)
    3. `inventory_pricing_calculator` (Tiered Pricing Engine, 3 controlled defects, 44 lines)
    4. `banking_operations_module` (Ledger & KYC Guard, 3 controlled defects, 72 lines)
    5. `currency_converter` (Currency Conversion & Spread, 3 controlled defects, 72 lines)
  - `CorpusRunner.run_evaluation(strategy, fixture_ids)`: Evaluates a testing strategy across the corpus against 15 controlled defects and 201 mutants.
  - `BenchmarkRunner`: Executes Condition A (Baseline), Condition B (Zero-Shot), and Condition C (Reflection) and produces comparative Markdown/JSON summaries.
- **Relevant Tests**:
  - `tests/test_evaluation_corpus.py`
  - `tests/test_strategy_comparison.py`
  - `tests/test_benchmarking.py`
