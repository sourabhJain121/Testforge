# 01 — Repository Baseline & Protection Record

**TestForge Master Frontend Playground Audit**  
**Audit Workspace:** `qa_artifacts/complete_frontend_acceptance_audit/`  
**Execution Timestamp:** 2026-10-30T12:25:00+05:30  
**Virtual Environment:** `/Users/sourabh/TestForge/.venv-release/bin/python` (Python 3.13.18)  
**Host Architecture:** Darwin arm64 (10 Cores, 16 GB Unified RAM)  

---

## 1. Git Repository Coordinates

- **Active Branch:** `main`
- **Current HEAD Commit SHA:** `dc040f027d191d25225d4eb09a5885eef6233f79`
- **Remote Tracking:** `origin/main` (Up to date with remote commit)
- **Git Safety Rule:** No git history-altering commands (`add`, `commit`, `push`, `reset`, `clean`, `restore`, `checkout`) will be executed.

---

## 2. Protected Files Hash Baseline

All protected files were cryptographically fingerprinted using SHA-256 prior to starting any audit workflows:

| File Path | SHA-256 Hash | Size (Bytes) | Baseline Status |
| :--- | :--- | :--- | :--- |
| `test_hardened.py` | `cb349b4354961f7a06ba32655f1723d99a3e363660e3d385411d7b699c2d369a` | 271 | Verified Pre-Audit State |
| `benchmark_results.json` | `d336b9b279a21b51ab994abfe24291defe0564d0095add87e7626f83dc516d84` | 1,201 | Exact Match with Freeze Backup |
| `benchmark_results.md` | `ef2ce29811d84bfd58f35e1f158163fdd425bbdd82ecdccefa6c293fa94b9262` | 964 | Exact Match with Freeze Backup |
| `samples/generated_making_a_python_file.py` | `a8c50bc2657065acbb3df43ef92589e89f318f78fb3ce52ded742d82c8274066` | 21,644 | Exact Match with Freeze Backup |
| `server.py` | `275562d3237df903b1635511460b5c6df5c0271ac038656e061869de368a4a46` | 70,691 | Exact Match with Freeze Backup |
| `app.py` | `3ebb91937aa8a071afca488f71507019031824b70740930e467b8af5ab7f011f` | 48,108 | Exact Match with Freeze Backup |

---

## 3. Working Tree Status (`git status --short`)

### Tracked Modified Files:
- `testforge/adk_engine.py` (Phase 2B Indirect Prompt Injection Sanitization)
- `testforge/adk_generator.py` (Phase 2B Delimiter Fencing)
- `testforge/agents.py` (Phase 2B Agent Prompt Sanitization)
- `testforge/blackboard.py` (Phase 2A & 2B Event Telemetry)
- `testforge/crew_critic.py` (Phase 2B Adversarial Prompt Guarding)
- `testforge/github_service.py` (Phase 2A Network SSRF & Bounded Downloads)
- `testforge/ingestion.py` (Phase 2A & 2B Safe File Ingestion)
- `testforge/mcp_server.py` (Phase 2A.1 FastMCP SSRF Hardening)
- `testforge/orchestrator.py` (Phase 2B Safe Agent Invocation)
- `testforge/security.py` (Phase 2A Network SSRF Handlers)
- `benchmark_results.json` & `benchmark_results.md` (Evaluation Baseline)
- `test_hardened.py` (Nominal candidate assertions)

### Untracked Assets:
- `qa_artifacts/` (Historical and evaluation QA artifacts)
- `docs/` (System documentation and evaluation package)
- `testforge/network_security.py` (Phase 2A network security module)
- `testforge/prompt_guard.py` (Phase 2B prompt injection guard module)
- `tests/test_network_security.py`, `tests/test_mcp_network_security.py`, `tests/test_prompt_injection_defense.py`

---

## 4. Backup Coordinates & Verification

A fresh, independent, timestamped backup was created outside the repository before initiating Phase 1:

- **Backup Path:** `/Users/sourabh/TestForge_backups/frontend_audit_20261030_122400/`
- **Verification Method:** Full recursive rsync excluding `.venv*`.
- **Integrity Status:** 100% SHA-256 match confirmed across all critical files.

Historical backups preserved:
1. `/Users/sourabh/TestForge_backups/backup_20261030_093200/` (Phase 1 Baseline)
2. `/Users/sourabh/TestForge_backups/backup_20261030_101600/` (Phase 2A Baseline)
3. `/Users/sourabh/TestForge_backups/backup_20261030_104800/` (Phase 2A.1 Baseline)
4. `/Users/sourabh/TestForge_backups/backup_20261030_evaluation_freeze/` (Phase 2B Freeze Baseline)

---

## 5. Application Entry Points & Startup Commands

- **Backend & Web Dashboard (Cockpit SPA):**
  - Path: `server.py` + `frontend/`
  - URL: `http://127.0.0.1:8000/`
  - Docs: `http://127.0.0.1:8000/docs` & `http://127.0.0.1:8000/redoc`
  - Command: `.venv-release/bin/python -m uvicorn server:app --host 127.0.0.1 --port 8000`
- **Streamlit Autonomous Hardening Workbench:**
  - Path: `app.py`
  - URL: `http://127.0.0.1:8501/`
  - Command: `.venv-release/bin/python -m streamlit run app.py --server.address 127.0.0.1 --server.port 8501 --server.fileWatcherType none --server.headless false`

