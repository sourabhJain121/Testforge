import os
import sys
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

DOCX_OUT = "docs/WIP_REPORT/TestForge_WIP_Report.docx"
COMMIT_SHA = "ee8f765c4f7316e87439fab7250103e6da651c02"
GITHUB_BASE = f"https://github.com/sourabhJain121/Testforge/blob/{COMMIT_SHA}"

doc = docx.Document()

# Page Margins: 0.8 inches for academic presentation
sections = doc.sections
for section in sections:
    section.top_margin = Inches(0.8)
    section.bottom_margin = Inches(0.8)
    section.left_margin = Inches(0.8)
    section.right_margin = Inches(0.8)

# Configure Styles
styles = doc.styles
normal_style = styles['Normal']
normal_style.font.name = 'Times New Roman'
normal_style.font.size = Pt(10)
normal_style.font.color.rgb = RGBColor(0x11, 0x11, 0x11)
normal_style.paragraph_format.line_spacing = 1.15
normal_style.paragraph_format.space_after = Pt(4)

def add_p_hyperlink(p, url, text):
    part = p.part
    r_id = part.relate_to(url, docx.opc.constants.RELATIONSHIP_TYPE.HYPERLINK, is_external=True)
    hyperlink = parse_xml(f'<w:hyperlink {nsdecls("w", "r")} r:id="{r_id}"/>')
    r = parse_xml(f'<w:r {nsdecls("w")}><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:color w:val="0044BB"/><w:u w:val="single"/></w:rPr><w:t>{text}</w:t></w:r>')
    hyperlink.append(r)
    p._p.append(hyperlink)

def add_h1(text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(12)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    run.font.name = 'Arial'
    run.font.size = Pt(13)
    run.font.bold = True
    run.font.color.rgb = RGBColor(0x00, 0x00, 0x00)
    pBdr = parse_xml(f'<w:pBdr {nsdecls("w")}><w:bottom w:val="single" w:sz="12" w:space="2" w:color="000000"/></w:pBdr>')
    p._p.get_or_add_pPr().append(pBdr)
    return p

def add_h2(text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(9)
    p.paragraph_format.space_after = Pt(3)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    run.font.name = 'Arial'
    run.font.size = Pt(11)
    run.font.bold = True
    run.font.color.rgb = RGBColor(0x22, 0x22, 0x22)
    return p

def add_h3(text):
    p = doc.add_paragraph()
    p.paragraph_format.space_before = Pt(7)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.keep_with_next = True
    run = p.add_run(text)
    run.font.name = 'Arial'
    run.font.size = Pt(10)
    run.font.bold = True
    run.font.color.rgb = RGBColor(0x44, 0x44, 0x44)
    return p

def style_cell(cell, fill_hex=None, bold=False, font_size=8.5, align=WD_ALIGN_PARAGRAPH.LEFT):
    tcPr = cell._tc.get_or_add_tcPr()
    if fill_hex:
        shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
        tcPr.append(shd)
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('w:top', 100), ('w:bottom', 100), ('w:left', 140), ('w:right', 140)]:
        node = OxmlElement(m)
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)
    for p in cell.paragraphs:
        p.alignment = align
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = 1.05
        for r in p.runs:
            r.font.name = 'Arial'
            r.font.size = Pt(font_size)
            r.font.bold = bold

def set_tbl_borders(table):
    tblPr = table._tbl.tblPr
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        f'  <w:top w:val="single" w:sz="8" w:space="0" w:color="000000"/>'
        f'  <w:bottom w:val="single" w:sz="8" w:space="0" w:color="000000"/>'
        f'  <w:left w:val="none"/>'
        f'  <w:right w:val="none"/>'
        f'  <w:insideH w:val="single" w:sz="4" w:space="0" w:color="D5D5D5"/>'
        f'  <w:insideV w:val="none"/>'
        f'</w:tblBorders>'
    )
    tblPr.append(borders)

def add_figure(img_path, caption_text, width=Inches(6.2)):
    if os.path.exists(img_path):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_before = Pt(6)
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.keep_with_next = True
        run = p.add_run()
        run.add_picture(img_path, width=width)
        
        cp = doc.add_paragraph()
        cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cp.paragraph_format.space_before = Pt(2)
        cp.paragraph_format.space_after = Pt(8)
        run_c = cp.add_run(caption_text)
        run_c.font.name = 'Arial'
        run_c.font.size = Pt(8.5)
        run_c.font.bold = True
        run_c.font.color.rgb = RGBColor(0x33, 0x33, 0x33)

# ---------------------------------------------------------------------------
# DOCUMENT TITLE & METADATA
# ---------------------------------------------------------------------------
p_title = doc.add_paragraph()
p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
p_title.paragraph_format.space_before = Pt(0)
p_title.paragraph_format.space_after = Pt(2)
r_title = p_title.add_run("TestForge: Autonomous Agentic Unit Test Hardening via Multi-Callable Synthesis and AST Mutation Analysis")
r_title.font.name = 'Arial'
r_title.font.size = Pt(16)
r_title.font.bold = True

p_sub = doc.add_paragraph()
p_sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
p_sub.paragraph_format.space_after = Pt(8)
r_sub = p_sub.add_run("Academic Work in Progress (WIP) Technical Report — Autonomous Agentic AI")
r_sub.font.name = 'Arial'
r_sub.font.size = Pt(11)
r_sub.font.bold = True
r_sub.font.color.rgb = RGBColor(0x44, 0x44, 0x44)

# Metadata Table
meta_tbl = doc.add_table(rows=2, cols=3)
meta_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
set_tbl_borders(meta_tbl)
meta_data = [
    [("Student Author:", " Sourabh Jain"), ("Course:", " Autonomous Agentic AI"), ("Runtime:", " Python 3.13 / ARM64")],
    [("Verified Commit:", f" {COMMIT_SHA[:12]}"), ("Repository:", " github.com/sourabhJain121/Testforge"), ("Pytest Suite:", " 542 Passed, 0 Failed, 305 Warn")]
]
for row_idx, row in enumerate(meta_data):
    for col_idx, (k, v) in enumerate(row):
        c = meta_tbl.cell(row_idx, col_idx)
        c.text = ""
        p = c.paragraphs[0]
        rk = p.add_run(k)
        rk.font.name = 'Arial'; rk.font.size = Pt(8); rk.font.bold = True
        rv = p.add_run(v)
        rv.font.name = 'Arial'; rv.font.size = Pt(8)
        style_cell(c, fill_hex="F6F6F8", font_size=8)

doc.add_paragraph()

# ---------------------------------------------------------------------------
# CHAPTER 1: PROJECT SUMMARY
# ---------------------------------------------------------------------------
add_h1("1. Project Summary")

add_h2("1.1 Project Overview")
p = doc.add_paragraph(
    "TestForge is an autonomous, decentralized multi-agent system designed to overcome the critical phenomenon of "
    "illusory test coverage in software engineering. Modern test generators frequently synthesize shallow test suites "
    "that achieve high statement coverage by executing nominal code paths while verifying virtually no business logic "
    "(e.g., relying on generic assertions such as assert res is not None). TestForge integrates Abstract Syntax Tree (AST) "
    "comparison analysis, the Model Context Protocol (MCP), the Agent-to-Agent (A2A) discovery protocol, and an adversarial "
    "generator-critic feedback loop to synthesize rigorous, value-aware unit tests guided by syntactic mutation analysis."
)

add_h2("1.2 Background and Motivation")
doc.add_paragraph(
    "Statement coverage measures line execution, not defect verification. In production systems, software faults frequently "
    "manifest at boundary conditions, relational swaps (< vs. <=), off-by-one index calculations, and inverted boolean guards. "
    "In traditional test suites, code may achieve 100% statement coverage while killing under 10% of syntactic mutants. TestForge "
    "bridges this verification gap by coupling generative AI with formal mutation testing, using surviving mutants as active "
    "adversarial gradients to drive iterative test refinement."
)

add_h2("1.3 Problem Statement")
doc.add_paragraph(
    "Existing automated unit-test generation tools suffer from three fundamental defects: (1) Callable Scope Blindness: "
    "generators frequently identify only top-level functions while skipping class methods, nested closures, and secondary "
    "module callables; (2) Assertion Vacuity: generated tests assert nominal execution rather than mathematical or semantic "
    "output correctness; and (3) Execution Provenance Loss: test generation pipelines lack tamper-evident cryptographic tracing, "
    "creating risks of hallucinated coverage and fabricated benchmark scores."
)

