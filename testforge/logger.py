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

    def log_event(
        self,
        event_type: str,
        data: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
    ):
        """
        Appends an event record formatted in standard JSON-lines format.
        """
        meta = dict(metadata or {})
        w_id = workflow_id or meta.get("workflow_id")
        c_id = correlation_id or meta.get("correlation_id")
        record = {
            "timestamp": time.time(),
            "iso_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            "event_type": event_type,
            "workflow_id": w_id,
            "correlation_id": c_id,
            "data": data,
            "metadata": meta
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
        validation_error: str = "",
        provider_type: Optional[str] = None
    ):
        """
        Logs genuine Foundation Model telemetry including real tokens,
        latency in seconds, provider type, and AST validation status.
        """
        resolved_provider = provider_type or (model_name.split(":")[0] if ":" in model_name else "Unknown")
        payload = {
            "agent": agent_name,
            "model": model_name,
            "provider_type": resolved_provider,
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

    def get_events_by_correlation_id(self, correlation_id: str) -> list[Dict[str, Any]]:
        """Returns all events sharing the given correlation ID in chronological order."""
        return [
            entry for entry in self.read_traces()
            if entry.get("correlation_id") == correlation_id
            or entry.get("metadata", {}).get("correlation_id") == correlation_id
        ]

    def get_events_by_type(self, event_type: str) -> list[Dict[str, Any]]:
        """Returns all events matching a specific event type."""
        return [
            entry for entry in self.read_traces()
            if entry.get("event_type") == event_type
        ]

    def get_security_refusals(self) -> list[Dict[str, Any]]:
        """Returns all security refusal events."""
        return [
            entry for entry in self.read_traces()
            if "SECURITY_REFUSAL" in entry.get("event_type", "")
        ]

    def get_audit_summary(self) -> Dict[str, Any]:
        """Provides an aggregated audit summary of execution traces."""
        traces = self.read_traces()
        total_events = len(traces)
        event_types: Dict[str, int] = {}
        unique_correlations = set()
        error_count = 0
        security_refusals = 0

        for t in traces:
            etype = t.get("event_type", "UNKNOWN")
            event_types[etype] = event_types.get(etype, 0) + 1
            cid = t.get("correlation_id") or t.get("metadata", {}).get("correlation_id")
            if cid:
                unique_correlations.add(cid)
            if "ERROR" in etype or t.get("data", {}).get("outcome") == "FAILED":
                error_count += 1
            if "SECURITY_REFUSAL" in etype or "REFUSAL" in etype:
                security_refusals += 1

        return {
            "total_events": total_events,
            "event_type_breakdown": event_types,
            "unique_correlation_ids_count": len(unique_correlations),
            "error_count": error_count,
            "security_refusals_count": security_refusals,
            "total_tokens_consumed": self.get_total_tokens(),
        }

    def get_provenance_chain(self, mutant_id: str) -> Dict[str, Any]:
        """
        Reconstructs the full lifecycle provenance for a specific mutant:
        creation -> surviving AST diff -> critic directive -> hardened test -> final status.
        """
        traces = self.read_traces()
        related_events = []
        for t in traces:
            t_str = json.dumps(t)
            if mutant_id in t_str:
                related_events.append({
                    "timestamp": t.get("timestamp"),
                    "event_type": t.get("event_type"),
                    "data": t.get("data"),
                })
        return {
            "mutant_id": mutant_id,
            "event_count": len(related_events),
            "events": related_events,
        }
