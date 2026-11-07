"""
scripts/generate_coverage_matrix_slide.py
Generates the pixel-perfect 1-slide Requirements Coverage Matrix for TestForge:
1. PPTX presentation (16:9 widescreen) matching the exact layout, colors, and structure of the reference slide.
2. High-fidelity HTML slide.
3. Playwright screenshot PNG rendering for immediate artifact viewing.
"""

import os
import sys
import shutil
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

PPTX_PATH = "docs/VIVA.PRESENTATION/TestForge_Requirements_Coverage_Matrix.pptx"
HTML_PATH = "docs/VIVA.PRESENTATION/TestForge_Requirements_Coverage_Matrix.html"
PNG_PATH = "docs/VIVA.PRESENTATION/TestForge_Requirements_Coverage_Matrix.png"
ARTIFACT_PNG_PATH = "/Users/sourabh/.gemini/antigravity/brain/ad3919fc-7c4f-4e08-af89-e520bbc7c86c/TestForge_Requirements_Coverage_Matrix.png"

# 11 Criteria Data
CRITERIA = [
    (
        "1",
        "State sharing + Blackboard; messaging architectures compared",
        "Met",
        "In-memory Blackboard (RLock, 5 spaces) + 1,310 SQLite checkpoints; 3 archs benchmarked",
        "§4.1"
    ),
    (
        "2",
        "Tools via MCP (FastMCP servers)",
        "Met",
        "2 FastMCP servers with 6 production tools (3 Filesystem + 3 GitHub PR inspection)",
        "§4.2"
    ),
    (
        "3",
        "Structured output with Pydantic",
        "Met",
        "Strict Pydantic v2 schemas for AST targets, test suites, mutants & A2A envelopes",
        "§4.3"
    ),
    (
        "4",
        "Agentic design patterns, compared",
        "Met",
        "ReAct, Closed-Loop Mutation Reflection, and Hierarchical Supervisor-Worker architectures compared",
        "§4.4"
    ),
    (
        "5",
        "Monitoring via callback functions",
        "Met",
        "Synchronous event bus observer callbacks with real-time SSE live wiretap streaming (/api/wiretap)",
        "§4.5"
    ),
    (
        "6",
        "A2A between ADK and CrewAI agents",
        "Met",
        "Google ADK Generator → CrewAI Critic communicating over FIPA A2A envelopes (REQUEST/INFORM)",
        "§4.6"
    ),
    (
        "7",
        "Only CrewAI + Google ADK used",
        "Met",
        "Native engine using Google GenAI SDK and CrewAI adapter; 0 unapproved third-party frameworks",
        "§4.7"
    ),
    (
        "8",
        "Guardrails + prompt variants",
        "Met",
        "10 security scenarios × 4 personas × 3 prompt styles (120 trials, 100% defense rate)",
        "§4.8"
    ),
    (
        "9",
        "Observability: tracing, audit, provenance",
        "Met",
        "305k+ JSONL traces, 1,310 SQLite checkpoints, reconciled actual vs estimated tokens",
        "§4.9"
    ),
    (
        "10",
        "End-to-end evaluation: cost & time, prompt variance",
        "Met",
        "60 empirical runs in BENCHMARK_RAW_RESULTS.json; 89.47% mutation score achieved",
        "§4.10"
    ),
    (
        "11",
        "Cloud deployment",
        "Partial",
        "Docker container verified (Dockerfile & compose); local daemon live on :8000; cloud rollout staged",
        "§4.11"
    ),
]