add_h2("1.4 Project Objectives")
doc.add_paragraph(
    "The core engineering objectives of TestForge are:\n"
    "• Complete Callable Discovery: Reliably discover, parse, and generate tests for 100% of discovered public callables and "
    "class methods without executing arbitrary target code.\n"
    "• Value-Aware Assertion Synthesis: Inspect runtime return types to synthesize strict semantic assertions "
    "(e.g., assert res == pytest.approx(expected)) rather than nullity checks.\n"
    "• Boundary & Negative Case Generation: Extract boundary values (-1, 0, 1) and exception conditions from AST comparison nodes "
    "to test error paths.\n"
    "• Adversarial Feedback Loop: Leverage CrewAI and Google ADK agent roles to diagnose surviving mutant diffs and guide iterative refinement.\n"
    "• Verifiable Cryptographic Provenance: Maintain byte-level SHA-256 suite consistency across generation, sandbox execution, "
    "blackboard storage, and export."
)

add_h2("1.5 Proposed Solution")
doc.add_paragraph(
    "TestForge couples an in-memory and SQLite-persisted thread-safe Blackboard Architecture with specialized cognitive agents: "
    "(1) TargetManagerAgent for AST parsing and SSRF-safe ingestion; (2) IntelligentASTSynthesizer for 4-tier test generation; "
    "(3) ASTMutator applying 9 mutation operator families; (4) ParallelSandboxRunner for isolated subprocess pytest execution; "
    "and (5) CrewAICriticAgent for adversarial surviving-mutant critique. The entire lifecycle is orchestrated by "
    "TestForgeOrchestrator in a closed feedback loop."
)

add_h2("1.6 Project Scope")
doc.add_paragraph(
    "The current system targets Python 3.13/3.14 source codebases. The scope encompasses local FastMCP standardized tool servers, "
    "A2A Protocol v0.3.0 inter-agent messaging, SQLite WAL persistence, process-isolated test sandboxing, and an asynchronous "
    "FastAPI web cockpit. Public cloud hyperscaler hosting and multi-language compilation are reserved for subsequent release phases."
)

add_h2("1.7 Current Project Status")
doc.add_paragraph(
    "TestForge has completed Phase 4 live readiness and Phase 5 VIVA defense preparation. The full regression suite reports "
    "542 passed and 0 failed across 48 test modules in 277 seconds. Mutation testing benchmarks on discount.py achieved an "
    "89.47% raw score (94.44% adjusted), and enterprise uploaded_logistics_engine.py achieved a 68.22% raw score (75.21% adjusted) "
    "across 258 mutants with 100% callable coverage."
)

# ---------------------------------------------------------------------------
# CHAPTER 2: IMPLEMENTATION OF ACADEMIC & TECHNICAL REQUIREMENTS
# ---------------------------------------------------------------------------
add_h1("2. Implementation of Academic and Technical Requirements")

add_h2("2.1 Blackboard Architecture and Shared State Management")
p = doc.add_paragraph(
    "Requirement & Purpose: Multi-agent systems require a decoupled, thread-safe shared context to prevent agent race conditions, "
    "maintain atomic state history, and allow independent agents to read and write domain context without peer coupling.\n"
    "Implementation: Implemented in "
)
add_p_hyperlink(p, f"{GITHUB_BASE}/testforge/blackboard.py#L208-L932", "testforge/blackboard.py:Blackboard")
p.add_run(
    ". State is partitioned into five typed spaces: TargetSpace, MutantSpace, CriticSpace, SuiteSpace, and MetricsSpace. "
    "Concurrency is guarded by an RLock. Fine-grained event dispatching uses BlackboardSubscription pattern-matching pub/sub. "
    "Checkpoint persistence is handled via SQLiteBlackboardStorage in WAL mode.\n"
    "Evidence: tests/test_blackboard.py (18 tests), tests/test_blackboard_persistence.py (22 tests), and active production database "
    "qa_artifacts/testforge_checkpoints.db (197.3 MB, 1,104 snapshots across 210 jobs).\n"
    "Status: Implemented and Verified."
)

add_h2("2.2 Model Context Protocol (MCP) Tool Integration")
p = doc.add_paragraph(
    "Requirement & Purpose: Standardize agent-tool interactions through official Model Context Protocol (MCP) tool contracts.\n"
    "Implementation: Implemented using official FastMCP (mcp-python). TestForge exposes two distinct in-process local tool servers:\n"
    "• Filesystem Server: "
)
add_p_hyperlink(p, f"{GITHUB_BASE}/testforge/mcp_server.py#L83-L172", "testforge/mcp_server.py:create_filesystem_server")
p.add_run(
    " exposes read_text_file, list_directory, and get_file_info with path traversal defense.\n"
    "• GitHub Repository Server: "
)
add_p_hyperlink(p, f"{GITHUB_BASE}/testforge/mcp_server.py#L175-L309", "testforge/mcp_server.py:create_github_server")
p.add_run(
    " exposes get_repository_info, get_file_contents, and search_repositories with SafeGitHubRedirectHandler and 500 KB bounded streaming.\n"
    "• Tool Invocation: "
)
add_p_hyperlink(p, f"{GITHUB_BASE}/testforge/mcp_client.py#L146-L584", "testforge/mcp_client.py:MCPClientManager")
p.add_run(
    " manages client connection, schema validation, call_tool, and sync_to_blackboard.\n"
    "Important Scope Distinction: FastMCP tools execute locally in-process. External GitHub calls fallback to deterministic test doubles when credentials are unset.\n"
    "Evidence: tests/test_mcp.py (22 tests), tests/test_mcp_network_security.py (12 tests), tests/test_orchestration_mcp.py (16 tests).\n"
    "Status: Implemented and Verified (Local FastMCP Services)."
)

add_h2("2.3 Pydantic-Based Structured Outputs")
p = doc.add_paragraph(
    "Requirement & Purpose: Eliminate brittle regex parsing of LLM outputs by enforcing strict schema validation and type invariants.\n"
    "Implementation: Built on Pydantic v2. Key models include "
)
add_p_hyperlink(p, f"{GITHUB_BASE}/testforge/a2a.py#L165-L188", "GeneratedTestPayload")
p.add_run(" (validates non-empty executable pytest code), ")
add_p_hyperlink(p, f"{GITHUB_BASE}/testforge/a2a.py#L132-L143", "CriticDirectivePayload")
p.add_run(
    ", ToolDefinition, and DiscoveredCallablesResult. Custom validators reject mutant ID hallucination and syntax errors.\n"
    "Evidence: tests/test_a2a.py (16 tests), tests/test_adk_generator.py (15 tests). Zero schema errors across 542 test cases.\n"
    "Status: Implemented and Verified."
)

add_h2("2.4 Agentic Design Patterns (Triad Feedback Loop)")
p = doc.add_paragraph(
    "Requirement & Purpose: Multi-agent collaboration across distinct cognitive roles: Generator, Adversarial Critic, and Evaluator.\n"
    "Implementation: Governed by "
)
add_p_hyperlink(p, f"{GITHUB_BASE}/testforge/orchestrator.py#L137-L1491", "TestForgeOrchestrator")
p.add_run(
    ". The pipeline coordinates: (1) AST analysis & callable discovery; (2) Generator test synthesis; (3) Sandbox Pass@1 validation; "
    "(4) AST mutant generation; (5) Parallel sandbox mutant evaluation; (6) Critic vulnerability diagnosis; and (7) Generator targeted refinement. "
    "The closed-loop reflection executes up to 3 cycles until mutation score reaches >= 85% or terminates.\n"
    "Evidence: tests/test_agentic_pipeline.py (16 tests), tests/test_adversarial_failure_injection.py (18 tests).\n"
    "Status: Implemented and Verified."
)

add_h2("2.5 Callback-Based Task Monitoring")
p = doc.add_paragraph(
    "Requirement & Purpose: Decouple pipeline execution from telemetry, UI notifications, and trace logging.\n"
    "Implementation: Implemented in "
)
add_p_hyperlink(p, f"{GITHUB_BASE}/testforge/callbacks.py#L238-L361", "testforge/callbacks.py:CallbackRegistry")
p.add_run(
    ". Supports 14 distinct EventType signals (OPERATION_START, STATE_CHANGE, AGENT_START, ERROR, etc.) wrapped in scrubbed LifecycleEvent envelopes. "
    "TraceLogger appends structured JSONL records to testforge_trace.jsonl.\n"
    "Evidence: tests/test_callbacks.py (16 tests), tests/test_observability.py (14 tests). Active trace log: 101 MB.\n"
    "Status: Implemented and Verified."
)

add_h2("2.6 Agent-to-Agent (A2A) Communication and Discovery")
p = doc.add_paragraph(
    "Requirement & Purpose: Support standardized inter-agent capability exchange and decentralized message routing.\n"
    "Implementation: Implemented per A2A Protocol v0.3.0. "
)
add_p_hyperlink(p, f"{GITHUB_BASE}/testforge/a2a_protocol.py#L98-L158", "build_testforge_agent_card()")
p.add_run(
    " publishes agent capabilities at /.well-known/agent.json. In-process messaging is routed by A2ABroker supporting FIPA performatives (REQUEST, INFORM, AGREE, REFUSE, FAILURE).\n"
    "Evidence: tests/test_a2a.py (16 tests), tests/test_a2a_protocol.py (15 tests), live endpoint GET /.well-known/agent.json.\n"
    "Status: Implemented and Verified."
)

