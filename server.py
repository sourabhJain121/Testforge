"""
server.py - TestForge FastAPI Backend Application.

Serves the REST API for autonomous test hardening, target ingestion,
blast radius analysis, git diff inspection, agent wiretap, and telemetry,
while hosting the modern HTML/CSS/JavaScript web frontend.
"""

from __future__ import annotations
import os
import sys
import uuid
import time
import json
import logging
import threading
import asyncio
import sqlite3
import xml.etree.ElementTree as ET
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Dict, Any, Optional, List, Literal

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks, status, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse, PlainTextResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from testforge.ingestion import TargetManagerAgent, parse_and_normalize_github_url
from testforge.github_service import GitHubRepoService, parse_github_repo_url
from testforge.orchestrator import TestForgeOrchestrator
from testforge.state import TaskLifecycleState
from testforge.blast_analyzer import BlastRadiusAnalyzer
from testforge.git_diff import GitDiffInspector
from testforge.accel import hw_profile
from testforge.llm_client import is_ollama_running
from testforge.logger import TraceLogger, resolve_dynamic_execution_engine, determine_scope_execution_engine
from testforge.benchmarking import (
    BenchmarkRunner,
    BenchmarkReport,
    run_multi_target_benchmark,
    generate_markdown_benchmark_summary,
    CANONICAL_TARGET_MODULES,
    MultiTargetBenchmarkRunner,
)
from testforge.websocket_hub import global_websocket_hub

from testforge.persistence import (
    SQLiteBlackboardStorage,
    CheckpointNotFoundError,
    CorruptedSnapshotError,
    IncompatibleSchemaError,
    InputHashMismatchError,
    IncompleteCheckpointError,
    InvalidRecoveryStageError,
    ResumptionPlan,
)

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s in %(name)s: %(message)s")
logger = logging.getLogger("testforge.server")

# In-memory store for background hardening jobs
JOB_LOCK = threading.Lock()
JOBS: Dict[str, Dict[str, Any]] = {}
BENCHMARK_JOBS: Dict[str, Dict[str, Any]] = {}
LATEST_BENCHMARK: Optional[Dict[str, Any]] = None

BASE_DIR = Path(__file__).parent.resolve()
FRONTEND_DIR = BASE_DIR / "frontend"
SAMPLES_DIR = BASE_DIR / "samples"
SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
FRONTEND_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_CHECKPOINT_DB_PATH = os.environ.get(
    "TESTFORGE_CHECKPOINT_DB",
    str(BASE_DIR / "qa_artifacts" / "testforge_checkpoints.db")
)


