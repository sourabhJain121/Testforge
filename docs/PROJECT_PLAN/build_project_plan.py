"""
build_project_plan.py
Generates the TestForge Updated Project Plan document:
1. docs/PROJECT_PLAN/TestForge_Updated_Project_Plan.docx (native DOCX)
2. docs/PROJECT_PLAN/TestForge_Updated_Project_Plan.pdf (compiled via agent-browser)
Target: Exactly 4 pages, perfectly balanced per section.
"""
import os
import sys
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

OUT_DIR = "/Users/sourabh/TestForge/docs/PROJECT_PLAN"
DOCX_PATH = os.path.join(OUT_DIR, "TestForge_Updated_Project_Plan.docx")
HTML_PATH = os.path.join(OUT_DIR, "project_plan_print.html")
PDF_PATH = os.path.join(OUT_DIR, "TestForge_Updated_Project_Plan.pdf")

# ==============================================================================
# 1. HTML GENERATION (FOR PDF)
# ==============================================================================
html_content = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>TestForge — Updated Project Plan</title>
<style>
  @page {
    size: A4 portrait;
    margin: 14mm 14mm 14mm 14mm;
    @top-right {
      content: "TestForge — Updated Project Plan";
      font-family: Arial, Helvetica, sans-serif;
      font-size: 7.5pt;
      color: #64748B;
    }
    @bottom-right {
      content: "Page " counter(page);
      font-family: Arial, Helvetica, sans-serif;
      font-size: 7.5pt;
      color: #64748B;
    }
  }

  body {
    font-family: "Times New Roman", Times, Georgia, serif;
    font-size: 9.3pt;
    line-height: 1.34;
    color: #0F172A;
    margin: 0;
    padding: 0;
    background-color: #FFFFFF;
  }

  /* Document Header */
  .doc-header {
    text-align: center;
    border-bottom: 1.5px solid #1E3A8A;
    padding-bottom: 6px;
    margin-bottom: 12px;
  }
  h1.doc-title {
    font-family: Arial, Helvetica, sans-serif;
    font-size: 15pt;
    font-weight: bold;
    color: #1E3A8A;
    margin: 0 0 2px 0;
    letter-spacing: 0.5px;
    text-transform: uppercase;
  }
  .doc-subtitle {
    font-family: Arial, Helvetica, sans-serif;
    font-size: 9.5pt;
    font-weight: bold;
    color: #334155;
    margin: 0 0 4px 0;
  }
  .doc-meta {
    font-family: Arial, Helvetica, sans-serif;
    font-size: 8pt;
    color: #475569;
    margin: 0;
  }

  /* Headings */
  h1 {
    font-family: Arial, Helvetica, sans-serif;
    font-size: 11pt;
    font-weight: bold;
    color: #1E3A8A;
    border-bottom: 1px solid #CBD5E1;
    padding-bottom: 2px;
    margin-top: 10px;
    margin-bottom: 6px;
    text-transform: uppercase;
    page-break-after: avoid;
  }
  h2 {
    font-family: Arial, Helvetica, sans-serif;
    font-size: 9.3pt;
    font-weight: bold;
    color: #0F172A;
    margin-top: 5px;
    margin-bottom: 2px;
    page-break-after: avoid;
  }

  p {
    margin: 0 0 6px 0;
    text-align: justify;
  }

  ol, ul {
    margin: 0 0 6px 0;
    padding-left: 18px;
  }
  li {
    margin-bottom: 3.5px;
    text-align: justify;
  }

  /* Plan Item */
  .plan-item {
    margin-bottom: 5.5px;
    text-align: justify;
  }
  .plan-item-title {
    font-family: Arial, Helvetica, sans-serif;
    font-weight: bold;
    color: #0F172A;
  }

  /* Academic Tables */
  table.academic-table {
    width: 100%;
    border-collapse: collapse;
    margin: 6px 0 8px 0;
    font-family: Arial, Helvetica, sans-serif;
    font-size: 7.7pt;
    line-height: 1.25;
    page-break-inside: avoid;
  }
  table.academic-table th {
    background-color: #F1F5F9;
    color: #1E3A8A;
    font-weight: bold;
    text-align: left;
    padding: 4px 5px;
    border-top: 1.5px solid #1E3A8A;
    border-bottom: 1.2px solid #1E3A8A;
    border-left: none;
    border-right: none;
  }
  table.academic-table td {
    padding: 3.5px 5px;
    border-bottom: 1px solid #E2E8F0;
    border-top: none;
    border-left: none;
    border-right: none;
    vertical-align: top;
    text-align: left;
  }
  table.academic-table tr:last-child td {
    border-bottom: 1.5px solid #1E3A8A;
  }

  /* Status Badges */
  .badge-completed {
    font-weight: bold;
    color: #047857;
  }
  .badge-partial {
    font-weight: bold;
    color: #B45309;
  }
  .badge-progress {
    font-weight: bold;
    color: #1D4ED8;
  }
  .badge-planned {
    font-weight: bold;
    color: #475569;
  }

  code {
    font-family: "Courier New", Courier, monospace;
    font-size: 8pt;
    background-color: #F1F5F9;
    padding: 0 2px;
    border: 1px solid #CBD5E1;
  }

  .caption-table {
    font-family: Arial, Helvetica, sans-serif;
    font-size: 8pt;
    font-weight: bold;
    color: #0F172A;
    margin-top: 4px;
    margin-bottom: 2px;
    page-break-after: avoid;
  }
</style>
</head>
<body>

