"""
styles.py - Professional Academic Document Styling for python-docx.
Configures typography, color palettes, custom table borders, callout boxes,
code blocks, and header/footer pagination for TestForge Viva Book.
"""

import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import parse_xml, OxmlElement
from docx.oxml.ns import nsdecls, qn

# --- Color Palette ---
COLOR_PRIMARY_NAVY = RGBColor(30, 58, 138)       # #1E3A8A - Headings & Hero
COLOR_SECONDARY_BLUE = RGBColor(2, 132, 199)     # #0284C7 - Subheadings
COLOR_TEXT_MAIN = RGBColor(15, 23, 42)           # #0F172A - Body text
COLOR_TEXT_MUTED = RGBColor(100, 116, 139)       # #64748B - Captions & metadata
COLOR_ACCENT_AMBER = RGBColor(217, 119, 6)       # #D97706 - Notes & Warnings
COLOR_ACCENT_GREEN = RGBColor(16, 149, 111)      # #10B981 - Verified evidence
COLOR_BG_GRAY = "F8FAFC"                         # Light table/code shading
COLOR_BORDER_GRAY = "E2E8F0"                     # Subtle border


def setup_document_styles(doc: docx.Document):
    """Sets standard 1-inch margins and base typographic defaults."""
    for section in doc.sections:
        section.top_margin = Inches(1.0)
        section.bottom_margin = Inches(1.0)
        section.left_margin = Inches(1.0)
        section.right_margin = Inches(1.0)
        section.different_first_page_header_footer = True

        # Header (Pages 2+)
        header = section.header
        hp = header.paragraphs[0]
        hp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        hrun = hp.add_run("TestForge: Autonomous Test Hardening via Reflection — Viva Book")
        hrun.font.name = "Calibri"
        hrun.font.size = Pt(8.5)
        hrun.font.color.rgb = COLOR_TEXT_MUTED

        # Footer (Pages 2+)
        footer = section.footer
        fp = footer.paragraphs[0]
        fp.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        frun = fp.add_run("Page ")
        frun.font.name = "Calibri"
        frun.font.size = Pt(9)
        frun.font.color.rgb = COLOR_TEXT_MUTED

        # Add page number field
        fldSimple = OxmlElement("w:fldSimple")
        fldSimple.set(qn("w:instr"), "PAGE")
        frun._r.append(fldSimple)

        frun2 = fp.add_run(" | Confidential University Viva Examination Copy")
        frun2.font.name = "Calibri"
        frun2.font.size = Pt(8.5)
        frun2.font.color.rgb = COLOR_TEXT_MUTED

    # Base Normal Style
    style_normal = doc.styles["Normal"]
    style_normal.font.name = "Calibri"
    style_normal.font.size = Pt(10.5)
    style_normal.font.color.rgb = COLOR_TEXT_MAIN
    style_normal.paragraph_format.line_spacing = 1.15
    style_normal.paragraph_format.space_after = Pt(4)


