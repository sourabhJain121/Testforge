import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches

OUT_DIR = "docs/screenshots/report_assets"
os.makedirs(OUT_DIR, exist_ok=True)

plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = ["Helvetica", "Arial", "DejaVu Sans"]

def create_architecture_diagram():
    fig, ax = plt.subplots(figsize=(12, 7.5), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")

    # Background canvas
    fig.patch.set_facecolor("#FFFFFF")
    ax.set_facecolor("#FFFFFF")

    # Title
    ax.text(50, 96, "TestForge Multi-Agent Hierarchical Blackboard Architecture", 
            ha="center", va="center", fontsize=15, fontweight="bold", color="#1E293B")
    ax.text(50, 93, "Dual-Framework Orchestration: Google ADK Supervisor + CrewAI Adversarial Intelligence", 
            ha="center", va="center", fontsize=10, color="#64748B")

    # Central Blackboard
    bb = patches.FancyBboxPatch((28, 42), 44, 20, boxstyle="round,pad=1.5", 
                                facecolor="#F8FAFC", edgecolor="#0284C7", linewidth=2.5)
    ax.add_patch(bb)
    ax.text(50, 56, "Centralized SQLite WAL Blackboard", ha="center", va="center", 
            fontsize=12, fontweight="bold", color="#0369A1")
    ax.text(50, 52, "Revision-Controlled Typed State (schema_version: 1.0.0)", ha="center", va="center", 
            fontsize=8.5, color="#0F172A")
    ax.text(50, 48, "• AST Symbols & Call Graph   • Candidate Test Suites (v0...vk)\n• Surviving/Killed Mutants   • Execution Spans & Checkpoints", 
            ha="center", va="center", fontsize=8, color="#334155")

    # Top: Hierarchical Supervisor (Google ADK)
    sup = patches.FancyBboxPatch((32, 75), 36, 13, boxstyle="round,pad=1.2", 
                                 facecolor="#EFF6FF", edgecolor="#2563EB", linewidth=2)
    ax.add_patch(sup)
    ax.text(50, 83.5, "Hierarchical Supervisor Agent", ha="center", va="center", 
            fontsize=11, fontweight="bold", color="#1E40AF")
    ax.text(50, 80, "Framework: Google Agent Development Kit (ADK)", ha="center", va="center", 
            fontsize=8.5, fontweight="bold", color="#2563EB")
    ax.text(50, 76.5, "6-Stage FSM Orchestration • Dynamic Re-planning • Convergence Gating", ha="center", va="center", 
            fontsize=7.5, color="#475569")

    # Bidirectional arrow Supervisor <-> Blackboard
    ax.annotate("", xy=(50, 62), xytext=(50, 75),
                arrowprops=dict(arrowstyle="<->", color="#2563EB", lw=2, mutation_scale=15))
    ax.text(51.5, 68.5, "State Sync & Stage Gating", fontsize=7.5, color="#1E40AF", fontweight="bold")

    # Left Worker Agents (CrewAI / Code Intelligence)
    agents_left = [
        ("Code Intelligence Agent", "Static AST parsing, symbol extraction,\ncyclomatic complexity, stateful class detection", 8, 70, "#F0FDF4", "#16A34A"),
        ("Stateful Sequence Planner", "Multi-step constructor mutation sequences,\nstate-transition graph path extraction", 8, 48, "#FAF5FF", "#9333EA"),
        ("Mutation Testing Agent", "MutPy-style AST operator mutations,\nsyntax verification & equivalence check", 8, 26, "#FFFBEB", "#D97706")
    ]

    for name, desc, x, y, bg, border in agents_left:
        box = patches.FancyBboxPatch((x, y), 24, 15, boxstyle="round,pad=1", 
                                     facecolor=bg, edgecolor=border, linewidth=1.5)
        ax.add_patch(box)
        ax.text(x + 12, y + 11.5, name, ha="center", va="center", fontsize=9, fontweight="bold", color="#0F172A")
        ax.text(x + 12, y + 6.5, desc, ha="center", va="center", fontsize=7, color="#334155")
        # Arrow to blackboard
        ax.annotate("", xy=(28, 52), xytext=(x + 24, y + 7.5),
                    arrowprops=dict(arrowstyle="->", color=border, lw=1.5, mutation_scale=12))

    # Right Worker Agents (Generation, Critique, Execution, Minimization)
    agents_right = [
        ("Unit Test Generator Agent", "Google ADK multi-turn synthesis,\nboundary exploration & sequence assertions", 68, 70, "#EFF6FF", "#2563EB"),
        ("Adversarial Critic Agent", "CrewAI autonomous critic persona,\nsemantic diff analysis & directive formulation", 68, 48, "#FEF2F2", "#DC2626"),
        ("Sandboxed Test Runner", "Subprocess RLIMIT execution (CPU 3s, 256MB),\nzero-egress socket monkeypatching", 68, 26, "#F8FAFC", "#475569")
    ]

    for name, desc, x, y, bg, border in agents_right:
        box = patches.FancyBboxPatch((x, y), 24, 15, boxstyle="round,pad=1", 
                                     facecolor=bg, edgecolor=border, linewidth=1.5)
        ax.add_patch(box)
        ax.text(x + 12, y + 11.5, name, ha="center", va="center", fontsize=9, fontweight="bold", color="#0F172A")
        ax.text(x + 12, y + 6.5, desc, ha="center", va="center", fontsize=7, color="#334155")
        # Arrow to/from blackboard
        ax.annotate("", xy=(x, y + 7.5), xytext=(72, 52),
                    arrowprops=dict(arrowstyle="<-", color=border, lw=1.5, mutation_scale=12))

    # Bottom: Test Suite Minimizer
    min_box = patches.FancyBboxPatch((32, 10), 36, 12, boxstyle="round,pad=1", 
                                     facecolor="#F1F5F9", edgecolor="#0F172A", linewidth=1.5)
    ax.add_patch(min_box)
    ax.text(50, 18, "Test Suite Minimizer Agent", ha="center", va="center", 
            fontsize=10, fontweight="bold", color="#0F172A")
    ax.text(50, 13.5, "Greedy Set Cover Optimization • Sub-modular Kill Matrix Compression\nRetains 100% Mutation Score with ~78% Test Count Reduction", 
            ha="center", va="center", fontsize=7.5, color="#334155")
    ax.annotate("", xy=(50, 22), xytext=(50, 42),
                arrowprops=dict(arrowstyle="->", color="#0F172A", lw=1.5, mutation_scale=12))

    plt.tight_layout()
    plt.savefig(f"{OUT_DIR}/architecture_diagram.png", dpi=300, bbox_inches="tight")
    plt.close()
    print("Saved architecture_diagram.png")

def create_fastmcp_diagram():
    fig, ax = plt.subplots(figsize=(11, 6), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")
    fig.patch.set_facecolor("#FFFFFF")

    ax.text(50, 95, "FastMCP Agent-Tool Integration Architecture", 
            ha="center", va="center", fontsize=14, fontweight="bold", color="#1E293B")
    ax.text(50, 91, "Standardized JSON-RPC stdio Protocol Bridging Autonomous Agents and Deterministic Tooling", 
            ha="center", va="center", fontsize=9, color="#64748B")

    # Agent Layer (Left)
    agent_box = patches.FancyBboxPatch((6, 25), 26, 50, boxstyle="round,pad=1.2", 
                                       facecolor="#EFF6FF", edgecolor="#2563EB", linewidth=2)
    ax.add_patch(agent_box)
    ax.text(19, 70, "Multi-Agent System", ha="center", va="center", fontsize=11, fontweight="bold", color="#1E40AF")
    ax.text(19, 64, "(Google ADK + CrewAI)", ha="center", va="center", fontsize=9, color="#2563EB")
    ax.text(19, 52, "• Code Intelligence Agent\n• Mutation Testing Agent\n• Test Generator Agent\n• Adversarial Critic Agent\n• Sandboxed Runner Agent", 
            ha="center", va="center", fontsize=8, color="#1E293B")

    # Protocol Bus (Center)
    bus_box = patches.FancyBboxPatch((38, 30), 24, 40, boxstyle="round,pad=1.2", 
                                     facecolor="#F8FAFC", edgecolor="#0284C7", linewidth=2)
    ax.add_patch(bus_box)
    ax.text(50, 64, "FastMCP stdio Bridge", ha="center", va="center", fontsize=11, fontweight="bold", color="#0369A1")
    ax.text(50, 58, "JSON-RPC 2.0 Transport", ha="center", va="center", fontsize=8.5, fontweight="bold", color="#0284C7")
    ax.text(50, 46, "• Pydantic v2 Schema Validation\n• Zero Network Attack Surface\n• Subprocess Pipe Isolation\n• Standardized Tool Call Dispatch", 
            ha="center", va="center", fontsize=7.5, color="#334155")

    # Arrows between Agent and Bus
    ax.annotate("", xy=(38, 52), xytext=(32, 52),
                arrowprops=dict(arrowstyle="<->", color="#0284C7", lw=2, mutation_scale=15))
    ax.text(35, 55, "stdio", ha="center", va="center", fontsize=8, fontweight="bold", color="#0284C7")

    # 4 MCP Tools (Right)
    tools = [
        ("mcp_ast_symbol_analyzer", "Extracts functions, arguments, branches,\ncyclomatic complexity, and state mutations", 68, 70, "#F0FDF4", "#16A34A"),
        ("mcp_mutant_generator", "Generates verified AST mutants (operator swap,\nboundary condition shifts, constant offsets)", 68, 52, "#FFFBEB", "#D97706"),
        ("mcp_sandbox_runner", "Executes test suites in isolated subprocess\nwith RLIMIT resource bounds & socket block", 68, 34, "#FEF2F2", "#DC2626"),
        ("mcp_equivalence_classifier", "Applies structural AST invariant checks\nto filter semantic equivalent mutants", 68, 16, "#FAF5FF", "#9333EA")
    ]

    for name, desc, x, y, bg, border in tools:
        tbox = patches.FancyBboxPatch((x, y), 28, 13, boxstyle="round,pad=0.8", 
                                      facecolor=bg, edgecolor=border, linewidth=1.5)
        ax.add_patch(tbox)
        ax.text(x + 14, y + 9.5, name, ha="center", va="center", fontsize=8.5, fontweight="bold", color="#0F172A")
        ax.text(x + 14, y + 4.5, desc, ha="center", va="center", fontsize=6.8, color="#334155")
        # Arrow from Bus
        ax.annotate("", xy=(x, y + 6.5), xytext=(62, 50),
                    arrowprops=dict(arrowstyle="<->", color=border, lw=1.2, mutation_scale=10))

    plt.tight_layout()
    plt.savefig(f"{OUT_DIR}/fastmcp_agent_tool_diagram.png", dpi=300, bbox_inches="tight")
    plt.close()
    print("Saved fastmcp_agent_tool_diagram.png")

def create_security_diagram():
    fig, ax = plt.subplots(figsize=(11, 5.5), dpi=300)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")
    fig.patch.set_facecolor("#FFFFFF")

    ax.text(50, 94, "TestForge 3-Tier Multi-Agent Security & Sandboxing Framework", 
            ha="center", va="center", fontsize=14, fontweight="bold", color="#1E293B")
    ax.text(50, 89, "Defense-in-Depth Model Protecting Local & Cloud Environments from Untrusted Code", 
            ha="center", va="center", fontsize=9, color="#64748B")

    tiers = [
        ("Tier 1: Static AST Guardrails", 
         "Pre-Execution Inspection", 
         "• AST Node Visitor rejects dangerous imports:\n   os, sys, subprocess, socket, shutil, pty\n• Bans eval(), exec(), __import__(), open()\n• Validates syntax tree integrity before execution\n• Blocks code injection at parse time",
         6, 15, 27, 65, "#F0FDF4", "#16A34A", "#15803D"),
        ("Tier 2: Subprocess Sandboxing", 
         "OS-Level Isolation & RLIMIT", 
         "• Dedicated ephemeral subprocess execution\n• CPU Limit: RLIMIT_CPU = 3.0 seconds\n• Memory Limit: RLIMIT_AS = 256 Megabytes\n• Zero-Egress: socket.socket monkeypatched to None\n• Prevents denial-of-service and data exfiltration",
         37, 15, 27, 65, "#FEF2F2", "#DC2626", "#B91C1C"),
        ("Tier 3: Lifecycle Callbacks", 
         "Transactional State & Rollback", 
         "• Pre-step and Post-step validation hooks\n• Git checkpoint commits before each phase\n• SQLite WAL atomicity with rollback triggers\n• Immediate state restore upon test regression\n• DEF-022: 100% Pass@1 clean preflight verification",
         68, 15, 27, 65, "#EFF6FF", "#2563EB", "#1D4ED8")
    ]

    for title, subtitle, details, x, y, w, h, bg, border, title_col in tiers:
        box = patches.FancyBboxPatch((x, y), w, h, boxstyle="round,pad=1.2", 
                                     facecolor=bg, edgecolor=border, linewidth=2)
        ax.add_patch(box)
        ax.text(x + w/2, y + h - 5, title, ha="center", va="center", fontsize=10, fontweight="bold", color=title_col)
        ax.text(x + w/2, y + h - 11, subtitle, ha="center", va="center", fontsize=8, fontweight="bold", color="#475569")
        ax.text(x + 2, y + 22, details, ha="left", va="center", fontsize=7.5, color="#1E293B", linespacing=1.4)

    plt.tight_layout()
    plt.savefig(f"{OUT_DIR}/security_3tier_diagram.png", dpi=300, bbox_inches="tight")
    plt.close()
    print("Saved security_3tier_diagram.png")

if __name__ == "__main__":
    create_architecture_diagram()
    create_fastmcp_diagram()
    create_security_diagram()
