"""Database and source-data integrity tests for HRA-001.

These tests exercise the Step 10 SQLite deliverable immediately. Cleaning tests
use the documented Step 15 interface and are skipped until src/cleaning.py exists.
"""
from __future__ import annotations

import importlib.util
import sqlite3
from pathlib import Path

import pandas as pd
import pytest

from src.db import DEFAULT_DB_PATH, get_connection

ROOT = Path(__file__).resolve().parents[1]
EXPECTED_COUNTS = {
    "departments": 6,
    "utilization_categories": 7,
    "patient_encounters": 240,
    "daily_utilization": 12_775,
}
EXPECTED_COLUMNS = {
    "departments": [
        "dept_id", "dept_code", "dept_name", "department_level", "parent_dept_id",
        "department_group", "active_flag", "occupancy_warning_threshold_pct",
        "threshold_effective_from", "threshold_effective_to", "threshold_scope",
        "threshold_owner", "threshold_approval_status", "created_at",
    ],
    "utilization_categories": [
        "category_id", "category_code", "category_name", "category_group",
        "unit_of_measure", "active_flag", "description",
    ],
    "patient_encounters": [
        "encounter_id", "encounter_code", "dept_id", "admission_date",
        "discharge_date", "encounter_status", "data_source_label",
    ],
    "daily_utilization": [
        "utilization_id", "metric_date", "dept_id", "category_id",
        "available_amount", "used_amount", "source_batch_id",
    ],
}


@pytest.fixture(scope="module")
def conn():
    assert DEFAULT_DB_PATH.exists(), f"Expected database at {DEFAULT_DB_PATH}"
    connection = get_connection(DEFAULT_DB_PATH)
    try:
        yield connection
    finally:
        connection.close()


def test_database_loads_from_data_app_db(conn):
    assert conn.execute("SELECT 1").fetchone()[0] == 1
    names = {row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert set(EXPECTED_COUNTS).issubset(names)


@pytest.mark.parametrize("table, expected_rows", EXPECTED_COUNTS.items())
def test_planned_table_row_counts(conn, table, expected_rows):
    actual = conn.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
    assert actual == expected_rows


@pytest.mark.parametrize("table, expected_columns", EXPECTED_COLUMNS.items())
def test_exact_table_columns(conn, table, expected_columns):
    actual = [row[1] for row in conn.execute(f'PRAGMA table_info("{table}")')]
    assert actual == expected_columns


def test_declared_sqlite_types_match_schema(conn):
    expected_types = {
        "departments": ["INTEGER", "TEXT", "TEXT", "TEXT", "INTEGER", "TEXT", "INTEGER", "REAL", "TEXT", "TEXT", "TEXT", "TEXT", "TEXT", "TEXT"],
        "utilization_categories": ["INTEGER", "TEXT", "TEXT", "TEXT", "TEXT", "INTEGER", "TEXT"],
        "patient_encounters": ["INTEGER", "TEXT", "INTEGER", "TEXT", "TEXT", "TEXT", "TEXT"],
        "daily_utilization": ["INTEGER", "TEXT", "INTEGER", "INTEGER", "REAL", "REAL", "TEXT"],
    }
    for table, types in expected_types.items():
        actual = [row[2].upper() for row in conn.execute(f'PRAGMA table_info("{table}")')]
        assert actual == types


def test_joined_analysis_view_has_1825_rows_and_40_columns(conn):
    cur = conn.execute("SELECT * FROM vw_department_daily_analysis LIMIT 0")
    assert len(cur.description) == 40
    assert conn.execute("SELECT COUNT(*) FROM vw_department_daily_analysis").fetchone()[0] == 1825


@pytest.mark.parametrize("table, primary_key", [
    ("departments", "dept_id"),
    ("utilization_categories", "category_id"),
    ("patient_encounters", "encounter_id"),
    ("daily_utilization", "utilization_id"),
])
def test_primary_keys_are_unique_and_non_null(conn, table, primary_key):
    total, distinct_count, null_count = conn.execute(
        f'SELECT COUNT(*), COUNT(DISTINCT "{primary_key}"), '
        f'SUM(CASE WHEN "{primary_key}" IS NULL THEN 1 ELSE 0 END) FROM "{table}"'
    ).fetchone()
    assert total == distinct_count
    assert null_count == 0


def test_all_foreign_keys_are_valid(conn):
    violations = conn.execute("PRAGMA foreign_key_check").fetchall()
    assert violations == []


def test_every_application_connection_enables_foreign_keys(tmp_path):
    db_copy = tmp_path / "app_fk_test.db"
    source = sqlite3.connect(DEFAULT_DB_PATH)
    target = sqlite3.connect(db_copy)
    try:
        source.backup(target)
    finally:
        source.close()
        target.close()
    test_conn = get_connection(db_copy)
    try:
        assert test_conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        category_id = test_conn.execute("SELECT category_id FROM utilization_categories LIMIT 1").fetchone()[0]
        with pytest.raises(sqlite3.IntegrityError):
            test_conn.execute(
                "INSERT INTO daily_utilization "
                "(metric_date, dept_id, category_id, available_amount, used_amount, source_batch_id) "
                "VALUES ('2026-01-01', 999999, ?, 10, 5, 'TEST-FK')",
                (category_id,),
            )
        test_conn.rollback()
    finally:
        test_conn.close()


def test_daily_composite_business_key_is_unique(conn):
    total, unique_keys = conn.execute(
        "SELECT COUNT(*), COUNT(DISTINCT metric_date || '|' || dept_id || '|' || category_id) "
        "FROM daily_utilization"
    ).fetchone()
    assert total == unique_keys


def test_required_values_and_numeric_ranges_are_valid(conn):
    assert conn.execute("SELECT COUNT(*) FROM daily_utilization WHERE metric_date IS NULL OR dept_id IS NULL OR category_id IS NULL OR available_amount IS NULL OR used_amount IS NULL OR source_batch_id IS NULL").fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM daily_utilization WHERE available_amount < 0 OR used_amount < 0").fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM departments WHERE occupancy_warning_threshold_pct NOT BETWEEN 0 AND 100").fetchone()[0] == 0


