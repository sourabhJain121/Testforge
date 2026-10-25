# TestForge — Known Issues & Separately Tracked Items

**Audit Date:** 2026-10-23
**Audit Directory:** `qa_artifacts/m3_final_acceptance_audit_20261023_153600/`

---

## 1. Upstream CrewAI Framework Deprecations (Tracked Separately)

- **Description:** CrewAI version 0.102.0 emits runtime deprecation warnings during agent initialization and execution:
  - `function_calling_llm is deprecated and will be removed in a future release.`
  - `allow_code_execution is deprecated.`
  - `multimodal attribute check is deprecated.`
- **Impact:** Non-fatal upstream warnings during pytest execution (208 total warnings across the test suite). Does not affect test execution, assertion validity, or runtime functionality.
- **Policy:** In accordance with prompt rules, these warnings are tracked separately and **not** globally suppressed.

## 2. Google Cloud Storage SDK Deprecation Warning

- **Description:** `google.cloud.aiplatform.models` emits:
  - `FutureWarning: Support for google-cloud-storage < 3.0.0 will be removed in a future version of google-cloud-aiplatform. Please upgrade to google-cloud-storage >= 3.0.0.`
- **Impact:** Upstream dependency notice. Does not affect test suite or runtime operations.

## 3. Fast Benchmark Mode Disclosures

- **Description:** When running `run_benchmark.py --fast`, metrics are derived from deterministic offline fixtures rather than live foundation model calls.
- **Handling:** All JSON exports, Markdown reports, and console outputs prominently feature a simulated banner warning users that results reflect offline CI fixtures and not live foundation model performance.

## 4. MCP NPM Package Installation Latency in Offline Environments

- **Description:** When running `tests/test_mcp.py` tests involving `use_node=True`, `npx` may attempt to query npm registry.
- **Handling:** Native Python FastMCP servers (`use_node=False`) are used as the primary supported standard in offline workflows.
