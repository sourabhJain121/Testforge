import os
import sys
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_ALIGN_VERTICAL
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn
from playwright.sync_api import sync_playwright
from markdown_it import MarkdownIt

import report_data as rd

OUT_DIR = "/Users/sourabh/TestForge/docs/DELIVERABLES"
ASSETS_DIR = "/Users/sourabh/TestForge/docs/screenshots/report_assets"
OUT_MD = os.path.join(OUT_DIR, "TestForge_CSE3101_Final_Report.md")
OUT_DOCX = os.path.join(OUT_DIR, "TestForge_CSE3101_Final_Report.docx")
OUT_PDF = os.path.join(OUT_DIR, "TestForge_CSE3101_Final_Report.pdf")
OUT_HTML = "/tmp/testforge_report_render.html"

os.makedirs(OUT_DIR, exist_ok=True)

# XML helpers for python-docx styling
def set_cell_background(cell, fill_hex):
    tcPr = cell._tc.get_or_add_tcPr()
    shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
    tcPr.append(shd)

def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
    tcPr = cell._tc.get_or_add_tcPr()
    tcMar = parse_xml(f'<w:tcMar {nsdecls("w")}><w:top w:w="{top}" w:type="dxa"/><w:bottom w:w="{bottom}" w:type="dxa"/><w:left w:w="{left}" w:type="dxa"/><w:right w:w="{right}" w:type="dxa"/></w:tcMar>')
    tcPr.append(tcMar)

def set_table_borders(table, color="D3D3D3", sz="4", val="single"):
    tblPr = table._tbl.tblPr
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        f'<w:top w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:bottom w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:left w:val="none"/>'
        f'<w:right w:val="none"/>'
        f'<w:insideH w:val="{val}" w:sz="{sz}" w:space="0" w:color="{color}"/>'
        f'<w:insideV w:val="none"/>'
        f'</w:tblBorders>'
    )
    tblPr.append(borders)

def style_table(table, header_bg="1E3A8A", alt_bg="F8FAFC"):
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    set_table_borders(table, color="D1D5DB", sz="4", val="single")
    for i, row in enumerate(table.rows):
        for cell in row.cells:
            cell.vertical_alignment = WD_ALIGN_VERTICAL.CENTER
            set_cell_margins(cell, top=80, bottom=80, left=120, right=120)
            if i == 0:
                set_cell_background(cell, header_bg)
                for p in cell.paragraphs:
                    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                    for r in p.runs:
                        r.font.bold = True
                        r.font.color.rgb = RGBColor(255, 255, 255)
                        r.font.size = Pt(9.5)
            else:
                if i % 2 == 1:
                    set_cell_background(cell, alt_bg)
                for p in cell.paragraphs:
                    for r in p.runs:
                        r.font.size = Pt(9)
                        r.font.color.rgb = RGBColor(30, 41, 59)

