"""
app.py - TestForge Interactive Streamlit Web Interface.

Authors: Sourabh & Shreshth
Course: CSE3101 - Agentic AI
"""

import os
import sys
import json
import time
import pandas as pd
import streamlit as st
from dotenv import load_dotenv

# Load local .env file if present
load_dotenv()

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from testforge.ingestion import TargetManagerAgent
from testforge.orchestrator import TestForgeOrchestrator
from testforge.logger import TraceLogger
from testforge.accel import hw_profile
from testforge.llm_client import is_ollama_running

st.set_page_config(
    page_title="TestForge: Autonomous Test Hardening System",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("⚡ TestForge: Autonomous Agentic Test Hardening")
st.caption("CSE3101: Agentic AI — Authors: Sourabh & Shreshth | Apple Silicon Hardware Optimized")

# Sidebar Configuration
with st.sidebar:
    st.header("⚙ System Configuration")

    # Execution Mode selector radio button
    engine_choice = st.radio(
        "Execution Mode",
        [
            "Auto (Gemini -> OpenRouter -> Local Ollama Fallback)",
            "OpenRouter Cloud",
            "Force Local Engine (Ollama - Offline Mode)",
            "Force Cloud (Gemini)"
        ],
        index=0
    )
    if engine_choice == "Force Cloud (Gemini)":
        engine_mode = "cloud"
    elif engine_choice == "OpenRouter Cloud":
        engine_mode = "openrouter"
    elif engine_choice == "Force Local Engine (Ollama - Offline Mode)":
        engine_mode = "local"
    else:
        engine_mode = "auto"
    
    # User-provided API Key inputs in UI to guard against missing shell env vars
    ui_api_key = st.text_input(
        "Gemini API Key (Primary)",
        value=os.environ.get("GEMINI_API_KEY", ""),
        type="password",
        help="Paste your Gemini API key here if not exported in shell."
    )
    if ui_api_key.strip():
        os.environ["GEMINI_API_KEY"] = ui_api_key.strip()

    ui_openrouter_key = st.text_input(
        "OpenRouter API Key (Secondary)",
        value=os.environ.get("OPENROUTER_API_KEY", ""),
        type="password",
        help="Paste your OpenRouter API key here if not exported in shell."
    )
    if ui_openrouter_key.strip():
        os.environ["OPENROUTER_API_KEY"] = ui_openrouter_key.strip()

    model_name = st.selectbox(
        "Foundation Model",
        ["gemini-3.6-flash"],
        index=0
    )
    max_iterations = st.slider("Max Reflection Iterations", min_value=1, max_value=5, value=3)
    target_score = st.slider("Target Mutation Score (%)", min_value=50.0, max_value=100.0, value=85.0, step=5.0)

    st.divider()
    st.subheader("💻 Hardware & Provider Status")
    st.write(f"**Architecture:** {hw_profile.machine} ({hw_profile.os_system})")
    st.write(f"**CPU Cores:** {hw_profile.cpu_count}")
    st.write(f"**Sandbox Workers:** {hw_profile.recommended_workers}")
    st.write(f"**Unified RAM:** {hw_profile.total_memory_gb} GB")

    # Live status ping for Local Ollama
    ollama_online = is_ollama_running("http://localhost:11434/api/tags")
    if ollama_online:
        st.markdown("🟢 **Local Ollama Active (qwen2.5-coder:7b)**")
    else:
        st.markdown("⚪ **Local Ollama Offline**")

    has_gemini = bool(os.environ.get("GEMINI_API_KEY"))
    if has_gemini:
        st.success("🟢 Cloud Gemini API Key Active")
    else:
        st.warning("🟡 Cloud Gemini API Key Missing")

    has_openrouter = bool(os.environ.get("OPENROUTER_API_KEY"))
    if has_openrouter:
        st.success("🟢 OpenRouter API Key Active")
    else:
        st.warning("⚪ OpenRouter API Key Missing")

# Initialize session state for persistent source selection
if "target_file_path" not in st.session_state:
    st.session_state["target_file_path"] = None
if "target_code_to_run" not in st.session_state:
    st.session_state["target_code_to_run"] = None

# Tabs for Mode A, Mode B, Mode C, Telemetry
tab_ingest, tab_synth, tab_github, tab_telemetry = st.tabs([
    "📁 Mode A: Pick / Upload Existing File",
    "✨ Mode B: AI Module Synthesis",
    "🌐 Mode C: GitHub Direct Import",
    "📊 Observability & Telemetry Trace"
])

with tab_ingest:
    st.subheader("Ingest & Inspect Python Module")
    col1, col2 = st.columns([1, 1])

    with col1:
        ingest_mode = st.radio("Choose Source:", ["Workspace Sample", "Upload Custom .py File"])
        if ingest_mode == "Workspace Sample":
            samples_dir = "samples"
            sample_files = [f for f in os.listdir(samples_dir) if f.endswith(".py")] if os.path.exists(samples_dir) else []
            chosen_sample = st.selectbox("Select Sample:", sample_files)
            if chosen_sample:
                chosen_path = os.path.join(samples_dir, chosen_sample)
                with open(chosen_path, "r", encoding="utf-8") as f:
                    chosen_code = f.read()
                st.session_state["target_file_path"] = chosen_path
                st.session_state["target_code_to_run"] = chosen_code
        else:
            uploaded_file = st.file_uploader("Upload Python File", type=["py"])
            if uploaded_file:
                uploaded_code = uploaded_file.getvalue().decode("utf-8")
                temp_upload_path = os.path.join("samples", f"uploaded_{uploaded_file.name}")
                with open(temp_upload_path, "w", encoding="utf-8") as f:
                    f.write(uploaded_code)
                st.session_state["target_file_path"] = temp_upload_path
                st.session_state["target_code_to_run"] = uploaded_code

    with col2:
        curr_path = st.session_state.get("target_file_path")
        curr_code = st.session_state.get("target_code_to_run")
        if curr_path and curr_code and "github_" not in os.path.basename(curr_path) and "generated_" not in os.path.basename(curr_path):
            supervisor = TargetManagerAgent(model_name=model_name, api_key=os.environ.get("GEMINI_API_KEY"))
            analysis = supervisor.ingest_file(curr_path)
            st.write(f"**Module:** `{analysis.module_name}`")
            st.write(f"**Functions:** `{', '.join(analysis.functions) if analysis.functions else 'None'}`")
            st.write(f"**Classes:** `{', '.join(analysis.classes) if analysis.classes else 'None'}`")
            with st.expander("View Ingested Source Code", expanded=False):
                st.code(curr_code, language="python")

        # ⚡ Git Diff-Aware Targeted Hardening Toggle
        st.markdown("---")
        git_diff_enabled = st.toggle("⚡ Git Diff-Aware Targeted Hardening", value=False, key="git_diff_toggle")
        if git_diff_enabled:
            from testforge.git_diff import GitDiffInspector
            detected_lines = GitDiffInspector.get_modified_lines(repo_path=".", target_file=curr_path)
            if detected_lines:
                st.success(f"🎯 Target Lines from Git Diff: `{detected_lines}`")
                st.session_state["target_lines"] = detected_lines
            else:
                st.info("ℹ️ No uncommitted git changes detected for this file. Testing will cover all syntactic nodes.")
                st.session_state["target_lines"] = None
        else:
            st.session_state["target_lines"] = None

with tab_synth:
    st.subheader("Synthesize New Python Module via Gemini")
    prompt_input = st.text_area(
        "Describe the business logic or algorithm to generate:",
        placeholder="e.g. Implement a stock trading order book that matches BUY and SELL limit orders with price-time priority."
    )
    if st.button("🚀 Synthesize Module", key="synth_btn"):
        if prompt_input.strip():
            with st.spinner("TargetManagerAgent synthesizing production code with rich boundary checks..."):
                supervisor = TargetManagerAgent(model_name=model_name, api_key=os.environ.get("GEMINI_API_KEY"))
                synthed_path, synthed_code = supervisor.synthesize_module(prompt_input)
                st.session_state["target_file_path"] = synthed_path
                st.session_state["target_code_to_run"] = synthed_code
                st.success(f"Synthesized code saved to: `{synthed_path}`")
                st.code(synthed_code, language="python")

with tab_github:
    st.subheader("🌐 Mode C: Direct GitHub File Ingestion")
    st.caption("Pulls any arbitrary Python module from a public GitHub repository URL and inspects its AST structure.")
    gh_col1, gh_col2 = st.columns([1, 1])

    with gh_col1:
        github_url_input = st.text_input(
            "Enter GitHub Python File URL",
            placeholder="https://github.com/psf/requests/blob/main/src/requests/status_codes.py",
            help="Accepts GitHub blob URLs (e.g. https://github.com/owner/repo/blob/main/file.py) or raw URLs."
        )
        fetch_btn = st.button("Fetch & Ingest", key="gh_fetch_btn", type="primary")

        if fetch_btn and github_url_input.strip():
            with st.spinner("Fetching and validating Python AST from GitHub..."):
                try:
                    from testforge.ingestion import fetch_github_source
                    saved_path = fetch_github_source(github_url_input.strip())
                    with open(saved_path, "r", encoding="utf-8") as f:
                        gh_code = f.read()

                    st.session_state["target_file_path"] = str(saved_path)
                    st.session_state["target_code_to_run"] = gh_code
                    st.success(f"Successfully ingested `{saved_path.name}` from GitHub!")
                except Exception as exc:
                    st.error(f"GitHub Ingestion Error: {exc}")

    with gh_col2:
        curr_path = st.session_state.get("target_file_path")
        curr_code = st.session_state.get("target_code_to_run")
        if curr_path and curr_code and "github_" in os.path.basename(curr_path):
            supervisor = TargetManagerAgent(model_name=model_name, api_key=os.environ.get("GEMINI_API_KEY"))
            analysis = supervisor.ingest_file(curr_path)
            st.write(f"**Module:** `{analysis.module_name}`")
            st.write(f"**Functions ({len(analysis.functions)}):** `{', '.join(analysis.functions) if analysis.functions else 'None'}`")
            st.write(f"**Classes ({len(analysis.classes)}):** `{', '.join(analysis.classes) if analysis.classes else 'None'}`")
            with st.expander("View Ingested GitHub Source Code", expanded=False):
                st.code(curr_code, language="python")

# Resolve active target for execution
target_code_to_run = st.session_state.get("target_code_to_run")
target_file_path = st.session_state.get("target_file_path")

# ----------------------------------------------------------------------
# 💥 BLAST RADIUS & DEPENDENCY IMPACT ANALYSIS
# ----------------------------------------------------------------------
if target_code_to_run:
    with st.expander("💥 Blast Radius & Dependency Impact Analysis", expanded=False):
        st.caption("Static AST call-graph inspection, recursive caller propagation, downstream sub-routines, and architectural risk categorization.")
        from testforge.blast_analyzer import BlastRadiusAnalyzer
        call_graph = BlastRadiusAnalyzer.build_call_graph(target_code_to_run)
        defined_funcs = [k for k in call_graph.keys() if k != "<module>"]

        if defined_funcs:
            sel_func = st.selectbox("Select Target Function to Inspect Blast Radius:", defined_funcs, index=0)
            impact_res = BlastRadiusAnalyzer.analyze_impact(sel_func, target_code_to_run)

            risk_cat = impact_res.get("risk_category", "LOW")
            if risk_cat == "LOW":
                risk_badge = "🟢 LOW (<20%)"
            elif risk_cat == "MEDIUM":
                risk_badge = "🟡 MEDIUM (20%-50%)"
            else:
                risk_badge = "🔴 HIGH (>50%)"

            bcol1, bcol2, bcol3, bcol4 = st.columns(4)
            bcol1.metric("Risk Category", risk_badge)
            bcol2.metric("Total Affected", f"{len(impact_res.get('affected_functions', []))} / {impact_res.get('total_functions', 1)}")
            bcol3.metric("Impact Ratio", f"{impact_res.get('impacted_pct', 0.0)}%")
            bcol4.metric("Direct Callees", len(impact_res.get("direct_callees", [])))

            st.markdown("**ASCII Call Tree:**")
            st.code(impact_res.get("tree_representation", ""), language="text")

            # Visual graph of caller-callee chains using Graphviz
            cg = impact_res.get("call_graph", {})
            if cg and any(v for v in cg.values()):
                dot_lines = [
                    "digraph CallGraph {",
                    '  rankdir="LR";',
                    '  node [shape=box, style="filled,rounded", fontname="Helvetica", fillcolor="#eef2ff", color="#4f46e5"];'
                ]
                for caller, callees in cg.items():
                    if caller == "<module>":
                        continue
                    for callee in callees:
                        if callee == sel_func or caller == sel_func:
                            dot_lines.append(f'  "{caller}" -> "{callee}" [color="#ef4444", penwidth=2.5];')
                        else:
                            dot_lines.append(f'  "{caller}" -> "{callee}";')
                dot_lines.append("}")
                st.graphviz_chart("\n".join(dot_lines))
        else:
            st.info("No explicit function definitions detected in active target module.")

# Execution Area
st.divider()
st.subheader("🔥 Execution & Hardening Pipeline")

if st.button("⚡ Run TestForge Autonomous Hardening", type="primary", width="stretch"):
    if not target_code_to_run or not target_file_path:
        st.error("Please select, upload, or synthesize a target module first!")
    else:
        # Ensure API key is bound before orchestrator runs
        active_key = os.environ.get("GEMINI_API_KEY", "").strip()
        active_openrouter_key = os.environ.get("OPENROUTER_API_KEY", "").strip()

        progress_bar = st.progress(0.0)
        col_metrics1, col_metrics2, col_metrics3, col_metrics4 = st.columns(4)

        metric_cov = col_metrics1.empty()
        metric_score = col_metrics2.empty()
        metric_status = col_metrics3.empty()
        metric_provider = col_metrics4.empty()

        metric_cov.metric("Line Coverage", "Calculating...")
        metric_score.metric("Mutation Score", "0.0%")
        metric_status.metric("Pipeline Status", "Initializing...")
        metric_provider.metric("Active LLM Provider", "Detecting...")

        trace_log = "testforge_trace.jsonl"
        orchestrator = TestForgeOrchestrator(
            target_source_code=target_code_to_run,
            max_iterations=max_iterations,
            target_mutation_score=target_score,
            model_name=model_name,
            trace_log_path=trace_log,
            target_file_path=target_file_path,
            api_key=active_key,
            openrouter_api_key=active_openrouter_key,
            engine_mode=engine_mode,
            target_lines=st.session_state.get("target_lines")
        )

        with st.spinner("Multi-Agent reflection loop running across CPU cores..."):
            final_state = orchestrator.run()
            orchestrator.export_hardened_suite("test_hardened.py")

        progress_bar.progress(1.0)
        final_metric = final_state.history[-1] if final_state.history else None
        final_score = final_metric.mutation_score if final_metric else 0.0
        active_provider = getattr(final_state, "active_provider", "") or orchestrator.generator.active_provider

        # Standardized badge formatting matching user specification
        if "OpenRouter" in active_provider:
            provider_badge = f"[Provider: {active_provider}]"
        elif "Gemini" in active_provider:
            provider_badge = "[Provider: Cloud Gemini (gemini-3.6-flash)]"
        elif "Local" in active_provider or "Ollama" in active_provider:
            provider_badge = "[Provider: Local Ollama (qwen2.5-coder:7b)]"
        else:
            provider_badge = f"[Provider: {active_provider}]"

        metric_cov.metric("Line Coverage", f"{final_state.baseline_line_coverage:.1f}%")
        metric_score.metric("Mutation Score", f"{final_score:.1f}%", delta=f"{final_score - 50.0:.1f}%")
        metric_status.metric("Status", "SUCCESS" if final_score >= target_score else "TERMINATED")
        metric_provider.metric("Active LLM Provider", provider_badge)

        # Prominent provider badge display
        st.markdown(f"### 🏷️ `{provider_badge}`")
        if "OpenRouter" in provider_badge:
            st.success(f"**`{provider_badge}`** — Assertions synthesized and hardened via OpenRouter Cloud API.")
        elif "Cloud Gemini" in provider_badge:
            st.success(f"**`{provider_badge}`** — Assertions synthesized and hardened via Google AI Studio (`gemini-3.6-flash`).")
        elif "Local Ollama" in provider_badge:
            st.info(f"**`{provider_badge}`** — Assertions synthesized offline via Local Ollama (`qwen2.5-coder:7b`).")
        else:
            st.warning(f"**`{provider_badge}`** — Assertions generated via AST-guided deterministic synthesizer.")

        # ----------------------------------------------------------------------
        # ENHANCEMENT 1: SOURCE CODE INSPECTION DRAWER
        # ----------------------------------------------------------------------
        with st.expander("📄 View Generated Source Code Under Test", expanded=False):
            st.caption(f"Inspecting file: `{target_file_path}`")
            st.code(target_code_to_run, language="python")

        # Iteration History Table
        st.subheader("📈 Iteration Breakdown")
        history_rows = []
        for h in final_state.history:
            history_rows.append({
                "Iteration": h.iteration,
                "Total Mutants": h.total_mutants,
                "Killed": h.killed_mutants,
                "Survived": h.survived_mutants,
                "Mutation Score (%)": f"{h.mutation_score}%",
                "Duration (s)": f"{h.duration_seconds}s"
            })
        st.table(history_rows)

        # ----------------------------------------------------------------------
        # ENHANCEMENT 2: AST MUTANT AUDIT INSPECTOR & DIFF VIEWER
        # ----------------------------------------------------------------------
        with st.expander("🔍 AST Mutation Audit & Diff Viewer", expanded=True):
            st.caption("Detailed report of all injected deterministic AST faults, execution outcomes, and unified diffs.")
            
            if final_state.mutants:
                audit_records = []
                for m in final_state.mutants:
                    orig_snippet = ""
                    mut_snippet = ""
                    for line in m.unified_diff.splitlines():
                        if line.startswith("-") and not line.startswith("---"):
                            orig_snippet = line[1:].strip()
                        elif line.startswith("+") and not line.startswith("+++"):
                            mut_snippet = line[1:].strip()

                    status_badge = "🟢 KILLED" if m.status in ("KILLED", "TIMEOUT") else "🔴 SURVIVED"
                    audit_records.append({
                        "Mutant ID": m.mutant_id,
                        "Type": m.mutation_type,
                        "Line": m.line_number,
                        "Original Statement": orig_snippet or "(AST Node)",
                        "Mutated Statement": mut_snippet or "(AST Node)",
                        "Outcome": status_badge,
                        "Exec Time": f"{m.execution_time_ms:.1f} ms"
                    })

                audit_df = pd.DataFrame(audit_records)
                st.dataframe(audit_df, width="stretch")

                # Individual Unified Diff Viewer
                st.markdown("**Inspect Unified AST Diffs:**")
                selected_mutant_id = st.selectbox(
                    "Choose Mutant to view unified diff:",
                    [m.mutant_id for m in final_state.mutants]
                )
                selected_mutant = next((m for m in final_state.mutants if m.mutant_id == selected_mutant_id), None)
                if selected_mutant:
                    status_str = "🟢 KILLED (Caught by assertions)" if selected_mutant.status in ("KILLED", "TIMEOUT") else "🔴 SURVIVED (Test bypassed)"
                    st.write(f"**Status:** {status_str} | **Type:** `{selected_mutant.mutation_type}` | **Line:** `{selected_mutant.line_number}`")
                    st.code(selected_mutant.unified_diff, language="diff")
            else:
                st.info("No mutants generated for this module.")

        # Standalone Test Suite Export Viewer
        st.subheader("📦 Final Hardened Test Suite (`test_hardened.py`)")
        st.caption(f"Generated via **`{provider_badge}`** | Standalone Pytest executable")
        with open("test_hardened.py", "r", encoding="utf-8") as tf:
            hardened_content = tf.read()
        st.code(hardened_content, language="python")
        st.info("Verified standalone: You can run `pytest test_hardened.py -v` in any terminal.")

        # ----------------------------------------------------------------------
        # ENHANCEMENT 3: LIVE TELEMETRY & TOKEN AUDIT (AFTER RUN)
        # ----------------------------------------------------------------------
        with st.expander("📊 Live Telemetry & Token Trace Log (testforge_trace.jsonl)", expanded=False):
            st.caption("Telemetry captured on every foundation model and evaluation step.")
            logger = TraceLogger()
            traces = logger.read_traces()
            recent_llm_calls = [t for t in traces if t.get("event_type") == "LLM_INFERENCE_TELEMETRY"][-8:]

            if recent_llm_calls:
                telemetry_rows = []
                for entry in reversed(recent_llm_calls):
                    data = entry.get("data", {})
                    tokens = data.get("tokens", {})
                    telemetry_rows.append({
                        "Agent Name": data.get("agent", "Unknown"),
                        "Model": data.get("model", "Unknown"),
                        "Iteration": data.get("iteration", 0),
                        "Latency (s)": f"{data.get('latency_seconds', 0.0):.2f}s",
                        "Prompt Tokens": tokens.get("prompt_tokens", 0),
                        "Completion Tokens": tokens.get("completion_tokens", 0),
                        "Total Tokens": tokens.get("total_tokens", 0),
                        "AST Valid": "Yes" if data.get("is_valid_ast", True) else "No"
                    })
                st.table(telemetry_rows)
            else:
                st.info("No LLM inference calls recorded in this trace yet.")

with tab_telemetry:
    st.subheader("🔍 Complete Telemetry Trace Log (`testforge_trace.jsonl`)")
    logger = TraceLogger()
    traces = logger.read_traces()
    st.write(f"Total Logged Events: **{len(traces)}** | Total LLM Tokens Used: **{logger.get_total_tokens():,}**")

    if traces:
        recent_traces = traces[-15:]
        for entry in reversed(recent_traces):
            event_type = entry.get("event_type", "UNKNOWN")
            timestamp = entry.get("iso_time", "")
            with st.expander(f"[{timestamp}] {event_type}"):
                st.json(entry.get("data", {}))
    else:
        st.info("No traces recorded yet in this session.")

    # ----------------------------------------------------------------------
    # 🤖 ADK AGENT TOOL TRAJECTORY VIEW
    # ----------------------------------------------------------------------
    st.divider()
    st.subheader("🤖 ADK Agent Tool Deliberation Trajectory")
    st.caption("Sequence of autonomous ADK tools invoked by TestGeneratorAgent and AdversarialCriticAgent during reflection.")
    adk_calls = [t for t in traces if t.get("event_type") == "ADK_TOOL_CALL"]
    if adk_calls:
        adk_rows = []
        for call in adk_calls[-20:]:
            cdata = call.get("data", {})
            iso_t = call.get("iso_time", "")
            adk_rows.append({
                "Timestamp": iso_t,
                "Iteration": cdata.get("iteration", 1),
                "Tool Invoked": cdata.get("tool_name", "unknown"),
                "Success": "✅ Yes" if cdata.get("success") else "❌ No",
                "Latency (s)": f"{cdata.get('latency_seconds', 0.0):.3f}s",
                "Output Summary": str(cdata.get("output_preview", ""))[:80]
            })
        st.dataframe(pd.DataFrame(adk_rows), width="stretch")
        with st.expander("🔍 View Raw ADK Tool Invocations"):
            for call in reversed(adk_calls[-10:]):
                st.json(call)
    else:
        st.info("No ADK tool deliberations logged yet in this session. Run a hardening pipeline to see live ADK agent tool calls.")
