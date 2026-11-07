"""
build_coverage_slide.py
Builds the single-slide Project Coverage presentation for TestForge:
1. TestForge_Project_Coverage.pptx (16:9 widescreen, dark theme)
2. project_coverage_slide.html (for PDF compilation via agent-browser)
3. TestForge_Project_Coverage.pdf
"""
import os
import sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

OUT_DIR = "/Users/sourabh/TestForge/docs/PROJECT_COVERAGE"
os.makedirs(OUT_DIR, exist_ok=True)
PPTX_PATH = os.path.join(OUT_DIR, "TestForge_Project_Coverage.pptx")
HTML_PATH = os.path.join(OUT_DIR, "project_coverage_slide.html")
PDF_PATH = os.path.join(OUT_DIR, "TestForge_Project_Coverage.pdf")

# ==============================================================================
# DATA DEFINITIONS (All 11 Criteria)
# ==============================================================================
CRITERIA_DATA = [
    {
        "no": "1",
        "title": "Context Sharing & State Updates",
        "demand": "Intermediate output from one agent feeds into another; state used for sharing context; messaging architectures considered; Blackboard architecture mandatory.",
        "impl": "testforge/blackboard.py:Blackboard manages 5 typed partitions (TargetSpace, SuiteSpace, MutantSpace, CriticSpace, MetricsSpace) with threading.RLock(). Target AST feeds Generator -> Suite feeds Sandbox Evaluator -> Mutant diffs feed Critic -> Critic directives feed Refinement. SQLite persistence (testforge_checkpoints.db) stores 1,104 atomic snapshots. Messaging architectures evaluated (Blackboard pub/sub vs A2A broker). Verified in tests/test_blackboard.py (18) and tests/test_blackboard_persistence.py (22).",
        "status": "COMPLETE"
    },
    {
        "no": "2",
        "title": "Tool Integration using MCP",
        "demand": "At least two external or custom tools must be used (e.g. web search API, database lookup, file parser, calculator).",
        "impl": "FastMCP server (testforge/mcp_server.py) exposes 3 verified local tools: read_text_file (custom file parser with path validation), list_directory, and get_repository_info. GitHub MCP client (testforge/github_service.py) provides repository search and file fetching with deterministic offline test doubles when token is unset. Verified in tests/test_mcp.py (22), tests/test_mcp_network_security.py (12), and tests/test_orchestration_mcp.py (16).",
        "status": "COMPLETE"
    },
    {
        "no": "3",
        "title": "Structured Output using Pydantic",
        "demand": "Final output must be generated in a structured form such as Markdown, Table or JSON.",
        "impl": "Strict Pydantic V2 models across all subsystems (testforge/models.py, a2a.py, adk_engine.py): HardeningRequest, HardeningResponse, MutantResult, SynthesizedSuiteResult. Final outputs generated deterministically as JSON (benchmark_results.json, API payloads), GitHub-flavored Markdown (benchmark_results.md, test summaries), and SQLite relational table schema with JSON state blobs. Verified in tests/test_pydantic_models.py (14) and tests/test_contract_schemas.py (16).",
        "status": "COMPLETE"
    },
    {
        "no": "4",
        "title": "Suitable Agentic Design Patterns",
        "demand": "Implement suitable and relevant agentic design patterns. Evaluate them against other agentic patterns.",
        "impl": "Multi-agent cognitive decomposition (testforge/orchestrator.py): TargetManager (ingestion), Generator (synthesis), Evaluator (sandbox execution), and Critic (adversarial reflection). Implements multi-turn reflection loop (1-3 iterations) guided by surviving mutants. Evaluated against linear single-prompt generation: Baseline achieved 5.26% on Discount and 3.10% on Logistics; agentic reflection achieved 94.44% and 75.21% adjusted mutation scores. Verified in tests/test_agentic_pipeline.py (16).",
        "status": "COMPLETE"
    },
    {
        "no": "5",
        "title": "Task Monitoring & Logging (Callbacks)",
        "demand": "Track intermediate outputs, execution flows and errors for transparency and debugging.",
        "impl": "testforge/callbacks.py:CallbackRegistry manages subscriptions across 14 typed lifecycle event types (STAGE_STARTED, MUTANT_EVALUATED, ERROR, SECURITY_REFUSAL, etc.). testforge/logger.py:TraceLogger records append-only structured JSONL event records (testforge_trace.jsonl, 101 MB) with microsecond timestamps and credential redaction. WebSocket hub (/ws/telemetry) broadcasts live pipeline events. Verified in tests/test_callbacks.py (16) and tests/test_observability.py (14).",
        "status": "COMPLETE"
    },
    {
        "no": "6",
        "title": "Agent-to-Agent Communication (A2A)",
        "demand": "Use A2A protocol for interoperability (e.g. one agent defined using ADK and another using CrewAI).",
        "impl": "A2A Protocol v0.3.0 implemented in testforge/a2a.py and testforge/a2a_protocol.py. Agent Card published at /.well-known/agent.json. In-process A2ABroker coordinates FIPA-compliant JSON-RPC performatives (REQUEST, INFORM, AGREE) bridging Google ADK Generator agent with CrewAI Critic agent. Verified in tests/test_a2a.py (16), tests/test_a2a_protocol.py (15), and tests/test_a2a_card_ui_and_endpoint.py (5). Active HTTP 200 endpoint response verified.",
        "status": "COMPLETE"
    },
    {
        "no": "7",
        "title": "Mandatory Agentic Frameworks",
        "demand": "Both CrewAI and Google ADK MUST be used. Do not use another agentic framework.",
        "impl": "Google ADK implemented in testforge/adk_generator.py and testforge/adk_engine.py using LlmAgent, Runner, InMemorySessionService, and ADKModelBridge for structured candidate test synthesis. CrewAI implemented in testforge/crew_critic.py using crewai.Agent, Task, Crew, and custom CrewAILlmAdapter for adversarial surviving-mutant critique. Zero third-party frameworks used. Verified in tests/test_adk_generator.py (15) and tests/test_crew_critic.py (12).",
        "status": "COMPLETE"
    },
    {
        "no": "8",
        "title": "Security Guardrails",
        "demand": "Validation of agent/tool outputs; callback validation; user prompt parsing for toxic/abusive language; prompt-injection protection; prompt variations (ReAct vs few-shot).",
        "impl": "AST safety visitor (testforge/security.py) blocks os.system, subprocess, socket, eval, exec. Prompt-injection defense (testforge/prompt_guard.py) uses XML delimiters and defuses injections in comments/docstrings (10/10 tests passed). Toxic/abusive language filtering verified (INJ_TOXIC_ABUSIVE rule in tests/test_security.py). Output/callback validation enforced. Gaps: ReAct vs. few-shot prompt architecture comparison and persona variations were not formally benchmarked.",
        "status": "PARTIAL"
    },
    {
        "no": "9",
        "title": "Observability, Auditability & Provenance",
        "demand": "Implement a suitable observability mechanism for tracing, auditability and provenance.",
        "impl": "Microsecond-timestamped JSONL execution tracing (TraceLogger). SQLite persistence (testforge_checkpoints.db) storing 1,104 atomic state snapshots with replay engine (load_checkpoint_from_db). End-to-end cryptographic SHA-256 provenance chain matches hashes across Ingestion (source_sha), Generation (candidate_suite_hash), Validation (validated_suite_hash), and Export (exported_suite_hash). Verified in Phase 3 clean-room audit (eaa41e0b... / c3e17c4d...) and tests/test_observability.py (14).",
        "status": "COMPLETE"
    },
    {
        "no": "10",
        "title": "End-to-End Performance Evaluation",
        "demand": "Evaluate performance across multiple runs; include running-time and cost estimates; evaluate variations in prompts, architecture and content/personas.",
        "impl": "testforge/benchmarking.py:BenchmarkRunner executes multi-run trials (5 repetitions) with statistical aggregation (mean, median, IQR, stddev); hardware duration measurement; token and USD cost estimation based on published Gemini pricing models (benchmark_results.json, benchmark_results.md). Evaluated 3 architectural ablation strategies (Baseline vs Zero-Shot vs Reflection). Gaps: Prompt variations (ReAct vs few-shot) and diverse persona variations were not evaluated.",
        "status": "PARTIAL"
    },
    {
        "no": "11",
        "title": "Cloud Deployment",
        "demand": "Deploy the project on a cloud platform.",
        "impl": "Local execution verified on port 8000 via ./start_testforge.sh. Production multi-stage Dockerfile (python:3.13-slim, non-root user UID 10001) and docker-compose.yml verified locally with passing health probes (tests/test_deployment.py, 10/10 passed). Gaps: Live deployment to a public cloud hyperscaler (AWS ECS, Google Cloud Run, or Azure App Service) has not been performed; public cloud hosting remains planned.",
        "status": "PENDING"
    }
]

