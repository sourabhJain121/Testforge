# TestForge: Streamlit Dependency & Ingestion Audit

**Audit Date:** 2026-10-30  
**Auditor:** Lead Architect & Antigravity QA Suite  
**Objective:** Comprehensive catalog of all Streamlit references, runtime entry points, and architectural dependencies across the TestForge repository.

---

## 1. Executive Summary

This audit catalogs all occurrences of `streamlit`, `streamlit run`, port `8501`, `app.py`, and `st.` API calls across the TestForge repository.

**Key Finding:**
- **Zero Core Engine Coupling:** The core TestForge multi-agent engine (`testforge/`), the blackboard system (`testforge/blackboard.py`), the mutation engine (`testforge/mutator.py`), the orchestration layer (`testforge/orchestrator.py`), and the FastAPI server (`server.py`) contain **zero** imports of `streamlit` and zero runtime calls to Streamlit APIs.
- Streamlit was introduced strictly as a standalone monolithic UI prototype in `app.py` (commit `6d9366c`, Sep 19, 2026).
- All modern agentic features (FastMCP tools status, official A2A AgentCard discovery & testing, WebSocket streaming, and SQLite partition diffing) were built directly on the FastAPI dashboard (`server.py` + `frontend/app.js`), making Streamlit completely redundant.

---

## 2. Comprehensive Repository Reference Catalog

### 2.1 Application & Frontend Source Code

| File Path | Location / Line | Content / Context | Action Required |
| :--- | :--- | :--- | :--- |
| `frontend/index.html` | Line 70 | `<a href="http://127.0.0.1:8501" ... id="btn-streamlit-link">` | **Remove**: Eliminate cross-link button and all redirects to port 8501. |
| `app.py` | Full file (923 LOC) | Monolithic Streamlit application (`import streamlit as st`) | **Preserve**: Mark file as legacy manual implementation. Exclude from normal runtime. |
| `server.py` | Full file (1660 LOC) | FastAPI application entry point | **Verified Clean**: Contains 0 imports of `streamlit` or `app.py`. |
| `testforge/` | All 35 modules | Multi-agent hardening engine | **Verified Clean**: Contains 0 imports of `streamlit` or references to port 8501. |

### 2.2 Containerization & Orchestration Manifests

| File Path | Location / Line | Content / Context | Action Required |
| :--- | :--- | :--- | :--- |
| `Dockerfile` | Line 39 | `EXPOSE 8000 8501` | **Clean**: Retain default CMD (`uvicorn server:app --port 8000`); document 8501 as legacy. |
| `docker-compose.yml` | Lines 23-38 | `dashboard: command: ["streamlit", "run", "app.py", "--server.port", "8501", ...]` | **Update**: Mark dashboard service with legacy profile or streamline to single backend service. |
| `requirements.txt` | Line 10 | `streamlit>=1.35.0,<2.0.0` | **Preserve**: Keep in requirements so `app.py` remains manually runnable if ever needed. |

### 2.3 Automated Test Suites

| File Path | Location / Line | Content / Context | Action Required |
| :--- | :--- | :--- | :--- |
| `tests/test_deployment.py` | Line 84 | `assert "8501:8501" in parsed["services"]["dashboard"]["ports"]` | **Preserve**: Keep test aligned with `docker-compose.yml` structure. |
| `tests/test_blackboard.py` | Line 138 | `target_file_path="src/app.py"` | **Verified Clean**: String literal test fixture; no Streamlit dependency. |
| Full `tests/` Suite | 42 test files | 523 regression tests | **Verified Clean**: Zero tests launch Streamlit or depend on port 8501. |

### 2.4 Documentation & Setup Guides

| File Path | Section | Context | Action Required |
| :--- | :--- | :--- | :--- |
| `README.md` | Line 258 | `streamlit run app.py` | **Update**: Designate `server.py` (`uvicorn server:app`) as the single official startup command. |
| `docs/EVALUATION_PACKAGE/SETUP_AND_EXECUTION_GUIDE.md` | Line 62 | `streamlit run app.py` | **Update**: Clarify FastAPI on port 8000 as the official UI. |
| `docs/EVALUATION_PACKAGE/DEMONSTRATION_SCRIPT.md` | Line 39 | `streamlit run app.py` | **Update**: Update walkthrough steps to use port 8000. |

---

## 3. Launch Mechanisms Analysis

The following mechanisms were identified as potential sources of Streamlit process creation:
1. **Manual CLI execution:** An operator running `streamlit run app.py` or `.venv-release/bin/python -m streamlit run app.py`.
2. **Background Daemons:** Background tasks or IDE terminal tabs started in earlier testing sessions.
3. **Docker Compose:** Running `docker compose up` without specifying services launches both `backend` and `dashboard`.

**Verification:**
- Neither `server.py` nor any module in `testforge/` contains subprocess calls, `os.system()`, or thread spawners that launch Streamlit automatically.
- Once the running background Streamlit process (PID 20342) is stopped, the application will run exclusively on FastAPI (`http://127.0.0.1:8000/`).

