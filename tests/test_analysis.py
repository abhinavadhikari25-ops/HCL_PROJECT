"""Analytical calculation contract tests for implementation in Step 15.

Expected module: src/analysis.py. Missing module causes a clear pytest skip until
Step 15, not a broken collection. All expected formulas use tiny deterministic data.
"""
from __future__ import annotations

import importlib.util

import numpy as np
import pandas as pd
import pytest

analysis_spec = importlib.util.find_spec("src.analysis")
if analysis_spec is None:
    pytest.skip("src.analysis is scheduled for Step 15; analytical API contract is defined now", allow_module_level=True)

from src import analysis


@pytest.fixture
def encounters():
    return pd.DataFrame([
        {"encounter_id": 1, "dept_name": "General Medicine", "admission_date": "2026-01-01", "discharge_date": "2026-01-03", "encounter_status": "DISCHARGED"},
        {"encounter_id": 2, "dept_name": "General Medicine", "admission_date": "2026-01-02", "discharge_date": "2026-01-06", "encounter_status": "DISCHARGED"},
        {"encounter_id": 3, "dept_name": "Paediatrics", "admission_date": "2026-01-03", "discharge_date": None, "encounter_status": "OPEN"},
        {"encounter_id": 4, "dept_name": "Paediatrics", "admission_date": "2026-01-10", "discharge_date": "2026-01-12", "encounter_status": "DISCHARGED"},
    ])


def test_bed_occupancy_weighted_formula():
    assert analysis.bed_occupancy_rate(occupied_bed_days=675, available_bed_days=900) == pytest.approx(75.0)


def test_occupancy_zero_denominator_returns_not_available():
    assert analysis.bed_occupancy_rate(10, 0) is None


def test_available_beds_formula():
    assert analysis.available_beds(usable_capacity=30, occupied_beds=24) == 6


def test_staff_utilization_formula():
    assert analysis.staff_utilization_rate(used_hours=72, available_hours=90) == pytest.approx(80.0)


def test_resource_utilization_formula():
    assert analysis.resource_utilization_rate(used_amount=30, available_amount=50) == pytest.approx(60.0)


def test_zero_available_hours_returns_not_available():
    assert analysis.staff_utilization_rate(8, 0) is None


def test_admissions_count_inclusive_boundaries_and_department(encounters):
    assert analysis.count_admissions(encounters, "2026-01-01", "2026-01-03") == 3
    assert analysis.count_admissions(encounters, "2026-01-01", "2026-01-06", department="General Medicine") == 2


def test_discharges_count_by_discharge_date(encounters):
    assert analysis.count_discharges(encounters, "2026-01-03", "2026-01-12") == 3


def test_average_length_of_stay_excludes_open_encounters(encounters):
    # Discharged between Jan 1 and Jan 6: 2-day and 4-day stays -> 3 days.
    assert analysis.average_length_of_stay(encounters, "2026-01-01", "2026-01-06", department="General Medicine") == pytest.approx(3.0)


def test_admission_grouping_daily_weekly_monthly_reconciles(encounters):
    for frequency in ("D", "W", "M"):
        grouped = analysis.admissions_by_period(encounters, "2026-01-01", "2026-01-31", frequency=frequency)
        assert int(grouped["admissions"].sum()) == 4


def test_descriptive_statistics_known_values():
    result = analysis.descriptive_statistics(pd.Series([1, 2, 3, 4, 5], dtype=float))
    assert result["count"] == 5
    assert result["mean"] == pytest.approx(3.0)
    assert result["median"] == pytest.approx(3.0)
    assert result["std"] == pytest.approx(np.std([1, 2, 3, 4, 5], ddof=1))


def test_pearson_correlation_known_values():
    assert analysis.pearson_correlation([1, 2, 3], [2, 4, 6]) == pytest.approx(1.0)


def test_iqr_outlier_detection_flags_extreme_value():
    flagged = analysis.detect_iqr_outliers(pd.Series([1, 2, 2, 3, 100], dtype=float))
    assert 100 in list(flagged)


def test_threshold_rule_is_strictly_greater_than():
    assert analysis.is_threshold_breach(85.01, 85.0) is True
    assert analysis.is_threshold_breach(85.0, 85.0) is False
    assert analysis.is_threshold_breach(84.99, 85.0) is False
