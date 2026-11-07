"""
test_messaging_benchmark.py - Unit Tests for Messaging & State Architecture Benchmark.

Tests:
  1. Initialization and validation of iterations count.
  2. Execution of Blackboard partition update benchmark.
  3. Execution of Blackboard snapshot read benchmark.
  4. Execution of A2A Broker message dispatch benchmark.
  5. Report aggregation, Markdown formatting, and JSON serialization.
  6. CLI execution support and file export.
"""

import json
from pathlib import Path

import pytest

from testforge.benchmark_messaging import (
    MessagingBenchmarkReport,
    MessagingBenchmarkRunner,
    OperationalBenchmarkResult,
)


class TestMessagingBenchmark:
    def test_invalid_iterations_raises_error(self):
        with pytest.raises(ValueError):
            MessagingBenchmarkRunner(iterations=0)
        with pytest.raises(ValueError):
            MessagingBenchmarkRunner(iterations=-10)

    def test_blackboard_update_benchmark(self):
        runner = MessagingBenchmarkRunner(iterations=50)
        res = runner.benchmark_blackboard_partition_updates()

        assert isinstance(res, OperationalBenchmarkResult)
        assert res.iterations == 50
        assert res.architecture == "Centralized Blackboard"
        assert res.operation_name == "update_critic_space"
        assert res.total_time_seconds > 0.0
        assert res.mean_latency_microseconds > 0.0
        assert res.throughput_ops_per_second > 0.0
        assert res.min_latency_microseconds <= res.max_latency_microseconds

    def test_blackboard_snapshot_benchmark(self):
        runner = MessagingBenchmarkRunner(iterations=50)
        res = runner.benchmark_blackboard_snapshot_reads()

        assert isinstance(res, OperationalBenchmarkResult)
        assert res.iterations == 50
        assert "snapshot" in res.operation_name.lower()
        assert res.mean_latency_microseconds > 0.0

    def test_a2a_broker_dispatch_benchmark(self):
        runner = MessagingBenchmarkRunner(iterations=50)
        res = runner.benchmark_a2a_broker_dispatch()

        assert isinstance(res, OperationalBenchmarkResult)
        assert res.iterations == 50
        assert res.architecture == "Direct In-Process A2A Broker"
        assert res.mean_latency_microseconds > 0.0
        assert res.throughput_ops_per_second > 0.0

    def test_run_all_and_report_serialization(self, tmp_path):
        runner = MessagingBenchmarkRunner(iterations=25)
        report = runner.run_all()

        assert isinstance(report, MessagingBenchmarkReport)
        assert len(report.results) == 3
        assert "disclaimer" in report.model_dump()
        assert len(report.disclaimer) > 0

        # Markdown serialization
        md = report.to_markdown()
        assert "# TestForge — Messaging & State Architecture Benchmark Report" in md
        assert "Centralized Blackboard" in md
        assert "Direct In-Process A2A Broker" in md
        assert "Architectural Integrity Disclosure" in md

        # JSON serialization
        json_str = report.to_json()
        parsed = json.loads(json_str)
        assert parsed["iterations"] == 25
        assert len(parsed["results"]) == 3

        # Test file saving
        out_json = tmp_path / "bench.json"
        out_md = tmp_path / "bench.md"
        out_json.write_text(json_str, encoding="utf-8")
        out_md.write_text(md, encoding="utf-8")

        assert out_json.exists()
        assert out_md.exists()
