"""
tests/test_distributed_cross_process_a2a.py

Verification tests for Stage 2.3: Distributed Cross-Process A2A Execution.
Verifies:
  1. Spawning the standalone Critic worker produces a distinct OS PID from the test runner.
  2. Cross-process A2A requests execute remotely with critic_pid != parent_pid.
  3. Stopping the remote process triggers clean, non-blocking in-process fallback.
  4. Both modes return valid critique directives for survivor guidance.
"""

import os
from pathlib import Path

import pytest

from testforge.a2a_distributed import CriticProcessManager, DistributedCriticClient


def test_cross_process_critic_dual_pids_and_fallback():
    parent_pid = os.getpid()
    port = 8019  # High port for test isolation
    manager = CriticProcessManager(port=port)
    client = DistributedCriticClient(port=port, in_process_fallback=True)

    try:
        # 1. Start out-of-process Critic service
        worker_pid = manager.start(timeout_sec=5.0)
        assert worker_pid is not None
        assert worker_pid != parent_pid, f"Worker PID {worker_pid} must differ from parent {parent_pid}"
        assert manager.is_running() is True

        # 2. Issue cross-process A2A request
        source = "def add(a, b): return a + b"
        tests = "def test_add(): assert add(1, 2) == 3"
        mutants = [{"mutant_id": "MUT_001", "description": "a - b", "line_number": 1}]

        res_remote = client.diagnose_mutants(source, tests, mutants, iteration=1)
        assert res_remote["status"] == "SUCCESS"
        assert res_remote["critic_pid"] == worker_pid
        assert res_remote["critic_pid"] != parent_pid
        assert client.last_execution_mode == "CROSS_PROCESS"
        assert "directive" in res_remote

        # 3. Stop remote worker to test in-process fallback
        manager.stop()
        assert manager.is_running() is False

        # 4. Issue request again; must execute via in-process fallback
        res_fallback = client.diagnose_mutants(source, tests, mutants, iteration=2)
        assert res_fallback["status"] == "FALLBACK_SUCCESS"
        assert res_fallback["critic_pid"] == parent_pid
        assert client.last_execution_mode == "IN_PROCESS_FALLBACK"
        assert "directive" in res_fallback

    finally:
        manager.stop()