def add_cover_page(doc: docx.Document, title: str, subtitle: str, metadata_rows: list):
    """Constructs an elegant, publication-quality academic title page."""
    p_pre = doc.add_paragraph()
    p_pre.paragraph_format.space_before = Pt(36)
    p_pre.paragraph_format.space_after = Pt(12)

    # University / Course Header
    p_org = doc.add_paragraph()
    r_org = p_org.add_run("BML MUNJAL UNIVERSITY • SCHOOL OF ENGINEERING & TECHNOLOGY\nCSE3101: AGENTIC AI & AUTONOMOUS SOFTWARE SYSTEMS")
    r_org.font.name = "Calibri"
    r_org.font.size = Pt(11)
    r_org.font.bold = True
    r_org.font.color.rgb = COLOR_SECONDARY_BLUE
    p_org.paragraph_format.space_after = Pt(40)

    # Main Title
    p_title = doc.add_paragraph()
    r_title = p_title.add_run(title)
    r_title.font.name = "Calibri"
    r_title.font.size = Pt(26)
    r_title.font.bold = True
    r_title.font.color.rgb = COLOR_PRIMARY_NAVY
    p_title.paragraph_format.space_after = Pt(14)

    # Subtitle
    p_sub = doc.add_paragraph()
    r_sub = p_sub.add_run(subtitle)
    r_sub.font.name = "Calibri"
    r_sub.font.size = Pt(13.5)
    r_sub.font.italic = True
    r_sub.font.color.rgb = COLOR_TEXT_MUTED
    p_sub.paragraph_format.space_after = Pt(48)

    # Metadata Card Table
    tbl = doc.add_table(rows=len(metadata_rows), cols=2)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False

    for i, (k, v) in enumerate(metadata_rows):
        row = tbl.rows[i]
        c0, c1 = row.cells[0], row.cells[1]
        c0.width = Inches(2.2)
        c1.width = Inches(4.3)

        p0 = c0.paragraphs[0]
        r0 = p0.add_run(k)
        r0.font.bold = True
        r0.font.size = Pt(9.5)
        r0.font.color.rgb = COLOR_PRIMARY_NAVY

        p1 = c1.paragraphs[0]
        r1 = p1.add_run(v)
        r1.font.size = Pt(9.5)

        # Style borders and padding
        set_cell_padding(c0, top=60, bottom=60, left=100, right=100)
        set_cell_padding(c1, top=60, bottom=60, left=100, right=100)
        set_cell_shading(c0, "F1F5F9" if i % 2 == 0 else "FFFFFF")
        set_cell_shading(c1, "F8FAFC" if i % 2 == 0 else "FFFFFF")

    # Document Status Stamp
    p_stamp = doc.add_paragraph()
    p_stamp.paragraph_format.space_before = Pt(60)
    r_stamp = p_stamp.add_run("DEFINITIVE ENGINEERING & VIVA EXAMINATION REFERENCE MANUAL\nIncludes 100% Verified Source References, Execution Trajectories & Full 114 Question Bank Answers")
    r_stamp.font.size = Pt(9)
    r_stamp.font.bold = True
    r_stamp.font.color.rgb = COLOR_ACCENT_AMBER

    doc.add_page_break()


def add_h1(doc: docx.Document, text: str):
    """Adds a primary numbered section heading."""
    p = doc.add_paragraph()
    try:
        p.style = "Heading 1"
    except Exception:
        pass
    p.paragraph_format.space_before = Pt(18)
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(text)
    r.font.name = "Calibri"
    r.font.size = Pt(18)
    r.font.bold = True
    r.font.color.rgb = COLOR_PRIMARY_NAVY
    return p


def add_h2(doc: docx.Document, text: str):
    """Adds a secondary subsection heading."""
    p = doc.add_paragraph()
    try:
        p.style = "Heading 2"
    except Exception:
        pass
    p.paragraph_format.space_before = Pt(14)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(text)
    r.font.name = "Calibri"
    r.font.size = Pt(13.5)
    r.font.bold = True
    r.font.color.rgb = COLOR_SECONDARY_BLUE
    return p


def add_h3(doc: docx.Document, text: str):
    """Adds a tertiary sub-subsection heading."""
    p = doc.add_paragraph()
    try:
        p.style = "Heading 3"
    except Exception:
        pass
    p.paragraph_format.space_before = Pt(10)
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.keep_with_next = True
    r = p.add_run(text)
    r.font.name = "Calibri"
    r.font.size = Pt(11)
    r.font.bold = True
    r.font.color.rgb = COLOR_TEXT_MAIN
    return p


def add_p(doc: docx.Document, text: str, bold: bool = False, italic: bool = False, color=None):
    """Adds a body paragraph with optional styling."""
    p = doc.add_paragraph()
    r = p.add_run(text)
    r.font.bold = bold
    r.font.italic = italic
    if color:
        r.font.color.rgb = color
    return p


def add_bullet(doc: docx.Document, text: str, bold_prefix: str = None):
    """Adds a bullet list item with an optional bold prefix."""
    p = doc.add_paragraph(style="List Bullet")
    p.paragraph_format.space_after = Pt(2)
    p.paragraph_format.line_spacing = 1.15
    if bold_prefix:
        r_pre = p.add_run(bold_prefix + " ")
        r_pre.font.bold = True
        r_pre.font.color.rgb = COLOR_PRIMARY_NAVY
    p.add_run(text)
    return p


def add_callout(doc: docx.Document, text: str, title: str = None, alert_type: str = "note"):
    """Creates a highlighted callout box with a colored left border."""
    border_color = "1E3A8A" if alert_type == "note" else ("D97706" if alert_type == "warning" else "10B981")
    bg_color = "F0F9FF" if alert_type == "note" else ("FEF3C7" if alert_type == "warning" else "ECFDF5")

    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    cell.width = Inches(6.5)

    set_cell_shading(cell, bg_color)
    set_cell_padding(cell, top=100, bottom=100, left=150, right=150)
    set_left_border_only(cell, border_color, sz="36")

    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(2)
    if title:
        rt = p.add_run(title + "\n")
        rt.font.bold = True
        rt.font.size = Pt(9.5)
        rt.font.color.rgb = COLOR_PRIMARY_NAVY if alert_type != "warning" else COLOR_ACCENT_AMBER
    r = p.add_run(text)
    r.font.size = Pt(9.5)
    r.font.color.rgb = COLOR_TEXT_MAIN

    doc.add_paragraph().paragraph_format.space_after = Pt(4)


def add_code_block(doc: docx.Document, code_text: str):
    """Inserts a monospaced code block in a shaded container box."""
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    cell.width = Inches(6.5)

    set_cell_shading(cell, "F8FAFC")
    set_cell_padding(cell, top=80, bottom=80, left=120, right=120)
    set_all_borders(cell, "CBD5E1", sz="6")

    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(0)
    p.paragraph_format.line_spacing = 1.05
    r = p.add_run(code_text.strip())
    r.font.name = "Consolas"
    r.font.size = Pt(8.5)
    r.font.color.rgb = RGBColor(30, 41, 59)

    doc.add_paragraph().paragraph_format.space_after = Pt(4)


def add_table(doc: docx.Document, headers: list, rows: list, col_widths: list = None):
    """Creates a professionally formatted data table with a navy header row."""
    tbl = doc.add_table(rows=len(rows) + 1, cols=len(headers))
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    tbl.autofit = False

    # Header Row
    hdr_row = tbl.rows[0]
    hdr_row._tr.get_or_add_trPr().append(parse_xml(f'<w:tblHeader {nsdecls("w")}/>'))
    for j, h in enumerate(headers):
        cell = hdr_row.cells[j]
        if col_widths and j < len(col_widths):
            cell.width = col_widths[j]
        set_cell_shading(cell, "1E3A8A")
        set_cell_padding(cell, top=80, bottom=80, left=100, right=100)
        p = cell.paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        r = p.add_run(str(h))
        r.font.bold = True
        r.font.size = Pt(9)
        r.font.color.rgb = RGBColor(255, 255, 255)

    # Data Rows
    for i, r_data in enumerate(rows):
        row = tbl.rows[i + 1]
        bg = "F8FAFC" if i % 2 == 1 else "FFFFFF"
        for j, val in enumerate(r_data):
            cell = row.cells[j]
            if col_widths and j < len(col_widths):
                cell.width = col_widths[j]
            set_cell_shading(cell, bg)
            set_cell_padding(cell, top=60, bottom=60, left=100, right=100)
            p = cell.paragraphs[0]
            p.alignment = WD_ALIGN_PARAGRAPH.LEFT
            r = p.add_run(str(val))
            r.font.size = Pt(8.5)

    doc.add_paragraph().paragraph_format.space_after = Pt(6)


def add_viva_question(
    doc: docx.Document,
    q_num: int,
    question: str,
    short_answer: str,
    detailed_explanation: str,
    implementation: str,
    example: str,
    why_design: str,
    follow_up: str,
    evidence_status: str
):
    """
    Renders a complete viva question in the mandatory 7-field structure.
    Surrounds each question with an elegant card container.
    """
    tbl = doc.add_table(rows=1, cols=1)
    tbl.alignment = WD_TABLE_ALIGNMENT.CENTER
    cell = tbl.cell(0, 0)
    cell.width = Inches(6.5)

    set_cell_shading(cell, "FFFFFF")
    set_cell_padding(cell, top=100, bottom=100, left=140, right=140)
    set_left_border_only(cell, "1E3A8A", sz="32")
    set_all_borders_except_left(cell, "E2E8F0", sz="4")

    p = cell.paragraphs[0]
    p.paragraph_format.space_after = Pt(6)
    p.paragraph_format.keep_with_next = True

    # Question Header
    rq = p.add_run(f"Question {q_num}: {question}\n")
    rq.font.name = "Calibri"
    rq.font.size = Pt(11.5)
    rq.font.bold = True
    rq.font.color.rgb = COLOR_PRIMARY_NAVY

    # Field 1: Short Viva Answer
    p1 = cell.add_paragraph()
    p1.paragraph_format.space_after = Pt(4)
    r1_lbl = p1.add_run("Short viva answer (20–40s spoken):\n")
    r1_lbl.font.bold = True
    r1_lbl.font.size = Pt(9.5)
    r1_lbl.font.color.rgb = COLOR_SECONDARY_BLUE
    r1_txt = p1.add_run(short_answer)
    r1_txt.font.size = Pt(9.5)
    r1_txt.font.italic = True

    # Field 2: Detailed Explanation
    p2 = cell.add_paragraph()
    p2.paragraph_format.space_after = Pt(4)
    r2_lbl = p2.add_run("Detailed explanation:\n")
    r2_lbl.font.bold = True
    r2_lbl.font.size = Pt(9.5)
    r2_lbl.font.color.rgb = COLOR_PRIMARY_NAVY
    r2_txt = p2.add_run(detailed_explanation)
    r2_txt.font.size = Pt(9.5)

    # Field 3: How TestForge Implements It
    p3 = cell.add_paragraph()
    p3.paragraph_format.space_after = Pt(4)
    r3_lbl = p3.add_run("How TestForge implements it:\n")
    r3_lbl.font.bold = True
    r3_lbl.font.size = Pt(9.5)
    r3_lbl.font.color.rgb = COLOR_PRIMARY_NAVY
    r3_txt = p3.add_run(implementation)
    r3_txt.font.size = Pt(9.5)

    # Field 4: Example
    if example:
        p4 = cell.add_paragraph()
        p4.paragraph_format.space_after = Pt(4)
        r4_lbl = p4.add_run("Example:\n")
        r4_lbl.font.bold = True
        r4_lbl.font.size = Pt(9.5)
        r4_lbl.font.color.rgb = COLOR_PRIMARY_NAVY
        r4_txt = p4.add_run(example)
        r4_txt.font.size = Pt(9)
        r4_txt.font.name = "Consolas" if "def " in example or "assert " in example else "Calibri"

    # Field 5: Why this design was chosen
    p5 = cell.add_paragraph()
    p5.paragraph_format.space_after = Pt(4)
    r5_lbl = p5.add_run("Why this design was chosen:\n")
    r5_lbl.font.bold = True
    r5_lbl.font.size = Pt(9.5)
    r5_lbl.font.color.rgb = COLOR_PRIMARY_NAVY
    r5_txt = p5.add_run(why_design)
    r5_txt.font.size = Pt(9.5)

    # Field 6: Possible examiner follow-up
    p6 = cell.add_paragraph()
    p6.paragraph_format.space_after = Pt(4)
    r6_lbl = p6.add_run("Possible examiner follow-up & response:\n")
    r6_lbl.font.bold = True
    r6_lbl.font.size = Pt(9.5)
    r6_lbl.font.color.rgb = COLOR_ACCENT_AMBER
    r6_txt = p6.add_run(follow_up)
    r6_txt.font.size = Pt(9.5)

    # Field 7: Evidence and verification status
    p7 = cell.add_paragraph()
    p7.paragraph_format.space_after = Pt(2)
    r7_lbl = p7.add_run("Evidence and verification status: ")
    r7_lbl.font.bold = True
    r7_lbl.font.size = Pt(9)
    r7_lbl.font.color.rgb = COLOR_ACCENT_GREEN
    r7_txt = p7.add_run(evidence_status)
    r7_txt.font.size = Pt(9)
    r7_txt.font.bold = True

    # Spacing between questions
    doc.add_paragraph().paragraph_format.space_after = Pt(8)


