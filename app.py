"""
app.py - TestForge Interactive Streamlit Web Interface.

Authors: Sourabh & Shreshth
Course: CSE3101 - Agentic AI
"""

import os
import sys
import json
import time
import streamlit as st

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from testforge.ingestion import TargetManagerAgent
from testforge.orchestrator import TestForgeOrchestrator
from testforge.logger import TraceLogger
from testforge.accel import hw_profile

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
    model_name = st.selectbox(
        "Foundation Model",
        ["gemini-3.6-flash", "gemini-2.5-flash", "gemini-2.5-pro", "gemini-1.5-flash"],
        index=0
    )
    max_iterations = st.slider("Max Reflection Iterations", min_value=1, max_value=5, value=3)
    target_score = st.slider("Target Mutation Score (%)", min_value=50.0, max_value=100.0, value=85.0, step=5.0)

    st.divider()
    st.subheader("💻 Hardware Profile")
    st.write(f"**Architecture:** {hw_profile.machine} ({hw_profile.os_system})")
    st.write(f"**CPU Cores:** {hw_profile.cpu_count}")
    st.write(f"**Sandbox Workers:** {hw_profile.recommended_workers}")
    st.write(f"**Unified RAM:** {hw_profile.total_memory_gb} GB")

    has_key = bool(os.environ.get("GEMINI_API_KEY"))
    if has_key:
        st.success("🟢 GEMINI_API_KEY Configured (Live API)")
    else:
        st.warning("🟡 GEMINI_API_KEY Not Set (Deterministic Fallback)")

# Tabs for Mode A vs Mode B
tab_ingest, tab_synth, tab_telemetry = st.tabs([
    "📁 Mode A: Pick / Upload Existing File",
    "✨ Mode B: AI Module Synthesis",
    "📊 Observability & Telemetry Trace"
])

target_code_to_run = None
target_file_path = None

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
                target_file_path = os.path.join(samples_dir, chosen_sample)
                with open(target_file_path, "r", encoding="utf-8") as f:
                    target_code_to_run = f.read()
        else:
            uploaded_file = st.file_uploader("Upload Python File", type=["py"])
            if uploaded_file:
                target_code_to_run = uploaded_file.getvalue().decode("utf-8")
                temp_upload_path = os.path.join("samples", f"uploaded_{uploaded_file.name}")
                with open(temp_upload_path, "w", encoding="utf-8") as f:
                    f.write(target_code_to_run)
                target_file_path = temp_upload_path

    with col2:
        if target_code_to_run and target_file_path:
            supervisor = TargetManagerAgent(model_name=model_name)
            analysis = supervisor.ingest_file(target_file_path)
            st.write(f"**Module:** `{analysis.module_name}`")
            st.write(f"**Functions:** `{', '.join(analysis.functions) if analysis.functions else 'None'}`")
            st.write(f"**Classes:** `{', '.join(analysis.classes) if analysis.classes else 'None'}`")
            with st.expander("View Source Code", expanded=False):
                st.code(target_code_to_run, language="python")

with tab_synth:
    st.subheader("Synthesize New Python Module via Gemini")
    prompt_input = st.text_area(
        "Describe the business logic or algorithm to generate:",
        placeholder="e.g. Implement a stock trading order book that matches BUY and SELL limit orders with price-time priority."
    )
    if st.button("🚀 Synthesize Module", key="synth_btn"):
        if prompt_input.strip():
            with st.spinner("TargetManagerAgent synthesizing production code with rich boundary checks..."):
                supervisor = TargetManagerAgent(model_name=model_name)
                synthed_path, synthed_code = supervisor.synthesize_module(prompt_input)
                target_file_path = synthed_path
                target_code_to_run = synthed_code
                st.success(f"Synthesized code saved to: `{synthed_path}`")
                st.code(synthed_code, language="python")

# Execution Area
st.divider()
st.subheader("🔥 Execution & Hardening Pipeline")

if st.button("⚡ Run TestForge Autonomous Hardening", type="primary", use_container_width=True):
    if not target_code_to_run or not target_file_path:
        st.error("Please select, upload, or synthesize a target module first!")
    else:
        status_container = st.container()
        progress_bar = st.progress(0.0)
        col_metrics1, col_metrics2, col_metrics3 = st.columns(3)

        metric_cov = col_metrics1.empty()
        metric_score = col_metrics2.empty()
        metric_status = col_metrics3.empty()

        metric_cov.metric("Line Coverage", "Calculating...")
        metric_score.metric("Mutation Score", "0.0%")
        metric_status.metric("Pipeline Status", "Initializing...")

        trace_log = "testforge_trace.jsonl"
        orchestrator = TestForgeOrchestrator(
            target_source_code=target_code_to_run,
            max_iterations=max_iterations,
            target_mutation_score=target_score,
            model_name=model_name,
            trace_log_path=trace_log,
            target_file_path=target_file_path
        )

        with st.spinner("Multi-Agent reflection loop running across CPU cores..."):
            final_state = orchestrator.run()
            orchestrator.export_hardened_suite("test_hardened.py")

        progress_bar.progress(1.0)
        final_metric = final_state.history[-1] if final_state.history else None
        final_score = final_metric.mutation_score if final_metric else 0.0

        metric_cov.metric("Line Coverage", f"{final_state.baseline_line_coverage:.1f}%")
        metric_score.metric("Mutation Score", f"{final_score:.1f}%", delta=f"{final_score - 50.0:.1f}%")
        metric_status.metric("Status", "SUCCESS" if final_score >= target_score else "TERMINATED")

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

        # Standalone Test Suite Export Viewer
        st.subheader("📦 Final Hardened Test Suite (`test_hardened.py`)")
        with open("test_hardened.py", "r", encoding="utf-8") as tf:
            hardened_content = tf.read()
        st.code(hardened_content, language="python")
        st.info("Verified standalone: You can run `pytest test_hardened.py -v` in any terminal.")

with tab_telemetry:
    st.subheader("🔍 Real Telemetry & Trace Inspector (`testforge_trace.jsonl`)")
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
