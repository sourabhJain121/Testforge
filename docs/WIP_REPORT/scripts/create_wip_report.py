import os
import sys
import docx
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml import OxmlElement, parse_xml
from docx.oxml.ns import nsdecls, qn

DOCX_OUT = "docs/WIP_REPORT/TestForge_WIP_Report.docx"
HTML_OUT = "docs/WIP_REPORT/report_print.html"
ASSETS = "docs/WIP_REPORT/assets"

COMMIT_SHA = "ee8f765c4f7316e87439fab7250103e6da651c02"
GITHUB_BASE = f"https://github.com/sourabhJain121/Testforge/blob/{COMMIT_SHA}"

def add_p_hyperlink(p, url, text):
    part = p.part
    r_id = part.relate_to(url, docx.opc.constants.RELATIONSHIP_TYPE.HYPERLINK, is_external=True)
    hyperlink = parse_xml(f'<w:hyperlink {nsdecls("w")} r:id="{r_id}"/>')
    r = parse_xml(f'<w:r {nsdecls("w")}><w:rPr><w:color w:val="0044BB"/><w:u w:val="single"/></w:rPr><w:t>{text}</w:t></w:r>')
    hyperlink.append(r)
    p._p.append(hyperlink)

def style_cell(cell, fill_hex=None, bold=False, font_size=8.5, align=WD_ALIGN_PARAGRAPH.LEFT):
    tcPr = cell._tc.get_or_add_tcPr()
    if fill_hex:
        shd = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{fill_hex}"/>')
        tcPr.append(shd)
    tcMar = OxmlElement('w:tcMar')
    for m, val in [('w:top', 90), ('w:bottom', 90), ('w:left', 120), ('w:right', 120)]:
        node = OxmlElement(m)
        node.set(qn('w:w'), str(val))
        node.set(qn('w:type'), 'dxa')
        tcMar.append(node)
    tcPr.append(tcMar)
    for p in cell.paragraphs:
        p.alignment = align
        for r in p.runs:
            r.font.name = 'Arial'
            r.font.size = Pt(font_size)
            r.font.bold = bold

def set_tbl_borders(table):
    tblPr = table._tbl.tblPr
    borders = parse_xml(
        f'<w:tblBorders {nsdecls("w")}>'
        f'  <w:top w:val="single" w:sz="6" w:space="0" w:color="333333"/>'
        f'  <w:bottom w:val="single" w:sz="6" w:space="0" w:color="333333"/>'
        f'  <w:left w:val="none"/>'
        f'  <w:right w:val="none"/>'
        f'  <w:insideH w:val="single" w:sz="4" w:space="0" w:color="E0E0E0"/>'
        f'  <w:insideV w:val="none"/>'
        f'</w:tblBorders>'
    )
    tblPr.append(borders)

print("Setup completed successfully.")
