"""Data loader module for HRA-001 with cached, read-only SQLite access."""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from src.db import DEFAULT_DB_PATH, PROJECT_ROOT, get_connection
from src.validation import (
    ValidationError,
    validate_database_integrity,
    validate_database_schema,
    validate_date_range,
)

# Optional Streamlit cache decorator fallback
try:
    import streamlit as st
    cache_data = st.cache_data(ttl=300)
except Exception:
    def cache_data(f):
        return f

DATA_DIR = PROJECT_ROOT / "data"


@cache_data
def load_departments() -> pd.DataFrame:
    """Load all department records (both HOSPITAL root and child departments)."""
    conn = get_connection(read_only=True)
    try:
        df = pd.read_sql_query("SELECT * FROM departments ORDER BY dept_id", conn)
        df["active_flag"] = df["active_flag"].astype(int)
        df["occupancy_warning_threshold_pct"] = df["occupancy_warning_threshold_pct"].astype(float)
        return df
    finally:
        conn.close()


@cache_data
def load_child_departments() -> pd.DataFrame:
    """Load only functional department-level rows (excludes the HOSPITAL root)."""
    conn = get_connection(read_only=True)
    try:
        query = "SELECT * FROM departments WHERE department_level = 'DEPARTMENT' ORDER BY dept_id"
        df = pd.read_sql_query(query, conn)
        df["active_flag"] = df["active_flag"].astype(int)
        df["occupancy_warning_threshold_pct"] = df["occupancy_warning_threshold_pct"].astype(float)
        return df
    finally:
        conn.close()


@cache_data
def load_utilization_categories() -> pd.DataFrame:
    """Load all utilization categories."""
    conn = get_connection(read_only=True)
    try:
        df = pd.read_sql_query("SELECT * FROM utilization_categories ORDER BY category_id", conn)
        df["active_flag"] = df["active_flag"].astype(int)
        return df
    finally:
        conn.close()


@cache_data
def load_patient_encounters(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    dept_id: Optional[int] = None,
) -> pd.DataFrame:
    """Load patient encounters with inclusive admission date and department filters."""
    s, e = validate_date_range(start_date, end_date)
    conn = get_connection(read_only=True)
    try:
        conditions = ["1=1"]
        params: List[Any] = []

        if s:
            conditions.append("admission_date >= ?")
            params.append(s)
        if e:
            conditions.append("admission_date <= ?")
            params.append(e)
        if dept_id is not None:
            conditions.append("dept_id = ?")
            params.append(int(dept_id))

        query = f"""
            SELECT pe.*, d.dept_name, d.dept_code
            FROM patient_encounters pe
            JOIN departments d ON pe.dept_id = d.dept_id
            WHERE {' AND '.join(conditions)}
            ORDER BY pe.admission_date, pe.encounter_id
        """
        df = pd.read_sql_query(query, conn, params=params)
        df["admission_date"] = pd.to_datetime(df["admission_date"])
        df["discharge_date"] = pd.to_datetime(df["discharge_date"])
        return df
    finally:
        conn.close()


@cache_data
def load_daily_utilization(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    dept_id: Optional[int] = None,
    category_id: Optional[int] = None,
) -> pd.DataFrame:
    """Load clean daily utilization records with parameterized filters."""
    s, e = validate_date_range(start_date, end_date)
    conn = get_connection(read_only=True)
    try:
        conditions = ["1=1"]
        params: List[Any] = []

        if s:
            conditions.append("du.metric_date >= ?")
            params.append(s)
        if e:
            conditions.append("du.metric_date <= ?")
            params.append(e)
        if dept_id is not None:
            conditions.append("du.dept_id = ?")
            params.append(int(dept_id))
        if category_id is not None:
            conditions.append("du.category_id = ?")
            params.append(int(category_id))

        query = f"""
            SELECT du.*, d.dept_name, d.dept_code, uc.category_code, uc.category_name, uc.category_group, uc.unit_of_measure
            FROM daily_utilization du
            JOIN departments d ON du.dept_id = d.dept_id
            JOIN utilization_categories uc ON du.category_id = uc.category_id
            WHERE {' AND '.join(conditions)}
            ORDER BY du.metric_date, du.dept_id, du.category_id
        """
        df = pd.read_sql_query(query, conn, params=params)
        df["metric_date"] = pd.to_datetime(df["metric_date"])
        df["available_amount"] = df["available_amount"].astype(float)
        df["used_amount"] = df["used_amount"].astype(float)
        return df
    finally:
        conn.close()


@cache_data
def load_analysis_view(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    dept_id: Optional[int] = None,
    exclude_root: bool = True,
) -> pd.DataFrame:
    """Load the 40-column joined analysis view with inclusive date and department filters."""
    s, e = validate_date_range(start_date, end_date)
    conn = get_connection(read_only=True)
    try:
        conditions = ["1=1"]
        params: List[Any] = []

        if s:
            conditions.append("metric_date >= ?")
            params.append(s)
        if e:
            conditions.append("metric_date <= ?")
            params.append(e)
        if dept_id is not None:
            conditions.append("dept_id = ?")
            params.append(int(dept_id))

        query = f"""
            SELECT *
            FROM vw_department_daily_analysis
            WHERE {' AND '.join(conditions)}
            ORDER BY metric_date, dept_id
        """
        df = pd.read_sql_query(query, conn, params=params)
        if not df.empty and "metric_date" in df.columns:
            df["metric_date"] = pd.to_datetime(df["metric_date"])
        return df
    finally:
        conn.close()


@cache_data
def load_data_quality_issues() -> pd.DataFrame:
    """Load the documented synthetic data quality issues log."""
    path = DATA_DIR / "data_quality_issues.csv"
    if not path.exists():
        raise FileNotFoundError(f"Data quality issue log not found at {path}")
    return pd.read_csv(path)


def verify_database_ready() -> Dict[str, Any]:
    """Perform quick startup validation on the database."""
    conn = get_connection(read_only=True)
    try:
        validate_database_schema(conn)
        validate_database_integrity(conn)
        return {"status": "READY", "db_path": str(DEFAULT_DB_PATH)}
    finally:
        conn.close()
