"""
app.py - TestForge Legacy Streamlit Interface (ARCHIVED / HISTORICAL REFERENCE).

NOTE: Streamlit has been permanently disabled from normal project execution.
The official, production-ready, supported interface for TestForge is the
FastAPI HTML/CSS/JavaScript Dashboard served from `server.py` at:
    http://127.0.0.1:8000/

This file is preserved strictly for historical audit compliance, evaluation
verification, and legacy prototype reference. Do not launch this file during
normal production operation.

Authors: Sourabh & Shreshth
Course: CSE3101 - Agentic AI
"""

import os
import sys
import json
import time
import re
import hashlib
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
st.info("🌟 **Primary Evaluation Interface:** TestForge's modern enterprise dashboard is running on port 8000: [http://127.0.0.1:8000](http://127.0.0.1:8000) (includes FastMCP tools, A2A discovery card, and SQLite checkpoint diffing).")

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

# Initialize session state for isolated source modes
if "active_mode" not in st.session_state:
    st.session_state["active_mode"] = "Mode A"
if "target_file_path" not in st.session_state:
    st.session_state["target_file_path"] = "samples/discount.py"
if "target_code_to_run" not in st.session_state:
    if os.path.exists("samples/discount.py"):
        with open("samples/discount.py", "r", encoding="utf-8") as f:
            st.session_state["target_code_to_run"] = f.read()
    else:
        st.session_state["target_code_to_run"] = ""
if "target_source_sha" not in st.session_state:
    st.session_state["target_source_sha"] = hashlib.sha256(
        st.session_state.get("target_code_to_run", "").encode("utf-8")
    ).hexdigest()
if "mode_c_metadata" not in st.session_state:
    st.session_state["mode_c_metadata"] = None
if "mode_c_analysis" not in st.session_state:
    st.session_state["mode_c_analysis"] = None
if "last_ingested_github_url" not in st.session_state:
    st.session_state["last_ingested_github_url"] = None

# Tabs for Mode A, Mode B, Mode C, Wiretap, Telemetry
tab_ingest, tab_synth, tab_github, tab_wiretap, tab_telemetry = st.tabs([
    "📁 Mode A: Pick / Upload Existing File",
    "✨ Mode B: AI Module Synthesis",
    "🌐 Mode C: GitHub Direct Import",
    "🤖 Multi-Agent Inter-Communication & Wiretap",
    "📊 Observability & Telemetry Trace"
])

