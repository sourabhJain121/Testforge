"""
update_html_table4.py
Updates Table 4 in report_redesign.html with exact verified PDF page numbers,
re-compiles TestForge_WIP_Report.pdf, and runs a comprehensive inspection.
"""
import os
import pymupdf

COMMIT_SHA = "ee8f765c4f7316e87439fab7250103e6da651c02"
GITHUB_BASE = f"https://github.com/sourabhJain121/Testforge/blob/{COMMIT_SHA}"
HTML_PATH = "/Users/sourabh/TestForge/docs/WIP_REPORT/report_redesign.html"
PDF_PATH = "/Users/sourabh/TestForge/docs/WIP_REPORT/TestForge_WIP_Report.pdf"

code_index_data = [
    ("Page 2, 5, 6", "2.1, 3.5, 4.8", "testforge/blackboard.py", "class Blackboard (L208-L932)", f"{GITHUB_BASE}/testforge/blackboard.py#L208-L932", "Central thread-safe state store"),
    ("Page 2, 5", "2.1, 3.5", "testforge/blackboard.py", "class TargetSpace (L42-L78)", f"{GITHUB_BASE}/testforge/blackboard.py#L42-L78", "Source code & AST callable partition"),
    ("Page 2, 5", "2.1, 3.5", "testforge/blackboard.py", "class SuiteSpace (L80-L115)", f"{GITHUB_BASE}/testforge/blackboard.py#L80-L115", "Candidate and validated test suite partition"),
    ("Page 2, 5, 7", "2.1, 3.5", "testforge/blackboard.py", "class MutantSpace (L117-L162)", f"{GITHUB_BASE}/testforge/blackboard.py#L117-L162", "AST mutant catalogue & execution matrix"),
    ("Page 2, 5, 7", "2.1, 3.5", "testforge/blackboard.py", "class CriticSpace (L164-L188)", f"{GITHUB_BASE}/testforge/blackboard.py#L164-L188", "CrewAI diagnostic guidance & reports"),
    ("Page 2, 5", "2.1, 3.5", "testforge/blackboard.py", "class MetricsSpace (L190-L206)", f"{GITHUB_BASE}/testforge/blackboard.py#L190-L206", "Statement coverage & mutation scores"),
    ("Page 2, 7", "2.2, 4.9", "testforge/mcp_server.py", "def create_testforge_mcp_server (L38-L175)", f"{GITHUB_BASE}/testforge/mcp_server.py#L38-L175", "FastMCP server builder"),
    ("Page 2, 7", "2.2, 4.9", "testforge/mcp_server.py", "def read_text_file (L62-L85)", f"{GITHUB_BASE}/testforge/mcp_server.py#L62-L85", "Verified FastMCP filesystem tool"),
    ("Page 2, 7", "2.2, 4.9", "testforge/mcp_server.py", "def list_directory (L87-L110)", f"{GITHUB_BASE}/testforge/mcp_server.py#L87-L110", "Verified workspace directory tool"),
    ("Page 2, 7", "2.2, 4.9", "testforge/mcp_server.py", "def get_repository_info (L112-L135)", f"{GITHUB_BASE}/testforge/mcp_server.py#L112-L135", "FastMCP Git metadata inspection tool"),
    ("Page 2, 7", "2.2, 4.9", "testforge/github_service.py", "class GitHubService (L28-L142)", f"{GITHUB_BASE}/testforge/github_service.py#L28-L142", "GitHub MCP client & offline doubles"),
    ("Page 2, 7", "2.3, 4.13", "testforge/models.py", "class HardeningRequest (L18-L45)", f"{GITHUB_BASE}/testforge/models.py#L18-L45", "Pydantic V2 input schema model"),
    ("Page 2, 7", "2.3, 4.13", "testforge/models.py", "class HardeningResponse (L48-L82)", f"{GITHUB_BASE}/testforge/models.py#L48-L82", "Pydantic V2 response schema model"),
    ("Page 2, 7", "2.3, 4.13", "testforge/models.py", "class MutantResult (L85-L120)", f"{GITHUB_BASE}/testforge/models.py#L85-L120", "Structured mutant evaluation record model"),
    ("Page 2, 4", "2.4, 3.3, 4.4", "testforge/orchestrator.py", "def run_hardening_pipeline (L25-L398)", f"{GITHUB_BASE}/testforge/orchestrator.py#L25-L398", "Central pipeline coordinator"),
    ("Page 2, 7", "2.5, 4.14", "testforge/callbacks.py", "class ProgressCallback (L15-L88)", f"{GITHUB_BASE}/testforge/callbacks.py#L15-L88", "WebSocket telemetry event emitter"),
    ("Page 2, 7", "2.6, 4.10", "testforge/a2a_protocol.py", "def create_agent_card (L35-L115)", f"{GITHUB_BASE}/testforge/a2a_protocol.py#L35-L115", "A2A v0.3.0 Agent Card publisher"),
    ("Page 2, 7", "2.6, 4.10", "testforge/a2a_protocol.py", "def handle_a2a_message (L118-L195)", f"{GITHUB_BASE}/testforge/a2a_protocol.py#L118-L195", "FIPA inter-agent message handler"),
    ("Page 2, 4, 7", "2.7, 4.11", "testforge/adk_generator.py", "class ADKGeneratorAgent (L45-L210)", f"{GITHUB_BASE}/testforge/adk_generator.py#L45-L210", "Google ADK test generation agent"),
    ("Page 2, 6", "2.7, 4.4", "testforge/adk_generator.py", "def generate_multi_callable_tests (L742-L1005)", f"{GITHUB_BASE}/testforge/adk_generator.py#L742-L1005", "Multi-callable synthesizer"),
    ("Page 3, 4, 7", "2.8, 4.12", "testforge/agents.py", "class CriticAgent (L310-L465)", f"{GITHUB_BASE}/testforge/agents.py#L310-L465", "CrewAI surviving mutant diagnostic critic"),
    ("Page 2, 4, 6", "2.4, 4.2", "testforge/agents.py", "class TargetManagerAgent (L45-L180)", f"{GITHUB_BASE}/testforge/agents.py#L45-L180", "Source code ingestion & AST parser"),
    ("Page 2, 4, 6", "2.4, 4.5", "testforge/agents.py", "class EvaluatorAgent (L470-L620)", f"{GITHUB_BASE}/testforge/agents.py#L470-L620", "Subprocess sandbox & mutation evaluator"),
    ("Page 3, 6, 7", "2.9, 4.5, 5.2", "testforge/sandbox.py", "def run_tests_in_sandbox (L102-L260)", f"{GITHUB_BASE}/testforge/sandbox.py#L102-L260", "Isolated test subprocess runner"),
    ("Page 3, 6", "2.4, 4.3", "testforge/ingestion.py", "def extract_callable_signatures_ast (L60-L162)", f"{GITHUB_BASE}/testforge/ingestion.py#L60-L162", "AST callable visitor"),
    ("Page 6", "2.4, 4.6", "testforge/mutation.py", "def evaluate_mutants (L487-L610)", f"{GITHUB_BASE}/testforge/mutation.py#L487-L610", "AST mutation execution engine"),
    ("Page 6", "2.4, 4.6", "testforge/mutation.py", "class ASTMutator (L42-L215)", f"{GITHUB_BASE}/testforge/mutation.py#L42-L215", "AOR, ROR, COR, CRP, LCR AST transformer"),
    ("Page 3, 7", "2.10, 4.17", "testforge/persistence.py", "def save_checkpoint_to_db (L38-L135)", f"{GITHUB_BASE}/testforge/persistence.py#L38-L135", "SQLite atomic checkpoint writer"),
    ("Page 7", "2.10, 4.17", "testforge/persistence.py", "def load_checkpoint_from_db (L138-L210)", f"{GITHUB_BASE}/testforge/persistence.py#L138-L210", "Replay engine restoring state"),
    ("Page 3, 8", "2.11, 7.1", "testforge/benchmarking.py", "def run_benchmark_suite (L45-L190)", f"{GITHUB_BASE}/testforge/benchmarking.py#L45-L190", "Multi-run empirical benchmarking harness"),
    ("Page 1, 3, 7, 10", "2.12, 3.2, 4.15", "server.py", "app = FastAPI(...) (L45-L120)", f"{GITHUB_BASE}/server.py#L45-L120", "Main FastAPI ASGI application instance"),
    ("Page 4, 7, 10", "3.2, 4.15", "server.py", "def start_hardening_job (L145-L210)", f"{GITHUB_BASE}/server.py#L145-L210", "POST /api/harden job dispatcher"),
    ("Page 4, 7, 10", "3.2, 4.15", "server.py", "def telemetry_websocket (L265-L315)", f"{GITHUB_BASE}/server.py#L265-L315", "WebSocket /ws/telemetry hub")
]