def build_pptx(output_path: str):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)

    blank_layout = prs.slide_layouts[6]
    slide = prs.slides.add_slide(blank_layout)

    # 1. Header (Title & Subtitle)
    title_box = slide.shapes.add_textbox(Inches(0.6), Inches(0.4), Inches(12.133), Inches(0.95))
    tf = title_box.text_frame
    tf.word_wrap = True
    tf.margin_left = tf.margin_top = tf.margin_right = tf.margin_bottom = 0

    p_title = tf.paragraphs[0]
    p_title.text = "Coverage Matrix: 10 of 11 Requirements Met"
    p_title.font.size = Pt(26)
    p_title.font.bold = True
    p_title.font.name = "Calibri"
    p_title.font.color.rgb = RGBColor(26, 54, 93)  # #1A365D Navy
    p_title.space_after = Pt(4)

    p_sub = tf.add_paragraph()
    p_sub.text = 'Progress across all 11 technical review criteria · ~91% complete (10 Met, 1 Partial). Each "§" link opens the matching heading in TestForge documentation.'
    p_sub.font.size = Pt(12)
    p_sub.font.name = "Calibri"
    p_sub.font.color.rgb = RGBColor(100, 116, 139)  # #64748B Slate

    # 2. Left Sidebar Card
    card_shape = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE,
        Inches(0.6), Inches(1.5), Inches(2.75), Inches(5.35)
    )
    card_shape.fill.solid()
    card_shape.fill.fore_color.rgb = RGBColor(248, 250, 252)  # #F8FAFC
    card_shape.line.color.rgb = RGBColor(226, 232, 240)       # #E2E8F0
    card_shape.line.width = Pt(1)

    ctf = card_shape.text_frame
    ctf.word_wrap = True
    ctf.vertical_anchor = MSO_ANCHOR.TOP
    ctf.margin_left = ctf.margin_right = Inches(0.2)
    ctf.margin_top = Inches(0.25)
    ctf.margin_bottom = Inches(0.2)

    # Big Number: 91%
    p_pct = ctf.paragraphs[0]
    p_pct.text = "91%"
    p_pct.font.size = Pt(54)
    p_pct.font.bold = True
    p_pct.font.name = "Calibri"
    p_pct.font.color.rgb = RGBColor(26, 54, 93)
    p_pct.space_after = Pt(2)

    # Subtitle under big number
    p_comp = ctf.add_paragraph()
    p_comp.text = "complete: Core System Verified\n(10 of 11 Met)"
    p_comp.font.size = Pt(11)
    p_comp.font.bold = True
    p_comp.font.name = "Calibri"
    p_comp.font.color.rgb = RGBColor(15, 23, 42)
    p_comp.space_after = Pt(16)

    # Breakdown Items
    p_met = ctf.add_paragraph()
    p_met.text = "10 met"
    p_met.font.size = Pt(16)
    p_met.font.bold = True
    p_met.font.name = "Calibri"
    p_met.font.color.rgb = RGBColor(22, 101, 52)  # #166534 Green
    p_met.space_after = Pt(4)

    p_part = ctf.add_paragraph()
    p_part.text = "1 partial · Cloud"
    p_part.font.size = Pt(14)
    p_part.font.bold = True
    p_part.font.name = "Calibri"
    p_part.font.color.rgb = RGBColor(180, 83, 9)   # #B45309 Amber
    p_part.space_after = Pt(4)

    p_plan = ctf.add_paragraph()
    p_plan.text = "0 unaddressed"
    p_plan.font.size = Pt(12)
    p_plan.font.name = "Calibri"
    p_plan.font.color.rgb = RGBColor(100, 116, 139)
    p_plan.space_after = Pt(2)

    p_of11 = ctf.add_paragraph()
    p_of11.text = "of the 11 review requirements"
    p_of11.font.size = Pt(10)
    p_of11.font.name = "Calibri"
    p_of11.font.color.rgb = RGBColor(148, 163, 184)
    p_of11.space_after = Pt(24)

    # Partial Cloud Details Callout
    p_rem_head = ctf.add_paragraph()
    p_rem_head.text = "Cloud Deployment (Partial):"
    p_rem_head.font.size = Pt(11)
    p_rem_head.font.bold = True
    p_rem_head.font.name = "Calibri"
    p_rem_head.font.color.rgb = RGBColor(26, 54, 93)
    p_rem_head.space_after = Pt(4)

    p_rem_body = ctf.add_paragraph()
    p_rem_body.text = "Container ready (Dockerfile & compose); local daemon verified (:8000); cloud cluster rollout staged."
    p_rem_body.font.size = Pt(9.5)
    p_rem_body.font.name = "Calibri"
    p_rem_body.font.color.rgb = RGBColor(71, 85, 105)

    # 3. Requirements Table (11 Rows + Header)
    table_left = Inches(3.55)
    table_top = Inches(1.5)
    table_width = Inches(9.18)
    table_height = Inches(5.35)

    table_shape = slide.shapes.add_table(12, 5, table_left, table_top, table_width, table_height)
    table = table_shape.table

    # Column Widths
    col_widths = [Inches(0.42), Inches(2.95), Inches(1.05), Inches(4.06), Inches(0.70)]
    for idx, width in enumerate(col_widths):
        table.columns[idx].width = width

    # Headers
    headers = ["#", "Requirement", "Status", "Evidence", "Report"]
    for col_idx, header in enumerate(headers):
        cell = table.cell(0, col_idx)
        cell.fill.solid()
        cell.fill.fore_color.rgb = RGBColor(30, 58, 138)  # #1E3A8A Navy
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE
        cell.margin_left = cell.margin_right = Inches(0.04)
        cell.margin_top = cell.margin_bottom = Inches(0.02)
        p = cell.text_frame.paragraphs[0]
        p.text = header
        p.font.size = Pt(10)
        p.font.bold = True
        p.font.name = "Calibri"
        p.font.color.rgb = RGBColor(255, 255, 255)
        p.alignment = PP_ALIGN.CENTER if col_idx in (0, 2, 4) else PP_ALIGN.LEFT

    for row_idx, (num, req, status, ev, rep) in enumerate(CRITERIA, start=1):
        row_bg = RGBColor(255, 255, 255) if row_idx % 2 != 0 else RGBColor(248, 250, 252)

        # Col 0: #
        c0 = table.cell(row_idx, 0)
        c0.fill.solid()
        c0.fill.fore_color.rgb = row_bg
        c0.vertical_anchor = MSO_ANCHOR.MIDDLE
        c0.margin_left = c0.margin_right = Inches(0.02)
        c0.margin_top = c0.margin_bottom = Inches(0.02)
        p0 = c0.text_frame.paragraphs[0]
        p0.text = num
        p0.font.size = Pt(9.5)
        p0.font.bold = True
        p0.font.name = "Calibri"
        p0.font.color.rgb = RGBColor(15, 23, 42)
        p0.alignment = PP_ALIGN.CENTER

        # Col 1: Requirement
        c1 = table.cell(row_idx, 1)
        c1.fill.solid()
        c1.fill.fore_color.rgb = row_bg
        c1.vertical_anchor = MSO_ANCHOR.MIDDLE
        c1.margin_left = Inches(0.06)
        c1.margin_right = Inches(0.04)
        c1.margin_top = c1.margin_bottom = Inches(0.02)
        p1 = c1.text_frame.paragraphs[0]
        p1.text = req
        p1.font.size = Pt(8.5)
        p1.font.bold = (status == "Partial")
        p1.font.name = "Calibri"
        p1.font.color.rgb = RGBColor(15, 23, 42)
        p1.alignment = PP_ALIGN.LEFT

        # Col 2: Status
        c2 = table.cell(row_idx, 2)
        c2.fill.solid()
        if status == "Met":
            c2.fill.fore_color.rgb = RGBColor(220, 252, 231)  # #DCFCE7 Soft Green
            status_color = RGBColor(22, 101, 52)             # #166534 Dark Green
        else:
            c2.fill.fore_color.rgb = RGBColor(254, 243, 199)  # #FEF3C7 Soft Amber
            status_color = RGBColor(180, 83, 9)              # #B45309 Dark Amber

        c2.vertical_anchor = MSO_ANCHOR.MIDDLE
        c2.margin_left = c2.margin_right = Inches(0.02)
        c2.margin_top = c2.margin_bottom = Inches(0.02)
        p2 = c2.text_frame.paragraphs[0]
        p2.text = status
        p2.font.size = Pt(9)
        p2.font.bold = True
        p2.font.name = "Calibri"
        p2.font.color.rgb = status_color
        p2.alignment = PP_ALIGN.CENTER

        # Col 3: Evidence
        c3 = table.cell(row_idx, 3)
        c3.fill.solid()
        c3.fill.fore_color.rgb = row_bg
        c3.vertical_anchor = MSO_ANCHOR.MIDDLE
        c3.margin_left = Inches(0.06)
        c3.margin_right = Inches(0.04)
        c3.margin_top = c3.margin_bottom = Inches(0.02)
        p3 = c3.text_frame.paragraphs[0]
        p3.text = ev
        p3.font.size = Pt(8.0)
        p3.font.name = "Calibri"
        p3.font.color.rgb = RGBColor(51, 65, 85)
        p3.alignment = PP_ALIGN.LEFT

        # Col 4: Report
        c4 = table.cell(row_idx, 4)
        c4.fill.solid()
        c4.fill.fore_color.rgb = row_bg
        c4.vertical_anchor = MSO_ANCHOR.MIDDLE
        c4.margin_left = c4.margin_right = Inches(0.02)
        c4.margin_top = c4.margin_bottom = Inches(0.02)
        p4 = c4.text_frame.paragraphs[0]
        p4.text = rep
        p4.font.size = Pt(9)
        p4.font.underline = True
        p4.font.name = "Calibri"
        p4.font.color.rgb = RGBColor(37, 99, 235)  # #2563EB Blue
        p4.alignment = PP_ALIGN.CENTER

    # 4. Slide Footer
    footer_box = slide.shapes.add_textbox(Inches(0.6), Inches(7.05), Inches(12.133), Inches(0.3))
    ftf = footer_box.text_frame
    ftf.margin_left = ftf.margin_top = ftf.margin_right = ftf.margin_bottom = 0
    p_ft = ftf.paragraphs[0]
    p_ft.text = "TestForge · Autonomous Multi-Agent Unit Test Hardening via Mutation-Verified Reflection Loops · Final Technical Review"
    p_ft.font.size = Pt(9)
    p_ft.font.name = "Calibri"
    p_ft.font.color.rgb = RGBColor(148, 163, 184)

    # 5. Slide Speaker Notes
    notes_slide = slide.notes_slide
    ntf = notes_slide.notes_text_frame
    ntf.text = (
        "Presenter Notes:\n"
        "Here is the complete 11-point Requirements Coverage Matrix for TestForge.\n"
        "Out of the 11 course review requirements, 10 are completely Met and backed by rigorous empirical evidence:\n"
        "1. State sharing via thread-safe in-memory Blackboard (threading.RLock) with 1,310 SQLite checkpoints.\n"
        "2. Tool integration using FastMCP exposing 6 production tools across Filesystem and GitHub.\n"
        "3. Structured output via strict Pydantic models for targets, tests, mutants, and A2A envelopes.\n"
        "4. Agentic design patterns compared across ReAct, Reflection, and Supervisor-Worker paradigms.\n"
        "5. Monitoring via event bus callbacks with live Server-Sent Events (SSE) wiretap streaming.\n"
        "6. Agent-to-Agent (A2A) protocol connecting Google ADK Generator and CrewAI Critic over FIPA performatives.\n"
        "7. Framework compliance using only CrewAI and Google ADK.\n"
        "8. Enterprise guardrails evaluated across 120 deterministic trials with a 100% defense rate.\n"
        "9. Full observability with 305k+ trace events and reconciled token accounting (29,476 actual / 27,920 estimated).\n"
        "10. End-to-end evaluation with 60 empirical runs in BENCHMARK_RAW_RESULTS.json achieving 89.47% raw mutation score.\n"
        "11. Cloud deployment is marked Partial: our Dockerfile and docker-compose configurations are complete and our local daemon is live on port 8000; the multi-node cloud cluster deployment is currently staged."
    )

    prs.save(output_path)
    print(f"Successfully generated PPTX: {output_path}")