with tab_ingest:
    st.subheader("📁 Ingest & Inspect Workspace Module")
    col1, col2 = st.columns([1, 1])

    with col1:
        ingest_mode = st.radio("Choose Source:", ["Workspace Sample", "Upload Custom .py File"], key="mode_a_source_radio")
        if ingest_mode == "Workspace Sample":
            samples_dir = "samples"
            # Filter out github_* and uploaded_* so only pure workspace samples appear in Mode A
            sample_files = [
                f for f in sorted(os.listdir(samples_dir))
                if f.endswith(".py") and not f.startswith("github_") and not f.startswith("uploaded_") and not f.startswith("generated_")
            ] if os.path.exists(samples_dir) else []

            chosen_sample = st.selectbox("Select Sample:", sample_files, key="mode_a_sample_select")
            if st.button("📂 Load Workspace Sample", key="mode_a_load_btn", type="secondary"):
                if chosen_sample:
                    chosen_path = os.path.join(samples_dir, chosen_sample)
                    with open(chosen_path, "r", encoding="utf-8") as f:
                        chosen_code = f.read()
                    st.session_state["active_mode"] = "Mode A"
                    st.session_state["target_file_path"] = chosen_path
                    st.session_state["target_code_to_run"] = chosen_code
                    st.session_state["target_source_sha"] = hashlib.sha256(chosen_code.encode("utf-8")).hexdigest()
                    st.session_state["mode_c_metadata"] = None
                    st.session_state["mode_c_analysis"] = None
                    st.rerun()
        else:
            uploaded_file = st.file_uploader("Upload Python File", type=["py"], key="mode_a_file_uploader")
            if uploaded_file:
                uploaded_code = uploaded_file.getvalue().decode("utf-8")
                temp_upload_path = os.path.join("samples", f"uploaded_{uploaded_file.name}")
                with open(temp_upload_path, "w", encoding="utf-8") as f:
                    f.write(uploaded_code)
                st.session_state["active_mode"] = "Mode A"
                st.session_state["target_file_path"] = temp_upload_path
                st.session_state["target_code_to_run"] = uploaded_code
                st.session_state["target_source_sha"] = hashlib.sha256(uploaded_code.encode("utf-8")).hexdigest()
                st.session_state["mode_c_metadata"] = None
                st.session_state["mode_c_analysis"] = None

    with col2:
        curr_path = st.session_state.get("target_file_path")
        curr_code = st.session_state.get("target_code_to_run")
        active_m = st.session_state.get("active_mode")
        if curr_path and curr_code and active_m == "Mode A":
            supervisor = TargetManagerAgent(model_name=model_name, api_key=os.environ.get("GEMINI_API_KEY"))
            analysis = supervisor.ingest_file(curr_path)
            mod_name = getattr(analysis, "module_name", "")
            funcs = getattr(analysis, "functions", [])
            cls_list = getattr(analysis, "classes", [])
            sha_val = getattr(analysis, "source_sha", "")
            st.write(f"**Active Module:** `{mod_name}`")
            st.write(f"**Functions ({len(funcs)}):** `{', '.join(funcs) if funcs else 'None'}`")
            st.write(f"**Classes ({len(cls_list)}):** `{', '.join(cls_list) if cls_list else 'None'}`")
            st.caption(f"SHA-256 Fingerprint: `{sha_val}`")
            with st.expander("View Ingested Source Code", expanded=False):
                st.code(curr_code, language="python")

        # ⚡ Git Diff-Aware Targeted Hardening Toggle
        st.markdown("---")
        git_diff_enabled = st.toggle("⚡ Git Diff-Aware Targeted Hardening", value=False, key="git_diff_toggle")
        if git_diff_enabled and curr_path:
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
    st.subheader("✨ Synthesize New Python Module via Gemini")
    prompt_input = st.text_area(
        "Describe the business logic or algorithm to generate:",
        placeholder="e.g. Implement a stock trading order book that matches BUY and SELL limit orders with price-time priority."
    )
    if st.button("🚀 Synthesize Module", key="synth_btn"):
        if prompt_input.strip():
            with st.spinner("TargetManagerAgent synthesizing production code with rich boundary checks..."):
                supervisor = TargetManagerAgent(model_name=model_name, api_key=os.environ.get("GEMINI_API_KEY"))
                synthed_path, synthed_code = supervisor.synthesize_module(prompt_input)
                st.session_state["active_mode"] = "Mode B"
                st.session_state["target_file_path"] = synthed_path
                st.session_state["target_code_to_run"] = synthed_code
                st.session_state["target_source_sha"] = hashlib.sha256(synthed_code.encode("utf-8")).hexdigest()
                st.session_state["mode_c_metadata"] = None
                st.session_state["mode_c_analysis"] = None
                st.success(f"Synthesized code saved to: `{synthed_path}`")
                st.code(synthed_code, language="python")

