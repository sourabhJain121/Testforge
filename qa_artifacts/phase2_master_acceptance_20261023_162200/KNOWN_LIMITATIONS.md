# TestForge — Known Technical & Operational Limitations

**Audit Directory:** `qa_artifacts/phase2_master_acceptance_20261023_162200/`  
**Evaluation Scope:** Phase 2 Master Acceptance  
**Status:** Monitored & Documented (Non-blocking for Phase 2 Evaluation)

---

## 1. Upstream Framework Deprecations (CrewAI & Google GenAI)

- **Nature of Warning:**
  - `PydanticDeprecatedSince20: The 'dict' method is deprecated; use 'model_dump' instead.`
  - `LangChainBetaWarning: Tool calls and agent parsing hooks in langchain-core.`
  - `FutureWarning: Support for google-cloud-storage < 3.0.0 will be removed in google-cloud-aiplatform.`
- **Assessment:**
  - These warnings originate from external library packages installed in the release virtualenv (`.venv-release`).
  - As mandated by Part 1 rules, dependency versions must not be modified arbitrarily solely to eliminate third-party warnings.
  - Zero warnings originate from TestForge's core code (`testforge/`, `server.py`).

---

## 2. Remote GitHub Import Token Rate Limiting

- **Nature of Limitation:**
  - Unauthenticated requests to `https://api.github.com/` are subject to GitHub's IP rate limit of 60 requests per hour.
- **Mitigation & Workaround:**
  - TestForge provides a simulated fast mock mode and local fixture repository caching for offline and CI environments.
  - Optional `GITHUB_TOKEN` environment variable configuration allows expanding the rate limit to 5,000 requests per hour when demonstrating Mode C on live external repositories.

---

## 3. Sandboxed Execution Isolation Model

- **Nature of Limitation:**
  - The parallel test runner uses isolated OS sub-processes (`ProcessPoolExecutor`) with timeouts and memory monitoring rather than hardware virtual machines or root-privileged microVMs.
- **Assessment:**
  - This design ensures rapid execution (sub-millisecond overhead per mutant) suitable for rapid agentic reflection loops on developer workstations.
  - Adversarial payload scanning (via AST static visitor) blocks dangerous system calls (`os.system`, `subprocess`, socket creation) before test execution.

---

## 4. Headless Clipboard API Browser Permissions

- **Nature of Limitation:**
  - In automated headless browsers or environments without direct user gesture focus, the browser `navigator.clipboard.writeText()` API rejects by default for security reasons.
- **Mitigation:**
  - TestForge implements a robust fallback mechanism using a hidden `<textarea>` element with `document.execCommand('copy')` ensuring clipboard copying and visual feedback (`✅ Copied!`) function seamlessly in both automated CDP tests and real user sessions.
