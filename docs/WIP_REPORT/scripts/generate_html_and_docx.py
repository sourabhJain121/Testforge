"""
generate_html_and_docx.py
Generates the HTML representation (for PDF compilation via agent-browser) and the native DOCX
for the redesigned TestForge Work in Progress Report.
"""
import os
import sys

COMMIT_SHA = "ee8f765c4f7316e87439fab7250103e6da651c02"
GITHUB_BASE = f"https://github.com/sourabhJain121/Testforge/blob/{COMMIT_SHA}"
ASSETS_DIR = "/Users/sourabh/TestForge/docs/WIP_REPORT/assets"
WIP_DIR = "/Users/sourabh/TestForge/docs/WIP_REPORT"

# Verify all required assets exist
required_assets = [
    "figure1_system_architecture.png",
    "figure2_execution_workflow.png",
    "figure3_blackboard_architecture.png",
    "figure4_mutation_refinement.png",
    "figure7_benchmark_comparison.png",
    "fresh_01_homepage.png",
    "fresh_02_discount_hardened.png",
    "figure5_logistics_hardened_kpi.png",
    "fresh_03_checkpoints_timeline.png"
]
for asset in required_assets:
    path = os.path.join(ASSETS_DIR, asset)
    if not os.path.exists(path):
        raise FileNotFoundError(f"Missing required asset: {path}")

print("All required image assets verified.")

