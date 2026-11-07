import matplotlib.pyplot as plt
import matplotlib.patches as patches
import os

os.makedirs("docs/WIP_REPORT/assets", exist_ok=True)

# -----------------------------------------------------------------------------
# FIGURE 1: Overall TestForge System Architecture
# Pure white background, black borders, black text, black arrows, rectangular boxes.
# -----------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(11, 7.5), dpi=300)
fig.patch.set_facecolor('white')
ax.set_facecolor('white')
ax.set_xlim(0, 110)
ax.set_ylim(0, 75)
ax.axis('off')

# Outer Title
ax.text(55, 72.5, "Figure 1: Overall TestForge System Architecture", 
        fontsize=12, fontweight='bold', ha='center', va='center', color='black')

def draw_box(x, y, w, h, title, subtitle=None, sub_items=None):
    rect = patches.Rectangle((x, y), w, h, linewidth=1.2, edgecolor='black', facecolor='white', zorder=2)
    ax.add_patch(rect)
    if subtitle:
        ax.text(x + w/2, y + h - 1.8, title, fontsize=9, fontweight='bold', ha='center', va='top', color='black')
        ax.text(x + w/2, y + h - 3.8, subtitle, fontsize=7.5, fontstyle='italic', ha='center', va='top', color='black')
    else:
        ax.text(x + w/2, y + h/2 + (1.2 if sub_items else 0), title, fontsize=8.5, fontweight='bold', ha='center', va='center', color='black')
    if sub_items:
        start_y = y + h - 5.5
        for item in sub_items:
            ax.text(x + 1.5, start_y, item, fontsize=7, ha='left', va='center', color='black', family='monospace')
            start_y -= 1.8

def draw_arrow(x1, y1, x2, y2, label=None, label_offset=(0, 1.2)):
    ax.annotate('', xy=(x2, y2), xytext=(x1, y1),
                arrowprops=dict(arrowstyle="->", color="black", lw=1.2, shrinkA=2, shrinkB=2), zorder=3)
    if label:
        ax.text((x1 + x2)/2 + label_offset[0], (y1 + y2)/2 + label_offset[1], label, 
                fontsize=6.5, ha='center', va='center', color='black', backgroundcolor='white')

# 1. UI Layer
draw_box(5, 58, 26, 11, "Unified Web Cockpit", "frontend/ (app.js, index.html)", 
         ["- Glassmorphic Single-Page UI", "- Real-Time WebSocket Telemetry", "- Interactive Checkpoint Timeline"])

# 2. API & Server Tier
draw_box(42, 58, 26, 11, "FastAPI Backend & Hub", "server.py (Port 8000)", 
         ["- 42 REST API Endpoints", "- WebSocket Streaming Hub", "- Health & A2A Discovery Probes"])

# 3. Hardening Orchestrator Tier
draw_box(79, 58, 26, 11, "Master Orchestrator", "testforge/orchestrator.py", 
         ["- Closed-Loop Reflection Engine", "- Cooperative Timeout Control", "- Lifecycle Checkpoint Trigger"])

# Connect Top Row
draw_arrow(31, 63.5, 42, 63.5, "HTTP / WS")
draw_arrow(68, 63.5, 79, 63.5, "Direct Invocation")

# 4. Cognitive Multi-Agent Tier (Middle)
draw_box(5, 34, 28, 17, "Target & Security Ingestion", "testforge/ingestion.py, security.py",
         ["- AST Source Parser & Analyzer", "- Forbidden Node Filter (AST)", "- SSRF & Redirect Defense", "- Prompt Injection Defuser"])

draw_box(41, 34, 28, 17, "Test Generation Agents", "intelligent_generator.py, adk_generator.py",
         ["- AST Comparison Analyzer", "- Boundary & Guard Synthesizer", "- Multi-Callable Coverage (100%)", "- Google ADK Runner & LlmAgent"])

draw_box(77, 34, 28, 17, "Adversarial Critic Agent", "testforge/crew_critic.py, agents.py",
         ["- CrewAI Mutation Specialist", "- Surviving Mutant AST Differ", "- Semantics-Aware Critique", "- Reflection Directives"])

# Connect Orchestrator down to Agents
draw_arrow(92, 58, 91, 51, "Coordinates")
draw_arrow(79, 60, 55, 51, "Coordinates")
draw_arrow(55, 58, 19, 51, "Ingests")

# 5. Shared Memory & Communication Tier (Bottom Center)
draw_box(5, 8, 45, 19, "Thread-Safe Blackboard Context", "testforge/blackboard.py (RLock Protected)",
         ["- TargetSpace (Ingested Code & AST)", "- MutantSpace (258 Mutants & Unified Diffs)",
          "- CriticSpace (Structured Directives)", "- SuiteSpace (Candidate & Validated Suites)",
          "- MetricsSpace (Coverage, Kills, Mutation Score)", "- Pattern-Matching Pub/Sub Dispatcher"])

