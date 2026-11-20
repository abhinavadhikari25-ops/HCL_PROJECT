"""UI-04 — EDA & Statistics: Statistical distributions, outlier detection, and correlation analysis."""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

from src.data_loader import load_departments, load_analysis_view
from src.filters import get_active_filters
from src.ui import render_header
from src.statistics import descriptive_statistics, detect_iqr_outliers, pearson_correlation

st.set_page_config(page_title="EDA & Statistics | Hospital Resource Utilization", page_icon="📊", layout="wide")

render_header("Exploratory Data Analysis & Statistics", "Statistical distributions, variability metrics, and correlation analysis")

dept_df = load_departments()
filters = get_active_filters(dept_df)

start_date = filters["start_date"]
end_date = filters["end_date"]
dept_id = filters["dept_id"]
dept_label = filters["department_label"]

st.title("📊 Exploratory Data Analysis & Statistics")
st.caption(f"Analyzing operational distributions from **{start_date}** to **{end_date}** | Scope: **{dept_label}**")

view_df = load_analysis_view(start_date=start_date, end_date=end_date, dept_id=dept_id)

if view_df.empty:
    st.info("No records found for the selected filter.")
else:
    metrics_map = {
        "Bed Occupancy Rate (%)": "occupancy_rate_pct",
        "Available Beds Count": "available_beds",
        "Admissions": "admissions",
        "Discharges": "discharges",
        "Doctor Used Hours": "doctor_used_hours",
        "Nurse Used Hours": "nurse_used_hours",
        "Technician Used Hours": "technician_used_hours",
        "Ventilator Used Hours": "icu_ventilator_used_hours",
    }

    selected_label = st.selectbox("Select Operational Metric for Distribution Analysis", list(metrics_map.keys()), index=0)
    col_name = metrics_map[selected_label]
    series = view_df[col_name].dropna()

    stats = descriptive_statistics(series)

    # 1. KPI row for statistics
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Sample Mean", f"{stats['mean']:.2f}" if stats['mean'] is not None else "N/A")
    c2.metric("Median (Q2)", f"{stats['median']:.2f}" if stats['median'] is not None else "N/A")
    c3.metric("Standard Deviation", f"{stats['std']:.2f}" if stats['std'] is not None else "N/A")
    c4.metric("Interquartile Range (IQR)", f"{stats['iqr']:.2f}" if stats['iqr'] is not None else "N/A")

    st.markdown("---")

    # 2. Charts
    chart_c1, chart_c2 = st.columns(2)
    with chart_c1:
        st.subheader(f"{selected_label} Histogram")
        hist_fig = px.histogram(view_df, x=col_name, nbins=30, color_discrete_sequence=["#17365D"], marginal="box")
        hist_fig.update_layout(height=380, margin={"l": 20, "r": 20, "t": 30, "b": 20})
        st.plotly_chart(hist_fig, use_container_width=True)

    with chart_c2:
        st.subheader("Outlier Audit (Tukey IQR)")
        outliers = detect_iqr_outliers(series)
        st.write(f"Detected **{len(outliers)}** statistical outlier observations.")
        if not outliers.empty:
            outlier_rows = view_df.loc[outliers.index, ["metric_date", "dept_name", col_name]].head(10)
            st.dataframe(outlier_rows, use_container_width=True, hide_index=True)
        else:
            st.info("No extreme statistical outliers detected in this subset.")

    st.markdown("---")
    st.subheader("Bivariate Correlation Heatmap")
    num_cols = ["occupancy_rate_pct", "admissions", "discharges", "doctor_used_hours", "nurse_used_hours", "icu_ventilator_used_hours"]
    corr_df = view_df[num_cols].corr().round(2)
    corr_fig = px.imshow(corr_df, text_auto=True, aspect="auto", color_continuous_scale="Blues", title="Pearson Correlation Matrix")
    corr_fig.update_layout(height=420)
    st.plotly_chart(corr_fig, use_container_width=True)
    st.caption("ℹ️ *Note: Correlation reflects descriptive linear relationships within synthetic operational records and does not imply clinical causation.*")
