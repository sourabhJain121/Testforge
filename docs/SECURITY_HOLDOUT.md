# TestForge Security Holdout Evaluation Report (Task F3)

> **Evaluation Mode:** Strictly Frozen Code (Zero Edits to `security.py` or `prompt_guard.py`)  
> **Date:** November 8, 2026  
> **Frozen Hashes:**  
> - `testforge/security.py`: `9fd9a8cf6ba2c6be313fa84551e4eaab2157bd0bc7ab50cdfc832b2d223c0378`  
> - `testforge/prompt_guard.py`: `1b387d96ad46b52d4f5795e67591b09b6a7415cfbc2c7e56694cf438028a1f77`  

---

## 1. Provenance Disambiguation

In accordance with strict evaluation integrity, all security metrics are segregated into **Development Set (Tuned)** and **Holdout Test Set (Un-Tuned)**:

| Evaluation Tier | Dataset | Samples | Result | Status |
| :--- | :--- | :---: | :---: | :---: |
| **Development Set (Tuned)** | Python 3.13 stdlib production files | 100 | **0/100 FP (0.0% FPR)** | **DEVELOPMENT SET, TUNED** |
| **Development Set (Tuned)** | Multi-technique adversarial evasions (Homoglyphs, Base64, etc.) | 30 | **30/30 Blocked (100.0% TPR)** | **DEVELOPMENT SET, TUNED** |
| **Holdout Test Set (Un-Tuned)** | Diverse third-party packages in `site-packages` (49 packages) | 150 | **0/150 FP (0.0% FPR)** | **HOLDOUT TEST SET, UN-TUNED** |
| **Holdout Evasions** | Human-supplied adversarial test cases | - | **NOT RUN** | Absent (`qa_artifacts/security_holdout/evasions_human.json`) |

---

## 2. Holdout Test Set Methodology

- **Sample Selection**: 150 pure-Python files selected across 49 distinct third-party packages in `.venv-release/lib/python3.13/site-packages` (including `pydantic`, `httpx`, `fastapi`, `anyio`, `urllib3`, `rich`, `click`, `yaml`, `jinja2`, `starlette`, `playwright`, `matplotlib`, `google-adk`).
- **Exclusion Filters**: All test files, test fixtures, `__pycache__`, and internal testforge packages were strictly excluded.
- **Diversity Cap**: At most 4 files per package.
- **Empirical Measurement**:
  * Total files evaluated: **150**
  * False positive detections: **0**
  * False Positive Rate: **0.00%**
  * Evidence JSON: [`qa_artifacts/SECURITY_HOLDOUT_EVALUATION.json`](file:///Users/sourabh/TestForge/qa_artifacts/SECURITY_HOLDOUT_EVALUATION.json)