def build_html(output_path: str):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    rows_html = ""
    for idx, (num, req, status, ev, rep) in enumerate(CRITERIA, start=1):
        bg_class = "even" if idx % 2 == 0 else "odd"
        status_class = "status-met" if status == "Met" else "status-partial"
        rows_html += f"""
        <tr class="{bg_class}">
          <td class="col-num">{num}</td>
          <td class="col-req">{req}</td>
          <td class="col-status"><span class="badge {status_class}">{status}</span></td>
          <td class="col-ev">{ev}</td>
          <td class="col-rep"><a href="#">{rep}</a></td>
        </tr>"""

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Coverage Matrix: 10 of 11 Requirements Met - TestForge</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    background-color: #f1f5f9;
    font-family: 'Segoe UI', Calibri, -apple-system, BlinkMacSystemFont, 'Inter', Roboto, sans-serif;
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
    padding: 20px;
  }}
  .slide-container {{
    width: 1280px;
    height: 720px;
    background: #ffffff;
    padding: 36px 48px;
    box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.1), 0 8px 10px -6px rgba(0, 0, 0, 0.1);
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    overflow: hidden;
  }}
  .header {{
    margin-bottom: 20px;
  }}
  .title {{
    font-size: 26px;
    font-weight: 700;
    color: #1a365d;
    margin-bottom: 4px;
    letter-spacing: -0.3px;
  }}
  .subtitle {{
    font-size: 13px;
    color: #64748b;
  }}
  .content-grid {{
    display: grid;
    grid-template-columns: 260px 1fr;
    gap: 24px;
    flex: 1;
    align-items: stretch;
  }}
  .sidebar-card {{
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 12px;
    padding: 22px 18px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
  }}
  .big-metric {{
    font-size: 56px;
    font-weight: 800;
    color: #1a365d;
    line-height: 1;
    letter-spacing: -1px;
    margin-bottom: 6px;
  }}
  .metric-label {{
    font-size: 12px;
    font-weight: 700;
    color: #0f172a;
    line-height: 1.3;
    margin-bottom: 20px;
  }}
  .status-counts {{
    display: flex;
    flex-direction: column;
    gap: 6px;
    margin-bottom: 12px;
  }}
  .count-met {{
    font-size: 17px;
    font-weight: 700;
    color: #166534;
  }}
  .count-partial {{
    font-size: 14px;
    font-weight: 700;
    color: #b45309;
  }}
  .count-planned {{
    font-size: 12px;
    font-weight: 600;
    color: #64748b;
  }}
  .count-sub {{
    font-size: 10.5px;
    color: #94a3b8;
    margin-top: -2px;
    margin-bottom: 14px;
  }}
  .callout-box {{
    background: #ffffff;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 12px 10px;
    border-left: 3px solid #b45309;
  }}
  .callout-title {{
    font-size: 11px;
    font-weight: 700;
    color: #1a365d;
    margin-bottom: 4px;
  }}
  .callout-text {{
    font-size: 10px;
    color: #475569;
    line-height: 1.35;
  }}
  .table-container {{
    display: flex;
    flex-direction: column;
    overflow: hidden;
    border-radius: 8px;
    border: 1px solid #e2e8f0;
  }}
  table {{
    width: 100%;
    border-collapse: collapse;
    font-size: 11px;
  }}
  th {{
    background-color: #1e3a8a;
    color: #ffffff;
    padding: 9px 8px;
    font-weight: 700;
    font-size: 11px;
    text-align: left;
    letter-spacing: 0.3px;
  }}
  th.center, td.center {{
    text-align: center;
  }}
  tr.odd {{
    background-color: #ffffff;
  }}
  tr.even {{
    background-color: #f8fafc;
  }}
  td {{
    padding: 6.5px 8px;
    vertical-align: middle;
    border-top: 1px solid #f1f5f9;
    color: #0f172a;
    line-height: 1.25;
  }}
  .col-num {{
    width: 32px;
    font-weight: 700;
    text-align: center;
    color: #0f172a;
  }}
  .col-req {{
    width: 250px;
    font-size: 10.5px;
    font-weight: 600;
  }}
  .col-status {{
    width: 85px;
    text-align: center;
  }}
  .col-ev {{
    font-size: 10px;
    color: #334155;
  }}
  .col-rep {{
    width: 55px;
    text-align: center;
    font-size: 11px;
    font-weight: 600;
  }}
  .col-rep a {{
    color: #2563eb;
    text-decoration: underline;
  }}
  .badge {{
    display: inline-block;
    padding: 2px 8px;
    border-radius: 4px;
    font-weight: 700;
    font-size: 10.5px;
  }}
  .status-met {{
    background-color: #dcfce7;
    color: #166534;
  }}
  .status-partial {{
    background-color: #fef3c7;
    color: #b45309;
  }}
  .footer {{
    margin-top: 12px;
    font-size: 10.5px;
    color: #94a3b8;
  }}
