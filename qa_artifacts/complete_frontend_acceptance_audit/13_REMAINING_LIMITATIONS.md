# TestForge Complete Frontend Acceptance Audit: Remaining Limitations & Operational Boundaries

**Audit Date:** 2026-10-30  
**Auditor:** Antigravity Automated QA Suite  
**Evaluation Scope:** Academic & Project Evaluation Handover

---

## 1. Overview

This document explicitly identifies known operational boundaries, design trade-offs, and environmental constraints of the current TestForge deployment. These are not unhandled defects, but documented characteristics for evaluators and operators.

---

## 2. Documented Operational Boundaries

### 2.1 Dual-Frontend Coexistence
- **Architecture:** The platform runs two concurrent web servers:
  1. Primary Enterprise Cockpit (FastAPI + Modern SPA): Port `8000`
  2. Secondary Data Workbench (Streamlit): Port `8501`
- **State Partitioning:** Both frontends share the underlying SQLite blackboard database (`DEFAULT_CHECKPOINT_DB_PATH`) and telemetry log (`testforge_trace.jsonl`), but maintain independent in-memory UI sessions. Modifications made in Streamlit's sidebar (e.g. reflection slider) do not dynamically mutate the FastAPI server's default configuration until saved via the API or settings modal.
- **Evaluation Recommendation:** Always use **FastAPI on Port 8000** as the primary demonstration interface.

### 2.2 Local Model & Offline LLM Availability
- **Engine Hierarchy:** TestForge uses a strict 4-tier hierarchy:
  1. Tier 1: Google Gemini Cloud (`gemini-3.6-flash`)
  2. Tier 2: OpenRouter Cloud Fallback
  3. Tier 3: Local Ollama (`qwen2.5-coder:7b` on `http://localhost:11434`)
  4. Tier 4: AST-guided deterministic rule synthesizer
- **Requirement for Tier 3:** For local offline LLM generation without cloud API keys, Ollama must be running locally with `qwen2.5-coder:7b` pulled. If Ollama is offline and cloud API keys are unset, TestForge gracefully falls back to Tier 4 (deterministic AST mutation and synthesis), ensuring zero unhandled crashes.

### 2.3 Network Security & SSRF Confinement
- **GitHub Ingestion:** Strict domain validation and redirect verification are enforced. Ingestion is bounded to `github.com` and `raw.githubusercontent.com`.
- **Private Subnets & Cloud Metadata:** All private IP ranges (`10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, `169.254.169.254`, `127.0.0.1`) are blocked at both DNS resolution and HTTP redirect levels.
- **File Size Caps:** Remote downloads are bounded to 5 MB with strict AST syntax validation prior to disk persistence.

### 2.4 Trace Log Pruning
- **Streamlit Performance:** Streamlit reads `testforge_trace.jsonl` on startup. To prevent GIL stalls, active trace size should remain under 50,000 lines. The full historical trace has been safely preserved in `testforge_trace.jsonl.archive_full`.
- **Command Flag:** Always start Streamlit with `--server.fileWatcherType none` to prevent recursive file watcher thrashing over `.venv-release/`.