<!-- PAGE 1: HEADER & SECTION 1 -->
<div class="doc-header">
  <h1 class="doc-title">TestForge — Updated Project Plan</h1>
  <div class="doc-subtitle">Autonomous AI-Powered Software Test Generation and Hardening Platform</div>
  <div class="doc-meta">
    BML Munjal University &bull; Course: Agentic AI &bull; Repository: https://github.com/sourabhJain121/Testforge &bull; November 2026
  </div>
</div>

<h1>1. Project Plan</h1>
<p>
The TestForge development plan is structured into eleven numbered development activities spanning requirement elicitation, architecture design, intelligent test synthesis, multi-agent orchestration, full-stack implementation, mutation hardening, comprehensive evaluation, deployment, and final academic deliverables.
</p>

<div class="plan-item">
  <span class="plan-item-title">1. Requirement Analysis:</span>
  Identify the functional requirements, academic evaluation criteria, and architectural scope of the TestForge platform. Define operational boundaries for static AST callable extraction, isolated subprocess execution, and mutation-driven hardening.
</div>

<div class="plan-item">
  <span class="plan-item-title">2. System Architecture and Design:</span>
  Design the decoupled 7-layer application architecture, multi-agent coordination workflow, Blackboard shared-state pattern, backend services, communication protocols (FastMCP and A2A), and iterative reflection cycles.
</div>

<div class="plan-item">
  <span class="plan-item-title">3. AST Analysis and Intelligent Test Generation:</span>
  Implement source-code ingestion, AST parsing, callable discovery, intelligent test synthesis, type-driven boundary-value generation, and negative exception handling to guarantee 100% callable coverage across functions and methods.
</div>

<div class="plan-item">
  <span class="plan-item-title">4. Agent Development and Orchestration:</span>
  Implement and integrate specialized agents: TargetManagerAgent (ingestion), ADKGeneratorAgent (Google ADK synthesis), CriticAgent (CrewAI reflection), EvaluatorAgent (sandbox validation), and OrchestratorAgent (workflow and budget control).
</div>

<div class="plan-item">
  <span class="plan-item-title">5. Backend Development:</span>
  Develop the FastAPI asynchronous application, REST endpoints (<code>/api/harden</code>, <code>/api/checkpoints</code>), health check routes (<code>/healthz</code>, <code>/readyz</code>), execution cancellation guards, and WebSocket telemetry broadcaster (<code>/ws/telemetry</code>).
</div>

<div class="plan-item">
  <span class="plan-item-title">6. Frontend Development:</span>
  Develop the TestForge responsive single-page web interface for target source upload, callable selection, hardening configuration, real-time terminal monitoring, mutation kill matrix display, and checkpoint timeline replay.
</div>

<div class="plan-item">
  <span class="plan-item-title">7. Blackboard, Database and Communication:</span>
  Implement thread-safe shared state management with five isolated partitions (TargetSpace, SuiteSpace, MutantSpace, CriticSpace, MetricsSpace), SQLite checkpoint persistence (<code>testforge_checkpoints.db</code>), FastMCP tool execution, and A2A Protocol v0.3.0 discovery.
</div>

<div class="plan-item">
  <span class="plan-item-title">8. Mutation Testing and Security:</span>
  Implement the AST mutation engine with five operators (AOR, ROR, COR, CRP, LCR), ephemeral directory sandboxing with 15s/30s timeout guards, stripped execution environments, mutant triage, and clean-code SHA-256 integrity verification.
</div>

<div class="plan-item">
  <span class="plan-item-title">9. Testing and Evaluation:</span>
  Perform comprehensive multi-tiered verification including unit testing, subsystem integration testing, full regression testing (542 tests), end-to-end browser automation, benchmark evaluation on standard targets, and independent validation.
</div>

<div class="plan-item">
  <span class="plan-item-title">10. Deployment:</span>
  Prepare local single-command launch configurations (<code>./start_testforge.sh</code>), production Docker multi-stage containerization, container orchestration manifests, and deployment runbooks for demonstration environments.
</div>

<div class="plan-item">
  <span class="plan-item-title">11. Documentation and Final Submission:</span>
  Prepare academic technical documentation, updated project plans, viva defense packages, final project reports, presentation slide decks, and live demonstration assets for university academic evaluation.
</div>

<!-- PAGE 2: SECTION 2 -->
<div style="page-break-before: always;"></div>
<h1>2. Progress Against the Plan</h1>
<p>
Project execution has been systematically tracked and independently verified against repository source code, automated test suites, and empirical QA artifacts. Table 1 summarizes current progress across all planned activities.
</p>

