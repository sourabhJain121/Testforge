# ADR-001: Blackboard Pattern for Multi-Agent Consensus and State Sharing

## Status
Accepted

## Context
In a complex multi-agent system like TestForge, specialist agents (e.g., CodeIntelligence, TestGenerator, MutationQualityCritic, TestExecution) need to exchange structured state, intermediate AST representations, mutant kill matrices, and metrics across iterative reflection cycles. Direct point-to-point communication between all pairs creates an $O(N^2)$ coupling explosion, complicates debugging, and prevents reliable checkpointing.

## Decision
We adopted the classic **Blackboard Architectural Pattern** backed by an append-only SQLite database in Write-Ahead Logging (WAL) mode. The Blackboard is partitioned into 8 strongly-typed, schema-validated partition spaces:
1. `TargetSpace`: Source code, file path, LOC, symbols, and syntax trees.
2. `ScopeSpace`: Call graph edges, caller/callee trees, and blast radius risk scores.
3. `SuiteSpace`: Candidate test ASTs, hardened test code, and Pass@1 clean baseline status.
4. `MutantSpace`: AST mutants, operator classes, diff hunks, and 2D kill matrices.
5. `ExecutionSpace`: Subprocess worker telemetry, timeouts, and execution logs.
6. `CriticSpace`: Adversarial critic directives, failure mechanisms, and reflection notes.
7. `MetricsSpace`: Line coverage, branch coverage, and raw/adjusted mutation kill scores.
8. `CheckpointSpace`: Immutable snapshot revisions and transactional diffs.

All accesses are guarded by a thread-safe re-entrant lock (`threading.RLock()`).

## Consequences

### Positive
- **Decoupled Agent Coordination**: Agents observe and update only their relevant partition spaces without knowing the implementation details of upstream or downstream agents.
- **Transactional State Persistence**: Snapshots written to SQLite WAL provide durable point-in-time recovery, crash resumption, and deterministic diffing.
- **Auditability**: Every mutation in state is traceable to a specific agent, iteration, and timestamp.

### Negative / Trade-offs
- Slight serialization overhead when marshaling complete state snapshots to JSON for SQLite storage.
- Requires strict adherence to Pydantic data schemas across all participating agents.

