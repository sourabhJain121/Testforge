# TestForge — Known Limitations, Residual Risks & Unverified Scope

**Course:** Autonomous Agentic AI  
**Document ID:** TF-LIMIT-EVAL-001  
**Date:** October 30, 2026  
**Status:** Evaluation Candidate  

---

## 1. Overview & Evaluation Disclosure Policy

In accordance with strict academic integrity and engineering transparency standards, this document registers all known technical limitations, unverified external integrations, deferred features, and residual risks in the current TestForge implementation (frozen at Phase 2B).

**Evaluation Rule:** Presenters should never claim full functionality for capabilities documented below.

---

## 2. Incomplete & Unverified Capabilities

### 2.1 Phase 2C Scope: Arbitrary Public GitHub Repository Ingestion
- **Current State:** TestForge currently ingests individual files from approved GitHub endpoints (`testforge/github_service.py`) and pre-configured repository samples (`samples/`).
- **Limitation:** Full recursive repository discovery across previously unconfigured, multi-file public GitHub projects and cryptographic byte-for-byte SHA256 pipeline provenance from GitHub retrieval to sandbox is scheduled for **Phase 2C** and has **NOT** been implemented.

### 2.2 Live Cloud LLM API Dependency
- **Current State:** Bounded offline deterministic test doubles (`ADKModelBridge._synthesize_deterministic_tests`, `CrewAILLMBridge._synthesize_deterministic_critique`) operate without external tokens.
- **Limitation:** Live calling against Gemini (`gemini-3.6-flash`), OpenRouter, or OpenAI has not been continuously executed during test runs to avoid live API token expenses and network nondeterminism. Live mode is fully implemented in `HybridLLMClient`, but evaluations should clearly distinguish offline deterministic execution from live cloud calling.

### 2.3 Live Third-Party MCP Server Discovery
- **Current State:** In-process FastMCP servers (`testforge-filesystem` and `testforge-github`) are operational and verified.
- **Limitation:** Connecting to remote external MCP servers over stdio or SSE requires external Node.js / npx processes or network endpoints that may not be available in an offline academic grading environment.

### 2.4 Cloud Production Deployment
- **Current State:** Local subprocess sandbox, Dockerfile, and docker-compose configurations are implemented.
- **Limitation:** Deployment to public cloud providers (GCP Cloud Run, AWS ECS) has not been verified in live staging environments.

---

## 3. Residual Security Risks

| Threat Category | Current Defense | Residual Limitation | Recommended Future Work |
| :--- | :--- | :--- | :--- |
| **Sandbox Isolation** | Subprocess sandbox, timeouts (5.0s), and AST import/call blocking. | Execution runs as the current OS user rather than inside a hardware hypervisor (gVisor / Firecracker). | Phase 2C / Phase 5: Integrate OS `rlimits` and ephemeral container sandboxes. |
| **Obfuscated Injections** | Regex and AST token scanning for 11 injection rules. | Sophisticated zero-width Unicode attacks or multi-lingual homoglyphs could evade exact regex matches. | Integrate Unicode NFKC normalization and lightweight ML embedding classifier. |
| **GitHub Rate Limits** | Hostname allowlist, SSRF handler, bounded reading. | Anonymous GitHub API calls are subject to GitHub's 60 req/hour rate limit. | Evaluators must supply a `GITHUB_TOKEN` in `.env` for heavy repository traffic. |

---

## 4. Upstream Library Deprecation Warnings

During pytest test execution, 345 warnings are emitted by third-party packages:
1. **Google Cloud Storage (`google.cloud.aiplatform.models`):**  
   `FutureWarning: Support for google-cloud-storage < 3.0.0 will be removed in a future version...`
2. **CrewAI (`crewai.agent.core`, `crewai.crew`):**  
   `DeprecationWarning: function_calling_llm is deprecated and will be removed in a future release.`  
   `DeprecationWarning: if self.allow_code_execution...`
3. **Starlette TestClient (`starlette.testclient`):**  
   `DeprecationWarning: The anyio.abc.BlockingPortal alias is deprecated...`
4. **Pydantic Settings (`pydantic_settings`):**  
   `IncompleteFieldDefinitionWarning: Field 'lifespan' has an incomplete definition...`

**Impact:** These warnings originate within vendor libraries installed in `.venv-release`, do not cause runtime failures or broken assertions, and are tracked for upstream updates in Phase 5.