<div class="caption-table">Table 1: Project Implementation Progress and Empirical Evidence</div>
<table class="academic-table">
  <thead>
    <tr>
      <th style="width: 5%;">No.</th>
      <th style="width: 25%;">Project Activity</th>
      <th style="width: 15%;">Status</th>
      <th style="width: 55%;">Progress / Empirical Evidence</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td>1</td>
      <td><strong>Requirement Analysis</strong></td>
      <td><span class="badge-completed">Completed</span></td>
      <td>Documented in university acceptance matrices; 11 of 12 academic requirements verified as implemented; functional boundaries and evaluation rubrics established.</td>
    </tr>
    <tr>
      <td>2</td>
      <td><strong>System Architecture &amp; Design</strong></td>
      <td><span class="badge-completed">Completed</span></td>
      <td>7-layer decoupled architecture, multi-agent coordination, and Blackboard pattern implemented in <code>testforge/orchestrator.py</code> and <code>testforge/blackboard.py</code>.</td>
    </tr>
    <tr>
      <td>3</td>
      <td><strong>AST Analysis &amp; Test Generation</strong></td>
      <td><span class="badge-completed">Completed</span></td>
      <td><code>IntelligentASTSynthesizer</code> and AST visitor implemented; 100% callable discovery (10/10 callables) verified on enterprise logistics engine; boundary and exception tests validated.</td>
    </tr>
    <tr>
      <td>4</td>
      <td><strong>Agent Development &amp; Orchestration</strong></td>
      <td><span class="badge-completed">Completed</span></td>
      <td>Google ADK generator, CrewAI critic, EvaluatorAgent, and OrchestratorAgent reflection loop implemented; passes 34 orchestration tests with budget governor.</td>
    </tr>
    <tr>
      <td>5</td>
      <td><strong>Backend Development</strong></td>
      <td><span class="badge-completed">Completed</span></td>
      <td>FastAPI server running on <code>http://127.0.0.1:8000/</code>; REST endpoints, lifecycle hooks, WebSocket telemetry, and <code>/api/harden/cancel</code> guards verified.</td>
    </tr>
    <tr>
      <td>6</td>
      <td><strong>Frontend Development</strong></td>
      <td><span class="badge-completed">Completed</span></td>
      <td>Single-page dashboard in <code>frontend/</code> operational; verified via browser automation for code ingestion, live WebSocket logs, mutation matrix, and checkpoint timeline.</td>
    </tr>
    <tr>
      <td>7</td>
      <td><strong>Blackboard, DB &amp; Communication</strong></td>
      <td><span class="badge-completed">Completed</span></td>
      <td>Blackboard with 5 typed partitions and RLock synchronization verified; SQLite persistence verified with 1,104 saved checkpoints; FastMCP tools and A2A v0.3.0 card active.</td>
    </tr>
    <tr>
      <td>8</td>
      <td><strong>Mutation Testing &amp; Security</strong></td>
      <td><span class="badge-completed">Completed</span></td>
      <td><code>ASTMutator</code> with AOR/ROR/COR/CRP/LCR operators verified; subprocess sandboxing with 15s timeouts verified; clean-code SHA-256 integrity check verified (0 source mutation).</td>
    </tr>
    <tr>
      <td>9</td>
      <td><strong>Testing and Evaluation</strong></td>
      <td><span class="badge-completed">Completed</span></td>
      <td>Full regression suite verified: <strong>542 passed, 0 failed in ~277s</strong> (305 non-breaking deprecation warnings tracked). Benchmark evidence verified:<br>
      &bull; <em>Discount:</em> 11/11 passed, 100% stmt cov (10/10), 17/19 killed, <strong>89.47% raw, 94.44% adj</strong> (94.74% live UI).<br>
      &bull; <em>Logistics:</em> 64/64 passed, 90.15% stmt cov (119/132), 176/258 killed, <strong>68.22% raw, 75.21% adj</strong> across 10/10 callables.</td>
    </tr>
    <tr>
      <td>10</td>
      <td><strong>Deployment</strong></td>
      <td><span class="badge-partial">Partially Completed</span></td>
      <td>Single-command launch (<code>./start_testforge.sh</code>) and Docker multi-stage containerization (<code>Dockerfile</code>) verified. Public-cloud deployment (AWS/GCP/Azure) has not been completed.</td>
    </tr>
    <tr>
      <td>11</td>
      <td><strong>Documentation &amp; Final Submission</strong></td>
      <td><span class="badge-progress">In Progress</span></td>
      <td>Technical WIP Report, Viva preparation package, and Updated Project Plan completed. Final comprehensive report, presentation slide deck, and defense rehearsals remain to be finalized.</td>
    </tr>
  </tbody>
</table>

<!-- PAGE 3: SECTION 3 & SECTION 4 -->
<div style="page-break-before: always;"></div>
<h1>3. Revised Timeline</h1>
<p>
The project timeline has been structured into five chronological development phases based on verified Git commit history, QA artifact timestamps, and remaining academic requirements. Table 2 outlines the revised schedule.
</p>

<div class="caption-table">Table 2: TestForge Revised Development Timeline and Phase Milestones</div>
<table class="academic-table">
  <thead>
    <tr>
      <th style="width: 18%;">Development Phase</th>
      <th style="width: 22%;">Period</th>
      <th style="width: 48%;">Planned Activities / Deliverables</th>
      <th style="width: 12%;">Status</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>Phase 1: Setup &amp; Baseline</strong></td>
      <td>Oct 15 – Oct 25, 2026</td>
      <td>Project requirements definition, development environment setup, baseline test generator, initial mutation baselines (Discount: 5.26%, Logistics: 3.10%), security sandbox, initial callback monitoring.</td>
      <td><span class="badge-completed">Completed</span></td>
    </tr>
    <tr>
      <td><strong>Phase 2: Intelligent Test Generation</strong></td>
      <td>Oct 26 – Oct 30, 2026</td>
      <td><code>IntelligentASTSynthesizer</code> implementation, multi-callable discovery (10/10 callables), boundary-value and negative exception test generation, CrewAI surviving mutant reflection loop, defect fixes.</td>
      <td><span class="badge-completed">Completed</span></td>
    </tr>
    <tr>
      <td><strong>Phase 3: Independent Validation</strong></td>
      <td>Oct 31, 2026</td>
      <td>Independent clean-room benchmark reproduction, test assertion quality verification, mutation-kill validation, suite cryptographic provenance audit (SHA-256 match), full regression execution (542 passed, 0 failed).</td>
      <td><span class="badge-completed">Completed</span></td>
    </tr>
    <tr>
      <td><strong>Phase 4: Final Readiness &amp; Demo</strong></td>
      <td>Oct 31 – Nov 1, 2026</td>
      <td>Frontend workflow verification via browser automation, FastAPI and A2A discovery endpoint validation, Blackboard timeline inspection (1,104 SQLite snapshots), failure scenario testing, Docker packaging verification.</td>
      <td><span class="badge-completed">Completed</span></td>
    </tr>
    <tr>
      <td><strong>Phase 5: Documentation &amp; Submission</strong></td>
      <td>Nov 1, 2026 – Final Evaluation Period</td>
      <td>Academic WIP Report, Updated Project Plan, Viva defense package, final comprehensive project report, slide presentation, and live demonstration rehearsal.</td>
      <td><span class="badge-progress">In Progress</span></td>
    </tr>
  </tbody>