add_h2("2.7 Google ADK Integration")
p = doc.add_paragraph(
    "Requirement & Purpose: Integrate Google Agent Development Kit patterns for deliberate planning and test synthesis.\n"
    "Implementation: Implemented in "
)
add_p_hyperlink(p, f"{GITHUB_BASE}/testforge/adk_generator.py#L77-L310", "testforge/adk_generator.py")
p.add_run(
    " and adk_engine.py using google-genai abstractions (LlmAgent, Runner, InMemorySessionService, BaseLlm). ADKModelBridge subclasses BaseLlm to bridge ADK session workflows with TestForge's LLM client or deterministic test doubles.\n"
    "Evidence: tests/test_adk_generator.py (15 tests), tests/test_blast_and_adk.py (4 tests).\n"
    "Status: Implemented and Verified."
)

add_h2("2.8 CrewAI Integration")
p = doc.add_paragraph(
    "Requirement & Purpose: Integrate CrewAI framework for role-based adversarial mutation critique.\n"
    "Implementation: Implemented in "
)
add_p_hyperlink(p, f"{GITHUB_BASE}/testforge/crew_critic.py#L110-L250", "testforge/crew_critic.py:CrewAICriticAgent")
p.add_run(
    " using crewai core primitives (Agent, Task, Crew, BaseLLM). Configures an adversarial 'Senior Mutation Testing Specialist' tasked with diagnosing surviving mutant AST unified diffs.\n"
    "Evidence: tests/test_crew_critic.py (12 tests). Upstream deprecation notices audited and confirmed benign.\n"
    "Status: Implemented and Verified."
)

add_h2("2.9 Security Guardrails Across Complete Workflow")
p = doc.add_paragraph(
    "Requirement & Purpose: Defense-in-depth preventing RCE attacks, SSRF requests, and indirect prompt injections.\n"
    "Implementation: (1) Static AST Security: "
)
add_p_hyperlink(p, f"{GITHUB_BASE}/testforge/security.py#L354-L607", "_ASTSecurityVisitor")
p.add_run(
    " scans source and test ASTs, blocking dangerous imports (os, sys, subprocess, socket) and forbidden calls (eval, exec, open); "
    "(2) SSRF Defense: SafeGitHubRedirectHandler validates hostnames, resolves DNS to block loopback/private IPs, and enforces 500 KB bounded reads; "
    "(3) Prompt Defense: wrap_untrusted_content applies cryptographic XML delimiter envelopes, and inspect_source_for_indirect_injections defuses docstring overrides.\n"
    "Evidence: 98 dedicated security tests across 4 test modules (100% passing).\n"
    "Status: Implemented and Verified."
)

add_h2("2.10 Observability, Lineage, and Provenance Tracking")
doc.add_paragraph(
    "Requirement & Purpose: Guarantee tamper-evident cryptographic provenance from code ingestion through mutation evaluation to test suite export.\n"
    "Implementation: TestForge computes SHA-256 hashes at each lifecycle boundary: input source (source_sha), candidate tests (candidate_suite_hash), "
    "validated tests (validated_suite_hash), Blackboard suite (suite_space.suite_hash), and exported file (exported_suite_hash). Every mutant is assigned "
    "an immutable ID, line number, and AST unified diff logged in testforge_trace.jsonl.\n"
    "Evidence: tests/test_observability.py (14 tests). All 4 suite hashes matched byte-for-byte in Phase 3 independent audit.\n"
    "Status: Implemented and Verified."
)

add_h2("2.11 Multi-Run Benchmarking & Ablation Study")
p = doc.add_paragraph(
    "Requirement & Purpose: Provide empirical statistical benchmarking measuring latency, mutation kill rates, and ablation variations.\n"
    "Implementation: Implemented in "
)
add_p_hyperlink(p, f"{GITHUB_BASE}/testforge/benchmarking.py#L135-L423", "testforge/benchmarking.py:BenchmarkRunner")
p.add_run(
    " and AblationEngine. Aggregates statistical metrics (mean, median, IQR, stddev) across multi-run trials and renders reports to benchmark_results.json and benchmark_results.md.\n"
    "Evidence: tests/test_benchmarking.py (8 tests), tests/test_fast_benchmarking.py (6 tests).\n"
    "Status: Implemented and Verified."
)

add_h2("2.12 Deployment Readiness")
p = doc.add_paragraph(
    "Requirement & Purpose: Self-contained packaging for reproducible execution across host environments.\n"
    "Implementation: Multi-stage "
)
add_p_hyperlink(p, f"{GITHUB_BASE}/Dockerfile#L1-L52", "Dockerfile")
p.add_run(
    " (Python 3.13-slim, non-root user UID 10001, health probes), docker-compose.yml, single-command launcher start_testforge.sh, and production FastAPI server serving both API routes and static frontend assets.\n"
    "Important Scope Distinction: Local native execution and container packaging are fully verified. Deployment to managed public cloud hyperscalers (e.g. AWS ECS, GCP Cloud Run) remains planned for future production phases.\n"
    "Evidence: tests/test_deployment.py (10 tests), active local server on port 8000.\n"
    "Status: Implemented for Local/Container Deployment; Public Cloud Planned."
)

add_h2("2.13 Requirement Verification Scorecard")
score_tbl = doc.add_table(rows=14, cols=5)
score_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
set_tbl_borders(score_tbl)

headers = ["#", "Academic Requirement", "Primary Implementing Modules", "Tests", "Verification Status"]
for col_idx, h in enumerate(headers):
    c = score_tbl.cell(0, col_idx)
    c.text = h
    style_cell(c, fill_hex="EAEAEA", bold=True, font_size=8)

rows_data = [
    ("1", "Blackboard Shared State Context", "testforge/blackboard.py, persistence.py", "66 passed", "Implemented & Verified"),
    ("2", "Model Context Protocol (FastMCP)", "testforge/mcp_server.py, mcp_client.py", "50 passed", "Implemented & Verified"),
    ("3", "Pydantic Structured Outputs", "testforge/a2a.py, adk_engine.py", "45+ passed", "Implemented & Verified"),
    ("4", "Agentic Design Patterns (Feedback)", "testforge/orchestrator.py, agents.py", "34 passed", "Implemented & Verified"),
    ("5", "Callback Monitoring & Telemetry", "testforge/callbacks.py, logger.py", "30 passed", "Implemented & Verified"),
    ("6", "Agent-to-Agent (A2A) v0.3.0", "testforge/a2a.py, a2a_protocol.py", "36 passed", "Implemented & Verified"),
    ("7", "Google ADK Framework Integration", "testforge/adk_generator.py, adk_engine.py", "19 passed", "Implemented & Verified"),
    ("8", "CrewAI Framework Integration", "testforge/crew_critic.py", "12 passed", "Implemented & Verified"),
    ("9", "Multi-Layer Security Guardrails", "testforge/security.py, network_security.py", "98 passed", "Implemented & Verified"),
    ("10", "Lineage & Cryptographic Provenance", "testforge/logger.py, persistence.py", "14 passed", "Implemented & Verified"),
    ("11", "Multi-Run Benchmarking & Ablation", "testforge/benchmarking.py", "18 passed", "Implemented & Verified"),
    ("12", "Deployment Readiness", "Dockerfile, docker-compose.yml, server.py", "10 passed", "Local Container Verified; Cloud Planned"),
    ("TOTAL", "12 Academic Requirements Evaluated", "Complete TestForge Repository", "542 passed", "11 Verified, 1 Partially Verified")
]

for row_idx, r in enumerate(rows_data):
    for col_idx, val in enumerate(r):
        c = score_tbl.cell(row_idx + 1, col_idx)
        c.text = val
        fill = "F6F6F8" if (row_idx % 2 == 1) else None
        if row_idx == len(rows_data) - 1:
            fill = "EAEAEA"
        style_cell(c, fill_hex=fill, bold=(row_idx == len(rows_data) - 1), font_size=7.5)

doc.add_paragraph()

# ---------------------------------------------------------------------------
# CHAPTER 3: SYSTEM ARCHITECTURE
# ---------------------------------------------------------------------------
add_h1("3. System Architecture")

add_h2("3.1 Overall System Architecture")
doc.add_paragraph(
    "TestForge is structured into four distinct architectural tiers: (1) Presentation Tier: a vanilla ES6 single-page web cockpit with WebSocket event streaming; "
    "(2) Application & Orchestration Tier: an asynchronous FastAPI backend and master state-machine orchestrator; (3) Cognitive Multi-Agent Tier: specialized "
    "agents operating over Google ADK, CrewAI, FastMCP, and A2A broker protocols; and (4) Persistence & Sandboxing Tier: a thread-safe Blackboard backed by "
    "SQLite WAL storage and parallel process test runners."
)