# --- XML Helper Functions for XML Manipulation ---

def set_cell_shading(cell, color_hex: str):
    """Fills a cell with background color."""
    ns = nsdecls("w")
    shd = parse_xml(f'<w:shd {ns} w:fill="{color_hex}"/>')
    cell._tc.get_or_add_tcPr().append(shd)


def set_cell_padding(cell, top=60, bottom=60, left=100, right=100):
    """Sets cell margins/padding in dxa (1 pt = 20 dxa)."""
    ns = nsdecls("w")
    tcMar = parse_xml(
        f'<w:tcMar {ns}>'
        f'  <w:top w:w="{top}" w:type="dxa"/>'
        f'  <w:bottom w:w="{bottom}" w:type="dxa"/>'
        f'  <w:left w:w="{left}" w:type="dxa"/>'
        f'  <w:right w:w="{right}" w:type="dxa"/>'
        f'</w:tcMar>'
    )
    cell._tc.get_or_add_tcPr().append(tcMar)


def set_left_border_only(cell, color_hex: str, sz="36"):
    """Sets thick left accent border and clears top, bottom, right."""
    ns = nsdecls("w")
    borders = parse_xml(
        f'<w:tcBorders {ns}>'
        f'  <w:top w:val="none"/>'
        f'  <w:left w:val="single" w:sz="{sz}" w:space="0" w:color="{color_hex}"/>'
        f'  <w:bottom w:val="none"/>'
        f'  <w:right w:val="none"/>'
        f'</w:tcBorders>'
    )
    cell._tc.get_or_add_tcPr().append(borders)


def set_all_borders(cell, color_hex: str, sz="4"):
    """Sets identical subtle borders on all four sides."""
    ns = nsdecls("w")
    borders = parse_xml(
        f'<w:tcBorders {ns}>'
        f'  <w:top w:val="single" w:sz="{sz}" w:space="0" w:color="{color_hex}"/>'
        f'  <w:left w:val="single" w:sz="{sz}" w:space="0" w:color="{color_hex}"/>'
        f'  <w:bottom w:val="single" w:sz="{sz}" w:space="0" w:color="{color_hex}"/>'
        f'  <w:right w:val="single" w:sz="{sz}" w:space="0" w:color="{color_hex}"/>'
        f'</w:tcBorders>'
    )
    cell._tc.get_or_add_tcPr().append(borders)


def set_all_borders_except_left(cell, color_hex: str, sz="4"):
    """Keeps left border untouched, sets top, bottom, right."""
    ns = nsdecls("w")
    tcPr = cell._tc.get_or_add_tcPr()
    existing_borders = tcPr.find(qn("w:tcBorders"))
    if existing_borders is not None:
        left_elm = existing_borders.find(qn("w:left"))
        left_val = left_elm.get(qn("w:val")) if left_elm is not None else "single"
        left_sz = left_elm.get(qn("w:sz")) if left_elm is not None else "32"
        left_col = left_elm.get(qn("w:color")) if left_elm is not None else "1E3A8A"
    else:
        left_val, left_sz, left_col = "single", "32", "1E3A8A"

    new_borders = parse_xml(
        f'<w:tcBorders {ns}>'
        f'  <w:top w:val="single" w:sz="{sz}" w:space="0" w:color="{color_hex}"/>'
        f'  <w:left w:val="{left_val}" w:sz="{left_sz}" w:space="0" w:color="{left_col}"/>'
        f'  <w:bottom w:val="single" w:sz="{sz}" w:space="0" w:color="{color_hex}"/>'
        f'  <w:right w:val="single" w:sz="{sz}" w:space="0" w:color="{color_hex}"/>'
        f'</w:tcBorders>'
    )
    if existing_borders is not None:
        tcPr.remove(existing_borders)
    tcPr.append(new_borders)
