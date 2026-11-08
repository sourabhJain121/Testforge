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

import json
import os
import time
from collections import Counter
from typing import Any, Dict, List, Optional, Tuple


def resolve_dynamic_execution_engine(
    model_name: Optional[str],
    provider_type: Optional[str] = None,
    is_actual_llm: Optional[bool] = None
) -> Tuple[str, Optional[str], Optional[str]]:
    """
    Dynamically identifies the execution engine, provider, and clean model name.
    Returns: (execution_engine_label, normalized_provider, normalized_model_name)
    """
    lower_model = (model_name or "").lower()
    lower_prov = (provider_type or "").lower()

    # Deterministic AST Synthesizer
    if (
        is_actual_llm is False
        or "deterministic" in lower_model
        or "ast" in lower_model
        or lower_prov in ["deterministic synthesizer", "ast synthesizer", "deterministic"]
    ):
        return ("Deterministic AST Synthesizer", None, None)

    # Genuine LLM providers
    if is_actual_llm is True or (
        is_actual_llm is None
        and any(k in lower_model or k in lower_prov for k in ["gemini", "ollama", "openrouter", "codellama", "qwen", "llama", "claude"])
    ):
        # Google Gemini
        if "gemini" in lower_prov or "gemini" in lower_model:
            clean = model_name or "gemini-3.6-flash"
            if clean.startswith("Cloud Gemini:"):
                clean = clean[len("Cloud Gemini:"):].strip()
            elif ":" in clean and "gemini" in clean.split(":")[-1].lower():
                clean = clean.split(":")[-1].strip()
            clean = clean.strip()
            return (f"Gemini – {clean}", "Google GenAI", clean)

        # CodeLlama through Ollama
        if "codellama" in lower_model or "codellama" in lower_prov:
            clean = model_name or "codellama:7b"
            if clean.startswith("Local Ollama:"):
                clean = clean[len("Local Ollama:"):].strip()
            clean = clean.strip()
            return ("CodeLlama (Ollama / Local)", "Local Ollama", clean)

        # Other Ollama / Local model
        if "ollama" in lower_prov or "ollama" in lower_model or "qwen" in lower_model or "starcoder" in lower_model:
            clean = model_name or "local-model"
            if clean.startswith("Local Ollama:"):
                clean = clean[len("Local Ollama:"):].strip()
            clean = clean.strip()
            return (f"{clean} (Ollama / Local)", "Local Ollama", clean)

        # OpenRouter
        if "openrouter" in lower_prov or "openrouter" in lower_model:
            clean = model_name or "openrouter-model"
            if clean.startswith("OpenRouter:"):
                clean = clean[len("OpenRouter:"):].strip()
            clean = clean.strip()
            return (f"{clean} (OpenRouter)", "OpenRouter", clean)

        # Other explicit provider
        if provider_type and provider_type not in ("Unknown", "None", ""):
            lbl = f"{model_name} ({provider_type})" if model_name else provider_type
            return (lbl, provider_type, model_name)

    # Legacy or unknown
    if is_actual_llm is True:
        return ("Unknown / Legacy", "Unknown / Legacy", "Unknown / Legacy")
    return ("Deterministic AST Synthesizer", None, None)


def determine_scope_execution_engine(engine_labels: List[str]) -> str:
    """
    Determines scope-level execution engine label from a list of record engine labels.
    - If 0 records: 'No Execution Yet'
    - If all records have the same engine: that engine label (e.g. 'Deterministic AST Synthesizer')
    - If multiple different engines exist: 'Mixed Execution Engines'
    """
    if not engine_labels:
        return "No Execution Yet"
    unique = sorted(list(set(engine_labels)))
    if len(unique) == 1:
        return unique[0]
    return "Mixed Execution Engines"