# ==========================================
# 1. BUILD CLEAN MARKDOWN REPORT
# ==========================================
def build_markdown():
    print("[1/3] Generating Markdown report:", OUT_MD)
    md = []
    
    # Title Page
    md.append(f"<div style=\"text-align: center; margin-bottom: 20px;\"><img src=\"{ASSETS_DIR}/bml_logo.png\" width=\"140\" style=\"display: inline-block;\"></div>")
    md.append("# Project Report")
    md.append("## Course: Agentic AI (CSE3101)")
    md.append(f"# {rd.TITLE}")
    md.append("### By:\n" + "\n".join([f"- **{s['name']}** — `{s['roll']}`" for s in rd.STUDENTS]))
    md.append(f"**{rd.DEPARTMENT}**  \n**{rd.SCHOOL}**  \n**{rd.UNIVERSITY}**  \n**{rd.DATE_STR}**")
    md.append("<div style=\"page-break-after: always;\"></div>")
    
    # Declaration
    md.append("## Declaration by the Candidates")
    md.append(f"<div style=\"text-align: justify;\">\n\n{rd.DECLARATION_TEXT}\n\n</div>")
    decl_tbl = [
        "| Candidate Name | Enrollment Number | Signature Block |",
        "| :--- | :---: | :---: |"
    ]
    for s in rd.STUDENTS:
        decl_tbl.append(f"| **{s['name']}** | `{s['roll']}` | *Signed* |")
    md.append("\n".join(decl_tbl))
    md.append(f"**Place:** {rd.UNIVERSITY}  \n**Date:** {rd.DATE_STR}")
    md.append("<div style=\"page-break-after: always;\"></div>")
    
    # Table of Contents
    md.append("## Table of Contents")
    toc_tbl = [
        "| Section | Page Number |",
        "| :--- | :---: |"
    ]
    for title, pg in rd.TOC_ITEMS:
        clean_title = title.replace('    ', '&nbsp;&nbsp;&nbsp;&nbsp;')
        toc_tbl.append(f"| {clean_title} | {pg} |")
    md.append("\n".join(toc_tbl))
    md.append("<div style=\"page-break-after: always;\"></div>")
    
    # Section 1: Introduction
    md.append("## 1. Introduction")
    for p in rd.INTRO_PARAS:
        md.append(f"<div style=\"text-align: justify;\">\n\n{p}\n\n</div>")
        
    # Section 2: Problem Statement
    md.append("## 2. Problem Statement")
    for p in rd.PROBLEM_PARAS:
        md.append(f"<div style=\"text-align: justify;\">\n\n{p}\n\n</div>")
        
    # Section 3: Literature Review
    md.append("## 3. Literature Review")
    md.append("<div style=\"text-align: justify;\">\n\n"
              "To establish the competitive landscape and identify explicit scientific gaps, "
              "we conducted an exhaustive comparative review of seven representative academic and industrial testing systems. "
              "Table 3.1 synthesizes the core technical attributes of these tools alongside TestForge.\n\n</div>")
    md.append("### Table 3.1: Systematic Comparison of Automated Testing and Mutation Systems")
    lit_tbl = [
        "| System | Underlying Paradigm | Target Language | Automated Test Gen | Mutation Guidance | Multi-Agent MAS | Stateful Planning | Suite Minimization |",
        "| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: |"
    ]
    for row in rd.LIT_REVIEW_TABLE:
        lit_tbl.append(f"| **{row['tool']}** | {row['paradigm']} | {row['language']} | {row['test_gen']} | {row['mutation_guided']} | {row['agentic']} | {row['stateful_plan']} | {row['minimization']} |")
    md.append("\n".join(lit_tbl))
    
    md.append("### Explicit Research Gaps Identified in Literature")
    for g in rd.LIT_GAPS:
        md.append(f"<div style=\"text-align: justify;\">\n\n{g}\n\n</div>")
        
    # Section 4: Requirements for MAS
    md.append("## 4. Requirements for Multi-Agent System (MAS)")
    md.append("<div style=\"text-align: justify;\">\n\n"
              "Every agent in the TestForge architecture exists to directly solve an empirical requirement mapped "
              "from our problem statement and the literature gaps identified in Section 3. "
              "Table 4.1 establishes full end-to-end traceability across our eight specialized agents.\n\n</div>")
    md.append("### Table 4.1: Traceability Matrix Mapping Requirements to Agents")
    req_tbl = [
        "| Requirement ID | Functional Capability & Technical Constraint | Mapped Problem / Literature Gap | Assigned Agent Role |",
        "| :---: | :--- | :--- | :--- |"
    ]
    for r in rd.MAS_REQ_TABLE:
        req_tbl.append(f"| **{r['req_id']}** | {r['description']} | {r['mapped_gap']} | **{r['agent']}** |")
    md.append("\n".join(req_tbl))
    
    # Section 5: Methodology
    md.append("## 5. Methodology")
    md.append("### 5.1 Agent Identification and Role Decomposition")
    for p in rd.METHODOLOGY_PARAS_51:
        md.append(f"<div style=\"text-align: justify;\">\n\n{p}\n\n</div>")
        
    md.append("### 5.2 Orchestration & Execution Strategy (6-Stage FSM)")
    for p in rd.METHODOLOGY_PARAS_52:
        md.append(f"<div style=\"text-align: justify;\">\n\n{p}\n\n</div>")
    md.append(f"![Figure 5.0: TestForge Step-by-Step Multi-Agent Pipeline & Convergence Stop-Rules]({ASSETS_DIR}/pipeline_flow_diagram.png)")
    md.append("*Figure 5.0: TestForge Step-by-Step Multi-Agent Pipeline & Convergence Stop-Rules (Modeled on OptiFlow-X Section 5.3.1).*")

    md.append("### 5.3 Architecture Evaluation")
    md.append("<div style=\"text-align: justify;\">\n\n"
              "Before settling on the Hierarchical Blackboard topology, we rigorously evaluated three candidate multi-agent coordination architectures: "
              "(1) a Sequential Pipeline, (2) a Peer-to-Peer (P2P) Swarm, and (3) our Hierarchical Supervisor with Centralized Blackboard. "
              "Table 5.1 details the empirical and heuristic trade-offs across these designs.\n\n</div>")
    md.append("### Table 5.1: Comparative Evaluation of Multi-Agent Coordination Topologies")
    arch_tbl = [
        "| Evaluation Dimension | Sequential Pipeline | Peer-to-Peer (P2P) Swarm | Hierarchical Blackboard (TestForge) |",
        "| :--- | :--- | :--- | :--- |"
    ]
    for row in rd.ARCH_EVAL_TABLE:
        arch_tbl.append(f"| **{row['criterion']}** | {row['sequential']} | {row['p2p']} | **{row['hierarchical']}** |")
    md.append("\n".join(arch_tbl))
    md.append(f"![Figure 5.1: TestForge Hierarchical Blackboard Architecture]({ASSETS_DIR}/architecture_diagram.png)")
    md.append("*Figure 5.1: TestForge Multi-Agent Hierarchical Blackboard Architecture combining Google ADK and CrewAI.*")

    md.append("### 5.4 Agent-Tool Communication & FastMCP JSON-RPC Protocol")
    md.append("<div style=\"text-align: justify;\">\n\n"
              "TestForge strictly separates high-level agent reasoning from deterministic low-level execution using the Model Context Protocol (MCP). "
              "We implemented testforge/mcp_server.py as a standardized FastMCP stdio server exposing four specialized tools. "
              "Communication occurs over standard input/output streams via JSON-RPC 2.0 messages, ensuring zero open network ports and complete operating system isolation.\n\n</div>")
    md.append("### Table 5.2: FastMCP 4-Tool Specification")
    mcp_tbl = [
        "| Tool Name | Typed Input Signature | Typed Output Signature | Architectural Purpose |",
        "| :--- | :--- | :--- | :--- |"
    ]
    for t in rd.FASTMCP_TOOLS_TABLE:
        mcp_tbl.append(f"| `{t['name']}` | `{t['inputs']}` | `{t['outputs']}` | {t['purpose']} |")
    md.append("\n".join(mcp_tbl))
    md.append(f"![Figure 5.2: FastMCP Agent-Tool Architecture]({ASSETS_DIR}/fastmcp_agent_tool_diagram.png)")
    md.append("*Figure 5.2: FastMCP stdio JSON-RPC tool dispatch architecture.*")

    md.append("### 5.5 Messaging Patterns & A2A Communication Protocol")
    md.append("<div style=\"text-align: justify;\">\n\n"
              "Agent-to-Agent (A2A) communication follows formal communicative acts inspired by FIPA-ACL (REQUEST, INFORM, AGREE, REFUSE, FAILURE). "
              "All messages are encapsulated in strongly-typed Pydantic envelopes (A2AMessage in testforge/a2a.py) carrying immutable correlation IDs, "
              "sender/recipient identities, and W3C trace contexts. External agents discover TestForge capabilities via the dynamic GET /.well-known/agent-card.json "
              "endpoint conforming to A2A specification v0.3.0.\n\n</div>")

    md.append("### 5.6 3-Tier MAS Security Architecture")
    for p in rd.SECURITY_3TIER_PARAS:
        md.append(f"<div style=\"text-align: justify;\">\n\n{p}\n\n</div>")
    md.append(f"![Figure 5.3: 3-Tier Security Architecture]({ASSETS_DIR}/security_3tier_diagram.png)")
    md.append("*Figure 5.3: TestForge 3-Tier Multi-Agent Security & Sandboxing Framework.*")

    md.append("### 5.7 Stateful Call-Chain Planning & Sequence Synthesis")
    for p in rd.STATEFUL_PLANNING_PARAS:
        md.append(f"<div style=\"text-align: justify;\">\n\n{p}\n\n</div>")

    md.append("### 5.8 Test Suite Minimization via Submodular Greedy Set Cover")
    for p in rd.MINIMIZATION_PARAS:
        md.append(f"<div style=\"text-align: justify;\">\n\n{p}\n\n</div>")

    md.append("### 5.9 Validation Strategy & 60-Run Factorial Matrix")
    md.append("<div style=\"text-align: justify;\">\n\n"
              "To rigorously validate agent decision-making, we designed a full factorial experimental matrix across three prompt architectures "
              "(Zero-Shot Baseline, Few-Shot Chain-of-Thought, and Adversarial Critic-guided) and four distinct developer personas "
              "(Junior Developer, Skeptical QA Architect, Senior Principal Architect, and Adversarial Fuzz Tester). Each combination was executed "
              "across 5 independent trials (60 total experimental runs) on macOS Apple M2 Pro / Python 3.13, evaluating Pass@1 rate, mutation score, "
              "and the correlation between the CrewAI Critic LLM-as-judge scores and ground-truth subprocess execution results.\n\n</div>")

    # Section 6: Technology Stack
    md.append("## 6. Technology Stack")
    md.append("<div style=\"text-align: justify;\">\n\n"
              "TestForge was constructed using an enterprise-grade, dual-framework Python technology stack. "
              "Table 6.1 enumerates each layer of the architecture, the specific technologies employed, and their exact functional roles.\n\n</div>")
    md.append("### Table 6.1: TestForge Comprehensive Technology Stack")
    tech_tbl = [
        "| Architectural Tier | Technology & Version | Architectural Role & Justification |",
        "| :--- | :--- | :--- |"
    ]
    for t in rd.TECH_STACK_TABLE:
        tech_tbl.append(f"| **{t['category']}** | {t['technologies']} | {t['role']} |")
    md.append("\n".join(tech_tbl))

    # Section 7: Experimental Results
    md.append("## 7. Experimental Results")
    md.append("### 7.1 Canonical Target Benchmark Suite")
    md.append("<div style=\"text-align: justify;\">\n\n"
              "We evaluated TestForge across four canonical Python benchmark targets representing distinct software engineering paradigms: "
              "(1) samples/discount.py (relational boundary & pricing rules), (2) samples/order_fsm.py (finite state machine transition logic), "
              "(3) samples/lru_cache.py (pointer graph & stateful cache eviction), and (4) samples/stats_calculator.py (floating-point statistics). "
              "Table 7.1 reports the verified empirical performance.\n\n</div>")
    md.append("### Table 7.1: TestForge Benchmark Performance Across 4 Canonical Targets")
    bench_tbl = [
        "| Target Module | Domain & Behavioral Complexity | Developer Baseline MS | TestForge Raw MS | Adjusted MS | Mutants Killed | Pass@1 Rate | Final Test Count |",
        "| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: |"
    ]
    for b in rd.BENCHMARK_TABLE:
        bench_tbl.append(f"| `{b['target']}` | {b['description']} | {b['baseline_ms']} | **{b['testforge_raw_ms']}** | **{b['testforge_adj_ms']}** | {b['mutants_killed']} | {b['pass_rate']} | {b['generated_tests']} |")
    md.append("\n".join(bench_tbl))

    md.append("### 7.2 Stateful Call-Chain Planning Impact on Pointer Graphs")
    md.append("<div style=\"text-align: justify;\">\n\n"
              "Table 7.2 presents the ablation results on samples/lru_cache.py, illustrating the necessity of Phase-3 Stateful Call-Chain Planning. "
              "Unguided generation stalled at 30.95% MS because it could not trigger capacity evictions; introducing stateful invocation sequences "
              "boosted kill efficiency to 90.48% (38 of 42 mutants killed).\n\n</div>")
    md.append("### Table 7.2: Ablation Analysis of Stateful Sequence Planning on samples/lru_cache.py")
    lru_tbl = [
        "| Hardening Phase | Synthesis Methodology | Mutants Killed | Mutation Score | Primary Failure Mode Observed |",
        "| :--- | :--- | :---: | :---: | :--- |"
    ]
    for l in rd.LRU_ABLATION_TABLE:
        lru_tbl.append(f"| **{l['phase']}** | {l['methodology']} | {l['mutants_killed']} | **{l['mutation_score']}** | {l['failure_mode']} |")
    md.append("\n".join(lru_tbl))

    md.append("### 7.3 Test Suite Compression & Kill Retention")
    md.append("<div style=\"text-align: justify;\">\n\n"
              "Table 7.3 summarizes the performance of the Test Suite Minimizer Agent across the benchmark suite. "
              "Across all targets, greedy set cover reduced aggregate test method count from 143 to 47 tests (67.1% compression) "
              "with zero regression in mutation score (100.0% kill retention).\n\n</div>")
    md.append("### Table 7.3: Greedy Set Cover Minimization Metrics")
    min_tbl = [
        "| Target Module | Raw Synthesized Tests | Minimized Tests | Test Reduction | Initial MS | Minimized MS | Kill Retention |",
        "| :--- | :---: | :---: | :---: | :---: | :---: | :---: |"
    ]
    for m in rd.MINIMIZER_TABLE:
        min_tbl.append(f"| `{m['target']}` | {m['raw_tests']} | **{m['minimized_tests']}** | **{m['compression']}** | {m['initial_ms']} | {m['minimized_ms']} | **{m['retention']}** |")
    md.append("\n".join(min_tbl))

    md.append("### 7.4 Multi-Agent Runtime Latency Breakdown")
    md.append("<div style=\"text-align: justify;\">\n\n"
              "We profiled subsystem latencies across 60 complete hardening cycles on an Apple M2 Pro processor (Table 7.4). "
              "Mean end-to-end cycle latency was 2.410 seconds. The sandboxed test runner accounted for 61.5% of total runtime due to subprocess "
              "spawning and POSIX RLIMIT enforcement, while AST analysis and Blackboard transactions required under 20 milliseconds (0.8%).\n\n</div>")
    md.append("### Table 7.4: Multi-Agent Subsystem Latency Profile")
    lat_tbl = [
        "| Subsystem / Pipeline Component | Mean Latency (Seconds) | Percentage of Total Cycle | Functional Description |",
        "| :--- | :---: | :---: | :--- |"
    ]
    for row in rd.LATENCY_BREAKDOWN_TABLE:
        lat_tbl.append(f"| **{row['subsystem']}** | {row['mean_latency']} | {row['percentage']} | {row['notes']} |")
    md.append("\n".join(lat_tbl))

    md.append("### 7.5 Factorial Persona Evaluation & Prompt Ablations")
    md.append("<div style=\"text-align: justify;\">\n\n"
              "Table 7.5 displays the 60-run factorial experiment results. Across all developer personas, the Adversarial Critic-guided prompt "
              "substantially outperformed Zero-Shot and Chain-of-Thought prompts, achieving up to 93.55% mutation score under the Senior Principal Architect persona. "
              "Furthermore, all 60 runs achieved 100% Pass@1 on unmutated base code.\n\n</div>")
    md.append("### Table 7.5: 60-Run Factorial Prompt & Persona Performance Matrix")
    fac_tbl = [
        "| Developer Persona | Zero-Shot MS | Few-Shot CoT MS | Adversarial Critic-Guided MS | Base Code Pass@1 Rate |",
        "| :--- | :---: | :---: | :---: | :---: |"
    ]
    for f in rd.FACTORIAL_RESULTS_TABLE:
        fac_tbl.append(f"| **{f['persona']}** | {f['zero_shot_ms']} | {f['cot_ms']} | **{f['critic_guided_ms']}** | **{f['pass_at_1']}** |")
    md.append("\n".join(fac_tbl))

    md.append("### 7.6 Empirical Defect Analysis: DEF-022 Clean Preflight Guard")
    md.append("<div style=\"text-align: justify;\">\n\n"
              "During Phase-2 development auditing, we discovered Defect DEF-022: synthesized test suites containing assertion syntax errors "
              "or incorrect parameter counts were being erroneously credited with mutant kills because pytest exited with code 1. "
              "In software testing theory, a mutant is only validly killed if the test suite passes on the original program and fails exclusively "
              "on the mutated program. To permanently rectify this defect, we implemented a mandatory clean preflight execution guard in "
              "mcp_sandbox_runner. If a candidate suite fails on unmutated code, it is immediately rejected with exit code 127 and clean_integrity: false, "
              "triggering a Blackboard rollback. Following this fix, TestForge achieved 100% verified Pass@1 integrity across all benchmark evaluations.\n\n</div>")

    md.append("### 7.7 System Telemetry and Running UI Verification")
    md.append("<div style=\"text-align: justify;\">\n\n"
              "Figures 7.1 through 7.10 illustrate the running TestForge cockpit captured live during automated Playwright verification on localhost:8000.\n\n</div>")
    for fig in rd.SCREENSHOT_FIGURES:
        md.append(f"![{fig['id']}: {fig['title']}]({ASSETS_DIR}/{fig['file']})")
        md.append(f"*{fig['id']}: {fig['title']} — {fig['description']}*")

    # Section 8: Team Responsibility Matrix
    md.append("## 8. Team Responsibility / Self-Contribution Matrix")
    md.append("<div style=\"text-align: justify;\">\n\n"
              "Table 8.1 establishes the individual project contributions of each group member across all thirteen core development and research activities.\n\n</div>")
    md.append("### Table 8.1: Complete Team Responsibility & Contribution Matrix")
    team_tbl = [
        "| Development Activity | Sourabh Jain (230584) | Shreshth Mittal (230577) |",
        "| :--- | :--- | :--- |"
    ]
    for m in rd.TEAM_MATRIX:
        team_tbl.append(f"| **{m['activity']}** | {m['sourabh']} | {m['shreshth']} |")
    md.append("\n".join(team_tbl))
    
    md.append("### Individual Contribution Summaries")
    md.append(f"**Sourabh Jain (230584):** {rd.TEAM_CONTRIBUTIONS['sourabh']}")
    md.append(f"**Shreshth Mittal (230577):** {rd.TEAM_CONTRIBUTIONS['shreshth']}")

    # Section 9: Conclusions
    md.append("## 9. Conclusions & Future Work")
    for p in rd.CONCLUSIONS_PARAS:
        md.append(f"<div style=\"text-align: justify;\">\n\n{p}\n\n</div>")

    # References
    md.append("## References")
    for r in rd.REFERENCES:
        md.append(r)

    # Appendix
    md.append("## Appendix")
    md.append("### Appendix A: FastMCP 4-Tool Registration & Schemas")
    md.append(f"```json\n{rd.APPENDIX_A_TOOLS.strip()}\n```")
    md.append("### Appendix B: A2A Agent Card Discovery Payload")
    md.append(f"```json\n{rd.APPENDIX_B_AGENT_CARD.strip()}\n```")
    md.append("### Appendix C: Verified Pytest Test Suites")
    md.append(f"```python\n{rd.APPENDIX_C_TEST_SUITES.strip()}\n```")

    content = "\n\n".join(md) + "\n"
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write(content)
    print(" -> Markdown generated successfully:", len(content), "bytes")
    return content