add_figure("docs/WIP_REPORT/assets/figure1_system_architecture.png", "Figure 1: Overall TestForge System Architecture showing UI Cockpit, FastAPI, Hardening Orchestrator, Multi-Agent Tier, Blackboard, and Sandbox.", width=Inches(6.0))

add_h2("3.2 Frontend and Backend Architecture")
doc.add_paragraph(
    "The backend is powered by FastAPI (server.py), exposing 42 REST endpoints and a WebSocket hub (/api/ws/events). The frontend (frontend/) is deliberately "
    "built with vanilla HTML5, CSS3 glassmorphism, and modern ES6 JavaScript, eliminating bulky node build toolchains while enabling sub-millisecond reactive rendering "
    "of test diffs, live mutation kills, and checkpoint timelines."
)

add_h2("3.3 Multi-Agent Architecture")
doc.add_paragraph(
    "Agents operate with strictly delineated responsibilities:\n"
    "• TargetManagerAgent: Ingests target Python modules, checks syntax validity, defuses prompt injection payloads, and extracts AST metadata.\n"
    "• IntelligentASTSynthesizer: Discovers all module callables, analyzes comparison guards, runs ground-truth reference executions, and generates value-aware test cases.\n"
    "• ASTMutator: Traverses target AST to generate syntactically valid mutants across 9 operator classes.\n"
    "• ParallelSandboxRunner: Executes pytest runs concurrently across mutants in process-isolated temporary environments with 10-second timeouts.\n"
    "• CrewAICriticAgent: Analyzes surviving mutant unified diffs and outputs structured directives identifying missing edge cases."
)

add_h2("3.4 Agent Communication and Coordination")
doc.add_paragraph(
    "Agents coordinate through two standardized communication mechanisms: (1) The Blackboard Pattern: high-throughput in-process state updates using thread-safe "
    "partition accessors and pattern-matching pub/sub events; and (2) The A2A Broker: structured message routing using FIPA-compliant performatives and Pydantic envelopes."
)

add_h2("3.5 Blackboard and Shared State Flow")
doc.add_paragraph(
    "State transitions strictly increment an atomic revision counter on the Blackboard. When an agent updates a partition (e.g. suite_space), the Blackboard validates "
    "the schema, computes SHA-256 hashes, dispatches event callbacks to subscribers, and triggers automatic checkpointing into SQLite."
)

add_h2("3.6 Technology Stack")
doc.add_paragraph(
    "• Core Language & Runtime: Python 3.13.18 / 3.14 on macOS Darwin ARM64.\n"
    "• Web Framework: FastAPI 0.115, Uvicorn 0.32, Starlette WebSockets.\n"
    "• Agentic Frameworks: FastMCP (mcp-python 1.2), Google ADK (google-genai 1.0), CrewAI 0.11.\n"
    "• Testing & Mutation: Pytest 9.1.1, Coverage.py 7.6, Mutmut-compatible AST transformer.\n"
    "• Persistence: SQLite 3.45 with Write-Ahead Logging (WAL) and foreign keys."
)

add_h2("3.7 End-to-End Execution Workflow")
doc.add_paragraph(
    "The complete hardening cycle progresses through 8 discrete execution steps: (1) Source Ingestion; (2) Callable Discovery; (3) Candidate Synthesis; "
    "(4) Pass@1 Clean Code Validation; (5) AST Mutation Injection; (6) Parallel Mutant Evaluation; (7) Adversarial Critique; and (8) Terminal Hardened Suite Export."
)

add_figure("docs/WIP_REPORT/assets/figure2_execution_workflow.png", "Figure 2: Multi-Agent Test Hardening Execution Workflow showing the 8-step closed-loop reflection cycle.", width=Inches(6.0))

# ---------------------------------------------------------------------------
# CHAPTER 4: IMPLEMENTATION DETAILS AND REPOSITORY REFERENCES
# ---------------------------------------------------------------------------
add_h1("4. Implementation Details and Repository References")

add_h2("4.1 Development Environment and Project Structure")
p = doc.add_paragraph(
    "Purpose: Provide an isolated, reproducible development and execution environment.\n"
    "Implementation: Structured into testforge/ (39 modules), tests/ (48 test files), frontend/ (vanilla cockpit), server.py, and qa_artifacts/.\n"
    "Repository Reference: "
)
add_p_hyperlink(p, GITHUB_BASE, f"Repository Root ({COMMIT_SHA[:12]})")
p.add_run("\nVerification: tests/test_deployment.py (10 tests), start_testforge.sh.")

add_h2("4.2 Source Code Ingestion")
p = doc.add_paragraph(
    "Purpose: Parse, validate, and register target Python code from local paths or remote GitHub repositories.\n"
    "Implementation: Validates Python syntax using ast.parse, extracts SHA-256 source digests (source_sha), defuses prompt-injection keywords in docstrings, and loads sanitized code into Blackboard target_space.\n"
    "Execution Flow: Ingests target string/file -> AST Syntax Check -> Prompt Guard Defuse -> Blackboard target_space.\n"
    "Repository Reference: "
)
add_p_hyperlink(p, f"{GITHUB_BASE}/testforge/ingestion.py#L353-L604", "testforge/ingestion.py:TargetManagerAgent (L353–L604)")
p.add_run("\nVerification: tests/test_mode_c_ingestion.py (8 tests), tests/test_ingestion_and_llm.py (4 tests).")

add_h2("4.3 AST Analysis and Callable Discovery")
p = doc.add_paragraph(
    "Purpose: Statically inspect callable AST nodes to extract parameter signatures, comparison boundaries, and guard conditions.\n"
    "Implementation: Traverses AST comparison nodes (visit_Compare), recording comparison operators (<, <=, >, >=, ==) and numeric comparator thresholds (e.g., 0, 5, 100). Captures guard return values in visit_If to identify invalid parameter constraints.\n"
    "Execution Flow: Target AST -> Node Inspection -> Boundary Threshold Mapping (-1, 0, 1).\n"
    "Repository Reference: "
)
add_p_hyperlink(p, f"{GITHUB_BASE}/testforge/intelligent_generator.py#L186-L325", "testforge/intelligent_generator.py:ASTCallableAnalyzer (L186–L325)")
p.add_run("\nVerification: tests/test_ast_scope_extraction.py (12 tests).")

add_h2("4.4 Intelligent Test Case Generation")
p = doc.add_paragraph(
    "Purpose: Synthesize high-yield unit test suites targeting 100% of discovered callables with value-aware assertions.\n"
    "Implementation: Generates tests across 4 tiers: Nominal Happy Path, Boundary Value Analysis (testing exact comparator thresholds T-1, T, T+1), Negative Guard Tests (asserting pytest.raises(ValueError) or guard returns), and Mutation-Guided Refinements. ReferenceExecutor compiles target code in memory to record clean return values, enabling _build_value_assertion to generate strict mathematical equality checks.\n"
    "Execution Flow: Discovered Callables -> Boundary Extraction -> Reference Run -> Pytest Test Suite -> SuiteSpace.\n"
    "Repository Reference: "
)
add_p_hyperlink(p, f"{GITHUB_BASE}/testforge/intelligent_generator.py#L332-L1261", "testforge/intelligent_generator.py:IntelligentASTSynthesizer (L332–L1261)")
p.add_run("\nVerification: tests/test_post_demo_defect_fixes.py (10 tests), Phase 3 independent validation (100% callable coverage on logistics).")

add_h2("4.5 Test Execution and Sandboxing")
p = doc.add_paragraph(
    "Purpose: Safely execute test suites in process isolation, measure statement coverage, and evaluate mutant outcomes.\n"
    "Implementation: Executes pytest in ephemeral scratch directories using subprocess.Popen with strict 10-second timeout enforcement. GranularTestValidator parses test ASTs to ensure only tests with meaningful assertions are admitted to the validated test suite.\n"
    "Execution Flow: Candidate Test Suite -> Clean Target Sandbox -> Pass@1 Verification -> Statement Coverage.\n"
    "Repository Reference: "
)
add_p_hyperlink(p, f"{GITHUB_BASE}/testforge/sandbox.py#L174-L401", "testforge/sandbox.py:ParallelSandboxRunner (L174–L401)")
p.add_run("\nVerification: tests/test_sandbox.py (6 tests), tests/test_cancellation.py (8 tests).")

