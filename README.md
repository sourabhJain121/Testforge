# TestForge: Autonomous Multi-Agent Unit Test Suite Hardener

> **Course**: CSE3101 - Agentic AI (16 Weeks, Project-Based Learning)  
> **Authors**: Sourabh & Shreshth  
> **Target Platform**: macOS (Apple Silicon M-Series Optimized, arm64)

---

## 1. Overview
**TestForge** is an autonomous multi-agent system that hardens unit test suites for weakly-tested Python programs. Rather than relying on simple line coverage (which can pass trivially even with hollow assertions), TestForge employs **deterministic AST-based mutation testing** as an adversarial self-reflection signal.

### Key Architectural Pillars:
1. **Agentic Patterns**: Planning, ReAct tool execution, and adversarial self-reflection feedback loops.
2. **Deterministic AST Fault Injection (Shreshth)**: Native `ast.NodeTransformer` targeting comparison operators, arithmetic operators, conditional inversions, and return values.
3. **Subprocess Isolation Sandbox (Shreshth)**: Safe execution guardrails with 5s timeout limits and memory isolation to neutralize mutation-induced infinite loops.
4. **Hardware-Accelerated Parallel Execution**: Sized for Apple Silicon M2 Pro (10 cores, 8 parallel workers) via `ProcessPoolExecutor`.
5. **State Graph & Dynamic Prompting (Sourabh)**: Multi-agent orchestration feeding surviving mutant unified diffs directly into the Test Generator to harden assertions.
6. **Structured Observability**: Event-level JSON-lines trace log (`testforge_trace.jsonl`) recording prompts, tool calls, and kill scores for viva examination.

---

## 2. Directory Structure
```
TestForge/
├── requirements.txt
├── run_demo.py                     # Deterministic end-to-end benchmark driver
├── testforge_trace.jsonl           # JSON-lines structured telemetry
├── testforge/
│   ├── __init__.py
│   ├── accel.py                    # Apple Silicon hardware discovery & MLX/MPS hooks
│   ├── state.py                    # Typed Pydantic state contracts
│   ├── mutator.py                  # Deterministic AST mutation engine
│   ├── sandbox.py                  # Multi-process sandboxed runner with timeouts
│   ├── logger.py                   # Event-level JSONL tracer
│   ├── agents.py                   # TestGenerator & AdversarialCritic agents
│   ├── orchestrator.py             # Agent state graph & reflection loop controller
│   └── cli.py                      # CLI runner interface
├── samples/
│   ├── banking.py                  # Sample target with subtle boundary conditions
│   └── discount.py                 # E-commerce rule engine
└── tests/
    ├── test_mutator.py             # Unit tests for AST fault injector
    └── test_sandbox.py             # Unit tests for sandbox isolation & timeouts
```

---

## 3. Quickstart & Installation

```bash
# 1. Clone & enter repository
cd /Users/sourabh/TestForge

# 2. Activate virtual environment
source .venv/bin/activate

# 3. Run unit tests
python -m pytest tests/ -v

# 4. Run end-to-end demo benchmark
python run_demo.py
```

---

## 4. Running TestForge CLI

```bash
python -m testforge.cli --target samples/banking.py --max-iter 3 --target-score 85.0 --output test_hardened.py
```

### Options:
- `--target, -t`: Path to target Python module under test.
- `--tests, -s`: Path to optional baseline test suite.
- `--max-iter, -i`: Maximum reflection iterations (default: 3).
- `--target-score, -score`: Target mutation score percentage (default: 85.0%).
- `--output, -o`: File path where hardened tests will be exported.

---

## 5. Coursework & Viva Evaluation Highlights

- **Line Coverage vs. Mutation Score Proof**: A weak test suite that attains 86.7% line coverage will only score 66.7% against TestForge AST mutants.
- **Reflection Hardening**: Upon inspecting the surviving mutant unified diffs, the system hardens boundary assertions and raises the score to **91.7%**, satisfying the project passing criterion ($\ge 85\%$).
- **Apple Silicon Parallelism**: 12 mutants evaluated concurrently in under 0.7 seconds on M2 Pro.
- **Trace Audit**: Full telemetry available in `testforge_trace.jsonl`.
