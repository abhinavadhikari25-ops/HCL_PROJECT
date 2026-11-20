"""UI-01 — Overview / KPIs: Hospital-wide executive resource utilization landing page."""
import streamlit as st
import pandas as pd
from datetime import date

from src.data_loader import load_departments, load_analysis_view, load_patient_encounters
from src.filters import get_active_filters
from src.ui import render_header, render_kpi_row
from src.charts import plot_occupancy_trend, plot_patient_flow
from src.metrics import bed_occupancy_rate, available_beds, count_admissions, count_discharges

st.set_page_config(page_title="Overview | Hospital Resource Utilization", page_icon="🏥", layout="wide")

# Render header
render_header("Executive Resource Utilization Overview", "Hospital-wide occupancy, capacity snapshots, and patient flow")

# Sidebar and filter state
dept_df = load_departments()
filters = get_active_filters(dept_df)

start_date = filters["start_date"]
end_date = filters["end_date"]
dept_id = filters["dept_id"]
dept_label = filters["department_label"]

st.title("🏥 Executive Overview & Key Performance Indicators")
st.caption(f"Showing analytical data from **{start_date}** to **{end_date}** | Scope: **{dept_label}**")

# Load view data for the filtered range
view_df = load_analysis_view(start_date=start_date, end_date=end_date, dept_id=dept_id)
encounters_df = load_patient_encounters(start_date=start_date, end_date=end_date, dept_id=dept_id)

if view_df.empty:
    st.warning("No utilization records found for the selected date range and department filter.")
else:
    # 1. Headline KPIs
    tot_occupied = view_df["occupied_beds"].sum()
    tot_available = view_df["usable_bed_capacity"].sum()
    occ_rate = bed_occupancy_rate(tot_occupied, tot_available)

    # Date-specific latest available bed snapshot
    latest_date = view_df["metric_date"].max()
    latest_day = view_df[view_df["metric_date"] == latest_date]
    latest_avail = latest_day["available_beds"].sum()

    adm_count = count_admissions(encounters_df, start_date=start_date, end_date=end_date)
    dis_count = count_discharges(encounters_df, start_date=start_date, end_date=end_date)

    kpi_cards = [
        {
            "label": "Period Bed Occupancy",
            "value": f"{occ_rate:.1f}%" if occ_rate is not None else "N/A",
            "delta": f"{tot_occupied:,.0f} / {tot_available:,.0f} bed-days",
            "footnote": "Weighted period average",
            "accent": "amber" if (occ_rate and occ_rate > 85.0) else "teal",
        },
        {
            "label": "Available Beds Snapshot",
            "value": f"{latest_avail:,.0f}",
            "delta": f"As of {latest_date.strftime('%d %b %Y')}",
            "footnote": "Usable capacity − occupied",
            "accent": "navy",
        },
        {
            "label": "Total Admissions",
            "value": f"{adm_count:,}",
            "delta": "Unique encounters",
            "footnote": "Inclusive event dates",
            "accent": "teal",
        },
        {
            "label": "Total Discharges",
            "value": f"{dis_count:,}",
            "delta": "Excludes open encounters",
            "footnote": "Discharged patients",
            "accent": "slate",
        },
    ]
    render_kpi_row(kpi_cards)

    st.markdown("---")

    # 2. Occupancy Trend Chart
    daily_summary = view_df.groupby("metric_date").agg({
        "occupied_beds": "sum",
        "usable_bed_capacity": "sum",
        "admissions": "sum",
        "discharges": "sum",
    }).reset_index()

    daily_summary["occupancy_rate_pct"] = (
        daily_summary["occupied_beds"] / daily_summary["usable_bed_capacity"] * 100.0
    ).round(2)

    c1, c2 = st.columns([3, 2])
    with c1:
        st.subheader("Daily Bed Occupancy Rate (%)")
        trend_fig = plot_occupancy_trend(daily_summary, threshold=85.0)
        st.plotly_chart(trend_fig, use_container_width=True)

    with c2:
        st.subheader("Patient Admissions & Discharges")
        flow_fig = plot_patient_flow(daily_summary)
        st.plotly_chart(flow_fig, use_container_width=True)

    # 3. Department Breakdown Table
    st.subheader("Department Utilization Summary")
    dept_summary = view_df.groupby("dept_name").agg({
        "usable_bed_capacity": "sum",
        "occupied_beds": "sum",
        "available_beds": "mean",
        "admissions": "sum",
        "discharges": "sum",
    }).reset_index()

    dept_summary["Period Occupancy (%)"] = (
        dept_summary["occupied_beds"] / dept_summary["usable_bed_capacity"] * 100.0
    ).round(1)
    dept_summary = dept_summary.rename(columns={
        "dept_name": "Department",
        "usable_bed_capacity": "Total Available Bed-Days",
        "occupied_beds": "Total Occupied Bed-Days",
        "available_beds": "Avg Daily Available Beds",
        "admissions": "Admissions",
        "discharges": "Discharges",
    })
    st.dataframe(dept_summary, use_container_width=True, hide_index=True)
