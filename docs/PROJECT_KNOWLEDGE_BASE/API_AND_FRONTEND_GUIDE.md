# TESTFORGE — API & FRONTEND ARCHITECTURE GUIDE
## FastAPI Endpoints, WebSocket Event Telemetry, Single-Page Application Design & State Management

**Document Version:** 2.0.0  
**Target Audience:** Frontend/Backend Developers, API Integrators, Evaluators  
**Authoritative Location:** `docs/PROJECT_KNOWLEDGE_BASE/API_AND_FRONTEND_GUIDE.md`

---

## 1. BACKEND API SPECIFICATION (`server.py`)

The TestForge backend is powered by FastAPI, serving REST endpoints, streaming WebSockets, and static frontend assets from a single port (`8000`).

```
Base URL: http://127.0.0.1:8000
Interactive Swagger Docs: http://127.0.0.1:8000/docs
OpenAPI Schema: http://127.0.0.1:8000/openapi.json
```

---

### 1.1 Ingestion & Target Analysis Endpoints

#### 1. Ingest Sample Module
- **Endpoint:** `POST /api/ingest/sample`
- **Request Body:** `{"sample_name": "banking.py"}`
- **Response (200 OK):**
  ```json
  {
    "status": "success",
    "filename": "banking.py",
    "line_count": 55,
    "source_code": "def banking_transaction...",
    "ast_summary": {
      "classes": ["BankAccount"],
      "functions": ["transfer_funds", "apply_interest"]
    }
  }
  ```

#### 2. Ingest Uploaded File
- **Endpoint:** `POST /api/ingest/upload`
- **Request:** `multipart/form-data` with `file: UploadFile`
- **Validation:** Enforces maximum size (500 KB), rejects non-Python extensions (`.exe` -> 400 Bad Request), and validates Python syntax (`ast.parse`).
- **Response (200 OK):** Ingested metadata, AST node breakdown, and line count.

---

### 1.2 Pipeline Execution & Control Endpoints

#### 1. Start Hardening Pipeline
- **Endpoint:** `POST /api/harden/start`
- **Request Body:**
  ```json
  {
    "target_source_code": "def discount(...): ...",
    "max_iterations": 3,
    "timeout_seconds": 60.0,
    "enable_crewai_critic": true,
    "enable_adk_generator": true
  }
  ```
- **Response (200 OK):**
  ```json
  {
    "status": "started",
    "job_id": "job_20261030_161500_abc123",
    "target_hash": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
  }
  ```

#### 2. Poll Pipeline Status
- **Endpoint:** `GET /api/harden/status/{job_id}`
- **Response (200 OK):**
  ```json
  {
    "job_id": "job_20261030_161500_abc123",
    "status": "COMPLETED",
    "current_stage": "FINAL_EVALUATION",
    "progress_percent": 100,
    "metrics": {
      "baseline_mutation_score": 0.0,
      "hardened_mutation_score": 52.0,
      "mutants_total": 25,
      "mutants_killed": 13,
      "mutants_survived": 12,
      "tests_synthesized": 18,
      "test_pass_rate": 100.0
    },
    "error_message": null
  }
  ```

#### 3. Cancel Active Job
- **Endpoint:** `POST /api/harden/cancel/{job_id}`
- **Behavior:** Signals the cooperative `CancellationToken` associated with `job_id`. Halts the running pipeline at the next safe step boundary.
- **Response (200 OK):**
  ```json
  {
    "status": "cancelling",
    "job_id": "job_20261030_161500_abc123",
    "message": "Cancellation signal dispatched to orchestrator."
  }
  ```

---

### 1.3 Checkpoints & Provenance Endpoints

#### 1. List Checkpoints
- **Endpoint:** `GET /api/checkpoints`
- **Response (200 OK):** Returns list of serialized SQLite checkpoints from `qa_artifacts/testforge_checkpoints.db` with timestamps, target filenames, and mutation scores.

#### 2. Checkpoint Lineage Diff
- **Endpoint:** `GET /api/checkpoints/diff?base_id={id1}&compare_id={id2}`
- **Response (200 OK):** Line-by-line diff of generated tests, mutant status transitions (Survived -> Killed), and score delta.

---

### 1.4 Protocol & System Endpoints

- `GET /healthz`: Health probe returning `{"status": "healthy", "service": "testforge-backend", "version": "2.0.0"}`.
- `GET /.well-known/agent-card.json`: A2A discovery card (Linux Foundation A2A v0.3.0).
- `GET /api/mcp/status`: Returns status of FastMCP servers (`testforge-filesystem-samples`, `testforge-github`).
- `GET /ws/events`: WebSocket endpoint broadcasting real-time JSON lifecycle events.

---

## 2. WEBSOCKET EVENT STREAMING (`/ws/events`)

The frontend establishes a persistent WebSocket connection to receive real-time telemetry:

```json
{
  "event_type": "STAGE_TRANSITION",
  "job_id": "job_20261030_161500_abc123",
  "timestamp": 1793358902.585,
  "stage": "TEST_SYNTHESIS",
  "message": "GoogleADKTestGenerator synthesized 18 granular scenario tests.",
  "data": {
    "agent": "GoogleADKTestGenerator",
    "partition": "SuiteSpace",
    "tests_count": 18
  }
}
```

---

## 3. FRONTEND ARCHITECTURE & STATE MANAGEMENT (`frontend/`)

### 3.1 Technology Stack & Structure
- **Frontend Stack:** HTML5, CSS3, Vanilla JavaScript (ES2022). Zero external bundle dependencies (No React/Vue/Angular node_modules bloat).
- **Files:**
  - `frontend/index.html` (68 KB): Markup structure, navigation bar, and tab panels.
  - `frontend/style.css` (48 KB): High-contrast dark theme, accessible typography, responsive breakpoints.
  - `frontend/app.js` (180 KB): Core client-side application logic.

### 3.2 State Store Topology (`frontend/app.js`)
All client-side state is centrally managed within a global `AppState` object:
```javascript
const AppState = {
  activeTab: 'overview',
  currentJobId: null,
  isJobRunning: false,
  selectedSample: 'logistics_engine.py',
  targetSourceCode: '',
  targetAST: null,
  mutantsList: [],
  generatedTests: '',
  metrics: {
    baselineScore: 0.0,
    hardenedScore: 0.0,
    mutantsKilled: 0,
    totalMutants: 0
  },
  wsConnected: false
};
```

### 3.3 The Six Core UI Views / Tabs
1. **Overview Tab:** System status cards, pipeline architecture diagram, and summary of the last completed hardening run.
2. **Interactive Sandbox Tab:** File upload dropzone, sample target picker, code editor with syntax highlighting, and the **Run Autonomous Hardening** primary action button.
3. **Target Analysis Tab:** Visualizes parsed AST hierarchy: module callables, class declarations, argument signatures, and cyclomatic complexity estimates.
4. **Mutant Inspector Tab:** Interactive table of all first-order mutants with filters for Killed vs. Survived, operator enums, line numbers, and a side-by-side unified AST diff viewer.
5. **Test Studio Tab:** Displays the synthesized unit test suite decomposed into collapsible sections for Normal, Boundary, Negative, and Exception scenarios with a Copy-to-Clipboard action.
6. **Observability & Benchmarks Tab:** Multi-target benchmark score comparison table, execution duration metrics, and SQLite checkpoint inspection history.

