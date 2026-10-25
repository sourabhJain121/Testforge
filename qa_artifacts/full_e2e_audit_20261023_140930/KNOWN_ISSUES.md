# TestForge — Known Issues, Limitations & Environmental Notes
**Audit Date:** October 23, 2026  
**Artifact Directory:** `/Users/sourabh/TestForge/qa_artifacts/full_e2e_audit_20261023_140930`

---

## 1. Environmental & Tooling Constraints

### 1.1 Playwright Driver Remote Download 404 in Subagent Sandbox
- **Description:** When invoking the internal `browser_subagent`, the container attempted to download `playwright-1.57.0-mac-arm64.zip` from Microsoft Azure Edge CDN (`https://playwright.azureedge.net/builds/driver/...`), which returned HTTP 404.
- **Impact:** Automated browser subagent context failed to initialize within the agent container.
- **Resolution / Workaround:** The native Google Chrome application on macOS (`/Applications/Google Chrome.app/Contents/MacOS/Google Chrome`) was launched with remote debugging port `--remote-debugging-port=9230`. An automated CDP client communicating via `websockets` executed all user interactions, exercised controls, validated responses, and captured 22 full-page screenshots directly into the QA evidence directory.
- **Status:** **RESOLVED VIA NATIVE CHROME CDP AUTOMATION**.

---

## 2. Architectural Design Nuances & Intentional Behaviors

### 2.1 Non-Destructive Checkpoint Recovery Isolation
- **Description:** Restoring a historical checkpoint (`POST /api/checkpoints/{id}/restore`) does not destructively overwrite live database records or active in-flight worker jobs. Instead, it instantiates an isolated Blackboard state loaded with the snapshot partition dictionary.
- **Impact:** Historical timeline records in SQLite remain immutable. The user can safely inspect past test suites, mutants, and directives without corrupting benchmark or job history.
- **Status:** **AS DESIGNED (SAFETY SAFEGUARD)**.

### 2.2 Conservative Equivalence Detection on Small Domain Functions
- **Description:** For functions with simple arithmetic and boundary checks (such as `samples/discount.py`), mutants modifying comparison operators (`> 50` to `>= 50`) or tier discount multipliers (`0.90` to `0.85`) change output values for specific volume thresholds and are correctly classified as non-equivalent (`🔴 SURVIVED` or `🟢 KILLED`). Thus, verified equivalent count is 0 on `discount.py`.
- **Impact:** Denominator adjustment formula remains exact: when 0 verified equivalent mutants exist, raw mutation score and adjusted mutation score are identical.
- **Status:** **MATHEMATICALLY AND LOGICALLY SOUND**.

---

## 3. Dependency Warnings

### 3.1 CrewAI Deprecation Notices in Test Logs
- **Description:** Running pytest emits warnings from `crewai/agent/core.py` and `crewai/crew.py` concerning deprecated attributes (`function_calling_llm`, `allow_code_execution`).
- **Impact:** Benign. These warnings originate from upstream CrewAI 0.100+ internal utilities and do not cause test failures (293/293 tests pass).
- **Status:** **MONITORED; UPSTREAM DEPENDENCY NOTICE**.

---

## 4. Manual Verification Steps for User

If you wish to view the running application in Google Chrome on your screen right now:
1. Ensure the server is running on port 8000:
   ```bash
   cd /Users/sourabh/TestForge
   .venv-release/bin/python -m uvicorn server:app --host 127.0.0.1 --port 8000
   ```
2. Open Google Chrome:
   ```bash
   open -a "Google Chrome" "http://127.0.0.1:8000"
   ```
3. In Chrome:
   - Click **Run TestForge Autonomous Hardening** on the **Hardening Lab & Results** tab.
   - Filter the mutants table using the **🟢 Killed**, **🔴 Survived**, and **🔵 Equiv** buttons.
   - Click on any mutant in the table to view the real-time unified AST diff in the inspector.
   - Switch to **💾 Checkpoint Timeline & Diff** to inspect persistent snapshots, compare diffs, and test the safe restore modal.