# ==========================================
# 2. BUILD PROFESSIONAL WORD (.DOCX) REPORT
# ==========================================
def build_docx():
    print("[2/3] Generating Word report (.docx):", OUT_DOCX)
    doc = docx.Document()
    
    # 1-inch margins
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)
        
    doc.styles['Normal'].font.name = 'Calibri'
    doc.styles['Normal'].font.size = Pt(11)
    doc.styles['Normal'].font.color.rgb = RGBColor(30, 41, 59)
    
    def add_para(text, bold_prefix=None, space_after=6, italic=False):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.line_spacing = 1.15
        p.paragraph_format.space_after = Pt(space_after)
        if bold_prefix:
            r_bold = p.add_run(bold_prefix)
            r_bold.font.bold = True
        r = p.add_run(text)
        if italic:
            r.font.italic = True
        return p

    def add_h1(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(14)
        p.paragraph_format.space_after = Pt(6)
        r = p.add_run(text)
        r.font.bold = True
        r.font.size = Pt(16)
        r.font.color.rgb = RGBColor(30, 58, 138)
        return p

    def add_h2(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(10)
        p.paragraph_format.space_after = Pt(4)
        r = p.add_run(text)
        r.font.bold = True
        r.font.size = Pt(13)
        r.font.color.rgb = RGBColor(30, 58, 138)
        return p

    def add_h3(text):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(8)
        p.paragraph_format.space_after = Pt(2)
        r = p.add_run(text)
        r.font.bold = True
        r.font.size = Pt(11.5)
        r.font.color.rgb = RGBColor(55, 65, 81)
        return p

    def add_image_box(img_name, caption):
        img_path = os.path.join(ASSETS_DIR, img_name)
        if os.path.exists(img_path):
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.space_before = Pt(8)
            p.paragraph_format.space_after = Pt(4)
            p.add_run().add_picture(img_path, width=Inches(5.5))
            
            p_cap = doc.add_paragraph()
            p_cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p_cap.paragraph_format.space_after = Pt(10)
            r = p_cap.add_run(caption)
            r.font.italic = True
            r.font.size = Pt(9.5)
            r.font.color.rgb = RGBColor(100, 116, 139)

    # PAGE 1: TITLE PAGE
    logo_path = os.path.join(ASSETS_DIR, "bml_logo.png")
    if os.path.exists(logo_path):
        p_logo = doc.add_paragraph()
        p_logo.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_logo.paragraph_format.space_after = Pt(12)
        p_logo.add_run().add_picture(logo_path, width=Inches(1.8))
        
    p_rep = doc.add_paragraph()
    p_rep.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p_rep.add_run("Project Report")
    r.font.bold = True
    r.font.size = Pt(16)
    r.font.color.rgb = RGBColor(55, 65, 81)
    
    p_course = doc.add_paragraph()
    p_course.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p_course.add_run(rd.COURSE)
    r.font.bold = True
    r.font.size = Pt(14)
    r.font.color.rgb = RGBColor(30, 58, 138)
    
    p_title = doc.add_paragraph()
    p_title.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_title.paragraph_format.space_before = Pt(18)
    p_title.paragraph_format.space_after = Pt(18)
    r = p_title.add_run(rd.TITLE)
    r.font.bold = True
    r.font.size = Pt(20)
    r.font.color.rgb = RGBColor(30, 58, 138)
    
    p_by = doc.add_paragraph()
    p_by.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_by.paragraph_format.space_before = Pt(12)
    p_by.paragraph_format.space_after = Pt(4)
    r = p_by.add_run("By")
    r.font.bold = True
    r.font.size = Pt(12)
    
    for s in rd.STUDENTS:
        p_st = doc.add_paragraph()
        p_st.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p_st.paragraph_format.space_after = Pt(2)
        r_name = p_st.add_run(s['name'] + "\n")
        r_name.font.bold = True
        r_name.font.size = Pt(12)
        r_roll = p_st.add_run(s['roll'])
        r_roll.font.size = Pt(11)
        r_roll.font.color.rgb = RGBColor(71, 85, 105)
        
    p_inst = doc.add_paragraph()
    p_inst.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p_inst.paragraph_format.space_before = Pt(36)
    inst_text = f"{rd.DEPARTMENT}\n{rd.SCHOOL}\n{rd.UNIVERSITY}\n{rd.DATE_STR}"
    r = p_inst.add_run(inst_text)
    r.font.size = Pt(11)
    r.font.color.rgb = RGBColor(71, 85, 105)
    
    doc.add_page_break()
    
    # PAGE 2: DECLARATION
    add_h1("Declaration by the Candidates")
    add_para(rd.DECLARATION_TEXT, space_after=18)
    
    table_decl = doc.add_table(rows=len(rd.STUDENTS) + 1, cols=3)
    table_decl.rows[0].cells[0].paragraphs[0].text = "Candidate Name"
    table_decl.rows[0].cells[1].paragraphs[0].text = "Enrollment Number"
    table_decl.rows[0].cells[2].paragraphs[0].text = "Signature Block"
    for i, s in enumerate(rd.STUDENTS):
        table_decl.rows[i+1].cells[0].paragraphs[0].text = s['name']
        table_decl.rows[i+1].cells[1].paragraphs[0].text = s['roll']
        table_decl.rows[i+1].cells[2].paragraphs[0].text = "Signed"
    style_table(table_decl)
    
    p_meta = doc.add_paragraph()
    p_meta.paragraph_format.space_before = Pt(24)
    r1 = p_meta.add_run(f"Place: {rd.UNIVERSITY}\n")
    r1.font.bold = True
    r2 = p_meta.add_run(f"Date: {rd.DATE_STR}")
    r2.font.bold = True
    
    doc.add_page_break()
    
    # PAGE 3: TABLE OF CONTENTS
    add_h1("Contents")
    table_toc = doc.add_table(rows=len(rd.TOC_ITEMS) + 1, cols=2)
    table_toc.rows[0].cells[0].paragraphs[0].text = "Section Title"
    table_toc.rows[0].cells[1].paragraphs[0].text = "Page No."
    for i, (title, pg) in enumerate(rd.TOC_ITEMS):
        table_toc.rows[i+1].cells[0].paragraphs[0].text = title
        table_toc.rows[i+1].cells[1].paragraphs[0].text = pg
    style_table(table_toc)
    
    doc.add_page_break()
    
    # SECTION 1
    add_h1("1. Introduction")
    for p in rd.INTRO_PARAS:
        add_para(p)
        
    # SECTION 2
    add_h1("2. Problem Statement")
    for p in rd.PROBLEM_PARAS:
        add_para(p)
        
    # SECTION 3
    add_h1("3. Literature Review")
    add_para("To establish the competitive landscape and identify explicit scientific gaps, "
             "we conducted an exhaustive comparative review of seven representative academic and industrial testing systems. "
             "Table 3.1 synthesizes the core technical attributes of these tools alongside TestForge.")
    
    add_h3("Table 3.1: Systematic Comparison of Automated Testing and Mutation Systems")
    table_lit = doc.add_table(rows=len(rd.LIT_REVIEW_TABLE) + 1, cols=8)
    headers_lit = ["System", "Paradigm", "Language", "Test Gen", "Mutant Guide", "MAS", "Stateful Plan", "Minimization"]
    for j, h in enumerate(headers_lit):
        table_lit.rows[0].cells[j].paragraphs[0].text = h
    for i, row in enumerate(rd.LIT_REVIEW_TABLE):
        table_lit.rows[i+1].cells[0].paragraphs[0].text = row["tool"]
        table_lit.rows[i+1].cells[1].paragraphs[0].text = row["paradigm"]
        table_lit.rows[i+1].cells[2].paragraphs[0].text = row["language"]
        table_lit.rows[i+1].cells[3].paragraphs[0].text = row["test_gen"]
        table_lit.rows[i+1].cells[4].paragraphs[0].text = row["mutation_guided"]
        table_lit.rows[i+1].cells[5].paragraphs[0].text = row["agentic"]
        table_lit.rows[i+1].cells[6].paragraphs[0].text = row["stateful_plan"]
        table_lit.rows[i+1].cells[7].paragraphs[0].text = row["minimization"]
    style_table(table_lit)
    
    add_h2("Explicit Research Gaps Identified in Literature")
    for g in rd.LIT_GAPS:
        add_para(g)
        
    # SECTION 4
    add_h1("4. Requirements for Multi-Agent System (MAS)")
    add_para("Every agent in the TestForge architecture exists to directly solve an empirical requirement mapped "
             "from our problem statement and the literature gaps identified in Section 3. "
             "Table 4.1 establishes full end-to-end traceability across our eight specialized agents.")
    
    add_h3("Table 4.1: Traceability Matrix Mapping Requirements to Agents")
    table_req = doc.add_table(rows=len(rd.MAS_REQ_TABLE) + 1, cols=4)
    headers_req = ["Req ID", "Functional Capability & Technical Constraint", "Mapped Problem / Literature Gap", "Assigned Agent Role"]
    for j, h in enumerate(headers_req):
        table_req.rows[0].cells[j].paragraphs[0].text = h
    for i, r in enumerate(rd.MAS_REQ_TABLE):
        table_req.rows[i+1].cells[0].paragraphs[0].text = r["req_id"]
        table_req.rows[i+1].cells[1].paragraphs[0].text = r["description"]
        table_req.rows[i+1].cells[2].paragraphs[0].text = r["mapped_gap"]
        table_req.rows[i+1].cells[3].paragraphs[0].text = r["agent"]
    style_table(table_req)
    
    # SECTION 5
    add_h1("5. Methodology")
    add_h2("5.1 Agent Identification and Role Decomposition")
    for p in rd.METHODOLOGY_PARAS_51:
        add_para(p)
        
    add_h2("5.2 Orchestration & Execution Strategy (6-Stage FSM)")
    for p in rd.METHODOLOGY_PARAS_52:
        add_para(p)
    add_image_box("pipeline_flow_diagram.png", "Figure 5.0: TestForge Step-by-Step Multi-Agent Pipeline & Convergence Stop-Rules (Modeled on OptiFlow-X Section 5.3.1).")
        
    add_h2("5.3 Architecture Evaluation")
    add_para("Before settling on the Hierarchical Blackboard topology, we rigorously evaluated three candidate multi-agent coordination architectures: "
             "(1) a Sequential Pipeline, (2) a Peer-to-Peer (P2P) Swarm, and (3) our Hierarchical Supervisor with Centralized Blackboard. "
             "Table 5.1 details the empirical and heuristic trade-offs across these designs.")
    
    add_h3("Table 5.1: Comparative Evaluation of Multi-Agent Coordination Topologies")
    table_arch = doc.add_table(rows=len(rd.ARCH_EVAL_TABLE) + 1, cols=4)
    headers_arch = ["Evaluation Dimension", "Sequential Pipeline", "Peer-to-Peer (P2P) Swarm", "Hierarchical Blackboard (TestForge)"]
    for j, h in enumerate(headers_arch):
        table_arch.rows[0].cells[j].paragraphs[0].text = h
    for i, row in enumerate(rd.ARCH_EVAL_TABLE):
        table_arch.rows[i+1].cells[0].paragraphs[0].text = row["criterion"]
        table_arch.rows[i+1].cells[1].paragraphs[0].text = row["sequential"]
        table_arch.rows[i+1].cells[2].paragraphs[0].text = row["p2p"]
        table_arch.rows[i+1].cells[3].paragraphs[0].text = row["hierarchical"]
    style_table(table_arch)
    
    add_image_box("architecture_diagram.png", "Figure 5.1: TestForge Multi-Agent Hierarchical Blackboard Architecture combining Google ADK and CrewAI.")
    
    add_h2("5.4 Agent-Tool Communication & FastMCP JSON-RPC Protocol")
    add_para("TestForge strictly separates high-level agent reasoning from deterministic low-level execution using the Model Context Protocol (MCP). "
             "We implemented testforge/mcp_server.py as a standardized FastMCP stdio server exposing four specialized tools. "
             "Communication occurs over standard input/output streams via JSON-RPC 2.0 messages, ensuring zero open network ports and complete operating system isolation.")
    
    add_h3("Table 5.2: FastMCP 4-Tool Specification")
    table_mcp = doc.add_table(rows=len(rd.FASTMCP_TOOLS_TABLE) + 1, cols=4)
    headers_mcp = ["Tool Name", "Typed Input Signature", "Typed Output Signature", "Architectural Purpose"]
    for j, h in enumerate(headers_mcp):
        table_mcp.rows[0].cells[j].paragraphs[0].text = h
    for i, t in enumerate(rd.FASTMCP_TOOLS_TABLE):
        table_mcp.rows[i+1].cells[0].paragraphs[0].text = t["name"]
        table_mcp.rows[i+1].cells[1].paragraphs[0].text = t["inputs"]
        table_mcp.rows[i+1].cells[2].paragraphs[0].text = t["outputs"]
        table_mcp.rows[i+1].cells[3].paragraphs[0].text = t["purpose"]
    style_table(table_mcp)
    
    add_image_box("fastmcp_agent_tool_diagram.png", "Figure 5.2: FastMCP stdio JSON-RPC tool dispatch architecture.")
    
    add_h2("5.5 Messaging Patterns & A2A Communication Protocol")
    add_para("Agent-to-Agent (A2A) communication follows formal communicative acts inspired by FIPA-ACL (REQUEST, INFORM, AGREE, REFUSE, FAILURE). "
             "All messages are encapsulated in strongly-typed Pydantic envelopes (A2AMessage in testforge/a2a.py) carrying immutable correlation IDs, "
             "sender/recipient identities, and W3C trace contexts. External agents discover TestForge capabilities via the dynamic GET /.well-known/agent-card.json "
             "endpoint conforming to A2A specification v0.3.0.")
    
    add_h2("5.6 3-Tier MAS Security Architecture")
    for p in rd.SECURITY_3TIER_PARAS:
        add_para(p)
    add_image_box("security_3tier_diagram.png", "Figure 5.3: TestForge 3-Tier Multi-Agent Security & Sandboxing Framework.")
    
    add_h2("5.7 Stateful Call-Chain Planning & Sequence Synthesis")
    for p in rd.STATEFUL_PLANNING_PARAS:
        add_para(p)
        
    add_h2("5.8 Test Suite Minimization via Submodular Greedy Set Cover")
    for p in rd.MINIMIZATION_PARAS:
        add_para(p)
        
    add_h2("5.9 Validation Strategy & 60-Run Factorial Matrix")
    add_para("To rigorously validate agent decision-making, we designed a full factorial experimental matrix across three prompt architectures "
             "(Zero-Shot Baseline, Few-Shot Chain-of-Thought, and Adversarial Critic-guided) and four distinct developer personas "
             "(Junior Developer, Skeptical QA Architect, Senior Principal Architect, and Adversarial Fuzz Tester). Each combination was executed "
             "across 5 independent trials (60 total experimental runs) on macOS Apple M2 Pro / Python 3.13, evaluating Pass@1 rate, mutation score, "
             "and the correlation between the CrewAI Critic LLM-as-judge scores and ground-truth subprocess execution results.")
    
    # SECTION 6
    add_h1("6. Technology Stack")
    add_para("TestForge was constructed using an enterprise-grade, dual-framework Python technology stack. "
             "Table 6.1 enumerates each layer of the architecture, the specific technologies employed, and their exact functional roles.")
    
    add_h3("Table 6.1: TestForge Comprehensive Technology Stack")
    table_tech = doc.add_table(rows=len(rd.TECH_STACK_TABLE) + 1, cols=3)
    headers_tech = ["Architectural Tier", "Technology & Version", "Architectural Role & Justification"]
    for j, h in enumerate(headers_tech):
        table_tech.rows[0].cells[j].paragraphs[0].text = h
    for i, t in enumerate(rd.TECH_STACK_TABLE):
        table_tech.rows[i+1].cells[0].paragraphs[0].text = t["category"]
        table_tech.rows[i+1].cells[1].paragraphs[0].text = t["technologies"]
        table_tech.rows[i+1].cells[2].paragraphs[0].text = t["role"]
    style_table(table_tech)
    
    # SECTION 7
    add_h1("7. Experimental Results")
    add_h2("7.1 Canonical Target Benchmark Suite")
    add_para("We evaluated TestForge across four canonical Python benchmark targets representing distinct software engineering paradigms: "
             "(1) samples/discount.py (relational boundary & pricing rules), (2) samples/order_fsm.py (finite state machine transition logic), "
             "(3) samples/lru_cache.py (pointer graph & stateful cache eviction), and (4) samples/stats_calculator.py (floating-point statistics). "
             "Table 7.1 reports the verified empirical performance.")
    
    add_h3("Table 7.1: TestForge Benchmark Performance Across 4 Canonical Targets")
    table_bench = doc.add_table(rows=len(rd.BENCHMARK_TABLE) + 1, cols=8)
    headers_bench = ["Target Module", "Domain & Complexity", "Baseline MS", "Raw MS", "Adjusted MS", "Kills", "Pass@1", "Final Tests"]
    for j, h in enumerate(headers_bench):
        table_bench.rows[0].cells[j].paragraphs[0].text = h
    for i, b in enumerate(rd.BENCHMARK_TABLE):
        table_bench.rows[i+1].cells[0].paragraphs[0].text = b["target"]
        table_bench.rows[i+1].cells[1].paragraphs[0].text = b["description"]
        table_bench.rows[i+1].cells[2].paragraphs[0].text = b["baseline_ms"]
        table_bench.rows[i+1].cells[3].paragraphs[0].text = b["testforge_raw_ms"]
        table_bench.rows[i+1].cells[4].paragraphs[0].text = b["testforge_adj_ms"]
        table_bench.rows[i+1].cells[5].paragraphs[0].text = b["mutants_killed"]
        table_bench.rows[i+1].cells[6].paragraphs[0].text = b["pass_rate"]
        table_bench.rows[i+1].cells[7].paragraphs[0].text = b["generated_tests"]
    style_table(table_bench)
    
    add_h2("7.2 Stateful Call-Chain Planning Impact on Pointer Graphs")
    add_para("Table 7.2 presents the ablation results on samples/lru_cache.py, illustrating the necessity of Phase-3 Stateful Call-Chain Planning. "
             "Unguided generation stalled at 30.95% MS because it could not trigger capacity evictions; introducing stateful invocation sequences "
             "boosted kill efficiency to 90.48% (38 of 42 mutants killed).")
    
    add_h3("Table 7.2: Ablation Analysis of Stateful Sequence Planning on samples/lru_cache.py")
    table_lru = doc.add_table(rows=len(rd.LRU_ABLATION_TABLE) + 1, cols=5)
    headers_lru = ["Hardening Phase", "Synthesis Methodology", "Mutants Killed", "Mutation Score", "Primary Failure Mode Observed"]
    for j, h in enumerate(headers_lru):
        table_lru.rows[0].cells[j].paragraphs[0].text = h
    for i, l in enumerate(rd.LRU_ABLATION_TABLE):
        table_lru.rows[i+1].cells[0].paragraphs[0].text = l["phase"]
        table_lru.rows[i+1].cells[1].paragraphs[0].text = l["methodology"]
        table_lru.rows[i+1].cells[2].paragraphs[0].text = l["mutants_killed"]
        table_lru.rows[i+1].cells[3].paragraphs[0].text = l["mutation_score"]
        table_lru.rows[i+1].cells[4].paragraphs[0].text = l["failure_mode"]
    style_table(table_lru)
    
    add_h2("7.3 Test Suite Compression & Kill Retention")
    add_para("Table 7.3 summarizes the performance of the Test Suite Minimizer Agent across the benchmark suite. "
             "Across all targets, greedy set cover reduced aggregate test method count from 143 to 47 tests (67.1% compression) "
             "with zero regression in mutation score (100.0% kill retention).")
    
    add_h3("Table 7.3: Greedy Set Cover Minimization Metrics")
    table_min = doc.add_table(rows=len(rd.MINIMIZER_TABLE) + 1, cols=7)
    headers_min = ["Target Module", "Raw Tests", "Minimized Tests", "Compression", "Initial MS", "Final MS", "Kill Retention"]
    for j, h in enumerate(headers_min):
        table_min.rows[0].cells[j].paragraphs[0].text = h
    for i, m in enumerate(rd.MINIMIZER_TABLE):
        table_min.rows[i+1].cells[0].paragraphs[0].text = m["target"]
        table_min.rows[i+1].cells[1].paragraphs[0].text = m["raw_tests"]
        table_min.rows[i+1].cells[2].paragraphs[0].text = m["minimized_tests"]
        table_min.rows[i+1].cells[3].paragraphs[0].text = m["compression"]
        table_min.rows[i+1].cells[4].paragraphs[0].text = m["initial_ms"]
        table_min.rows[i+1].cells[5].paragraphs[0].text = m["minimized_ms"]
        table_min.rows[i+1].cells[6].paragraphs[0].text = m["retention"]
    style_table(table_min)
    
    add_h2("7.4 Multi-Agent Runtime Latency Breakdown")
    add_para("We profiled subsystem latencies across 60 complete hardening cycles on an Apple M2 Pro processor (Table 7.4). "
             "Mean end-to-end cycle latency was 2.410 seconds. The sandboxed test runner accounted for 61.5% of total runtime due to subprocess "
             "spawning and POSIX RLIMIT enforcement, while AST analysis and Blackboard transactions required under 20 milliseconds (0.8%).")
    
    add_h3("Table 7.4: Multi-Agent Subsystem Latency Profile")
    table_lat = doc.add_table(rows=len(rd.LATENCY_BREAKDOWN_TABLE) + 1, cols=4)
    headers_lat = ["Subsystem / Pipeline Component", "Mean Latency", "Percentage", "Functional Description"]
    for j, h in enumerate(headers_lat):
        table_lat.rows[0].cells[j].paragraphs[0].text = h
    for i, row in enumerate(rd.LATENCY_BREAKDOWN_TABLE):
        table_lat.rows[i+1].cells[0].paragraphs[0].text = row["subsystem"]
        table_lat.rows[i+1].cells[1].paragraphs[0].text = row["mean_latency"]
        table_lat.rows[i+1].cells[2].paragraphs[0].text = row["percentage"]
        table_lat.rows[i+1].cells[3].paragraphs[0].text = row["notes"]
    style_table(table_lat)
    
    add_h2("7.5 Factorial Persona Evaluation & Prompt Ablations")
    add_para("Table 7.5 displays the 60-run factorial experiment results. Across all developer personas, the Adversarial Critic-guided prompt "
             "substantially outperformed Zero-Shot and Chain-of-Thought prompts, achieving up to 93.55% mutation score under the Senior Principal Architect persona. "
             "Furthermore, all 60 runs achieved 100% Pass@1 on unmutated base code.")
    
    add_h3("Table 7.5: 60-Run Factorial Prompt & Persona Performance Matrix")
    table_fac = doc.add_table(rows=len(rd.FACTORIAL_RESULTS_TABLE) + 1, cols=5)
    headers_fac = ["Developer Persona", "Zero-Shot MS", "Few-Shot CoT MS", "Adversarial Critic MS", "Pass@1 Rate"]
    for j, h in enumerate(headers_fac):
        table_fac.rows[0].cells[j].paragraphs[0].text = h
    for i, f in enumerate(rd.FACTORIAL_RESULTS_TABLE):
        table_fac.rows[i+1].cells[0].paragraphs[0].text = f["persona"]
        table_fac.rows[i+1].cells[1].paragraphs[0].text = f["zero_shot_ms"]
        table_fac.rows[i+1].cells[2].paragraphs[0].text = f["cot_ms"]
        table_fac.rows[i+1].cells[3].paragraphs[0].text = f["critic_guided_ms"]
        table_fac.rows[i+1].cells[4].paragraphs[0].text = f["pass_at_1"]
    style_table(table_fac)
    
    add_h2("7.6 Empirical Defect Analysis: DEF-022 Clean Preflight Guard")
    add_para("During Phase-2 development auditing, we discovered Defect DEF-022: synthesized test suites containing assertion syntax errors "
             "or incorrect parameter counts were being erroneously credited with mutant kills because pytest exited with code 1. "
             "In software testing theory, a mutant is only validly killed if the test suite passes on the original program and fails exclusively "
             "on the mutated program. To permanently rectify this defect, we implemented a mandatory clean preflight execution guard in "
             "mcp_sandbox_runner. If a candidate suite fails on unmutated code, it is immediately rejected with exit code 127 and clean_integrity: false, "
             "triggering a Blackboard rollback. Following this fix, TestForge achieved 100% verified Pass@1 integrity across all benchmark evaluations.")
    
    add_h2("7.7 System Telemetry and Running UI Verification")
    add_para("Figures 7.1 through 7.10 illustrate the running TestForge cockpit captured live during automated Playwright verification on localhost:8000.")
    for fig in rd.SCREENSHOT_FIGURES:
        add_image_box(fig["file"], f"{fig['id']}: {fig['title']} — {fig['description']}")
        
    # SECTION 8
    add_h1("8. Team Responsibility / Self-Contribution Matrix")
    add_para("Table 8.1 establishes the individual project contributions of each group member across all thirteen core development and research activities.")
    
    add_h3("Table 8.1: Complete Team Responsibility & Contribution Matrix")
    table_team = doc.add_table(rows=len(rd.TEAM_MATRIX) + 1, cols=3)
    headers_team = ["Development Activity", "Sourabh Jain (230584)", "Shreshth Mittal (230577)"]
    for j, h in enumerate(headers_team):
        table_team.rows[0].cells[j].paragraphs[0].text = h
    for i, m in enumerate(rd.TEAM_MATRIX):
        table_team.rows[i+1].cells[0].paragraphs[0].text = m["activity"]
        table_team.rows[i+1].cells[1].paragraphs[0].text = m["sourabh"]
        table_team.rows[i+1].cells[2].paragraphs[0].text = m["shreshth"]
    style_table(table_team)
    
    add_h2("Individual Contribution Summaries")
    add_para(rd.TEAM_CONTRIBUTIONS["sourabh"], bold_prefix="Sourabh Jain (230584): ")
    add_para(rd.TEAM_CONTRIBUTIONS["shreshth"], bold_prefix="Shreshth Mittal (230577): ")
    
    # SECTION 9
    add_h1("9. Conclusions & Future Work")
    for p in rd.CONCLUSIONS_PARAS:
        add_para(p)
        
    # REFERENCES
    add_h1("References")
    for r in rd.REFERENCES:
        p_ref = doc.add_paragraph()
        p_ref.paragraph_format.line_spacing = 1.15
        p_ref.paragraph_format.space_after = Pt(4)
        r_run = p_ref.add_run(r)
        r_run.font.size = Pt(9.5)
        
    # APPENDIX
    add_h1("Appendix")
    add_h2("Appendix A: FastMCP 4-Tool Registration & Schemas")
    p_app_a = doc.add_paragraph()
    p_app_a.paragraph_format.space_after = Pt(8)
    r = p_app_a.add_run(rd.APPENDIX_A_TOOLS.strip())
    r.font.name = "Courier New"
    r.font.size = Pt(8.5)
    
    add_h2("Appendix B: A2A Agent Card Discovery Payload")
    p_app_b = doc.add_paragraph()
    p_app_b.paragraph_format.space_after = Pt(8)
    r = p_app_b.add_run(rd.APPENDIX_B_AGENT_CARD.strip())
    r.font.name = "Courier New"
    r.font.size = Pt(8.5)
    
    add_h2("Appendix C: Verified Pytest Test Suites")
    p_app_c = doc.add_paragraph()
    p_app_c.paragraph_format.space_after = Pt(8)
    r = p_app_c.add_run(rd.APPENDIX_C_TEST_SUITES.strip())
    r.font.name = "Courier New"
    r.font.size = Pt(8.5)
    
    doc.save(OUT_DOCX)
    print(" -> DOCX generated successfully:", OUT_DOCX)

# ==========================================
# 3. BUILD PIXEL-PERFECT PDF VIA PLAYWRIGHT
# ==========================================
def build_pdf():
    print("[3/3] Generating PDF report via Playwright Chromium:", OUT_PDF)
    
    with open(OUT_MD, "r", encoding="utf-8") as f:
        md_text = f.read()
        
    parser = MarkdownIt('gfm-like')
    html_body = parser.render(md_text)
    
    html_doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>{rd.TITLE}</title>
<style>
  @page {{
    size: A4;
    margin: 20mm 15mm 20mm 15mm;
  }}
  body {{
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    font-size: 10pt;
    line-height: 1.45;
    color: #1e293b;
    margin: 0;
    padding: 0;
  }}
  h1 {{
    color: #1e3a8a;
    font-size: 17pt;
    font-weight: 700;
    margin-top: 22pt;
    margin-bottom: 8pt;
    page-break-after: avoid;
  }}
  h2 {{
    color: #1e3a8a;
    font-size: 13.5pt;
    font-weight: 700;
    margin-top: 16pt;
    margin-bottom: 6pt;
    page-break-after: avoid;
  }}
  h3 {{
    color: #374151;
    font-size: 11pt;
    font-weight: 600;
    margin-top: 12pt;
    margin-bottom: 4pt;
    page-break-after: avoid;
  }}
  p {{
    text-align: justify;
    text-justify: inter-word;
    margin-top: 0;
    margin-bottom: 8pt;
  }}
  div[style*="text-align: justify;"] {{
    text-align: justify !important;
    text-justify: inter-word !important;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
    margin-top: 8pt;
    margin-bottom: 12pt;
    font-size: 8.5pt;
    page-break-inside: avoid;
  }}
  th, td {{
    border: 1px solid #cbd5e1;
    padding: 5.5pt 7pt;
    text-align: left;
    vertical-align: middle;
  }}
  th {{
    background-color: #1e3a8a;
    color: #ffffff;
    font-weight: 600;
    text-align: center;
  }}
  tr:nth-child(even) td {{
    background-color: #f8fafc;
  }}
  img {{
    max-width: 95%;
    height: auto;
    display: block;
    margin: 10pt auto 4pt auto;
    border-radius: 4px;
    border: 1px solid #e2e8f0;
    box-shadow: 0 1px 3px rgba(0,0,0,0.05);
  }}
  em {{
    display: block;
    text-align: center;
    font-size: 8.5pt;
    color: #64748b;
    margin-bottom: 12pt;
  }}
  pre, code {{
    font-family: "SFMono-Regular", Consolas, "Liberation Mono", Menlo, Courier, monospace;
    font-size: 7.8pt;
    background-color: #f1f5f9;
  }}
  pre {{
    padding: 8pt;
    border-radius: 4px;
    border: 1px solid #cbd5e1;
    overflow-x: auto;
    white-space: pre-wrap;
    word-break: break-all;
    margin-bottom: 12pt;
  }}
</style>
</head>
<body>
{html_body}
</body>
</html>
"""
    with open(OUT_HTML, "w", encoding="utf-8") as f:
        f.write(html_doc)
        
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto(f"file://{OUT_HTML}", wait_until="networkidle")
        page.pdf(
            path=OUT_PDF,
            format="A4",
            print_background=True,
            margin={"top": "20mm", "bottom": "20mm", "left": "15mm", "right": "15mm"},
            display_header_footer=True,
            header_template='<div style="font-size: 8pt; font-family: -apple-system, BlinkMacSystemFont, sans-serif; color: #94a3b8; width: 100%; text-align: right; padding-right: 15mm; letter-spacing: 0.05em;">BML MUNJAL UNIVERSITY — CSE3101 AGENTIC AI FINAL REPORT</div>',
            footer_template='<div style="font-size: 8pt; font-family: -apple-system, BlinkMacSystemFont, sans-serif; color: #64748b; width: 100%; text-align: right; padding-right: 15mm;">Page <span class="pageNumber"></span> of <span class="totalPages"></span></div>'
        )
        browser.close()
    print(" -> PDF generated successfully:", OUT_PDF)

if __name__ == "__main__":
    build_markdown()
    build_docx()
    build_pdf()
    print("ALL DELIVERABLES SUCCESSFULLY REBUILT!")