</table>

<h1>4. Remaining Work</h1>
<p>
Based on the current development audit, the following genuinely incomplete activities constitute the remaining project workload prior to final evaluation:
</p>
<ol>
  <li><strong>Targeted Assertion Refinement for Complex Edge Cases:</strong> Extend heuristic assertion generation for edge-case branching logic, complex nested objects, and recursive functions to further raise enterprise mutation scores beyond 75%.</li>
  <li><strong>Evaluation Across Additional Realistic Source Targets:</strong> Test the platform against additional third-party Python modules and multi-file packages to validate callable discovery robustness across larger codebases.</li>
  <li><strong>Packaging Reproducible Benchmark Automation Scripts:</strong> Consolidate isolated benchmark reproduction scripts into a unified CLI command for one-step evaluator verification.</li>
  <li><strong>Public-Cloud Container Deployment:</strong> Configure and verify container hosting on a public cloud provider (e.g., AWS ECS, Google Cloud Run, or Azure App Service) if required for external demonstration.</li>
  <li><strong>Final Project Report Completion:</strong> Finalize the comprehensive academic project report integrating final evaluation feedback and benchmark conclusions.</li>
  <li><strong>Presentation Slide Deck and Demonstration Rehearsal:</strong> Complete the university presentation slide deck and conduct end-to-end rehearsals of the live demonstration workflow for the final viva defense.</li>
</ol>

<!-- PAGE 4: SECTION 5 -->
<div style="page-break-before: always;"></div>
<h1>5. Risks and Mitigation</h1>
<p>
Project execution involves technical, environmental, and evaluation risks. Table 3 outlines the identified risks, their potential impact, and the practical mitigation strategies implemented in TestForge.
</p>

<div class="caption-table">Table 3: Project Technical Risks, Potential Impact, and Mitigation Strategies</div>
<table class="academic-table">
  <thead>
    <tr>
      <th style="width: 25%;">Risk</th>
      <th style="width: 35%;">Potential Impact</th>
      <th style="width: 40%;">Mitigation Strategy</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>Surviving Equivalent Mutants</strong></td>
      <td>Syntactically altered mutants that are semantically identical cannot be killed by any test suite, artificially capping raw mutation scores below theoretical targets.</td>
      <td>Apply AST equivalence analysis and manual review triage to compute and report Adjusted Mutation Scores alongside raw scores, transparently isolating mathematically unkillable mutants.</td>
    </tr>
    <tr>
      <td><strong>LLM Output Non-Determinism</strong></td>
      <td>Generative models may produce variable test assertions or occasionally hallucinate API signatures during dynamic test synthesis.</td>
      <td>Enforce pre-execution AST validation, parameter type constraints from static analysis, deterministic template fallbacks, and isolated sandbox compilation before test adoption.</td>
    </tr>
    <tr>
      <td><strong>Benchmark Diversity Limitations</strong></td>
      <td>Initial benchmark targets (pricing and logistics modules) may not capture all real-world software paradigms such as asynchronous network streams or compiled C-extensions.</td>
      <td>Explicitly scope capabilities to pure Python 3.10+ business logic, while expanding ongoing test evaluation to multi-file packages and diverse functional codebases.</td>
    </tr>
    <tr>
      <td><strong>Model API Latency and Quota Limits</strong></td>
      <td>External LLM API rate limits, transient network outages, or token quotas may delay multi-iteration reflection loops during live demonstrations.</td>
      <td>Implement exponential backoff retries, multi-model fallback hierarchy (Gemini 3.6 Flash primary with Pro fallback), offline test doubles, and deterministic local synthesis modes.</td>
    </tr>
    <tr>
      <td><strong>Subprocess Timeouts on Complex Mutants</strong></td>
      <td>Mutated code containing modified loop boundaries may introduce infinite loops or excessive latency during test execution.</td>
      <td>Enforce strict subprocess execution timeouts (15.0s / 30.0s) with automated <code>SIGKILL</code> termination, marking timed-out mutants as killed without stalling the pipeline.</td>
    </tr>
    <tr>
      <td><strong>Public-Cloud Deployment Discrepancies</strong></td>
      <td>Deploying solely in local/container environments leaves cloud-specific network, storage, or permission issues untested.</td>
      <td>Maintain standardized multi-stage Docker containerization with local container verification, paired with planned early staging deployment prior to final evaluation.</td>
    </tr>
    <tr>
      <td><strong>Benchmark Environment Reproducibility Drift</strong></td>
      <td>Discrepancies in dependency versions, pytest plugins, or OS-level configurations may cause variations in regression runtimes or test passes.</td>
      <td>Maintain pinned dependency specifications (<code>requirements.txt</code>), isolated virtual environments (<code>.venv-release/</code>), cryptographic SHA-256 state hashing, and automated regression logging.</td>
    </tr>
  </tbody>
</table>