draw_box(55, 8, 23, 19, "SQLite WAL Persistence", "testforge/persistence.py",
         ["- 1,104 Atomic Snapshots", "- testforge_checkpoints.db", "- Deterministic Resumption", "- Differential Audit Engine"])

draw_box(83, 8, 22, 19, "Sandboxed Test Execution", "testforge/sandbox.py, mutator.py",
         ["- Parallel Sandbox Runner", "- AST Mutator (9 Operators)", "- Subprocess Isolation (10s)", "- Granular Assertion Validator"])

# Inter-tier Connections
draw_arrow(19, 34, 19, 27, "Target Code")
draw_arrow(55, 34, 45, 27, "Test Suites")
draw_arrow(91, 34, 89, 27, "Mutant Diffs")

draw_arrow(50, 17.5, 55, 17.5, "Auto-Save / Diff")
draw_arrow(78, 17.5, 83, 17.5, "Evaluates")
draw_arrow(83, 22, 50, 22, "Kills / Coverage")

plt.tight_layout()
fig.savefig("docs/WIP_REPORT/assets/figure1_system_architecture.png", dpi=300, facecolor='white')
plt.close(fig)
print("Figure 1 generated successfully.")

# -----------------------------------------------------------------------------
# FIGURE 2: Multi-Agent Execution Workflow
# Pure white background, black borders, black text, black arrows, rectangular boxes.
# -----------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(11, 7.5), dpi=300)
fig.patch.set_facecolor('white')
ax.set_facecolor('white')
ax.set_xlim(0, 110)
ax.set_ylim(0, 75)
ax.axis('off')

ax.text(55, 72.5, "Figure 2: Multi-Agent Test Hardening Execution Workflow", 
        fontsize=12, fontweight='bold', ha='center', va='center', color='black')

def draw_step(x, y, w, h, step_no, title, details):
    rect = patches.Rectangle((x, y), w, h, linewidth=1.2, edgecolor='black', facecolor='white', zorder=2)
    ax.add_patch(rect)
    ax.text(x + 2, y + h - 2, f"Step {step_no}: {title}", fontsize=8.5, fontweight='bold', ha='left', va='top', color='black')
    start_y = y + h - 4.5
    for d in details:
        ax.text(x + 2.5, start_y, d, fontsize=7, ha='left', va='center', color='black')
        start_y -= 1.8

# Top Row: Ingestion -> Callable Discovery -> Baseline Synthesis -> Sandbox Validation
draw_step(5, 52, 22, 16, "1", "Source Ingestion", 
          ["- Read Target Code (.py)", "- AST Syntax Verification", "- Security Guardrail Scan", "- Publish to TargetSpace"])

draw_step(31, 52, 22, 16, "2", "Callable Discovery", 
          ["- AST Comparison Inspection", "- Extract All 10 Callables", "- Extract Guard Thresholds", "- Build Nominal Dict"])

draw_step(57, 52, 22, 16, "3", "Candidate Synthesis", 
          ["- Nominal Happy Path Tests", "- Boundary Condition Cases", "- Negative Exception Tests", "- Strict Value Assertions"])

draw_step(83, 52, 22, 16, "4", "Pass@1 Validation", 
          ["- Compile Candidate Suite", "- Sandbox Clean Execution", "- Filter Failing Tests", "- Store in SuiteSpace"])

draw_arrow(27, 60, 31, 60)
draw_arrow(53, 60, 57, 60)
draw_arrow(79, 60, 83, 60)

# Middle Turn: Step 4 down to Step 5
draw_arrow(94, 52, 94, 44)

# Middle Row: Mutation Injection -> Parallel Sandbox -> Adversarial Critique
draw_step(83, 27, 22, 17, "5", "Mutation Injection", 
          ["- AST Mutator Traversal", "- 9 Operator Families", "- Generate 258 Mutants", "- Publish to MutantSpace"])

draw_step(44, 27, 33, 17, "6", "Parallel Mutant Evaluation", 
          ["- Isolated Temporary Subprocesses", "- Run Suite against 258 Mutants", "- Measure Statement Coverage (90.15%)", "- Track Kills (176) & Survivors (82)"])

draw_step(5, 27, 33, 17, "7", "Adversarial Critique", 
          ["- CrewAI Mutation Specialist", "- Analyze AST Unified Diffs", "- Identify Uncovered Conditions", "- Issue Reflection Directives"])

draw_arrow(83, 35.5, 77, 35.5)
draw_arrow(44, 35.5, 38, 35.5)

