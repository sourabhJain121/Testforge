import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches

OUT_PATH = "docs/screenshots/report_assets/pipeline_flow_diagram.png"
os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)

plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = ["Helvetica", "Arial", "DejaVu Sans"]

def create_pipeline_diagram():
    fig, ax = plt.subplots(figsize=(15, 8.5), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")
    fig.patch.set_facecolor("#FFFFFF")
    ax.set_facecolor("#FFFFFF")

    # Header
    ax.text(50, 96, "Figure 5.0: TestForge Step-by-Step Multi-Agent Pipeline & Convergence Stop-Rules", 
            ha="center", va="center", fontsize=15, fontweight="bold", color="#1E293B")
    ax.text(50, 92.5, "Autonomous Execution Flow from Ingestion to Submodular Suite Minimization (Modeled on OptiFlow-X Section 5.3.1)", 
            ha="center", va="center", fontsize=9.5, color="#64748B")

    # 7 Step Boxes (Arranged in a balanced 2-row serpentine or horizontal layout)
    # Row 1 (Steps 1 to 4): Left to Right
    # Row 2 (Steps 5 to 7): Right to Left or clean structured grid
    steps_row1 = [
        ("Step 1: Code Intelligence", "CodeIntelligenceAgent (CrewAI)", 
         "• AST symbol parsing\n• Cyclomatic complexity\n• Call-graph blast radius\n• Stateful class detection", 
         4, 58, 20, 26, "#F0FDF4", "#16A34A", "#15803D"),
        ("Step 2: Sequence Planner", "StatefulSequencePlanner", 
         "• Constructor attribute maps\n• Mutator/accessor chains\n• State transition paths\n• Eviction trigger models", 
         28, 58, 20, 26, "#FAF5FF", "#9333EA", "#7E22CE"),
        ("Step 3: ADK Generator", "UnitTestGenerator (Google ADK)", 
         "• Multi-turn tool calling\n• Sequence test synthesis\n• Boundary condition infill\n• Pydantic contract specs", 
         52, 58, 20, 26, "#EFF6FF", "#2563EB", "#1D4ED8"),
        ("Step 4: DEF-022 Preflight", "SandboxedRunner (Preflight Gate)", 
         "• Base unmutated test run\n• Mandatory 100% Pass@1\n• Exit 127 on test failure\n• Zero-tolerance syntax filter", 
         76, 58, 20, 26, "#FEF2F2", "#DC2626", "#B91C1C")
    ]

    for title, subtitle, desc, x, y, w, h, bg, border, tcol in steps_row1:
        box = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=1.2", 
                                     facecolor=bg, edgecolor=border, linewidth=2)
        ax.add_patch(box)
        ax.text(x + w/2, y + h - 3.5, title, ha="center", va="center", fontsize=9.5, fontweight="bold", color=tcol)
        ax.text(x + w/2, y + h - 7.5, subtitle, ha="center", va="center", fontsize=7.2, fontweight="bold", color="#475569")
        ax.text(x + 1.2, y + 8, desc, ha="left", va="center", fontsize=7.2, color="#1E293B", linespacing=1.35)

    # Arrows Row 1
    ax.annotate("", xy=(28, 71), xytext=(24, 71), arrowprops=dict(arrowstyle="->", color="#16A34A", lw=2, mutation_scale=14))
    ax.annotate("", xy=(52, 71), xytext=(48, 71), arrowprops=dict(arrowstyle="->", color="#9333EA", lw=2, mutation_scale=14))
    ax.annotate("", xy=(76, 71), xytext=(72, 71), arrowprops=dict(arrowstyle="->", color="#2563EB", lw=2, mutation_scale=14))

    # Connector Row 1 to Row 2 (Down from Step 4 to Step 5)
    ax.annotate("", xy=(86, 48), xytext=(86, 58), arrowprops=dict(arrowstyle="->", color="#DC2626", lw=2, mutation_scale=14))

    # Row 2 (Steps 5 to 7): Right to Left
    steps_row2 = [
        ("Step 5: Mutation Testing", "MutationTestingAgent (MCP)", 
         "• 10 AST mutation operators\n• Boundary & relational swaps\n• Equivalence invariant pruning\n• 8-worker parallel execution", 
         76, 20, 20, 26, "#FFFBEB", "#D97706", "#B45309"),
        ("Step 6: Critic Reflection Loop", "AdversarialCritic (CrewAI)", 
         "• Surviving mutant diff review\n• Boundary testing directives\n• Dynamic re-planning handoff\n• Convergence verification", 
         40, 20, 32, 26, "#FEF2F2", "#DC2626", "#B91C1C"),
        ("Step 7: Suite Minimizer", "TestSuiteMinimizer (Set Cover)", 
         "• Greedy submodular solver\n• Marginal kill optimization\n• 78.3% test suite reduction\n• 100% kill score retention", 
         4, 20, 32, 26, "#F1F5F9", "#0F172A", "#0F172A")
    ]

    for title, subtitle, desc, x, y, w, h, bg, border, tcol in steps_row2:
        box = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=1.2", 
                                     facecolor=bg, edgecolor=border, linewidth=2)
        ax.add_patch(box)
        ax.text(x + w/2, y + h - 3.5, title, ha="center", va="center", fontsize=9.5, fontweight="bold", color=tcol)
        ax.text(x + w/2, y + h - 7.5, subtitle, ha="center", va="center", fontsize=7.2, fontweight="bold", color="#475569")
        ax.text(x + 1.5, y + 8, desc, ha="left", va="center", fontsize=7.2, color="#1E293B", linespacing=1.35)

    # Arrows Row 2
    ax.annotate("", xy=(72, 33), xytext=(76, 33), arrowprops=dict(arrowstyle="->", color="#D97706", lw=2, mutation_scale=14))
    ax.annotate("", xy=(36, 33), xytext=(40, 33), arrowprops=dict(arrowstyle="->", color="#DC2626", lw=2, mutation_scale=14))

    # Reflection Loop Arrow (Step 6 back to Step 3)
    ax.annotate("", xy=(62, 58), xytext=(56, 46),
                arrowprops=dict(arrowstyle="->", color="#DC2626", lw=2, ls="--", connectionstyle="arc3,rad=-0.25", mutation_scale=14))
    ax.text(64, 52, "Adversarial Feedback\n(If Score < 85% & Iter < 3)", fontsize=7.5, fontweight="bold", color="#B91C1C", ha="center")

    # Bottom Banner: Stop Rules & Convergence Criteria
    stop_box = patches.FancyBboxPatch((4, 3), 92, 13, boxstyle="round,pad=1", 
                                      facecolor="#F8FAFC", edgecolor="#0284C7", linewidth=1.5)
    ax.add_patch(stop_box)
    ax.text(6, 12.5, "CORE CONVERGENCE STOP-RULES (testforge/supervisor.py & core/budget):", 
            fontsize=8.5, fontweight="bold", color="#0369A1")
    ax.text(6, 8, 
            "• Stop Rule 1 (Target Score Reached): Mutation Score >= 85.0% across verified mutants -> Terminate loop & transition to FINALIZE.\n"
            "• Stop Rule 2 (Budget Exhaustion): Maximum iteration count reached (iter == 3) -> Save best candidate suite and prevent runaway token spend.\n"
            "• Stop Rule 3 (Never-Regress Guard): If candidate suite k has fewer kills than suite k-1 -> Trigger transactional Git & SQLite rollback.\n"
            "• Preflight Gate (DEF-022): Candidate suite must achieve 100% Pass@1 on unmutated source; syntax/runtime errors abort with exit code 127.",
            fontsize=7.2, color="#334155", linespacing=1.35)

    plt.tight_layout()
    plt.savefig(OUT_PATH, dpi=300, bbox_inches="tight")
    plt.close()
    print("Saved pipeline_flow_diagram.png successfully!")

if __name__ == "__main__":
    create_pipeline_diagram()
