"""UI-05 — Insights & Threshold Monitor: Bed occupancy threshold monitoring and operational breach alerts."""
import streamlit as st
import pandas as pd

from src.data_loader import load_departments, load_analysis_view
from src.filters import get_active_filters
from src.ui import render_header, render_kpi_row
from src.charts import plot_occupancy_trend
from src.metrics import is_threshold_breach

st.set_page_config(page_title="Threshold Monitor | Hospital Resource Utilization", page_icon="⚠️", layout="wide")

render_header("Capacity Threshold & Exception Monitor", "Operational breach alerts, occupancy thresholds, and capacity governance")

dept_df = load_departments()
filters = get_active_filters(dept_df)

start_date = filters["start_date"]
end_date = filters["end_date"]
dept_id = filters["dept_id"]
dept_label = filters["department_label"]

st.title("⚠️ Insights & Occupancy Threshold Monitor")
st.caption(f"Monitoring threshold breaches (>85.0%) from **{start_date}** to **{end_date}** | Scope: **{dept_label}**")

view_df = load_analysis_view(start_date=start_date, end_date=end_date, dept_id=dept_id)

if view_df.empty:
    st.info("No records to monitor for the selected period.")
else:
    # 85% Warning threshold
    threshold_val = 85.0
    view_df["is_breach"] = view_df["occupancy_rate_pct"].apply(lambda x: is_threshold_breach(x, threshold_val))
    breaches_df = view_df[view_df["is_breach"]].copy()

    total_days = view_df["metric_date"].nunique()
    total_obs = len(view_df)
    breach_count = len(breaches_df)
    breach_pct = (breach_count / total_obs * 100.0) if total_obs > 0 else 0.0

    kpi_cards = [
        {"label": "Active Warning Threshold", "value": "85.0%", "delta": "Strict greater-than rule", "footnote": "Status: ASSUMED / Academic", "accent": "amber"},
        {"label": "Total Breach Events", "value": f"{breach_count:,}", "delta": f"{breach_pct:.1f}% of observations", "footnote": "Department-days exceeding 85%", "accent": "slate" if breach_count == 0 else "navy"},
        {"label": "Peak Observed Occupancy", "value": f"{view_df['occupancy_rate_pct'].max():.1f}%", "footnote": "Highest daily department rate", "accent": "teal"},
        {"label": "Hospital Capacity Buffer", "value": "15.0%", "footnote": "Planned safety margin", "accent": "slate"},
    ]
    render_kpi_row(kpi_cards)

    st.markdown("---")

    breach_only = st.checkbox("Show Breach Events Only (> 85.0% Occupancy)", value=False)
    chart_data = breaches_df if breach_only else view_df

    st.subheader("Occupancy Timeline & Breach Observations")
    fig = plot_occupancy_trend(chart_data, threshold=85.0, title="Daily Occupancy with 85% Threshold Breaches")
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("Detailed Breach Event Log")
    if breaches_df.empty:
        st.success("🎉 No threshold breaches detected in the selected timeframe!")
    else:
        table_cols = [
            "metric_date", "dept_name", "usable_bed_capacity", "occupied_beds",
            "available_beds", "occupancy_rate_pct"
        ]
        display_breaches = breaches_df[table_cols].sort_values("occupancy_rate_pct", ascending=False)
        display_breaches = display_breaches.rename(columns={
            "metric_date": "Date",
            "dept_name": "Department",
            "usable_bed_capacity": "Total Beds",
            "occupied_beds": "Occupied Beds",
            "available_beds": "Available Beds",
            "occupancy_rate_pct": "Occupancy Rate (%)",
        })
        st.dataframe(display_breaches, use_container_width=True, hide_index=True)

    st.info("📌 **Operational Note:** This monitor flags department-days exceeding the 85.0% threshold for administrative capacity balancing. It is an operational prototype and not intended for real-time clinical dispatch.")
