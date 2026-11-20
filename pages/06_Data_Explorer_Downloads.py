"""UI-06 — Data Explorer & Downloads: Read-only preview and export of underlying analytical datasets."""
import io
import streamlit as st
import pandas as pd

from src.data_loader import (
    load_departments,
    load_utilization_categories,
    load_patient_encounters,
    load_daily_utilization,
    load_analysis_view,
    load_data_quality_issues,
)
from src.ui import render_header

st.set_page_config(page_title="Data Explorer | Hospital Resource Utilization", page_icon="💾", layout="wide")

render_header("Analytical Data Explorer & Export Hub", "Transparent read-only table views, schema dictionaries, and CSV/Excel downloads")

st.title("💾 Data Explorer & Downloads")
st.caption("Inspect and download clean operational tables and the 40-column joined analytical view.")

table_options = [
    "vw_department_daily_analysis (Joined Analysis View)",
    "departments (Master)",
    "utilization_categories (Master)",
    "patient_encounters (Facts)",
    "daily_utilization (Daily Facts)",
    "data_quality_issues (Audit Log)",
]

selected_table = st.selectbox("Select Table / Dataset to Explore", table_options, index=0)

if "vw_department_daily_analysis" in selected_table:
    df = load_analysis_view()
    table_name = "vw_department_daily_analysis"
elif "departments" in selected_table:
    df = load_departments()
    table_name = "departments"
elif "utilization_categories" in selected_table:
    df = load_utilization_categories()
    table_name = "utilization_categories"
elif "patient_encounters" in selected_table:
    df = load_patient_encounters()
    table_name = "patient_encounters"
elif "daily_utilization" in selected_table:
    df = load_daily_utilization()
    table_name = "daily_utilization"
else:
    df = load_data_quality_issues()
    table_name = "data_quality_issues"

col_meta1, col_meta2 = st.columns(2)
with col_meta1:
    st.metric("Total Records", f"{len(df):,}")
with col_meta2:
    st.metric("Total Columns", f"{len(df.columns)}")

st.subheader(f"Preview: {table_name}")
st.dataframe(df.head(100), use_container_width=True)

# Export options
st.markdown("### Export Dataset")
exp_col1, exp_col2 = st.columns(2)

with exp_col1:
    csv_bytes = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label=f"⬇️ Download {table_name}.csv",
        data=csv_bytes,
        file_name=f"{table_name}.csv",
        mime="text/csv",
        use_container_width=True,
    )

with exp_col2:
    # Build in-memory multi-table Excel
    excel_buffer = io.BytesIO()
    with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
        df.head(1000).to_excel(writer, sheet_name=table_name[:31], index=False)
    st.download_button(
        label=f"⬇️ Download {table_name}.xlsx",
        data=excel_buffer.getvalue(),
        file_name=f"{table_name}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )
