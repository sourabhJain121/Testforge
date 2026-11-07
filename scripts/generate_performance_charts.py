"""
Generate high-resolution performance evaluation charts for TestForge Criterion 10.
Produces 6 charts saved to docs/PERFORMANCE_EVALUATION/:
1. mutation_score_by_prompt_architecture.png
2. execution_time_by_prompt_architecture.png
3. persona_performance_comparison.png
4. estimated_cost_by_prompt_architecture.png
5. token_consumption_by_prompt_architecture.png
6. mutation_score_vs_runtime.png
"""

import json
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

# Set academic presentation styling
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')
plt.rcParams['font.sans-serif'] = 'Helvetica, Arial, DejaVu Sans'
plt.rcParams['font.size'] = 11
plt.rcParams['axes.titlesize'] = 13
plt.rcParams['axes.labelsize'] = 11
plt.rcParams['xtick.labelsize'] = 10
plt.rcParams['ytick.labelsize'] = 10
plt.rcParams['figure.titlesize'] = 14

DATA_PATH = Path('docs/PERFORMANCE_EVALUATION/BENCHMARK_RAW_RESULTS.json')
OUTPUT_DIR = Path('docs/PERFORMANCE_EVALUATION')
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

with open(DATA_PATH) as f:
    runs = json.load(f)

# Colors
COLOR_ZERO = '#2b5c8f'   # Slate Blue
COLOR_FEW = '#1b7837'    # Forest Green
COLOR_REACT = '#d95f02'  # Rust Orange
STRATEGY_COLORS = {
    'ZERO_SHOT': COLOR_ZERO,
    'FEW_SHOT': COLOR_FEW,
    'REACT': COLOR_REACT
}

# -------------------------------------------------------------
# Chart 1: Mutation Score by Prompt Architecture
# -------------------------------------------------------------
fig, ax = plt.subplots(figsize=(8, 5), dpi=300)
strategies = ['ZERO_SHOT', 'FEW_SHOT', 'REACT']
strat_labels = ['Zero-Shot', 'Few-Shot', 'ReAct']
x = np.arange(len(strategies))
width = 0.35

raw_scores = [np.mean([r['raw_mutation_score'] for r in runs if r['strategy'] == s]) for s in strategies]
adj_scores = [np.mean([r['adjusted_mutation_score'] for r in runs if r['strategy'] == s]) for s in strategies]

rects1 = ax.bar(x - width/2, raw_scores, width, label='Raw Mutation Score (17/19 killed)', color='#4a7bb0', edgecolor='#1e3d59', linewidth=1.2)
rects2 = ax.bar(x + width/2, adj_scores, width, label='Adjusted Mutation Score (17/18 viable)', color='#1b3a4b', edgecolor='#0d1b2a', linewidth=1.2)

ax.set_ylabel('Mutation Score (%)', fontweight='bold')
ax.set_title('Figure 1: Mutation Score by Prompt Architecture (N=60 runs)', fontweight='bold', pad=15)
ax.set_xticks(x)
ax.set_xticklabels(strat_labels, fontweight='bold')
ax.set_ylim(0, 115)
ax.axhline(100, color='gray', linestyle='--', alpha=0.5)
ax.legend(loc='upper right', framealpha=0.95)

for rect in rects1:
    h = rect.get_height()
    ax.annotate(f'{h:.2f}%', xy=(rect.get_x() + rect.get_width()/2, h),
                xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontweight='bold', fontsize=10)

for rect in rects2:
    h = rect.get_height()
    ax.annotate(f'{h:.2f}%', xy=(rect.get_x() + rect.get_width()/2, h),
                xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontweight='bold', fontsize=10)

plt.tight_layout()
plt.savefig(OUTPUT_DIR / 'mutation_score_by_prompt_architecture.png')
plt.close()

# -------------------------------------------------------------
# Chart 2: Execution Time by Prompt Architecture (Box Plot + Breakdown)
# -------------------------------------------------------------
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5), dpi=300)

dur_data = [[r['total_duration_sec'] for r in runs if r['strategy'] == s] for s in strategies]

bp = ax1.boxplot(dur_data, tick_labels=strat_labels, patch_artist=True, widths=0.45)
for patch, strat in zip(bp['boxes'], strategies):
    patch.set_facecolor(STRATEGY_COLORS[strat])
    patch.set_alpha(0.8)
    patch.set_edgecolor('black')
for median in bp['medians']:
    median.set(color='black', linewidth=1.5)

ax1.set_ylabel('Total Execution Time (Seconds)', fontweight='bold')
ax1.set_title('(A) Total Wall-Clock Time Distribution', fontweight='bold')
ax1.set_ylim(2.1, 2.7)

