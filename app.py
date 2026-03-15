"""
app.py — Streamlit UI for the AI Business Process Analyzer.
"""

import streamlit as st
import pandas as pd
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

import parser as proc_parser
import analyzer

# --- Page config ---
st.set_page_config(
    page_title="AI Business Process Analyzer",
    page_icon="🔍",
    layout="wide",
)

# --- Header ---
st.title("🔍 AI Business Process Analyzer")
st.markdown(
    "Upload a process event log (CSV) or describe your process in plain text — "
    "get an AI-powered audit report with bottlenecks, inefficiencies, and prioritized recommendations."
)
st.divider()

# --- Sidebar ---
with st.sidebar:
    st.header("Settings")
    api_key_input = st.text_input(
        "Anthropic API Key",
        type="password",
        value=os.getenv("ANTHROPIC_API_KEY", ""),
        help="Your key is never stored. Get one at console.anthropic.com",
    )
    if api_key_input:
        os.environ["ANTHROPIC_API_KEY"] = api_key_input

    st.divider()
    st.markdown("**Expected CSV columns:**")
    st.code("case_id, timestamp, activity, resource")
    st.markdown("**Timestamp format:**")
    st.code("YYYY-MM-DD HH:MM:SS")
    st.divider()
    st.markdown("**Sample datasets included:**")
    st.markdown("- `order_processing.csv`")
    st.markdown("- `invoice_approval.csv`")
    st.markdown("- `customer_onboarding.csv`")
    st.divider()
    st.caption("Built with Python · Streamlit · Claude API")

# --- Input mode tabs ---
tab_csv, tab_text = st.tabs(["📂 Upload Event Log (CSV)", "✍️ Describe Your Process"])

# ===== TAB 1: CSV Upload =====
with tab_csv:
    st.subheader("Upload a Process Event Log")

    col1, col2 = st.columns([2, 1])
    with col1:
        uploaded_file = st.file_uploader(
            "Upload CSV file",
            type=["csv"],
            help="CSV with columns: case_id, timestamp, activity, resource",
        )
    with col2:
        st.markdown("**Or try a sample:**")
        sample_choice = st.selectbox(
            "Load sample dataset",
            ["— Select —", "Order Processing", "Invoice Approval", "Customer Onboarding"],
        )
        load_sample = st.button("Load Sample")

    # Load data
    df = None
    process_name = "Business Process"

    sample_map = {
        "Order Processing": ("sample_data/order_processing.csv", "Order Processing"),
        "Invoice Approval": ("sample_data/invoice_approval.csv", "Invoice Approval"),
        "Customer Onboarding": ("sample_data/customer_onboarding.csv", "Customer Onboarding"),
    }

    if load_sample and sample_choice != "— Select —":
        path, process_name = sample_map[sample_choice]
        try:
            df = pd.read_csv(path)
            st.success(f"Loaded sample: {sample_choice}")
        except FileNotFoundError:
            st.error(f"Sample file not found: {path}")

    elif uploaded_file:
        df = pd.read_csv(uploaded_file)
        process_name = uploaded_file.name.replace(".csv", "").replace("_", " ").title()
        st.success(f"Uploaded: {uploaded_file.name}")

    if df is not None:
        # Preview
        with st.expander("Preview data", expanded=False):
            st.dataframe(df.head(20), use_container_width=True)
            st.caption(f"{len(df)} rows · {df.columns.tolist()}")

        # Parse stats
        try:
            stats = proc_parser.parse_event_log(df=df)
            s = stats["summary"]

            # Metrics row
            st.subheader("Process Overview")
            m1, m2, m3, m4, m5 = st.columns(5)
            m1.metric("Total Cases", s["total_cases"])
            m2.metric("Avg Duration", f"{s['avg_case_duration_hours']}h")
            m3.metric("Median Duration", f"{s['median_case_duration_hours']}h")
            m4.metric("Rework Rate", f"{s['rework_rate_pct']}%")
            m5.metric("Activities", s["unique_activities"])

            # Charts
            col_a, col_b = st.columns(2)

            with col_a:
                st.markdown("**Activity Waiting Times (avg hours)**")
                act_df = pd.DataFrame(stats["activity_stats"][:8])
                if not act_df.empty:
                    st.bar_chart(act_df.set_index("activity")["avg_hours"])

            with col_b:
                st.markdown("**Case Duration Distribution**")
                dur_df = pd.DataFrame(stats["case_durations"])
                if not dur_df.empty:
                    st.bar_chart(dur_df.set_index("case_id")["duration_hours"])

            # Analyze button
            st.divider()
            if st.button("🤖 Run AI Analysis", type="primary", key="analyze_csv"):
                if not os.getenv("ANTHROPIC_API_KEY"):
                    st.error("Add your Anthropic API key in the sidebar first.")
                else:
                    with st.spinner("Analyzing your process with Claude AI..."):
                        try:
                            report = analyzer.analyze_from_stats(stats, process_name)
                            st.session_state["csv_report"] = report
                            st.session_state["csv_report_name"] = process_name
                        except Exception as e:
                            st.error(f"Analysis failed: {e}")

            # Show report
            if "csv_report" in st.session_state:
                st.subheader("AI Process Audit Report")
                st.markdown(st.session_state["csv_report"])

                # Download
                report_filename = f"process_report_{st.session_state['csv_report_name'].replace(' ', '_').lower()}_{datetime.now().strftime('%Y%m%d_%H%M')}.md"
                st.download_button(
                    "⬇️ Download Report (Markdown)",
                    data=st.session_state["csv_report"],
                    file_name=report_filename,
                    mime="text/markdown",
                )

        except ValueError as e:
            st.error(f"Could not parse file: {e}")
        except Exception as e:
            st.error(f"Unexpected error: {e}")

