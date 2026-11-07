"""
testforge/a2a_distributed.py

Stage 2.3: Distributed Cross-Process Agent2Agent (A2A) Execution.
Coordinates the MutationQualityCriticAgent running in an isolated OS process
communicating via A2A wire protocol, capturing distinct PIDs in audit logs,
with guaranteed in-process fallback when the external process is unreachable.
"""

from __future__ import annotations

import json
import logging
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional

from testforge.crew_critic import MutationQualityCriticAgent

logger = logging.getLogger("testforge.a2a_distributed")


class CriticProcessManager:
    """
    Manages the lifecycle of an out-of-process standalone A2A Critic daemon.
    """
    def __init__(self, port: int = 8011, host: str = "127.0.0.1"):
        self.port = port
        self.host = host
        self.process: Optional[subprocess.Popen] = None
        self.worker_pid: Optional[int] = None

    def start(self, timeout_sec: float = 5.0) -> int:
        """Starts the standalone Critic worker process and waits for readiness."""
        if self.is_running():
            return self.worker_pid or 0

        python_bin = sys.executable
        cmd = [
            python_bin,
            "-m", "testforge.scripts.run_critic_service",
            "--host", self.host,
            "--port", str(self.port)
        ]
        repo_root = Path(__file__).parent.parent.resolve()
        env = dict(os.environ)
        env["PYTHONPATH"] = str(repo_root)

        logger.info("Spawning external A2A Critic process: %s", " ".join(cmd))
        self.process = subprocess.Popen(
            cmd,
            cwd=str(repo_root),
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        self.worker_pid = self.process.pid

        # Wait for healthcheck readiness
        start_t = time.perf_counter()
        ready = False
        while time.perf_counter() - start_t < timeout_sec:
            try:
                url = f"http://{self.host}:{self.port}/healthz"
                with urllib.request.urlopen(url, timeout=0.5) as resp:
                    if resp.status == 200:
                        ready = True
                        break
            except Exception:
                time.sleep(0.1)

        if not ready:
            self.stop()
            raise RuntimeError(f"Standalone Critic worker failed to start on port {self.port} within {timeout_sec}s")

        logger.info("[A2A Cross-Process Gateway] Remote Critic worker online. Parent PID: %d, Worker PID: %d",
                    os.getpid(), self.worker_pid)
        return self.worker_pid

    def is_running(self) -> bool:
        if self.process is None:
            return False
        return self.process.poll() is None

    def stop(self) -> None:
        """Terminates the worker process cleanly."""
        if self.process and self.is_running():
            logger.info("Terminating external Critic worker PID: %d", self.worker_pid or 0)
            self.process.terminate()
            try:
                self.process.wait(timeout=2.0)
            except subprocess.TimeoutExpired:
                self.process.kill()
        self.process = None
        self.worker_pid = None


class DistributedCriticClient:
    """
    A2A Client communicating with the out-of-process Critic service,
    with automatic in-process fallback if remote worker is dead.
    """
    def __init__(self, port: int = 8011, host: str = "127.0.0.1", in_process_fallback: bool = True):
        self.port = port
        self.host = host
        self.in_process_fallback = in_process_fallback
        self._fallback_critic = MutationQualityCriticAgent(use_live_llm=False)
        self.last_execution_mode: Optional[str] = None  # "CROSS_PROCESS" or "IN_PROCESS_FALLBACK"
        self.last_parent_pid: Optional[int] = None
        self.last_critic_pid: Optional[int] = None

    def diagnose_mutants(
        self,
        target_source: str,
        existing_tests: str,
        surviving_mutants: List[Any],
        iteration: int = 1
    ) -> Dict[str, Any]:
        """
        Routes critique request to out-of-process Critic worker over HTTP.
        Falls back cleanly to in-process execution if unreachable.
        """
        caller_pid = os.getpid()
        self.last_parent_pid = caller_pid

        # Format serializable mutants
        serializable_mutants = []
        for m in surviving_mutants:
            if hasattr(m, "model_dump"):
                serializable_mutants.append(m.model_dump())
            elif isinstance(m, dict):
                serializable_mutants.append(m)
            else:
                serializable_mutants.append(str(m))

        payload = {
            "caller_pid": caller_pid,
            "target_source": target_source,
            "existing_tests": existing_tests,
            "surviving_mutants": serializable_mutants,
            "iteration": iteration,
        }

        url = f"http://{self.host}:{self.port}/a2a/critic/diagnose"
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={"Content-Type": "application/json"}
            )
            with urllib.request.urlopen(req, timeout=5.0) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                remote_pid = data.get("critic_pid")
                self.last_critic_pid = remote_pid
                self.last_execution_mode = "CROSS_PROCESS"

                logger.info("[A2A Cross-Process Dispatch] Parent PID: %d, Remote Critic Worker PID: %d (Distinct: %s)",
                            caller_pid, remote_pid, caller_pid != remote_pid)
                return data

        except Exception as exc:
            if not self.in_process_fallback:
                raise RuntimeError(f"Remote A2A Critic call failed on {url}: {exc}") from exc

            logger.warning("[A2A In-Process Fallback] Remote Critic unreachable on %s (%s). "
                           "Falling back to in-process execution in PID: %d", url, exc, caller_pid)
            self.last_execution_mode = "IN_PROCESS_FALLBACK"
            self.last_critic_pid = caller_pid

            surviving_diffs = [
                m.get("unified_diff", m.get("description", "")) if isinstance(m, dict) else getattr(m, "unified_diff", str(m))
                for m in surviving_mutants
            ]
            directive = self._fallback_critic.diagnose_mutants(
                target_source_code=target_source,
                surviving_diffs=surviving_diffs,
                surviving_mutants=surviving_mutants,
                iteration=iteration
            )
            return {
                "status": "FALLBACK_SUCCESS",
                "critic_pid": caller_pid,
                "directive": directive.model_dump() if hasattr(directive, "model_dump") else directive,
            }
