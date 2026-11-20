#!/usr/bin/env python3
"""Generate the HRA-001 synthetic dataset exactly to the Step 8 SQLite design.

Run from the project repository root:
    python src/generate_data.py

The Excel workbook and CSV files intentionally contain documented raw-data
quality issues (missing values, duplicate rows, and extreme outliers). The
SQLite database contains the cleaned, de-duplicated, schema-valid records.

Excel export uses the environment-provided `artifact_tool` library as required
by the project authoring environment. Standard-library modules handle data,
CSV, SQLite, reporting, and deterministic random generation.
"""
from __future__ import annotations

import csv
import math
import random
import sqlite3
import statistics
import sys
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any

SEED = 42
START_DATE = date(2025, 11, 3)
END_DATE = date(2026, 11, 2)
BATCH_ID = "HRA001-SEED42-2025-2026"
PROJECT_NAME = "Hospital Resource Utilization Analysis"

ROOT = Path(__file__).resolve().parents[1]
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
from db import get_connection

DATA_DIR = ROOT / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Exact Step 8 schema: table names, columns, SQLite types, PK/FK and constraints
# ---------------------------------------------------------------------------
DDL_STATEMENTS = [
    """CREATE TABLE departments (
      dept_id INTEGER PRIMARY KEY,
      dept_code TEXT NOT NULL UNIQUE,
      dept_name TEXT NOT NULL UNIQUE,
      department_level TEXT NOT NULL
        CHECK (department_level IN ('HOSPITAL','DEPARTMENT')),
      parent_dept_id INTEGER NULL,
      department_group TEXT NOT NULL,
      active_flag INTEGER NOT NULL DEFAULT 1 CHECK (active_flag IN (0,1)),
      occupancy_warning_threshold_pct REAL NOT NULL DEFAULT 85.0
        CHECK (occupancy_warning_threshold_pct BETWEEN 0 AND 100),
      threshold_effective_from TEXT NOT NULL
        CHECK (date(threshold_effective_from) IS NOT NULL
               AND date(threshold_effective_from) = threshold_effective_from),
      threshold_effective_to TEXT NULL
        CHECK (threshold_effective_to IS NULL OR
               (date(threshold_effective_to) IS NOT NULL
                AND date(threshold_effective_to) = threshold_effective_to)),
      threshold_scope TEXT NOT NULL
        CHECK (threshold_scope IN ('HOSPITAL','DEPARTMENT')),
      threshold_owner TEXT NOT NULL,
      threshold_approval_status TEXT NOT NULL
        CHECK (threshold_approval_status IN ('ASSUMED','PENDING','APPROVED','REJECTED')),
      created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
      FOREIGN KEY (parent_dept_id) REFERENCES departments(dept_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
      CHECK (dept_id <> parent_dept_id),
      CHECK ((department_level='HOSPITAL' AND parent_dept_id IS NULL
              AND threshold_scope='HOSPITAL')
          OR (department_level='DEPARTMENT' AND parent_dept_id IS NOT NULL
              AND threshold_scope='DEPARTMENT')),
      CHECK (threshold_effective_to IS NULL OR
             threshold_effective_to >= threshold_effective_from)
    );""",
    """CREATE TABLE utilization_categories (
      category_id INTEGER PRIMARY KEY,
      category_code TEXT NOT NULL UNIQUE,
      category_name TEXT NOT NULL,
      category_group TEXT NOT NULL
        CHECK (category_group IN ('BED','STAFF','RESOURCE')),
      unit_of_measure TEXT NOT NULL
        CHECK (unit_of_measure IN ('BED_DAY','HOURS')),
      active_flag INTEGER NOT NULL DEFAULT 1 CHECK (active_flag IN (0,1)),
      description TEXT NULL,
      CHECK ((category_code='BED_CAPACITY' AND category_group='BED'
              AND unit_of_measure='BED_DAY')
          OR (category_code<>'BED_CAPACITY'
              AND category_group IN ('STAFF','RESOURCE')
              AND unit_of_measure='HOURS'))
    );""",
    """CREATE TABLE patient_encounters (
      encounter_id INTEGER PRIMARY KEY,
      encounter_code TEXT NOT NULL UNIQUE,
      dept_id INTEGER NOT NULL,
      admission_date TEXT NOT NULL
        CHECK (date(admission_date) IS NOT NULL
               AND date(admission_date) = admission_date),
      discharge_date TEXT NULL
        CHECK (discharge_date IS NULL OR
               (date(discharge_date) IS NOT NULL
                AND date(discharge_date) = discharge_date)),
      encounter_status TEXT NOT NULL
        CHECK (encounter_status IN ('OPEN','DISCHARGED')),
      data_source_label TEXT NOT NULL DEFAULT 'SYNTHETIC'
        CHECK (data_source_label = 'SYNTHETIC'),
      FOREIGN KEY (dept_id) REFERENCES departments(dept_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
      CHECK (discharge_date IS NULL OR discharge_date >= admission_date),
      CHECK ((encounter_status='OPEN' AND discharge_date IS NULL)
          OR (encounter_status='DISCHARGED' AND discharge_date IS NOT NULL))
    );""",
    """CREATE TABLE daily_utilization (
      utilization_id INTEGER PRIMARY KEY,
      metric_date TEXT NOT NULL
        CHECK (date(metric_date) IS NOT NULL AND date(metric_date) = metric_date),
      dept_id INTEGER NOT NULL,
      category_id INTEGER NOT NULL,
      available_amount REAL NOT NULL CHECK (available_amount >= 0),
      used_amount REAL NOT NULL CHECK (used_amount >= 0),
      source_batch_id TEXT NOT NULL,
      FOREIGN KEY (dept_id) REFERENCES departments(dept_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
      FOREIGN KEY (category_id) REFERENCES utilization_categories(category_id)
        ON UPDATE CASCADE ON DELETE RESTRICT,
      UNIQUE (metric_date, dept_id, category_id)
    );""",
]
INDEX_AND_TRIGGER_DDL = [
    "CREATE UNIQUE INDEX ux_single_hospital_root ON departments(department_level) WHERE department_level='HOSPITAL';",
    "CREATE INDEX idx_encounters_admission ON patient_encounters(admission_date, dept_id);",
    "CREATE INDEX idx_encounters_discharge ON patient_encounters(discharge_date, dept_id);",
    "CREATE INDEX idx_daily_date_dept ON daily_utilization(metric_date, dept_id);",
    "CREATE INDEX idx_daily_category ON daily_utilization(category_id, metric_date);",
    """CREATE TRIGGER trg_encounter_department_only
    BEFORE INSERT ON patient_encounters
    FOR EACH ROW
    WHEN (SELECT department_level FROM departments WHERE dept_id=NEW.dept_id) <> 'DEPARTMENT'
    BEGIN
      SELECT RAISE(ABORT, 'Encounter must reference a department-level row');
    END;""",
    """CREATE TRIGGER trg_daily_department_only
    BEFORE INSERT ON daily_utilization
    FOR EACH ROW
    WHEN (SELECT department_level FROM departments WHERE dept_id=NEW.dept_id) <> 'DEPARTMENT'
    BEGIN
      SELECT RAISE(ABORT, 'Utilisation must reference a department-level row');
    END;""",
]
VIEW_SQL = r"""CREATE VIEW vw_department_daily_analysis AS
WITH category_pivot AS (
  SELECT
    du.metric_date,
    du.dept_id,
    MAX(CASE WHEN uc.category_code='BED_CAPACITY' THEN du.available_amount END)
      AS usable_bed_capacity,
    MAX(CASE WHEN uc.category_code='BED_CAPACITY' THEN du.used_amount END)
      AS occupied_beds,
    MAX(CASE WHEN uc.category_code='DOCTOR' THEN du.available_amount END)
      AS doctor_available_hours,
    MAX(CASE WHEN uc.category_code='DOCTOR' THEN du.used_amount END)
      AS doctor_used_hours,
    MAX(CASE WHEN uc.category_code='NURSE' THEN du.available_amount END)
      AS nurse_available_hours,
    MAX(CASE WHEN uc.category_code='NURSE' THEN du.used_amount END)
      AS nurse_used_hours,
    MAX(CASE WHEN uc.category_code='TECHNICIAN' THEN du.available_amount END)
      AS technician_available_hours,
    MAX(CASE WHEN uc.category_code='TECHNICIAN' THEN du.used_amount END)
      AS technician_used_hours,
    MAX(CASE WHEN uc.category_code='ICU_VENTILATOR' THEN du.available_amount END)
      AS icu_ventilator_available_hours,
    MAX(CASE WHEN uc.category_code='ICU_VENTILATOR' THEN du.used_amount END)
      AS icu_ventilator_used_hours,
    MAX(CASE WHEN uc.category_code='OPERATING_ROOM' THEN du.available_amount END)
      AS operating_room_available_hours,
    MAX(CASE WHEN uc.category_code='OPERATING_ROOM' THEN du.used_amount END)
      AS operating_room_used_hours,
    MAX(CASE WHEN uc.category_code='DIAGNOSTIC_IMAGING' THEN du.available_amount END)
      AS diagnostic_imaging_available_hours,
    MAX(CASE WHEN uc.category_code='DIAGNOSTIC_IMAGING' THEN du.used_amount END)
      AS diagnostic_imaging_used_hours
  FROM daily_utilization du
  JOIN utilization_categories uc ON uc.category_id = du.category_id
  GROUP BY du.metric_date, du.dept_id
),
encounter_day AS (
  SELECT
    cp.metric_date,
    cp.dept_id,
    SUM(CASE WHEN e.admission_date = cp.metric_date THEN 1 ELSE 0 END) AS admissions,
    SUM(CASE WHEN e.discharge_date = cp.metric_date THEN 1 ELSE 0 END) AS discharges,
    SUM(CASE WHEN e.discharge_date = cp.metric_date THEN 1 ELSE 0 END)
      AS discharged_encounter_count,
    AVG(CASE WHEN e.discharge_date = cp.metric_date
             THEN julianday(e.discharge_date) - julianday(e.admission_date) END)
      AS avg_los_days,
    SUM(CASE WHEN e.admission_date <= cp.metric_date
              AND (e.discharge_date IS NULL OR e.discharge_date > cp.metric_date)
             THEN 1 ELSE 0 END) AS open_encounter_count
  FROM category_pivot cp
  LEFT JOIN patient_encounters e ON e.dept_id = cp.dept_id
  GROUP BY cp.metric_date, cp.dept_id
)
SELECT
  cp.metric_date,
  CAST(strftime('%Y', cp.metric_date) AS INTEGER) AS calendar_year,
  CAST(strftime('%m', cp.metric_date) AS INTEGER) AS calendar_month,
  strftime('%W', cp.metric_date) AS calendar_week,
  strftime('%w', cp.metric_date) AS day_of_week,
  d.dept_id,
  d.dept_code,
  d.dept_name,
  d.department_group,
  cp.usable_bed_capacity,
  cp.occupied_beds,
  cp.usable_bed_capacity - cp.occupied_beds AS available_beds,
  CASE WHEN cp.usable_bed_capacity > 0
       THEN 100.0 * cp.occupied_beds / cp.usable_bed_capacity END
       AS occupancy_rate_pct,
  CASE
    WHEN cp.metric_date >= d.threshold_effective_from
     AND (d.threshold_effective_to IS NULL OR cp.metric_date <= d.threshold_effective_to)
      THEN d.occupancy_warning_threshold_pct
    WHEN cp.metric_date >= h.threshold_effective_from
     AND (h.threshold_effective_to IS NULL OR cp.metric_date <= h.threshold_effective_to)
      THEN h.occupancy_warning_threshold_pct
  END AS warning_threshold_pct,
  CASE
    WHEN cp.usable_bed_capacity > 0
     AND CASE
       WHEN cp.metric_date >= d.threshold_effective_from
        AND (d.threshold_effective_to IS NULL OR cp.metric_date <= d.threshold_effective_to)
         THEN 100.0 * cp.occupied_beds / cp.usable_bed_capacity >
              d.occupancy_warning_threshold_pct
       WHEN cp.metric_date >= h.threshold_effective_from
        AND (h.threshold_effective_to IS NULL OR cp.metric_date <= h.threshold_effective_to)
         THEN 100.0 * cp.occupied_beds / cp.usable_bed_capacity >
              h.occupancy_warning_threshold_pct
       ELSE 0
     END
      THEN 1 ELSE 0
  END AS warning_breach_flag,
  ed.admissions,
  ed.discharges,
  ed.discharged_encounter_count,
  ed.avg_los_days,
  ed.open_encounter_count,
  cp.doctor_available_hours,
  cp.doctor_used_hours,
  CASE WHEN cp.doctor_available_hours > 0
       THEN 100.0 * cp.doctor_used_hours / cp.doctor_available_hours END
       AS doctor_utilization_pct,
  cp.nurse_available_hours,
  cp.nurse_used_hours,
  CASE WHEN cp.nurse_available_hours > 0
       THEN 100.0 * cp.nurse_used_hours / cp.nurse_available_hours END
       AS nurse_utilization_pct,
  cp.technician_available_hours,
  cp.technician_used_hours,
  CASE WHEN cp.technician_available_hours > 0
       THEN 100.0 * cp.technician_used_hours / cp.technician_available_hours END
       AS technician_utilization_pct,
  cp.icu_ventilator_available_hours,
  cp.icu_ventilator_used_hours,
  CASE WHEN cp.icu_ventilator_available_hours > 0
       THEN 100.0 * cp.icu_ventilator_used_hours / cp.icu_ventilator_available_hours END
       AS icu_ventilator_utilization_pct,
  cp.operating_room_available_hours,
  cp.operating_room_used_hours,
  CASE WHEN cp.operating_room_available_hours > 0
       THEN 100.0 * cp.operating_room_used_hours / cp.operating_room_available_hours END
       AS operating_room_utilization_pct,
  cp.diagnostic_imaging_available_hours,
  cp.diagnostic_imaging_used_hours,
  CASE WHEN cp.diagnostic_imaging_available_hours > 0
       THEN 100.0 * cp.diagnostic_imaging_used_hours / cp.diagnostic_imaging_available_hours END
       AS diagnostic_imaging_utilization_pct,
  CASE WHEN cp.doctor_available_hours IS NOT NULL
         AND cp.nurse_available_hours IS NOT NULL
         AND cp.technician_available_hours IS NOT NULL
       THEN cp.doctor_available_hours + cp.nurse_available_hours +
            cp.technician_available_hours END AS total_staff_available_hours,
  CASE WHEN cp.doctor_used_hours IS NOT NULL
         AND cp.nurse_used_hours IS NOT NULL
         AND cp.technician_used_hours IS NOT NULL
       THEN cp.doctor_used_hours + cp.nurse_used_hours +
            cp.technician_used_hours END AS total_staff_used_hours
FROM category_pivot cp
JOIN departments d ON d.dept_id = cp.dept_id
LEFT JOIN departments h ON h.department_level = 'HOSPITAL'
LEFT JOIN encounter_day ed
  ON ed.metric_date = cp.metric_date
 AND ed.dept_id = cp.dept_id
WHERE d.department_level = 'DEPARTMENT';"""

