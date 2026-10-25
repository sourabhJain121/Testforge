"""
benchmark_messaging.py - Empirical Messaging & State Architecture Benchmark for TestForge.

Author: TestForge Agentic Architecture Team
Course: CSE3101 - Agentic AI

Features:
  1. Microsecond-level operational latency and throughput benchmarking comparing:
     - Shared Blackboard State Operations (Centralized partition mutation, thread locking, validation, snapshots).
     - A2A Broker Message Dispatch (Pydantic envelope validation, sender/action authorization, handler routing).
  2. Rigorous separation of setup from measured loop execution.
  3. Statistical aggregation: Mean, standard deviation, min, max, throughput (ops/sec).
  4. Explicit architectural disclosure:
     - State mutation and message dispatch are fundamentally different semantic abstractions.
     - Neither architecture is "universally faster"; they serve complementary decoupled roles.
  5. Machine-readable JSON export and GitHub-flavored Markdown formatting.
"""

from __future__ import annotations
import time
import math
import json
import argparse
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

from testforge.blackboard import Blackboard
from testforge.a2a import (
    A2ABroker,
    A2AMessage,
    A2APerformative,
    CriticDirectivePayload,
)


class OperationalBenchmarkResult(BaseModel):
    architecture: str
    operation_name: str
    iterations: int
    total_time_seconds: float
    mean_latency_microseconds: float
    stddev_latency_microseconds: float
    min_latency_microseconds: float
    max_latency_microseconds: float
    throughput_ops_per_second: float
    metadata: Dict[str, Any] = Field(default_factory=dict)


class MessagingBenchmarkReport(BaseModel):
    timestamp: float = Field(default_factory=time.time)
    iterations: int
    results: List[OperationalBenchmarkResult] = Field(default_factory=list)
    semantic_comparison: Dict[str, Any] = Field(default_factory=dict)
    disclaimer: str

    def to_markdown(self) -> str:
        lines = [
            "# TestForge — Messaging & State Architecture Benchmark Report",
            f"- **Timestamp:** {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.timestamp))}",
            f"- **Iterations per Benchmark:** {self.iterations:,}",
            "",
            "## Empirical Performance Summary",
            "",
            "| Architecture | Operation | Iterations | Total Time (s) | Mean Latency (μs) | StdDev (μs) | Throughput (ops/s) |",
            "|:---|:---|:---|:---|:---|:---|:---|",
        ]
        for r in self.results:
            lines.append(
                f"| **{r.architecture}** | {r.operation_name} | {r.iterations:,} | "
                f"{r.total_time_seconds:.4f}s | {r.mean_latency_microseconds:.2f} μs | "
                f"±{r.stddev_latency_microseconds:.2f} μs | {r.throughput_ops_per_second:,.0f} ops/s |"
            )

        lines.extend([
            "",
            "## Semantic & Architectural Comparison",
            "",
            "| Architectural Dimension | Centralized Shared Blackboard | Direct In-Process A2A Broker |",
            "|:---|:---|:---|",
            "| **Primary Abstraction** | Decoupled Shared Knowledge State | Point-to-Point Communicative Acts |",
            "| **Coupling Model** | $O(1)$ Pub/Sub & Partition Readers | $O(N)$ Addressable Identity Routing |",
            "| **Concurrency & Synchronization** | Re-entrant `threading.RLock()` | Bounded `ThreadPoolExecutor` Workers |",
            "| **State Persistence** | SQLite Snapshots & Checkpoints | Ephemeral In-Memory Envelope History |",
            "| **Validation Point** | Fail-Closed Partition Pydantic Schemas | Pre/Post Envelope Pydantic Contracts |",
            "| **Security Inspection** | Passive Secret Scrubbing on Save | Active Prompt Injection Guardrails |",
            "",
            "> [!NOTE]",
            "> **Architectural Integrity Disclosure:**",
            f"> {self.disclaimer}",
            ""
        ])
        return "\n".join(lines)

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.model_dump(), indent=indent)


