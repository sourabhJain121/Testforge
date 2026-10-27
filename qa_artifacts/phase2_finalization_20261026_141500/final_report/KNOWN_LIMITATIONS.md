# TestForge — Known Limitations & Prioritized Future Work

**Date:** 2026-10-26  
**Artifact Directory:** `qa_artifacts/phase2_finalization_20261026_141500/final_report/`  
**Engineer:** TestForge Core Engineering  

---

## 1. Functional & Execution Limitations

### 1.1 Process-Level Sandbox Isolation
- **Current Behavior:** Generated test execution is isolated using a Python `subprocess.Popen` execution harness with hard timeouts (default 5.0s), temporary directory confinement, and static AST security inspection.
- **Limitation:** This provides process and resource isolation, but not OS kernel container isolation (no Linux `cgroups`, `chroot`, or gVisor sandbox). Malicious test code targeting kernel exploits or local socket brute-forcing could potentially affect the host if AST rules are somehow bypassed.
- **Mitigation:** Production cloud deployments should always run TestForge worker containers with dropped Linux capabilities (`cap_drop: ALL`) and unprivileged user execution (`user: 10001:10001`).

### 1.2 Local LLM Hardware Latency
- **Current Behavior:** Local inference via Ollama (`qwen2.5-coder:7b`) on CPU takes 15–45 seconds per reflection pass.
- **Limitation:** On constrained machines without Apple Silicon GPU acceleration or dedicated NVIDIA CUDA cards, live multi-iteration reflection can exceed interactive UI timeout thresholds.
- **Mitigation:** The system defaults to bounded timeouts (60s) with seamless failover to Tier 4 AST-Aware Deterministic Synthesis, guaranteeing sub-second completion when live models are slow or offline.

### 1.3 Single-Node SQLite Storage
- **Current Behavior:** Checkpoints and state snapshots are persisted to a local SQLite database (`testforge_checkpoints.db`) with atomic transactions.
- **Limitation:** SQLite is optimized for single-host concurrent access. It does not support horizontal scaling across multi-node Kubernetes clusters.
- **Mitigation:** A storage abstraction layer (`testforge/persistence.py`) defines clean interface methods that can easily be backed by PostgreSQL or AWS DynamoDB for distributed enterprise deployments.

---

## 2. Benchmark & Evaluation Limitations

### 2.1 Benchmark Corpus Size
- **Current Behavior:** The standard evaluation corpus comprises 5 representative reference fixtures (`task_state_transition`, `token_bucket_limiter`, `inventory_allocator`, `banking_ledger`, `currency_converter`) spanning 221 total mutants and 15 ground-truth defects.
- **Limitation:** While highly representative of business and algorithmic logic, N=5 is a focused benchmark. Evaluating large multi-thousand-line monolithic codebases may surface additional syntactic edge cases.
- **Mitigation:** TestForge includes Mode C public GitHub repository ingestion to dynamically evaluate arbitrary open-source Python repositories.

### 2.2 Token Expenditure Bounding
- **Current Behavior:** Evaluated in offline local mode ($0.00 spend).
- **Limitation:** Cloud-based frontier models (Gemini 2.5 Pro, Claude 3.5 Sonnet) were evaluated via local simulated and deterministic paths rather than live multi-hundred-dollar API spend.
- **Mitigation:** The provider client architecture (`testforge/llm_client.py`) is fully wired for Gemini and OpenRouter; adding valid API keys immediately enables frontier models without code changes.

---

## 3. Prioritized Next Steps

1. **Kernel-Level Container Sandboxing:** Introduce Docker-in-Docker or gVisor container runners for executing untrusted candidate tests.
2. **PostgreSQL Checkpoint Backend:** Provide a production-grade distributed persistence adapter for high-availability cloud deployments.
3. **Multi-File Project Refactoring:** Extend AST mutation and blast radius analysis from single-module targets to complete multi-package repository trees.
4. **Adaptive Mutation Sampling:** Implement mutation score predictive sampling (e.g. testing only a statistically representative 20% sample of mutants) to accelerate reflection passes on massive codebases.
