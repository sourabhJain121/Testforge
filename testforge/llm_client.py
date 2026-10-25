"""
llm_client.py - Hybrid LLM Client (Cloud API + Local Model) with Strict Fallback Chain.

Author: Sourabh (Module 1 & 3)
Course: CSE3101 - Agentic AI

Architecture (4-Tier Failover Cascade):
  - Tier 1: Google GenAI (gemini-3.6-flash) via official google-genai SDK (GEMINI_API_KEY)
  - Tier 2: OpenRouter Cloud API (https://openrouter.ai/api/v1/chat/completions) via OPENROUTER_API_KEY
  - Tier 3: Local Ollama (http://localhost:11434/api/generate) with model qwen2.5-coder:7b
  - Tier 4: AST-guided deterministic rule synthesizer (guarantees zero unhandled crashes)

Engine Modes:
  - "auto": Gemini -> OpenRouter -> Local Ollama -> AST Rule Synthesizer
  - "cloud": Force Cloud (Gemini) -> AST Rule Synthesizer
  - "openrouter": Force OpenRouter Cloud -> AST Rule Synthesizer
  - "local": Force Local (Ollama - Offline Mode) -> AST Rule Synthesizer
"""

from __future__ import annotations
import os
import time
import json
import urllib.request
import urllib.error
from typing import Dict, Any, Optional, Tuple, List
from testforge.logger import TraceLogger


def is_ollama_running(url: str = "http://localhost:11434/api/tags", timeout: float = 1.0) -> bool:
    """
    Pings the local Ollama daemon tags endpoint to check if it is active.
    """
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status == 200
    except Exception:
        return False


def call_openrouter_api(
    prompt: str,
    system_instruction: str = "",
    api_key: str = "",
    model: str = "meta-llama/llama-3.3-70b-instruct",
    temperature: float = 0.2,
    timeout: float = 30.0
) -> Tuple[str, Dict[str, int], float]:
    """
    Executes a completion request against OpenRouter's OpenAI-compatible endpoint.
    """
    url = "https://openrouter.ai/api/v1/chat/completions"
    resolved_key = (api_key or os.environ.get("OPENROUTER_API_KEY", "")).strip()
    if not resolved_key:
        raise ValueError("OPENROUTER_API_KEY is not set.")
    headers = {
        "Authorization": f"Bearer {resolved_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/sourabhJain121/Testforge",
        "X-Title": "TestForge Autonomous Test Hardener"
    }
    messages: List[Dict[str, str]] = []
    if system_instruction:
        messages.append({"role": "system", "content": system_instruction})
    messages.append({"role": "user", "content": prompt})

    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature
    }
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers
    )
    start_time = time.perf_counter()
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    latency = time.perf_counter() - start_time

    choices = data.get("choices", [])
    if not choices:
        raise RuntimeError("OpenRouter returned no choices in response.")

    raw_text = choices[0].get("message", {}).get("content", "") or ""
    usage = data.get("usage", {})
    tokens = {
        "prompt_tokens": usage.get("prompt_tokens", 0),
        "completion_tokens": usage.get("completion_tokens", 0),
        "total_tokens": usage.get("total_tokens", 0)
    }
    return raw_text, tokens, latency


