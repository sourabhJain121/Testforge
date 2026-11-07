with open("generate_html_template.html", "r", encoding="utf-8") as f:
    text = f.read()

# Replace page-breaks with comments (except right before Appendices)
parts = text.split("<!-- APPENDICES -->")
body_part = parts[0].replace('<div class="page-break"></div>', '')
appendices_part = '<div class="page-break"></div>\n<!-- APPENDICES -->' + parts[1]

new_text = body_part + appendices_part

# Update styling for tighter, professional layout
new_text = new_text.replace(
"""  .figure-img {
    max-width: 98%;
    height: auto;
    border: 1px solid #CCCCCC;
  }""",
"""  .figure-img {
    max-width: 85%;
    max-height: 215px;
    object-fit: contain;
    border: 1px solid #333333;
    display: inline-block;
  }
  .screenshot-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 8px;
    margin-top: 6px;
    margin-bottom: 8px;
    page-break-inside: avoid;
  }
  .screenshot-item {
    text-align: center;
  }
  .screenshot-item img {
    max-width: 100%;
    max-height: 160px;
    object-fit: contain;
    border: 1px solid #444444;
  }
  .screenshot-item .figure-caption {
    font-size: 7.5pt;
    margin-top: 2px;
  }"""
)

# Replace individual screenshot blocks in Chapter 8 with a 2x2 grid or clean pairs
old_screenshots = """<div class="figure-container">
  <img src="assets/fresh_01_homepage.png" class="figure-img" alt="Figure 3: Dashboard Standby View">
  <div class="figure-caption">Figure 3: TestForge Unified Application Dashboard and System Health Overview (Captured live: 2026-11-02 02:29).</div>
</div>

<div class="figure-container">
  <img src="assets/fresh_02_discount_hardened.png" class="figure-img" alt="Figure 4: Discount Hardening Results">
  <div class="figure-caption">Figure 4: Automated Test Generation and Mutation Testing Terminal KPI Results for discount.py (89.5% Mutation Score, 17 Killed, 2 Survived, 100% Statement Coverage; Captured live: 2026-11-02 02:30).</div>
</div>

<div class="figure-container">
  <img src="assets/figure5_logistics_hardened_kpi.png" class="figure-img" alt="Figure 5: Logistics Hardening Results">
  <div class="figure-caption">Figure 5: Enterprise Multi-Callable Hardening Terminal Results for uploaded_logistics_engine.py (64 Tests, 176 Mutants Killed, 68.22% Raw Score, 90.15% Coverage; Captured: 2026-10-31 14:55).</div>
</div>

<div class="figure-container">
  <img src="assets/fresh_03_checkpoints_timeline.png" class="figure-img" alt="Figure 6: SQLite Checkpoint Timeline">
  <div class="figure-caption">Figure 6: Persistent Blackboard Checkpoint Timeline in SQLite showing Atomic Revisions and Semantic Diff Controls (Captured live: 2026-11-02 02:30).</div>
</div>"""

new_screenshots = """<div class="screenshot-grid">
  <div class="screenshot-item">
    <img src="assets/fresh_01_homepage.png" alt="Figure 3: Dashboard Standby View">
    <div class="figure-caption">Figure 3: TestForge Unified Application Dashboard and System Health Overview (Captured live: 2026-11-02 02:29).</div>
  </div>
  <div class="screenshot-item">
    <img src="assets/fresh_02_discount_hardened.png" alt="Figure 4: Discount Hardening Results">
    <div class="figure-caption">Figure 4: Automated Test Generation and Mutation Terminal Results for discount.py (89.5% Score, 17 Killed, 2 Survived, 100% Coverage; Captured live: 2026-11-02 02:30).</div>
  </div>
  <div class="screenshot-item">
    <img src="assets/figure5_logistics_hardened_kpi.png" alt="Figure 5: Logistics Hardening Results">
    <div class="figure-caption">Figure 5: Enterprise Multi-Callable Hardening Terminal Results for uploaded_logistics_engine.py (64 Tests, 176 Mutants Killed, 68.22% Raw Score; Captured: 2026-10-31 14:55).</div>
  </div>
  <div class="screenshot-item">
    <img src="assets/fresh_03_checkpoints_timeline.png" alt="Figure 6: SQLite Checkpoint Timeline">
    <div class="figure-caption">Figure 6: Persistent Blackboard Checkpoint Timeline in SQLite showing Atomic Revisions and Diff Controls (Captured live: 2026-11-02 02:30).</div>
  </div>
</div>"""

new_text = new_text.replace(old_screenshots, new_screenshots)

with open("generate_html_template.html", "w", encoding="utf-8") as f:
    f.write(new_text)

print("Updated template successfully.")
