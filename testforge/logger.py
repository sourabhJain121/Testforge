"""
logger.py - Structured JSON-lines Event Tracer & Observability.

Course: CSE3101 - Agentic AI
Authors: Sourabh & Shreshth

Captures:
  - Agent Prompts & Model Completions
  - Real Prompt Tokens, Completion Tokens, Total Tokens, Latency (ms), and Temperature
  - Tool Invocations (pytest, AST mutator)
  - Mutant survival and kill outcomes
  - MLX GPU triaging telemetry
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

    def log_llm_telemetry(
        self,
        agent_name: str,
        model_name: str,
        prompt: str,
        response_text: str,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int,
        latency_ms: float,
        temperature: float,
        system_instruction: str = "",
        is_live_call: bool = True
    ):
        """
        Specialized logger for real LLM foundation model calls.
        Tracks genuine token usage, latency, and hyperparameter config for viva evaluation.
        """
        telemetry_payload = {
            "agent": agent_name,
            "model": model_name,
            "is_live_api": is_live_call,
            "prompt_length_chars": len(prompt),
            "response_length_chars": len(response_text),
            "tokens": {
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens
            },
            "latency_ms": round(latency_ms, 2),
            "hyperparameters": {
                "temperature": temperature
            },
            "system_instruction": system_instruction,
            "prompt_excerpt": prompt[:300] + ("..." if len(prompt) > 300 else ""),
            "response_snippet": response_text[:300] + ("..." if len(response_text) > 300 else "")
        }
        self.log_event("LLM_INFERENCE_TELEMETRY", telemetry_payload)

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