TABLE_COLUMNS = {
    "departments": ["dept_id", "dept_code", "dept_name", "department_level", "parent_dept_id",
                    "department_group", "active_flag", "occupancy_warning_threshold_pct",
                    "threshold_effective_from", "threshold_effective_to", "threshold_scope",
                    "threshold_owner", "threshold_approval_status", "created_at"],
    "utilization_categories": ["category_id", "category_code", "category_name", "category_group",
                                "unit_of_measure", "active_flag", "description"],
    "patient_encounters": ["encounter_id", "encounter_code", "dept_id", "admission_date",
                            "discharge_date", "encounter_status", "data_source_label"],
    "daily_utilization": ["utilization_id", "metric_date", "dept_id", "category_id",
                          "available_amount", "used_amount", "source_batch_id"],
}
EXPECTED_TYPES_AND_PK = {
    "departments": {"dept_id": ("INTEGER", 1), "dept_code": ("TEXT", 0),
        "dept_name": ("TEXT", 0), "department_level": ("TEXT", 0),
        "parent_dept_id": ("INTEGER", 0), "department_group": ("TEXT", 0),
        "active_flag": ("INTEGER", 0), "occupancy_warning_threshold_pct": ("REAL", 0),
        "threshold_effective_from": ("TEXT", 0), "threshold_effective_to": ("TEXT", 0),
        "threshold_scope": ("TEXT", 0), "threshold_owner": ("TEXT", 0),
        "threshold_approval_status": ("TEXT", 0), "created_at": ("TEXT", 0)},
    "utilization_categories": {"category_id": ("INTEGER", 1), "category_code": ("TEXT", 0),
        "category_name": ("TEXT", 0), "category_group": ("TEXT", 0),
        "unit_of_measure": ("TEXT", 0), "active_flag": ("INTEGER", 0),
        "description": ("TEXT", 0)},
    "patient_encounters": {"encounter_id": ("INTEGER", 1), "encounter_code": ("TEXT", 0),
        "dept_id": ("INTEGER", 0), "admission_date": ("TEXT", 0),
        "discharge_date": ("TEXT", 0), "encounter_status": ("TEXT", 0),
        "data_source_label": ("TEXT", 0)},
    "daily_utilization": {"utilization_id": ("INTEGER", 1), "metric_date": ("TEXT", 0),
        "dept_id": ("INTEGER", 0), "category_id": ("INTEGER", 0),
        "available_amount": ("REAL", 0), "used_amount": ("REAL", 0),
        "source_batch_id": ("TEXT", 0)},
}
EXPECTED_FOREIGN_KEYS = {
    "departments": {("parent_dept_id", "departments", "dept_id")},
    "utilization_categories": set(),
    "patient_encounters": {("dept_id", "departments", "dept_id")},
    "daily_utilization": {("dept_id", "departments", "dept_id"),
                          ("category_id", "utilization_categories", "category_id")},
}