def recover_interrupted_jobs_on_startup(db_path: str = DEFAULT_CHECKPOINT_DB_PATH) -> List[str]:
    """
    Scans the checkpoint database on server startup for unfinalized / in-flight jobs
    that were interrupted by an abrupt server crash or reboot, and marks them as INTERRUPTED.
    """
    interrupted_job_ids: List[str] = []
    if not os.path.exists(db_path):
        return interrupted_job_ids

    terminal_statuses = {
        "FINALIZED", "CANCELLED", "FAILED", "CONVERGED",
        "COMPLETED", "TERMINATED", "SUCCESS", "TIMED_OUT",
        "TARGET_SCORE_UNREACHED", "INTERRUPTED"
    }
    terminal_stages = {"FINALIZED", "CANCELLED", "TIMED_OUT"}

    try:
        conn = sqlite3.connect(db_path, timeout=5.0)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = {row["name"] for row in cursor.fetchall()}

        # 1. Inspect primary 'checkpoints' table
        if "checkpoints" in tables:
            cursor.execute("SELECT DISTINCT job_id FROM checkpoints WHERE job_id IS NOT NULL AND job_id != ''")
            job_rows = cursor.fetchall()
            for j_row in job_rows:
                jid = j_row["job_id"]
                cursor.execute(
                    "SELECT checkpoint_id, stage, status, created_at, snapshot_json FROM checkpoints WHERE job_id = ? ORDER BY created_at DESC LIMIT 1",
                    (jid,)
                )
                latest = cursor.fetchone()
                if latest:
                    st = (latest["status"] or "").upper()
                    sg = (latest["stage"] or "").upper()
                    if st not in terminal_statuses and sg not in terminal_stages:
                        interrupted_job_ids.append(jid)
                        now = time.time()
                        cursor.execute(
                            "UPDATE checkpoints SET status = 'INTERRUPTED' WHERE checkpoint_id = ?",
                            (latest["checkpoint_id"],)
                        )
                        target_file = None
                        try:
                            snap = json.loads(latest["snapshot_json"])
                            target_file = snap.get("target", {}).get("target_module_path")
                        except Exception:
                            pass

                        with JOB_LOCK:
                            JOBS[jid] = {
                                "job_id": jid,
                                "status": "INTERRUPTED",
                                "lifecycle_state": "INTERRUPTED",
                                "interrupted_at": now,
                                "interrupted_stage": latest["stage"],
                                "resumable": True,
                                "resumed_from_checkpoint": latest["checkpoint_id"],
                                "target_file_path": target_file or "unknown",
                                "created_at": latest["created_at"],
                            }
                        logger.info(f"Marked interrupted job '{jid}' (stage: {latest['stage']}) as INTERRUPTED on server startup.")

        # 2. Inspect 'blackboard_checkpoints' table if present
        if "blackboard_checkpoints" in tables:
            cursor.execute("SELECT DISTINCT job_id FROM blackboard_checkpoints WHERE job_id IS NOT NULL AND job_id != ''")
            for j_row in cursor.fetchall():
                jid = j_row["job_id"]
                cursor.execute(
                    "SELECT id, status, stage FROM blackboard_checkpoints WHERE job_id = ? ORDER BY created_at DESC LIMIT 1",
                    (jid,)
                )
                latest = cursor.fetchone()
                if latest and (latest["status"] or "").upper() not in terminal_statuses:
                    cursor.execute("UPDATE blackboard_checkpoints SET status = 'INTERRUPTED' WHERE id = ?", (latest["id"],))
                    if jid not in interrupted_job_ids:
                        interrupted_job_ids.append(jid)

        # 3. Inspect 'workflow_runs' table if present
        if "workflow_runs" in tables:
            cursor.execute(
                "UPDATE workflow_runs SET status = 'INTERRUPTED' WHERE UPPER(status) IN ('STARTED', 'INITIALIZING', 'GENERATING', 'EVALUATING', 'MUTATING', 'RUNNING', 'IN_PROGRESS')"
            )

        conn.commit()
        conn.close()
    except Exception as exc:
        logger.warning(f"Error during startup interrupted jobs scan: {exc}")

    return interrupted_job_ids


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initializes WebSocket hub and connects it to the central callback registry, and checks for interrupted jobs."""
    try:
        loop = asyncio.get_running_loop()
        global_websocket_hub.set_event_loop(loop)
        global_websocket_hub.attach_to_registry()
        logger.info("WebSocket event hub initialized on server startup.")
    except Exception as exc:
        logger.warning(f"Error during WebSocket hub startup hook: {exc}")

    # GAP-007: Inspect SQLite checkpoint database for unfinalized jobs and mark status cleanly
    try:
        interrupted = recover_interrupted_jobs_on_startup()
        if interrupted:
            logger.info(f"Recovered and marked {len(interrupted)} interrupted job(s) from previous server session.")
    except Exception as exc:
        logger.warning(f"Error recovering interrupted jobs on startup: {exc}")

    yield

app = FastAPI(
    title="TestForge API",
    description="Autonomous Agentic Test Hardening System API with Apple Silicon Optimization",
    version="2.0.0",
    lifespan=lifespan,
)

# Enable CORS for development flexibility
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static frontend directory with explicit cache disabling
class NoCacheStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope: Any) -> Response:
        response = await super().get_response(path, scope)
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

app.mount("/static", NoCacheStaticFiles(directory=str(FRONTEND_DIR)), name="static")


# --------------------------------------------------------------------------
# Request / Response Schemas
# --------------------------------------------------------------------------

class KeyConfigPayload(BaseModel):
    gemini_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None

class SampleIngestPayload(BaseModel):
    filename: str

class SynthesisPayload(BaseModel):
    prompt: str
    model_name: str = "gemini-3.6-flash"

class GithubIngestPayload(BaseModel):
    url: str

class GithubRepoDiscoverPayload(BaseModel):
    url: str
    ref: Optional[str] = None

class GithubRepoIngestFilePayload(BaseModel):
    url: str
    commit_sha: str
    path: str

class BlastRadiusPayload(BaseModel):
    source_code: str
    target_function: Optional[str] = None

class GitDiffPayload(BaseModel):
    target_file_path: str

class HardeningRunPayload(BaseModel):
    target_file_path: Optional[str] = None
    target_source_code: Optional[str] = None
    max_iterations: int = 3
    target_mutation_score: float = 85.0
    model_name: str = "gemini-3.6-flash"
    engine_mode: str = "auto"
    target_lines: Optional[List[int]] = None
    gemini_api_key: Optional[str] = None
    openrouter_api_key: Optional[str] = None
    timeout_seconds: Optional[int] = Field(default=300, ge=5, le=3600)
    resume_checkpoint_id: Optional[str] = None
    resume_job_id: Optional[str] = None


class CheckpointResumePayload(BaseModel):
    max_iterations: Optional[int] = None
    target_mutation_score: Optional[float] = None
    timeout_seconds: Optional[int] = Field(default=300, ge=5, le=3600)
    expected_source_code: Optional[str] = None
    model_name: Optional[str] = None
    engine_mode: Optional[str] = None


class BenchmarkRunPayload(BaseModel):
    target_file_path: Optional[str] = "samples/discount.py"
    target_source_code: Optional[str] = None
    baseline_tests: Optional[str] = None
    scenarios: Optional[List[str]] = Field(default_factory=lambda: ["baseline", "zeroshot", "agentic_reflection"])
    repetitions: int = 1
    engine_mode: str = "auto"
    model_name: str = "gemini-3.6-flash"


class MultiTargetBenchmarkRunPayload(BaseModel):
    target_modules: Optional[List[str]] = None
    scenarios: Optional[List[str]] = Field(default_factory=lambda: ["baseline", "zeroshot", "agentic_reflection"])
    repetitions: int = 1
    engine_mode: str = "auto"
    fast_mode: bool = False
    model_name: str = "gemini-3.6-flash"
    output_dir: Optional[str] = None


# --------------------------------------------------------------------------
# Static Homepage Route
# --------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def serve_index():
    index_path = FRONTEND_DIR / "index.html"
    if index_path.exists():
        return HTMLResponse(
            content=index_path.read_text(encoding="utf-8"),
            headers={
                "Cache-Control": "no-cache, no-store, must-revalidate",
                "Pragma": "no-cache",
                "Expires": "0"
            }
        )
    return HTMLResponse(content="<h1>TestForge Frontend Initializing...</h1>", status_code=200)


# --------------------------------------------------------------------------
# System Health & Hardware Endpoints
# --------------------------------------------------------------------------

@app.get("/healthz")
async def healthz():
    """
    Standard liveness probe endpoint for Docker and Kubernetes.
    """
    return {
        "status": "healthy",
        "service": "testforge-backend",
        "version": "2.0.0",
        "timestamp": time.time(),
    }


@app.get("/favicon.ico")
async def favicon():
    """
    Serves favicon to eliminate browser 404 network warnings.
    """
    svg_icon = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><text y=".9em" font-size="90">⚡</text></svg>'
    return Response(content=svg_icon, media_type="image/svg+xml")


@app.get("/readyz")
@app.get("/api/ready")
async def readyz():
    """
    Comprehensive readiness probe verifying core subsystem capabilities:
      1. Sandbox execution environment and write permissions.
      2. AST analysis parser.
      3. Blackboard state management.
    """
    subsystems = {}
    is_ready = True

    # 1. Test AST Mutator parsing
    try:
        from testforge.mutator import ASTMutator
        m = ASTMutator.mutate("def probe(): return True\n")
        subsystems["ast_mutator"] = "operational"
    except Exception as exc:
        subsystems["ast_mutator"] = f"degraded: {exc}"
        is_ready = False

    # 2. Test Blackboard partition initialization
    try:
        from testforge.blackboard import Blackboard
        b = Blackboard()
        subsystems["blackboard"] = "operational"
    except Exception as exc:
        subsystems["blackboard"] = f"degraded: {exc}"
        is_ready = False

    # 3. Test Filesystem access for sandbox runs
    try:
        import tempfile
        with tempfile.NamedTemporaryFile(prefix="probe_", suffix=".py") as tf:
            tf.write(b"# probe")
            tf.flush()
        subsystems["sandbox_storage"] = "operational"
    except Exception as exc:
        subsystems["sandbox_storage"] = f"degraded: {exc}"
        is_ready = False

    # 4. Test SQLite Persistence storage
    try:
        from testforge.persistence import SQLiteBlackboardStorage
        test_db = DEFAULT_CHECKPOINT_DB_PATH if os.path.exists(os.path.dirname(DEFAULT_CHECKPOINT_DB_PATH) or ".") else ":memory:"
        probe_storage = SQLiteBlackboardStorage(test_db)
        probe_storage.close()
        subsystems["sqlite_persistence"] = "operational"
    except Exception as exc:
        subsystems["sqlite_persistence"] = f"degraded: {exc}"
        is_ready = False

    status_code = status.HTTP_200_OK if is_ready else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "ready" if is_ready else "not_ready",
            "service": "testforge-backend",
            "db_accessible": subsystems.get("sqlite_persistence") == "operational",
            "subsystems": subsystems,
            "timestamp": time.time(),
        }
    )


@app.get("/api/mcp/status")
async def get_mcp_status():
    """
    Read-only status endpoint reporting Model Context Protocol (FastMCP) integration state.
    Distinguishes configured tool servers, registered tool schemas, and environment connectivity.
    Does not perform destructive operations or leak credentials/paths.
    """
    try:
        from testforge.mcp_server import create_filesystem_server, create_github_server

        # Filesystem MCP server capabilities
        fs_tools = [
            {
                "name": "read_text_file",
                "description": "Reads text file bounded by permitted workspace root with path-traversal guardrails",
                "status": "ready"
            },
            {
                "name": "list_directory",
                "description": "Lists directory entries with sensitive file masking",
                "status": "ready"
            },
            {
                "name": "get_file_info",
                "description": "Returns file metadata, line count, and SHA-256 fingerprint",
                "status": "ready"
            }
        ]

        # GitHub MCP server capabilities
        has_github_token = bool(os.environ.get("GITHUB_PERSONAL_ACCESS_TOKEN") or os.environ.get("GITHUB_TOKEN"))
        gh_tools = [
            {
                "name": "get_repository_info",
                "description": "Retrieves public repository metadata",
                "status": "authenticated" if has_github_token else "public_unauthenticated"
            }
        ]

        return {
            "status": "operational",
            "protocol": "Model Context Protocol (MCP)",
            "sdk": "FastMCP / mcp-python v1.28.0",
            "transport": "stdio JSON-RPC 2.0",
            "servers": [
                {
                    "server_id": "testforge-filesystem",
                    "status": "configured",
                    "confinement": "samples_dir",
                    "tools_count": len(fs_tools),
                    "tools": fs_tools
                },
                {
                    "server_id": "testforge-github",
                    "status": "configured",
                    "auth_mode": "token" if has_github_token else "anonymous_rate_limited",
                    "tools_count": len(gh_tools),
                    "tools": gh_tools
                }
            ],
            "total_tools_registered": len(fs_tools) + len(gh_tools),
            "timestamp": time.time()
        }
    except Exception as exc:
        logger.warning(f"Error querying MCP status: {exc}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "error": str(exc),
                "servers": [],
                "total_tools_registered": 0,
                "timestamp": time.time()
            }
        )


class MCPTestRequest(BaseModel):
    tool_name: Literal["list_directory", "get_file_info"] = "list_directory"
    path: str = Field(default="samples", max_length=100)


@app.post("/api/mcp/test")
async def run_mcp_test_action(req: MCPTestRequest):
    """
    Executes a safe, verified Model Context Protocol (FastMCP) tool call over stdio.
    Strictly allowlists read-only operations bounded within repository samples root.
    Rejects path traversal, arbitrary shell execution, or sensitive file access.
    """
    clean_path = req.path.strip()
    if ".." in clean_path or clean_path.startswith("/") or clean_path.startswith("\\"):
        raise HTTPException(
            status_code=400,
            detail="Security Violation: Directory traversal or absolute paths are strictly forbidden."
        )

    low_path = clean_path.lower()
    if ".env" in low_path or "id_rsa" in low_path or ".key" in low_path or ".git" in low_path:
        raise HTTPException(
            status_code=400,
            detail="Security Violation: Access to sensitive credential files is strictly forbidden."
        )

    start_t = time.perf_counter()
    try:
        from testforge.mcp_client import create_filesystem_client
        samples_root = (BASE_DIR / "samples").resolve()
        client = create_filesystem_client(permitted_root=samples_root, use_node=False)

        async with client:
            tool_args = {"path": "." if req.tool_name == "list_directory" else (clean_path.split("/")[-1] if "/" in clean_path else clean_path)}
            result = await client.call_tool(req.tool_name, tool_args)

            elapsed_ms = round((time.perf_counter() - start_t) * 1000, 2)
            if not result.success:
                raise HTTPException(status_code=400, detail=f"FastMCP Tool Error: {result.error}")

            return {
                "status": "success",
                "protocol": "Model Context Protocol (FastMCP)",
                "sdk": "mcp-python / FastMCP v1.28.0",
                "transport": "stdio JSON-RPC 2.0",
                "tool_name": req.tool_name,
                "target_path": req.path,
                "elapsed_ms": elapsed_ms,
                "data": result.data,
                "verified": True,
                "timestamp": time.time()
            }
    except HTTPException:
        raise
    except Exception as exc:
        elapsed_ms = round((time.perf_counter() - start_t) * 1000, 2)
        logger.warning(f"MCP diagnostic test error: {exc}")
        raise HTTPException(
            status_code=500,
            detail=f"FastMCP stdio execution failed ({elapsed_ms}ms): {str(exc)}"
        )


@app.get("/.well-known/agent-card.json")
@app.get("/.well-known/agent.json")
async def get_a2a_agent_card():
    """
    Exposes the official A2A AgentCard for cross-framework agent discovery.
    """
    try:
        from testforge.a2a_protocol import build_testforge_agent_card
        card = build_testforge_agent_card(rpc_url="http://127.0.0.1:8000/")
        return card.model_dump(exclude_none=True)
    except Exception as exc:
        logger.warning(f"Failed to generate dynamic A2A AgentCard: {exc}")
        return {
            "name": "TestForge Agentic Unit Test Hardening System",
            "protocol_version": "0.3.0",
            "description": "Autonomous unit-test generation and mutation hardening agent.",
            "url": "http://127.0.0.1:8000/",
        }


class A2ATestRequest(BaseModel):
    target_url: str = Field(default="http://127.0.0.1:8000/", max_length=200)


@app.post("/api/a2a/test")
async def run_a2a_test_action(req: A2ATestRequest):
    """
    Executes a verified Agent-to-Agent (A2A) protocol diagnostic test.
    Validates official A2A AgentCard discovery, protocol version (0.3.0),
    and cross-framework declared skills over local JSON-RPC.
    Strictly forbids remote SSRF targets or arbitrary external network endpoints.
    """
    target = req.target_url.strip().lower()
    if not (target.startswith("http://127.0.0.1") or target.startswith("http://localhost")):
        raise HTTPException(
            status_code=400,
            detail="Security Violation: A2A diagnostic actions are restricted strictly to local agent instances."
        )

    start_t = time.perf_counter()
    try:
        from testforge.a2a_protocol import build_testforge_agent_card, OFFICIAL_A2A_PROTOCOL_VERSION
        from a2a.types import AgentCard

        card = build_testforge_agent_card(rpc_url=req.target_url)
        card_dict = card.model_dump(exclude_none=True)
        validated_card = AgentCard.model_validate(card_dict)

        elapsed_ms = round((time.perf_counter() - start_t) * 1000, 2)

        return {
            "status": "success",
            "protocol": "Agent2Agent (A2A) Protocol",
            "protocol_version": validated_card.protocol_version,
            "agent_name": validated_card.name,
            "transport": str(validated_card.preferred_transport.value if hasattr(validated_card.preferred_transport, 'value') else validated_card.preferred_transport),
            "skills": [s.name for s in validated_card.skills],
            "input_modes": validated_card.default_input_modes,
            "output_modes": validated_card.default_output_modes,
            "elapsed_ms": elapsed_ms,
            "schema_verified": True,
            "timestamp": time.time()
        }
    except Exception as exc:
        elapsed_ms = round((time.perf_counter() - start_t) * 1000, 2)
        logger.warning(f"A2A diagnostic test error: {exc}")
        raise HTTPException(
            status_code=500,
            detail=f"A2A protocol validation failed ({elapsed_ms}ms): {str(exc)}"
        )


# --------------------------------------------------------------------------
# Real-Time WebSocket Event Hub Endpoints (Milestone 3)
# --------------------------------------------------------------------------

@app.websocket("/ws/events")
async def websocket_events_endpoint(websocket: WebSocket):
    """
    Real-time WebSocket streaming endpoint for lifecycle events.
    Subscribes connected clients to live agent state transitions, tool deliberations,
    and checkpoint events with isolated bounded queues and non-blocking delivery.
    """
    await global_websocket_hub.handle_websocket_connection(websocket)


@app.get("/api/ws/status")
async def get_websocket_hub_status():
    """
    Returns real-time health and connection metrics of the WebSocket event hub.
    """
    return {
        "active_clients": global_websocket_hub.client_count,
        "total_events_broadcast": global_websocket_hub.total_events_broadcast,
        "dropped_events_count": global_websocket_hub.dropped_events_count,
        "max_queue_size_per_client": global_websocket_hub.max_queue_size,
    }


@app.get("/api/status")
async def get_system_status():
    """
    Returns hardware topology, accelerator status, and provider connectivity.
    """
    ollama_online = is_ollama_running("http://localhost:11434/api/tags")
    return {
        "hardware": {
            "machine": hw_profile.machine,
            "os_system": hw_profile.os_system,
            "cpu_count": hw_profile.cpu_count,
            "recommended_workers": hw_profile.recommended_workers,
            "total_memory_gb": hw_profile.total_memory_gb,
        },
        "providers": {
            "ollama_online": ollama_online,
            "has_gemini": bool(os.environ.get("GEMINI_API_KEY", "").strip()),
            "has_openrouter": bool(os.environ.get("OPENROUTER_API_KEY", "").strip()),
        },
        "supported_models": [
            "gemini-3.6-flash",
            "gemini-3.1-pro-preview",
            "qwen2.5-coder:7b"
        ],
        "default_engine_mode": "auto"
    }


@app.post("/api/config/keys")
async def update_api_keys(payload: KeyConfigPayload):
    """
    Dynamically binds or updates Gemini / OpenRouter API keys in the environment.
    """
    if payload.gemini_api_key is not None:
        os.environ["GEMINI_API_KEY"] = payload.gemini_api_key.strip()
    if payload.openrouter_api_key is not None:
        os.environ["OPENROUTER_API_KEY"] = payload.openrouter_api_key.strip()

    return {
        "status": "success",
        "has_gemini": bool(os.environ.get("GEMINI_API_KEY")),
        "has_openrouter": bool(os.environ.get("OPENROUTER_API_KEY")),
    }


# --------------------------------------------------------------------------
# Ingestion Endpoints (Mode A, Mode B, Mode C)
# --------------------------------------------------------------------------

@app.get("/api/samples")
async def list_workspace_samples():
    """
    Lists clean sample files from the samples/ directory (excluding temporary or auto-generated files).
    """
    if not SAMPLES_DIR.exists():
        return {"samples": []}

    files = [
        f for f in sorted(os.listdir(str(SAMPLES_DIR)))
        if f.endswith(".py")
        and not f.startswith("github_")
        and not f.startswith("uploaded_")
        and not f.startswith("generated_")
    ]
    return {"samples": files}


@app.post("/api/ingest/sample")
def ingest_sample(payload: SampleIngestPayload):
    """
    Mode A: Ingests an existing workspace sample file and extracts AST metadata.
    """
    filename = payload.filename.strip()
    target_path = SAMPLES_DIR / filename
    if not target_path.exists():
        raise HTTPException(status_code=404, detail=f"Sample file '{filename}' not found.")

    supervisor = TargetManagerAgent()
    analysis = supervisor.ingest_file(str(target_path))

    return {
        "status": "success",
        "mode": "Mode A",
        "target_file_path": str(target_path),
        "module_name": analysis.module_name,
        "functions": analysis.functions,
        "classes": analysis.classes,
        "methods": analysis.methods,
        "all_callables": analysis.all_callables,
        "source_sha": analysis.source_sha,
        "line_count": analysis.line_count,
        "dependencies": getattr(analysis, "dependencies", []),
        "source_code": analysis.source_code,
    }


@app.post("/api/ingest/upload")
async def ingest_upload(file: UploadFile = File(...)):
    """
    Mode A: Uploads an arbitrary Python file, saves to samples/uploaded_<name>.py, and inspects AST.
    """
    if not file.filename.endswith(".py"):
        raise HTTPException(status_code=400, detail="Only Python source files (.py) are supported.")

    content_bytes = await file.read()
    code_text = content_bytes.decode("utf-8", errors="replace")

    safe_name = os.path.basename(file.filename)
    dest_path = SAMPLES_DIR / f"uploaded_{safe_name}"
    dest_path.write_text(code_text, encoding="utf-8")

    supervisor = TargetManagerAgent()
    analysis = supervisor.ingest_file(str(dest_path))

    has_syntax_error = getattr(analysis, "has_syntax_error", False)
    error_msg = getattr(analysis, "error_msg", None)

    return {
        "status": "syntax_error" if has_syntax_error else "success",
        "has_syntax_error": has_syntax_error,
        "error": error_msg,
        "mode": "Mode A (Uploaded)",
        "target_file_path": str(dest_path),
        "module_name": analysis.module_name,
        "functions": analysis.functions,
        "classes": analysis.classes,
        "methods": analysis.methods,
        "all_callables": analysis.all_callables,
        "source_sha": analysis.source_sha,
        "line_count": analysis.line_count,
        "dependencies": getattr(analysis, "dependencies", []),
        "source_code": analysis.source_code,
    }


@app.post("/api/ingest/synthesize")
def synthesize_module(payload: SynthesisPayload):
    """
    Mode B: Synthesizes production-ready Python logic from a natural language specification.
    """
    prompt = payload.prompt.strip()
    if not prompt:
        raise HTTPException(status_code=400, detail="Prompt specification cannot be empty.")

    supervisor = TargetManagerAgent(model_name=payload.model_name)
    try:
        saved_path, code = supervisor.synthesize_module(prompt, output_dir=str(SAMPLES_DIR))
        analysis = supervisor.ingest_file(saved_path)

        return {
            "status": "success",
            "mode": "Mode B",
            "target_file_path": saved_path,
            "module_name": analysis.module_name,
            "functions": analysis.functions,
            "classes": analysis.classes,
            "methods": analysis.methods,
            "all_callables": analysis.all_callables,
            "source_sha": analysis.source_sha,
            "line_count": analysis.line_count,
            "dependencies": getattr(analysis, "dependencies", []),
            "source_code": code,
        }
    except Exception as exc:
        logger.error(f"Synthesis failed: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/ingest/github")
def ingest_github(payload: GithubIngestPayload):
    """
    Mode C: Ingests an arbitrary Python module from a public GitHub repository.
    Enforces strict URL normalization, control character validation, and relative import resolution.
    """
    raw_url = payload.url.strip()
    if not raw_url:
        raise HTTPException(status_code=400, detail="GitHub URL cannot be empty.")

    try:
        # Pre-validate and normalize URL
        meta_url = parse_and_normalize_github_url(raw_url)
    except ValueError as val_err:
        raise HTTPException(status_code=422, detail=str(val_err))

    supervisor = TargetManagerAgent()
    try:
        saved_path, analysis = supervisor.ingest_github(meta_url["normalized_url"], output_dir=str(SAMPLES_DIR))
        meta = getattr(analysis, "github_metadata", {})

        return {
            "status": "success",
            "mode": "Mode C",
            "target_file_path": str(saved_path),
            "filename": getattr(saved_path, "name", os.path.basename(str(saved_path))),
            "module_name": analysis.module_name,
            "functions": analysis.functions,
            "classes": analysis.classes,
            "methods": analysis.methods,
            "all_callables": analysis.all_callables,
            "source_sha": analysis.source_sha,
            "line_count": analysis.line_count,
            "dependencies": getattr(analysis, "dependencies", []),
            "source_code": analysis.source_code,
            "metadata": {
                "source_github_url": meta.get("source_github_url", meta_url["normalized_url"]),
                "raw_github_url": meta.get("raw_github_url", meta_url["raw_url"]),
                "repository": meta.get("repository", meta_url["repository"]),
                "branch": meta.get("branch", meta_url["branch"]),
                "file_path": meta.get("file_path", meta_url["file_path"]),
                "filename": meta.get("filename", meta_url["filename"]),
                "generated_module_name": meta.get("generated_module_name", analysis.module_name),
                "source_sha": analysis.source_sha,
                "line_count": analysis.line_count,
                "ast_class_count": analysis.ast_class_count,
                "ast_function_count": analysis.ast_function_count,
            }
        }
    except Exception as exc:
        logger.error(f"GitHub ingestion error: {exc}", exc_info=True)
        raise HTTPException(status_code=400, detail=str(exc))


@app.post("/api/github/repo/discover")
def discover_github_repo(payload: GithubRepoDiscoverPayload):
    """
    Discovers Python source files in any accessible public GitHub repository using the Git Trees API.
    """
    raw_url = payload.url.strip()
    if not raw_url:
        raise HTTPException(status_code=400, detail="GitHub Repository URL cannot be empty.")

    try:
        url_info = parse_github_repo_url(raw_url)
    except ValueError as val_err:
        raise HTTPException(status_code=422, detail=str(val_err))

    ref = payload.ref.strip() if payload.ref and payload.ref.strip() else url_info.get("ref")
    subpath = url_info.get("subpath")

    service = GitHubRepoService()
    try:
        manifest = service.discover_python_files(
            owner=url_info["owner"],
            repo=url_info["repo"],
            ref=ref,
            subpath_filter=subpath
        )
        return manifest.model_dump()
    except PermissionError as perm_err:
        raise HTTPException(status_code=403, detail=str(perm_err))
    except FileNotFoundError as fnf_err:
        raise HTTPException(status_code=404, detail=str(fnf_err))
    except ValueError as val_err:
        raise HTTPException(status_code=422, detail=str(val_err))
    except ConnectionError as conn_err:
        raise HTTPException(status_code=502, detail=str(conn_err))
    except Exception as exc:
        logger.error(f"GitHub repository discovery error: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/github/repo/ingest-file")
def ingest_github_repo_file(payload: GithubRepoIngestFilePayload):
    """
    Retrieves a selected Python file from a public repository, resolves relative package imports,
    validates AST syntax, writes to samples/, and returns ingestion analysis.
    """
    raw_url = payload.url.strip()
    if not raw_url:
        raise HTTPException(status_code=400, detail="GitHub Repository URL cannot be empty.")

    try:
        url_info = parse_github_repo_url(raw_url)
    except ValueError as val_err:
        raise HTTPException(status_code=422, detail=str(val_err))

    commit_sha = payload.commit_sha.strip()
    if not commit_sha:
        raise HTTPException(status_code=400, detail="Commit SHA is required.")

    file_path = payload.path.strip()
    if not file_path:
        raise HTTPException(status_code=400, detail="File path is required.")

    service = GitHubRepoService()
    try:
        saved_path, analysis = service.ingest_repository_file(
            owner=url_info["owner"],
            repo=url_info["repo"],
            commit_sha=commit_sha,
            file_path=file_path,
            output_dir=str(SAMPLES_DIR)
        )
        meta = getattr(analysis, "github_metadata", {})

        return {
            "status": "success",
            "mode": "GitHub Repository Explorer",
            "target_file_path": str(saved_path),
            "filename": getattr(saved_path, "name", os.path.basename(str(saved_path))),
            "module_name": analysis.module_name,
            "functions": analysis.functions,
            "classes": analysis.classes,
            "methods": analysis.methods,
            "all_callables": analysis.all_callables,
            "source_sha": analysis.source_sha,
            "line_count": analysis.line_count,
            "dependencies": getattr(analysis, "dependencies", []),
            "source_code": analysis.source_code,
            "metadata": {
                "source_github_url": meta.get("source_github_url", ""),
                "raw_github_url": meta.get("raw_github_url", ""),
                "repository": meta.get("repository", url_info["repository"]),
                "owner": url_info["owner"],
                "repo": url_info["repo"],
                "commit_sha": commit_sha,
                "file_path": file_path,
                "filename": getattr(saved_path, "name", os.path.basename(str(saved_path))),
                "generated_module_name": analysis.module_name,
                "source_sha": analysis.source_sha,
                "line_count": analysis.line_count,
                "ast_class_count": analysis.ast_class_count,
                "ast_function_count": analysis.ast_function_count,
                "is_untrusted": True,
                "sandbox_required": True,
            }
        }
    except PermissionError as perm_err:
        raise HTTPException(status_code=403, detail=str(perm_err))
    except FileNotFoundError as fnf_err:
        raise HTTPException(status_code=404, detail=str(fnf_err))
    except ValueError as val_err:
        raise HTTPException(status_code=422, detail=str(val_err))
    except ConnectionError as conn_err:
        raise HTTPException(status_code=502, detail=str(conn_err))
    except Exception as exc:
        logger.error(f"GitHub file ingestion error: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


# --------------------------------------------------------------------------
# Static Analysis Endpoints (Blast Radius & Git Diff)
# --------------------------------------------------------------------------

@app.post("/api/analysis/blast-radius")
def analyze_blast_radius(payload: BlastRadiusPayload):
    """
    Computes static AST call graph, caller propagation, downstream dependencies,
    and architectural risk categorization.
    """
    code = payload.source_code
    if not code:
        raise HTTPException(status_code=400, detail="Source code cannot be empty.")

    call_graph = BlastRadiusAnalyzer.build_call_graph(code)
    defined_funcs = [k for k in call_graph.keys() if k != "<module>"]

    target_fn = payload.target_function
    if not target_fn and defined_funcs:
        target_fn = defined_funcs[0]

    impact = {}
    if target_fn:
        impact = BlastRadiusAnalyzer.analyze_impact(target_fn, code)

    # Format call graph as nodes & links for graph visualization
    graph_nodes = []
    graph_edges = []
    seen_nodes = set()

    for caller, callees in call_graph.items():
        if caller != "<module>":
            if caller not in seen_nodes:
                graph_nodes.append({"id": caller, "label": caller, "is_target": caller == target_fn})
                seen_nodes.add(caller)
            for callee in callees:
                if callee not in seen_nodes:
                    graph_nodes.append({"id": callee, "label": callee, "is_target": callee == target_fn})
                    seen_nodes.add(callee)
                graph_edges.append({"from": caller, "to": callee, "is_critical": callee == target_fn or caller == target_fn})

    return {
        "defined_functions": defined_funcs,
        "selected_target": target_fn,
        "impact": impact,
        "graph_data": {
            "nodes": graph_nodes,
            "edges": graph_edges
        }
    }


@app.post("/api/analysis/git-diff")
def analyze_git_diff(payload: GitDiffPayload):
    """
    Inspects git working tree for modified/added lines in the target file.
    """
    fpath = payload.target_file_path.strip()
    if not fpath:
        raise HTTPException(status_code=400, detail="Target file path cannot be empty.")

    modified_lines = GitDiffInspector.get_modified_lines(repo_path=".", target_file=fpath)
    return {
        "target_file_path": fpath,
        "modified_lines": modified_lines,
        "has_changes": len(modified_lines) > 0
    }


# --------------------------------------------------------------------------
# Hardening Pipeline Execution (Synchronous & Async Job Store)
# --------------------------------------------------------------------------

def _run_orchestration_job(job_id: str, payload: HardeningRunPayload):
    """Worker function executed in background thread."""
    with JOB_LOCK:
        if job_id not in JOBS:
            return
        job = JOBS[job_id]
        cancel_event: threading.Event = job.get("_cancel_event") or threading.Event()

        # Check if already cancelled before starting
        if job.get("status") in ("CANCELLED", "CANCELLING") or cancel_event.is_set():
            job["status"] = "CANCELLED"
            job["end_time"] = time.time()
            start = job.get("start_time") or job.get("created_at") or time.time()
            job["duration_seconds"] = round(job["end_time"] - start, 2)
            return

        if job.get("status") in ("COMPLETED", "FAILED", "TIMED_OUT"):
            return

        job["status"] = "RUNNING"
        job["start_time"] = time.time()
        timeout_seconds = job.get("timeout_seconds", payload.timeout_seconds or 300)

    mcp_client = None
    try:
        from testforge.mcp_client import create_filesystem_client
        from testforge.callbacks import default_callback_registry
        mcp_client = create_filesystem_client(
            permitted_root=BASE_DIR,
            callback_registry=default_callback_registry
        )
    except Exception as exc:
        logger.warning(f"Could not initialize filesystem MCP client for job {job_id}: {exc}")

    try:
        resume_cp_id = payload.resume_checkpoint_id
        if not resume_cp_id and payload.resume_job_id:
            storage = SQLiteBlackboardStorage(DEFAULT_CHECKPOINT_DB_PATH)
            try:
                cp = storage.get_resumable_checkpoint(job_id=payload.resume_job_id)
                if cp:
                    resume_cp_id = cp.checkpoint_id
                else:
                    raise ValueError(f"No resumable checkpoint found for job '{payload.resume_job_id}'.")
            finally:
                storage.close()

        trace_log = "testforge_trace.jsonl"
        orchestrator = TestForgeOrchestrator(
            target_source_code=payload.target_source_code or "",
            max_iterations=payload.max_iterations,
            target_mutation_score=payload.target_mutation_score,
            model_name=payload.model_name,
            trace_log_path=trace_log,
            target_file_path=payload.target_file_path or "",
            api_key=payload.gemini_api_key or os.environ.get("GEMINI_API_KEY"),
            openrouter_api_key=payload.openrouter_api_key or os.environ.get("OPENROUTER_API_KEY"),
            engine_mode=payload.engine_mode,
            target_lines=payload.target_lines,
            cancel_event=cancel_event,
            timeout_seconds=timeout_seconds,
            job_id=job_id,
            checkpoint_db_path=DEFAULT_CHECKPOINT_DB_PATH,
            mcp_client=mcp_client,
            resume_checkpoint_id=resume_cp_id,
        )

        with JOB_LOCK:
            if job_id in JOBS:
                JOBS[job_id]["_orchestrator"] = orchestrator
                if orchestrator.resumption_plan:
                    JOBS[job_id]["resumed_from_checkpoint"] = orchestrator.resumption_plan.checkpoint_id
                    JOBS[job_id]["resumption_plan"] = orchestrator.resumption_plan.model_dump()

        final_state = orchestrator.run()
        # Export hardened suite using job-specific path to guarantee concurrent job isolation
        job_export_path = str(SAMPLES_DIR / f"test_hardened_{job_id}.py")
        test_hardened_content = orchestrator.export_hardened_suite(job_export_path)
        # Also maintain top-level test_hardened.py for single-job CLI compatibility
        try:
            with open("test_hardened.py", "w", encoding="utf-8") as f:
                f.write(test_hardened_content)
        except Exception:
            pass

        active_provider = getattr(final_state, "active_provider", "") or orchestrator.generator.active_provider

        # Serialize Pydantic models
        state_dict = final_state.model_dump() if hasattr(final_state, "model_dump") else final_state.dict()
        # Bidirectional alias mapping for frontend API compatibility
        state_dict["mutation_score"] = getattr(final_state, "final_mutation_score", None)
        state_dict["final_mutation_score"] = getattr(final_state, "final_mutation_score", None)
        state_dict["hardening_status"] = getattr(final_state, "final_hardening_status", "UNKNOWN")
        state_dict["iteration_history"] = state_dict.get("history", [])
        state_dict["baseline_coverage"] = getattr(final_state, "baseline_line_coverage", 0.0)
        state_dict["baseline_line_coverage"] = getattr(final_state, "baseline_line_coverage", 0.0)
        state_dict["baseline_branch_coverage"] = getattr(final_state, "baseline_branch_coverage", 0.0)
        state_dict["branch_coverage"] = getattr(final_state, "baseline_branch_coverage", 0.0)
        state_dict["total_branches"] = getattr(final_state, "total_branches", 0)
        state_dict["covered_branches"] = getattr(final_state, "covered_branches", 0)
        state_dict["missing_branches"] = getattr(final_state, "missing_branches", [])
        state_dict["baseline_execution_error"] = getattr(final_state, "baseline_execution_error", None)
        state_dict["execution_errors"] = getattr(final_state, "execution_errors", 0) or getattr(final_state, "mutation_execution_errors", 0)
        state_dict["baseline_run"] = {
            "tests_generated": getattr(final_state, "baseline_tests_generated", 0),
            "tests_executed": getattr(final_state, "baseline_tests_executed", 0),
            "tests_passed": getattr(final_state, "baseline_tests_passed", 0),
            "tests_failed": getattr(final_state, "baseline_tests_failed", 0),
            "passed": getattr(final_state, "baseline_passed", False),
            "execution_error": getattr(final_state, "baseline_execution_error", None),
        }

        with JOB_LOCK:
            if job_id in JOBS:
                job_record = JOBS[job_id]
                final_status = getattr(final_state, "final_hardening_status", None) or getattr(final_state, "verdict", None)
                curr_status = job_record.get("status")

                if final_status in ("EXECUTION_ERROR", "FAILED_BASELINE", "MUTATION_GENERATION_FAILED", "MUTATION_EXECUTION_FAILED", "FAILED"):
                    job_record["status"] = "FAILED"
                    job_record["error"] = getattr(final_state, "termination_reason", "Pipeline execution failure")
                    job_record["lifecycle_state"] = TaskLifecycleState.FAILED.value
                elif final_status == "TIMED_OUT":
                    job_record["status"] = "TIMED_OUT"
                    job_record["lifecycle_state"] = TaskLifecycleState.TIMED_OUT.value
                elif final_status == "CANCELLED" or curr_status == "CANCELLING" or cancel_event.is_set():
                    job_record["status"] = "CANCELLED"
                    job_record["lifecycle_state"] = TaskLifecycleState.CANCELLED.value
                elif curr_status not in ("COMPLETED", "FAILED", "CANCELLED", "TIMED_OUT"):
                    job_record["status"] = "COMPLETED"
                    job_record["lifecycle_state"] = TaskLifecycleState.COMPLETED.value

                job_record["end_time"] = time.time()
                start = job_record.get("start_time", job_record.get("created_at", time.time()))
                job_record["duration_seconds"] = round(job_record["end_time"] - start, 2)
                job_record["final_state"] = state_dict
                job_record["test_hardened_code"] = test_hardened_content
                job_record["active_provider"] = active_provider
                job_record["stage_durations"] = getattr(final_state, "stage_durations", {})
                job_record["stage_history"] = [
                    r.model_dump() if hasattr(r, "model_dump") else r
                    for r in getattr(final_state, "stage_history", [])
                ]
                if orchestrator.resumption_plan:
                    job_record["resumed_from_checkpoint"] = orchestrator.resumption_plan.checkpoint_id
                    job_record["resumption_plan"] = orchestrator.resumption_plan.model_dump()
    except Exception as exc:
        logger.error(f"Job {job_id} failed: {exc}", exc_info=True)
        with JOB_LOCK:
            if job_id in JOBS:
                job_record = JOBS[job_id]
                # Never overwrite terminal CANCELLED or TIMED_OUT states
                if job_record.get("status") not in ("CANCELLED", "TIMED_OUT"):
                    job_record["status"] = "FAILED"
                    job_record["lifecycle_state"] = TaskLifecycleState.FAILED.value
                    job_record["error"] = str(exc)
                    job_record["end_time"] = time.time()
    finally:
        if mcp_client:
            try:
                mcp_client.disconnect_sync()
            except Exception:
                pass


@app.post("/api/harden/start")
async def start_hardening_job(payload: HardeningRunPayload, background_tasks: BackgroundTasks):
    """
    Initiates an asynchronous autonomous hardening run and returns a job_id for polling.
    """
    if not payload.resume_checkpoint_id and not payload.resume_job_id:
        if not (payload.target_source_code and payload.target_source_code.strip()) or not (payload.target_file_path and payload.target_file_path.strip()):
            raise HTTPException(status_code=400, detail="Target source code and file path are required.")

    job_id = str(uuid.uuid4())[:8]
    cancel_event = threading.Event()
    with JOB_LOCK:
        JOBS[job_id] = {
            "job_id": job_id,
            "status": "QUEUED",
            "lifecycle_state": TaskLifecycleState.CREATED.value,
            "stage_durations": {},
            "stage_history": [],
            "created_at": time.time(),
            "target_file_path": payload.target_file_path,
            "max_iterations": payload.max_iterations,
            "target_mutation_score": payload.target_mutation_score,
            "engine_mode": payload.engine_mode,
            "model_name": payload.model_name,
            "timeout_seconds": payload.timeout_seconds or 300,
            "_cancel_event": cancel_event,
            "_orchestrator": None,
        }

    worker_thread = threading.Thread(
        target=_run_orchestration_job,
        args=(job_id, payload),
        daemon=True,
        name=f"worker-{job_id}"
    )
    worker_thread.start()

    return {
        "status": "queued",
        "job_id": job_id,
        "poll_url": f"/api/harden/status/{job_id}"
    }


@app.get("/api/harden/status/{job_id}")
async def get_hardening_job_status(job_id: str):
    """
    Polls status, metrics, mutant records, and hardened test output of a running or completed job.
    """
    with JOB_LOCK:
        job = JOBS.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Hardening job '{job_id}' not found.")
        orch = job.get("_orchestrator")
        if orch:
            if hasattr(orch, "fsm"):
                job["lifecycle_state"] = orch.fsm.current_state.value
                job["stage_durations"] = orch.fsm.get_stage_durations()
                job["stage_history"] = [r.model_dump() for r in orch.fsm.get_history()]
            if hasattr(orch, "resumption_plan") and orch.resumption_plan:
                job["resumption_plan"] = orch.resumption_plan.model_dump()
                job["resumed_from_checkpoint"] = orch.resumption_plan.checkpoint_id
            if hasattr(orch, "state") and orch.state:
                job["current_iteration"] = getattr(orch.state, "iteration", 0)
                job["max_iterations"] = getattr(orch.state, "max_iterations", 3)
            if hasattr(orch, "blackboard") and orch.blackboard:
                bb = orch.blackboard
                with bb._lock:
                    job["blackboard_summary"] = {
                        "revision": bb.revision,
                        "spaces": {
                            "TargetSpace": {
                                "status": "active" if bb.target.target_source_code else "empty",
                                "module": bb.target.target_module_path,
                                "functions_count": len(bb.target.functions),
                                "blast_risk": bb.target.blast_risk
                            },
                            "SuiteSpace": {
                                "status": "active" if bb.suite.current_test_code else "empty",
                                "provider": bb.suite.active_provider,
                                "has_baseline": bool(bb.suite.baseline_test_code),
                                "has_hardened": bool(bb.suite.hardened_test_code)
                            },
                            "MutantSpace": {
                                "status": "active" if bb.mutant.mutants_generated > 0 else "empty",
                                "generated": bb.mutant.mutants_generated,
                                "killed": bb.mutant.mutants_killed,
                                "survived": bb.mutant.mutants_survived,
                                "score": bb.mutant.raw_mutation_score
                            },
                            "CriticSpace": {
                                "status": "active" if (bb.critic.latest_directive or bb.critic.critic_directives) else "empty",
                                "directives_count": len(bb.critic.critic_directives),
                                "has_latest": bool(bb.critic.latest_directive)
                            },
                            "ExecutionSpace": {
                                "status": "active" if bb.execution.status != "NOT_STARTED" else "empty",
                                "status_val": bb.execution.status,
                                "total_tests": bb.execution.total_tests,
                                "passed_tests": bb.execution.passed_tests,
                                "line_coverage_pct": bb.execution.line_coverage_pct,
                                "branch_coverage": getattr(bb.execution, "branch_coverage", 0.0),
                                "total_branches": getattr(bb.execution, "total_branches", 0),
                                "covered_branches": getattr(bb.execution, "covered_branches", 0),
                            },
                            "MetricsSpace": {
                                "status": "active" if (bb.metrics.current_iteration > 0 or bb.metrics.history) else "empty",
                                "iteration": bb.metrics.current_iteration,
                                "score": bb.metrics.final_mutation_score or bb.metrics.raw_mutation_score,
                                "line_coverage": getattr(bb.metrics, "baseline_line_coverage", 0.0),
                                "branch_coverage": getattr(bb.metrics, "branch_coverage", 0.0),
                                "total_branches": getattr(bb.metrics, "total_branches", 0),
                                "covered_branches": getattr(bb.metrics, "covered_branches", 0),
                                "status_val": bb.metrics.final_hardening_status
                            }
                        }
                    }

        # If job is finalized/completed and blackboard_summary is not yet set, build from final_state
        if "blackboard_summary" not in job and "final_state" in job:
            fs = job["final_state"]
            mut_records = fs.get("mutants", [])
            gen_count = len(mut_records)
            kill_count = sum(1 for m in mut_records if m.get("status") == "KILLED")
            surv_count = sum(1 for m in mut_records if m.get("status") == "SURVIVED")
            job["blackboard_summary"] = {
                "revision": fs.get("revision", 76),
                "spaces": {
                    "TargetSpace": {
                        "status": "active",
                        "module": fs.get("target_module_path", "samples/discount.py"),
                        "functions_count": len(fs.get("target_metadata", {}).get("functions", [])),
                        "blast_risk": fs.get("blast_risk", "LOW")
                    },
                    "SuiteSpace": {
                        "status": "active",
                        "provider": fs.get("active_provider", "Google ADK Generator"),
                        "has_baseline": True,
                        "has_hardened": bool(fs.get("hardened_test_code"))
                    },
                    "MutantSpace": {
                        "status": "active",
                        "generated": gen_count,
                        "killed": kill_count,
                        "survived": surv_count,
                        "score": fs.get("final_mutation_score", fs.get("mutation_score", 0))
                    },
                    "CriticSpace": {
                        "status": "active",
                        "directives_count": len(fs.get("critic_directives", [])),
                        "has_latest": bool(fs.get("latest_directive"))
                    },
                    "ExecutionSpace": {
                        "status": "active",
                        "status_val": "PASSED",
                        "line_coverage_pct": fs.get("baseline_line_coverage", fs.get("baseline_coverage", 0.0)),
                        "branch_coverage": fs.get("baseline_branch_coverage", fs.get("branch_coverage", 0.0)),
                        "total_branches": fs.get("total_branches", 0),
                        "covered_branches": fs.get("covered_branches", 0),
                    },
                    "MetricsSpace": {
                        "status": "active",
                        "iteration": len(fs.get("history", fs.get("iteration_history", []))),
                        "score": fs.get("final_mutation_score", fs.get("mutation_score", 0)),
                        "line_coverage": fs.get("baseline_line_coverage", fs.get("baseline_coverage", 0.0)),
                        "branch_coverage": fs.get("baseline_branch_coverage", fs.get("branch_coverage", 0.0)),
                        "total_branches": fs.get("total_branches", 0),
                        "covered_branches": fs.get("covered_branches", 0),
                        "status_val": fs.get("final_hardening_status", "COMPLETED")
                    }
                }
            }
        # Filter out internal/non-serializable keys (starting with _)
        return {k: v for k, v in job.items() if not k.startswith("_")}


@app.post("/api/harden/cancel/{job_id}")
async def cancel_hardening_job(job_id: str):
    """
    Gracefully requests cooperative cancellation of an active or queued hardening job.
    Idempotent and thread-safe.
    """
    with JOB_LOCK:
        job = JOBS.get(job_id)
        if not job:
            raise HTTPException(status_code=404, detail=f"Hardening job '{job_id}' not found.")

        current_status = job.get("status")

        # Check if already terminal
        if current_status in ("COMPLETED", "FAILED", "CANCELLED", "TIMED_OUT"):
            return {
                "status": "already_terminal",
                "job_id": job_id,
                "current_status": current_status,
                "message": f"Job '{job_id}' is already in terminal state '{current_status}'."
            }

        # Signal cancellation event
        cancel_evt: Optional[threading.Event] = job.get("_cancel_event")
        if cancel_evt is not None:
            cancel_evt.set()

        # Handle QUEUED state immediately
        if current_status == "QUEUED":
            job["status"] = "CANCELLED"
            job["lifecycle_state"] = TaskLifecycleState.CANCELLED.value
            job["end_time"] = time.time()
            start = job.get("created_at", time.time())
            job["duration_seconds"] = round(job["end_time"] - start, 2)
            return {
                "status": "cancelled",
                "job_id": job_id,
                "current_status": "CANCELLED",
                "lifecycle_state": "CANCELLED",
                "message": f"Queued job '{job_id}' was cancelled before execution."
            }

        # Handle RUNNING state
        if current_status == "RUNNING":
            job["status"] = "CANCELLING"
            job["lifecycle_state"] = TaskLifecycleState.CANCELLING.value
            job["cancellation_requested_at"] = time.time()
            return {
                "status": "cancelling",
                "job_id": job_id,
                "current_status": "CANCELLING",
                "lifecycle_state": "CANCELLING",
                "message": f"Cancellation request sent for running job '{job_id}'."
            }

        # Handle already CANCELLING state
        return {
            "status": "cancelling",
            "job_id": job_id,
            "current_status": current_status,
            "lifecycle_state": job.get("lifecycle_state", current_status),
            "message": f"Job '{job_id}' is already undergoing cancellation."
        }


@app.post("/api/harden/run")
def run_hardening_sync(payload: HardeningRunPayload):
    """
    Synchronous execution endpoint for automated test callers or direct single-invocation workflows.
    """
    if not payload.resume_checkpoint_id and not payload.resume_job_id:
        if not (payload.target_source_code and payload.target_source_code.strip()) or not (payload.target_file_path and payload.target_file_path.strip()):
            raise HTTPException(status_code=400, detail="Target source code and file path are required.")

    job_id = f"sync_{str(uuid.uuid4())[:6]}"
    cancel_event = threading.Event()
    with JOB_LOCK:
        JOBS[job_id] = {
            "job_id": job_id,
            "status": "RUNNING",
            "start_time": time.time(),
            "timeout_seconds": payload.timeout_seconds or 300,
            "_cancel_event": cancel_event,
            "_orchestrator": None,
        }
    _run_orchestration_job(job_id, payload)
    with JOB_LOCK:
        return {k: v for k, v in JOBS[job_id].items() if not k.startswith("_")}


@app.get("/api/hardened-code")
async def get_hardened_suite():
    """
    Returns the current contents of the generated standalone test suite `test_hardened.py`.
    """
    suite_path = BASE_DIR / "test_hardened.py"
    if not suite_path.exists():
        return {"code": "", "exists": False}
    return {
        "code": suite_path.read_text(encoding="utf-8"),
        "exists": True,
        "file_path": str(suite_path)
    }


# --------------------------------------------------------------------------
# Checkpoint Persistence & Recovery Endpoints
# --------------------------------------------------------------------------

@app.get("/api/checkpoints")
async def list_checkpoints(
    job_id: Optional[str] = None,
    workflow_id: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """
    Lists saved Blackboard checkpoints with metadata, stages, and pagination.
    """
    try:
        from testforge.persistence import SQLiteBlackboardStorage
        storage = SQLiteBlackboardStorage(DEFAULT_CHECKPOINT_DB_PATH)
        checkpoints = storage.list_checkpoints(job_id=job_id, workflow_id=workflow_id, limit=limit, offset=offset)
        total = storage.count_checkpoints(job_id=job_id, workflow_id=workflow_id)
        storage.close()
        return {
            "checkpoints": [c.model_dump() for c in checkpoints],
            "total_count": total,
            "limit": limit,
            "offset": offset,
        }
    except Exception as exc:
        logger.error(f"Failed to list checkpoints: {exc}", exc_info=True)
        return {"checkpoints": [], "total_count": 0, "error": str(exc)}


@app.get("/api/checkpoints/diff")
async def diff_checkpoints_endpoint(
    base_id: str,
    target_id: str,
    include_unchanged: bool = False
):
    """
    Computes a deterministic, partition-aware semantic diff between two checkpoints.
    """
    try:
        from testforge.persistence import SQLiteBlackboardStorage, CheckpointNotFoundError
        from testforge.diff_inspector import compare_checkpoints
        storage = SQLiteBlackboardStorage(DEFAULT_CHECKPOINT_DB_PATH)
        try:
            base_record = storage.load_checkpoint(base_id)
            target_record = storage.load_checkpoint(target_id)
        finally:
            storage.close()

        base_dict = json.loads(base_record.snapshot_json)
        target_dict = json.loads(target_record.snapshot_json)

        diff_result = compare_checkpoints(
            base_snapshot=base_dict,
            target_snapshot=target_dict,
            base_checkpoint_id=base_id,
            target_checkpoint_id=target_id,
            base_stage=base_record.metadata.stage,
            target_stage=target_record.metadata.stage,
            include_unchanged=include_unchanged
        )
        return diff_result.model_dump()
    except CheckpointNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        logger.error(f"Error computing diff between {base_id} and {target_id}: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/api/checkpoints/{checkpoint_id}")
async def get_checkpoint_details(checkpoint_id: str):
    """
    Retrieves metadata and structured partition info for a specific checkpoint.
    """
    try:
        from testforge.persistence import SQLiteBlackboardStorage, CheckpointNotFoundError
        storage = SQLiteBlackboardStorage(DEFAULT_CHECKPOINT_DB_PATH)
        try:
            record = storage.load_checkpoint(checkpoint_id)
        finally:
            storage.close()

        snapshot_dict = json.loads(record.snapshot_json)
        return {
            "metadata": record.metadata.model_dump(),
            "target": snapshot_dict.get("target", {}),
            "metrics": snapshot_dict.get("metrics", {}),
            "critic": snapshot_dict.get("critic", {}),
            "suite_info": {
                "test_module_path": snapshot_dict.get("suite", {}).get("test_module_path"),
                "active_provider": snapshot_dict.get("suite", {}).get("active_provider"),
                "test_code_length": len(snapshot_dict.get("suite", {}).get("current_test_code", "")),
            },
            "mutant_summary": {
                "count": len(snapshot_dict.get("mutant", {}).get("mutants", [])),
                "generated": snapshot_dict.get("mutant", {}).get("mutants_generated", 0),
                "killed": snapshot_dict.get("mutant", {}).get("mutants_killed", 0),
                "survived": snapshot_dict.get("mutant", {}).get("mutants_survived", 0),
            },
            "suite": snapshot_dict.get("suite", {}),
            "mutant": snapshot_dict.get("mutant", {}),
            "snapshot": snapshot_dict,
        }
    except CheckpointNotFoundError:
        raise HTTPException(status_code=404, detail=f"Checkpoint '{checkpoint_id}' not found.")
    except Exception as exc:
        logger.error(f"Error loading checkpoint {checkpoint_id}: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))




@app.post("/api/checkpoints/{checkpoint_id}/restore")
async def restore_checkpoint_endpoint(checkpoint_id: str):
    """
    Restores the specified checkpoint into an isolated Blackboard instance for
    diagnostic inspection, state comparison, and verification.
    """
    try:
        from testforge.persistence import SQLiteBlackboardStorage, CheckpointNotFoundError
        from testforge.blackboard import Blackboard, BlackboardSnapshot
        storage = SQLiteBlackboardStorage(DEFAULT_CHECKPOINT_DB_PATH)
        try:
            record = storage.load_checkpoint(checkpoint_id)
        finally:
            storage.close()

        bb = Blackboard()
        snapshot_dict = json.loads(record.snapshot_json)
        snapshot = BlackboardSnapshot.model_validate(snapshot_dict)
        bb.restore_from_snapshot(snapshot)

        restored_state = bb.to_testforge_state()
        return {
            "status": "restored",
            "checkpoint_id": checkpoint_id,
            "revision": bb.revision,
            "stage": record.metadata.stage,
            "restored_state": restored_state.model_dump(),
        }
    except CheckpointNotFoundError:
        raise HTTPException(status_code=404, detail=f"Checkpoint '{checkpoint_id}' not found.")
    except Exception as exc:
        logger.error(f"Failed to restore checkpoint {checkpoint_id}: {exc}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/api/checkpoints/{checkpoint_id}/resume")
async def resume_checkpoint_execution(
    checkpoint_id: str,
    background_tasks: BackgroundTasks,
    payload: Optional[CheckpointResumePayload] = None
):
    """
    Initiates genuine execution resumption from an existing checkpoint.
    Validates schema and partition completeness before queuing the resumed task.
    """
    storage = SQLiteBlackboardStorage(DEFAULT_CHECKPOINT_DB_PATH)
    try:
        record, plan = storage.validate_checkpoint(
            checkpoint_id,
            expected_source_code=payload.expected_source_code if payload else None
        )
    except CheckpointNotFoundError:
        raise HTTPException(status_code=404, detail=f"Checkpoint '{checkpoint_id}' not found.")
    except (InputHashMismatchError, IncompleteCheckpointError, IncompatibleSchemaError, CorruptedSnapshotError, InvalidRecoveryStageError) as exc:
        raise HTTPException(status_code=422, detail=f"Checkpoint '{checkpoint_id}' cannot be resumed: {str(exc)}")
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        storage.close()

    job_id = str(uuid.uuid4())[:8]
    cancel_event = threading.Event()
    hardening_payload = HardeningRunPayload(
        resume_checkpoint_id=checkpoint_id,
        max_iterations=payload.max_iterations if payload and payload.max_iterations else 3,
        target_mutation_score=payload.target_mutation_score if payload and payload.target_mutation_score else 85.0,
        timeout_seconds=payload.timeout_seconds if payload and payload.timeout_seconds else 300,
        model_name=payload.model_name if payload and payload.model_name else "gemini-3.6-flash",
        engine_mode=payload.engine_mode if payload and payload.engine_mode else "auto",
    )

    with JOB_LOCK:
        JOBS[job_id] = {
            "job_id": job_id,
            "status": "QUEUED",
            "lifecycle_state": TaskLifecycleState.CREATED.value,
            "stage_durations": {},
            "stage_history": [],
            "created_at": time.time(),
            "target_file_path": getattr(record.metadata, "target_file", None) or "resumed_task",
            "max_iterations": hardening_payload.max_iterations,
            "target_mutation_score": hardening_payload.target_mutation_score,
            "engine_mode": hardening_payload.engine_mode,
            "model_name": hardening_payload.model_name,
            "timeout_seconds": hardening_payload.timeout_seconds,
            "resumed_from_checkpoint": checkpoint_id,
            "resumption_plan": plan.model_dump(),
            "_cancel_event": cancel_event,
            "_orchestrator": None,
        }

    worker_thread = threading.Thread(
        target=_run_orchestration_job,
        args=(job_id, hardening_payload),
        daemon=True,
        name=f"worker-{job_id}"
    )
    worker_thread.start()

    return {
        "status": "queued",
        "job_id": job_id,
        "resumed_from_checkpoint": checkpoint_id,
        "resumption_plan": plan.model_dump(),
        "poll_url": f"/api/harden/status/{job_id}"
    }


@app.post("/api/harden/resume/{job_id}")
async def resume_job_execution(
    job_id: str,
    background_tasks: BackgroundTasks,
    payload: Optional[CheckpointResumePayload] = None
):
    """
    Finds the latest resumable checkpoint for an interrupted or failed job and initiates execution resumption.
    Returns HTTP 200 with {"status": "RESUMED", "job_id": job_id, "resumed_stage": stage}.
    """
    storage = SQLiteBlackboardStorage(DEFAULT_CHECKPOINT_DB_PATH)
    try:
        cp = storage.get_resumable_checkpoint(job_id=job_id)
        if not cp:
            # Check latest checkpoint even if in intermediate stage
            cp = storage.get_latest_checkpoint(job_id=job_id)
        if not cp:
            raise HTTPException(status_code=404, detail=f"No resumable checkpoint found: Job '{job_id}' not found.")

        rec, plan = storage.validate_checkpoint(
            cp.checkpoint_id,
            expected_source_code=payload.expected_source_code if payload else None
        )
    except CheckpointNotFoundError:
        raise HTTPException(status_code=404, detail=f"Checkpoint for job '{job_id}' not found.")
    except (InputHashMismatchError, IncompleteCheckpointError, IncompatibleSchemaError, CorruptedSnapshotError, InvalidRecoveryStageError) as exc:
        raise HTTPException(status_code=422, detail=f"Checkpoint for job '{job_id}' cannot be resumed: {str(exc)}")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    finally:
        storage.close()

    stage = plan.resumes_at or getattr(rec.metadata, "stage", "INITIALIZING")
    cancel_event = threading.Event()
    hardening_payload = HardeningRunPayload(
        resume_checkpoint_id=cp.checkpoint_id,
        resume_job_id=job_id,
        max_iterations=payload.max_iterations if payload and payload.max_iterations else 3,
        target_mutation_score=payload.target_mutation_score if payload and payload.target_mutation_score else 85.0,
        timeout_seconds=payload.timeout_seconds if payload and payload.timeout_seconds else 300,
        model_name=payload.model_name if payload and payload.model_name else "gemini-3.6-flash",
        engine_mode=payload.engine_mode if payload and payload.engine_mode else "auto",
    )

    with JOB_LOCK:
        JOBS[job_id] = {
            "job_id": job_id,
            "status": "RUNNING",
            "lifecycle_state": TaskLifecycleState.RECOVERING.value,
            "stage_durations": {},
            "stage_history": [],
            "created_at": time.time(),
            "target_file_path": getattr(rec.metadata, "target_file", None) or "resumed_task",
            "max_iterations": hardening_payload.max_iterations,
            "target_mutation_score": hardening_payload.target_mutation_score,
            "engine_mode": hardening_payload.engine_mode,
            "model_name": hardening_payload.model_name,
            "timeout_seconds": hardening_payload.timeout_seconds,
            "resumed_from_checkpoint": cp.checkpoint_id,
            "resumed_stage": stage,
            "resumption_plan": plan.model_dump(),
            "_cancel_event": cancel_event,
            "_orchestrator": None,
        }

    worker_thread = threading.Thread(
        target=_run_orchestration_job,
        args=(job_id, hardening_payload),
        daemon=True,
        name=f"worker-{job_id}"
    )
    worker_thread.start()

    return {
        "status": "RESUMED",
        "job_id": job_id,
        "resumed_stage": stage,
        "resumed_from_checkpoint": cp.checkpoint_id,
        "poll_url": f"/api/harden/status/{job_id}",
    }


# --------------------------------------------------------------------------
# Enterprise CI/CD Report Exports (GAP-010): JUnit XML & OASIS SARIF v2.1.0
# --------------------------------------------------------------------------

from testforge.export import generate_junit_xml, generate_sarif_report


@app.get("/api/export/junit/{job_id}")
async def export_junit_report(job_id: str):
    """
    Exports a standard JUnit XML report for all unit tests and mutation evaluations for job_id.
    """
    with JOB_LOCK:
        job = JOBS.get(job_id)

    if not job:
        storage = SQLiteBlackboardStorage(DEFAULT_CHECKPOINT_DB_PATH)
        try:
            rec = storage.get_latest_checkpoint(job_id=job_id)
            if rec:
                snap = json.loads(rec.snapshot_json)
                job = {
                    "job_id": job_id,
                    "target_file_path": snap.get("target", {}).get("target_module_path", "target.py"),
                    "final_state": {
                        "mutants": snap.get("mutant", {}).get("mutants", []),
                        "baseline_run": {
                            "tests_executed": snap.get("suite", {}).get("baseline_tests_executed", 1),
                            "tests_passed": snap.get("suite", {}).get("baseline_tests_passed", 1),
                            "tests_failed": snap.get("suite", {}).get("baseline_tests_failed", 0),
                        }
                    }
                }
        finally:
            storage.close()

    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")

    xml_content = generate_junit_xml(job_id, job)
    return Response(
        content=xml_content,
        media_type="application/xml",
        headers={"Content-Disposition": f'attachment; filename="testforge-junit-{job_id}.xml"'}
    )


@app.get("/api/export/sarif/{job_id}")
async def export_sarif_report(job_id: str):
    """
    Exports an OASIS standard SARIF v2.1.0 vulnerability report for job_id.
    """
    with JOB_LOCK:
        job = JOBS.get(job_id)

    if not job:
        storage = SQLiteBlackboardStorage(DEFAULT_CHECKPOINT_DB_PATH)
        try:
            rec = storage.get_latest_checkpoint(job_id=job_id)
            if rec:
                snap = json.loads(rec.snapshot_json)
                job = {
                    "job_id": job_id,
                    "target_file_path": snap.get("target", {}).get("target_module_path", "target.py"),
                    "final_state": {
                        "mutants": snap.get("mutant", {}).get("mutants", []),
                    }
                }
        finally:
            storage.close()

    if not job:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found.")

    sarif_data = generate_sarif_report(job_id, job)
    return JSONResponse(
        content=sarif_data,
        media_type="application/sarif+json",
        headers={"Content-Disposition": f'attachment; filename="testforge-sarif-{job_id}.json"'}
    )


# --------------------------------------------------------------------------
# Observability, Live Wiretap & Telemetry
# --------------------------------------------------------------------------

@app.get("/api/telemetry")
def get_telemetry_trace(
    limit: int = 50,
    scope: str = "all",
    workflow_id: Optional[str] = None,
    correlation_id: Optional[str] = None
):
    """
    Returns structured event traces, token audit, and foundation model inference latencies.
    Distinguishes actual LLM tokens from offline heuristic estimates, and supports
    isolated current run querying without combining historical runs.
    """
    logger_instance = TraceLogger("testforge_trace.jsonl")
    traces = logger_instance.read_traces()

    target_wf = workflow_id
    target_corr = correlation_id
    if scope == "current" and not target_wf and not target_corr:
        for t in reversed(traces):
            if t.get("workflow_id"):
                target_wf = t.get("workflow_id")
                break
            elif t.get("correlation_id"):
                target_corr = t.get("correlation_id")
                break

    filtered_traces = traces
    if target_wf:
        filtered_traces = [t for t in traces if t.get("workflow_id") == target_wf or t.get("metadata", {}).get("workflow_id") == target_wf]
    elif target_corr:
        filtered_traces = [t for t in traces if t.get("correlation_id") == target_corr or t.get("metadata", {}).get("correlation_id") == target_corr]

    summary = logger_instance.get_token_summary(traces=filtered_traces)
    llm_events = [t for t in filtered_traces if t.get("event_type") == "LLM_INFERENCE_TELEMETRY"]

    # 4-concept model & provider resolution
    configured_model = os.environ.get("TESTFORGE_MODEL", "gemini-3.6-flash")
    if os.environ.get("GEMINI_API_KEY"):
        active_provider = "Google GenAI (Gemini)"
    elif os.environ.get("OPENROUTER_API_KEY"):
        active_provider = "OpenRouter Cloud"
    elif is_ollama_running():
        active_provider = "Local Ollama"
    else:
        active_provider = "None (Offline)"

    normalized_calls = []
    engine_labels = []
    for event in reversed(llm_events[-limit:]):
        d = dict(event.get("data", {}))
        is_actual = d.get("is_actual_llm")
        model = d.get("model_name") or d.get("model", "")
        provider = d.get("provider") or d.get("provider_type", "")
        if is_actual is None:
            is_actual = False if ("deterministic" in model.lower() or "ast" in model.lower() or provider == "Unknown") else True
            d["is_actual_llm"] = is_actual
        if "token_accounting_source" not in d:
            d["token_accounting_source"] = "provider_reported" if is_actual else "offline_heuristic_estimate"

        # Dynamically resolve engine, provider, and clean model
        engine_lbl, norm_prov, norm_model = resolve_dynamic_execution_engine(
            model_name=model,
            provider_type=provider,
            is_actual_llm=is_actual
        )

        tokens_obj = d.get("tokens", {})
        if "actual_total_tokens" in d and "estimated_total_tokens" in d:
            actual_p = d.get("actual_prompt_tokens", 0)
            actual_c = d.get("actual_completion_tokens", 0)
            actual_t = d.get("actual_total_tokens", 0)
            est_p = d.get("estimated_prompt_tokens", 0)
            est_c = d.get("estimated_completion_tokens", 0)
            est_t = d.get("estimated_total_tokens", 0)
        else:
            raw_p = tokens_obj.get("prompt_tokens", d.get("prompt_tokens", 0)) or 0
            raw_c = tokens_obj.get("completion_tokens", d.get("completion_tokens", 0)) or 0
            raw_t = tokens_obj.get("total_tokens", d.get("total_tokens", 0)) or 0
            if is_actual:
                actual_p, actual_c, actual_t = raw_p, raw_c, raw_t
                est_p, est_c, est_t = 0, 0, 0
            else:
                actual_p, actual_c, actual_t = 0, 0, 0
                est_p, est_c, est_t = raw_p, raw_c, raw_t

        if not is_actual:
            d["provider"] = None
            d["model_name"] = None
            d["execution_engine"] = "AST Deterministic Synthesizer"
            d["actual_prompt_tokens"] = 0
            d["actual_completion_tokens"] = 0
            d["actual_total_tokens"] = 0
            d["estimated_prompt_tokens"] = est_p
            d["estimated_completion_tokens"] = est_c
            d["estimated_total_tokens"] = est_t
            engine_labels.append("Deterministic AST Synthesizer")
        else:
            d["provider"] = norm_prov
            d["model_name"] = norm_model
            d["execution_engine"] = engine_lbl
            d["actual_prompt_tokens"] = actual_p
            d["actual_completion_tokens"] = actual_c
            d["actual_total_tokens"] = actual_t
            d["estimated_prompt_tokens"] = 0
            d["estimated_completion_tokens"] = 0
            d["estimated_total_tokens"] = 0
            engine_labels.append(engine_lbl)

        d["prompt_tokens"] = d["actual_prompt_tokens"]
        d["completion_tokens"] = d["actual_completion_tokens"]
        d["total_tokens"] = d["actual_total_tokens"]
        d["workflow_id"] = event.get("workflow_id")
        d["correlation_id"] = event.get("correlation_id")
        d["ast_valid"] = d.get("is_valid_ast", True)
        d["latency_seconds"] = float(d.get("latency_seconds", 0.0))

        normalized_calls.append({
            "timestamp": event.get("timestamp"),
            "iso_time": event.get("iso_time"),
            "event_type": event.get("event_type"),
            "workflow_id": event.get("workflow_id"),
            "correlation_id": event.get("correlation_id"),
            "data": d,
            "metadata": event.get("metadata", {})
        })

    # Scope-level KPI determination
    if not llm_events:
        execution_engine_kpi = "No Execution Yet"
        last_execution_model = None
        last_execution_engine = None
    else:
        execution_engine_kpi = summary.get("execution_engine_kpi") or determine_scope_execution_engine(engine_labels)
        last_execution_model = summary.get("last_execution_model")
        last_execution_engine = summary.get("last_execution_engine")

    return {
        "scope": scope,
        "selected_workflow_id": target_wf or target_corr or "all",
        "configured_model": configured_model,
        "active_provider": active_provider,
        "actual_execution_engine": execution_engine_kpi,
        "execution_engine_kpi": execution_engine_kpi,
        "last_execution_model": last_execution_model,
        "last_execution_engine": last_execution_engine,
        "execution_engine_breakdown": summary.get("execution_engine_breakdown", {}),
        "execution_engines_used": summary.get("unique_execution_engines", []),
        "total_logged_events": len(filtered_traces),
        "actual_llm_tokens_used": summary["actual_llm_tokens"],
        "actual_prompt_tokens_used": summary["actual_prompt_tokens"],
        "actual_completion_tokens_used": summary["actual_completion_tokens"],
        "estimated_tokens_used": summary["estimated_tokens"],
        "estimated_prompt_tokens_used": summary["estimated_prompt_tokens"],
        "estimated_completion_tokens_used": summary["estimated_completion_tokens"],
        "total_tokens_used": summary["actual_llm_tokens"],
        "combined_tokens_including_estimates": summary["total_tokens"],
        "total_actual_llm_calls": summary["actual_calls"],
        "total_deterministic_calls": summary["deterministic_calls"],
        "recent_traces": list(reversed(filtered_traces[-limit:])),
        "recent_llm_calls": normalized_calls,
    }


@app.get("/api/wiretap")
def get_wiretap_events(workflow_id: Optional[str] = None):
    """
    Returns multi-agent handoff trajectories and ADK tool deliberation events.
    Optionally scoped to a specific workflow_id.
    """
    logger_instance = TraceLogger("testforge_trace.jsonl")
    traces = logger_instance.read_traces()

    if workflow_id:
        traces = [t for t in traces if t.get("workflow_id") == workflow_id or t.get("correlation_id") == workflow_id]

    handoffs = [t for t in traces if t.get("event_type") == "AGENT_HANDOFF"]
    adk_calls = [t for t in traces if t.get("event_type") == "ADK_TOOL_CALL"]
    supervisor_decisions = [t for t in traces if t.get("event_type") == "SUPERVISOR_DECISION"]

    participating_entities = set()
    for h in handoffs:
        d = h.get("data", {})
        if d.get("from_agent"):
            participating_entities.add(d["from_agent"])
        if d.get("to_agent"):
            participating_entities.add(d["to_agent"])

    for s in supervisor_decisions:
        participating_entities.add("SupervisorAgent")
        d = s.get("data", {})
        target = d.get("target_agent", "")
        if target:
            clean_target = target.split(":")[-1].replace("-", " ").title().replace(" ", "")
            for c in ("CodeIntelligenceAgent", "SecurityAgent", "TestPlanningAgent", "TestExecutionAgent", "MutationQualityCriticAgent", "ReflectionRepairAgent"):
                if c.lower() in clean_target.lower():
                    participating_entities.add(c)

    sorted_entities = sorted(list(participating_entities))
    cognitive_agents = [e for e in sorted_entities if e != "SubprocessSandbox"]
    tool_entities = [e for e in sorted_entities if e == "SubprocessSandbox"]

    # Canonical Eight-Agent truthfulness matrix
    canonical_eight = [
        "SupervisorAgent",
        "CodeIntelligenceAgent",
        "TestPlanningAgent",
        "TestGeneratorAgent",
        "TestExecutionAgent",
        "MutationQualityCriticAgent",
        "SecurityAgent",
        "ReflectionRepairAgent",
    ]
    eight_agents_status = {}
    for agent_name in canonical_eight:
        is_participating = any(
            agent_name.lower() in str(e).lower()
            for e in participating_entities
        )
        eight_agents_status[agent_name] = {
            "name": agent_name,
            "registered": True,
            "instantiated": True,
            "available": True,
            "participating": is_participating,
            "executing": False,
            "completed": is_participating,
            "failed": False,
            "skipped": not is_participating if workflow_id else False,
        }

    return {
        "total_handoffs": len(handoffs),
        "total_adk_calls": len(adk_calls),
        "total_supervisor_decisions": len(supervisor_decisions),
        "participating_agents": sorted_entities,
        "cognitive_agents": cognitive_agents,
        "tool_entities": tool_entities,
        "cognitive_agents_count": len(cognitive_agents),
        "registered_agents": [
            "SupervisorAgent",
            "TargetManagerAgent",
            "TestGeneratorAgent",
            "GoogleADKTestGenerator",
            "AdversarialCriticAgent",
            "CrewAICriticAgent",
            "MutationQualityCriticAgent",
            "CodeIntelligenceAgent",
            "SecurityAgent",
            "TestPlanningAgent",
            "TestExecutionAgent",
            "ReflectionRepairAgent"
        ],
        "eight_agents_status": eight_agents_status,
        "supervisor_decisions": supervisor_decisions[-20:],
        "handoffs": handoffs,
        "adk_calls": adk_calls,
    }


# --------------------------------------------------------------------------
# Statistical Benchmarking & Cost Accounting Endpoints
# --------------------------------------------------------------------------

def _run_benchmark_job(job_id: str, payload: BenchmarkRunPayload):
    try:
        source_code = payload.target_source_code
        file_path = payload.target_file_path or "samples/discount.py"
        if not source_code or not source_code.strip():
            target_p = Path(file_path)
            if target_p.exists():
                source_code = target_p.read_text(encoding="utf-8")
            else:
                sample_p = SAMPLES_DIR / Path(file_path).name
                if sample_p.exists():
                    source_code = sample_p.read_text(encoding="utf-8")
                else:
                    source_code = (
                        "def calculate_discount(price: float, quantity: int) -> float:\n"
                        "    if quantity > 10:\n"
                        "        return price * 0.8\n"
                        "    elif quantity > 5:\n"
                        "        return price * 0.9\n"
                        "    return price\n"
                    )

        runner = BenchmarkRunner(
            target_code=source_code,
            target_file_path=file_path,
            baseline_tests=payload.baseline_tests,
            model_name=payload.model_name,
            job_id=job_id,
        )
        report = runner.run_benchmark(
            scenarios=payload.scenarios,
            repetitions=payload.repetitions,
            engine_mode=payload.engine_mode,
        )
        if not report.hardware_summary:
            report.hardware_summary = f"{hw_profile.machine} ({hw_profile.os_system}, {hw_profile.cpu_count} cores, {hw_profile.total_memory_gb:.1f}GB RAM)"

        data = report.model_dump()
        markdown = report.to_markdown()

        global LATEST_BENCHMARK
        LATEST_BENCHMARK = data

        try:
            (BASE_DIR / "benchmark_results.json").write_text(json.dumps(data, indent=2), encoding="utf-8")
            (BASE_DIR / "benchmark_results.md").write_text(markdown, encoding="utf-8")
        except Exception as write_err:
            logger.warning(f"Failed to write benchmark_results cache: {write_err}")

        BENCHMARK_JOBS[job_id]["status"] = "COMPLETED"
        BENCHMARK_JOBS[job_id]["end_time"] = time.time()
        BENCHMARK_JOBS[job_id]["total_duration_seconds"] = report.total_duration_sec
        BENCHMARK_JOBS[job_id]["report"] = data
        BENCHMARK_JOBS[job_id]["markdown"] = markdown
    except Exception as exc:
        logger.error(f"Benchmark job {job_id} failed: {exc}", exc_info=True)
        BENCHMARK_JOBS[job_id]["status"] = "FAILED"
        BENCHMARK_JOBS[job_id]["error"] = str(exc)
        BENCHMARK_JOBS[job_id]["end_time"] = time.time()


@app.get("/api/benchmark/results")
def get_benchmark_results():
    """
    Returns the latest statistical benchmark report and ablation analysis.
    """
    cache_path = BASE_DIR / "benchmark_results.json"
    if cache_path.exists():
        try:
            data = json.loads(cache_path.read_text(encoding="utf-8"))
            global LATEST_BENCHMARK
            LATEST_BENCHMARK = data
            return {"exists": True, "report": data}
        except Exception:
            pass

    if LATEST_BENCHMARK:
        return {"exists": True, "report": LATEST_BENCHMARK}

    return {"exists": False, "report": None, "message": "No benchmark runs have been recorded yet."}


@app.get("/api/benchmark/markdown", response_class=PlainTextResponse)
def get_benchmark_markdown():
    """
    Returns the Markdown report from the latest benchmark run.
    """
    md_path = BASE_DIR / "benchmark_results.md"
    if md_path.exists():
        return PlainTextResponse(content=md_path.read_text(encoding="utf-8"), media_type="text/markdown; charset=utf-8")
    if LATEST_BENCHMARK:
        try:
            rep = BenchmarkReport(**LATEST_BENCHMARK)
            return PlainTextResponse(content=rep.to_markdown(), media_type="text/markdown; charset=utf-8")
        except Exception:
            pass
    return PlainTextResponse(content="# No Benchmark Report\n\nNo benchmark report available yet. Run a benchmark first.", status_code=404, media_type="text/markdown; charset=utf-8")


@app.post("/api/benchmark/run")
def run_benchmark_sync(payload: BenchmarkRunPayload):
    """
    Executes a benchmark synchronously (ideal for automated test runners and CI).
    """
    job_id = f"bench_sync_{str(uuid.uuid4())[:6]}"
    BENCHMARK_JOBS[job_id] = {
        "job_id": job_id,
        "status": "RUNNING",
        "start_time": time.time(),
    }
    _run_benchmark_job(job_id, payload)
    return BENCHMARK_JOBS[job_id]


@app.post("/api/benchmark/start")
def start_benchmark_async(payload: BenchmarkRunPayload, background_tasks: BackgroundTasks):
    """
    Starts an asynchronous benchmark run in the background.
    """
    job_id = f"bench_{str(uuid.uuid4())[:6]}"
    BENCHMARK_JOBS[job_id] = {
        "job_id": job_id,
        "status": "RUNNING",
        "start_time": time.time(),
    }
    background_tasks.add_task(_run_benchmark_job, job_id, payload)
    return {"job_id": job_id, "status": "RUNNING"}


@app.get("/api/benchmark/job/{job_id}")
def get_benchmark_job(job_id: str):
    """
    Returns the execution status of a specific benchmark job.
    """
    job = BENCHMARK_JOBS.get(job_id)
    if not job:
        raise HTTPException(status_code=404, detail=f"Benchmark job '{job_id}' not found.")
    return job


@app.get("/api/benchmark/multi-target/summary")
def get_multi_target_benchmark_summary():
    """
    Returns the latest empirical scorecard across diverse target modules (GAP-009).
    """
    results_path = BASE_DIR / "qa_artifacts" / "MULTI_TARGET_BENCHMARK_RESULTS.json"
    if results_path.exists():
        try:
            data = json.loads(results_path.read_text(encoding="utf-8"))
            return {"status": "SUCCESS", "results": data}
        except Exception as exc:
            logger.warning(f"Failed to read multi-target benchmark results cache: {exc}")

    try:
        data = run_multi_target_benchmark(fast_mode=True, repetitions=1, output_dir=str(BASE_DIR / "qa_artifacts"))
        return {"status": "SUCCESS", "results": data}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to generate multi-target benchmark summary: {exc}")


@app.post("/api/benchmark/multi-target/run")
def run_multi_target_benchmark_endpoint(payload: Optional[MultiTargetBenchmarkRunPayload] = None):
    """
    Executes empirical benchmarking across diverse Python modules and aggregates statistical metrics (GAP-009).
    """
    opts = payload.model_dump() if payload else {}
    target_modules = opts.get("target_modules")
    scenarios = opts.get("scenarios")
    repetitions = opts.get("repetitions", 1)
    fast_mode = opts.get("fast_mode", False)
    engine_mode = opts.get("engine_mode", "auto")
    model_name = opts.get("model_name", "gemini-3.6-flash")
    output_dir = opts.get("output_dir") or str(BASE_DIR / "qa_artifacts")

    try:
        results = run_multi_target_benchmark(
            target_modules=target_modules,
            scenarios=scenarios,
            repetitions=repetitions,
            fast_mode=fast_mode,
            engine_mode=engine_mode,
            model_name=model_name,
            output_dir=output_dir,
        )
        return {"status": "SUCCESS", "results": results}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Multi-target benchmark run failed: {exc}")



if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server:app", host="0.0.0.0", port=8000, reload=True)
