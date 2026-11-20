# HRA-001 Synthetic Data Assets

## Overview
This directory contains the synthetic dataset for the Hospital Resource Utilization Analysis (HRA-001) project, representing a hypothetical 250-bed multi-specialty hospital in Ghaziabad, Uttar Pradesh.

## Files
- `app.db`: Clean, schema-valid SQLite analytical database with foreign keys enforced, constraints, and the 40-column analysis view (`vw_department_daily_analysis`).
- `hospital_resource_utilization_data.xlsx`: Approved raw synthetic workbook containing one sheet per base table plus a `Data_Quality_Issues` audit sheet.
- `departments.csv`: Raw department master table (6 rows).
- `utilization_categories.csv`: Raw utilization category master table (7 rows).
- `patient_encounters.csv`: Raw patient encounter facts (240 rows).
- `daily_utilization.csv`: Raw daily utilization facts (12,775 rows) containing intentional data-quality issues for cleaning demonstrations.
- `data_quality_issues.csv`: Auditable log of all 290 injected quality defects (281 missing values, 3 duplicate rows, 6 extreme outliers).
- `validation_report.txt`: Automated audit report confirming row counts, foreign key integrity, schema column matching, and clinical trend patterns.

## Reproduction
To regenerate this dataset deterministically using random seed 42:
```bash
python src/generate_data.py
```