with tab_github:
    st.subheader("🌐 Mode C: Direct GitHub File Ingestion")
    st.caption("Pulls any arbitrary Python module from a public GitHub repository URL, resolves dependencies, and inspects its AST structure.")
    gh_col1, gh_col2 = st.columns([1, 1])

    with gh_col1:
        github_url_input = st.text_input(
            "Enter GitHub Python File URL",
            placeholder="https://github.com/psf/requests/blob/main/src/requests/models.py",
            help="Accepts GitHub blob URLs or raw URLs.",
            key="github_file_url"
        )
        fetch_btn = st.button("Fetch & Ingest", key="github_fetch_button", type="primary")

        if fetch_btn:
            raw_user_input = github_url_input.strip() if github_url_input else ""
            if not raw_user_input:
                st.warning("Please enter a valid GitHub Python file URL.")
            else:
                # Clear previous state so failed fetch leaves NO stale source or old state active
                st.session_state["target_file_path"] = None
                st.session_state["target_code_to_run"] = None
                st.session_state["target_source_sha"] = None
                st.session_state["source_hash"] = None
                st.session_state["module_name"] = None
                st.session_state["ast_tree"] = None
                st.session_state["functions"] = []
                st.session_state["classes"] = []
                st.session_state["dependencies"] = []
                st.session_state["ingestion_metadata"] = None
                st.session_state["mode_c_metadata"] = None
                st.session_state["mode_c_analysis"] = None
                st.session_state.pop("final_state", None)
                st.session_state.pop("current_test_code", None)
                st.session_state.pop("hardened_test_suite", None)

                with st.spinner("Validating URL and fetching module from GitHub..."):
                    try:
                        supervisor = TargetManagerAgent(model_name=model_name, api_key=os.environ.get("GEMINI_API_KEY"))
                        saved_path, analysis = supervisor.ingest_github(raw_user_input)
                        gh_meta = getattr(analysis, "github_metadata", {})

                        # Atomically commit fresh ingestion state
                        st.session_state["active_mode"] = "Mode C"
                        st.session_state["github_url"] = gh_meta.get("source_github_url", raw_user_input)
                        st.session_state["raw_url"] = gh_meta.get("raw_github_url", "")
                        st.session_state["last_ingested_github_url"] = gh_meta.get("source_github_url", raw_user_input)
                        st.session_state["target_file_path"] = str(saved_path)
                        st.session_state["target_code_to_run"] = getattr(analysis, "source_code", "")
                        st.session_state["target_source_sha"] = getattr(analysis, "source_sha", "")
                        st.session_state["source_hash"] = getattr(analysis, "source_sha", "")
                        st.session_state["module_name"] = getattr(analysis, "module_name", "")
                        st.session_state["ast_tree"] = getattr(analysis, "tree", None)
                        st.session_state["functions"] = getattr(analysis, "functions", [])
                        st.session_state["classes"] = getattr(analysis, "classes", [])
                        st.session_state["dependencies"] = getattr(analysis, "dependencies", [])
                        st.session_state["ingestion_metadata"] = gh_meta
                        st.session_state["mode_c_metadata"] = gh_meta
                        st.session_state["mode_c_analysis"] = analysis

                        file_name = getattr(saved_path, "name", os.path.basename(str(saved_path)))
                        st.success(f"Successfully ingested `{file_name}` from GitHub!")
                    except Exception as exc:
                        # State is already cleared; display clean error
                        st.error(f"GitHub Ingestion Error:\n{exc}")

    with gh_col2:
        meta = st.session_state.get("mode_c_metadata")
        analysis = st.session_state.get("mode_c_analysis")
        active_m = st.session_state.get("active_mode")

        if meta and analysis:
            st.markdown("#### 📋 Ingestion Metadata & AST Audit")
            repo_name = meta.get("repository", "Unknown") if isinstance(meta, dict) else getattr(meta, "repository", "Unknown")
            branch_name = meta.get("branch", "main") if isinstance(meta, dict) else getattr(meta, "branch", "main")
            file_path_val = meta.get("file_path", "") if isinstance(meta, dict) else getattr(meta, "file_path", "")
            gen_mod_name = (
                meta.get("generated_module_name") or meta.get("module_name") or getattr(analysis, "module_name", "")
                if isinstance(meta, dict) else getattr(analysis, "module_name", "")
            )
            src_sha = (
                meta.get("source_sha", "")
                if isinstance(meta, dict) else getattr(analysis, "source_sha", "")
            )
            raw_gh_url = meta.get("raw_github_url", "") if isinstance(meta, dict) else getattr(meta, "raw_github_url", "")

            st.markdown(f"**Repository:** `{repo_name}` | **Branch:** `{branch_name}`")
            st.markdown(f"**File Path:** `{file_path_val}`")
            st.markdown(f"**Generated Module:** `{gen_mod_name}`")
            st.markdown(f"**Source SHA-256:** `{src_sha}`")
            if raw_gh_url:
                st.markdown(f"**Raw GitHub URL:** [{raw_gh_url}]({raw_gh_url})")

            line_cnt = meta.get("line_count", 0) if isinstance(meta, dict) else getattr(analysis, "line_count", 0)
            ast_cls_cnt = meta.get("ast_class_count", 0) if isinstance(meta, dict) else getattr(analysis, "ast_class_count", 0)
            ast_fn_cnt = meta.get("ast_function_count", 0) if isinstance(meta, dict) else getattr(analysis, "ast_function_count", 0)

            mcol1, mcol2, mcol3 = st.columns(3)
            mcol1.metric("Lines of Code", line_cnt)
            mcol2.metric("AST Classes", ast_cls_cnt)
            mcol3.metric("AST Callables", ast_fn_cnt)

            cls_list = getattr(analysis, "classes", []) if not isinstance(analysis, dict) else analysis.get("classes", [])
            fn_list = getattr(analysis, "functions", []) if not isinstance(analysis, dict) else analysis.get("functions", [])
            methods_map = getattr(analysis, "methods", {}) if not isinstance(analysis, dict) else analysis.get("methods", {})
            src_content = getattr(analysis, "source_code", "") if not isinstance(analysis, dict) else analysis.get("source_code", "")

            if cls_list:
                st.markdown(f"**Classes ({len(cls_list)}):** `{', '.join(cls_list)}`")
            if fn_list:
                st.markdown(f"**Top-Level Functions ({len(fn_list)}):** `{', '.join(fn_list)}`")
            if methods_map:
                tot_methods = sum(len(m) for m in methods_map.values())
                with st.expander(f"Inspect Class Methods ({tot_methods})", expanded=False):
                    for cls_name, meth_list in methods_map.items():
                        st.markdown(f"- **`{cls_name}`**: {', '.join(meth_list) if meth_list else '(no methods)'}")

            with st.expander("📄 View Downloaded GitHub Source Code", expanded=False):
                st.caption(f"SHA-256 Fingerprint: {src_sha}")
                st.code(src_content, language="python")

            if active_m != "Mode C":
                if st.button("🎯 Set Mode C File as Active Hardening Target", key="mode_c_activate_target_btn", type="secondary"):
                    st.session_state["active_mode"] = "Mode C"
                    st.session_state["target_file_path"] = str(getattr(analysis, "file_path", ""))
                    st.session_state["target_code_to_run"] = src_content
                    st.session_state["target_source_sha"] = src_sha
                    st.rerun()
        else:
            st.info("Enter a GitHub URL and click 'Fetch & Ingest' to load a public Python module.")

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
        metric_status.metric("Status", getattr(final_state, "final_hardening_status", "TERMINATED"))
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

        # Explicit Operational Execution & Mutation Testing Telemetry
        st.markdown("### 📊 Verified Execution & Hardening Telemetry")

        # Row 1: Baseline Test Validation
        st.markdown("##### 🧪 Baseline Test Suite Execution")
        b_col1, b_col2, b_col3, b_col4, b_col5 = st.columns(5)
        b_col1.metric("Baseline Generated", getattr(final_state, "baseline_tests_generated", 0))
        b_col2.metric("Baseline Executed", getattr(final_state, "baseline_tests_executed", 0))
        b_col3.metric("Baseline Passed", getattr(final_state, "baseline_tests_passed", 0))
        b_col4.metric("Baseline Failed", getattr(final_state, "baseline_tests_failed", 0))
        baseline_badge = "🟢 PASSED" if getattr(final_state, "baseline_passed", False) else "🔴 FAILED"
        b_col5.metric("Baseline Verdict", baseline_badge)

        # Row 2: Code Coverage & Mutation Analysis
        st.markdown("##### 🧬 Mutation Testing & Line Coverage")
        m_col1, m_col2, m_col3, m_col4, m_col5, m_col6, m_col7 = st.columns(7)
        lines_cov_str = f"{getattr(final_state, 'lines_covered', 0)} / {getattr(final_state, 'num_statements', 0)}"
        m_col1.metric("Lines Covered", lines_cov_str)
        m_col2.metric("Coverage %", f"{final_state.baseline_line_coverage:.1f}%")
        m_col3.metric("Mutants Generated", getattr(final_state, "mutants_generated", len(final_state.mutants)))
        m_col4.metric("Mutants Executed", getattr(final_state, "mutants_executed", 0))
        m_col5.metric("Mutants Killed", getattr(final_state, "mutants_killed", 0))
        m_col6.metric("Mutants Survived", getattr(final_state, "mutants_survived", 0))
        m_col7.metric("Exec Errors", getattr(final_state, "mutation_execution_errors", 0))

        # Row 3: Final Hardening Status
        st.markdown("##### 🏁 Hardening Status & Reflection Cycles")
        s_col1, s_col2, s_col3 = st.columns(3)
        s_col1.metric("Mutation Score", f"{final_score:.1f}%")
        s_col2.metric("Iterations Performed", getattr(final_state, "reflection_iterations_performed", len(final_state.history)))
        status_val = getattr(final_state, "final_hardening_status", "UNKNOWN")
        s_col3.metric("Hardening Status", status_val)

        # Banner alerts based on strict validation
        if status_val == "FAILED_BASELINE":
            st.error(f"❌ **HARDENING FAILED:** Baseline tests failed against clean target code ({final_state.termination_reason}). Mutants cannot be evaluated because the target is broken or imports failed.")
        elif final_state.baseline_line_coverage == 0.0:
            st.warning(f"⚠️ **ZERO COVERAGE WARNING:** Line coverage is 0.0%. Test suite did not execute any statements in `{os.path.basename(target_file_path)}`.")
        elif status_val == "SUCCESS":
            st.success(f"✅ **HARDENING SUCCESS:** {final_state.termination_reason}")
        else:
            st.info(f"ℹ️ **HARDENING COMPLETED ({status_val}):** {final_state.termination_reason}")

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

        # ----------------------------------------------------------------------
        # ENHANCEMENT 4: LIVE MULTI-AGENT WIRETAP & HANDOFF INSPECTOR (AFTER RUN)
        # ----------------------------------------------------------------------
        with st.expander("🤖 Live Multi-Agent Wiretap & Inter-Agent Handoff Trajectory", expanded=True):
            render_agent_wiretap(key_prefix="post_run_wiretap")


