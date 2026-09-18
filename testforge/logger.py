"""
logger.py - Structured JSON-lines Event Tracer & Observability.

Course: CSE3101 - Agentic AI
Authors: Sourabh & Shreshth

Captures:
  - Agent Prompts & Model Completions
  - Tool Invocations (pytest, ast mutator)
  - Mutant survival and kill events
  - Token consumption & duration timings
"""

from __future__ import annotations
import os
import json
import time
from typing import Dict, Any, Optional

class TraceLogger:
    def __init__(self, log_path: str = "testforge_trace.jsonl"):
        self.log_path = log_path
        # Ensure log directory exists if nested
        log_dir = os.path.dirname(self.log_path)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

    def log_event(self, event_type: str, data: Dict[str, Any], metadata: Optional[Dict[str, Any]] = None):
        """
        Appends an event record formatted in standard JSON-lines format.
        """
        record = {
            "timestamp": time.time(),
            "iso_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            "event_type": event_type,
            "data": data,
            "metadata": metadata or {}
        }
        with open(self.log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

    def read_traces(self) -> list[Dict[str, Any]]:
        """Reads all events logged in the session."""
        if not os.path.exists(self.log_path):
            return []
        traces = []
        with open(self.log_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    traces.append(json.loads(line))
        return traces