class HybridLLMClient:
    """
    Unified Hybrid LLM client managing Cloud API (Gemini & OpenRouter) and Local Engine (Ollama).
    Implements a strict 4-tier fallback chain with persistent telemetry.
    """
    def __init__(
        self,
        cloud_model: str = "gemini-3.6-flash",
        openrouter_model: str = "meta-llama/llama-3.3-70b-instruct",
        local_model: str = "qwen2.5-coder:7b",
        local_url: str = "http://localhost:11434/api/generate",
        engine_mode: str = "auto",
        api_key: Optional[str] = None,
        openrouter_api_key: Optional[str] = None,
        logger: Optional[TraceLogger] = None
    ):
        self.cloud_model = "gemini-3.6-flash" if "2.5" in cloud_model or "1.5" in cloud_model else cloud_model
        self.openrouter_model = openrouter_model
        self.local_model = local_model
        self.local_url = local_url
        self.engine_mode = engine_mode.lower()  # "auto", "cloud", "openrouter", "local"
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY", "").strip()
        self.openrouter_api_key = openrouter_api_key or os.environ.get("OPENROUTER_API_KEY", "").strip()
        self.logger = logger
        self.active_provider: str = "None"
        self.gemini_quota_exhausted: bool = False
        self.openrouter_quota_exhausted: bool = False

        # Single unified GenAI client instance
        self.genai_client = None
        if self.api_key and self.engine_mode in ("auto", "cloud"):
            try:
                from google import genai
                self.genai_client = genai.Client(api_key=self.api_key)
            except Exception as exc:
                if self.logger:
                    self.logger.log_event("LLM_INIT_ERROR", {"error": str(exc)})
                self.genai_client = None

    def generate(
        self,
        prompt: str,
        system_instruction: str = "",
        temperature: float = 0.2,
        agent_name: str = "TestGeneratorAgent",
        iteration: int = 1
    ) -> str:
        """
        Executes generation through the strict 4-tier fallback hierarchy:
          Tier 1: Google GenAI (gemini-3.6-flash) via GEMINI_API_KEY
          Tier 2: OpenRouter Cloud API (https://openrouter.ai/api/v1/chat/completions) via OPENROUTER_API_KEY
          Tier 3: Local Ollama (qwen2.5-coder:7b) via http://localhost:11434
          Tier 4: AST-guided deterministic rule synthesizer (guarantees zero unhandled crashes)
        """
        # ======================================================================
        # TIER 1: CLOUD API (Google GenAI - gemini-3.6-flash)
        # ======================================================================
        should_try_cloud = (
            self.engine_mode in ("auto", "cloud")
            and self.genai_client is not None
            and not self.gemini_quota_exhausted
        )

        if should_try_cloud:
            from google.genai import types
            from google.genai import errors

            retry_delays = [2.0, 4.0]
            for attempt in range(1, 3):
                try:
                    config = types.GenerateContentConfig(
                        system_instruction=system_instruction,
                        temperature=temperature,
                        automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True)
                    )
                    start_t = time.perf_counter()
                    response = self.genai_client.models.generate_content(
                        model=self.cloud_model,
                        contents=prompt,
                        config=config
                    )
                    latency = time.perf_counter() - start_t
                    raw_text = response.text or ""

                    tokens = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
                    if hasattr(response, "usage_metadata") and response.usage_metadata:
                        meta = response.usage_metadata
                        tokens["prompt_tokens"] = getattr(meta, "prompt_token_count", 0) or 0
                        tokens["completion_tokens"] = getattr(meta, "candidates_token_count", 0) or 0
                        tokens["total_tokens"] = getattr(meta, "total_token_count", 0) or 0

                    self.active_provider = f"Cloud Gemini ({self.cloud_model})"
                    
                    # Log telemetry to testforge_trace.jsonl
                    if self.logger:
                        self.logger.log_llm_event(
                            agent_name=agent_name,
                            model_name=f"Cloud Gemini:{self.cloud_model}",
                            prompt=prompt,
                            response_text=raw_text,
                            prompt_tokens=tokens["prompt_tokens"],
                            completion_tokens=tokens["completion_tokens"],
                            total_tokens=tokens["total_tokens"],
                            latency_sec=latency,
                            iteration=iteration,
                            provider_type="Cloud Gemini"
                        )

                    return raw_text

                except (errors.APIError, errors.ServerError, errors.ClientError, Exception) as exc:
                    err_msg = str(exc)
                    is_429 = (
                        any(token in err_msg for token in ("429", "RESOURCE_EXHAUSTED", "quota")) or
                        getattr(exc, "code", None) == 429 or
                        getattr(exc, "status_code", None) == 429
                    )
                    is_503 = any(token in err_msg for token in ("503", "UNAVAILABLE", "overloaded"))

                    if is_429:
                        self.gemini_quota_exhausted = True
                        failover_msg = "[!] Gemini quota exhausted. Switching to secondary provider..."
                        print(f"\n{failover_msg}")
                        if self.logger:
                            self.logger.log_event("PROVIDER_FAILOVER", {
                                "message": failover_msg,
                                "from_provider": "Cloud Gemini",
                                "to_provider": "Local Apple Silicon Engine (Ollama)",
                                "reason": "429 RESOURCE_EXHAUSTED",
                                "error": err_msg
                            })
                        break  # Fallthrough to Tier 2 immediately
                    elif is_503 and attempt < 2:
                        delay = retry_delays[attempt - 1]
                        print(f"[*] Transient GenAI 503 error (attempt {attempt}/2). Retrying in {delay:.1f}s...")
                        time.sleep(delay)
                        continue
                    else:
                        print(f"[!] Cloud Gemini failed ({exc}). Proceeding to next tier...")
                        break

        # If Cloud was already marked exhausted in a previous iteration:
        elif self.engine_mode == "auto" and self.gemini_quota_exhausted and self.genai_client:
            failover_msg = "[!] Gemini quota exhausted. Switching to secondary provider..."
            print(f"\n{failover_msg}")
            next_provider = "OpenRouter Cloud" if self.openrouter_api_key else "Local Apple Silicon Engine (Ollama)"
            if self.logger:
                self.logger.log_event("PROVIDER_FAILOVER", {
                    "message": failover_msg,
                    "from_provider": "Cloud Gemini",
                    "to_provider": next_provider,
                    "reason": "429 RESOURCE_EXHAUSTED (cached state)"
                })

        # If force-cloud (Gemini) mode was requested and Cloud failed, engage Tier 4 AST synthesizer
        if self.engine_mode == "cloud":
            raise RuntimeError("HybridLLMClient: Tier 4 Fallback Engaged - Cloud Gemini failed in force-cloud mode.")

        # ======================================================================
        # TIER 2: SECONDARY CLOUD API (OpenRouter - OpenAI compatible endpoint)
        # ======================================================================
        should_try_openrouter = (
            self.engine_mode in ("auto", "openrouter")
            and bool(self.openrouter_api_key)
            and not self.openrouter_quota_exhausted
        )

        if should_try_openrouter:
            candidate_openrouter_models: List[str] = []
            for m in [self.openrouter_model, "meta-llama/llama-3.3-70b-instruct", "qwen/qwen-2.5-coder-32b-instruct", "openrouter/free"]:
                if m and m not in candidate_openrouter_models:
                    candidate_openrouter_models.append(m)

            for model_cand in candidate_openrouter_models:
                try:
                    print(f"[*] Engaging Secondary Provider: OpenRouter Cloud ({model_cand})...")
                    raw_text, tokens, latency = call_openrouter_api(
                        prompt=prompt,
                        system_instruction=system_instruction,
                        api_key=self.openrouter_api_key,
                        model=model_cand,
                        temperature=temperature
                    )
                    if not raw_text.strip():
                        continue

                    self.active_provider = f"OpenRouter Cloud ({model_cand})"
                    print(f"[*] Successfully generated via OpenRouter: {model_cand}")

                    if self.logger:
                        self.logger.log_llm_event(
                            agent_name=agent_name,
                            model_name=f"OpenRouter:{model_cand}",
                            prompt=prompt,
                            response_text=raw_text,
                            prompt_tokens=tokens["prompt_tokens"],
                            completion_tokens=tokens["completion_tokens"],
                            total_tokens=tokens["total_tokens"],
                            latency_sec=latency,
                            iteration=iteration,
                            provider_type="OpenRouter Cloud"
                        )
                    return raw_text

                except urllib.error.HTTPError as http_err:
                    err_msg = str(http_err)
                    is_quota = http_err.code in (402, 429)
                    if is_quota:
                        self.openrouter_quota_exhausted = True
                        failover_msg = f"[!] OpenRouter quota/rate limit reached (HTTP {http_err.code}). Failing over..."
                        print(f"\n{failover_msg}")
                        if self.logger:
                            self.logger.log_event("PROVIDER_FAILOVER", {
                                "message": failover_msg,
                                "from_provider": f"OpenRouter ({model_cand})",
                                "to_provider": "Local Apple Silicon Engine (Ollama)",
                                "reason": f"HTTP {http_err.code}",
                                "error": err_msg
                            })
                        break
                    else:
                        print(f"[!] OpenRouter model {model_cand} error (HTTP {http_err.code}). Trying next candidate...")
                        continue
                except Exception as or_exc:
                    print(f"[!] OpenRouter request failed for {model_cand}: {or_exc}. Trying next candidate...")
                    continue

        if self.engine_mode == "openrouter":
            raise RuntimeError("HybridLLMClient: Tier 4 Fallback Engaged - OpenRouter failed in force-openrouter mode.")

        if self.engine_mode in ("auto", "local"):
            tags_url = self.local_url.replace("/api/generate", "/api/tags") if "/api/generate" in self.local_url else "http://localhost:11434/api/tags"
            if is_ollama_running(tags_url, timeout=0.8):
                candidate_models = [self.local_model, "qwen2.5:7b", "codellama:7b"]
                for model_candidate in candidate_models:
                    try:
                        payload = {
                            "model": model_candidate,
                            "system": system_instruction,
                            "prompt": prompt,
                            "stream": False,
                            "options": {"temperature": temperature}
                        }
                        req = urllib.request.Request(
                            self.local_url,
                            data=json.dumps(payload).encode("utf-8"),
                            headers={"Content-Type": "application/json"}
                        )
                        start_t = time.perf_counter()
                        with urllib.request.urlopen(req, timeout=30) as resp:
                            data = json.loads(resp.read().decode("utf-8"))
                        latency = time.perf_counter() - start_t
                        raw_text = data.get("response", "")

                        if not raw_text.strip():
                            continue

                        prompt_tokens = data.get("prompt_eval_count", 0)
                        eval_tokens = data.get("eval_count", 0)
                        tokens = {
                            "prompt_tokens": prompt_tokens,
                            "completion_tokens": eval_tokens,
                            "total_tokens": prompt_tokens + eval_tokens
                        }

                        self.active_provider = f"Local Ollama ({model_candidate})"
                        print(f"[*] Successfully generated via Local Engine: {model_candidate}")

                        # Log telemetry to testforge_trace.jsonl
                        if self.logger:
                            self.logger.log_llm_event(
                                agent_name=agent_name,
                                model_name=f"Local Ollama:{model_candidate}",
                                prompt=prompt,
                                response_text=raw_text,
                                prompt_tokens=tokens["prompt_tokens"],
                                completion_tokens=tokens["completion_tokens"],
                                total_tokens=tokens["total_tokens"],
                                latency_sec=latency,
                                iteration=iteration,
                                provider_type="Local Ollama"
                            )

                        return raw_text

                    except Exception as ollama_exc:
                        # Model might not be installed or Ollama not running
                        pass

        # ======================================================================
        # TIER 4: QUATERNARY AST DETERMINISTIC RULE SYNTHESIZER
        # ======================================================================
        raise RuntimeError("HybridLLMClient: Tier 4 Fallback Engaged - All configured live LLM providers failed or offline.")