def render_agent_wiretap(traces=None, key_prefix="wiretap"):
    """
    Renders the Live Agent Wiretap & Inter-Agent Handoff Inspector.
    Visualizes sequential state transitions, contract input/output payloads,
    and ADK tool deliberation telemetries across reflection loops.
    """
    if traces is None:
        wiretap_logger = TraceLogger()
        traces = wiretap_logger.read_traces()

    handoff_events = [t for t in traces if t.get("event_type") == "AGENT_HANDOFF"]
    adk_events = [t for t in traces if t.get("event_type") == "ADK_TOOL_CALL"]

    st.markdown("### 🤖 Live Agent Wiretap & Inter-Agent Handoff Inspector")
    st.caption("Inspect live sequential state transitions, inter-agent payloads, and ADK tool deliberation telemetries across reflection iterations.")

    # High-level summary metrics
    kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
    total_handoffs = len(handoff_events)
    participating_agents = set()
    for h in handoff_events:
        d = h.get("data", {})
        if d.get("from_agent"):
            participating_agents.add(d["from_agent"])
        if d.get("to_agent"):
            participating_agents.add(d["to_agent"])

    max_iter = max([h.get("data", {}).get("iteration", 0) for h in handoff_events], default=0)

    kpi_col1.metric("Captured Handoffs", total_handoffs)
    kpi_col2.metric("Active Agents", len(participating_agents))
    kpi_col3.metric("ADK Tool Calls", len(adk_events))
    kpi_col4.metric("Reflection Loops", f"{max_iter}")

    if not handoff_events:
        st.info("ℹ️ No agent handoffs recorded in this session yet. Run the TestForge hardening pipeline to stream live multi-agent communication!")
        return

    AGENT_BADGES = {
        "TargetManagerAgent": "🔵 TargetManagerAgent",
        "TestGeneratorAgent": "🟢 TestGeneratorAgent",
        "SubprocessSandbox": "🟡 SubprocessSandbox",
        "ParallelSandboxRunner": "🟡 SubprocessSandbox",
        "AdversarialCriticAgent": "🔴 AdversarialCriticAgent"
    }

    # Filtering toolbar
    f_col1, f_col2, f_col3 = st.columns([1, 1, 1])
    with f_col1:
        all_iters = sorted(list({h.get("data", {}).get("iteration", 0) for h in handoff_events}))
        iter_filter = st.selectbox(
            "Filter by Iteration:",
            ["All Iterations"] + [f"Iteration {it}" for it in all_iters],
            key=f"{key_prefix}_iter_filter"
        )
    with f_col2:
        agent_filter = st.selectbox(
            "Filter by Agent:",
            ["All Agents"] + sorted(list(participating_agents)),
            key=f"{key_prefix}_agent_filter"
        )
    with f_col3:
        search_query = st.text_input(
            "Search Wiretap Payloads:",
            placeholder="e.g. blast radius, test suite, critique",
            key=f"{key_prefix}_search_query"
        )

    # Filter events
    displayed = []
    for h in handoff_events:
        d = h.get("data", {})
        it = d.get("iteration", 0)
        fa = d.get("from_agent", "")
        ta = d.get("to_agent", "")
        summary = d.get("summary", "")
        payload_str = json.dumps(d.get("payload", {}))

        if iter_filter != "All Iterations" and f"Iteration {it}" != iter_filter:
            continue
        if agent_filter != "All Agents" and agent_filter not in (fa, ta):
            continue
        if search_query.strip():
            q = search_query.strip().lower()
            if q not in summary.lower() and q not in payload_str.lower() and q not in fa.lower() and q not in ta.lower():
                continue
        displayed.append(h)

    st.caption(f"Displaying **{len(displayed)}** of **{total_handoffs}** sequential inter-agent state transitions")

    # 1. Visual State-Flow Stepper
    for idx, event in enumerate(displayed, start=1):
        d = event.get("data", {})
        iso_time = event.get("iso_time", "")
        from_agent = d.get("from_agent", "Agent")
        to_agent = d.get("to_agent", "Agent")
        iteration = d.get("iteration", 0)
        summary = d.get("summary", "Inter-agent handoff")
        payload = d.get("payload", {})

        from_badge = AGENT_BADGES.get(from_agent, f"⚪ {from_agent}")
        to_badge = AGENT_BADGES.get(to_agent, f"⚪ {to_agent}")

        expander_title = f"Step {idx}: {from_badge}  ➔  {to_badge}  |  Iter {iteration}  [{iso_time}]"

        with st.expander(expander_title, expanded=(idx == len(displayed) or idx == 1)):
            st.markdown(f"**⚡ Action Summary:** {summary}")
            st.caption(f"Phase: Iteration `{iteration}` | Source: `{from_agent}` ➔ Recipient: `{to_agent}`")

            # 2. Input / Output Inspection Drawers
            tab_in, tab_out = st.tabs(["📥 What Agent Received", "📤 What Agent Produced / Passed"])

            with tab_in:
                if from_agent == "TargetManagerAgent":
                    st.markdown("**Target Intake & Pre-conditions:**")
                    st.write("• **Target Module / File:**", payload.get("target_file", st.session_state.get("target_file_path", "Clean Python Source")))
                    st.write("• **AST Scope:** Parse function definitions, AST call graph, and determine boundary conditions.")
                    st.write("• **Target Line Filters:**", f"`{payload.get('target_lines')}`" if payload.get("target_lines") else "Full module (unrestricted AST)")
                    if "received_input" in payload:
                        st.caption(payload["received_input"])
                elif from_agent == "TestGeneratorAgent":
                    st.markdown("**Context Received for Test Synthesis:**")
                    if iteration == 0:
                        st.write("• **Ingested Symbols:** Function signatures & call graphs received from `TargetManagerAgent`.")
                        st.write("• **Blast Risk Rating:**", f"`{payload.get('blast_risk', 'LOW')}`")
                        st.write("• **Directive:** Synthesize initial candidate pytest suite targeting pass@1 zero-shot cleanliness.")
                    else:
                        st.write(f"• **Adversarial Feedback (Iteration {iteration}):**")
                        critique_prev = payload.get("critique_directives") or payload.get("received_input")
                        if critique_prev:
                            st.info(critique_prev)
                        else:
                            st.info("Diagnosed surviving mutants from previous iteration; prompt engaged with mutant AST diffs.")
                elif from_agent == "SubprocessSandbox":
                    st.markdown("**Test Suite & Mutants Dispatched for Sandbox Execution:**")
                    st.write("• **Source Code Under Test:** Clean module source code.")
                    st.write("• **Candidate Suite:** Test suite generated by `TestGeneratorAgent`.")
                    st.write("• **Evaluation Target:** Multi-worker isolated sub-process execution.")
                elif from_agent == "AdversarialCriticAgent":
                    st.markdown("**Execution Diagnostics Received from Sandbox:**")
                    surv_ids = payload.get("surviving_mutants", [])
                    st.write(f"• **Total Surviving Mutants Diagnosed:** `{len(surv_ids)}`")
                    if surv_ids:
                        st.write("• **Surviving Mutant IDs:**", surv_ids)
                else:
                    st.json(payload)

            with tab_out:
                if from_agent == "TargetManagerAgent":
                    st.markdown("**Extracted AST Symbols & Blast Radius Metadata:**")
                    p_col1, p_col2 = st.columns(2)
                    with p_col1:
                        st.write("• **Functions Extracted:**", payload.get("functions", []))
                        st.write("• **Target Lines:**", payload.get("target_lines", []))
                    with p_col2:
                        st.write("• **Blast Risk Assessment:**", f"`{payload.get('blast_risk', 'LOW')}`")
                    with st.expander("Raw Payload JSON", expanded=False):
                        st.json(payload)
                elif from_agent == "TestGeneratorAgent":
                    st.markdown("**Synthesized Candidate Test Suite:**")
                    st.caption(f"Provider Active: `{payload.get('provider_used', 'Cloud / Local Model')}`")
                    test_prev = payload.get("test_code_preview", "")
                    if test_prev:
                        st.code(test_prev, language="python")
                    else:
                        st.json(payload)
                elif from_agent == "AdversarialCriticAgent":
                    st.markdown("**Adversarial Directives & Mutant Diagnosis:**")
                    st.write("• **Diagnosed Mutants:**", payload.get("surviving_mutants", []))
                    directives = payload.get("critique_directives", "")
                    if directives:
                        st.markdown(f"```text\n{directives}\n```")
                    else:
                        st.json(payload)
                elif from_agent == "SubprocessSandbox":
                    st.markdown("**Parallel Sandbox Verdicts:**")
                    st.json(payload)
                else:
                    st.json(payload)

            # 3. ADK Tool Execution Telemetry
            st.markdown("---")
            st.markdown("#### 🛠️ ADK Tool Execution Telemetry")
            matching_adk = [
                t for t in adk_events
                if t.get("data", {}).get("iteration") == iteration
            ]
            if matching_adk:
                for adk_call in matching_adk:
                    cdata = adk_call.get("data", {})
                    tname = cdata.get("tool_name", "adk_tool")
                    lat_sec = cdata.get("latency_seconds", 0.0)
                    lat_ms = lat_sec * 1000.0
                    lat_str = f"{int(round(lat_ms))}ms" if lat_ms >= 1.0 else f"{lat_ms:.2f}ms"
                    is_ok = cdata.get("success", True)
                    status_sym = "✅" if is_ok else "❌"

                    t_c1, t_c2 = st.columns([3, 1])
                    with t_c1:
                        st.markdown(f"{status_sym} **Tool:** `{tname}`")
                    with t_c2:
                        st.markdown(f"⏱️ **Latency:** `{lat_str}`")

                    with st.expander(f"Telemetry Details for `{tname}`", expanded=False):
                        st.caption("Tool Arguments:")
                        st.json(cdata.get("arguments", {}))
                        st.caption("Tool Output / Verdict:")
                        out_p = cdata.get("output_preview")
                        if out_p:
                            st.code(str(out_p), language="text")
                        else:
                            st.write("Execution completed with no preview string.")
            else:
                st.caption("ℹ️ No ADK tools invoked during this handoff phase.")


with tab_wiretap:
    render_agent_wiretap(key_prefix="tab_wiretap")

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