# Status counts
cnt_complete = sum(1 for c in CRITERIA_DATA if c["status"] == "COMPLETE")
cnt_partial = sum(1 for c in CRITERIA_DATA if c["status"] == "PARTIAL")
cnt_pending = sum(1 for c in CRITERIA_DATA if c["status"] == "PENDING")

print(f"Status Summary: COMPLETE={cnt_complete}, PARTIAL={cnt_partial}, PENDING={cnt_pending}")

# ==============================================================================
# 2. GENERATE PPTX (python-pptx)
# ==============================================================================
prs = Presentation()
prs.slide_width = Inches(13.333)
prs.slide_height = Inches(7.5)

# Use blank slide layout (index 6)
blank_layout = prs.slide_layouts[6]
slide = prs.slides.add_slide(blank_layout)

# Background shape (Deep Navy/Charcoal #0F172A)
bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
bg.fill.solid()
bg.fill.fore_color.rgb = RGBColor(0x0F, 0x17, 0x2A)  # #0F172A
bg.line.color.rgb = RGBColor(0x0F, 0x17, 0x2A)

# Header Title Box
header_box = slide.shapes.add_textbox(Inches(0.4), Inches(0.25), Inches(12.533), Inches(0.85))
tf = header_box.text_frame
tf.word_wrap = True
tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

