import os
import sys
import pptx
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE
from pptx.dml.color import RGBColor

ASSETS_DIR = "/Users/sourabh/TestForge/docs/screenshots/report_assets"
OUT_PPTX = "/Users/sourabh/TestForge/docs/DELIVERABLES/TestForge_CSE3101_Presentation.pptx"

# Color Palette (Dark Theme inspired by OptiFlow-X)
BG_DARK = RGBColor(15, 23, 42)        # #0F172A
CARD_BG = RGBColor(30, 41, 59)        # #1E293B
CARD_BORDER = RGBColor(51, 65, 85)    # #334155
TEXT_WHITE = RGBColor(248, 250, 252)  # #F8FAFC
TEXT_MUTED = RGBColor(148, 163, 184)  # #94A3B8
ACCENT_BLUE = RGBColor(56, 189, 248)  # #38BDF8 Cyan/Sky
ACCENT_GREEN = RGBColor(52, 211, 153) # #34D399 Emerald
ACCENT_AMBER = RGBColor(251, 191, 36) # #FBBF24 Amber
ACCENT_ROSE = RGBColor(251, 113, 133) # #FB7185 Rose

def create_deck():
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    def set_slide_background(slide, color=BG_DARK):
        background = slide.background
        fill = background.fill
        fill.solid()
        fill.fore_color.rgb = color

    def add_header(slide, category, title, subtitle):
        tb_cat = slide.shapes.add_textbox(Inches(0.8), Inches(0.4), Inches(11.7), Inches(0.35))
        tf_cat = tb_cat.text_frame
        tf_cat.word_wrap = True
        p_cat = tf_cat.paragraphs[0]
        p_cat.text = category.upper()
        p_cat.font.name = "Calibri"
        p_cat.font.size = Pt(10)
        p_cat.font.bold = True
        p_cat.font.color.rgb = ACCENT_BLUE

        tb_title = slide.shapes.add_textbox(Inches(0.8), Inches(0.7), Inches(11.7), Inches(0.55))
        tf_title = tb_title.text_frame
        tf_title.word_wrap = True
        p_title = tf_title.paragraphs[0]
        p_title.text = title
        p_title.font.name = "Calibri"
        p_title.font.size = Pt(20)
        p_title.font.bold = True
        p_title.font.color.rgb = TEXT_WHITE

        tb_sub = slide.shapes.add_textbox(Inches(0.8), Inches(1.22), Inches(11.7), Inches(0.35))
        tf_sub = tb_sub.text_frame
        tf_sub.word_wrap = True
        p_sub = tf_sub.paragraphs[0]
        p_sub.text = subtitle
        p_sub.font.name = "Calibri"
        p_sub.font.size = Pt(11)
        p_sub.font.color.rgb = TEXT_MUTED

    def add_card(slide, left, top, width, height, bg=CARD_BG, border=CARD_BORDER):
        card = slide.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, left, top, width, height)
        card.fill.solid()
        card.fill.fore_color.rgb = bg
        card.line.color.rgb = border
        card.line.width = Pt(1)
        return card

    # =========================================================================
    # SLIDE 00: TITLE SLIDE
    # =========================================================================
    s0 = prs.slides.add_slide(blank_layout)
    set_slide_background(s0)

    # University Logo
    logo_path = os.path.join(ASSETS_DIR, "bml_logo.png")
    if os.path.exists(logo_path):
        s0.shapes.add_picture(logo_path, Inches(0.8), Inches(0.8), width=Inches(1.6))

    # Title box
    tb_main = s0.shapes.add_textbox(Inches(0.8), Inches(2.0), Inches(11.7), Inches(2.4))
    tf_main = tb_main.text_frame
    tf_main.word_wrap = True
    p1 = tf_main.paragraphs[0]
    p1.text = "TESTFORGE:\nAUTONOMOUS MULTI-AGENT SYSTEM FOR MUTATION-GUIDED UNIT TEST HARDENING"
    p1.font.name = "Calibri"
    p1.font.size = Pt(25)
    p1.font.bold = True
    p1.font.color.rgb = TEXT_WHITE
    p1.line_spacing = 1.2

    p2 = tf_main.add_paragraph()
    p2.text = "Solving the Coverage-Kill Gap via Dual-Framework Multi-Agent Synthesis, Stateful Sequence Planning & Submodular Minimization"
    p2.font.name = "Calibri"
    p2.font.size = Pt(13.5)
    p2.font.color.rgb = ACCENT_BLUE
    p2.space_before = Pt(12)
    p2.line_spacing = 1.2
    p2.space_before = Pt(10)

    # Metadata cards container
    add_card(s0, Inches(0.8), Inches(4.7), Inches(5.6), Inches(2.0))
    tb_meta1 = s0.shapes.add_textbox(Inches(1.0), Inches(4.85), Inches(5.2), Inches(1.7))
    tf_m1 = tb_meta1.text_frame
    tf_m1.word_wrap = True
    p = tf_m1.paragraphs[0]
    p.text = "ACADEMIC DETAILS & EVALUATION"
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = ACCENT_GREEN
    
    p = tf_m1.add_paragraph()
    p.text = "Course: Agentic AI (CSE3101) — 7th Semester B.Tech (AY 2026-27)\nInstructor: Prof. Pranshu Tiwari\nDepartment of Computer Science & Engineering, SET\nBML Munjal University, November 2026"
    p.font.size = Pt(10)
    p.font.color.rgb = TEXT_MUTED
    p.space_before = Pt(6)

    add_card(s0, Inches(6.8), Inches(4.7), Inches(5.7), Inches(2.0))
    tb_meta2 = s0.shapes.add_textbox(Inches(7.0), Inches(4.85), Inches(5.3), Inches(1.7))
    tf_m2 = tb_meta2.text_frame
    tf_m2.word_wrap = True
    p = tf_m2.paragraphs[0]
    p.text = "SUBMITTED BY (TEAM 50/50 OWNERSHIP)"
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = ACCENT_AMBER
    
    p = tf_m2.add_paragraph()
    p.text = "• Sourabh Jain — Enrollment No: 230584\n  Google ADK Supervisor, Blackboard WAL, FastMCP Stdio, Minimizer\n• Shreshth Mittal — Enrollment No: 230577\n  CrewAI Adversarial Critic, AST Mutator, Sequence Planner, DEF-022"
    p.font.size = Pt(10)
    p.font.color.rgb = TEXT_MUTED
    p.space_before = Pt(6)

    # =========================================================================
    # SLIDE 01: 01 / PROBLEM & MOTIVATION
    # =========================================================================
    s1 = prs.slides.add_slide(blank_layout)
    set_slide_background(s1)
    add_header(s1, "01 / Problem & Motivation", "The Coverage-Kill Gap in Modern Software Testing", 
               "Why High Structural Coverage Fails to Prevent Production Regressions & What Makes MAS Essential")

    challenges = [
        ("01", "High Coverage != Bug Detection", 
         "Line and branch coverage measure executed instructions, not assertion effectiveness. 90%+ covered suites routinely kill <35% of boundary mutants, creating dangerous false confidence.",
         ACCENT_ROSE),
        ("02", "LLM Hallucinations (DEF-022)", 
         "Standard zero-shot LLMs synthesize tests with syntax errors and non-existent methods that fail on base unmutated code, falsely inflating kill counts without preflight guards.",
         ACCENT_AMBER),
        ("03", "Stateful Pointer Blindness", 
         "Single-method prompt assertions cannot trigger multi-step mutations on pointer graphs or cache eviction protocols (stalling at 30.95% MS on LRU caches).",
         ACCENT_BLUE),
        ("04", "Runaway Test Suite Bloat", 
         "Generating an individual test for every mutant explodes suite size (23+ tests for small functions), imposing prohibitive continuous integration runtime overhead.",
         ACCENT_GREEN)
    ]

    card_w = Inches(2.78)
    card_h = Inches(3.6)
    card_top = Inches(1.8)
    for i, (num, ch_title, ch_desc, col) in enumerate(challenges):
        left = Inches(0.8 + i * 2.98)
        add_card(s1, left, card_top, card_w, card_h)
        tb = s1.shapes.add_textbox(left + Inches(0.15), card_top + Inches(0.15), card_w - Inches(0.3), card_h - Inches(0.3))
        tf = tb.text_frame
        tf.word_wrap = True
        
        p = tf.paragraphs[0]
        p.text = num
        p.font.size = Pt(22)
        p.font.bold = True
        p.font.color.rgb = col
        
        p = tf.add_paragraph()
        p.text = ch_title
        p.font.size = Pt(12)
        p.font.bold = True
        p.font.color.rgb = TEXT_WHITE
        p.space_before = Pt(4)
        
        p = tf.add_paragraph()
        p.text = ch_desc
        p.font.size = Pt(9.5)
        p.font.color.rgb = TEXT_MUTED
        p.space_before = Pt(8)

    # Solution banner strip
    add_card(s1, Inches(0.8), Inches(5.65), Inches(11.7), Inches(1.3), bg=RGBColor(24, 34, 53), border=ACCENT_BLUE)
    tb_sol = s1.shapes.add_textbox(Inches(1.0), Inches(5.75), Inches(11.3), Inches(1.1))
    tf_sol = tb_sol.text_frame
    tf_sol.word_wrap = True
    p = tf_sol.paragraphs[0]
    p.text = "THE TESTFORGE AUTONOMOUS MULTI-AGENT SOLUTION:"
    p.font.size = Pt(10)
    p.font.bold = True
    p.font.color.rgb = ACCENT_BLUE

    p = tf_sol.add_paragraph()
    p.text = "• 1. AST Topology & Sequence Planner: Extracts state-mutation graphs to plan multi-step call sequences.\n" \
             "• 2. Google ADK & CrewAI Adversarial Loop: Synthesizes tests and critiques diffs with DEF-022 clean preflight gating.\n" \
             "• 3. Greedy Set Cover Minimizer: Compresses suites by 78.3% while retaining 100% of mutation kills."
    p.font.size = Pt(9.2)
    p.font.color.rgb = TEXT_WHITE
    p.space_before = Pt(4)

    # =========================================================================
    # SLIDE 02: 02 / LITERATURE REVIEW
    # =========================================================================
    s2 = prs.slides.add_slide(blank_layout)
    set_slide_background(s2)
    add_header(s2, "02 / Literature Review", "What Existing Testing Tools Solve — and What They Leave Open", 
               "Systematic Comparison Across 7 Industry and Academic Testing Paradigms")

    # Table
    table_shape = s2.shapes.add_table(8, 7, Inches(0.8), Inches(1.7), Inches(11.7), Inches(4.2))
    table = table_shape.table
    table.columns[0].width = Inches(1.8)
    table.columns[1].width = Inches(2.2)
    table.columns[2].width = Inches(1.4)
    table.columns[3].width = Inches(1.4)
    table.columns[4].width = Inches(1.5)
    table.columns[5].width = Inches(1.6)
    table.columns[6].width = Inches(1.8)

    headers = ["System", "Underlying Paradigm", "Language", "Test Gen", "Mutant Guide", "MAS & Blackboard", "Stateful Planning"]
    for j, h in enumerate(headers):
        cell = table.cell(0, j)
        cell.text = h
        cell.fill.solid()
        cell.fill.fore_color.rgb = RGBColor(30, 58, 138)
        for p in cell.text_frame.paragraphs:
            p.alignment = PP_ALIGN.CENTER
            for r in p.runs:
                r.font.size = Pt(9.5)
                r.font.bold = True
                r.font.color.rgb = TEXT_WHITE

    lit_data = [
        ("MutPy", "Static AST Mutator", "Python", "No", "Yes", "No (CLI)", "No"),
        ("Cosmic Ray", "Distributed Mutator", "Python", "No", "Yes", "No (Worker Queue)", "No"),
        ("Meta Sapienz", "Search-Based Testing", "Android/C++", "Yes (Crashes)", "Partial", "No (Genetic Alg)", "Partial (UI)"),
        ("GitHub Copilot", "Autoregressive LLM", "Multi-Lang", "Yes (Prompts)", "No", "No (Single Model)", "No"),
        ("Qodo Gen", "Context LLM Chains", "Python/JS", "Yes (Branches)", "No", "Partial (Chains)", "No"),
        ("EvoSuite", "Genetic Algorithm", "Java Bytecode", "Yes (Suites)", "Yes (Weak)", "No (Search)", "Partial"),
        ("TestForge (Ours)", "Dual-Framework MAS", "Python 3.13+", "Yes (Adversarial)", "Yes (10 AST Ops)", "Yes (ADK + CrewAI)", "Yes (Call-Chains)")
    ]

    for i, row in enumerate(lit_data):
        for j, val in enumerate(row):
            cell = table.cell(i+1, j)
            cell.text = val
            cell.fill.solid()
            if row[0] == "TestForge (Ours)":
                cell.fill.fore_color.rgb = RGBColor(30, 60, 90)
            elif i % 2 == 1:
                cell.fill.fore_color.rgb = RGBColor(20, 30, 48)
            else:
                cell.fill.fore_color.rgb = CARD_BG
            for p in cell.text_frame.paragraphs:
                p.alignment = PP_ALIGN.CENTER if j > 1 else PP_ALIGN.LEFT
                for r in p.runs:
                    r.font.size = Pt(8.5)
                    r.font.color.rgb = ACCENT_GREEN if val == "Yes" or "TestForge" in val else (TEXT_WHITE if j == 0 else TEXT_MUTED)
                    if row[0] == "TestForge (Ours)":
                        r.font.bold = True

    # Callout note below table
    add_card(s2, Inches(0.8), Inches(6.05), Inches(11.7), Inches(1.0), bg=RGBColor(24, 34, 53), border=CARD_BORDER)
    tb_gaps = s2.shapes.add_textbox(Inches(0.95), Inches(6.12), Inches(11.4), Inches(0.85))
    tf_g = tb_gaps.text_frame
    tf_g.word_wrap = True
    p = tf_g.paragraphs[0]
    p.text = "CORE LITERATURE GAPS ADDRESSED:"
    p.font.size = Pt(9.5)
    p.font.bold = True
    p.font.color.rgb = ACCENT_AMBER
    p = tf_g.add_paragraph()
    p.text = "• G1: Absence of execution feedback in LLMs | • G2: Hallucination-flakiness hazard on base unmutated code (DEF-022)\n• G3: Single-method assertion bottleneck on stateful data structures | • G4: Runaway test suite bloat and CI overhead"
    p.font.size = Pt(9)
    p.font.color.rgb = TEXT_WHITE
    p.space_before = Pt(2)

    # =========================================================================
    # SLIDE 03: 03 / AGENT REQUIREMENTS
    # =========================================================================
    s3 = prs.slides.add_slide(blank_layout)
    set_slide_background(s3)
    add_header(s3, "03 / Agent Requirements", "Requirement Traceability: Problem Statements & Gaps → Accountable Agents", 
               "Every Specialized Agent Exists to Solve an Identified Literature Gap or Structural Bottleneck")

    table_shape3 = s3.shapes.add_table(9, 4, Inches(0.8), Inches(1.7), Inches(11.7), Inches(5.1))
    t3 = table_shape3.table
    t3.columns[0].width = Inches(1.2)
    t3.columns[1].width = Inches(4.6)
    t3.columns[2].width = Inches(3.2)
    t3.columns[3].width = Inches(2.7)

    headers3 = ["Req ID", "Functional Capability & Technical Constraint", "Mapped Gap / Problem", "Assigned Agent Role"]
    for j, h in enumerate(headers3):
        cell = t3.cell(0, j)
        cell.text = h
        cell.fill.solid()
        cell.fill.fore_color.rgb = RGBColor(30, 58, 138)
        for p in cell.text_frame.paragraphs:
            p.alignment = PP_ALIGN.CENTER
            for r in p.runs:
                r.font.size = Pt(9.5)
                r.font.bold = True
                r.font.color.rgb = TEXT_WHITE

    req_rows = [
        ("REQ-01", "Extract AST structural symbols, cyclomatic complexity, and call graph blast radius", "Problem Statement & G1", "Code Intelligence Agent"),
        ("REQ-02", "Construct multi-step method call sequences & state-mutation paths for classes", "Gap 3 (Stateful Bottleneck)", "Stateful Sequence Planner"),
        ("REQ-03", "Synthesize verified AST mutants (10 operators) and classify semantic equivalents", "Problem Statement & G1", "Mutation Testing Agent"),
        ("REQ-04", "Synthesize targeted pytest unit test assertions killing surviving mutants", "Problem Statement & G1", "Unit Test Generator (Google ADK)"),
        ("REQ-05", "Conduct adversarial code critique of surviving mutants & emit boundary directives", "Gap 1 (Execution Feedback)", "Adversarial Critic (CrewAI)"),
        ("REQ-06", "Execute test suites in isolated subprocesses with RLIMIT bounds & DEF-022 preflight", "Gap 2 (Hallucination Hazard)", "Sandboxed Test Runner Agent"),
        ("REQ-07", "Minimize test suite using greedy set-cover optimization (100% kill retention)", "Gap 4 (Test Suite Bloat)", "Test Suite Minimizer Agent"),
        ("REQ-08", "Coordinate 6-stage FSM, enforce revision-controlled state, and rollback on regression", "Architecture Reliability", "Hierarchical Supervisor & Blackboard")
    ]

    for i, row in enumerate(req_rows):
        for j, val in enumerate(row):
            cell = t3.cell(i+1, j)
            cell.text = val
            cell.fill.solid()
            cell.fill.fore_color.rgb = RGBColor(20, 30, 48) if i % 2 == 1 else CARD_BG
            for p in cell.text_frame.paragraphs:
                p.alignment = PP_ALIGN.CENTER if j == 0 else PP_ALIGN.LEFT
                for r in p.runs:
                    r.font.size = Pt(8.5)
                    r.font.color.rgb = ACCENT_BLUE if j == 3 else (ACCENT_GREEN if j == 0 else TEXT_WHITE)
                    if j in (0, 3):
                        r.font.bold = True

    # =========================================================================
    # SLIDE 04: 04 / MULTI-AGENT ARCHITECTURE
    # =========================================================================
    s4 = prs.slides.add_slide(blank_layout)
    set_slide_background(s4)
    add_header(s4, "04 / Multi-Agent Architecture", "Hierarchical Supervisor & Step-by-Step Execution Pipeline", 
               "Google ADK Supervisor + CrewAI Adversarial Intelligence Over Revision-Controlled SQLite WAL Blackboard")

    arch_img = os.path.join(ASSETS_DIR, "architecture_diagram.png")
    pipe_img = os.path.join(ASSETS_DIR, "pipeline_flow_diagram.png")

    if os.path.exists(arch_img):
        s4.shapes.add_picture(arch_img, Inches(0.8), Inches(1.75), width=Inches(5.7))
    if os.path.exists(pipe_img):
        s4.shapes.add_picture(pipe_img, Inches(6.8), Inches(1.75), width=Inches(5.7))

    # Architecture key points strip below
    add_card(s4, Inches(0.8), Inches(5.9), Inches(11.7), Inches(1.2), bg=RGBColor(24, 34, 53), border=CARD_BORDER)
    tb_arch = s4.shapes.add_textbox(Inches(1.0), Inches(5.98), Inches(11.3), Inches(1.0))
    tf_a = tb_arch.text_frame
    tf_a.word_wrap = True
    p = tf_a.paragraphs[0]
    p.text = "CORE ARCHITECTURAL ATTRIBUTES & EXECUTION GUARANTEES:"
    p.font.size = Pt(9.5)
    p.font.bold = True
    p.font.color.rgb = ACCENT_BLUE

    p = tf_a.add_paragraph()
    p.text = "• Google ADK Hierarchical Supervisor: Deterministic 6-stage FSM gating (INGEST -> ANALYZE -> MUTATE -> GENERATE -> CRITIQUE -> FINALIZE).\n" \
             "• Central SQLite WAL Blackboard: PRAGMA journal_mode=WAL ensures zero-drift revision control (schema_version: 1.0.0).\n" \
             "• CrewAI Adversarial Critic: Autonomous persona reflection loops with strict convergence rules (Target >= 85%, Max 3 Iterations)."
    p.font.size = Pt(8.8)
    p.font.color.rgb = TEXT_WHITE
    p.space_before = Pt(3)

    # =========================================================================
    # SLIDE 05: 05 / ARCHITECTURE EVALUATION
    # =========================================================================
    s5 = prs.slides.add_slide(blank_layout)
    set_slide_background(s5)
    add_header(s5, "05 / Architecture Evaluation", "Why Hierarchical Blackboard Was Chosen: Evidence & Trade-offs", 
               "Empirical Comparison of Sequential Pipeline vs. Peer-to-Peer Swarm vs. Hierarchical Blackboard")

    arch_cards = [
        ("SEQUENTIAL PIPELINE", "Linear Handoffs (A -> B -> C)",
         "• Coordination Overhead: Low O(N) message passes\n• State Consistency: Brittle; susceptible to drift\n• Fault Tolerance: Single agent failure halts pipeline\n• Mean Latency: 2.840s (No parallelization)\n• Deadlock Risk: Zero\n• Verdict: Inflexible; cannot support iterative critique",
         CARD_BG, TEXT_MUTED),
        ("PEER-TO-PEER SWARM", "Decentralized Gossip / All-to-All",
         "• Coordination Overhead: Prohibitive O(N^2) chatter\n• State Consistency: Severe split-brain divergence\n• Fault Tolerance: Requires complex consensus voting\n• Mean Latency: 6.120s (Consensus overhead)\n• Deadlock Risk: High (Circular message dependencies)\n• Verdict: Expensive token burn; chaotic convergence",
         CARD_BG, ACCENT_ROSE),
        ("HIERARCHICAL BLACKBOARD (OURS)", "Supervisor + Central SQLite WAL",
         "• Coordination Overhead: Optimal O(N) centralized sync\n• State Consistency: Guaranteed atomic ACID revisioning\n• Fault Tolerance: Supervisor re-plans & rolls back\n• Mean Latency: 2.410s (Optimal caching & stdio calls)\n• Deadlock Risk: Zero (Monotonic FSM stage gating)\n• Verdict: Proven superior across speed, safety & tokens",
         RGBColor(24, 38, 60), ACCENT_GREEN)
    ]

    card_w5 = Inches(3.72)
    card_h5 = Inches(4.9)
    for i, (t_top, t_sub, body, bg_col, b_col) in enumerate(arch_cards):
        left = Inches(0.8 + i * 3.98)
        add_card(s5, left, Inches(1.8), card_w5, card_h5, bg=bg_col, border=b_col)
        tb = s5.shapes.add_textbox(left + Inches(0.2), Inches(1.95), card_w5 - Inches(0.4), card_h5 - Inches(0.4))
        tf = tb.text_frame
        tf.word_wrap = True
        
        p = tf.paragraphs[0]
        p.text = t_top
        p.font.size = Pt(13)
        p.font.bold = True
        p.font.color.rgb = b_col
        
        p = tf.add_paragraph()
        p.text = t_sub
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.color.rgb = TEXT_WHITE
        p.space_before = Pt(2)
        
        p = tf.add_paragraph()
        p.text = body
        p.font.size = Pt(9.5)
        p.font.color.rgb = TEXT_WHITE if "OURS" in t_top else TEXT_MUTED
        p.space_before = Pt(10)

    # =========================================================================
    # SLIDE 06: 06 / AGENT–TOOL COMMUNICATION
    # =========================================================================
    s6 = prs.slides.add_slide(blank_layout)
    set_slide_background(s6)
    add_header(s6, "06 / Agent–Tool Communication", "FastMCP: Controlled Agent Invocations over stdio JSON-RPC", 
               "Strict Separation of LLM Linguistic Reasoning from Deterministic Operating System Execution")

    mcp_img = os.path.join(ASSETS_DIR, "fastmcp_agent_tool_diagram.png")
    if os.path.exists(mcp_img):
        s6.shapes.add_picture(mcp_img, Inches(0.8), Inches(1.8), width=Inches(6.0))

    # 4 Tool cards on the right
    tool_cards = [
        ("1. mcp_ast_symbol_analyzer", "Inputs: source_code: str\nOutputs: symbols, complexity, branches, stateful_classes\nRole: Parses AST to extract function signatures, cyclomatic bounds, and class mutator/accessor metadata."),
        ("2. mcp_mutant_generator", "Inputs: source_code: str, max_mutants: int = 30\nOutputs: mutants: List[Dict] (id, operator, diff, line)\nRole: Synthesizes verified AST mutants across 10 mutation operators (relational, arithmetic, boundary, constant)."),
        ("3. mcp_sandbox_runner", "Inputs: test_suite_code: str, target_source: str, timeout: 3.0s\nOutputs: passed: bool, exit_code: int, clean_integrity: bool\nRole: Executes tests in isolated subprocess with RLIMIT bounds and zero-egress socket monkeypatch."),
        ("4. mcp_equivalence_classifier", "Inputs: original_source: str, mutant_source: str\nOutputs: is_equivalent: bool, confidence: float\nRole: Checks structural AST invariants to prune semantic equivalent mutants before test synthesis.")
    ]

    for i, (tool_name, tool_desc) in enumerate(tool_cards):
        top = Inches(1.8 + i * 1.25)
        add_card(s6, Inches(7.1), top, Inches(5.4), Inches(1.15))
        tb = s6.shapes.add_textbox(Inches(7.25), top + Inches(0.08), Inches(5.1), Inches(1.0))
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = tool_name
        p.font.size = Pt(10.5)
        p.font.bold = True
        p.font.color.rgb = ACCENT_BLUE
        p = tf.add_paragraph()
        p.text = tool_desc
        p.font.size = Pt(8.2)
        p.font.color.rgb = TEXT_MUTED
        p.space_before = Pt(2)

    # =========================================================================
    # SLIDE 07: 07 / AGENT-TO-AGENT MESSAGING
    # =========================================================================
    s7 = prs.slides.add_slide(blank_layout)
    set_slide_background(s7)
    add_header(s7, "07 / Agent-to-Agent Messaging", "Blackboard State Partitions & Standardized A2A Wire Protocol", 
               "Dual-Pattern Communication: In-Memory WAL State Partitions + Dynamic A2A Protocol v0.3.0 Discovery")

    # Left: Blackboard Partitions Card
    add_card(s7, Inches(0.8), Inches(1.8), Inches(5.7), Inches(4.9))
    tb_bb = s7.shapes.add_textbox(Inches(1.0), Inches(1.95), Inches(5.3), Inches(4.6))
    tf_b = tb_bb.text_frame
    tf_b.word_wrap = True
    p = tf_b.paragraphs[0]
    p.text = "BLACKBOARD SHARED STATE PARTITIONS"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = ACCENT_GREEN

    p = tf_b.add_paragraph()
    p.text = "All in-process agents coordinate via typed partitions in testforge/blackboard.py:\n" \
             "• TargetSpace: Ingested source AST, call graph, and stateful class models.\n" \
             "• PlanSpace: Ordered sequence execution plans and eviction trigger paths.\n" \
             "• SuiteSpace: Candidate test suites (v0...vk) with Pass@1 verification flags.\n" \
             "• MutantSpace: Catalogue of 10-operator mutants, kill statuses & diffs.\n" \
             "• TraceSpace: Distributed OpenTelemetry spans, latency logs & checkpoints.\n\n" \
             "Guarantees: Strict monotonic revision increment, deep-copy isolation preventing state corruption, and ACID rollback support."
    p.font.size = Pt(9.5)
    p.font.color.rgb = TEXT_MUTED
    p.space_before = Pt(8)

    # Right: A2A Protocol Card
    add_card(s7, Inches(6.8), Inches(1.8), Inches(5.7), Inches(4.9))
    tb_a2a = s7.shapes.add_textbox(Inches(7.0), Inches(1.95), Inches(5.3), Inches(4.6))
    tf_a2a = tb_a2a.text_frame
    tf_a2a.word_wrap = True
    p = tf_a2a.paragraphs[0]
    p.text = "A2A WIRE PROTOCOL & AGENT CARD (v0.3.0)"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = ACCENT_BLUE

    p = tf_a2a.add_paragraph()
    p.text = "Cross-service and inter-agent message broker in testforge/a2a.py:\n" \
             "• FIPA-ACL Communicative Acts: REQUEST, INFORM, AGREE, REFUSE, FAILURE.\n" \
             "• Strongly-Typed Envelope: A2AMessage carries correlation_id, trace_id, sender, recipient, and JSON-RPC payloads.\n" \
             "• Dynamic Agent Card Discovery: Serves GET /.well-known/agent-card.json registering agent skills:\n" \
             "   - unit-test-generation (Google ADK)\n" \
             "   - mutation-critique (CrewAI)\n" \
             "   - hardening-workflow (End-to-End Orchestrator)\n" \
             "• Preferred Transport: JSONRPC over HTTP/stdio with dual-key authentication."
    p.font.size = Pt(9.5)
    p.font.color.rgb = TEXT_MUTED
    p.space_before = Pt(8)

    # =========================================================================
    # SLIDE 08: 08 / SECURING THE MAS
    # =========================================================================
    s8 = prs.slides.add_slide(blank_layout)
    set_slide_background(s8)
    add_header(s8, "08 / Securing the MAS", "3-Tier Defense-in-Depth Security & Sandboxing Framework", 
               "Preventing Arbitrary Code Execution, Resource Exhaustion & Environment Contamination")

    sec_img = os.path.join(ASSETS_DIR, "security_3tier_diagram.png")
    if os.path.exists(sec_img):
        s8.shapes.add_picture(sec_img, Inches(0.8), Inches(1.8), width=Inches(11.7))

    # =========================================================================
    # SLIDE 09: 09 / EXPERIMENTAL DESIGN
    # =========================================================================
    s9 = prs.slides.add_slide(blank_layout)
    set_slide_background(s9)
    add_header(s9, "09 / Experimental Design", "60-Run Factorial Validation Matrix & Canonical Target Suite", 
               "Rigorous Evaluation Across 3 Prompt Styles × 4 Developer Personas × 5 Independent Trials")

    # Left: Targets Card
    add_card(s9, Inches(0.8), Inches(1.8), Inches(5.7), Inches(4.9))
    tb_t = s9.shapes.add_textbox(Inches(1.0), Inches(1.95), Inches(5.3), Inches(4.6))
    tf_t = tb_t.text_frame
    tf_t.word_wrap = True
    p = tf_t.paragraphs[0]
    p.text = "4 CANONICAL BENCHMARK TARGETS"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = ACCENT_AMBER

    p = tf_t.add_paragraph()
    p.text = "Target 1: samples/discount.py\n" \
             "• Pricing calculation engine with boolean logic & volume rules (19 mutants).\n\n" \
             "Target 2: samples/order_fsm.py\n" \
             "• Order state transition machine with guards and rollback checks (106 mutants).\n\n" \
             "Target 3: samples/lru_cache.py\n" \
             "• Stateful LRU cache data structure with doubly-linked node pointers (42 mutants).\n\n" \
             "Target 4: samples/stats_calculator.py\n" \
             "• Statistical accumulator with floating-point variance & percentiles (73 mutants)."
    p.font.size = Pt(9.5)
    p.font.color.rgb = TEXT_MUTED
    p.space_before = Pt(8)

    # Right: Factorial Card
    add_card(s9, Inches(6.8), Inches(1.8), Inches(5.7), Inches(4.9))
    tb_f = s9.shapes.add_textbox(Inches(7.0), Inches(1.95), Inches(5.3), Inches(4.6))
    tf_f = tb_f.text_frame
    tf_f.word_wrap = True
    p = tf_f.paragraphs[0]
    p.text = "3 × 4 × 5 = 60 FACTORIAL VALIDATION MATRIX"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = ACCENT_GREEN

    p = tf_f.add_paragraph()
    p.text = "3 Prompt Synthesis Paradigms:\n" \
             "• Zero-Shot Baseline (Direct function prompt)\n" \
             "• Few-Shot Chain-of-Thought (Step-by-step reasoning)\n" \
             "• Adversarial Critic-Guided (CrewAI semantic diff directives)\n\n" \
             "4 Autonomous Developer Personas:\n" \
             "• Junior Developer (Permissive happy-path assertions)\n" \
             "• Skeptical QA Architect (Boundary & threshold stress testing)\n" \
             "• Senior Principal Architect (Stateful invariants & edge conditions)\n" \
             "• Adversarial Fuzz Tester (Extreme inputs & mutation killing)\n\n" \
             "Validation Metrics: Ground-truth Pass@1 vs. LLM-as-judge score correlation."
    p.font.size = Pt(9.5)
    p.font.color.rgb = TEXT_MUTED
    p.space_before = Pt(8)

    # =========================================================================
    # SLIDE 10: 10 / VALIDATING THE MAS & RESULTS
    # =========================================================================
    s10 = prs.slides.add_slide(blank_layout)
    set_slide_background(s10)
    add_header(s10, "10 / Validating the MAS & Results", "Empirical Results: 12.0x Mutation Score Lift & 78.3% Test Minimization", 
               "Verified Quantitative Performance Across Canonical Benchmark Targets on macOS arm64 / Python 3.13")

    metrics = [
        ("77.42% / 80.37%", "Macro-Average Mutation Score", "12.0x over developer baseline (6.46%); 192 of 240 mutants killed across targets.", ACCENT_BLUE),
        ("90.48%", "Stateful Sequence Planning Lift", "samples/lru_cache.py lifted from 30.95% to 90.48% (38/42 mutants killed, 100% Pass@1).", ACCENT_GREEN),
        ("78.3%", "Greedy Set Cover Reduction", "samples/discount.py compressed from 23 to 5 tests with 100.0% kill retention.", ACCENT_AMBER),
        ("2.410s", "Mean End-to-End Latency", "61.5% sandbox execution, 18.6% ADK generator, 14.7% mutator, 4.4% critic reflection.", ACCENT_ROSE)
    ]

    for i, (m_val, m_lbl, m_desc, col) in enumerate(metrics):
        left = Inches(0.8 + i * 2.98)
        add_card(s10, left, Inches(1.8), Inches(2.78), Inches(1.8))
        tb = s10.shapes.add_textbox(left + Inches(0.1), Inches(1.88), Inches(2.58), Inches(1.6))
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = m_val
        p.font.size = Pt(20)
        p.font.bold = True
        p.font.color.rgb = col
        p = tf.add_paragraph()
        p.text = m_lbl
        p.font.size = Pt(10.5)
        p.font.bold = True
        p.font.color.rgb = TEXT_WHITE
        p.space_before = Pt(2)
        p = tf.add_paragraph()
        p.text = m_desc
        p.font.size = Pt(8.5)
        p.font.color.rgb = TEXT_MUTED
        p.space_before = Pt(4)

    # Benchmark results table below
    t10_shape = s10.shapes.add_table(5, 7, Inches(0.8), Inches(3.85), Inches(11.7), Inches(3.0))
    t10 = t10_shape.table
    t10.columns[0].width = Inches(2.2)
    t10.columns[1].width = Inches(1.6)
    t10.columns[2].width = Inches(1.6)
    t10.columns[3].width = Inches(1.6)
    t10.columns[4].width = Inches(1.5)
    t10.columns[5].width = Inches(1.6)
    t10.columns[6].width = Inches(1.6)

    h10 = ["Target Module", "Baseline MS", "TestForge Raw", "Adjusted MS", "Kills", "Pass@1 Rate", "Final Test Count"]
    for j, h in enumerate(h10):
        cell = t10.cell(0, j)
        cell.text = h
        cell.fill.solid()
        cell.fill.fore_color.rgb = RGBColor(30, 58, 138)
        for p in cell.text_frame.paragraphs:
            p.alignment = PP_ALIGN.CENTER
            for r in p.runs:
                r.font.size = Pt(9)
                r.font.bold = True
                r.font.color.rgb = TEXT_WHITE

    b_data = [
        ("samples/discount.py", "0.00%", "94.74%", "94.74%", "18 / 19", "100.0%", "5 (from 23)"),
        ("samples/order_fsm.py", "14.15%", "97.17%", "97.17%", "103 / 106", "100.0%", "16 (from 48)"),
        ("samples/lru_cache.py", "0.00%", "90.48%", "90.48%", "38 / 42", "100.0%", "12 (from 34)"),
        ("samples/stats_calculator.py", "11.76%", "45.21%", "57.89%", "33 / 73", "100.0%", "14 (from 38)")
    ]

    for i, row in enumerate(b_data):
        for j, val in enumerate(row):
            cell = t10.cell(i+1, j)
            cell.text = val
            cell.fill.solid()
            cell.fill.fore_color.rgb = RGBColor(20, 30, 48) if i % 2 == 1 else CARD_BG
            for p in cell.text_frame.paragraphs:
                p.alignment = PP_ALIGN.LEFT if j == 0 else PP_ALIGN.CENTER
                for r in p.runs:
                    r.font.size = Pt(8.5)
                    r.font.color.rgb = ACCENT_GREEN if j in (2, 3, 5) else TEXT_WHITE
                    if j in (0, 2, 3):
                        r.font.bold = True

    # =========================================================================
    # SLIDE 11: 11 / TEAM RESPONSIBILITY MATRIX
    # =========================================================================
    s11 = prs.slides.add_slide(blank_layout)
    set_slide_background(s11)
    add_header(s11, "11 / Team Responsibility Matrix", "Balanced 50/50 Engineering Ownership & Individual Deliverables", 
               "Sourabh Jain (230584) & Shreshth Mittal (230577) Across All 13 Engineering Dimensions")

    t11_shape = s11.shapes.add_table(14, 3, Inches(0.8), Inches(1.7), Inches(11.7), Inches(5.1))
    t11 = t11_shape.table
    t11.columns[0].width = Inches(2.7)
    t11.columns[1].width = Inches(4.5)
    t11.columns[2].width = Inches(4.5)

    h11 = ["Project Activity Dimension", "Sourabh Jain (230584)", "Shreshth Mittal (230577)"]
    for j, h in enumerate(h11):
        cell = t11.cell(0, j)
        cell.text = h
        cell.fill.solid()
        cell.fill.fore_color.rgb = RGBColor(30, 58, 138)
        for p in cell.text_frame.paragraphs:
            p.alignment = PP_ALIGN.CENTER
            for r in p.runs:
                r.font.size = Pt(9.5)
                r.font.bold = True
                r.font.color.rgb = TEXT_WHITE

    team_data = [
        ("Agent Design / Architecture", "Google ADK Hierarchical Supervisor & Blackboard", "CrewAI Adversarial Critic & persona design"),
        ("Agent Orchestration", "6-Stage FSM execution gating (INGEST -> FINALIZE)", "CrewAI reflection loop & task delegation"),
        ("State Management", "testforge/blackboard.py with SQLite WAL mode", "Typed Pydantic v2 schemas (schema_version: 1.0.0)"),
        ("MCP Design", "FastMCP stdio JSON-RPC server (mcp_server.py)", "4 Tool schemas and AST transformer integration"),
        ("A2A Communication", "A2A discovery endpoint (/.well-known/agent-card.json)", "Typed A2A message broker & FIPA-ACL performatives"),
        ("Guardrails & Callbacks", "Subprocess RLIMIT bounds & zero-egress socket block", "Static AST NodeVisitor guardrails & DEF-022 gate"),
        ("Observability", "OpenTelemetry W3C distributed tracing spans", "Real-time Multi-Agent Wiretap & event streams"),
        ("Integration & Testing", "Automated Playwright Chromium visual verification harness", "Pytest suite, Hypothesis fuzzing & CI pipeline"),
        ("Evaluation & Documentation", "Mathematical set-cover formulation & report lead", "60-run factorial experiment & DEF-022 audit"),
        ("Presentation / Interface UI", "Vanilla HTML5/CSS3/ES6 single-page cockpit", "AST mutant diff viewer & dark/light theme engine"),
        ("Deployment", "Local Ollama fallback routing & macOS arm64 build", "Multi-provider hot-swapping (Gemini & OpenRouter)"),
        ("End-to-End Evaluation", "Runtime latency profiling (2.410s mean) & cost analysis", "LLM-as-judge vs. ground truth Pass@1 correlation"),
        ("Stateful Planning & Minimizer", "Submodular greedy set cover minimizer algorithm", "Class state mutation graph & call-chain planner")
    ]

    for i, row in enumerate(team_data):
        for j, val in enumerate(row):
            cell = t11.cell(i+1, j)
            cell.text = val
            cell.fill.solid()
            cell.fill.fore_color.rgb = RGBColor(20, 30, 48) if i % 2 == 1 else CARD_BG
            for p in cell.text_frame.paragraphs:
                p.alignment = PP_ALIGN.LEFT
                for r in p.runs:
                    r.font.size = Pt(7.8)
                    r.font.color.rgb = ACCENT_BLUE if j == 1 else (ACCENT_GREEN if j == 2 else TEXT_WHITE)
                    if j == 0:
                        r.font.bold = True

    # =========================================================================
    # SLIDE 12: 12 / DEMONSTRATION SCREENSHOTS
    # =========================================================================
    s12 = prs.slides.add_slide(blank_layout)
    set_slide_background(s12)
    add_header(s12, "12 / Demonstration Screenshots", "Evidence from the Running Cockpit, Wiretap & FastMCP Studio", 
               "Verified Localhost Execution Captured via Playwright Chromium (1440×900, Retina 2×)")

    screen_cards = [
        ("03_hardening_lab_results.png", "HARDENING LAB: FINALIZED (94.74% MS)", "Live cockpit showing 18/19 mutants killed, 100% Pass@1, and AST diff inspector."),
        ("04_multi_agent_wiretap.png", "MULTI-AGENT WIRETAP LOGS", "Real-time streaming of A2A message handoffs between ADK Supervisor and CrewAI Critic."),
        ("10_fastmcp_studio.png", "FASTMCP INTERACTIVE PROTOCOL STUDIO", "Live testing of the 4 stdio tools with input/output Pydantic JSON schemas.")
    ]

    sc_w = Inches(3.72)
    for i, (fn, cap_t, cap_d) in enumerate(screen_cards):
        left = Inches(0.8 + i * 3.98)
        img_p = os.path.join(ASSETS_DIR, fn)
        if os.path.exists(img_p):
            s12.shapes.add_picture(img_p, left, Inches(1.8), width=sc_w)
        
        # Caption card below
        add_card(s12, left, Inches(4.4), sc_w, Inches(2.3))
        tb = s12.shapes.add_textbox(left + Inches(0.15), Inches(4.5), sc_w - Inches(0.3), Inches(2.1))
        tf = tb.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = cap_t
        p.font.size = Pt(10.5)
        p.font.bold = True
        p.font.color.rgb = ACCENT_BLUE
        p = tf.add_paragraph()
        p.text = cap_d
        p.font.size = Pt(9)
        p.font.color.rgb = TEXT_MUTED
        p.space_before = Pt(4)

    # =========================================================================
    # SLIDE 13: 13 / CONCLUSIONS & LIMITATIONS
    # =========================================================================
    s13 = prs.slides.add_slide(blank_layout)
    set_slide_background(s13)
    add_header(s13, "13 / Conclusions & Limitations", "Scientific Conclusions, Practical Limitations & Future Work", 
               "Key Engineering Takeaways & Honest Claim Boundaries on Dynamic Generics and Float Precision")

    # Left: Conclusions Card
    add_card(s13, Inches(0.8), Inches(1.8), Inches(5.7), Inches(4.9))
    tb_c = s13.shapes.add_textbox(Inches(1.0), Inches(1.95), Inches(5.3), Inches(4.6))
    tf_c = tb_c.text_frame
    tf_c.word_wrap = True
    p = tf_c.paragraphs[0]
    p.text = "CORE SCIENTIFIC CONCLUSIONS"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = ACCENT_GREEN

    p = tf_c.add_paragraph()
    p.text = "• Solved the Coverage-Kill Gap: Achieved 77.42% raw / 80.37% adjusted Mutation Score (12.0x over developer baseline) across diverse Python codebases.\n\n" \
             "• Dual-Framework Synergy: Combining Google ADK's structured FSM gating with CrewAI's adversarial critique eliminated cognitive drift and premature convergence.\n\n" \
             "• Stateful Planning Breakthrough: Raised LRU cache mutation score from 30.95% to 90.48% by modeling constructor and mutator invocation sequences.\n\n" \
             "• Submodular Test Suite Compression: Greedy set cover achieved 78.3% test count reduction with 100% kill retention, resolving CI runtime bloat."
    p.font.size = Pt(9.5)
    p.font.color.rgb = TEXT_MUTED
    p.space_before = Pt(8)

    # Right: Limitations Card
    add_card(s13, Inches(6.8), Inches(1.8), Inches(5.7), Inches(4.9))
    tb_l = s13.shapes.add_textbox(Inches(7.0), Inches(1.95), Inches(5.3), Inches(4.6))
    tf_l = tb_l.text_frame
    tf_l.word_wrap = True
    p = tf_l.paragraphs[0]
    p.text = "PRACTICAL LIMITATIONS & ROADMAP"
    p.font.size = Pt(12)
    p.font.bold = True
    p.font.color.rgb = ACCENT_AMBER

    p = tf_l.add_paragraph()
    p.text = "Honest Engineering Boundaries:\n" \
             "• Untyped Dynamic Generics: Without PEP 484 type hints, input domains are heuristically inferred, occasionally requiring extra repair turns.\n" \
             "• Floating-Point Precision: On samples/stats_calculator.py (45.21% MS), variance calculation mutants produce subtle rounding errors classified as equivalent.\n\n" \
             "Future Research Roadmap:\n" \
             "• Symbolic SMT Execution: Integrating CrossHair/Z3 solver via FastMCP to mathematically prove mutant equivalence and eliminate false survivors.\n" \
             "• Multi-Language Expansion: Porting AST and sandbox tools to Rust and TypeScript.\n" \
             "• Automated Patch Synthesis: Generating verified pull requests for genuine bugs exposed during hardening."
    p.font.size = Pt(9.5)
    p.font.color.rgb = TEXT_MUTED
    p.space_before = Pt(8)

    # =========================================================================
    # SLIDE 14: 14 / REFERENCES
    # =========================================================================
    s14 = prs.slides.add_slide(blank_layout)
    set_slide_background(s14)
    add_header(s14, "14 / References", "Research Papers, Framework Documentation & Industry Standards", 
               "Foundational Literature in Mutation Testing, Search-Based Software Engineering, and Agentic Protocols")

    ref_col1 = [
        ("[1] Y. Jia and M. Harman (2011)", "An analysis and survey of the development of mutation testing.", "IEEE Trans. on Software Engineering, vol. 37, no. 5, pp. 649–678."),
        ("[2] R. Just, D. Jalali, et al. (2014)", "Are mutants a valid substitute for real faults in software testing?", "Proc. 22nd ACM SIGSOFT FSE, pp. 654–665."),
        ("[3] G. Fraser and A. Arcuri (2011)", "EvoSuite: Automatic test suite generation for object-oriented software.", "Proc. 19th ACM SIGSOFT FSE, pp. 416–419."),
        ("[4] N. Alshahwan and M. Harman (2018)", "Automated mobile app testing at scale: Lessons from Sapienz at Facebook.", "Proc. 40th ICSE-SEIP, pp. 2–3."),
        ("[5] H. G. Rice (1953)", "Classes of recursively enumerable sets and their decision problems.", "Trans. American Mathematical Society, vol. 74, no. 2, pp. 358–366.")
    ]

    ref_col2 = [
        ("[6] Google Cloud (2025)", "Agent Development Kit (ADK) Documentation and Architecture Guide.", "Google LLC, Mountain View, CA. cloud.google.com/vertex-ai/docs/agent-development-kit"),
        ("[7] J. Moura (2024)", "CrewAI: Framework for Orchestrating Role-Playing Autonomous AI Agents.", "CrewAI Inc. github.com/crewAIInc/crewAI"),
        ("[8] Anthropic PBC (2024)", "Model Context Protocol (MCP) Specification.", "modelcontextprotocol.io/introduction"),
        ("[9] Python Software Foundation (2026)", "ast — Abstract Syntax Trees (Python 3.13 Standard Library).", "docs.python.org/3/library/ast.html"),
        ("[10] OpenTelemetry Authors (2025)", "OpenTelemetry Python API and SDK Documentation.", "Cloud Native Computing Foundation. opentelemetry.io/docs/languages/python")
    ]

    # Column 1
    add_card(s14, Inches(0.8), Inches(1.8), Inches(5.7), Inches(4.9))
    tb_r1 = s14.shapes.add_textbox(Inches(1.0), Inches(1.9), Inches(5.3), Inches(4.7))
    tf_r1 = tb_r1.text_frame
    tf_r1.word_wrap = True
    for i, (cit_id, cit_title, cit_venue) in enumerate(ref_col1):
        p = tf_r1.paragraphs[0] if i == 0 else tf_r1.add_paragraph()
        p.text = cit_id
        p.font.size = Pt(9.5)
        p.font.bold = True
        p.font.color.rgb = ACCENT_BLUE
        if i > 0:
            p.space_before = Pt(8)
        p = tf_r1.add_paragraph()
        p.text = f"{cit_title} {cit_venue}"
        p.font.size = Pt(8.2)
        p.font.color.rgb = TEXT_MUTED

    # Column 2
    add_card(s14, Inches(6.8), Inches(1.8), Inches(5.7), Inches(4.9))
    tb_r2 = s14.shapes.add_textbox(Inches(7.0), Inches(1.9), Inches(5.3), Inches(4.7))
    tf_r2 = tb_r2.text_frame
    tf_r2.word_wrap = True
    for i, (cit_id, cit_title, cit_venue) in enumerate(ref_col2):
        p = tf_r2.paragraphs[0] if i == 0 else tf_r2.add_paragraph()
        p.text = cit_id
        p.font.size = Pt(9.5)
        p.font.bold = True
        p.font.color.rgb = ACCENT_BLUE
        if i > 0:
            p.space_before = Pt(8)
        p = tf_r2.add_paragraph()
        p.text = f"{cit_title} {cit_venue}"
        p.font.size = Pt(8.2)
        p.font.color.rgb = TEXT_MUTED

    # Save PPTX
    prs.save(OUT_PPTX)
    print(f"Presentation successfully created with {len(prs.slides)} slides at: {OUT_PPTX}")
    return prs

if __name__ == "__main__":
    create_deck()