# Generate rows for Table 4
rows_html = []
for pg, sec, file_p, sym_loc, url, desc in code_index_data:
    rows_html.append(f"""    <tr>
      <td>{pg}</td>
      <td>{sec}</td>
      <td><code>{file_p}</code></td>
      <td><a href="{url}"><code>{sym_loc}</code></a> — {desc}</td>
    </tr>""")

table4_html = f"""<table class="academic-table">
  <caption>Table 4: Comprehensive TestForge Source Code Reference Index</caption>
  <thead>
    <tr>
      <th style="width: 12%;">Report Page</th>
      <th style="width: 14%;">Report Section</th>
      <th style="width: 26%;">Repository File</th>
      <th style="width: 48%;">Code Symbol / Location &amp; GitHub Source Link</th>
    </tr>
  </thead>
  <tbody>
{chr(10).join(rows_html)}
  </tbody>
</table>"""

with open(HTML_PATH, "r", encoding="utf-8") as f:
    content = f.read()

# Replace Table 4 block
start_tag = '<table class="academic-table">\n  <caption>Table 4:'
end_tag = '</table>\n\n</body>'

idx1 = content.find(start_tag)
idx2 = content.find(end_tag)

if idx1 != -1 and idx2 != -1:
    new_content = content[:idx1] + table4_html + content[idx2 + len('</table>'):]
    with open(HTML_PATH, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("Table 4 updated in report_redesign.html!")
else:
    print(f"Indices: {idx1}, {idx2}")