p1 = tf.paragraphs[0]
p1.text = "TESTFORGE  |  PROJECT COVERAGE"
p1.font.name = "Arial"
p1.font.size = Pt(17)
p1.font.bold = True
p1.font.color.rgb = RGBColor(0xF8, 0xFA, 0xFC)  # White

p2 = tf.add_paragraph()
r_sub = p2.add_run()
r_sub.text = "Evaluation Criteria vs Actual Implementation Status (Till Date)  "
r_sub.font.name = "Arial"
r_sub.font.size = Pt(10.5)
r_sub.font.bold = True
r_sub.font.color.rgb = RGBColor(0x38, 0xBD, 0xF8)  # Sky blue accent

r_meta = p2.add_run()
r_meta.text = "•  BML Munjal University  |  Agentic AI  |  Verified Git Commit: ee8f765  |  542 Tests Passed (0 Failed)"
r_meta.font.name = "Arial"
r_meta.font.size = Pt(8.5)
r_meta.font.color.rgb = RGBColor(0x94, 0xA3, 0xB8)  # Slate light grey

# Table Dimensions
# Available height: 7.5 - 1.15 (top) - 0.70 (bottom) = 5.65 in
rows_cnt = len(CRITERIA_DATA) + 1  # 12 rows
cols_cnt = 4
top_pos = Inches(1.18)
left_pos = Inches(0.4)
width_pos = Inches(12.533)
height_pos = Inches(5.45)

table_shape = slide.shapes.add_table(rows_cnt, cols_cnt, left_pos, top_pos, width_pos, height_pos)
table = table_shape.table

# Set Column Widths
table.columns[0].width = Inches(0.45)  # No.
table.columns[1].width = Inches(3.20)  # Criteria / Demand
table.columns[2].width = Inches(7.583) # Implementation & Evidence
table.columns[3].width = Inches(1.30)  # Status

# Format Header Row
headers = ["No.", "Evaluation Criteria / Mandatory Demand", "Actual Implementation & Evidence in TestForge Repository", "Status"]
for col_idx, h_text in enumerate(headers):
    cell = table.cell(0, col_idx)
    cell.fill.solid()
    cell.fill.fore_color.rgb = RGBColor(0x1E, 0x29, 0x3B)  # Dark slate header #1E293B
    p = cell.text_frame.paragraphs[0]
    p.text = h_text
    p.font.name = "Arial"
    p.font.size = Pt(8.5)
    p.font.bold = True
    p.font.color.rgb = RGBColor(0x38, 0xBD, 0xF8) if col_idx != 3 else RGBColor(0xF8, 0xFA, 0xFC)
    if col_idx in [0, 3]:
        p.alignment = PP_ALIGN.CENTER
    cell.text_frame.margin_left = Inches(0.06)
    cell.text_frame.margin_right = Inches(0.06)
    cell.text_frame.margin_top = Inches(0.04)
    cell.text_frame.margin_bottom = Inches(0.04)