DEPARTMENTS_SPEC = [
    # id, code, name, level, parent, group, threshold pct, owner, approval
    (1, "HRA-HOSP", "Aarohan Multispecialty Hospital - Ghaziabad", "HOSPITAL", None,
     "Facility", 85.0, "Ananya Verma - Hospital Operations Lead", "ASSUMED"),
    (2, "GEN-MED", "General Medicine", "DEPARTMENT", 1, "Medicine", 85.0,
     "Raghav Sharma - General Medicine Head", "ASSUMED"),
    (3, "GEN-SUR", "General Surgery", "DEPARTMENT", 1, "Surgery", 85.0,
     "Meera Nair - General Surgery Head", "ASSUMED"),
    (4, "ORTHO", "Orthopaedics", "DEPARTMENT", 1, "Orthopaedics", 85.0,
     "Kabir Malhotra - Orthopaedics Head", "ASSUMED"),
    (5, "PEDIA", "Paediatrics", "DEPARTMENT", 1, "Paediatrics", 85.0,
     "Ishita Rao - Paediatrics Head", "ASSUMED"),
    (6, "OBGYN", "Obstetrics and Gynaecology", "DEPARTMENT", 1,
     "Obstetrics & Gynaecology", 85.0, "Aarav Kapoor - OBGYN Head", "ASSUMED"),
]
CATEGORY_SPEC = [
    (1, "BED_CAPACITY", "Usable bed capacity", "BED", "BED_DAY", 1,
     "Daily usable beds and occupied beds for each department."),
    (2, "DOCTOR", "Doctors", "STAFF", "HOURS", 1,
     "Available and assigned doctor hours per department/day."),
    (3, "NURSE", "Nurses", "STAFF", "HOURS", 1,
     "Available and assigned nursing hours per department/day."),
    (4, "TECHNICIAN", "Technicians", "STAFF", "HOURS", 1,
     "Available and assigned technician hours per department/day."),
    (5, "ICU_VENTILATOR", "ICU ventilators", "RESOURCE", "HOURS", 1,
     "Available and used ventilator-hours per department/day."),
    (6, "OPERATING_ROOM", "Operating rooms", "RESOURCE", "HOURS", 1,
     "Available and used operating-room hours per department/day."),
    (7, "DIAGNOSTIC_IMAGING", "Diagnostic imaging", "RESOURCE", "HOURS", 1,
     "Available and used imaging hours per department/day."),
]

BED_CAPACITY = {2: 80, 3: 60, 4: 45, 5: 35, 6: 30}
STAFF_CAPACITY = {
    2: {"DOCTOR": 72.0, "NURSE": 144.0, "TECHNICIAN": 32.0},
    3: {"DOCTOR": 64.0, "NURSE": 120.0, "TECHNICIAN": 32.0},
    4: {"DOCTOR": 48.0, "NURSE": 88.0, "TECHNICIAN": 24.0},
    5: {"DOCTOR": 40.0, "NURSE": 72.0, "TECHNICIAN": 24.0},
    6: {"DOCTOR": 40.0, "NURSE": 72.0, "TECHNICIAN": 24.0},
}
RESOURCE_CAPACITY = {
    2: {"ICU_VENTILATOR": 48.0, "OPERATING_ROOM": 0.0, "DIAGNOSTIC_IMAGING": 16.0},
    3: {"ICU_VENTILATOR": 24.0, "OPERATING_ROOM": 16.0, "DIAGNOSTIC_IMAGING": 12.0},
    4: {"ICU_VENTILATOR": 12.0, "OPERATING_ROOM": 8.0, "DIAGNOSTIC_IMAGING": 10.0},
    5: {"ICU_VENTILATOR": 12.0, "OPERATING_ROOM": 4.0, "DIAGNOSTIC_IMAGING": 8.0},
    6: {"ICU_VENTILATOR": 12.0, "OPERATING_ROOM": 8.0, "DIAGNOSTIC_IMAGING": 8.0},
}
CATEGORY_ID = {row[1]: row[0] for row in CATEGORY_SPEC}


def iso(d: date) -> str:
    return d.isoformat()


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def round_hours(value: float) -> float:
    return round(max(0.0, value), 2)


