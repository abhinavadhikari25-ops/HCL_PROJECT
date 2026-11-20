"""Operational KPI and patient flow metrics for HRA-001."""
from __future__ import annotations

from typing import Any, Dict, Optional, Union
import numpy as np
import pandas as pd


def bed_occupancy_rate(occupied_bed_days: Union[int, float], available_bed_days: Union[int, float]) -> Optional[float]:
    """Calculate weighted bed occupancy rate percentage.

    Formula: (occupied_bed_days / available_bed_days) * 100
    Returns None if available_bed_days <= 0.
    """
    if available_bed_days is None or available_bed_days <= 0:
        return None
    if occupied_bed_days is None:
        return 0.0
    return float((occupied_bed_days / available_bed_days) * 100.0)


def available_beds(usable_capacity: Union[int, float], occupied_beds: Union[int, float]) -> float:
    """Calculate available beds for a date/department."""
    cap = usable_capacity if usable_capacity is not None else 0.0
    occ = occupied_beds if occupied_beds is not None else 0.0
    return float(cap - occ)


def staff_utilization_rate(used_hours: Union[int, float], available_hours: Union[int, float]) -> Optional[float]:
    """Calculate staff utilization rate percentage."""
    if available_hours is None or available_hours <= 0:
        return None
    if used_hours is None:
        return 0.0
    return float((used_hours / available_hours) * 100.0)


def resource_utilization_rate(used_amount: Union[int, float], available_amount: Union[int, float]) -> Optional[float]:
    """Calculate shared resource utilization rate percentage."""
    if available_amount is None or available_amount <= 0:
        return None
    if used_amount is None:
        return 0.0
    return float((used_amount / available_amount) * 100.0)


def is_threshold_breach(occupancy_pct: Union[int, float], threshold_pct: Union[int, float]) -> bool:
    """Strict greater-than threshold breach check.

    85.01% breaches 85.0%; exactly 85.0% does not.
    """
    if occupancy_pct is None or threshold_pct is None:
        return False
    return float(occupancy_pct) > float(threshold_pct)


def count_admissions(
    df: pd.DataFrame,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    department: Optional[Union[str, int]] = None,
) -> int:
    """Count unique admissions within inclusive date boundaries."""
    if df.empty:
        return 0
    sub = df.copy()
    sub["admission_date_str"] = pd.to_datetime(sub["admission_date"]).dt.strftime("%Y-%m-%d")
    
    if start_date:
        sub = sub[sub["admission_date_str"] >= str(start_date)[:10]]
    if end_date:
        sub = sub[sub["admission_date_str"] <= str(end_date)[:10]]
    if department is not None:
        if "dept_name" in sub.columns and str(department) in sub["dept_name"].values:
            sub = sub[sub["dept_name"] == department]
        elif "dept_id" in sub.columns:
            sub = sub[sub["dept_id"] == department]

    if "encounter_id" in sub.columns:
        return int(sub["encounter_id"].nunique())
    return len(sub)


def count_discharges(
    df: pd.DataFrame,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    department: Optional[Union[str, int]] = None,
) -> int:
    """Count unique discharges (excludes OPEN encounters)."""
    if df.empty:
        return 0
    sub = df[df["encounter_status"] == "DISCHARGED"].copy()
    sub = sub[sub["discharge_date"].notna()]
    sub["discharge_date_str"] = pd.to_datetime(sub["discharge_date"]).dt.strftime("%Y-%m-%d")

    if start_date:
        sub = sub[sub["discharge_date_str"] >= str(start_date)[:10]]
    if end_date:
        sub = sub[sub["discharge_date_str"] <= str(end_date)[:10]]
    if department is not None:
        if "dept_name" in sub.columns and str(department) in sub["dept_name"].values:
            sub = sub[sub["dept_name"] == department]
        elif "dept_id" in sub.columns:
            sub = sub[sub["dept_id"] == department]

    if "encounter_id" in sub.columns:
        return int(sub["encounter_id"].nunique())
    return len(sub)


def average_length_of_stay(
    df: pd.DataFrame,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    department: Optional[Union[str, int]] = None,
) -> Optional[float]:
    """Calculate mean ALOS in days for DISCHARGED encounters."""
    if df.empty:
        return None
    sub = df[df["encounter_status"] == "DISCHARGED"].copy()
    sub = sub[sub["discharge_date"].notna() & sub["admission_date"].notna()]

    if start_date:
        s_str = pd.to_datetime(sub["discharge_date"]).dt.strftime("%Y-%m-%d")
        sub = sub[s_str >= str(start_date)[:10]]
    if end_date:
        e_str = pd.to_datetime(sub["discharge_date"]).dt.strftime("%Y-%m-%d")
        sub = sub[e_str <= str(end_date)[:10]]
    if department is not None:
        if "dept_name" in sub.columns and str(department) in sub["dept_name"].values:
            sub = sub[sub["dept_name"] == department]
        elif "dept_id" in sub.columns:
            sub = sub[sub["dept_id"] == department]

    if sub.empty:
        return None

    adm = pd.to_datetime(sub["admission_date"])
    dis = pd.to_datetime(sub["discharge_date"])
    los_days = (dis - adm).dt.days
    return float(los_days.mean())


def admissions_by_period(
    df: pd.DataFrame,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    department: Optional[Union[str, int]] = None,
    frequency: str = "D",
) -> pd.DataFrame:
    """Group admissions chronologically by period (Daily, Weekly, Monthly)."""
    if df.empty:
        return pd.DataFrame(columns=["period", "admissions"])
    sub = df.copy()
    sub["admission_dt"] = pd.to_datetime(sub["admission_date"])
    
    if start_date:
        sub = sub[sub["admission_dt"] >= pd.to_datetime(start_date)]
    if end_date:
        sub = sub[sub["admission_dt"] <= pd.to_datetime(end_date)]
    if department is not None:
        if "dept_name" in sub.columns and str(department) in sub["dept_name"].values:
            sub = sub[sub["dept_name"] == department]
        elif "dept_id" in sub.columns:
            sub = sub[sub["dept_id"] == department]

    if sub.empty:
        return pd.DataFrame(columns=["period", "admissions"])

    # Map legacy pandas 2 aliases like 'M' to pandas 3 'ME'
    freq_map = {"M": "ME", "Y": "YE", "Q": "QE"}
    resample_freq = freq_map.get(frequency, frequency)

    sub = sub.set_index("admission_dt")
    grouped = sub.resample(resample_freq)["encounter_id"].count().reset_index()
    grouped.columns = ["period", "admissions"]
    return grouped