def test_encounter_dates_and_status_invariants_are_valid(conn):
    assert conn.execute("SELECT COUNT(*) FROM patient_encounters WHERE date(admission_date) IS NULL OR date(admission_date) <> admission_date").fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM patient_encounters WHERE discharge_date < admission_date").fetchone()[0] == 0
    assert conn.execute("SELECT COUNT(*) FROM patient_encounters WHERE (encounter_status='OPEN' AND discharge_date IS NOT NULL) OR (encounter_status='DISCHARGED' AND discharge_date IS NULL)").fetchone()[0] == 0


def test_category_groups_and_units_are_valid(conn):
    invalid = conn.execute(
        "SELECT COUNT(*) FROM utilization_categories "
        "WHERE category_group NOT IN ('BED','STAFF','RESOURCE') "
        "OR unit_of_measure NOT IN ('BED_DAY','HOURS')"
    ).fetchone()[0]
    assert invalid == 0


def test_cleaned_database_contains_no_duplicate_daily_keys_or_missing_used_amounts(conn):
    duplicates = conn.execute(
        "SELECT COUNT(*) FROM (SELECT metric_date, dept_id, category_id, COUNT(*) c "
        "FROM daily_utilization GROUP BY metric_date, dept_id, category_id HAVING c > 1)"
    ).fetchone()[0]
    missing = conn.execute("SELECT COUNT(*) FROM daily_utilization WHERE used_amount IS NULL").fetchone()[0]
    assert duplicates == 0
    assert missing == 0


def test_cleaning_contract_repairs_missing_values_and_duplicates():
    """Step 15 contract: cleaner returns (clean_frame, issue_summary)."""
    if importlib.util.find_spec("src.cleaning") is None:
        pytest.skip("src.cleaning is scheduled for Step 15; test contract is defined now")
    from src.cleaning import clean_daily_utilization

    raw = pd.DataFrame([
        {"utilization_id": 1, "metric_date": "2026-01-01", "dept_id": 2, "category_id": 2, "available_amount": 100.0, "used_amount": None, "source_batch_id": "RAW"},
        {"utilization_id": 1, "metric_date": "2026-01-01", "dept_id": 2, "category_id": 2, "available_amount": 100.0, "used_amount": None, "source_batch_id": "RAW"},
        {"utilization_id": 2, "metric_date": "2026-01-02", "dept_id": 2, "category_id": 2, "available_amount": 100.0, "used_amount": 50.0, "source_batch_id": "RAW"},
        {"utilization_id": 3, "metric_date": "2026-01-03", "dept_id": 2, "category_id": 2, "available_amount": 100.0, "used_amount": 190.0, "source_batch_id": "RAW"},
    ])
    cleaned, report = clean_daily_utilization(raw)
    assert not cleaned.duplicated(["metric_date", "dept_id", "category_id"]).any()
    assert cleaned["used_amount"].notna().all()
    assert report["duplicates_removed"] >= 1
    assert report["missing_values_repaired"] >= 1
    assert report["outliers_flagged"] >= 1