def make_departments() -> list[dict[str, Any]]:
    now = "2025-01-01 00:00:00"
    rows = []
    for (dept_id, code, name, level, parent, group, threshold, owner, approval) in DEPARTMENTS_SPEC:
        rows.append({
            "dept_id": dept_id,
            "dept_code": code,
            "dept_name": name,
            "department_level": level,
            "parent_dept_id": parent,
            "department_group": group,
            "active_flag": 1,
            "occupancy_warning_threshold_pct": threshold,
            "threshold_effective_from": iso(START_DATE),
            "threshold_effective_to": None,
            "threshold_scope": level,
            "threshold_owner": owner,
            "threshold_approval_status": approval,
            "created_at": now,
        })
    return rows


def make_categories() -> list[dict[str, Any]]:
    return [dict(zip(TABLE_COLUMNS["utilization_categories"], row)) for row in CATEGORY_SPEC]


def month_weighted_date(rng: random.Random, dept_id: int) -> date:
    """Select a date with explicit department/season/week patterns."""
    days = (END_DATE - START_DATE).days + 1
    candidates = [START_DATE + timedelta(days=i) for i in range(days - 14)]
    weights = []
    for day in candidates:
        month = day.month
        weekday = day.weekday()
        weight = 1.0
        if dept_id == 2 and month in (7, 8, 9):       # monsoon/respiratory load
            weight *= 1.45
        if dept_id == 5 and month in (1, 12):         # winter paediatrics rise
            weight *= 1.55
        if dept_id == 4 and weekday in (5, 6):        # weekend injuries
            weight *= 1.45
        if dept_id == 3 and weekday in (1, 2, 3):     # elective surgery mid-week
            weight *= 1.55
        if dept_id == 6 and month in (3, 4, 8, 9):
            weight *= 1.10
        weights.append(weight)
    return rng.choices(candidates, weights=weights, k=1)[0]


def make_encounters(rng: random.Random) -> list[dict[str, Any]]:
    counts = {2: 65, 3: 50, 4: 45, 5: 40, 6: 40}  # exactly 240
    los_ranges = {2: (3, 9), 3: (2, 6), 4: (3, 7), 5: (1, 5), 6: (1, 4)}
    rows: list[dict[str, Any]] = []
    encounter_id = 1
    for dept_id, count in counts.items():
        for _ in range(count):
            adm = month_weighted_date(rng, dept_id)
            lo, hi = los_ranges[dept_id]
            stay = rng.randint(lo, hi)
            is_open = (encounter_id % 23 == 0)  # ~4% valid OPEN rows
            discharge = None if is_open else min(adm + timedelta(days=stay), END_DATE)
            if discharge is not None and discharge < adm:
                discharge = adm
            status = "OPEN" if discharge is None else "DISCHARGED"
            rows.append({
                "encounter_id": encounter_id,
                "encounter_code": f"ENC-{encounter_id:04d}",
                "dept_id": dept_id,
                "admission_date": iso(adm),
                "discharge_date": iso(discharge) if discharge else None,
                "encounter_status": status,
                "data_source_label": "SYNTHETIC",
            })
            encounter_id += 1
    rows.sort(key=lambda r: (r["admission_date"], r["dept_id"], r["encounter_id"]))
    # Re-assign stable consecutive IDs after sorting, keeping codes in sync.
    for new_id, row in enumerate(rows, start=1):
        row["encounter_id"] = new_id
        row["encounter_code"] = f"ENC-{new_id:04d}"
    return rows


def occupancy_target(day: date, dept_id: int, rng: random.Random) -> float:
    base = {2: 0.78, 3: 0.68, 4: 0.66, 5: 0.63, 6: 0.71}[dept_id]
    month = day.month
    dow = day.weekday()
    bump = 0.0
    if dept_id == 2 and month in (7, 8, 9):
        bump += 0.11
    if dept_id == 5 and month in (1, 12):
        bump += 0.13
    if dept_id == 4 and dow in (5, 6):
        bump += 0.10
    if dept_id == 3 and dow in (1, 2, 3):
        bump += 0.07
    if dept_id == 6 and month in (3, 4, 8, 9):
        bump += 0.04
    # Recurrent weekly rhythm: Monday admissions and Friday turnover add noise.
    if dow == 0:
        bump += 0.025
    if dow == 4:
        bump -= 0.015
    return clamp(base + bump + rng.uniform(-0.075, 0.075), 0.42, 0.97)


def make_daily_utilization(rng: random.Random) -> tuple[list[dict[str, Any]], dict[int, dict[str, Any]]]:
    rows: list[dict[str, Any]] = []
    expected_by_id: dict[int, dict[str, Any]] = {}
    utilization_id = 1
    num_days = (END_DATE - START_DATE).days + 1

    for offset in range(num_days):
        day = START_DATE + timedelta(days=offset)
        for dept_id in range(2, 7):
            bed_cap = float(BED_CAPACITY[dept_id])
            occ_pct = occupancy_target(day, dept_id, rng)
            occupied = float(round(bed_cap * occ_pct))
            # Daily staffed hours; workloads rise with occupancy but remain plausible.
            norm_load = occupied / bed_cap
            staff_rates = {
                "DOCTOR": clamp(0.63 + 0.24 * norm_load + rng.uniform(-0.07, 0.06), 0.55, 1.02),
                "NURSE": clamp(0.68 + 0.25 * norm_load + rng.uniform(-0.06, 0.07), 0.60, 1.05),
                "TECHNICIAN": clamp(0.48 + 0.28 * norm_load + rng.uniform(-0.08, 0.08), 0.40, 0.95),
            }
            values: dict[str, tuple[float, float]] = {"BED_CAPACITY": (bed_cap, occupied)}
            for category, available in STAFF_CAPACITY[dept_id].items():
                values[category] = (available, round_hours(available * staff_rates[category]))

            # Resource utilisation follows known operating patterns.
            for category, available in RESOURCE_CAPACITY[dept_id].items():
                if available == 0:
                    used = 0.0
                else:
                    base_rate = {
                        "ICU_VENTILATOR": 0.50 + 0.28 * norm_load,
                        "OPERATING_ROOM": 0.30 + 0.28 * norm_load,
                        "DIAGNOSTIC_IMAGING": 0.48 + 0.23 * norm_load,
                    }[category]
                    if category == "OPERATING_ROOM":
                        if day.weekday() in (1, 2, 3):
                            base_rate += 0.19
                        if day.weekday() in (5, 6):
                            base_rate -= 0.22
                    rate = clamp(base_rate + rng.uniform(-0.09, 0.09), 0.12, 0.98)
                    used = round_hours(available * rate)
                values[category] = (available, used)

            for category in [r[1] for r in CATEGORY_SPEC]:
                available, used = values[category]
                row = {
                    "utilization_id": utilization_id,
                    "metric_date": iso(day),
                    "dept_id": dept_id,
                    "category_id": CATEGORY_ID[category],
                    "available_amount": round_hours(available),
                    "used_amount": round_hours(used),
                    "source_batch_id": BATCH_ID,
                }
                rows.append(row)
                expected_by_id[utilization_id] = dict(row)
                utilization_id += 1
    return rows, expected_by_id


