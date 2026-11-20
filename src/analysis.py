"""Analytical functions facade for HRA-001.

Re-exports metrics and statistical functions required by the test contract.
"""
from __future__ import annotations

from src.metrics import (
    admissions_by_period,
    available_beds,
    average_length_of_stay,
    bed_occupancy_rate,
    count_admissions,
    count_discharges,
    is_threshold_breach,
    resource_utilization_rate,
    staff_utilization_rate,
)
from src.statistics import (
    descriptive_statistics,
    detect_iqr_outliers,
    pearson_correlation,
)

__all__ = [
    "bed_occupancy_rate",
    "available_beds",
    "staff_utilization_rate",
    "resource_utilization_rate",
    "is_threshold_breach",
    "count_admissions",
    "count_discharges",
    "average_length_of_stay",
    "admissions_by_period",
    "descriptive_statistics",
    "pearson_correlation",
    "detect_iqr_outliers",
]