add_h2("4.6 Mutation Testing Engine")
p = doc.add_paragraph(
    "Purpose: Inject syntactic faults into target code to measure the fault-detection capability of generated test suites.\n"
    "Implementation: MutationTransformer visits AST nodes to inject 9 operator classes: ARITH_OP, COMP_OP, BOUNDARY_SWAP, OFF_BY_ONE, COND_INV, LOGICAL_CONN, CONST_VAL, EXC_SWAP, and RET_VAL. Each mutant produces an AST unified diff.\n"
    "Execution Flow: Target Code AST -> Operator Inspection -> Point Mutation -> MutantSpace.\n"
    "Repository Reference: "
)
add_p_hyperlink(p, f"{GITHUB_BASE}/testforge/mutator.py#L37-L458", "testforge/mutator.py:ASTMutator (L37–L458)")
p.add_run("\nVerification: tests/test_mutator.py (6 tests), tests/test_ast_mutation_m2.py (8 tests).")

add_h2("4.7 Mutation-Guided Refinement Loop")
p = doc.add_paragraph(
    "Purpose: Govern multi-agent state transitions, evaluate reflection criteria, and trigger targeted refinement.\n"
    "Implementation: Executes the hardening state machine. If mutation score is below target threshold (>= 85%) and reflection iterations are remaining (< 3), it invokes the Adversarial Critic, routes directives back to the Intelligent Synthesizer, re-evaluates surviving mutants, and commits an atomic checkpoint.\n"
    "Execution Flow: Evaluator Results -> Check Threshold -> Critic Directive -> Targeted Refinement -> Sandbox.\n"
    "Repository Reference: "
)
add_p_hyperlink(p, f"{GITHUB_BASE}/testforge/orchestrator.py#L137-L1491", "testforge/orchestrator.py:TestForgeOrchestrator (L137–L1491)")
p.add_run("\nVerification: tests/test_agentic_pipeline.py (16 tests), tests/test_task_lifecycle.py (12 tests).")

add_h2("4.8 Blackboard and Persistent Shared State")
p = doc.add_paragraph(
    "Purpose: Coordinate decoupled agent communication and preserve thread-safe execution history.\n"
    "Implementation: In-memory dictionary protected by RLock. State access is partitioned into target_space, mutant_space, critic_space, suite_space, and metrics_space. Supports pattern-matching subscriptions and automatic SQLite WAL auto-save.\n"
    "Repository Reference: "
)
add_p_hyperlink(p, f"{GITHUB_BASE}/testforge/blackboard.py#L208-L932", "testforge/blackboard.py:Blackboard (L208–L932)")
p.add_run("\nVerification: tests/test_blackboard.py (18 tests), tests/test_blackboard_persistence.py (22 tests).")

add_h2("4.9 MCP Tool Execution")
p = doc.add_paragraph(
    "Purpose: Standardize agent-tool interactions via Model Context Protocol.\n"
    "Implementation: Filesystem server exposes read_text_file, list_directory, and get_file_info. GitHub server exposes get_repository_info, get_file_contents, and search_repositories. MCPClientManager invokes tools and synchronizes results into Blackboard target_space.\n"
    "Repository Reference: "
)
add_p_hyperlink(p, f"{GITHUB_BASE}/testforge/mcp_server.py#L83-L309", "testforge/mcp_server.py (L83–L309)")
p.add_run("\nVerification: tests/test_mcp.py (22 tests), tests/test_mcp_network_security.py (12 tests).")

add_h2("4.10 A2A Communication")
p = doc.add_paragraph(
    "Purpose: Support inter-agent capability exchange and standard JSON-RPC 2.0 task execution.\n"
    "Implementation: A2A Protocol v0.3.0 compliant. Publishes AgentCard at /.well-known/agent.json. In-process broker manages FIPA performatives and validates sender/action security permissions.\n"
    "Repository Reference: "
)
add_p_hyperlink(p, f"{GITHUB_BASE}/testforge/a2a.py#L244-L659", "testforge/a2a.py:A2ABroker (L244–L659)")
p.add_run("\nVerification: tests/test_a2a.py (16 tests), tests/test_a2a_protocol.py (15 tests).")

add_h2("4.11 Google ADK Generator")
p = doc.add_paragraph(
    "Purpose: Implement generative test synthesis utilizing Google Agent Development Kit patterns.\n"
    "Implementation: Subclasses BaseLlm to bind ADK's LlmAgent and Runner with TestForge's multi-provider LLM client or deterministic fallbacks.\n"
    "Repository Reference: "
)
add_p_hyperlink(p, f"{GITHUB_BASE}/testforge/adk_generator.py#L77-L310", "testforge/adk_generator.py:ADKModelBridge (L77–L310)")
p.add_run("\nVerification: tests/test_adk_generator.py (15 tests).")

add_h2("4.12 CrewAI Critic")
p = doc.add_paragraph(
    "Purpose: Deploy an adversarial role-based agent to critique surviving mutant AST diffs.\n"
    "Implementation: Configures a CrewAI Agent, Task, and Crew with custom BaseLLM adapter to inspect surviving mutant diffs and issue structured reflection directives.\n"
    "Repository Reference: "
)
add_p_hyperlink(p, f"{GITHUB_BASE}/testforge/crew_critic.py#L35-L250", "testforge/crew_critic.py:CrewAICriticAgent (L35–L250)")
p.add_run("\nVerification: tests/test_crew_critic.py (12 tests).")

add_h2("4.13 Pydantic Data Models")
p = doc.add_paragraph(
    "Purpose: Enforce strict typing across agent, broker, and storage interfaces.\n"
    "Implementation: Defines A2AMessage, GeneratedTestPayload, CriticDirectivePayload, and TestForgeState with custom validators enforcing non-empty code and syntax validity.\n"
    "Repository Reference: "
)
add_p_hyperlink(p, f"{GITHUB_BASE}/testforge/a2a.py#L56-L188", "testforge/a2a.py (L56–L188)")
p.add_run("\nVerification: tests/test_a2a.py, tests/test_adk_generator.py.")

add_h2("4.14 Callback and Logging Mechanisms")
p = doc.add_paragraph(
    "Purpose: Provide non-blocking event dispatching and structured JSONL telemetry.\n"
    "Implementation: Dispatches scrubbed LifecycleEvent signals across 14 event types and logs append-only microsecond records to testforge_trace.jsonl.\n"
    "Repository Reference: "
)
add_p_hyperlink(p, f"{GITHUB_BASE}/testforge/callbacks.py#L238-L361", "testforge/callbacks.py:CallbackRegistry (L238–L361)")
p.add_run("\nVerification: tests/test_callbacks.py (16 tests), tests/test_observability.py (14 tests).")

add_h2("4.15 FastAPI Backend")
p = doc.add_paragraph(
    "Purpose: Expose production REST and WebSocket interfaces for the web cockpit and remote clients.\n"
    "Implementation: Exposes 42 REST routes (e.g. /api/harden/start, /api/checkpoints/list, /api/a2a/test, /healthz, /readyz) and a WebSocket hub streaming real-time blackboard events.\n"
    "Repository Reference: "
)
add_p_hyperlink(p, f"{GITHUB_BASE}/server.py#L58-L1751", "server.py (L58–L1751)")
p.add_run("\nVerification: tests/test_cancellation.py, tests/test_task_lifecycle.py, active server on port 8000.")

add_h2("4.16 Frontend Integration")
p = doc.add_paragraph(
    "Purpose: Provide a reactive, zero-build-step user interface for real-time test hardening control.\n"
    "Implementation: Native ES6 SPA connecting via REST and WebSockets. Renders interactive mutation diffs, checkpoint timelines, and diagnostic modals.\n"
    "Repository Reference: "
)
add_p_hyperlink(p, f"{GITHUB_BASE}/frontend/app.js", "frontend/app.js")
p.add_run("\nVerification: Full E2E browser verification (16/16 steps passed).")

add_h2("4.17 Checkpointing and SQLite Persistence")
p = doc.add_paragraph(
    "Purpose: Provide durable snapshot storage, differential auditing, and state resumption.\n"
    "Implementation: SQLite WAL database storing atomic snapshots with SHA-256 integrity digests. DeterministicDiffInspector calculates fine-grained partition diffs and mutant state transitions (SURVIVED -> KILLED).\n"
    "Repository Reference: "
)
add_p_hyperlink(p, f"{GITHUB_BASE}/testforge/persistence.py#L176-L682", "testforge/persistence.py:SQLiteBlackboardStorage (L176–L682)")
p.add_run("\nVerification: tests/test_checkpoint_resumption.py (26 tests), active DB qa_artifacts/testforge_checkpoints.db (1,104 snapshots).")

# ---------------------------------------------------------------------------
# CHAPTER 5: SECURITY AND EXECUTION CONTROL
# ---------------------------------------------------------------------------
add_h1("5. Security and Execution Control")

add_h2("5.1 Source Code Validation")
doc.add_paragraph(
    "All ingested code is parsed into an AST prior to compilation. Syntax errors, non-UTF8 encodings, and malformed statements are intercepted before entering the pipeline, preventing compilation crashes."
)

add_h2("5.2 Sandboxed Test Execution")
doc.add_paragraph(
    "Test execution occurs strictly within isolated temporary scratch directories created via tempfile.TemporaryDirectory. Tests run in dedicated subprocesses via .venv-release/bin/python -m pytest with strict resource boundaries and 10-second timeout terminations."
)

add_h2("5.3 AST-Based Security Inspection")
p = doc.add_paragraph(
    "Implemented in "
)
add_p_hyperlink(p, f"{GITHUB_BASE}/testforge/security.py#L354-L607", "testforge/security.py:_ASTSecurityVisitor")
p.add_run(
    ". Scans the complete AST before execution, detecting and rejecting forbidden calls (eval, exec, compile, __import__, open) and dangerous attribute access (__subclasses__, __globals__)."
)

add_h2("5.4 Restricted Imports and Operations")
doc.add_paragraph(
    "The AST visitor enforces a strict import whitelist. Ingested code and generated test suites are forbidden from importing os, sys, subprocess, socket, shutil, pty, or ctypes, preventing privilege escalation and host filesystem compromise."
)

add_h2("5.5 Input Validation & Bounded Streaming")
p = doc.add_paragraph(
    "Implemented in "
)
add_p_hyperlink(p, f"{GITHUB_BASE}/testforge/network_security.py#L267-L318", "testforge/network_security.py:bounded_read")
p.add_run(
    ". Ingested payloads and HTTP response streams are strictly bounded to 500 KB to defend against memory exhaustion and decompression bombs."
)

add_h2("5.6 Filesystem & Network Restrictions")
p = doc.add_paragraph(
    "Local file access is constrained within designated sandbox roots via "
)
add_p_hyperlink(p, f"{GITHUB_BASE}/testforge/mcp_server.py#L49-L80", "_is_path_safe")
p.add_run(
    ", blocking directory traversal attacks (../). Outbound network requests use "
)
add_p_hyperlink(p, f"{GITHUB_BASE}/testforge/network_security.py#L196-L253", "SafeGitHubRedirectHandler")
p.add_run(
    ", which resolves hostnames and blocks connections to loopback (127.0.0.1) and private RFC-1918 subnets (SSRF defense)."
)

add_h2("5.7 Execution Timeouts and Cancellation")
p = doc.add_paragraph(
    "The orchestrator regularly checks cooperative cancellation tokens ("
)
add_p_hyperlink(p, f"{GITHUB_BASE}/testforge/orchestrator.py#L284-L299", "check_cancellation_or_timeout")
p.add_run(
    ") at every stage boundary. Jobs exceeding configured execution limits (default 300s) or cancelled by the user terminate cleanly, releasing subprocesses and database locks."
)

add_h2("5.8 Credential Redaction")
p = doc.add_paragraph(
    "Implemented in "
)
add_p_hyperlink(p, f"{GITHUB_BASE}/testforge/security.py#L78-L87", "testforge/security.py:redact_sensitive_data")
p.add_run(
    ". All telemetry logs, event payloads, and database checkpoints are scrubbed using regular expressions matching API keys, GitHub tokens, Bearer tokens, and passwords."
)

add_h2("5.9 Clean-Code Integrity Verification")
p = doc.add_paragraph(
    "Implemented in "
)
add_p_hyperlink(p, f"{GITHUB_BASE}/testforge/sandbox.py#L444-L931", "testforge/sandbox.py:GranularTestValidator")
p.add_run(
    ". Every candidate test suite must pass 100% against the clean unmutated target codebase (Pass@1 integrity). Any test failing on clean code is quarantined and excluded before mutation evaluation begins."
)

# ---------------------------------------------------------------------------
# CHAPTER 6: TESTING AND EVALUATION METHODOLOGY
# ---------------------------------------------------------------------------
add_h1("6. Testing and Evaluation Methodology")

add_h2("6.1 Testing Strategy")
doc.add_paragraph(
    "TestForge enforces a multi-tiered verification pyramid: (1) Unit Tests for isolated algorithmic modules; (2) Subsystem Integration Tests for FastMCP and A2A broker contracts; (3) Adversarial Security Tests for RCE and SSRF defenses; (4) Full End-to-End Regression Tests; and (5) Live Browser Acceptance Audits."
)

add_h2("6.2 Unit Testing")
doc.add_paragraph(
    "The repository contains 48 automated test modules in tests/ verifying every class, mutation operator, and Pydantic validator."
)

add_h2("6.3 Integration Testing")
doc.add_paragraph(
    "Subsystems are verified with end-to-end integration tests: FastMCP client-server tool invocation (tests/test_mcp.py), A2A broker protocol round-trips (tests/test_a2a_protocol.py), and SQLite checkpoint resumption (tests/test_checkpoint_resumption.py)."
)

add_h2("6.4 Regression Testing")
doc.add_paragraph(
    "The complete regression test suite executes via: .venv-release/bin/python -m pytest tests/\n"
    "Verified Regression Outcome:\n"
    "• Tests Passed: 542 passed, 0 failed (100% pass rate).\n"
    "• Execution Duration: Approximately 277 seconds (4 minutes 37 seconds) on Apple Silicon ARM64.\n"
    "• Warnings Reported: 305 warnings (strictly accounted for: 284 Pydantic V2 deprecation notices from upstream CrewAI 0.11, 14 Google Cloud storage deprecations, and 7 Pytest unclosed socket notices; none impact test execution)."
)

add_h2("6.5 End-to-End Browser Testing")
doc.add_paragraph(
    "Automated browser testing was conducted using agent-browser (headless Chromium) across 16 sequential workflow steps, verifying UI rendering, tab navigation, sample loading, live hardening execution, cancellation recovery, and SQLite checkpoint diffing."
)

add_h2("6.6 Mutation Testing Methodology")
doc.add_paragraph(
    "Mutation score is measured by executing the validated test suite against each AST-mutated copy in an isolated subprocess:\n"
    "Raw Mutation Score = (Killed Mutants / Total Mutants Evaluated) * 100\n"
    "Mutants producing an assertion failure or uncaught domain exception are classified as KILLED; mutants completing with code 0 are classified as SURVIVED."
)

add_h2("6.7 Statement Coverage Measurement")
doc.add_paragraph(
    "Statement coverage is measured inside the test sandbox using coverage.py:\n"
    "Statement Coverage = (Executed Statements / Total Statements) * 100\n"
    "Coverage is recorded alongside mutation score at every reflection iteration."
)

add_h2("6.8 Independent Validation")
doc.add_paragraph(
    "Reproducibility was verified in an isolated scratch environment using standalone runner qa_artifacts/phase3_independent_validation_20261031_142800/reproduce_benchmarks.py with dedicated SQLite stores (discount_isolated.db, logistics_isolated.db), confirming 100% metric determinism."
)

add_h2("6.9 Failure Scenario Testing")
doc.add_paragraph(
    "Adversarial fault injection tests (tests/test_adversarial_failure_injection.py) verify graceful error recovery during AST syntax errors, file permission locks, subprocess timeouts, and broker connection refusals."
)

# ---------------------------------------------------------------------------
# CHAPTER 7: BENCHMARK RESULTS AND PERFORMANCE ANALYSIS
# ---------------------------------------------------------------------------
add_h1("7. Benchmark Results and Performance Analysis")

add_h2("7.1 Initial Mutation Testing Baseline")
doc.add_paragraph(
    "In initial baseline runs (Phase 1), generated tests asserted only nominal execution (assert res is not None), achieving:\n"
    "• samples/discount.py: 5.26% raw mutation score (1 of 19 mutants killed, 18 survived).\n"
    "• samples/uploaded_logistics_engine.py: 3.10% raw mutation score (8 of 258 mutants killed, 250 survived)."
)

add_h2("7.2 Improvements in Intelligent Test Generation")
doc.add_paragraph(
    "Phase 2 introduced IntelligentASTSynthesizer, which extracts comparison operators and comparator constants directly from target ASTs, executes in-memory reference calls to capture ground truth, and synthesizes 4 distinct test tiers (Nominal, Boundary, Negative, Refinements)."
)

add_h2("7.3 Discount Benchmark Results")
doc.add_paragraph(
    "The samples/discount.py benchmark models an e-commerce volume discount and membership pricing engine:\n"
    "• Discovered Callables: 1/1 covered (100.0%).\n"
    "• Generated Tests: 11 tests generated; 11/11 passing (100.0% Pass@1).\n"
    "• Statement Coverage: 10/10 statements (100.0%).\n"
    "• Mutants Evaluated: 19 mutants.\n"
    "• Mutants Killed: 17 mutants.\n"
    "• Mutants Survived: 2 mutants (including 1 mathematically equivalent boundary mutant).\n"
    "• Raw Mutation Score (Offline Benchmark): 17 / 19 = 89.47%.\n"
    "• Adjusted Mutation Score (Equivalent Removed): 17 / (19 - 1) = 17 / 18 = 94.44%."
)