# Format Data Rows
for row_idx, item in enumerate(CRITERIA_DATA):
    r_num = row_idx + 1
    # Zebra striping: alternate row backgrounds
    row_bg = RGBColor(0x0F, 0x17, 0x2A) if row_idx % 2 == 0 else RGBColor(0x15, 0x1F, 0x32)
    
    # Cell 0: No.
    c0 = table.cell(r_num, 0)
    c0.fill.solid()
    c0.fill.fore_color.rgb = row_bg
    p0 = c0.text_frame.paragraphs[0]
    p0.text = item["no"]
    p0.font.name = "Arial"
    p0.font.size = Pt(8)
    p0.font.bold = True
    p0.font.color.rgb = RGBColor(0x94, 0xA3, 0xB8)
    p0.alignment = PP_ALIGN.CENTER
    
    # Cell 1: Criteria & Demand
    c1 = table.cell(r_num, 1)
    c1.fill.solid()
    c1.fill.fore_color.rgb = row_bg
    tf1 = c1.text_frame
    tf1.word_wrap = True
    p1_title = tf1.paragraphs[0]
    p1_title.text = item["title"]
    p1_title.font.name = "Arial"
    p1_title.font.size = Pt(8)
    p1_title.font.bold = True
    p1_title.font.color.rgb = RGBColor(0xF8, 0xFA, 0xFC)
    
    p1_dem = tf1.add_paragraph()
    p1_dem.text = item["demand"]
    p1_dem.font.name = "Arial"
    p1_dem.font.size = Pt(6.8)
    p1_dem.font.color.rgb = RGBColor(0x94, 0xA3, 0xB8)
    
    # Cell 2: Implementation & Evidence
    c2 = table.cell(r_num, 2)
    c2.fill.solid()
    c2.fill.fore_color.rgb = row_bg
    tf2 = c2.text_frame
    tf2.word_wrap = True
    p2_impl = tf2.paragraphs[0]
    p2_impl.text = item["impl"]
    p2_impl.font.name = "Arial"
    p2_impl.font.size = Pt(6.8)
    p2_impl.font.color.rgb = RGBColor(0xCB, 0xD5, 0xE1)  # Soft slate light grey
    
    # Cell 3: Status Badge
    c3 = table.cell(r_num, 3)
    c3.fill.solid()
    c3.fill.fore_color.rgb = row_bg
    p3 = c3.text_frame.paragraphs[0]
    p3.text = item["status"]
    p3.font.name = "Arial"
    p3.font.size = Pt(8)
    p3.font.bold = True
    p3.alignment = PP_ALIGN.CENTER
    
    if item["status"] == "COMPLETE":
        p3.font.color.rgb = RGBColor(0x10, 0xB9, 0x81)  # Emerald green #10B981
    elif item["status"] == "PARTIAL":
        p3.font.color.rgb = RGBColor(0xF5, 0x9E, 0x0B)  # Amber #F59E0B
    else:
        p3.font.color.rgb = RGBColor(0xEF, 0x44, 0x44)  # Muted red #EF4444

    # Padding
    for c in [c0, c1, c2, c3]:
        c.text_frame.margin_left = Inches(0.06)
        c.text_frame.margin_right = Inches(0.06)
        c.text_frame.margin_top = Inches(0.03)
        c.text_frame.margin_bottom = Inches(0.03)

# Footer Box
footer_box = slide.shapes.add_textbox(Inches(0.4), Inches(6.72), Inches(12.533), Inches(0.65))
tff = footer_box.text_frame
tff.word_wrap = True
tff.margin_left = tff.margin_top = tff.margin_right = tff.margin_bottom = 0

pf1 = tff.paragraphs[0]
r_tot = pf1.add_run()
r_tot.text = f"OVERALL PROJECT EVALUATION STATUS (11 CRITERIA):   "
r_tot.font.name = "Arial"
r_tot.font.size = Pt(9)
r_tot.font.bold = True
r_tot.font.color.rgb = RGBColor(0xF8, 0xFA, 0xFC)

r_comp = pf1.add_run()
r_comp.text = f"COMPLETE: {cnt_complete}   "
r_comp.font.name = "Arial"
r_comp.font.size = Pt(9)
r_comp.font.bold = True
r_comp.font.color.rgb = RGBColor(0x10, 0xB9, 0x81)  # Green

