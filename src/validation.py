"""Database schema and input validation utilities for HRA-001."""
from __future__ import annotations

import re
import sqlite3
from datetime import date, datetime
from typing import Any, Dict, List, Optional, Tuple

EXPECTED_COUNTS = {
    "departments": 6,
    "utilization_categories": 7,
    "patient_encounters": 240,
    "daily_utilization": 12775,
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


class ValidationError(Exception):
    """Custom validation exception with clear non-sensitive diagnostics."""
    pass


def validate_date_string(val: Optional[str]) -> Optional[str]:
    """Validate ISO date string format (YYYY-MM-DD)."""
    if val is None:
        return None
    val = str(val).strip()
    if not val:
        return None
    try:
        parsed = datetime.strptime(val, "%Y-%m-%d").date()
        return parsed.isoformat()
    except ValueError:
        raise ValidationError(f"Invalid date format '{val}'. Expected YYYY-MM-DD.")


def validate_date_range(start_date: Optional[str], end_date: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """Validate inclusive date range."""
    s = validate_date_string(start_date)
    e = validate_date_string(end_date)
    if s and e and s > e:
        raise ValidationError(f"Start date '{s}' cannot be after end date '{e}'.")
    return s, e


def validate_database_schema(conn: sqlite3.Connection) -> Dict[str, Any]:
    """Validate SQLite database schema against expected tables and columns."""
    existing_tables = {
        row[0]
        for row in conn.execute("SELECT name FROM sqlite_master WHERE type IN ('table','view')").fetchall()
    }
    
    missing_tables = [t for t in EXPECTED_COLUMNS if t not in existing_tables]
    if missing_tables:
        raise ValidationError(f"Database is missing required tables: {', '.join(missing_tables)}")

    if "vw_department_daily_analysis" not in existing_tables:
        raise ValidationError("Database is missing required analysis view: vw_department_daily_analysis")

    results = {}
    for table, expected_cols in EXPECTED_COLUMNS.items():
        actual_cols = [r[1] for r in conn.execute(f'PRAGMA table_info("{table}")').fetchall()]
        if actual_cols != expected_cols:
            raise ValidationError(
                f"Column mismatch in table '{table}'. Expected {expected_cols}, got {actual_cols}"
            )
        results[table] = actual_cols

    view_cols = [r[1] for r in conn.execute('PRAGMA table_info("vw_department_daily_analysis")').fetchall()]
    if len(view_cols) != 40:
        raise ValidationError(
            f"vw_department_daily_analysis must have 40 columns, found {len(view_cols)}"
        )
    results["vw_department_daily_analysis"] = view_cols
    return results


def validate_database_integrity(conn: sqlite3.Connection) -> bool:
    """Verify foreign key integrity and required row counts."""
    fk_issues = conn.execute("PRAGMA foreign_key_check").fetchall()
    if fk_issues:
        raise ValidationError(f"Foreign key integrity check failed: {fk_issues}")

    for table, expected_count in EXPECTED_COUNTS.items():
        count = conn.execute(f'SELECT COUNT(*) FROM "{table}"').fetchone()[0]
        if count != expected_count:
            raise ValidationError(
                f"Table '{table}' has {count} rows; expected exactly {expected_count}."
            )

    view_count = conn.execute("SELECT COUNT(*) FROM vw_department_daily_analysis").fetchone()[0]
    if view_count != 1825:
        raise ValidationError(
            f"View 'vw_department_daily_analysis' has {view_count} rows; expected 1825."
        )

    return True