</style>
</head>
<body>
<div class="slide-container">
  <div class="header">
    <div class="title">Coverage Matrix: 10 of 11 Requirements Met</div>
    <div class="subtitle">Progress across all 11 technical review criteria · ~91% complete (10 Met, 1 Partial). Each "§" link opens the matching heading in TestForge documentation.</div>
  </div>

  <div class="content-grid">
    <!-- Sidebar -->
    <div class="sidebar-card">
      <div>
        <div class="big-metric">91%</div>
        <div class="metric-label">complete: Core System Verified<br>(10 of 11 Met)</div>
        <div class="status-counts">
          <div class="count-met">10 met</div>
          <div class="count-partial">1 partial · Cloud</div>
          <div class="count-planned">0 unaddressed</div>
          <div class="count-sub">of the 11 review requirements</div>
        </div>
      </div>
      <div class="callout-box">
        <div class="callout-title">Cloud Deployment (Partial):</div>
        <div class="callout-text">Container ready (Dockerfile & compose); local daemon verified (:8000); cloud cluster rollout staged.</div>
      </div>
    </div>

    <!-- Table -->
    <div class="table-container">
      <table>
        <thead>
          <tr>
            <th class="center" style="width: 32px;">#</th>
            <th style="width: 250px;">Requirement</th>
            <th class="center" style="width: 85px;">Status</th>
            <th>Evidence</th>
            <th class="center" style="width: 55px;">Report</th>
          </tr>
        </thead>
        <tbody>
          {rows_html}
        </tbody>
      </table>
    </div>
  </div>

  <div class="footer">
    TestForge · Autonomous Multi-Agent Unit Test Hardening via Mutation-Verified Reflection Loops · Final Technical Review
  </div>
</div>
</body>
</html>"""
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Successfully generated HTML: {output_path}")


def render_screenshot(html_path: str, png_path: str, artifact_path: str):
    from playwright.sync_api import sync_playwright
    abs_html = os.path.abspath(html_path)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1360, "height": 800}, device_scale_factor=2)
        page.goto(f"file://{abs_html}")
        slide_elem = page.locator(".slide-container")
        slide_elem.screenshot(path=png_path)
        browser.close()
    print(f"Successfully rendered screenshot: {png_path}")

    # Copy to artifact path
    os.makedirs(os.path.dirname(artifact_path), exist_ok=True)
    shutil.copyfile(png_path, artifact_path)
    print(f"Copied to artifact path: {artifact_path}")


if __name__ == "__main__":
    build_pptx(PPTX_PATH)
    build_html(HTML_PATH)
    render_screenshot(HTML_PATH, PNG_PATH, ARTIFACT_PNG_PATH)
