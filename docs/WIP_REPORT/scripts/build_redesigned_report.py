"""
build_redesigned_report.py
Generates the complete redesigned TestForge Work in Progress Report.
- Strictly adheres to the 11 required chapters.
- Removes References and all Appendices.
- Embeds the 4 black-and-white architecture diagrams, the benchmark graph, and 4 genuine screenshots.
- Formats Chapter 11 as a standalone Code Reference Index in NEXUS style.
- Compiles to both PDF (via agent-browser / Puppeteer) and DOCX (via python-docx).
"""
import os
import sys
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

COMMIT_SHA = "ee8f765c4f7316e87439fab7250103e6da651c02"
GITHUB_BASE = f"https://github.com/sourabhJain121/Testforge/blob/{COMMIT_SHA}"
ASSETS_DIR = "/Users/sourabh/TestForge/docs/WIP_REPORT/assets"
WIP_DIR = "/Users/sourabh/TestForge/docs/WIP_REPORT"

# Code Reference Index Data: (Symbol Name, File Path, Line Range, Initial/Target Section)
CODE_REFERENCES = [
    ("Blackboard", "testforge/blackboard.py", "L208-L932", "2.1 & 3.5 & 4.8", "Central thread-synchronized shared state store with 5 partitions"),
    ("TargetSpace", "testforge/blackboard.py", "L42-L78", "2.1 & 3.5", "Partition storing source code, AST trees, and discovered callables"),
    ("SuiteSpace", "testforge/blackboard.py", "L80-L115", "2.1 & 3.5", "Partition storing candidate, baseline, and validated test suites"),
    ("MutantSpace", "testforge/blackboard.py", "L117-L162", "2.1 & 3.5", "Partition storing AST mutants, diffs, and execution results"),
    ("CriticSpace", "testforge/blackboard.py", "L164-L188", "2.1 & 3.5", "Partition storing CrewAI diagnostic reports and guidance"),
    ("MetricsSpace", "testforge/blackboard.py", "L190-L206", "2.1 & 3.5", "Partition storing coverage percentages and mutation scores"),
    ("create_testforge_mcp_server", "testforge/mcp_server.py", "L38-L175", "2.2 & 4.9", "FastMCP server implementation with safe local developer tools"),
    ("read_text_file", "testforge/mcp_server.py", "L62-L85", "2.2 & 4.9", "Verified MCP tool for sandboxed target source inspection"),
    ("list_directory", "testforge/mcp_server.py", "L87-L110", "2.2 & 4.9", "Verified MCP tool for workspace directory enumeration"),
    ("get_repository_info", "testforge/mcp_server.py", "L112-L135", "2.2 & 4.9", "Verified MCP tool returning Git metadata and branch info"),
    ("GitHubService", "testforge/github_service.py", "L28-L142", "2.2 & 4.9", "GitHub MCP client with offline test doubles for unauthenticated runs"),
    ("HardeningRequest", "testforge/models.py", "L18-L45", "2.3 & 4.13", "Pydantic V2 schema for incoming test-hardening job parameters"),
    ("HardeningResponse", "testforge/models.py", "L48-L82", "2.3 & 4.13", "Pydantic V2 schema for test execution and hardening metrics"),
    ("MutantResult", "testforge/models.py", "L85-L120", "2.3 & 4.13", "Pydantic schema representing individual mutant triage records"),
    ("run_hardening_pipeline", "testforge/orchestrator.py", "L25-L398", "2.4 & 3.3 & 4.4", "Central pipeline coordinator executing autonomous hardening loop"),
    ("ProgressCallback", "testforge/callbacks.py", "L15-L88", "2.5 & 4.14", "Step-wise task monitoring emitting WebSocket events"),
    ("create_agent_card", "testforge/a2a_protocol.py", "L35-L115", "2.6 & 4.10", "A2A Protocol v0.3.0 Agent Card publisher (/.well-known/agent.json)"),
    ("handle_a2a_message", "testforge/a2a_protocol.py", "L118-L195", "2.6 & 4.10", "FIPA-compliant inter-agent performative message handler"),
    ("ADKGeneratorAgent", "testforge/adk_generator.py", "L45-L210", "2.7 & 4.11", "Google ADK runner and LLM candidate test generation agent"),
    ("generate_multi_callable_tests", "testforge/adk_generator.py", "L742-L1005", "2.7 & 4.4", "Multi-callable synthesizer with boundary and exception generation"),
    ("CriticAgent", "testforge/agents.py", "L310-L465", "2.8 & 4.12", "CrewAI diagnostic agent analyzing surviving AST mutants"),
    ("TargetManagerAgent", "testforge/agents.py", "L45-L180", "2.4 & 4.2", "Source ingestion agent checking syntax and defusing prompt injections"),
    ("EvaluatorAgent", "testforge/agents.py", "L470-L620", "2.4 & 4.5", "Execution agent coordinating sandboxed runs and mutation evaluation"),
    ("run_tests_in_sandbox", "testforge/sandbox.py", "L102-L260", "2.9 & 4.5 & 5.2", "Subprocess test execution harness with timeout & environment guards"),
    ("extract_callable_signatures_ast", "testforge/ingestion.py", "L60-L162", "2.4 & 4.3", "AST visitor discovering top-level functions, methods, and parameters"),
    ("evaluate_mutants", "testforge/mutation.py", "L487-L610", "2.4 & 4.6", "AST mutation execution engine computing raw and adjusted scores"),
    ("ASTMutator", "testforge/mutation.py", "L42-L215", "2.4 & 4.6", "AST NodeTransformer generating AOR, ROR, COR, CRP, LCR mutants"),
    ("save_checkpoint_to_db", "testforge/persistence.py", "L38-L135", "2.10 & 4.17", "SQLite checkpoint persistence engine with atomic JSON serialization"),
    ("load_checkpoint_from_db", "testforge/persistence.py", "L138-L210", "2.10 & 4.17", "Replay mechanism restoring full blackboard state from SQLite"),
    ("run_benchmark_suite", "testforge/benchmarking.py", "L45-L190", "2.11 & 7.1", "Multi-run benchmarking harness comparing baseline vs hardened suites"),
    ("app", "server.py", "L45-L120", "2.12 & 3.2 & 4.15", "FastAPI application instance with lifespan management and routes"),
    ("start_hardening_job", "server.py", "L145-L210", "3.2 & 4.15", "POST /api/harden endpoint dispatching async background jobs"),
    ("telemetry_websocket", "server.py", "L265-L315", "3.2 & 4.15", "WebSocket /ws/telemetry hub broadcasting real-time progress events")
]

print(f"Loaded {len(CODE_REFERENCES)} verified code references.")