# Phase breakdown
phase_gen = [np.mean([r['test_gen_ms'] for r in runs if r['strategy'] == s]) for s in strategies]
phase_exec = [np.mean([r['test_exec_ms'] for r in runs if r['strategy'] == s]) for s in strategies]
phase_mut = [np.mean([r['mutation_eval_ms'] for r in runs if r['strategy'] == s]) for s in strategies]

b1 = ax2.bar(strat_labels, phase_gen, label='AST Synthesis (ms)', color='#6baed6')
b2 = ax2.bar(strat_labels, phase_exec, bottom=phase_gen, label='Sandbox Test Exec (ms)', color='#fd8d3c')
bottom_mut = [g + e for g, e in zip(phase_gen, phase_exec)]
b3 = ax2.bar(strat_labels, phase_mut, bottom=bottom_mut, label='Mutation Evaluation (ms)', color='#74c476')

ax2.set_ylabel('Time (Milliseconds)', fontweight='bold')
ax2.set_title('(B) Mean Latency by Subsystem Phase', fontweight='bold')
ax2.legend(loc='lower right', framealpha=0.95)

fig.suptitle('Figure 2: Execution Latency Analysis Across Prompt Architectures', fontweight='bold', fontsize=14)
plt.tight_layout()
plt.savefig(OUTPUT_DIR / 'execution_time_by_prompt_architecture.png')
plt.close()

# -------------------------------------------------------------
# Chart 3: Persona Performance Comparison
# -------------------------------------------------------------
fig, ax = plt.subplots(figsize=(9, 5), dpi=300)
personas = ['BEGINNER', 'EXPERIENCED', 'QA_ENGINEER', 'SECURITY_CONSCIOUS']
pers_labels = ['Beginner', 'Experienced', 'QA Engineer', 'Security-Conscious']
x_pers = np.arange(len(personas))
pers_colors = ['#4575b4', '#74add1', '#f46d43', '#d73027']

pers_dur = [np.mean([r['total_duration_sec'] for r in runs if r['persona'] == p]) for p in personas]
pers_tok = [np.mean([r['total_tokens'] for r in runs if r['persona'] == p]) for p in personas]

bars = ax.bar(x_pers, pers_dur, color=pers_colors, width=0.5, edgecolor='black', linewidth=1.1)
ax.set_ylabel('Mean Execution Time (Seconds)', fontweight='bold')
ax.set_title('Figure 3: Multi-Persona Execution Profile (N=15 runs per persona)', fontweight='bold', pad=15)
ax.set_xticks(x_pers)
ax.set_xticklabels(pers_labels, fontweight='bold')
ax.set_ylim(2.2, 2.6)

for bar, dur, tok in zip(bars, pers_dur, pers_tok):
    h = bar.get_height()
    ax.annotate(f'{dur:.2f}s\n({tok:.0f} tok)', xy=(bar.get_x() + bar.get_width()/2, h),
                xytext=(0, 4), textcoords="offset points", ha='center', va='bottom', fontweight='bold', fontsize=9.5)

plt.tight_layout()
plt.savefig(OUTPUT_DIR / 'persona_performance_comparison.png')
plt.close()

# -------------------------------------------------------------
# Chart 4: Estimated Cost by Prompt Architecture
# -------------------------------------------------------------
fig, ax = plt.subplots(figsize=(8, 5), dpi=300)
costs = [np.mean([r['estimated_cost_usd'] * 1000 for r in runs if r['strategy'] == s]) for s in strategies]  # In millicents ($/1000)
cost_std = [np.std([r['estimated_cost_usd'] * 1000 for r in runs if r['strategy'] == s]) for s in strategies]

bars_cost = ax.bar(strat_labels, costs, yerr=cost_std, capsize=6, color=['#3182bd', '#31a354', '#e6550d'], width=0.45, edgecolor='black')
ax.set_ylabel('Estimated Cost (USD per 1,000 Runs)', fontweight='bold')
ax.set_title('Figure 4: Unit Cost Estimation (Gemini 1.5 Flash Pricing Baseline)', fontweight='bold', pad=15)
ax.set_ylim(0, 0.30)

for bar, cost in zip(bars_cost, costs):
    h = bar.get_height()
    single_run_cost = cost / 1000
    ax.annotate(f'${cost:.3f} / 1k runs\n(${single_run_cost:.6f} / run)',
                xy=(bar.get_x() + bar.get_width()/2, h),
                xytext=(0, 6), textcoords="offset points", ha='center', va='bottom', fontweight='bold', fontsize=9.5)

ax.text(0.5, 0.05, 'Actual Billed Cost: $0.00 (Deterministic Offline AST Sandbox Execution)',
        transform=ax.transAxes, ha='center', va='center',
        bbox=dict(boxstyle='round,pad=0.5', facecolor='#e6f4ea', edgecolor='#137333', linewidth=1.5),
        fontweight='bold', fontsize=10, color='#137333')

plt.tight_layout()
plt.savefig(OUTPUT_DIR / 'estimated_cost_by_prompt_architecture.png')
plt.close()