# Bottom Row: Feedback Decision & Hardened Suite Export
# Decision Diamond
diamond = patches.Polygon([[21.5, 17], [32.5, 10.5], [21.5, 4], [10.5, 10.5]],
                          closed=True, linewidth=1.2, edgecolor='black', facecolor='white', zorder=2)
ax.add_patch(diamond)
ax.text(21.5, 12, "Terminal Gate?", fontsize=8, fontweight='bold', ha='center', va='center', color='black')
ax.text(21.5, 9, "(Score ≥ 85% or\nIters ≥ 3)", fontsize=6.5, ha='center', va='center', color='black')

draw_arrow(21.5, 27, 21.5, 17, "Check Verdict")

# Loop Back Arrow (No)
ax.annotate('', xy=(68, 52), xytext=(32.5, 10.5),
            arrowprops=dict(arrowstyle="->", color="black", lw=1.2,
                            connectionstyle="angle,angleA=0,angleB=90,rad=0"), zorder=3)
ax.text(50, 11.5, "NO (Refine Suite with Critic Directives)", fontsize=7, ha='center', va='bottom', color='black', backgroundcolor='white')

# Final Exit Arrow (Yes)
draw_step(60, 3, 45, 15, "8", "Final Hardened Suite Export",
          ["- Atomic SQLite Checkpoint Commit (testforge_checkpoints.db)",
           "- Export Final test_hardened.py to Disk",
           "- Generate SHA-256 Provenance Manifest (Identical Hashes)",
           "- Stream Final KPIs & AST Diffs to Web Cockpit"])

draw_arrow(32.5, 10.5, 60, 10.5, "YES (Finalize)")

plt.tight_layout()
fig.savefig("docs/WIP_REPORT/assets/figure2_execution_workflow.png", dpi=300, facecolor='white')
plt.close(fig)
print("Figure 2 generated successfully.")

# -----------------------------------------------------------------------------
# FIGURE 7: Mutation Hardening Benchmark Comparison Graph
# High-contrast publication chart: Baseline Raw vs Hardened Raw vs Hardened Adjusted
# -----------------------------------------------------------------------------
import numpy as np

fig, ax = plt.subplots(figsize=(8.5, 4.8), dpi=300)
fig.patch.set_facecolor('white')
ax.set_facecolor('white')

benchmarks = ['Discount Benchmark\n(19 Mutants, 1 Callable)', 'Logistics Engine Benchmark\n(258 Mutants, 10 Callables)']
x = np.arange(len(benchmarks))
width = 0.22

# Data
baseline_raw = [5.26, 3.10]
hardened_raw = [89.47, 68.22]
hardened_adj = [94.44, 75.21]

rects1 = ax.bar(x - width, baseline_raw, width, label='Initial Baseline (Raw)', color='#D3D3D3', edgecolor='black', linewidth=1)
rects2 = ax.bar(x, hardened_raw, width, label='TestForge Hardened (Raw)', color='#505050', edgecolor='black', linewidth=1)
rects3 = ax.bar(x + width, hardened_adj, width, label='TestForge Hardened (Adjusted)', color='#101010', edgecolor='black', linewidth=1)

ax.set_ylabel('Mutation Score (%)', fontsize=10, fontweight='bold', color='black')
ax.set_title('Figure 7: Mutation Score Comparison: Baseline vs. TestForge Hardened', fontsize=11, fontweight='bold', pad=14, color='black')
ax.set_xticks(x)
ax.set_xticklabels(benchmarks, fontsize=9.5, fontweight='bold', color='black')
ax.set_ylim(0, 112)
ax.legend(loc='upper left', frameon=True, edgecolor='black', fontsize=8.5)
ax.grid(axis='y', linestyle='--', alpha=0.5, color='gray')
ax.spines['top'].set_visible(False)
ax.spines['right'].set_visible(False)
ax.spines['left'].set_color('black')
ax.spines['bottom'].set_color('black')

def autolabel(rects, is_bold=False):
    for rect in rects:
        height = rect.get_height()
        ax.annotate(f'{height:.2f}%',
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0, 3),  # 3 points vertical offset
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=8,
                    fontweight='bold' if is_bold else 'normal', color='black')

autolabel(rects1)
autolabel(rects2, is_bold=True)
autolabel(rects3, is_bold=True)

# Add annotation on Discount live UI score
ax.annotate('Live Demo: 94.74% (18/19 killed)', xy=(0, 89.47), xytext=(-0.25, 102),
            arrowprops=dict(arrowstyle="->", color="black", lw=0.9),
            fontsize=7.5, fontstyle='italic', bbox=dict(boxstyle="square,pad=0.3", fc="white", ec="black", lw=0.8))

plt.tight_layout()
fig.savefig("docs/WIP_REPORT/assets/figure7_benchmark_comparison.png", dpi=300, facecolor='white')
plt.close(fig)
print("Figure 7 generated successfully.")