class TraceLogger:
    def __init__(self, log_path: str = "testforge_trace.jsonl"):
        self.log_path = log_path
        self.default_workflow_id: Optional[str] = None
        self.default_correlation_id: Optional[str] = None
        self._session_actual_llm_tokens: int = 0
        self._session_total_tokens: int = 0
        self._session_events: list[Dict[str, Any]] = []
        log_dir = os.path.dirname(self.log_path)
        if log_dir and not os.path.exists(log_dir):
            os.makedirs(log_dir, exist_ok=True)

    def set_context(self, workflow_id: Optional[str] = None, correlation_id: Optional[str] = None) -> None:
        """Sets the ambient run context (workflow/correlation ID) for subsequent logged events."""
        if workflow_id is not None:
            self.default_workflow_id = workflow_id
        if correlation_id is not None:
            self.default_correlation_id = correlation_id

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
        w_id = workflow_id or meta.get("workflow_id") or self.default_workflow_id
        c_id = correlation_id or meta.get("correlation_id") or self.default_correlation_id
        record = {
            "timestamp": time.time(),
            "iso_time": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime()),
            "event_type": event_type,
            "workflow_id": w_id,
            "correlation_id": c_id,
            "data": data,
            "metadata": meta
        }
        self._session_events.append(record)
        if len(self._session_events) > 5000:
            self._session_events.pop(0)

        # Auto-rotate log if larger than 10MB to prevent unbounded disk & memory bloat
        try:
            if os.path.exists(self.log_path) and os.path.getsize(self.log_path) > 10 * 1024 * 1024:
                old_path = self.log_path + ".old"
                if os.path.exists(old_path):
                    os.remove(old_path)
                os.rename(self.log_path, old_path)
                TraceLogger._FILE_CACHES.pop(os.path.abspath(self.log_path), None)
        except Exception:
            pass

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
        provider_type: Optional[str] = None,
        is_actual_llm: Optional[bool] = None,
        token_accounting_source: Optional[str] = None,
        correlation_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
    ):
        """
        Logs Foundation Model and Synthesizer telemetry, explicitly distinguishing
        actual provider LLM token consumption from deterministic synthesis and offline
        heuristic estimations.
        """
        w_id = workflow_id or self.default_workflow_id
        c_id = correlation_id or self.default_correlation_id
        lower_name = (model_name or "").lower()
        if is_actual_llm is None:
            if "deterministic" in lower_name or "ast" in lower_name or provider_type in ["Deterministic Synthesizer", "AST Synthesizer", "Deterministic"]:
                is_actual_llm = False
            else:
                is_actual_llm = True

        if token_accounting_source is None:
            token_accounting_source = "provider_reported" if is_actual_llm else "offline_heuristic_estimate"

        engine_lbl, resolved_provider, resolved_model = resolve_dynamic_execution_engine(
            model_name=model_name,
            provider_type=provider_type,
            is_actual_llm=is_actual_llm
        )

        # For deterministic AST synthesis, explicitly record:
        # provider = None, model_name = None, execution_engine = "AST Deterministic Synthesizer", is_actual_llm = False, actual_total_tokens = 0
        if not is_actual_llm:
            provider_field = None
            model_field = None
            engine_field = "AST Deterministic Synthesizer"
            actual_p = 0
            actual_c = 0
            actual_t = 0
            est_p = prompt_tokens
            est_c = completion_tokens
            est_t = total_tokens
        else:
            provider_field = resolved_provider
            model_field = resolved_model
            engine_field = engine_lbl
            actual_p = prompt_tokens
            actual_c = completion_tokens
            actual_t = total_tokens
            est_p = 0
            est_c = 0
            est_t = 0

        payload = {
            "agent": agent_name,
            "provider": provider_field,
            "model_name": model_field,
            "execution_engine": engine_field,
            "is_actual_llm": is_actual_llm,
            "token_accounting_source": token_accounting_source,
            "workflow_id": w_id,
            "correlation_id": c_id,
            "latency_seconds": round(latency_sec, 3),
            "actual_prompt_tokens": actual_p,
            "actual_completion_tokens": actual_c,
            "actual_total_tokens": actual_t,
            "estimated_prompt_tokens": est_p,
            "estimated_completion_tokens": est_c,
            "estimated_total_tokens": est_t,
            # Backwards compatibility and fast rendering aliases
            "model": model_field or model_name,
            "provider_type": provider_field or provider_type or ("Deterministic Synthesizer" if not is_actual_llm else "Unknown"),
            "iteration": iteration,
            "prompt_tokens": actual_p if is_actual_llm else 0,
            "completion_tokens": actual_c if is_actual_llm else 0,
            "total_tokens": actual_t if is_actual_llm else 0,
            "tokens": {
                "prompt_tokens": actual_p if is_actual_llm else 0,
                "completion_tokens": actual_c if is_actual_llm else 0,
                "total_tokens": actual_t if is_actual_llm else 0,
                "estimated_prompt_tokens": est_p,
                "estimated_completion_tokens": est_c,
                "estimated_total_tokens": est_t,
            },
            "is_valid_ast": is_valid_ast,
            "ast_valid": is_valid_ast,
            "validation_error": validation_error,
            "prompt_length_chars": len(prompt),
            "response_length_chars": len(response_text),
            "prompt_excerpt": prompt[:300] + ("..." if len(prompt) > 300 else ""),
            "response_snippet": response_text[:300] + ("..." if len(response_text) > 300 else "")
        }
        if is_actual_llm:
            self._session_actual_llm_tokens += actual_t
        self._session_total_tokens += (actual_t if is_actual_llm else est_t)
        self.log_event("LLM_INFERENCE_TELEMETRY", payload, correlation_id=correlation_id, workflow_id=workflow_id)

    def get_token_summary(
        self,
        traces: Optional[list[Dict[str, Any]]] = None,
        correlation_id: Optional[str] = None,
        workflow_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Calculates distinct actual LLM tokens and offline estimated tokens.
        Can be scoped to a single run via correlation_id or workflow_id.
        """
        trace_list = traces if traces is not None else self.read_traces()
        if correlation_id:
            trace_list = [
                e for e in trace_list
                if e.get("correlation_id") == correlation_id
                or e.get("metadata", {}).get("correlation_id") == correlation_id
            ]
        elif workflow_id:
            trace_list = [
                e for e in trace_list
                if e.get("workflow_id") == workflow_id
                or e.get("metadata", {}).get("workflow_id") == workflow_id
            ]

        actual_llm_tokens = 0
        actual_prompt_tokens = 0
        actual_completion_tokens = 0

        estimated_tokens = 0
        estimated_prompt_tokens = 0
        estimated_completion_tokens = 0

        actual_calls = 0
        deterministic_calls = 0

        engine_labels: List[str] = []
        last_model: Optional[str] = None
        last_engine: Optional[str] = None

        for entry in trace_list:
            if entry.get("event_type") == "LLM_INFERENCE_TELEMETRY":
                data = entry.get("data", {})
                is_actual = data.get("is_actual_llm")
                model = data.get("model_name") or data.get("model", "")
                provider = data.get("provider") or data.get("provider_type", "")
                engine = data.get("execution_engine")

                # Check explicit or legacy heuristics
                if is_actual is None:
                    if "deterministic" in model.lower() or "ast" in model.lower() or provider == "Unknown":
                        is_actual = False
                    else:
                        is_actual = True

                if not is_actual:
                    engine = "Deterministic AST Synthesizer"
                    model = None
                else:
                    data_engine = data.get("execution_engine")
                    if data_engine and "CodeLlama" in data_engine:
                        engine = "CodeLlama (Ollama / Local)"
                        model = "codellama:7b"
                    elif data_engine and ("qwen" in data_engine.lower() or data_engine == "7b (Ollama / Local)"):
                        engine = "qwen2.5-coder:7b (Ollama / Local)"
                        model = "qwen2.5-coder:7b"
                    else:
                        engine, norm_prov, norm_model = resolve_dynamic_execution_engine(model, provider, is_actual)
                        if norm_model:
                            model = norm_model

                engine_labels.append(engine)
                last_engine = engine
                last_model = model or engine

                tokens_obj = data.get("tokens", {})
                if "actual_total_tokens" in data and "estimated_total_tokens" in data:
                    actual_p = data.get("actual_prompt_tokens", 0)
                    actual_c = data.get("actual_completion_tokens", 0)
                    actual_t = data.get("actual_total_tokens", 0)
                    est_p = data.get("estimated_prompt_tokens", 0)
                    est_c = data.get("estimated_completion_tokens", 0)
                    est_t = data.get("estimated_total_tokens", 0)
                else:
                    # Legacy record
                    raw_p = tokens_obj.get("prompt_tokens", data.get("prompt_tokens", 0)) or 0
                    raw_c = tokens_obj.get("completion_tokens", data.get("completion_tokens", 0)) or 0
                    raw_t = tokens_obj.get("total_tokens", data.get("total_tokens", 0)) or 0
                    if is_actual:
                        actual_p, actual_c, actual_t = raw_p, raw_c, raw_t
                        est_p, est_c, est_t = 0, 0, 0
                    else:
                        actual_p, actual_c, actual_t = 0, 0, 0
                        est_p, est_c, est_t = raw_p, raw_c, raw_t

                if is_actual:
                    actual_llm_tokens += actual_t
                    actual_prompt_tokens += actual_p
                    actual_completion_tokens += actual_c
                    actual_calls += 1
                else:
                    estimated_tokens += est_t
                    estimated_prompt_tokens += est_p
                    estimated_completion_tokens += est_c
                    deterministic_calls += 1

        execution_engine_kpi = determine_scope_execution_engine(engine_labels)

        return {
            "actual_llm_tokens": actual_llm_tokens,
            "actual_prompt_tokens": actual_prompt_tokens,
            "actual_completion_tokens": actual_completion_tokens,
            "estimated_tokens": estimated_tokens,
            "estimated_prompt_tokens": estimated_prompt_tokens,
            "estimated_completion_tokens": estimated_completion_tokens,
            "total_tokens": actual_llm_tokens + estimated_tokens,
            "actual_calls": actual_calls,
            "deterministic_calls": deterministic_calls,
            "execution_engine_kpi": execution_engine_kpi,
            "unique_execution_engines": sorted(list(set(engine_labels))),
            "execution_engine_breakdown": dict(Counter(engine_labels)),
            "last_execution_model": last_model,
            "last_execution_engine": last_engine,
            "is_isolated_run": bool(correlation_id or workflow_id)
        }

    def get_total_tokens(
        self,
        traces: Optional[list[Dict[str, Any]]] = None,
        correlation_id: Optional[str] = None,
        workflow_id: Optional[str] = None,
        actual_only: bool = True
    ) -> int:
        """
        Calculates total tokens consumed. By default (actual_only=True),
        returns strictly genuine LLM provider tokens, excluding offline deterministic estimates.
        """
        if traces is None and not correlation_id and not workflow_id and (self._session_actual_llm_tokens > 0 or self._session_total_tokens > 0):
            return self._session_actual_llm_tokens if actual_only else self._session_total_tokens
        summary = self.get_token_summary(traces=traces, correlation_id=correlation_id, workflow_id=workflow_id)
        return summary["actual_llm_tokens"] if actual_only else summary["total_tokens"]

    _FILE_CACHES: Dict[str, Dict[str, Any]] = {}

    def read_traces(self) -> list[Dict[str, Any]]:
        """
        Reads all events logged in the session with high-performance stat-based file caching.
        Avoids redundant multi-second JSON deserialization of large historical logs.
        """
        file_traces: list[Dict[str, Any]] = []
        if os.path.exists(self.log_path):
            abs_path = os.path.abspath(self.log_path)
            try:
                stat = os.stat(abs_path)
                current_mtime = stat.st_mtime
                current_size = stat.st_size
            except OSError:
                current_mtime = 0.0
                current_size = 0

            cached = TraceLogger._FILE_CACHES.get(abs_path)
            if cached and cached.get("mtime") == current_mtime and cached.get("size") == current_size:
                file_traces = list(cached.get("traces", []))
            else:
                traces = list(cached.get("traces", [])) if (cached and current_size > cached.get("size", 0) and cached.get("size", 0) > 0) else []
                seek_pos = cached.get("size", 0) if traces else 0

                try:
                    with open(abs_path, "r", encoding="utf-8") as f:
                        if seek_pos > 0:
                            f.seek(seek_pos)
                        for line in f:
                            line = line.strip()
                            if line:
                                try:
                                    traces.append(json.loads(line))
                                except json.JSONDecodeError:
                                    pass
                except OSError:
                    pass

                if len(traces) > 10000:
                    traces = traces[-10000:]

                TraceLogger._FILE_CACHES[abs_path] = {
                    "traces": traces,
                    "mtime": current_mtime,
                    "size": current_size
                }
                file_traces = list(traces)

        # Merge in-memory session events for this logger instance so recent events are never missed
        session_events = getattr(self, "_session_events", None)
        if session_events:
            seen_ids = set()
            combined = []
            for t in file_traces:
                k = (t.get("timestamp"), t.get("event_type"), t.get("workflow_id"), t.get("correlation_id"))
                seen_ids.add(k)
                combined.append(t)
            for s in session_events:
                k = (s.get("timestamp"), s.get("event_type"), s.get("workflow_id"), s.get("correlation_id"))
                if k not in seen_ids:
                    combined.append(s)
            return combined

        return file_traces

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
