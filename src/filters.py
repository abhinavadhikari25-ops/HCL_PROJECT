"""Shared filter helpers for HRA-001."""
from __future__ import annotations

from datetime import date
from typing import Any, Dict, Optional, Tuple

import pandas as pd
import streamlit as st

DEFAULT_START_DATE = date(2025, 11, 3)
DEFAULT_END_DATE = date(2026, 11, 2)


def get_active_filters(departments_df: pd.DataFrame) -> Dict[str, Any]:
    """Retrieve or initialize shared filter state from sidebar."""
    child_depts = departments_df[departments_df["department_level"] == "DEPARTMENT"]
    dept_names = sorted(child_depts["dept_name"].tolist())

    from src.ui import render_global_filters

    filter_state = render_global_filters(
        department_names=dept_names,
        min_date=DEFAULT_START_DATE,
        max_date=DEFAULT_END_DATE,
    )

    date_range = filter_state.get("date_range")
    if date_range and len(date_range) == 2:
        start_date_str = date_range[0].strftime("%Y-%m-%d")
        end_date_str = date_range[1].strftime("%Y-%m-%d")
    elif date_range and len(date_range) == 1:
        start_date_str = date_range[0].strftime("%Y-%m-%d")
        end_date_str = date_range[0].strftime("%Y-%m-%d")
    else:
        start_date_str = DEFAULT_START_DATE.strftime("%Y-%m-%d")
        end_date_str = DEFAULT_END_DATE.strftime("%Y-%m-%d")

    dept_label = filter_state.get("department")
    dept_id = None
    if dept_label:
        match = child_depts[child_depts["dept_name"] == dept_label]
        if not match.empty:
            dept_id = int(match.iloc[0]["dept_id"])

    return {
        "start_date": start_date_str,
        "end_date": end_date_str,
        "dept_id": dept_id,
        "dept_name": dept_label,
        "is_all_departments": dept_id is None,
        "department_label": filter_state.get("department_label", "All departments"),
    }