# ===== TAB 2: Plain Text =====
with tab_text:
    st.subheader("Describe Your Process in Plain Text")
    st.markdown(
        "No data file? Just describe how your process works — who does what, in what order, "
        "where things get stuck — and get an AI analysis."
    )

    example_text = """Our order fulfillment process starts when a customer places an order online.
It then goes to our finance team for a credit check, which can take anywhere from 30 minutes to 2 days
depending on team availability. After that, warehouse staff check inventory and pick the items.
We have a quality control step where about 30% of orders fail and need to be re-packed.
Once QC passes, the logistics team arranges shipping. The whole process often takes 3-7 days,
but our target is 2 days. The main complaints from customers are around delays during credit check
and having to wait for QC re-work."""

    process_text = st.text_area(
        "Process description",
        height=200,
        placeholder=example_text,
        help="Describe the steps, who is involved, typical timings, known problems",
    )

    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("📝 Load Example", key="load_example"):
            st.session_state["example_loaded"] = example_text
    if "example_loaded" in st.session_state:
        process_text = st.session_state["example_loaded"]

    if st.button("🤖 Run AI Analysis", type="primary", key="analyze_text"):
        if not process_text.strip():
            st.warning("Please enter a process description first.")
        elif not os.getenv("ANTHROPIC_API_KEY"):
            st.error("Add your Anthropic API key in the sidebar first.")
        else:
            with st.spinner("Analyzing your process with Claude AI..."):
                try:
                    report = analyzer.analyze_from_text(process_text)
                    st.session_state["text_report"] = report
                except Exception as e:
                    st.error(f"Analysis failed: {e}")

    if "text_report" in st.session_state:
        st.subheader("AI Process Audit Report")
        st.markdown(st.session_state["text_report"])

        report_filename = f"process_report_text_{datetime.now().strftime('%Y%m%d_%H%M')}.md"
        st.download_button(
            "⬇️ Download Report (Markdown)",
            data=st.session_state["text_report"],
            file_name=report_filename,
            mime="text/markdown",
        )

# --- Footer ---
st.divider()
st.caption(
    "AI Business Process Analyzer · Built by Ali Wahab · "
    "[GitHub](https://github.com/aliwahab/ai-process-analyzer)"
)