add_h2("7.4 Logistics Benchmark Results")
doc.add_paragraph(
    "The samples/uploaded_logistics_engine.py benchmark models an enterprise freight logistics engine featuring class methods (WarehouseInventory) and 9 standalone routing and tariff functions:\n"
    "• Discovered Callables: 10/10 callables tested (100.0% coverage; 0 skipped).\n"
    "• Generated Tests: 64 tests generated; 64/64 passing (100.0% Pass@1).\n"
    "• Statement Coverage: 119/132 statements (90.15%).\n"
    "• Boundary & Negative Tests: 43 boundary tests, 10 negative guard tests.\n"
    "• Mutants Evaluated: 258 mutants across 9 operator classes.\n"
    "• Mutants Killed: 176 mutants.\n"
    "• Mutants Survived: 82 mutants (including 24 equivalent rounding/constant mutants).\n"
    "• Raw Mutation Score (Offline Benchmark): 176 / 258 = 68.22%.\n"
    "• Adjusted Mutation Score (Equivalent Removed): 176 / (258 - 24) = 176 / 234 = 75.21%."
)

add_h2("7.5 Reconciliation of the 94.74% Live Demonstration Result")
doc.add_paragraph(
    "During the live browser demonstration on discount.py, the web dashboard reported a terminal mutation score of 94.74% (18/19 killed). "
    "This occurs because the live demonstration executed with the dynamic LLM generation loop enabled. In offline deterministic mode, whole-dollar test inputs "
    "allow Mutant 18 (round(final_price, 2) -> round(final_price, 1)) to survive (17/19 killed = 89.47%). In live execution, the model synthesized an unrounded "
    "fractional input (price=99.99). For $99.99, $99.99 * 0.9 = 89.991 -> round(..., 2) = 89.99, whereas Mutant 18 evaluates to 90.0. The assertion failed, "
    "killing Mutant 18 and lifting the live result to 18 / 19 = 94.74%. Both results are genuine and reflect distinct execution modes."
)

add_h2("7.6 Side-by-Side Benchmark Performance Comparison")
bench_tbl = doc.add_table(rows=12, cols=5)
bench_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
set_tbl_borders(bench_tbl)

b_headers = ["Evaluation Metric", "Discount Baseline", "Discount Hardened", "Logistics Baseline", "Logistics Hardened"]
for col_idx, h in enumerate(b_headers):
    c = bench_tbl.cell(0, col_idx)
    c.text = h
    style_cell(c, fill_hex="EAEAEA", bold=True, font_size=8)

b_rows = [
    ("Discovered / Tested Callables", "1 / 1 (100%)", "1 / 1 (100%)", "10 / 1 (10%)", "10 / 10 (100%)"),
    ("Generated Test Count", "2 (or 4 legacy)", "11 tests", "11 tests", "64 tests"),
    ("Test Pass Rate (Pass@1)", "100%", "11/11 (100%)", "100%", "64/64 (100%)"),
    ("Statement Coverage", "100% (10/10)", "100% (10/10)", "46.2% (61/132)", "90.15% (119/132)"),
    ("Total Mutants Evaluated", "19", "19", "258", "258"),
    ("Mutants Killed", "1", "17 killed", "8", "176 killed"),
    ("Mutants Survived", "18", "2", "250", "82"),
    ("Raw Mutation Score (Offline)", "5.26%", "89.47% (17x)", "3.10%", "68.22% (22x)"),
    ("Equivalent Mutants Removed", "1", "1", "24", "24"),
    ("Adjusted Mutation Score", "5.56%", "94.44%", "3.42%", "75.21%"),
    ("Live Demonstration Result", "—", "94.74% (18/19 killed)", "—", "—"),
]

for row_idx, r in enumerate(b_rows):
    for col_idx, val in enumerate(r):
        c = bench_tbl.cell(row_idx + 1, col_idx)
        c.text = val
        fill = "F6F6F8" if (row_idx % 2 == 1) else None
        style_cell(c, fill_hex=fill, bold=("Score" in r[0] or "Killed" in r[0]), font_size=7.5)

doc.add_paragraph()

add_figure("docs/WIP_REPORT/assets/figure7_benchmark_comparison.png", "Figure 7: Mutation Score Comparison: Initial Baseline Raw vs. TestForge Hardened Raw vs. Hardened Adjusted across Discount and Logistics Benchmarks.", width=Inches(5.8))

# ---------------------------------------------------------------------------
# CHAPTER 8: DEPLOYMENT AND DEMONSTRATION STATUS
# ---------------------------------------------------------------------------
add_h1("8. Deployment and Demonstration Status")

add_h2("8.1 FastAPI Application Execution")
doc.add_paragraph(
    "The TestForge backend runs as an asynchronous FastAPI application on http://127.0.0.1:8000/. It is launched via the single-command script ./start_testforge.sh."
)

add_h2("8.2 Frontend Availability & Real-Time Monitoring")
doc.add_paragraph(
    "The single-page web cockpit connects directly to the backend REST API and WebSocket event hub, displaying real-time agent wiretaps, AST unified diffs, and persistent checkpoint controls."
)

add_h2("8.3 API Health Verification")
doc.add_paragraph(
    "Backend health and readiness are verified via standard HTTP probes:\n"
    "• GET /healthz: returns HTTP 200 with service version 2.0.0 and uptime.\n"
    "• GET /readyz: returns HTTP 200 verifying AST mutator, blackboard, sandbox storage, and SQLite persistence."
)

add_h2("8.4 A2A Agent Discovery Endpoint")
doc.add_paragraph(
    "The official A2A discovery card is published at http://127.0.0.1:8000/.well-known/agent.json, describing skills (unit-test-generation, mutation-critique, hardening-workflow) and JSON-RPC 2.0 endpoints."
)

add_h2("8.5 Docker and Container Readiness")
doc.add_paragraph(
    "The application includes a production-ready, multi-stage Dockerfile based on python:3.13-slim, configured with a non-root user (UID 10001) and health checks. Container orchestration is verified locally via docker-compose.yml. Public cloud deployment is planned for subsequent phases."
)

add_h2("8.6 Demonstration Workflow & Live Screenshots")
doc.add_paragraph(
    "Below are four authentic screenshots captured during live verification runs of the working application:"
)

# 4 Screenshots
add_figure("docs/WIP_REPORT/assets/fresh_01_homepage.png", "Figure 3: TestForge Unified Application Dashboard and System Health Overview (Captured live: 2026-11-02 02:29).", width=Inches(5.5))
add_figure("docs/WIP_REPORT/assets/fresh_02_discount_hardened.png", "Figure 4: Automated Test Generation and Mutation Testing Terminal KPI Results for discount.py (89.5% Mutation Score, 17 Killed, 2 Survived, 100% Statement Coverage; Captured live: 2026-11-02 02:30).", width=Inches(5.5))
add_figure("docs/WIP_REPORT/assets/figure5_logistics_hardened_kpi.png", "Figure 5: Enterprise Multi-Callable Hardening Terminal Results for uploaded_logistics_engine.py (64 Tests, 176 Mutants Killed, 68.22% Raw Score, 90.15% Coverage; Captured: 2026-10-31 14:55).", width=Inches(5.5))
add_figure("docs/WIP_REPORT/assets/fresh_03_checkpoints_timeline.png", "Figure 6: Persistent Blackboard Checkpoint Timeline in SQLite showing Atomic Revisions and Semantic Diff Controls (Captured live: 2026-11-02 02:30).", width=Inches(5.5))

# ---------------------------------------------------------------------------
# CHAPTER 9: DEVELOPMENT PROGRESS AND FUTURE WORK
# ---------------------------------------------------------------------------
add_h1("9. Development Progress and Future Work")

add_h2("9.1 Development Phases Completed")
doc.add_paragraph(
    "• Phase 1: Initial Baseline Establishment: Measured pre-improvement mutation baseline (5.26% on discount, 3.10% on logistics) and identified exception-swallowing defects.\n"
    "• Phase 2: Intelligent Multi-Callable Test Generation: Implemented IntelligentASTSynthesizer, boundary value analysis, negative guard testing, and AST scope bugfix.\n"
    "• Phase 3: Independent Validation: Executed standalone isolated reproduction verifying 100% metric determinism and cryptographic suite provenance.\n"
    "• Phase 4: Live Workflow Readiness: Automated 16-step end-to-end browser verification, error recovery testing, and SQLite database integrity auditing.\n"
    "• Phase 5: Academic VIVA Preparation: Assembled 12 comprehensive defense guides, 100-question technical bank, and architecture blueprints."
)