class MessagingBenchmarkRunner:
    """
    Executes repeatable, zero-cost operational latency benchmarks comparing
    Blackboard state transactions against A2A Broker message dispatches.
    """
    def __init__(self, iterations: int = 1000):
        if iterations <= 0:
            raise ValueError("Iterations must be a positive integer.")
        self.iterations = iterations

    def benchmark_blackboard_partition_updates(self) -> OperationalBenchmarkResult:
        """Benchmarks atomic updates to Blackboard CriticSpace partition."""
        bb = Blackboard()
        # Pre-warm
        bb.update_critic_space(latest_directive="warmup", reflection_notes=["note0"])

        durations_us: List[float] = []
        t_start = time.perf_counter()

        for i in range(self.iterations):
            t0 = time.perf_counter()
            bb.update_critic_space(
                latest_directive=f"Directive {i}",
                reflection_notes=[f"Reflection {i}"],
                failure_mechanisms={"MUT_01": f"OffByOne error in step {i}"}
            )
            t1 = time.perf_counter()
            durations_us.append((t1 - t0) * 1_000_000.0)

        total_sec = time.perf_counter() - t_start
        mean_us = sum(durations_us) / len(durations_us)
        variance = sum((d - mean_us) ** 2 for d in durations_us) / len(durations_us) if len(durations_us) > 1 else 0.0
        stddev_us = math.sqrt(variance)

        return OperationalBenchmarkResult(
            architecture="Centralized Blackboard",
            operation_name="update_critic_space",
            iterations=self.iterations,
            total_time_seconds=round(total_sec, 6),
            mean_latency_microseconds=round(mean_us, 3),
            stddev_latency_microseconds=round(stddev_us, 3),
            min_latency_microseconds=round(min(durations_us), 3),
            max_latency_microseconds=round(max(durations_us), 3),
            throughput_ops_per_second=round(self.iterations / total_sec, 1) if total_sec > 0 else 0.0,
            metadata={
                "locking": "threading.RLock",
                "validation": "Pydantic v2 CriticSpace",
                "revision_increment": True,
            }
        )

    def benchmark_blackboard_snapshot_reads(self) -> OperationalBenchmarkResult:
        """Benchmarks deep-copy defensive snapshot isolation of Blackboard."""
        bb = Blackboard()
        bb.update_critic_space(latest_directive="initial", reflection_notes=["n1", "n2"])

        durations_us: List[float] = []
        t_start = time.perf_counter()

        for _ in range(self.iterations):
            t0 = time.perf_counter()
            _ = bb.get_snapshot()
            t1 = time.perf_counter()
            durations_us.append((t1 - t0) * 1_000_000.0)

        total_sec = time.perf_counter() - t_start
        mean_us = sum(durations_us) / len(durations_us)
        variance = sum((d - mean_us) ** 2 for d in durations_us) / len(durations_us) if len(durations_us) > 1 else 0.0
        stddev_us = math.sqrt(variance)

        return OperationalBenchmarkResult(
            architecture="Centralized Blackboard",
            operation_name="get_state_snapshot (Deep-Copy)",
            iterations=self.iterations,
            total_time_seconds=round(total_sec, 6),
            mean_latency_microseconds=round(mean_us, 3),
            stddev_latency_microseconds=round(stddev_us, 3),
            min_latency_microseconds=round(min(durations_us), 3),
            max_latency_microseconds=round(max(durations_us), 3),
            throughput_ops_per_second=round(self.iterations / total_sec, 1) if total_sec > 0 else 0.0,
            metadata={
                "isolation": "deepcopy",
                "thread_safety": "RLock guarded",
            }
        )

    def benchmark_a2a_broker_dispatch(self) -> OperationalBenchmarkResult:
        """Benchmarks full A2A Broker envelope validation, authorization, and dispatch."""
        broker = A2ABroker()

        # Register minimal synchronous mock agent handler
        def echo_critic_handler(msg: A2AMessage) -> A2AMessage:
            return msg.create_response(
                performative=A2APerformative.INFORM,
                payload={"status": "acknowledged", "directive": "Assert boundary"},
                action="diagnose_mutants"
            )

        broker.register_handler("agent:crewai:critic", echo_critic_handler)

        durations_us: List[float] = []
        t_start = time.perf_counter()

        for i in range(self.iterations):
            req = A2AMessage(
                correlation_id=f"corr_{i}",
                sender="agent:orchestrator",
                recipient="agent:crewai:critic",
                performative=A2APerformative.REQUEST,
                action="diagnose_mutants",
                payload={"target_func": "calculate_discount", "iteration": i}
            )
            t0 = time.perf_counter()
            resp = broker.send_message(req)
            t1 = time.perf_counter()
            assert resp.performative == A2APerformative.INFORM
            durations_us.append((t1 - t0) * 1_000_000.0)

        total_sec = time.perf_counter() - t_start
        mean_us = sum(durations_us) / len(durations_us)
        variance = sum((d - mean_us) ** 2 for d in durations_us) / len(durations_us) if len(durations_us) > 1 else 0.0
        stddev_us = math.sqrt(variance)

        return OperationalBenchmarkResult(
            architecture="Direct In-Process A2A Broker",
            operation_name="send_message (Request-Response)",
            iterations=self.iterations,
            total_time_seconds=round(total_sec, 6),
            mean_latency_microseconds=round(mean_us, 3),
            stddev_latency_microseconds=round(stddev_us, 3),
            min_latency_microseconds=round(min(durations_us), 3),
            max_latency_microseconds=round(max(durations_us), 3),
            throughput_ops_per_second=round(self.iterations / total_sec, 1) if total_sec > 0 else 0.0,
            metadata={
                "routing": "Dynamic handler dispatch",
                "envelope": "Pydantic A2AMessage v2",
                "security": "Prompt injection inspection & history recording",
            }
        )

    def run_all(self) -> MessagingBenchmarkReport:
        res1 = self.benchmark_blackboard_partition_updates()
        res2 = self.benchmark_blackboard_snapshot_reads()
        res3 = self.benchmark_a2a_broker_dispatch()

        disclaimer = (
            "State mutation and message dispatch are not semantically identical abstractions. "
            "Blackboard provides durable, thread-safe shared data partitions with point-in-time snapshots and history tracking. "
            "A2A Broker provides decoupled peer-to-peer communicative acts with prompt security, authorization, and handoff tracing. "
            "Neither is universally faster; both operate concurrently within TestForge's multi-agent architecture."
        )

        return MessagingBenchmarkReport(
            iterations=self.iterations,
            results=[res1, res2, res3],
            semantic_comparison={
                "blackboard_use_cases": ["TargetSpace call graphs", "Mutant execution status", "Checkpoint persistence"],
                "broker_use_cases": ["ADK to CrewAI handoff", "Adversarial critique requests", "External A2A protocol bridge"]
            },
            disclaimer=disclaimer
        )


def main():
    parser = argparse.ArgumentParser(description="TestForge Messaging & State Architecture Benchmark")
    parser.add_argument("--iterations", "-n", type=int, default=500, help="Iterations per operation (default: 500)")
    parser.add_argument("--output-json", "-j", type=str, default=None, help="Optional path to output JSON report")
    parser.add_argument("--output-markdown", "-m", type=str, default=None, help="Optional path to output Markdown report")
    args = parser.parse_args()

    runner = MessagingBenchmarkRunner(iterations=args.iterations)
    report = runner.run_all()

    print(report.to_markdown())

    if args.output_json:
        with open(args.output_json, "w", encoding="utf-8") as f:
            f.write(report.to_json())
        print(f"\nSaved JSON report to: {args.output_json}")

    if args.output_markdown:
        with open(args.output_markdown, "w", encoding="utf-8") as f:
            f.write(report.to_markdown())
        print(f"Saved Markdown report to: {args.output_markdown}")


if __name__ == "__main__":
    main()
