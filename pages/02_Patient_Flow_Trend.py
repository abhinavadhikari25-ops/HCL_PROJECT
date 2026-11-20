"""UI-02 — Patient Flow & Trends: Inpatient throughput, admissions, discharges, and length of stay."""
import streamlit as st
import pandas as pd

from src.data_loader import load_departments, load_patient_encounters
from src.filters import get_active_filters
from src.ui import render_header, render_kpi_row
from src.charts import plot_los_distribution
from src.metrics import count_admissions, count_discharges, average_length_of_stay, admissions_by_period
import plotly.express as px

st.set_page_config(page_title="Patient Flow | Hospital Resource Utilization", page_icon="📈", layout="wide")

render_header("Patient Flow & Throughput Trends", "Admissions, discharges, average length of stay (ALOS), and seasonal dynamics")

dept_df = load_departments()
filters = get_active_filters(dept_df)

start_date = filters["start_date"]
end_date = filters["end_date"]
dept_id = filters["dept_id"]
dept_label = filters["department_label"]

st.title("📈 Patient Flow & Admission Trends")
st.caption(f"Period: **{start_date}** to **{end_date}** | Scope: **{dept_label}**")

encounters = load_patient_encounters(start_date=start_date, end_date=end_date, dept_id=dept_id)

if encounters.empty:
    st.info("No encounter records match the selected date range and department.")
else:
    adm_count = count_admissions(encounters, start_date=start_date, end_date=end_date)
    dis_count = count_discharges(encounters, start_date=start_date, end_date=end_date)
    alos_val = average_length_of_stay(encounters, start_date=start_date, end_date=end_date)
    open_count = len(encounters[encounters["encounter_status"] == "OPEN"])

    kpi_cards = [
        {"label": "Total Admissions", "value": f"{adm_count:,}", "delta": "Selected window", "accent": "navy"},
        {"label": "Total Discharges", "value": f"{dis_count:,}", "delta": "Completed stays", "accent": "teal"},
        {"label": "Average Length of Stay", "value": f"{alos_val:.1f} days" if alos_val else "N/A", "footnote": "Excludes open encounters", "accent": "amber"},
        {"label": "Currently Open Encounters", "value": f"{open_count:,}", "footnote": "Active inpatients", "accent": "slate"},
    ]
    render_kpi_row(kpi_cards)

    st.markdown("---")

    col_ctrl, col_chart = st.columns([1, 3])
    with col_ctrl:
        st.subheader("Aggregation")
        freq_choice = st.radio("Trend Frequency", ["Daily", "Weekly", "Monthly"], index=0)
        freq_code = {"Daily": "D", "Weekly": "W", "Monthly": "ME"}[freq_choice]

    with col_chart:
        grouped_adm = admissions_by_period(encounters, start_date=start_date, end_date=end_date, frequency=freq_code)
        st.subheader(f"{freq_choice} Admissions Trend")
        fig_adm = px.line(grouped_adm, x="period", y="admissions", markers=True, color_discrete_sequence=["#0E86D4"])
        fig_adm.update_layout(height=350, margin={"l": 20, "r": 20, "t": 30, "b": 20})
        st.plotly_chart(fig_adm, use_container_width=True)

    st.markdown("---")
    st.subheader("Length of Stay (LOS) Distribution by Department")
    los_fig = plot_los_distribution(encounters)
    st.plotly_chart(los_fig, use_container_width=True)
