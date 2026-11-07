with open("generate_html_template.html", "r", encoding="utf-8") as f:
    text = f.read()

# Remove the page break before Appendices
text = text.replace('<div class="page-break"></div>\n<!-- APPENDICES -->', '<!-- APPENDICES -->')

# Tighten margins and spacing to target ~12-13 pages for core chapters
text = text.replace('margin: 18mm 16mm 18mm 16mm;', 'margin: 14mm 14mm 14mm 14mm;')
text = text.replace('font-size: 9.5pt;', 'font-size: 9pt;')
text = text.replace('line-height: 1.35;', 'line-height: 1.28;')
text = text.replace('max-height: 215px;', 'max-height: 185px;')
text = text.replace('max-height: 160px;', 'max-height: 140px;')
text = text.replace('margin-top: 14px;', 'margin-top: 8px;')
text = text.replace('margin-bottom: 6px;', 'margin-bottom: 4px;')

with open("generate_html_template.html", "w", encoding="utf-8") as f:
    f.write(text)

print("Tuned template successfully.")