# -------------------------------------------------------------
# Chart 5: Token Consumption by Prompt Architecture & Persona
# -------------------------------------------------------------
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5), dpi=300)

prompt_toks = [np.mean([r['prompt_tokens'] for r in runs if r['strategy'] == s]) for s in strategies]
comp_toks = [np.mean([r['completion_tokens'] for r in runs if r['strategy'] == s]) for s in strategies]

ax1.bar(strat_labels, prompt_toks, label='Prompt Context Tokens', color='#4393c3', width=0.45, edgecolor='black')
ax1.bar(strat_labels, comp_toks, bottom=prompt_toks, label='Completion Tokens', color='#f4a582', width=0.45, edgecolor='black')
ax1.set_ylabel('Tokens', fontweight='bold')
ax1.set_title('(A) Token Footprint by Strategy', fontweight='bold')
ax1.legend(loc='lower right', framealpha=0.95)
ax1.set_ylim(0, 1600)

for i, (p, c) in enumerate(zip(prompt_toks, comp_toks)):
    total = p + c
    ax1.annotate(f'{total:.0f} tok\n(P:{p:.0f}, C:{c:.0f})', xy=(i, total),
                 xytext=(0, 3), textcoords="offset points", ha='center', va='bottom', fontsize=9, fontweight='bold')

# By Persona
p_prompt = [np.mean([r['prompt_tokens'] for r in runs if r['persona'] == p]) for p in personas]
p_comp = [np.mean([r['completion_tokens'] for r in runs if r['persona'] == p]) for p in personas]

ax2.bar(pers_labels, p_prompt, label='Prompt Context Tokens', color='#92c5de', width=0.5, edgecolor='black')
ax2.bar(pers_labels, p_comp, bottom=p_prompt, label='Completion Tokens', color='#fddbc7', width=0.5, edgecolor='black')
ax2.set_ylabel('Tokens', fontweight='bold')
ax2.set_title('(B) Token Footprint by Persona', fontweight='bold')
ax2.set_xticks(range(len(personas)))
ax2.set_xticklabels(pers_labels, rotation=15, ha='right')
ax2.legend(loc='lower right', framealpha=0.95)
ax2.set_ylim(0, 1600)

fig.suptitle('Figure 5: Token Consumption Decomposition Across Architectures and Personas', fontweight='bold', fontsize=14)
plt.tight_layout()
plt.savefig(OUTPUT_DIR / 'token_consumption_by_prompt_architecture.png')
plt.close()

# -------------------------------------------------------------
# Chart 6: Mutation Score vs Runtime (Pareto Scatter / Stability)
# -------------------------------------------------------------
fig, ax = plt.subplots(figsize=(8.5, 5.5), dpi=300)

marker_map = {
    'BEGINNER': 'o',
    'EXPERIENCED': 's',
    'QA_ENGINEER': '^',
    'SECURITY_CONSCIOUS': 'D'
}

for strat in strategies:
    for pers in personas:
        subset = [r for r in runs if r['strategy'] == strat and r['persona'] == pers]
        durs = [r['total_duration_sec'] for r in subset]
        muts = [r['raw_mutation_score'] for r in subset]
        ax.scatter(durs, muts,
                   color=STRATEGY_COLORS[strat],
                   marker=marker_map[pers],
                   s=65, alpha=0.85,
                   edgecolor='black', linewidth=0.8)

# Custom legend for Strategy (colors) and Persona (shapes)
from matplotlib.lines import Line2D
strat_legend_elements = [Line2D([0], [0], marker='o', color='w', markerfacecolor=STRATEGY_COLORS[s], markersize=9, label=s.replace('_', ' ').title()) for s in strategies]
pers_legend_elements = [Line2D([0], [0], marker=marker_map[p], color='w', markerfacecolor='gray', markersize=9, label=p.replace('_', ' ').title()) for p in personas]

first_legend = ax.legend(handles=strat_legend_elements, title='Strategy', loc='upper left', framealpha=0.95)
ax.add_artist(first_legend)
ax.legend(handles=pers_legend_elements, title='Persona', loc='center left', framealpha=0.95)

ax.set_xlabel('End-to-End Wall-Clock Runtime (Seconds)', fontweight='bold')
ax.set_ylabel('Raw Mutation Score (%)', fontweight='bold')
ax.set_title('Figure 6: Mutation Score Stability vs Runtime Across All 60 Experimental Runs', fontweight='bold', pad=15)
ax.set_ylim(80, 100)
ax.axhline(89.47, color='red', linestyle=':', alpha=0.7, label='Deterministic Optimum (89.47%)')

plt.tight_layout()
plt.savefig(OUTPUT_DIR / 'mutation_score_vs_runtime.png')
plt.close()

print("All 6 performance charts successfully generated and saved to docs/PERFORMANCE_EVALUATION/")
