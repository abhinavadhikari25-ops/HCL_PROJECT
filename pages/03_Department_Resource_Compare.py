"""UI-03 — Department & Resource Compare: Multi-department benchmarks and capacity allocation."""
import streamlit as st
import pandas as pd

from src.data_loader import load_departments, load_analysis_view
from src.filters import get_active_filters
from src.ui import render_header
from src.charts import plot_department_occupancy_bars, plot_staff_utilization_bars
import plotly.express as px

st.set_page_config(page_title="Department Compare | Hospital Resource Utilization", page_icon="⚖️", layout="wide")

render_header("Department & Resource Comparison", "Cross-department benchmarks for beds, medical staff, and equipment")

dept_df = load_departments()
filters = get_active_filters(dept_df)

start_date = filters["start_date"]
end_date = filters["end_date"]
dept_id = filters["dept_id"]
dept_label = filters["department_label"]

st.title("⚖️ Department & Resource Comparison")
st.caption(f"Comparing clinical units from **{start_date}** to **{end_date}**")

view_df = load_analysis_view(start_date=start_date, end_date=end_date, dept_id=dept_id)

if view_df.empty:
    st.info("No comparative data available for the chosen filters.")
else:
    # Department summary
    dept_agg = view_df.groupby("dept_name").agg({
        "occupied_beds": "sum",
        "usable_bed_capacity": "sum",
        "available_beds": "mean",
        "doctor_available_hours": "sum",
        "doctor_used_hours": "sum",
        "nurse_available_hours": "sum",
        "nurse_used_hours": "sum",
        "technician_available_hours": "sum",
        "technician_used_hours": "sum",
        "icu_ventilator_available_hours": "sum",
        "icu_ventilator_used_hours": "sum",
        "operating_room_available_hours": "sum",
        "operating_room_used_hours": "sum",
        "diagnostic_imaging_available_hours": "sum",
        "diagnostic_imaging_used_hours": "sum",
    }).reset_index()

    dept_agg["occupancy_rate_pct"] = (dept_agg["occupied_beds"] / dept_agg["usable_bed_capacity"] * 100.0).round(1)
    dept_agg["doctor_utilization_pct"] = (dept_agg["doctor_used_hours"] / dept_agg["doctor_available_hours"] * 100.0).round(1)
    dept_agg["nurse_utilization_pct"] = (dept_agg["nurse_used_hours"] / dept_agg["nurse_available_hours"] * 100.0).round(1)
    dept_agg["technician_utilization_pct"] = (dept_agg["technician_used_hours"] / dept_agg["technician_available_hours"] * 100.0).round(1)

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Bed Occupancy Rate Ranking")
        occ_fig = plot_department_occupancy_bars(dept_agg, threshold=85.0)
        st.plotly_chart(occ_fig, use_container_width=True)

    with c2:
        st.subheader("Staff Utilization by Role")
        staff_fig = plot_staff_utilization_bars(dept_agg)
        st.plotly_chart(staff_fig, use_container_width=True)

    st.markdown("---")
    st.subheader("Equipment & Diagnostic Resource Utilization")

    res_df = pd.DataFrame([
        {
            "Resource": "ICU Ventilators (Hours)",
            "Available Hours": dept_agg["icu_ventilator_available_hours"].sum(),
            "Used Hours": dept_agg["icu_ventilator_used_hours"].sum(),
            "Utilization Rate (%)": round(dept_agg["icu_ventilator_used_hours"].sum() / dept_agg["icu_ventilator_available_hours"].sum() * 100.0, 1),
        },
        {
            "Resource": "Operating Rooms (Hours)",
            "Available Hours": dept_agg["operating_room_available_hours"].sum(),
            "Used Hours": dept_agg["operating_room_used_hours"].sum(),
            "Utilization Rate (%)": round(dept_agg["operating_room_used_hours"].sum() / dept_agg["operating_room_available_hours"].sum() * 100.0, 1),
        },
        {
            "Resource": "Diagnostic Imaging (Hours)",
            "Available Hours": dept_agg["diagnostic_imaging_available_hours"].sum(),
            "Used Hours": dept_agg["diagnostic_imaging_used_hours"].sum(),
            "Utilization Rate (%)": round(dept_agg["diagnostic_imaging_used_hours"].sum() / dept_agg["diagnostic_imaging_available_hours"].sum() * 100.0, 1),
        },
    ])
    st.dataframe(res_df, use_container_width=True, hide_index=True)
