# TestForge — Messaging & State Architecture Benchmark Report
- **Timestamp:** 2026-10-23 16:24:04
- **Iterations per Benchmark:** 500

## Empirical Performance Summary

| Architecture | Operation | Iterations | Total Time (s) | Mean Latency (μs) | StdDev (μs) | Throughput (ops/s) |
|:---|:---|:---|:---|:---|:---|:---|
| **Centralized Blackboard** | update_critic_space | 500 | 0.0074s | 14.82 μs | ±63.47 μs | 67,134 ops/s |
| **Centralized Blackboard** | get_state_snapshot (Deep-Copy) | 500 | 0.0135s | 26.55 μs | ±4.08 μs | 36,948 ops/s |
| **Direct In-Process A2A Broker** | send_message (Request-Response) | 500 | 0.0576s | 107.66 μs | ±21.20 μs | 8,673 ops/s |

## Semantic & Architectural Comparison

| Architectural Dimension | Centralized Shared Blackboard | Direct In-Process A2A Broker |
|:---|:---|:---|
| **Primary Abstraction** | Decoupled Shared Knowledge State | Point-to-Point Communicative Acts |
| **Coupling Model** | $O(1)$ Pub/Sub & Partition Readers | $O(N)$ Addressable Identity Routing |
| **Concurrency & Synchronization** | Re-entrant `threading.RLock()` | Bounded `ThreadPoolExecutor` Workers |
| **State Persistence** | SQLite Snapshots & Checkpoints | Ephemeral In-Memory Envelope History |
| **Validation Point** | Fail-Closed Partition Pydantic Schemas | Pre/Post Envelope Pydantic Contracts |
| **Security Inspection** | Passive Secret Scrubbing on Save | Active Prompt Injection Guardrails |

> [!NOTE]
> **Architectural Integrity Disclosure:**
> State mutation and message dispatch are not semantically identical abstractions. Blackboard provides durable, thread-safe shared data partitions with point-in-time snapshots and history tracking. A2A Broker provides decoupled peer-to-peer communicative acts with prompt security, authorization, and handoff tracing. Neither is universally faster; both operate concurrently within TestForge's multi-agent architecture.
