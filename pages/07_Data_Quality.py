"""UI-07 — Data Quality: Audit log, missing value treatment, deduplication, and anomaly reporting."""
import streamlit as st
import pandas as pd

from src.data_loader import load_data_quality_issues, load_departments, load_child_departments
from src.ui import render_header, render_kpi_row
import plotly.express as px

st.set_page_config(page_title="Data Quality | Hospital Resource Utilization", page_icon="🧹", layout="wide")

render_header("Data Quality Assurance & Cleaning Pipeline", "Transparent audit trail of raw extract defects, repairs, and integrity rules")

st.title("🧹 Data Quality Assurance & Issue Log")
st.caption("Demonstrating automated handling of synthetic data quality defects injected for cleaning validation.")

issues_df = load_data_quality_issues()

# Quality Metrics
total_issues = len(issues_df)
missing_count = len(issues_df[issues_df["issue_type"] == "MISSING_VALUE"])
dup_count = len(issues_df[issues_df["issue_type"] == "DUPLICATE_ROW"])
outlier_count = len(issues_df[issues_df["issue_type"] == "OUTLIER"])

kpi_cards = [
    {"label": "Total Quality Defects Logged", "value": f"{total_issues:,}", "delta": "Raw extract defects", "accent": "navy"},
    {"label": "Missing Values Repaired", "value": f"{missing_count:,}", "delta": "Group-median imputation", "accent": "teal"},
    {"label": "Duplicate Rows Deduplicated", "value": f"{dup_count:,}", "delta": "Deterministic composite key", "accent": "amber"},
    {"label": "High-Use Outliers Flagged", "value": f"{outlier_count:,}", "delta": ">150% capacity", "accent": "slate"},
]
render_kpi_row(kpi_cards)

st.markdown("---")

c1, c2 = st.columns([1, 2])
with c1:
    st.subheader("Issues by Category")
    issue_counts = issues_df["issue_type"].value_counts().reset_index()
    issue_counts.columns = ["Issue Type", "Count"]
    fig_pie = px.pie(issue_counts, names="Issue Type", values="Count", color_discrete_sequence=["#0E86D4", "#17365D", "#E38B29"])
    fig_pie.update_layout(height=320, margin={"l": 10, "r": 10, "t": 20, "b": 10})
    st.plotly_chart(fig_pie, use_container_width=True)

with c2:
    st.subheader("Filter Quality Issue Log")
    type_options = ["All Issues"] + sorted(issues_df["issue_type"].unique().tolist())
    selected_type = st.selectbox("Filter by Issue Type", type_options, index=0)

    filtered_issues = issues_df if selected_type == "All Issues" else issues_df[issues_df["issue_type"] == selected_type]
    st.write(f"Showing **{len(filtered_issues)}** records:")
    st.dataframe(filtered_issues, use_container_width=True, hide_index=True)

st.markdown("---")
st.subheader("Cleaning Pipeline Rules & Invariants")
st.markdown("""
- **Deduplication:** Composite business key `(metric_date, dept_id, category_id)` is deduplicated deterministically by keeping the primary record.
- **Missing Value Imputation:** Missing `used_amount` records are repaired using a multi-tier group fallback (Department + Category median $\\rightarrow$ Category median $\\rightarrow$ Global median).
- **Outlier Lineage:** Utilization exceeding 150% of available capacity is flagged in the audit register without silently corrupting historical lineage.
""")