r_part = pf1.add_run()
r_part.text = f"PARTIAL: {cnt_partial}   "
r_part.font.name = "Arial"
r_part.font.size = Pt(9)
r_part.font.bold = True
r_part.font.color.rgb = RGBColor(0xF5, 0x9E, 0x0B)  # Amber

r_pend = pf1.add_run()
r_pend.text = f"PENDING: {cnt_pending}   "
r_pend.font.name = "Arial"
r_pend.font.size = Pt(9)
r_pend.font.bold = True
r_pend.font.color.rgb = RGBColor(0xEF, 0x44, 0x44)  # Red

r_div = pf1.add_run()
r_div.text = "|   Core Agentic Pipeline: 100% Operational (Full Regression: 542 passed, 0 failed)"
r_div.font.name = "Arial"
r_div.font.size = Pt(8.5)
r_div.font.color.rgb = RGBColor(0x94, 0xA3, 0xB8)

pf2 = tff.add_paragraph()
r_rem = pf2.add_run()
r_rem.text = "Key Remaining Work Before Final Evaluation: "
r_rem.font.name = "Arial"
r_rem.font.size = Pt(8)
r_rem.font.bold = True
r_rem.font.color.rgb = RGBColor(0x38, 0xBD, 0xF8)

r_rem_desc = pf2.add_run()
r_rem_desc.text = "Public-cloud hyperscaler deployment (AWS/GCP/Azure) and formal comparative prompt variation study (ReAct vs Few-Shot prompt architectures)."
r_rem_desc.font.name = "Arial"
r_rem_desc.font.size = Pt(8)
r_rem_desc.font.color.rgb = RGBColor(0xCB, 0xD5, 0xE1)

prs.save(PPTX_PATH)
print(f"Generated PPTX at {PPTX_PATH}")

# ==============================================================================
# 3. GENERATE HTML (FOR PIXEL-PERFECT PDF COMPILATION)
# ==============================================================================
html_rows = []
for idx, item in enumerate(CRITERIA_DATA):
    bg_color = "#0F172A" if idx % 2 == 0 else "#151F32"
    status_cls = f"badge-{item['status'].lower()}"
    html_rows.append(f"""
    <tr style="background-color: {bg_color};">
      <td class="col-no">{item['no']}</td>
      <td class="col-criteria">
        <div class="criteria-title">{item['title']}</div>
        <div class="criteria-demand">{item['demand']}</div>
      </td>
      <td class="col-impl">{item['impl']}</td>
      <td class="col-status"><span class="badge {status_cls}">{item['status']}</span></td>
    </tr>
    """)