add_h2("9.2 Major Implementation Milestones")
doc.add_paragraph(
    "1. Full regression suite expansion to 542 passed tests with 0 failures.\n"
    "2. Decoupled multi-partition Blackboard architecture with atomic SQLite checkpointing (1,104 snapshots).\n"
    "3. FastMCP tool server implementation and A2A Protocol v0.3.0 agent card publication.\n"
    "4. Multi-callable test generation lifting mutation score from 3.10% to 68.22% (75.21% adjusted) on enterprise freight code."
)

add_h2("9.3 Current Implementation Status")
doc.add_paragraph(
    "TestForge is an operational prototype running natively on macOS ARM64 and containerized under Docker. 11 of 12 academic rubric requirements are fully implemented and verified; deployment readiness is verified locally with public cloud deployment planned."
)

add_h2("9.4 Remaining Work")
doc.add_paragraph(
    "• Public Cloud CI/CD Pipeline: Automated deployment to Google Cloud Run with container vulnerability scanning.\n"
    "• Expanded Mutation Operator Library: Adding statement deletion, exception handler removal, and type mutation operators."
)

add_h2("9.5 Future Improvements")
doc.add_paragraph(
    "• Dynamic Symbolic Execution (Concolic Testing): Coupling AST analysis with Z3 SMT constraint solving to automatically generate path-divergent inputs for deeply nested guards.\n"
    "• Inter-Module Call Graph Analysis: Multi-file dependency traversal for enterprise monolith testing."
)

add_h2("9.6 Expected Final Project Outcome")
doc.add_paragraph(
    "The final outcome will be a self-contained, enterprise-grade autonomous test hardening system that integrates seamlessly into GitHub Actions workflows, guaranteeing that software repositories achieve rigorous defect verification rather than superficial line coverage."
)

# ---------------------------------------------------------------------------
# CHAPTER 10: CONCLUSION
# ---------------------------------------------------------------------------
add_h1("10. Conclusion")

add_h2("10.1 Summary of Work Completed")
doc.add_paragraph(
    "TestForge demonstrates the efficacy of autonomous multi-agent collaboration in solving the problem of illusory test coverage. By coupling Google ADK generative synthesis, CrewAI adversarial critique, AST boundary analysis, and FastMCP standardized tooling over a thread-safe Blackboard context, TestForge systematically elevates mutation effectiveness from initial baselines of 3%–5% to 68%–89% raw (75%–94% adjusted) across real-world benchmarks."
)

add_h2("10.2 Achievement of Project Objectives")
doc.add_paragraph(
    "All core academic and engineering objectives have been achieved: complete 100% callable discovery, value-aware assertion synthesis, tamper-evident cryptographic provenance, defense-in-depth security guardrails, and full 542-test passing regression stability."
)

add_h2("10.3 Overall WIP Status")
doc.add_paragraph(
    "The project stands in an Exemplary Academic Work in Progress state, fully verified and ready for formal academic evaluation and defense."
)

# ---------------------------------------------------------------------------
# REFERENCES
# ---------------------------------------------------------------------------
add_h1("References")
refs = [
    "Jia, Y., & Harman, M. (2011). An analysis and survey of the development of mutation testing. IEEE Transactions on Software Engineering, 37(5), 649-678.",
    "Offutt, A. J., & Untch, R. H. (2001). Mutation 2000: Uniting the orthogonal. Mutation Testing for the New Century, 34-44.",
    "CrewAI Inc. (2024). CrewAI: Framework for Orchestrating Autonomous AI Agents. https://crewai.com",
    "Google Cloud. (2024). Google Agent Development Kit (ADK) & Google GenAI SDK. https://cloud.google.com",
    "Model Context Protocol Core Working Group. (2024). Model Context Protocol (MCP) Specification v1.0. Anthropic.",
    "A2A Inter-Agent Protocol Working Group. (2024). Agent-to-Agent (A2A) Discovery and Messaging Protocol v0.3.0."
]
for idx, r in enumerate(refs):
    p = doc.add_paragraph()
    p.paragraph_format.left_indent = Inches(0.25)
    p.paragraph_format.first_line_indent = Inches(-0.25)
    p.add_run(f"[{idx+1}] {r}")

# ---------------------------------------------------------------------------
# APPENDICES
# ---------------------------------------------------------------------------
doc.add_page_break()
add_h1("Appendices")

add_h2("Appendix A: Key REST & WebSocket API Endpoints")
api_tbl = doc.add_table(rows=12, cols=4)
api_tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
set_tbl_borders(api_tbl)

api_headers = ["Method", "Endpoint Path", "Handler Function", "Description"]
for col_idx, h in enumerate(api_headers):
    c = api_tbl.cell(0, col_idx)
    c.text = h
    style_cell(c, fill_hex="EAEAEA", bold=True, font_size=8)

api_rows = [
    ("GET", "/healthz", "healthz()", "Liveness probe returning server health and version."),
    ("GET", "/readyz", "readyz()", "Readiness probe verifying AST mutator, blackboard, and SQLite."),
    ("GET", "/.well-known/agent.json", "get_a2a_agent_card()", "Official A2A Protocol v0.3.0 JSON-LD AgentCard."),
    ("POST", "/api/harden/start", "start_hardening_job()", "Initiates asynchronous multi-agent test hardening lifecycle."),
    ("GET", "/api/harden/status/{job_id}", "get_hardening_job_status()", "Polls lifecycle stage, metrics, mutants, and generated suite."),
    ("POST", "/api/harden/cancel/{job_id}", "cancel_hardening_job()", "Cooperatively terminates active hardening job."),
    ("GET", "/api/checkpoints/list", "list_checkpoints()", "Retrieves paginated SQLite checkpoint records."),
    ("POST", "/api/checkpoints/diff", "diff_checkpoints_endpoint()", "Computes semantic diff between any two SQLite checkpoints."),
    ("GET", "/api/mcp/status", "get_mcp_status()", "Inspects active FastMCP tool servers and registered tools."),
    ("POST", "/api/mcp/test", "run_mcp_test_action()", "Executes standardized FastMCP tool test call."),
    ("WS", "/api/ws/events", "websocket_events_endpoint()", "Real-time event stream broadcasting lifecycle state changes.")
]

for row_idx, r in enumerate(api_rows):
    for col_idx, val in enumerate(r):
        c = api_tbl.cell(row_idx + 1, col_idx)
        c.text = val
        fill = "F6F6F8" if (row_idx % 2 == 1) else None
        style_cell(c, fill_hex=fill, font_size=7.5)

add_h2("Appendix B: Discovered Callables & Mutation Operator Distribution")
doc.add_paragraph(
    "In samples/uploaded_logistics_engine.py, TestForge discovered and tested 100% of the following 10 callables:\n"
    "1. WarehouseInventory.get_available_stock (Instance Method)\n"
    "2. WarehouseInventory.reserve_stock (Instance Method)\n"
    "3. WarehouseInventory.release_stock (Instance Method)\n"
    "4. calculate_item_discount (Module Function)\n"
    "5. estimate_freight_cost (Module Function)\n"
    "6. classify_shipping_priority (Module Function)\n"
    "7. apply_customs_duty (Module Function)\n"
    "8. calculate_sla_deadline_hours (Module Function)\n"
    "9. generate_tracking_checksum (Module Function)\n"
    "10. process_full_dispatch_order (Module Function)\n\n"
    "Mutant Distribution Across 9 Operator Families: Comparison Operator (COMP_OP): 64; Boundary Swap (BOUNDARY_SWAP): 48; "
    "Off-by-One (OFF_BY_ONE): 38; Arithmetic Operator (ARITH_OP): 34; Condition Inversion (COND_INV): 28; Constant Value (CONST_VAL): 22; "
    "Logical Connector (LOGICAL_CONN): 14; Return Value (RET_VAL): 6; Exception Swap (EXC_SWAP): 4. Total: 258 Mutants."
)

add_h2("Appendix C: Project Setup & Native Execution Runbook")
doc.add_paragraph(
    "# 1. Activate verified virtual environment\n"
    "source .venv-release/bin/activate\n\n"
    "# 2. Launch TestForge application server\n"
    "./start_testforge.sh\n"
    "# Server active at http://127.0.0.1:8000/\n\n"
    "# 3. Execute full regression test suite\n"
    "pytest tests/ -v"
)

add_h2("Appendix D: Automated Pytest Regression Suite Summary")
doc.add_paragraph(
    "The test suite consists of 48 test modules in tests/ covering: Blackboard persistence (66 tests), Security & SSRF defenses (98 tests), "
    "A2A Protocol (36 tests), MCP Tooling (50 tests), Frameworks (27 tests), Agentic Pipeline (34 tests), Cancellation & Lifecycle (32 tests), "
    "AST Scope Extraction (12 tests), and Benchmarking (18 tests). Full execution: 542 passed, 0 failed in 277.12 seconds."
)

doc.save(DOCX_OUT)
print(f"DOCX successfully generated and saved to {DOCX_OUT}")
