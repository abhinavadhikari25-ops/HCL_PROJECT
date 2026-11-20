"""UI-08 — About & Metric Definitions: Project provenance, KPI definitions, and governance."""
import streamlit as st
import pandas as pd
from src.ui import render_header

st.set_page_config(page_title="About & Definitions | Hospital Resource Utilization", page_icon="ℹ️", layout="wide")

render_header("Project Overview & Metric Definitions", "Academic metadata, data provenance, calculation methodologies, and governance")

st.title("ℹ️ About the Project & Metric Definitions")

col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader("Project Summary")
    st.markdown("""
    **Hospital Resource Utilization Analysis (HRA-001)** is a descriptive data-analytics dashboard built for a hypothetical 250-bed multi-specialty healthcare facility in Ghaziabad, Uttar Pradesh.
    
    The prototype consolidates clinical encounters, bed capacities, workforce scheduling, and diagnostic equipment into one unified, interactive analytical interface.
    """)

    st.subheader("Academic Metadata")
    st.markdown("""
    - **Student Name:** Abhinav Adhikari
    - **Roll Number:** 2503201450005
    - **Degree:** Master of Computer Applications (MCA) — 2nd Year
    - **Specialization:** Data Analytics
    - **Institution:** ABES Engineering College
    - **Document Baseline:** HRA-001-BUILD-14 (November 2026)
    """)

with col_right:
    st.subheader("System Architecture")
    st.markdown("""
    - **Runtime:** Python 3.12
    - **Interface:** Streamlit Multipage Framework
    - **Data Layer:** SQLite (`data/app.db`) with Foreign Key enforcement
    - **Styling:** Tailwind CDN in isolated iframe components
    - **Visualization:** Interactive Plotly graphics
    - **Quality Checks:** Automated `pytest` suite
    """)

st.markdown("---")

st.subheader("📐 Mathematical Metric Definitions")

metrics_table = [
    {
        "KPI Name": "Period Bed Occupancy Rate (%)",
        "Calculation Formula": "SUM(occupied bed-days) / SUM(available bed-days) * 100",
        "Unit": "Percentage (%)",
        "Interpretation": "Weighted period efficiency. Denominator = total capacity minus maintenance downtime.",
    },
    {
        "KPI Name": "Available Beds Snapshot",
        "Calculation Formula": "usable_bed_capacity - occupied_beds",
        "Unit": "Beds (Count)",
        "Interpretation": "Instantaneous vacant bed buffer for a given date and department.",
    },
    {
        "KPI Name": "Average Length of Stay (ALOS)",
        "Calculation Formula": "MEAN(discharge_date - admission_date) for DISCHARGED encounters",
        "Unit": "Days",
        "Interpretation": "Mean duration of completed inpatient stays. Same-day discharge = 0 days. OPEN encounters excluded.",
    },
    {
        "KPI Name": "Staff Utilization Rate (%)",
        "Calculation Formula": "SUM(used_hours) / SUM(available_hours) * 100",
        "Unit": "Percentage (%)",
        "Interpretation": "Separately calculated for Doctors, Nurses, and Technicians.",
    },
    {
        "KPI Name": "Shared Resource Utilization (%)",
        "Calculation Formula": "SUM(used_hours) / SUM(available_hours) * 100",
        "Unit": "Percentage (%)",
        "Interpretation": "Separately monitored for ICU Ventilators, Operating Rooms, and Diagnostic Imaging.",
    },
    {
        "KPI Name": "Capacity Warning Threshold",
        "Calculation Formula": "occupancy_rate_pct > 85.0%",
        "Unit": "Threshold (%)",
        "Interpretation": "Strict greater-than rule. Status: ASSUMED academic assumption.",
    },
]

st.dataframe(pd.DataFrame(metrics_table), use_container_width=True, hide_index=True)

st.markdown("---")
st.warning("""
⚠️ **Academic Prototype & Non-Clinical Disclaimer:**
This project is an academic simulation designed exclusively for educational, operational research, and coursework evaluation purposes. All patient names, encounter records, and clinician identifiers are synthetic. The software does not provide medical diagnoses, clinical triage, or patient-level dispatch decisions.
""")