html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>TESTFORGE | PROJECT COVERAGE</title>
<style>
  @page {{
    size: 16in 9in;
    margin: 0;
  }}
  * {{
    box-sizing: border-box;
  }}
  body {{
    margin: 0;
    padding: 24px 36px 20px 36px;
    background-color: #0F172A;
    font-family: Arial, Helvetica, sans-serif;
    color: #F8FAFC;
    width: 16in;
    height: 9in;
    overflow: hidden;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
  }}
  /* Header */
  .header {{
    display: flex;
    justify-content: space-between;
    align-items: flex-end;
    border-bottom: 2px solid #1E293B;
    padding-bottom: 8px;
    margin-bottom: 8px;
  }}
  .title-group {{
    display: flex;
    flex-direction: column;
  }}
  .main-title {{
    font-size: 20pt;
    font-weight: bold;
    letter-spacing: 0.5px;
    color: #F8FAFC;
  }}
  .sub-title {{
    font-size: 11pt;
    font-weight: bold;
    color: #38BDF8;
    margin-top: 2px;
  }}
  .meta-info {{
    font-size: 9pt;
    color: #94A3B8;
    text-align: right;
    line-height: 1.4;
  }}
  .meta-info strong {{
    color: #F8FAFC;
  }}
  
  /* Table */
  table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 8.5pt;
    line-height: 1.25;
    table-layout: fixed;
  }}
  th {{
    background-color: #1E293B;
    color: #38BDF8;
    font-weight: bold;
    font-size: 9.5pt;
    padding: 6px 8px;
    text-align: left;
    border-top: 1.5px solid #38BDF8;
    border-bottom: 1.5px solid #38BDF8;
  }}
  th.th-center, td.col-no, td.col-status {{
    text-align: center;
  }}
  td {{
    padding: 4.5px 8px;
    border-bottom: 1px solid #1E293B;
    vertical-align: top;
  }}
  .col-no {{
    width: 40px;
    font-weight: bold;
    color: #94A3B8;
  }}
  .col-criteria {{
    width: 320px;
  }}
  .criteria-title {{
    font-weight: bold;
    color: #F8FAFC;
    font-size: 8.8pt;
    margin-bottom: 1.5px;
  }}
  .criteria-demand {{
    font-size: 7.2pt;
    color: #94A3B8;
    line-height: 1.2;
  }}
  .col-impl {{
    font-size: 7.4pt;
    color: #CBD5E1;
    line-height: 1.28;
  }}
  .col-status {{
    width: 120px;
    vertical-align: middle;
  }}
  
  /* Status Badges */
  .badge {{
    display: inline-block;
    padding: 3px 8px;
    font-size: 8.5pt;
    font-weight: bold;
    border-radius: 3px;
    letter-spacing: 0.5px;
  }}
  .badge-complete {{
    background-color: #064E3B;
    color: #10B981;
    border: 1px solid #059669;
  }}
  .badge-partial {{
    background-color: #78350F;
    color: #F59E0B;
    border: 1px solid #D97706;
  }}
  .badge-pending {{
    background-color: #7F1D1D;
    color: #EF4444;
    border: 1px solid #DC2626;
  }}
  
  /* Footer */
  .footer {{
    border-top: 2px solid #1E293B;
    padding-top: 8px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }}
  .footer-summary {{
    font-size: 9.5pt;
    font-weight: bold;
  }}
  .stat-badge {{
    padding: 2px 7px;
    border-radius: 3px;
    margin: 0 4px;
    font-size: 9pt;
  }}
  .stat-comp {{
    background-color: #064E3B;
    color: #10B981;
  }}
  .stat-part {{
    background-color: #78350F;
    color: #F59E0B;
  }}
  .stat-pend {{
    background-color: #7F1D1D;
    color: #EF4444;
  }}
  .footer-remaining {{
    font-size: 8.5pt;
    color: #94A3B8;
    text-align: right;
  }}
  .footer-remaining strong {{
    color: #38BDF8;
  }}
</style>
</head>
<body>

  <!-- Top Header -->
  <div class="header">
    <div class="title-group">
      <div class="main-title">TESTFORGE &nbsp;|&nbsp; PROJECT COVERAGE</div>
      <div class="sub-title">Evaluation Criteria vs Actual Implementation Status (Till Date)</div>
    </div>
    <div class="meta-info">
      <strong>BML Munjal University &bull; Agentic AI</strong><br>
      Repository: <code>github.com/sourabhJain121/Testforge</code> &bull; Commit: <code>ee8f765</code> &bull; <strong>542 Tests Passed (0 Failed)</strong>
    </div>
  </div>

  <!-- Main Table -->
  <table>
    <thead>
      <tr>
        <th class="col-no th-center">#</th>
        <th class="col-criteria">Evaluation Criteria / Mandatory Demand</th>
        <th class="col-impl">Actual Implementation &amp; Evidence in TestForge Repository</th>
        <th class="col-status th-center">Status</th>
      </tr>
    </thead>
    <tbody>
      {''.join(html_rows)}
    </tbody>
  </table>

  <!-- Footer Summary -->
  <div class="footer">
    <div class="footer-summary">
      OVERALL STATUS:
      <span class="stat-badge stat-comp">COMPLETE: {cnt_complete}</span>
      <span class="stat-badge stat-part">PARTIAL: {cnt_partial}</span>
      <span class="stat-badge stat-pend">PENDING: {cnt_pending}</span>
      &nbsp;&nbsp;<span style="font-weight:normal; color:#94A3B8; font-size:8.5pt;">(Total 11 Evaluation Criteria &bull; 100% Core Pipeline Operational)</span>
    </div>
    <div class="footer-remaining">
      <strong>Key Remaining Work:</strong> Public-cloud deployment (AWS/GCP/Azure) and formal prompt variation study (ReAct vs Few-Shot).
    </div>
  </div>

</body>
</html>
"""

with open(HTML_PATH, "w", encoding="utf-8") as f:
    f.write(html_content)
print(f"Generated HTML template at {HTML_PATH}")

