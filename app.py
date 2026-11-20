"""HRA-001 — Hospital Resource Utilization Analysis Multipage Application."""
import streamlit as st

# Configure navigation for all 8 application screens
pages = [
    st.Page("pages/01_Overview.py", title="Overview & KPIs", icon="🏥", default=True),
    st.Page("pages/02_Patient_Flow_Trend.py", title="Patient Flow & Trends", icon="📈"),
    st.Page("pages/03_Department_Resource_Compare.py", title="Department & Resource Compare", icon="⚖️"),
    st.Page("pages/04_EDA_Statistics.py", title="EDA & Statistics", icon="📊"),
    st.Page("pages/05_Insights_Threshold_Monitor.py", title="Threshold Monitor", icon="⚠️"),
    st.Page("pages/06_Data_Explorer_Downloads.py", title="Data Explorer & Downloads", icon="💾"),
    st.Page("pages/07_Data_Quality.py", title="Data Quality", icon="🧹"),
    st.Page("pages/08_About_Metric_Definitions.py", title="About & Definitions", icon="ℹ️"),
]

pg = st.navigation(pages)
pg.run()