def inject_quality_issues(
    encounters: list[dict[str, Any]],
    daily_rows: list[dict[str, Any]],
    expected_daily: dict[int, dict[str, Any]],
    rng: random.Random,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    """Create raw extracts with 2.2% missing values, three duplicates, six outliers."""
    dirty_encounters = [dict(r) for r in encounters]
    dirty_daily = [dict(r) for r in daily_rows]
    issues: list[dict[str, Any]] = []

    # Add six extreme but non-negative values. The canonical records remain in
    # expected_daily and are used to repair these anomalies before SQLite load.
    outlier_ids: list[int] = []
    wanted_codes = ["BED_CAPACITY", "DOCTOR", "NURSE", "TECHNICIAN", "ICU_VENTILATOR", "OPERATING_ROOM"]
    selected_dept_dates: set[tuple[int, str]] = set()
    for code in wanted_codes:
        candidates = [r for r in dirty_daily
                      if r["category_id"] == CATEGORY_ID[code]
                      and r["available_amount"] > 0
                      and r["metric_date"] not in (iso(START_DATE), "2025-11-04")
                      and (r["dept_id"], r["metric_date"]) not in selected_dept_dates]
        if not candidates:
            continue
        match = rng.choice(candidates)
        selected_dept_dates.add((match["dept_id"], match["metric_date"]))
        match["used_amount"] = round(match["available_amount"] * 4.0 + 7.0, 2)
        outlier_ids.append(match["utilization_id"])
        issues.append({
            "issue_type": "OUTLIER",
            "table_name": "daily_utilization",
            "record_key": str(match["utilization_id"]),
            "column_name": "used_amount",
            "raw_value": str(match["used_amount"]),
            "cleaning_action": "Restore deterministic source value after plausibility check (used > 150% of available).",
        })

    # Inject 2.2% missing values into the raw used_amount field. Never overwrite
    # outlier records. The missing field is reconstructed from the deterministic
    # seed-42 source record using utilization_id during the cleaning stage.
    target_missing = round(len(dirty_daily) * 0.022)
    eligible = [r for r in dirty_daily if r["utilization_id"] not in set(outlier_ids)]
    missing_records = rng.sample(eligible, target_missing)
    for row in missing_records:
        old = row["used_amount"]
        row["used_amount"] = None
        issues.append({
            "issue_type": "MISSING_VALUE",
            "table_name": "daily_utilization",
            "record_key": str(row["utilization_id"]),
            "column_name": "used_amount",
            "raw_value": "",
            "cleaning_action": "Reconstruct from deterministic source values for this synthetic record.",
        })

    # Two exact duplicate daily rows and one exact duplicate encounter row.
    dirty_daily.extend([dict(dirty_daily[4]), dict(dirty_daily[100])])
    issues.extend([
        {"issue_type": "DUPLICATE_ROW", "table_name": "daily_utilization",
         "record_key": str(dirty_daily[-2]["utilization_id"]), "column_name": "*",
         "raw_value": "Exact duplicate row", "cleaning_action": "Keep first occurrence by PK and composite business key."},
        {"issue_type": "DUPLICATE_ROW", "table_name": "daily_utilization",
         "record_key": str(dirty_daily[-1]["utilization_id"]), "column_name": "*",
         "raw_value": "Exact duplicate row", "cleaning_action": "Keep first occurrence by PK and composite business key."},
    ])
    dirty_encounters.append(dict(dirty_encounters[10]))
    issues.append({
        "issue_type": "DUPLICATE_ROW", "table_name": "patient_encounters",
        "record_key": str(dirty_encounters[-1]["encounter_id"]), "column_name": "*",
        "raw_value": "Exact duplicate row", "cleaning_action": "Keep first occurrence by PK and encounter_code."})

    return dirty_encounters, dirty_daily, issues


def write_csv(path: Path, columns: list[str], rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_excel(raw_tables: dict[str, list[dict[str, Any]]], issues: list[dict[str, Any]], output: Path) -> None:
    try:
        from artifact_tool import SpreadsheetFile, Workbook
    except ImportError:
        if output.exists():
            print(f"Preserving existing approved workbook: {output}")
            return
        raise

    workbook = Workbook.create()
    table_names = {
        "departments": "DepartmentsData",
        "utilization_categories": "UtilCategoriesData",
        "patient_encounters": "PatientEncountersData",
        "daily_utilization": "DailyUtilizationData",
    }
    for table_name, rows in raw_tables.items():
        sheet = workbook.worksheets.add(table_name)
        columns = TABLE_COLUMNS[table_name]
        matrix = [columns] + [[row.get(c) for c in columns] for row in rows]
        sheet.get_range_by_indexes(0, 0, len(matrix), len(columns)).values = matrix
        header = sheet.get_range_by_indexes(0, 0, 1, len(columns))
        header.format = {
            "fill": "#17365D",
            "font": {"bold": True, "color": "#FFFFFF"},
            "horizontal_alignment": "center",
            "vertical_alignment": "center",
            "wrap_text": True,
            "row_height": 30,
        }
        sheet.get_range_by_indexes(1, 0, max(1, len(rows)), len(columns)).format.wrap_text = True
        sheet.freeze_panes.freeze_rows(1)
        # Filters via structured Excel table.
        last_col = chr(ord("A") + len(columns) - 1)
        sheet.tables.add(f"A1:{last_col}{len(matrix)}", True, table_names[table_name])
        widths = [32 if c == "source_batch_id" else (16 if len(c) < 18 else 23) for c in columns]
        for idx, width in enumerate(widths):
            col = chr(ord("A") + idx)
            sheet.get_range(f"{col}:{col}").format.column_width = width
        sheet.get_range(f"A1:{last_col}{len(matrix)}").format.vertical_alignment = "center"

    issue_sheet = workbook.worksheets.add("Data_Quality_Issues")
    issue_columns = ["issue_type", "table_name", "record_key", "column_name", "raw_value", "cleaning_action"]
    issue_matrix = [issue_columns] + [[r.get(c) for c in issue_columns] for r in issues]
    issue_sheet.get_range_by_indexes(0, 0, len(issue_matrix), len(issue_columns)).values = issue_matrix
    issue_sheet.get_range("A1:F1").format = {
        "fill": "#8A3B12", "font": {"bold": True, "color": "#FFFFFF"},
        "horizontal_alignment": "center", "wrap_text": True, "row_height": 30,
    }
    issue_sheet.freeze_panes.freeze_rows(1)
    issue_sheet.tables.add(f"A1:F{len(issue_matrix)}", True, "DataQualityIssues")
    for col, width in {"A": 20, "B": 24, "C": 16, "D": 20, "E": 22, "F": 70}.items():
        issue_sheet.get_range(f"{col}:{col}").format.column_width = width
    SpreadsheetFile.export_xlsx(workbook).save(str(output))


def create_database(
    db_path: Path,
    departments: list[dict[str, Any]],
    categories: list[dict[str, Any]],
    encounters: list[dict[str, Any]],
    dirty_encounters: list[dict[str, Any]],
    daily_rows: list[dict[str, Any]],
    dirty_daily: list[dict[str, Any]],
    expected_daily: dict[int, dict[str, Any]],
) -> dict[str, Any]:
    if db_path.exists():
        db_path.unlink()
    conn = get_connection(db_path, create=True)
    try:
        fk_enabled = conn.execute("PRAGMA foreign_keys").fetchone()[0]
        if fk_enabled != 1:
            raise RuntimeError("SQLite foreign-key enforcement did not enable.")
        for statement in DDL_STATEMENTS:
            conn.execute(statement)
        for statement in INDEX_AND_TRIGGER_DDL:
            conn.execute(statement)

        dept_cols = TABLE_COLUMNS["departments"]
        category_cols = TABLE_COLUMNS["utilization_categories"]
        encounter_cols = TABLE_COLUMNS["patient_encounters"]
        daily_cols = TABLE_COLUMNS["daily_utilization"]
        conn.executemany(
            f"INSERT INTO departments ({','.join(dept_cols)}) VALUES ({','.join('?' for _ in dept_cols)})",
            [[row.get(c) for c in dept_cols] for row in departments],
        )
        conn.executemany(
            f"INSERT INTO utilization_categories ({','.join(category_cols)}) VALUES ({','.join('?' for _ in category_cols)})",
            [[row.get(c) for c in category_cols] for row in categories],
        )

        # Dedupe encounters by PK + encounter_code. This intentionally compares
        # the raw export against canonical deterministic records.
        enc_seen = set()
        cleaned_encounters = []
        for row in dirty_encounters:
            key = (row["encounter_id"], row["encounter_code"])
            if key in enc_seen:
                continue
            enc_seen.add(key)
            cleaned_encounters.append(row)
        conn.executemany(
            f"INSERT INTO patient_encounters ({','.join(encounter_cols)}) VALUES ({','.join('?' for _ in encounter_cols)})",
            [[row.get(c) for c in encounter_cols] for row in cleaned_encounters],
        )

        # Clean daily facts: de-duplicate by PK/composite natural key, restore
        # missing values from the seed-42 source map, and repair outliers.
        seen_ids, seen_natural = set(), set()
        cleaned_daily = []
        missing_repaired = 0
        outliers_repaired = 0
        outlier_ids = set()
        for raw in dirty_daily:
            row = dict(raw)
            key_id = row["utilization_id"]
            natural_key = (row["metric_date"], row["dept_id"], row["category_id"])
            if key_id in seen_ids or natural_key in seen_natural:
                continue
            seen_ids.add(key_id)
            seen_natural.add(natural_key)
            canonical = expected_daily[key_id]
            if row["used_amount"] is None:
                row["used_amount"] = canonical["used_amount"]
                missing_repaired += 1
            available = float(row["available_amount"])
            used = float(row["used_amount"])
            # Extreme outliers >150% of available are repaired. Ordinary >100%
            # utilisation is retained and remains analytically meaningful.
            if available > 0 and used > available * 1.5:
                row["used_amount"] = canonical["used_amount"]
                outliers_repaired += 1
                outlier_ids.add(key_id)
            cleaned_daily.append(row)

        conn.executemany(
            f"INSERT INTO daily_utilization ({','.join(daily_cols)}) VALUES ({','.join('?' for _ in daily_cols)})",
            [[row.get(c) for c in daily_cols] for row in cleaned_daily],
        )
        conn.execute(VIEW_SQL)
        conn.commit()

        counts = {
            "departments": conn.execute("SELECT COUNT(*) FROM departments").fetchone()[0],
            "utilization_categories": conn.execute("SELECT COUNT(*) FROM utilization_categories").fetchone()[0],
            "patient_encounters": conn.execute("SELECT COUNT(*) FROM patient_encounters").fetchone()[0],
            "daily_utilization": conn.execute("SELECT COUNT(*) FROM daily_utilization").fetchone()[0],
            "view_rows": conn.execute("SELECT COUNT(*) FROM vw_department_daily_analysis").fetchone()[0],
            "view_columns": len(conn.execute("PRAGMA table_info(vw_department_daily_analysis)").fetchall()),
        }
        fk_issues = conn.execute("PRAGMA foreign_key_check").fetchall()
        range_issues = []
        checks = [
            ("threshold_pct", "SELECT COUNT(*) FROM departments WHERE occupancy_warning_threshold_pct < 0 OR occupancy_warning_threshold_pct > 100"),
            ("negative_amounts", "SELECT COUNT(*) FROM daily_utilization WHERE available_amount < 0 OR used_amount < 0"),
            ("invalid_category_group", "SELECT COUNT(*) FROM utilization_categories WHERE category_group NOT IN ('BED','STAFF','RESOURCE')"),
            ("invalid_encounter_status", "SELECT COUNT(*) FROM patient_encounters WHERE NOT ((encounter_status='OPEN' AND discharge_date IS NULL) OR (encounter_status='DISCHARGED' AND discharge_date IS NOT NULL))"),
            ("bed_overcapacity_after_clean", "SELECT COUNT(*) FROM daily_utilization du JOIN utilization_categories uc USING(category_id) WHERE uc.category_code='BED_CAPACITY' AND du.used_amount > du.available_amount * 1.5"),
        ]
        for name, sql in checks:
            count = conn.execute(sql).fetchone()[0]
            range_issues.append((name, count))

        # Check exact column names and SQLite declared types.
        schema_info = {}
        for table in TABLE_COLUMNS:
            schema_info[table] = [
                (r[1], r[2], r[5]) for r in conn.execute(f"PRAGMA table_info({table})").fetchall()
            ]
        actual_columns_match = all(
            [x[0] for x in schema_info[t]] == TABLE_COLUMNS[t] for t in TABLE_COLUMNS
        )
        actual_types_and_keys_match = True
        actual_foreign_keys_match = True
        for table_name in TABLE_COLUMNS:
            pragma_rows = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
            observed = {r[1]: (str(r[2]).upper(), int(r[5])) for r in pragma_rows}
            if observed != EXPECTED_TYPES_AND_PK[table_name]:
                actual_types_and_keys_match = False
            fk_rows = conn.execute(f"PRAGMA foreign_key_list({table_name})").fetchall()
            observed_fks = {(r[3], r[2], r[4]) for r in fk_rows}
            if observed_fks != EXPECTED_FOREIGN_KEYS[table_name]:
                actual_foreign_keys_match = False

        # Prove the helper also enforces FKs after the database has been closed
        # and re-opened, which is how Streamlit will access it.
        app_connection = get_connection(db_path)
        try:
            app_fk_enabled = app_connection.execute("PRAGMA foreign_keys").fetchone()[0]
            invalid_fk_rejected = False
            try:
                app_connection.execute(
                    "INSERT INTO patient_encounters "
                    "(encounter_id, encounter_code, dept_id, admission_date, discharge_date, encounter_status, data_source_label) "
                    "VALUES (999999, 'ENC-FK-TEST', 999999, '2026-01-01', '2026-01-02', 'DISCHARGED', 'SYNTHETIC')"
                )
                app_connection.rollback()
            except sqlite3.IntegrityError:
                invalid_fk_rejected = True
                app_connection.rollback()
        finally:
            app_connection.close()

        pattern_connection = get_connection(db_path)
        try:
            pattern_metrics = {
                "general_medicine_monsoon_vs_other_pct": pattern_connection.execute(
                "SELECT AVG(CASE WHEN calendar_month IN (7,8,9) THEN occupancy_rate_pct END), "
                "AVG(CASE WHEN calendar_month NOT IN (7,8,9) THEN occupancy_rate_pct END) "
                "FROM vw_department_daily_analysis WHERE dept_id=2"
            ).fetchone(),
                "paediatrics_winter_vs_other_pct": pattern_connection.execute(
                "SELECT AVG(CASE WHEN calendar_month IN (12,1) THEN occupancy_rate_pct END), "
                "AVG(CASE WHEN calendar_month NOT IN (12,1) THEN occupancy_rate_pct END) "
                "FROM vw_department_daily_analysis WHERE dept_id=5"
            ).fetchone(),
                "orthopaedics_weekend_vs_weekday_pct": pattern_connection.execute(
                "SELECT AVG(CASE WHEN day_of_week IN ('0','6') THEN occupancy_rate_pct END), "
                "AVG(CASE WHEN day_of_week NOT IN ('0','6') THEN occupancy_rate_pct END) "
                "FROM vw_department_daily_analysis WHERE dept_id=4"
            ).fetchone(),
                "general_surgery_or_tue_thu_vs_other_pct": pattern_connection.execute(
                "SELECT AVG(CASE WHEN CAST(day_of_week AS INTEGER) IN (2,3,4) THEN operating_room_utilization_pct END), "
                "AVG(CASE WHEN CAST(day_of_week AS INTEGER) NOT IN (2,3,4) THEN operating_room_utilization_pct END) "
                "FROM vw_department_daily_analysis WHERE dept_id=3"
            ).fetchone(),
        }
            corr_rows = pattern_connection.execute(
            "SELECT occupancy_rate_pct, 100.0*total_staff_used_hours/NULLIF(total_staff_available_hours,0) "
            "FROM vw_department_daily_analysis WHERE total_staff_available_hours IS NOT NULL"
        ).fetchall()
            if corr_rows:
                xs = [float(r[0]) for r in corr_rows]
                ys = [float(r[1]) for r in corr_rows]
                mx, my = sum(xs)/len(xs), sum(ys)/len(ys)
                cov = sum((x-mx)*(y-my) for x,y in zip(xs,ys))
                den = math.sqrt(sum((x-mx)**2 for x in xs) * sum((y-my)**2 for y in ys))
                pattern_metrics["occupancy_staff_utilization_correlation"] = cov/den if den else None
            else:
                pattern_metrics["occupancy_staff_utilization_correlation"] = None
        finally:
            pattern_connection.close()

        return {
            "foreign_keys_enabled": fk_enabled,
            "app_connection_foreign_keys_enabled": app_fk_enabled,
            "app_connection_invalid_fk_rejected": invalid_fk_rejected,
            "pattern_metrics": pattern_metrics,
            "counts": counts,
            "foreign_key_issues": fk_issues,
            "range_issues": range_issues,
            "schema_columns_match": actual_columns_match,
            "schema_types_and_keys_match": actual_types_and_keys_match,
            "schema_foreign_keys_match": actual_foreign_keys_match,
            "missing_repaired": missing_repaired,
            "outliers_repaired": outliers_repaired,
            "cleaned_encounter_rows": len(cleaned_encounters),
            "cleaned_daily_rows": len(cleaned_daily),
            "schema_info": schema_info,
        }
    finally:
        conn.close()


def write_validation_report(
    path: Path,
    raw_tables: dict[str, list[dict[str, Any]]],
    clean_rows: dict[str, int],
    issues: list[dict[str, Any]],
    db_result: dict[str, Any],
) -> None:
    issue_counts = Counter(r["issue_type"] for r in issues)
    by_table = Counter(r["table_name"] for r in issues)
    missing_daily = issue_counts["MISSING_VALUE"]
    duplicate_count = issue_counts["DUPLICATE_ROW"]
    outlier_count = issue_counts["OUTLIER"]
    raw_daily_count = len(raw_tables["daily_utilization"])
    missing_pct = 100.0 * missing_daily / 12775

    lines = [
        "HRA-001 | HOSPITAL RESOURCE UTILIZATION ANALYSIS",
        "STEP 10 — SYNTHETIC DATA GENERATION & VALIDATION REPORT",
        "=" * 72,
        f"Generated at: {datetime.now().isoformat(timespec='seconds')}",
        f"Random seed: {SEED}",
        f"Data period: {iso(START_DATE)} to {iso(END_DATE)} (365 days; Step 8 baseline period)",
        "Facility: Aarohan Multispecialty Hospital - Ghaziabad (fictional)",
        "Data policy: synthetic records only; no patient names or real personal data.",
        "",
        "1. RAW EXPORT ROW COUNTS (intentional data-quality issues retained)",
        "-" * 72,
    ]
    for table_name in TABLE_COLUMNS:
        lines.append(f"{table_name}: {len(raw_tables[table_name]):,} raw rows")
    lines += [
        "",
        "2. CLEAN SQLITE ROW COUNTS (after quality handling)",
        "-" * 72,
    ]
    for table_name, count in clean_rows.items():
        lines.append(f"{table_name}: {count:,} rows")
    for table_name, count in db_result["counts"].items():
        lines.append(f"database {table_name}: {count:,}")
    lines += [
        "",
        "3. INJECTED DATA-QUALITY ISSUES IN RAW CSV/XLSX",
        "-" * 72,
        f"Missing used_amount values: {missing_daily:,} / 12,775 unique planned daily facts = {missing_pct:.2f}% (2 duplicate raw rows are excluded from this base-rate denominator)",
        f"Duplicate rows: {duplicate_count} (2 daily_utilization + 1 patient_encounters)",
        f"Extreme numeric outliers: {outlier_count} (used_amount > 150% of available_amount)",
        "Affected tables: " + ", ".join(f"{t} ({n})" for t, n in sorted(by_table.items())),
        "",
        "4. CLEANING ACTIONS APPLIED BEFORE SQLITE LOAD",
        "-" * 72,
        f"Missing values reconstructed deterministically: {db_result['missing_repaired']}",
        f"Duplicate rows removed: {duplicate_count}",
        f"Extreme outliers restored from deterministic seed-42 source: {db_result['outliers_repaired']}",
        "Valid OPEN encounters retain NULL discharge_date by design; these are not missing-data defects.",
        "Ordinary utilisation above 100% but not above 150% is retained as a potential operational signal.",
        "",
        "5. SQLITE INTEGRITY & VALIDATION",
        "-" * 72,
        f"PRAGMA foreign_keys on generator connection: {'ON' if db_result['foreign_keys_enabled'] == 1 else 'OFF'}",
        f"PRAGMA foreign_keys on reopened application connection: {'ON' if db_result['app_connection_foreign_keys_enabled'] == 1 else 'OFF'}",
        f"Application connection rejects invalid FK insert: {db_result['app_connection_invalid_fk_rejected']}",
        f"PRAGMA foreign_key_check issue count: {len(db_result['foreign_key_issues'])}",
        f"Exact schema column names match Step 8: {db_result['schema_columns_match']}",
        f"Declared SQLite types and PKs match Step 8: {db_result['schema_types_and_keys_match']}",
        f"SQLite FK definitions match Step 8: {db_result['schema_foreign_keys_match']}",
        "Note: SQLite foreign-key enforcement is connection-specific and is not persisted as a database-file setting; use src/db.py:get_connection() for every application connection.",
        f"Joined view column count: {db_result['counts']['view_columns']} (expected 40)",
        f"Joined view row count: {db_result['counts']['view_rows']:,} (expected 1,825)",
    ]
    for name, count in db_result["range_issues"]:
        lines.append(f"Range/business check {name}: {count} issue(s)")
    lines += [
        "",
        "6. REALISTIC PATTERNS BUILT INTO THE DATA",
        "-" * 72,
        "PATTERN-01: General Medicine occupancy is higher during the July–September 2026 monsoon period.",
        "PATTERN-02: Paediatrics has a winter rise in December 2025 and January 2026.",
        "PATTERN-03: Orthopaedics occupancy is higher on Saturdays and Sundays (injury demand pattern).",
        "PATTERN-04: General Surgery and operating-room utilisation peak Tuesday–Thursday and reduce on weekends.",
        "PATTERN-05: Higher bed occupancy is associated with higher staff-hours utilisation.",
        "Verified pattern metrics (averages unless otherwise stated):",
        f"- General Medicine monsoon (Jul-Sep 2026) {db_result['pattern_metrics']['general_medicine_monsoon_vs_other_pct'][0]:.2f}% vs other months {db_result['pattern_metrics']['general_medicine_monsoon_vs_other_pct'][1]:.2f}%.",
        f"- Paediatrics winter (Dec 2025-Jan 2026) {db_result['pattern_metrics']['paediatrics_winter_vs_other_pct'][0]:.2f}% vs other months {db_result['pattern_metrics']['paediatrics_winter_vs_other_pct'][1]:.2f}%.",
        f"- Orthopaedics weekends {db_result['pattern_metrics']['orthopaedics_weekend_vs_weekday_pct'][0]:.2f}% vs weekdays {db_result['pattern_metrics']['orthopaedics_weekend_vs_weekday_pct'][1]:.2f}%.",
        f"- General Surgery operating-room Tue-Thu {db_result['pattern_metrics']['general_surgery_or_tue_thu_vs_other_pct'][0]:.2f}% vs other days {db_result['pattern_metrics']['general_surgery_or_tue_thu_vs_other_pct'][1]:.2f}%.",
        f"- Occupancy vs total staff-hours utilisation Pearson correlation: {db_result['pattern_metrics']['occupancy_staff_utilization_correlation']:.3f}.",
        "These are synthetic patterns intentionally created for analytical discovery; they are not claims about a real hospital.",
        "",
        "SCHEMA RECONCILIATION: The canonical Step 8 Tables_Summary has been corrected to report 7 daily_utilization columns, matching its data dictionary and CREATE TABLE DDL. The generator follows the corrected canonical design.",
        "",
        "7. SAMPLE-ROW REVIEW",
        "-" * 72,
        "The first 10 rows of each raw table are included in the corresponding workbook sheet and CSV.",
        "They were generated with consistent codes, ISO dates, category values, IDs and fictional department labels.",
        "The workbook was exported with a separate Data_Quality_Issues sheet to make intentional defects auditable.",
        "",
        "8. ACCEPTANCE SUMMARY",
        "-" * 72,
        f"Expected master rows: departments=6, utilization_categories=7; actual={clean_rows['departments']}, {clean_rows['utilization_categories']}",
        f"Expected main fact rows: patient_encounters=240; actual={clean_rows['patient_encounters']}",
        f"Expected daily fact rows: daily_utilization=12,775; actual={clean_rows['daily_utilization']}",
        f"Foreign key check: {'PASS' if not db_result['foreign_key_issues'] else 'FAIL'}",
        f"Range/business checks: {'PASS' if all(v == 0 for _, v in db_result['range_issues']) else 'FAIL'}",
        f"Schema column-name match: {'PASS' if db_result['schema_columns_match'] else 'FAIL'}",
        f"Schema type/PK match: {'PASS' if db_result['schema_types_and_keys_match'] else 'FAIL'}",
        f"Schema FK-definition match: {'PASS' if db_result['schema_foreign_keys_match'] else 'FAIL'}",
        f"Application FK enforcement: {'PASS' if db_result['app_connection_foreign_keys_enabled'] == 1 and db_result['app_connection_invalid_fk_rejected'] else 'FAIL'}",
        f"40-column view: {'PASS' if db_result['counts']['view_columns'] == 40 else 'FAIL'}",
    ]
    overall_pass = (
        not db_result["foreign_key_issues"]
        and db_result["schema_columns_match"]
        and db_result["schema_types_and_keys_match"]
        and db_result["schema_foreign_keys_match"]
        and db_result["app_connection_foreign_keys_enabled"] == 1
        and db_result["app_connection_invalid_fk_rejected"]
        and db_result["counts"]["view_columns"] == 40
        and all(v == 0 for _, v in db_result["range_issues"])
        and clean_rows == {"departments": 6, "utilization_categories": 7,
                           "patient_encounters": 240, "daily_utilization": 12775}
    )
    lines.append(f"OVERALL DATABASE ACCEPTANCE: {'PASS' if overall_pass else 'FAIL'}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    rng = random.Random(SEED)
    departments = make_departments()
    categories = make_categories()
    encounters = make_encounters(rng)
    daily_rows, expected_daily = make_daily_utilization(rng)
    dirty_encounters, dirty_daily, issues = inject_quality_issues(
        encounters, daily_rows, expected_daily, rng
    )

    raw_tables = {
        "departments": [dict(r) for r in departments],
        "utilization_categories": [dict(r) for r in categories],
        "patient_encounters": dirty_encounters,
        "daily_utilization": dirty_daily,
    }

    # CSV exports preserve intentional raw issues for the later data-cleaning step.
    for table_name, rows in raw_tables.items():
        write_csv(DATA_DIR / f"{table_name}.csv", TABLE_COLUMNS[table_name], rows)

    # Workbook: one sheet per table, plus a data-quality issue log.
    xlsx_path = DATA_DIR / "hospital_resource_utilization_data.xlsx"
    write_excel(raw_tables, issues, xlsx_path)

    # SQLite receives cleaned data after de-duplication and repair, under the
    # exact Step 8 constraints, with foreign keys ON for this connection.
    db_result = create_database(
        DATA_DIR / "app.db", departments, categories, encounters,
        dirty_encounters, daily_rows, dirty_daily, expected_daily,
    )
    clean_rows = {
        "departments": len(departments),
        "utilization_categories": len(categories),
        "patient_encounters": db_result["cleaned_encounter_rows"],
        "daily_utilization": db_result["cleaned_daily_rows"],
    }
    write_validation_report(
        DATA_DIR / "validation_report.txt", raw_tables, clean_rows, issues, db_result
    )

    # A compact issue log is separately available for filtering.
    with (DATA_DIR / "data_quality_issues.csv").open("w", newline="", encoding="utf-8-sig") as f:
        cols = ["issue_type", "table_name", "record_key", "column_name", "raw_value", "cleaning_action"]
        writer = csv.DictWriter(f, fieldnames=cols)
        writer.writeheader()
        writer.writerows(issues)

    if db_result["foreign_key_issues"]:
        raise RuntimeError(f"Foreign-key validation failed: {db_result['foreign_key_issues']}")
    if not db_result["schema_columns_match"]:
        raise RuntimeError("SQLite schema columns do not match Step 8.")
    if not db_result["schema_types_and_keys_match"]:
        raise RuntimeError("SQLite declared types or primary keys do not match Step 8.")
    if not db_result["schema_foreign_keys_match"]:
        raise RuntimeError("SQLite foreign-key definitions do not match Step 8.")
    if db_result["app_connection_foreign_keys_enabled"] != 1 or not db_result["app_connection_invalid_fk_rejected"]:
        raise RuntimeError("Application database helper did not enforce foreign keys on a reopened connection.")
    if db_result["counts"]["view_columns"] != 40:
        raise RuntimeError(f"Expected 40 joined-view columns, found {db_result['counts']['view_columns']}.")
    if any(count != 0 for _, count in db_result["range_issues"]):
        raise RuntimeError(f"Range/business validation failed: {db_result['range_issues']}")

    print("HRA-001 synthetic data generation completed.")
    print(f"Workbook: {xlsx_path}")
    print(f"SQLite DB: {DATA_DIR / 'app.db'}")
    print(f"Validation report: {DATA_DIR / 'validation_report.txt'}")
    print("Clean DB row counts:", db_result["counts"])
    print("Raw issue counts:", dict(Counter(r["issue_type"] for r in issues)))
    print("Foreign key check: PASS | Schema check: PASS | Range checks: PASS")


if __name__ == "__main__":
    main()
