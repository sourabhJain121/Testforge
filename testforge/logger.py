"""
logger.py - Structured JSON-lines Event Tracer & Observability.

Course: CSE3101 - Agentic AI
Authors: Sourabh & Shreshth

Captures:
  - Agent Prompts & Model Responses
  - Real Prompt Tokens, Completion Tokens, Total Tokens, and Latency (seconds)
  - Tool Invocations (pytest, AST mutator)
  - Iteration-level Mutation Scores and Killed/Survived mutant metrics
  - Validates JSON format appended to testforge_trace.jsonl
"""

from __future__ import annotations
import os
import json
import time
from typing import Dict, Any, Optional

class TraceLogger:
    def __init__(self, log_path: str = "testforge_trace.jsonl"):
        self.log_path = log_path
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

    def log_llm_event(
        self,
        agent_name: str,
        model_name: str,
        prompt: str,
        response_text: str,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int,
        latency_sec: float,
        iteration: int = 1,
        is_valid_ast: bool = True,
        validation_error: str = ""
    ):
        """
        Logs genuine Foundation Model telemetry including real tokens,
        latency in seconds, and AST validation status.
        """
        payload = {
            "agent": agent_name,
            "model": model_name,
            "iteration": iteration,
            "tokens": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens
            },
            "latency_seconds": round(latency_sec, 3),
            "is_valid_ast": is_valid_ast,
            "validation_error": validation_error,
            "prompt_length_chars": len(prompt),
            "response_length_chars": len(response_text),
            "prompt_excerpt": prompt[:300] + ("..." if len(prompt) > 300 else ""),
            "response_snippet": response_text[:300] + ("..." if len(response_text) > 300 else "")
        }
        self.log_event("LLM_INFERENCE_TELEMETRY", payload)

    def get_total_tokens(self) -> int:
        """Calculates total tokens consumed across all LLM calls in this session."""
        traces = self.read_traces()
        total = 0
        for entry in traces:
            if entry.get("event_type") == "LLM_INFERENCE_TELEMETRY":
                tokens = entry.get("data", {}).get("tokens", {})
                total += tokens.get("total_tokens", 0)
        return total

    def read_traces(self) -> list[Dict[str, Any]]:
        """Reads all events logged in the session."""
        if not os.path.exists(self.log_path):
            return []
        traces = []
        with open(self.log_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        traces.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
        return traces