</body>
</html>
"""

with open(HTML_PATH, "w", encoding="utf-8") as f:
    f.write(html_content)
print(f"Written HTML plan to {HTML_PATH}")

# ==============================================================================
# 2. DOCX GENERATION
# ==============================================================================
doc = docx.Document()

# Page Setup: A4 Portrait with 0.6 inch margins
for section in doc.sections:
    section.page_width = Inches(8.27)
    section.page_height = Inches(11.69)
    section.top_margin = Inches(0.6)
    section.bottom_margin = Inches(0.6)
    section.left_margin = Inches(0.6)
    section.right_margin = Inches(0.6)

# Styles
styles = doc.styles
normal = styles['Normal']
normal.font.name = 'Times New Roman'
normal.font.size = Pt(9.5)
normal.font.color.rgb = RGBColor(0x0F, 0x17, 0x2A)
normal.paragraph_format.line_spacing = 1.18
normal.paragraph_format.space_after = Pt(3)

def add_h1(text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    run.font.name = 'Arial'
    run.font.size = Pt(11)
    run.font.bold = True
    run.font.color.rgb = RGBColor(0x1E, 0x3A, 0x8A)
    # Add bottom border
    pBdr = parse_xml(f'<w:pBdr {nsdecls("w")}><w:bottom w:val="single" w:sz="6" w:space="2" w:color="CBD5E1"/></w:pBdr>')
    p._p.get_or_add_pPr().append(pBdr)

def set_cell_margins(cell, top=60, bottom=60, left=80, right=80):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('w:top', top), ('w:bottom', bottom), ('w:left', left), ('w:right', right)]:
        node = OxmlElement(m)
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)

def set_cell_shading(cell, color_hex):
    shading_elm = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{color_hex}"/>')
    cell._tc.get_or_add_tcPr().append(shading_elm)

def set_table_borders(table, color="E2E8F0", sz="4", val="single"):
    tblPr = table._tbl.tblPr
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        f'  <w:top w:val="{val}" w:sz="10" w:space="0" w:color="1E3A8A"/>'
        f'  <w:bottom w:val="{val}" w:sz="10" w:space="0" w:color="1E3A8A"/>'
        f'  <w:left w:val="none"/>'
        f'  <w:right w:val="none"/>'
        f'  <w:insideH w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'  <w:insideV w:val="none"/>'
        f'</w:tblBorders>'
    )
    tblPr.append(borders)

print("Building DOCX Project Plan...")

# Header
p_title = doc.add_paragraph()
p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
p_title.paragraph_format.space_before = Pt(0)
p_title.paragraph_format.space_after = Pt(2)
run_title = p_title.add_run("TESTFORGE — UPDATED PROJECT PLAN")
run_title.font.name = 'Arial'
run_title.font.size = Pt(15)
run_title.font.bold = True
run_title.font.color.rgb = RGBColor(0x1E, 0x3A, 0x8A)

p_sub = doc.add_paragraph()
p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
p_sub.paragraph_format.space_before = Pt(0)
p_sub.paragraph_format.space_after = Pt(2)
run_sub = p_sub.add_run("Autonomous AI-Powered Software Test Generation and Hardening Platform")
run_sub.font.name = 'Arial'
run_sub.font.size = Pt(9.5)
run_sub.font.bold = True
run_sub.font.color.rgb = RGBColor(0x33, 0x41, 0x55)

p_meta = doc.add_paragraph()
p_meta.alignment = WD_ALIGN_PARAGRAPH.CENTER
p_meta.paragraph_format.space_before = Pt(0)
p_meta.paragraph_format.space_after = Pt(8)
run_meta = p_meta.add_run("BML Munjal University • Course: Agentic AI • Repository: https://github.com/sourabhJain121/Testforge • November 2026")
run_meta.font.name = 'Arial'
run_meta.font.size = Pt(8)
run_meta.font.color.rgb = RGBColor(0x47, 0x55, 0x69)
# Bottom border on header
pBdr_hdr = parse_xml(f'<w:pBdr {nsdecls("w")}><w:bottom w:val="single" w:sz="10" w:space="4" w:color="1E3A8A"/></w:pBdr>')
p_meta._p.get_or_add_pPr().append(pBdr_hdr)

# SECTION 1: PROJECT PLAN
add_h1("1. Project Plan")
p_p1 = doc.add_paragraph()
p_p1.add_run("The TestForge development plan is structured into eleven numbered development activities spanning requirement elicitation, architecture design, intelligent test synthesis, multi-agent orchestration, full-stack implementation, mutation hardening, comprehensive evaluation, deployment, and final academic deliverables.")

plan_items = [
    ("1. Requirement Analysis:", " Identify the functional requirements, academic evaluation criteria, and architectural scope of the TestForge platform. Define operational boundaries for static AST callable extraction, isolated subprocess execution, and mutation-driven hardening."),
    ("2. System Architecture and Design:", " Design the decoupled 7-layer application architecture, multi-agent coordination workflow, Blackboard shared-state pattern, backend services, communication protocols (FastMCP and A2A), and iterative reflection cycles."),
    ("3. AST Analysis and Intelligent Test Generation:", " Implement source-code ingestion, AST parsing, callable discovery, intelligent test synthesis, type-driven boundary-value generation, and negative exception handling to guarantee 100% callable coverage across functions and methods."),
    ("4. Agent Development and Orchestration:", " Implement and integrate specialized agents: TargetManagerAgent (ingestion), ADKGeneratorAgent (Google ADK synthesis), CriticAgent (CrewAI reflection), EvaluatorAgent (sandbox validation), and OrchestratorAgent (workflow and budget control)."),
    ("5. Backend Development:", " Develop the FastAPI asynchronous application, REST endpoints (/api/harden, /api/checkpoints), health check routes (/healthz, /readyz), execution cancellation guards, and WebSocket telemetry broadcaster (/ws/telemetry)."),
    ("6. Frontend Development:", " Develop the TestForge responsive single-page web interface for target source upload, callable selection, hardening configuration, real-time terminal monitoring, mutation kill matrix display, and checkpoint timeline replay."),
    ("7. Blackboard, Database and Communication:", " Implement thread-safe shared state management with five isolated partitions (TargetSpace, SuiteSpace, MutantSpace, CriticSpace, MetricsSpace), SQLite checkpoint persistence (testforge_checkpoints.db), FastMCP tool execution, and A2A Protocol v0.3.0 discovery."),
    ("8. Mutation Testing and Security:", " Implement the AST mutation engine with five operators (AOR, ROR, COR, CRP, LCR), ephemeral directory sandboxing with 15s/30s timeout guards, stripped execution environments, mutant triage, and clean-code SHA-256 integrity verification."),
    ("9. Testing and Evaluation:", " Perform comprehensive multi-tiered verification including unit testing, subsystem integration testing, full regression testing (542 tests), end-to-end browser automation, benchmark evaluation on standard targets, and independent validation."),
    ("10. Deployment:", " Prepare local single-command launch configurations (./start_testforge.sh), production Docker multi-stage containerization, container orchestration manifests, and deployment runbooks for demonstration environments."),
    ("11. Documentation and Final Submission:", " Prepare academic technical documentation, updated project plans, viva defense packages, final project reports, presentation slide decks, and live demonstration assets for university academic evaluation.")
]

for title, desc in plan_items:
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(2.5)
    r_title = p.add_run(title)
    r_title.font.name = 'Arial'
    r_title.font.size = Pt(9)
    r_title.font.bold = True
    p.add_run(desc)

# PAGE BREAK TO SECTION 2
doc.add_page_break()

# SECTION 2: PROGRESS AGAINST THE PLAN
add_h1("2. Progress Against the Plan")
doc.add_paragraph("Project execution has been systematically tracked and independently verified against repository source code, automated test suites, and empirical QA artifacts. Table 1 summarizes current progress across all planned activities.")

p_c1 = doc.add_paragraph()
p_c1.paragraph_format.space_before = Pt(4)
p_c1.paragraph_format.space_after = Pt(1)
r_c1 = p_c1.add_run("Table 1: Project Implementation Progress and Empirical Evidence")
r_c1.font.name = 'Arial'
r_c1.font.size = Pt(8.5)
r_c1.font.bold = True

t1_headers = ["No.", "Project Activity", "Status", "Progress / Empirical Evidence"]
t1_widths = [Inches(0.4), Inches(1.8), Inches(1.2), Inches(3.6)]
t1_rows = [
    ("1", "Requirement Analysis", "Completed", "Documented in university acceptance matrices; 11 of 12 academic requirements verified as implemented; functional boundaries and evaluation rubrics established."),
    ("2", "System Architecture & Design", "Completed", "7-layer decoupled architecture, multi-agent coordination, and Blackboard pattern implemented in testforge/orchestrator.py and testforge/blackboard.py."),
    ("3", "AST Analysis & Test Generation", "Completed", "IntelligentASTSynthesizer and AST visitor implemented; 100% callable discovery (10/10 callables) verified on enterprise logistics engine; boundary and exception tests validated."),
    ("4", "Agent Development & Orchestration", "Completed", "Google ADK generator, CrewAI critic, EvaluatorAgent, and OrchestratorAgent reflection loop implemented; passes 34 orchestration tests with budget governor."),
    ("5", "Backend Development", "Completed", "FastAPI server running on http://127.0.0.1:8000/; REST endpoints, lifecycle hooks, WebSocket telemetry, and /api/harden/cancel guards verified."),
    ("6", "Frontend Development", "Completed", "Single-page dashboard in frontend/ operational; verified via browser automation for code ingestion, live WebSocket logs, mutation matrix, and checkpoint timeline."),
    ("7", "Blackboard, DB & Communication", "Completed", "Blackboard with 5 typed partitions and RLock synchronization verified; SQLite persistence verified with 1,104 saved checkpoints; FastMCP tools and A2A v0.3.0 card active."),
    ("8", "Mutation Testing & Security", "Completed", "ASTMutator with AOR/ROR/COR/CRP/LCR operators verified; subprocess sandboxing with 15s timeouts verified; clean-code SHA-256 integrity check verified (0 source mutation)."),
    ("9", "Testing and Evaluation", "Completed", "Full regression suite verified: 542 passed, 0 failed in ~277s (305 non-breaking deprecation warnings tracked). Benchmark evidence verified:\n• Discount: 11/11 passed, 100% stmt cov (10/10), 17/19 killed, 89.47% raw, 94.44% adj (94.74% live UI).\n• Logistics: 64/64 passed, 90.15% stmt cov (119/132), 176/258 killed, 68.22% raw, 75.21% adj across 10/10 callables."),
    ("10", "Deployment", "Partially Completed", "Single-command launch (./start_testforge.sh) and Docker multi-stage containerization (Dockerfile) verified. Public-cloud deployment (AWS/GCP/Azure) has not been completed."),
    ("11", "Documentation & Final Submission", "In Progress", "Technical WIP Report, Viva preparation package, and Updated Project Plan completed. Final comprehensive report, presentation slide deck, and defense rehearsals remain to be finalized.")
]

table1 = doc.add_table(rows=len(t1_rows) + 1, cols=4)
table1.alignment = WD_TABLE_ALIGNMENT.CENTER
set_table_borders(table1)

for c_idx, h in enumerate(t1_headers):
    cell = table1.cell(0, c_idx)
    cell.width = t1_widths[c_idx]
    set_cell_margins(cell, 35, 35, 45, 45)
    set_cell_shading(cell, "F1F5F9")
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(0)
    run = p.add_run(h)
    run.font.name = 'Arial'
    run.font.size = Pt(7.5)
    run.font.bold = True
    run.font.color.rgb = RGBColor(0x1E, 0x3A, 0x8A)

for r_idx, (num, act, stat, ev) in enumerate(t1_rows):
    row_cells = table1.rows[r_idx + 1].cells
    for c_idx, val in enumerate([num, act, stat, ev]):
        cell = row_cells[c_idx]
        cell.width = t1_widths[c_idx]
        set_cell_margins(cell, 25, 25, 45, 45)
        p = cell.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = 1.05
        run = p.add_run(val)
        run.font.name = 'Arial'
        run.font.size = Pt(7.2)
        if c_idx == 0:
            run.font.bold = True
        elif c_idx == 1:
            run.font.bold = True
        elif c_idx == 2:
            run.font.bold = True
            if val == "Completed":
                run.font.color.rgb = RGBColor(0x04, 0x78, 0x57)
            elif "Partial" in val:
                run.font.color.rgb = RGBColor(0xB4, 0x53, 0x09)
            elif "Progress" in val:
                run.font.color.rgb = RGBColor(0x1D, 0x4E, 0xD8)

# PAGE BREAK TO SECTION 3 & 4
doc.add_page_break()

# SECTION 3: REVISED TIMELINE
add_h1("3. Revised Timeline")
doc.add_paragraph("The project timeline has been structured into five chronological development phases based on verified Git commit history, QA artifact timestamps, and remaining academic requirements. Table 2 outlines the revised schedule.")

p_c2 = doc.add_paragraph()
p_c2.paragraph_format.space_before = Pt(4)
p_c2.paragraph_format.space_after = Pt(1)
r_c2 = p_c2.add_run("Table 2: TestForge Revised Development Timeline and Phase Milestones")
r_c2.font.name = 'Arial'
r_c2.font.size = Pt(8.5)
r_c2.font.bold = True

t2_headers = ["Development Phase", "Period", "Planned Activities / Deliverables", "Status"]
t2_widths = [Inches(1.5), Inches(1.4), Inches(3.2), Inches(0.9)]
t2_rows = [
    ("Phase 1: Setup & Baseline", "Oct 15 – Oct 25, 2026", "Project requirements definition, development environment setup, baseline test generator, initial mutation baselines (Discount: 5.26%, Logistics: 3.10%), security sandbox, initial callback monitoring.", "Completed"),
    ("Phase 2: Intelligent Test Generation", "Oct 26 – Oct 30, 2026", "IntelligentASTSynthesizer implementation, multi-callable discovery (10/10 callables), boundary-value and negative exception test generation, CrewAI surviving mutant reflection loop, defect fixes.", "Completed"),
    ("Phase 3: Independent Validation", "Oct 31, 2026", "Independent clean-room benchmark reproduction, test assertion quality verification, mutation-kill validation, suite cryptographic provenance audit (SHA-256 match), full regression execution (542 passed, 0 failed).", "Completed"),
    ("Phase 4: Final Readiness & Demo", "Oct 31 – Nov 1, 2026", "Frontend workflow verification via browser automation, FastAPI and A2A discovery endpoint validation, Blackboard timeline inspection (1,104 SQLite snapshots), failure scenario testing, Docker packaging verification.", "Completed"),
    ("Phase 5: Documentation & Submission", "Nov 1, 2026 – Final Evaluation Period", "Academic WIP Report, Updated Project Plan, Viva defense package, final comprehensive project report, slide presentation, and live demonstration rehearsal.", "In Progress")
]

table2 = doc.add_table(rows=len(t2_rows) + 1, cols=4)
table2.alignment = WD_TABLE_ALIGNMENT.CENTER
set_table_borders(table2)

for c_idx, h in enumerate(t2_headers):
    cell = table2.cell(0, c_idx)
    cell.width = t2_widths[c_idx]
    set_cell_margins(cell, 35, 35, 45, 45)
    set_cell_shading(cell, "F1F5F9")
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(0)
    run = p.add_run(h)
    run.font.name = 'Arial'
    run.font.size = Pt(7.5)
    run.font.bold = True
    run.font.color.rgb = RGBColor(0x1E, 0x3A, 0x8A)

for r_idx, (phase, period, acts, stat) in enumerate(t2_rows):
    row_cells = table2.rows[r_idx + 1].cells
    for c_idx, val in enumerate([phase, period, acts, stat]):
        cell = row_cells[c_idx]
        cell.width = t2_widths[c_idx]
        set_cell_margins(cell, 25, 25, 45, 45)
        p = cell.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = 1.05
        run = p.add_run(val)
        run.font.name = 'Arial'
        run.font.size = Pt(7.2)
        if c_idx == 0:
            run.font.bold = True
        elif c_idx == 3:
            run.font.bold = True
            if val == "Completed":
                run.font.color.rgb = RGBColor(0x04, 0x78, 0x57)
            elif "Progress" in val:
                run.font.color.rgb = RGBColor(0x1D, 0x4E, 0xD8)

# SECTION 4: REMAINING WORK
add_h1("4. Remaining Work")
doc.add_paragraph("Based on the current development audit, the following genuinely incomplete activities constitute the remaining project workload prior to final evaluation:")

rem_items = [
    ("1. Targeted Assertion Refinement for Complex Edge Cases: ", "Extend heuristic assertion generation for edge-case branching logic, complex nested objects, and recursive functions to further raise enterprise mutation scores beyond 75%."),
    ("2. Evaluation Across Additional Realistic Source Targets: ", "Test the platform against additional third-party Python modules and multi-file packages to validate callable discovery robustness across larger codebases."),
    ("3. Packaging Reproducible Benchmark Automation Scripts: ", "Consolidate isolated benchmark reproduction scripts into a unified CLI command for one-step evaluator verification."),
    ("4. Public-Cloud Container Deployment: ", "Configure and verify container hosting on a public cloud provider (e.g., AWS ECS, Google Cloud Run, or Azure App Service) if required for external demonstration."),
    ("5. Final Project Report Completion: ", "Finalize the comprehensive academic project report integrating final evaluation feedback and benchmark conclusions."),
    ("6. Presentation Slide Deck and Demonstration Rehearsal: ", "Complete the university presentation slide deck and conduct end-to-end rehearsals of the live demonstration workflow for the final viva defense.")
]

for num_title, desc in rem_items:
    p = doc.add_paragraph()
    p.paragraph_format.space_after = Pt(2.5)
    r_t = p.add_run(num_title)
    r_t.font.name = 'Arial'
    r_t.font.size = Pt(9)
    r_t.font.bold = True
    p.add_run(desc)

# PAGE BREAK TO SECTION 5
doc.add_page_break()

# SECTION 5: RISKS AND MITIGATION
add_h1("5. Risks and Mitigation")
doc.add_paragraph("Project execution involves technical, environmental, and evaluation risks. Table 3 outlines the identified risks, their potential impact, and the practical mitigation strategies implemented in TestForge.")

p_c3 = doc.add_paragraph()
p_c3.paragraph_format.space_before = Pt(4)
p_c3.paragraph_format.space_after = Pt(1)
r_c3 = p_c3.add_run("Table 3: Project Technical Risks, Potential Impact, and Mitigation Strategies")
r_c3.font.name = 'Arial'
r_c3.font.size = Pt(8.5)
r_c3.font.bold = True

t3_headers = ["Risk", "Potential Impact", "Mitigation Strategy"]
t3_widths = [Inches(1.8), Inches(2.5), Inches(2.7)]
t3_rows = [
    ("Surviving Equivalent Mutants",
     "Syntactically altered mutants that are semantically identical cannot be killed by any test suite, artificially capping raw mutation scores below theoretical targets.",
     "Apply AST equivalence analysis and manual review triage to compute and report Adjusted Mutation Scores alongside raw scores, transparently isolating mathematically unkillable mutants."),
    
    ("LLM Output Non-Determinism",
     "Generative models may produce variable test assertions or occasionally hallucinate API signatures during dynamic test synthesis.",
     "Enforce pre-execution AST validation, parameter type constraints from static analysis, deterministic template fallbacks, and isolated sandbox compilation before test adoption."),
    
    ("Benchmark Diversity Limitations",
     "Initial benchmark targets (pricing and logistics modules) may not capture all real-world software paradigms such as asynchronous network streams or compiled C-extensions.",
     "Explicitly scope capabilities to pure Python 3.10+ business logic, while expanding ongoing test evaluation to multi-file packages and diverse functional codebases."),
    
    ("Model API Latency and Quota Limits",
     "External LLM API rate limits, transient network outages, or token quotas may delay multi-iteration reflection loops during live demonstrations.",
     "Implement exponential backoff retries, multi-model fallback hierarchy (Gemini 3.6 Flash primary with Pro fallback), offline test doubles, and deterministic local synthesis modes."),
    
    ("Subprocess Timeouts on Complex Mutants",
     "Mutated code containing modified loop boundaries may introduce infinite loops or excessive latency during test execution.",
     "Enforce strict subprocess execution timeouts (15.0s / 30.0s) with automated SIGKILL termination, marking timed-out mutants as killed without stalling the pipeline."),
    
    ("Public-Cloud Deployment Discrepancies",
     "Deploying solely in local/container environments leaves cloud-specific network, storage, or permission issues untested.",
     "Maintain standardized multi-stage Docker containerization with local container verification, paired with planned early staging deployment prior to final evaluation."),
    
    ("Benchmark Environment Reproducibility Drift",
     "Discrepancies in dependency versions, pytest plugins, or OS-level configurations may cause variations in regression runtimes or test passes.",
     "Maintain pinned dependency specifications (requirements.txt), isolated virtual environments (.venv-release/), cryptographic SHA-256 state hashing, and automated regression logging.")
]

table3 = doc.add_table(rows=len(t3_rows) + 1, cols=3)
table3.alignment = WD_TABLE_ALIGNMENT.CENTER
set_table_borders(table3)

for c_idx, h in enumerate(t3_headers):
    cell = table3.cell(0, c_idx)
    cell.width = t3_widths[c_idx]
    set_cell_margins(cell, 35, 35, 45, 45)
    set_cell_shading(cell, "F1F5F9")
    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(0)
    run = p.add_run(h)
    run.font.name = 'Arial'
    run.font.size = Pt(7.5)
    run.font.bold = True
    run.font.color.rgb = RGBColor(0x1E, 0x3A, 0x8A)

for r_idx, (r_risk, r_imp, r_mit) in enumerate(t3_rows):
    row_cells = table3.rows[r_idx + 1].cells
    for c_idx, val in enumerate([r_risk, r_imp, r_mit]):
        cell = row_cells[c_idx]
        cell.width = t3_widths[c_idx]
        set_cell_margins(cell, 25, 25, 45, 45)
        p = cell.paragraphs[0]
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = 1.05
        run = p.add_run(val)
        run.font.name = 'Arial'
        run.font.size = Pt(7.2)
        if c_idx == 0:
            run.font.bold = True

doc.save(DOCX_PATH)
print(f"Saved DOCX plan to {DOCX_PATH}")
