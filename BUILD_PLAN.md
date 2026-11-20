# HRA-001 — BUILD PLAN

**Project:** Hospital Resource Utilization Analysis  
**Student:** Abhinav Adhikari | **Roll No.:** 2503201450005  
**Programme:** MCA 2nd Year – Data Analytics | **Institution:** ABES Engineering College  
**Domain:** Data Analytics / Healthcare Operations  
**Document ID:** HRA-001-BUILD-14 | **Version:** 1.0 | **Prepared:** 20 November 2026  
**Status:** Build baseline for Step 15 — follow one BUILD task per turn.

> **Execution rule:** Do not ask an AI to implement the whole repository at once. Start each turn with `STEP 15 — BUILD-XX`, attach the files named by that task, paste its exact prompt, implement only that task, run its checks, review the diff, and commit before proceeding. Do not begin BUILD-(XX+1) until the current task's exit criteria are met or a blocker is recorded.

## 1. Project summary (10 lines)

1. HRA-001 is a descriptive data-analytics prototype for a hypothetical 250-bed multi-specialty hospital in Ghaziabad, Uttar Pradesh.
2. It consolidates fictional department, patient-encounter, bed-capacity, staff-hour and shared-resource data into one analytical experience.
3. Its users are hospital administrators, operations managers, department heads, bed managers, workforce coordinators and academic reviewers.
4. The application uses Python 3.12, Streamlit multipage navigation, Pandas, NumPy, SciPy/statsmodels and Plotly.
5. SQLite is the read-only operational store at `data/app.db`; its base schema has four tables and one 40-column joined analysis view.
6. All data is synthetic; the raw CSV/XLSX extracts intentionally contain documented missing values, duplicates and outliers for cleaning demonstrations.
7. The dashboard must answer OQ-01 through OQ-10, including occupancy, patient flow, ALOS, staffing, shared resources and threshold monitoring.
8. The product has eight stable UI screens (`UI-01`–`UI-08`) and 18 user stories (`US-01`–`US-18`).
9. The approved business baseline is `BR-01`–`BR-12`; current tests are `TC-F-01`–`TC-F-34` and `TC-T-01`–`TC-T-26`.
10. The build is complete only when all Must requirements, all OQs, automated and functional tests, README, reproducible setup and the live Streamlit Community Cloud demo are verified.

## 2. Source documents and build references

The links below use the final repository paths. Step 1 was copied into `docs/` under the standardized name shown here. Step 6 (PRD) has **not** been created because the project sequence skipped from Step 5 to Step 7; its absence is explicit and must not be hidden.

| Step | Document / asset | Repository path | How it is used |
|---|---|---|---|
| 1 | [Project Understanding](docs/01_Project_Understanding.docx) | `docs/01_Project_Understanding.docx` | Problem, organisation assumptions, audience, stakeholders and OQ-01–OQ-10 |
| 2 | [HMW Statements](docs/02_HMW_Statements.docx) | `docs/02_HMW_Statements.docx` | HMW-01–HMW-10 and stakeholder pain points |
| 3 | [Needs Analysis](docs/03_Needs_Analysis.docx) | `docs/03_Needs_Analysis.docx` | BR-01–BR-12, priority and measurable business needs |
| 4 / 8 / 11 / 12 / 13 | [Master RTM](docs/04_Traceability_Matrix.xlsx) | `docs/04_Traceability_Matrix.xlsx` | Current traceability from OQ/HMW/BR through database, US, UI and test IDs |
| 5 | [Business Requirements Document](docs/05_BRD.docx) | `docs/05_BRD.docx` | Business rules, Must/Should/Could priority, data and success criteria |
| 6 | **PRD pending** | `docs/06_PRD.docx` (not present yet) | Must validate feature register before final product baseline; do not invent PRD approval |
| 7 | [Technical Requirements Document](docs/07_TRD.docx) | `docs/07_TRD.docx` | Stack, architecture, FR-01–FR-13, NFR-01–NFR-12 and deployment constraints |
| 8 | [Database Design](docs/08_Database_Design.xlsx) | `docs/08_Database_Design.xlsx` | Four base tables, exact columns/types/keys, constraints, KPI definitions and 40-column view |
| 9 | [ER Diagram document](docs/09_ER_Diagram.docx) | `docs/09_ER_Diagram.docx` | Relationships, cardinalities and database business rules |
| 9 | [ER Diagram image](docs/09_ER_Diagram.png) | `docs/09_ER_Diagram.png` | Visual schema reference |
| 10 | [Synthetic dataset workbook](data/hospital_resource_utilization_data.xlsx) | `data/hospital_resource_utilization_data.xlsx` | Raw synthetic data, one sheet per base table and data-quality issue sheet |
| 10 | [Departments CSV](data/departments.csv) | `data/departments.csv` | Raw department master |
| 10 | [Utilization categories CSV](data/utilization_categories.csv) | `data/utilization_categories.csv` | Raw category master |
| 10 | [Patient encounters CSV](data/patient_encounters.csv) | `data/patient_encounters.csv` | Raw synthetic encounter facts |
| 10 | [Daily utilization CSV](data/daily_utilization.csv) | `data/daily_utilization.csv` | Raw synthetic daily facts with intentional quality issues |
| 10 | [Data-quality issue log](data/data_quality_issues.csv) | `data/data_quality_issues.csv` | Auditable missing/duplicate/outlier issue list |
| 10 | [Clean SQLite database](data/app.db) | `data/app.db` | Clean, schema-valid production-read dataset |
| 10 | [Validation report](data/validation_report.txt) | `data/validation_report.txt` | Counts, schema/FK/range checks and verified synthetic patterns |
| 10 | [Dataset generator](src/generate_data.py) | `src/generate_data.py` | Reproducible generation with seed 42 |
| 10 | [SQLite connection helper](src/db.py) | `src/db.py` | `get_connection()` enables and verifies SQLite foreign-key enforcement |
| 11 | [User Stories](docs/11_User_Stories.docx) | `docs/11_User_Stories.docx` | US-01–US-18, Given/When/Then criteria, provisional F-01–F-09 and 10-day story plan |
| 12 | [UI Framework](docs/12_UI_Framework.docx) | `docs/12_UI_Framework.docx` | UI-01–UI-08, wireframes, chart choices, shared filters and design tokens |
| 12 | [Shared UI helpers](src/ui.py) | `src/ui.py` | Tailwind iframe header/KPI helpers and shared sidebar filter keys |
| 12 | [Streamlit theme](.streamlit/config.toml) | `.streamlit/config.toml` | Navy/teal/amber/slate theme |
| 13 | [Test Cases](docs/13_Test_Cases.docx) | `docs/13_Test_Cases.docx` | 34 functional cases and 26 technical cases; all functional statuses start Not run |
| 13 | [Test data checks](tests/test_data.py) | `tests/test_data.py` | Database, schema, integrity and cleaning contract tests |
| 13 | [Analysis tests](tests/test_analysis.py) | `tests/test_analysis.py` | KPI/statistics function contract tests |
| 13 | [App tests](tests/test_app.py) | `tests/test_app.py` | Streamlit AppTest page filenames and <3-second AppTest target |
| 13 | [Test fixtures/config](tests/conftest.py) | `tests/conftest.py` | Project-root import path for pytest |
| 13 | [Test instructions](tests/README.md) | `tests/README.md` | Existing test contracts and known pre-build skips |
| 14 | This Word copy | `docs/14_BUILD_PLAN.docx` | Human-readable copy of this executable plan |
| 14 | This AI build input | `BUILD_PLAN.md` | Source of truth for Step 15 task execution |

**Baseline note:** F-01–F-09 in the Step 11 backlog are provisional, BR-derived IDs because Step 6 PRD is pending. Preserve the IDs and their descriptions in Step 15; Step 6 must validate them later. If PRD review changes a feature, log the change and update the RTM without renumbering OQ, HMW, SH, BR, F, FR, NFR, US, UI or TC IDs.

## 3. Final repository folder structure

Repository name: `2503201450005-hospital-resource-utilization-analysis`  
Run all commands from the repository root (Windows PowerShell / Git Bash may be used; paths inside Python and Streamlit should use `pathlib` or forward slashes).

```text
2503201450005-hospital-resource-utilization-analysis/
├── app.py
├── BUILD_PLAN.md
├── README.md
├── requirements.txt
├── .python-version                 # 3.12
├── .gitignore
├── .streamlit/
│   └── config.toml
├── pages/
│   ├── 01_Overview.py              # UI-01 (app.py default page may call this)
│   ├── 02_Patient_Flow_Trend.py    # UI-02
│   ├── 03_Department_Resource_Compare.py # UI-03
│   ├── 04_EDA_Statistics.py        # UI-04
│   ├── 05_Insights_Threshold_Monitor.py  # UI-05
│   ├── 06_Data_Explorer_Downloads.py    # UI-06
│   ├── 07_Data_Quality.py          # UI-07
│   └── 08_About_Metric_Definitions.py    # UI-08
├── src/
│   ├── __init__.py
│   ├── db.py                       # existing Step 10 helper; retain FK enforcement
│   ├── generate_data.py            # existing reproducible generator; do not rewrite casually
│   ├── data_loader.py              # BUILD-02
│   ├── validation.py               # BUILD-02/03
│   ├── cleaning.py                 # BUILD-03
│   ├── metrics.py                  # BUILD-04
│   ├── statistics.py               # BUILD-04
│   ├── analysis.py                 # BUILD-04 public facade required by tests
│   ├── filters.py                  # BUILD-05 shared filter transformations
│   ├── charts.py                   # BUILD-05 reusable Plotly builders
│   └── ui.py                       # existing Step 12 Tailwind / Streamlit helpers
├── data/
│   ├── app.db
│   ├── hospital_resource_utilization_data.xlsx
│   ├── departments.csv
│   ├── utilization_categories.csv
│   ├── patient_encounters.csv
│   ├── daily_utilization.csv
│   ├── data_quality_issues.csv
│   ├── validation_report.txt
│   └── README.md
├── docs/
│   ├── 01_Project_Understanding.docx
│   ├── 02_HMW_Statements.docx
│   ├── 03_Needs_Analysis.docx
│   ├── 04_Traceability_Matrix.xlsx
│   ├── 05_BRD.docx
│   ├── 06_PRD.docx                 # add after completing skipped Step 6
│   ├── 07_TRD.docx
│   ├── 08_Database_Design.xlsx
│   ├── 09_ER_Diagram.docx
│   ├── 09_ER_Diagram.png
│   ├── 11_User_Stories.docx
│   ├── 12_UI_Framework.docx
│   ├── 13_Test_Cases.docx
│   └── 14_BUILD_PLAN.docx
└── tests/
    ├── conftest.py
    ├── test_data.py
    ├── test_analysis.py
    ├── test_app.py
    └── README.md
```

`data/app.db` contains the cleaned, schema-valid, read-only analytical dataset. The raw CSV/XLSX files intentionally retain the Step 10 quality defects for transparency and the UI-07 cleaning demonstration. Never replace the clean DB with raw CSV contents without passing the validation/cleaning pipeline.

## 4. Fixed build contract

### Technology and dependency baseline

Use Python 3.12 and these pins from the reviewed TRD. Do not silently upgrade or add packages; if a pin cannot be installed on the target environment, stop, report the exact resolver error, and propose the smallest documented change before modifying the lock baseline.

```text
streamlit==1.67.0
pandas==3.1.1
numpy==2.5.5
scipy==1.18.1
statsmodels==0.14.6
plotly==7.1.0
pytest==9.2.0
```

### Database and data contract

- Base tables and exact row counts: `departments` = 6; `utilization_categories` = 7; `patient_encounters` = 240; `daily_utilization` = 12,775.
- `daily_utilization` has **7 columns**, as corrected in the canonical Step 8 workbook.
- `vw_department_daily_analysis` has 1,825 rows and **40 columns** (365 dates × five department rows).
- Use only schema names, declared SQLite types, PK/FK and constraints from `docs/08_Database_Design.xlsx` and the SQL in the generator. Do not add a fifth base table or rename columns without a formally approved schema change.
- `src.db.get_connection()` is the required connection entry point. SQLite FK enforcement is connection-specific; preserve `PRAGMA foreign_keys=ON` and its runtime check. Application reads should be read-only and parameterised.
- Date filters are inclusive. The hospital root row must not be added to its five child departments when producing a hospital-wide aggregate.
- Bed occupancy for a period is weighted: `SUM(occupied bed-days) / SUM(available bed-days) * 100`. Never use an unweighted average of daily or department percentages for the headline KPI.
- Available beds on a particular date = usable bed capacity − occupied beds. A negative gap is flagged, not silently shown as valid.
- Admissions count unique encounters by `admission_date`; discharges count by `discharge_date`; OPEN encounters are not discharges.
- ALOS = mean `(discharge_date - admission_date)` for DISCHARGED encounters, using the Step 8 convention (same-day = 0 days).
- Staff and shared-resource utilisation = total used / total available × 100, calculated separately by role/resource and unit. Zero denominators show N/A.
- A threshold breach is strict `occupancy > active threshold`. The initial 85% threshold is **ASSUMED**, not a clinical, regulatory or approved safety limit.
- Keep synthetic source quality issues auditable: 281 missing `used_amount` values, 3 exact duplicate records and 6 high-use outliers are documented in the Step 10 report. Do not discard the issue log or silently convert raw data into clean data.

### IDs to preserve

- Operational questions: OQ-01–OQ-10.
- Stakeholders: SH-01–SH-07.
- HMW: HMW-01–HMW-10.
- Business requirements: BR-01–BR-12 (Must: BR-01, 02, 03, 06, 09, 10, 11; Should: BR-04, 05, 07, 08; Could: BR-12).
- Provisional feature IDs: F-01–F-09 (pending Step 6 PRD review).
- Technical functional/non-functional requirements: FR-01–FR-13 and NFR-01–NFR-12.
- User stories: US-01–US-18.
- Screens: UI-01–UI-08.
- Functional tests: TC-F-01–TC-F-34; technical tests: TC-T-01–TC-T-26.

## 5. Build tasks — execute one task at a time

Every task below has its own copy-ready prompt. Keep code changes limited to the files listed, unless the task discovers a necessary dependency; report any extra file before editing it. The `TC-F` cases are manual/functional acceptance checks and remain `Not run` until explicitly executed. `TC-T` cases are automated technical checks; previously skipped checks should become active as the corresponding Step 15 modules and Streamlit dependency are implemented.

---

### BUILD-01 — Repository bootstrap and pinned environment

**Goal:** Create a clean, reproducible Python 3.12 repository skeleton and install the fixed dependency baseline.

**Files:** `requirements.txt`, `.python-version`, `.gitignore`, `README.md` (initial shell only), `src/__init__.py`, required empty folders (`pages/`, `src/`, `data/`, `docs/`, `tests/`, `.streamlit/`). Preserve all Step 10–13 assets.

**Stories / features:** Foundation for all stories; F-01–F-09.  
**Requirements:** NFR-07, NFR-09, NFR-12; all BR/US downstream.

**Exact prompt for the AI:**

```text
STEP 15 — BUILD-01 — Repository bootstrap for HRA-001.
Read docs/07_TRD.docx and docs/14_BUILD_PLAN.docx, plus the existing repository structure. Create the project skeleton and root requirements.txt using exactly these pins: streamlit==1.67.0, pandas==3.1.1, numpy==2.5.5, scipy==1.18.1, statsmodels==0.14.6, plotly==7.1.0, pytest==9.2.0. Set .python-version to 3.12. Create a conservative .gitignore for .venv, __pycache__, *.py[cod], .pytest_cache, .streamlit/secrets.toml, local logs and OS/editor files. Do not ignore data/app.db or the approved synthetic CSV/XLSX assets. Add src/__init__.py if missing. Do not implement app features yet and do not change existing schema, IDs, data or tests. Show the complete changed files and a concise diff summary.
```

**How to check:**

```powershell
python --version
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
pip check
python -c "import streamlit,pandas,numpy,scipy,statsmodels,plotly,pytest; print('imports OK')"
```

**Tests that must pass:** Environment/import smoke check; existing `pytest -q` should collect without dependency errors. It is acceptable for the already-documented Step 15 contract tests to remain skipped at this stage.

**Commit:** `git add . && git commit -m "BUILD-01: bootstrap Python project"`

---

### BUILD-02 — SQLite data loader and schema validation

**Goal:** Load the four approved tables and 40-column analysis view safely from `data/app.db` with inclusive date/department filters, explicit data types, cache keys and read-only application access.

**Files:** `src/db.py` (minimal additive `read_only` option if needed; never remove FK enforcement), `src/data_loader.py`, `src/validation.py`.

**Stories / features:** US-01, US-02, US-03; F-01.  
**BR / OQ:** BR-01–BR-11 as applicable; OQ-01–OQ-10 data dependencies.  
**Technical requirements:** FR-01, FR-12; NFR-02, NFR-03, NFR-05, NFR-06, NFR-09.

**Exact prompt for the AI:**

```text
STEP 15 — BUILD-02 — Implement the HRA-001 SQLite data-access layer.
Read docs/08_Database_Design.xlsx, docs/09_ER_Diagram.docx, docs/07_TRD.docx, src/db.py, src/generate_data.py, data/validation_report.txt and tests/test_data.py. Create src/data_loader.py and src/validation.py. Load departments, utilization_categories, patient_encounters, daily_utilization, vw_department_daily_analysis and data_quality_issues.csv. Use pathlib paths based on the repository root, parameterised SQL, explicit date/numeric conversion, short-lived connections, and st.cache_data with a documented 300-second TTL or dataset-version cache key. Include the selected date and department in every relevant cache key. Do not cache a global SQLite connection. Application connections must be read-only and must still be created through src.db.get_connection so PRAGMA foreign_keys remains enabled; add a read-only option to src/db.py only if needed and keep the generator able to create/write the database. Validate exact schema names/types, expected row counts and required columns. Inclusive date filters only. Never include the hospital root as a child department in totals. Do not alter database schema, raw files or test expectations. Implement clear, non-sensitive errors for missing DB/table/column. Show APIs and changed files.
```

**How to check:** Import each loader; load the four base tables and joined view; compare schema and row counts against Section 4; try empty and filtered date ranges; verify SQL values are bound parameters; verify new app connections are read-only and FK enforcement remains on.

**Tests that must pass:** TC-T-01–TC-T-10 and TC-T-13; TC-F-01 should pass when UI-06 is implemented, not before.

**Commit:** `git add src && git commit -m "BUILD-02: add validated SQLite data loader"`

---

### BUILD-03 — Cleaning pipeline and data-quality validation

**Goal:** Implement reproducible cleaning of raw synthetic extracts while preserving the raw files and producing a transparent issue summary.

**Files:** `src/cleaning.py`, `src/validation.py`, `data/README.md` (data handling notes; may be finalised in BUILD-15).

**Stories / features:** US-01, US-02, US-03, US-17; F-01, F-09.  
**BR / OQ:** BR-11; supports OQ-01–OQ-10 through reliable source data.  
**Tests:** TC-T-11, TC-T-12; later UI acceptance TC-F-28, TC-F-29, TC-F-34.

**Exact prompt for the AI:**

```text
STEP 15 — BUILD-03 — Implement HRA-001 data cleaning and quality reporting.
Read Step 10 raw CSV/XLSX assets, data/data_quality_issues.csv, data/validation_report.txt, docs/08_Database_Design.xlsx, docs/13_Test_Cases.docx, tests/test_data.py and tests/README.md. Create src/cleaning.py with the exact public contract clean_daily_utilization(raw_df) -> (cleaned_dataframe, issue_summary). The summary must include duplicates_removed, missing_values_repaired and outliers_flagged. Remove duplicate daily business keys (metric_date, dept_id, category_id) deterministically; repair missing used_amount values using a documented, defensible group-based fallback with a global fallback only when necessary; flag but do not silently erase high-use outliers (>150% of available_amount); preserve row lineage/issue counts. Provide equivalent checks for encounter duplicates and required fields without inventing medical content. Keep raw CSV/XLSX unchanged. Do not overwrite data/app.db: it is already the clean analytics snapshot. Use only synthetic data. Make all cleaned output types and keys conform to Step 8. Do not change tests to make them pass. Show the issue summary format and changed files.
```

**How to check:** Run the cleaner twice on the same inputs and confirm deterministic outputs; reconcile missing, duplicate and outlier totals to the Step 10 validation report; inspect that raw source files remain unchanged and clean DB row counts still match.

**Tests that must pass:** TC-T-11, TC-T-12, TC-T-08, TC-T-09, TC-T-10; TC-F-34's cleaning/error path is exercised in the full integration pass.

**Commit:** `git add src data/README.md && git commit -m "BUILD-03: add deterministic data cleaning and quality checks"`

---

### BUILD-04 — KPI, analysis and statistics functions

**Goal:** Implement all reusable formulas and statistical functions independently of the UI, with one public test-compatible API.

**Files:** `src/metrics.py`, `src/statistics.py`, `src/analysis.py` (public facade matching tests), optionally `src/filters.py` if a pure filter helper is needed.

**Stories / features:** US-06–US-13, US-14–US-16, US-18; F-03, F-04, F-05, F-06, F-07, F-08, F-09.  
**BR / OQ:** BR-01–BR-10 and BR-12; OQ-01–OQ-10.  
**Tests:** TC-T-14–TC-T-23.

**Exact prompt for the AI:**

```text
STEP 15 — BUILD-04 — Implement HRA-001 analytical functions.
Read docs/05_BRD.docx business rules RULE-01 to RULE-08, docs/08_Database_Design.xlsx KPIs_Measures, docs/07_TRD.docx statistical-method section, docs/11_User_Stories.docx acceptance criteria and tests/test_analysis.py. Implement reusable functions in src/metrics.py and src/statistics.py, and expose the exact names/signatures used by tests through src/analysis.py: bed_occupancy_rate(occupied_bed_days, available_bed_days), available_beds(usable_capacity, occupied_beds), staff_utilization_rate(used_hours, available_hours), resource_utilization_rate(used_amount, available_amount), count_admissions(df,start_date,end_date,department=None), count_discharges(...), average_length_of_stay(...), admissions_by_period(...,frequency='D'), is_threshold_breach(occupancy_pct,threshold_pct), descriptive_statistics(series), pearson_correlation(x,y), detect_iqr_outliers(series). Use weighted bed-day formulas; inclusive date boundaries; count unique encounter IDs by event date; exclude OPEN encounters from ALOS; preserve daily/weekly/monthly chronology; return None/N/A for zero denominators; threshold rule is strictly greater-than; never aggregate unlike resource units. Document missing/constant/invalid-data behaviour. Keep UI code out of these modules. Do not modify tests. Run all TC-T-14–TC-T-23 and show results.
```

**How to check:** Run `python -m pytest tests/test_analysis.py -q`; manually reconcile a selected view sample against Step 8 KPI formulas; check weighted totals rather than average percentages.

**Tests that must pass:** TC-T-14–TC-T-23; TC-F-07–TC-F-18 and TC-F-21–TC-F-24 are UI-level follow-up checks.

**Commit:** `git add src && git commit -m "BUILD-04: add tested KPI and statistics functions"`

---

### BUILD-05 — Shared UI components, global filters and multipage shell

**Goal:** Build the shared Streamlit shell and make all eight destinations navigable using the stable screen IDs, shared filter state and reusable visual components.

**Files:** `app.py`, `src/ui.py`, `src/filters.py`, `src/charts.py`, `pages/01_Overview.py` and placeholder page scripts for UI-02–UI-08 (the later page tasks replace placeholders).

**Stories / features:** US-04, US-05, US-18; F-02, F-09.  
**BR / OQ:** BR-01–BR-11; all OQs affected by filters.  
**Tests:** TC-F-02–TC-F-06, TC-F-31–TC-F-33; TC-T-24 and page smoke portions of TC-T-25.

**Exact prompt for the AI:**

```text
STEP 15 — BUILD-05 — Implement the HRA-001 shared Streamlit app shell.
Read docs/07_TRD.docx, docs/12_UI_Framework.docx, src/ui.py, .streamlit/config.toml and tests/test_app.py. Use st.Page and st.navigation from app.py, with UI-01 as the default Overview and these exact page paths required by tests: pages/02_Patient_Flow_Trend.py, pages/03_Department_Resource_Compare.py, pages/04_EDA_Statistics.py, pages/05_Insights_Threshold_Monitor.py, pages/06_Data_Explorer_Downloads.py, pages/07_Data_Quality.py, pages/08_About_Metric_Definitions.py. Create simple title-only placeholders for pages not yet implemented so navigation works at this stage. Retain/verify the Tailwind iframe helpers in src/ui.py; use only trusted static HTML and HTML-escape dynamic values. Use the exact session_state keys hra_global_date_range and hra_global_department on every analytical page. Implement shared filter helpers in src/filters.py and shared Plotly chart-card helpers in src/charts.py. Native Streamlit widgets must remain keyboard accessible. Set page config and theme once. Do not redesign UI IDs or change test page filenames. Ensure `AppTest.from_file(app.py)` has a title/header and no exception.
```

**How to check:** Open all eight navigation destinations locally; date and department values persist when moving between pages; verify mobile sidebar collapse and no page has missing placeholder path.

**Tests that must pass:** TC-F-02, TC-F-03, TC-F-04, TC-F-05, TC-F-06, TC-F-31, TC-F-32, TC-F-33, TC-T-24; page placeholders must at least pass the smoke portion of TC-T-25.

**Commit:** `git add app.py pages src .streamlit && git commit -m "BUILD-05: add shared Streamlit shell and filters"`

---

### BUILD-06 — UI-01 Overview / KPIs

**Goal:** Deliver the hospital-wide landing page with weighted occupancy, available-bed snapshot, admissions/discharges, trend and department summary.

**Files:** `pages/01_Overview.py`, `app.py` only if default-page wiring is necessary.

**Stories / features:** US-04, US-05, US-06, US-08, US-18; F-02, F-03, F-09.  
**BR / OQ:** BR-01, BR-02, BR-03, BR-06, BR-10, BR-11; OQ-01, OQ-03, OQ-06, OQ-10.  
**Tests:** TC-F-03–TC-F-09, TC-F-19, TC-F-20, TC-F-32, TC-F-33; TC-T-24.

**Exact prompt for the AI:**

```text
STEP 15 — BUILD-06 — Build UI-01 Overview / KPIs for HRA-001.
Read docs/12_UI_Framework.docx UI-01 wireframe, docs/05_BRD.docx BR-01/02/03/06/10/11, docs/08_Database_Design.xlsx KPI definitions, docs/11_User_Stories.docx US-04/05/06/08/18, and existing src/data_loader.py, src/analysis.py, src/ui.py. Implement pages/01_Overview.py using the shared inclusive date and department filters. Show a weighted period bed-occupancy KPI, date-specific available-bed KPI, admission/discharge totals, occupancy time-series line, capacity summary and department table. All departments must aggregate the five child departments only and exclude the hospital root. Display selected date range, denominator note, units and synthetic-data label. Use safe no-data states and the reusable KPI/Plotly components. Do not calculate occupancy as a simple mean of daily rates and do not add clinical recommendations.
```

**How to check:** Compare headline occupancy to 675/900 = 75.00% fixture; test selected dates; verify same metric across overview and compare pages; test All departments does not double-count root.

**Tests that must pass:** TC-F-03–TC-F-09, TC-F-19, TC-F-20, TC-F-32, TC-F-33, TC-T-24.

**Commit:** `git add app.py pages src && git commit -m "BUILD-06: build UI-01 overview KPIs"`

---

### BUILD-07 — UI-02 Patient Flow & Trends

**Goal:** Present admissions, discharges, ALOS and daily/weekly/monthly admission patterns using consistent event dates.

**Files:** `pages/02_Patient_Flow_Trend.py`.

**Stories / features:** US-03, US-04, US-09, US-10, US-11, US-16, US-18; F-01, F-02, F-04, F-08, F-09.  
**BR / OQ:** BR-03, BR-04, BR-05, BR-10, BR-11; OQ-03, OQ-04, OQ-05, OQ-10.  
**Tests:** TC-F-10–TC-F-13, TC-F-18, TC-F-21, TC-F-32, TC-F-33; TC-T-25.

**Exact prompt for the AI:**

```text
STEP 15 — BUILD-07 — Build UI-02 Patient Flow & Trends for HRA-001.
Read the UI-02 screen definition in docs/12_UI_Framework.docx, BR-03/04/05/10 business rules in docs/05_BRD.docx, US-03/04/09/10/11/16/18 in docs/11_User_Stories.docx, and src/data_loader.py + src/analysis.py. Build pages/02_Patient_Flow_Trend.py. Use the shared date/department filters. Count unique admissions by admission_date and discharges by discharge_date; do not count OPEN encounters as discharges. Show grouped admissions/discharges as clustered columns, an admission trend line with Daily/Weekly/Monthly selector, ALOS KPI and discharge count, and encounter-level LOS box plot by department. Use the same inclusive date boundaries across components, chronological bucket labels, explicit day/count units, and a clear empty-data message. Never display real patient information; encounter_code is synthetic only.
```

**How to check:** Reconcile four admission buckets to four encounters; ALOS fixture with 2- and 4-day discharged stays = 3 days; OPEN record excluded; use daily, weekly and monthly selectors.

**Tests that must pass:** TC-F-10–TC-F-13, TC-F-18, TC-F-21, TC-F-32, TC-F-33, TC-T-25.

**Commit:** `git add pages/02_Patient_Flow_Trend.py && git commit -m "BUILD-07: build UI-02 patient flow and trends"`

---

### BUILD-08 — UI-03 Department & Resource Compare

**Goal:** Compare occupancy, bed capacity, staff roles and resource categories across departments without mixing denominators or units.

**Files:** `pages/03_Department_Resource_Compare.py`.

**Stories / features:** US-02, US-05, US-07, US-08, US-12, US-13, US-16, US-18; F-01, F-02, F-03, F-05, F-06, F-08, F-09.  
**BR / OQ:** BR-02, BR-06, BR-07, BR-08, BR-10, BR-11; OQ-02, OQ-06, OQ-07, OQ-08, OQ-10.  
**Tests:** TC-F-08, TC-F-09, TC-F-14, TC-F-15, TC-F-18, TC-F-22, TC-F-31–TC-F-33; TC-T-25.

**Exact prompt for the AI:**

```text
STEP 15 — BUILD-08 — Build UI-03 Department & Resource Compare for HRA-001.
Read UI-03 in docs/12_UI_Framework.docx, KPI-02/KPI-06/KPI-07/KPI-08/KPI-10 in docs/08_Database_Design.xlsx, US-02/05/07/08/12/13/16/18 and their acceptance criteria in docs/11_User_Stories.docx. Implement pages/03_Department_Resource_Compare.py using global date/department context plus a local measure/category selector. Include sorted horizontal department occupancy bars, available-versus-occupied bed summary, grouped staff-role utilisation bars (DOCTOR/NURSE/TECHNICIAN), resource-type heatmap (ICU_VENTILATOR/OPERATING_ROOM/DIAGNOSTIC_IMAGING) and a comparison table. Each category uses its own numerator, denominator and unit; do not combine unrelated resource types. Occupancy comparisons use the same weighted bed-day denominator and date range. Return N/A for zero denominators and show negative capacity gaps as quality exceptions. Add no-data states.
```

**How to check:** Fixtures: doctors 72/90 = 80%; nurses 140/200 = 70%; technicians 30/50 = 60%; resources remain separate; ranked occupancy uses a common period and weighted denominator.

**Tests that must pass:** TC-F-08, TC-F-09, TC-F-14, TC-F-15, TC-F-18, TC-F-22, TC-F-31–TC-F-33, TC-T-25.

**Commit:** `git add pages/03_Department_Resource_Compare.py && git commit -m "BUILD-08: build UI-03 department and resource comparison"`

---

### BUILD-09 — UI-04 EDA & Statistics

**Goal:** Offer descriptive exploratory analysis, distributions, outlier views and relationships for approved synthetic measures.

**Files:** `pages/04_EDA_Statistics.py`.

**Stories / features:** US-10, US-11, US-12, US-13, US-17, US-18; F-04, F-05, F-06, F-09.  
**BR / OQ:** BR-04, BR-05, BR-07, BR-08, BR-11; supporting evidence for OQ-01–OQ-10.  
**Tests:** TC-F-11–TC-F-15, TC-F-23, TC-F-34; TC-T-22, TC-T-23, TC-T-25.

**Exact prompt for the AI:**

```text
STEP 15 — BUILD-09 — Build UI-04 EDA & Statistics for HRA-001.
Read UI-04 in docs/12_UI_Framework.docx, TRD statistical methods, BRD scope/limitations and tests/test_analysis.py. Implement pages/04_EDA_Statistics.py using cleaned synthetic analysis data and the shared global filters. Provide metric selector, histogram, box plot, descriptive summary (count, mean, median, sample standard deviation, quartiles where useful) and correlation view where the data are suitable. Use the central statistics functions from src/statistics.py / src/analysis.py; do not duplicate formulas in the page. Exclude OPEN encounters from LOS distribution. Handle empty, constant, missing and low-sample data without uncaught exceptions. Explain that correlation is descriptive and does not imply causation. Do not display diagnoses or real patient data.
```

**How to check:** Select occupancy, LOS, staff utilisation and resource utilisation; confirm summary statistics use cleaned values; constant/empty series show clear explanations; correlation labels name both variables.

**Tests that must pass:** TC-F-11–TC-F-15, TC-F-23, TC-F-34, TC-T-22, TC-T-23, TC-T-25.

**Commit:** `git add pages/04_EDA_Statistics.py && git commit -m "BUILD-09: build UI-04 EDA and statistics"`

---

### BUILD-10 — UI-06 Data Explorer & Downloads

**Goal:** Give a transparent, read-only preview of all four base tables with safe CSV and XLSX exports.

**Files:** `pages/06_Data_Explorer_Downloads.py`.

**Stories / features:** US-01, US-02, US-03; F-01.  
**BR / OQ:** BR-11; auditability support for OQ-01–OQ-10.  
**Tests:** TC-F-01, TC-F-25–TC-F-27, TC-F-34; TC-T-25.

**Exact prompt for the AI:**

```text
STEP 15 — BUILD-10 — Build UI-06 Data Explorer & Downloads for HRA-001.
Read UI-06 in docs/12_UI_Framework.docx, Step 8 table dictionaries, Step 10 dataset workbook/CSV files and tests/test_app.py/test cases TC-F-01 and TC-F-25–TC-F-27. Implement pages/06_Data_Explorer_Downloads.py. Offer a selector for departments, utilization_categories, patient_encounters and daily_utilization; show row count, schema/header and a bounded preview. Provide one CSV download per selected table and one XLSX export with a named sheet per table. Use the clean SQLite tables for the operational preview; clearly label the raw synthetic workbook separately if it is made available for audit. No writes to SQLite. Ensure exported files have correct headers and are valid files, not HTML/error output. Keep encounter details synthetic and limited to schema fields.
```

**How to check:** Compare selector row counts and headers to SQLite; download each CSV; open XLSX and verify four sheets, correct headers and row counts.

**Tests that must pass:** TC-F-01, TC-F-25, TC-F-26, TC-F-27, TC-F-34, TC-T-25.

**Commit:** `git add pages/06_Data_Explorer_Downloads.py && git commit -m "BUILD-10: build UI-06 data explorer and exports"`

---

### BUILD-11 — UI-05 Insights & Threshold Monitor

**Goal:** Show occupancy threshold breaches and governance context with transparent non-clinical wording.

**Files:** `pages/05_Insights_Threshold_Monitor.py`.

**Stories / features:** US-14, US-15, US-16; F-07, F-08.  
**BR / OQ:** BR-09, BR-10, BR-12; OQ-09, OQ-10.  
**Tests:** TC-F-16–TC-F-18, TC-F-24; TC-T-21, TC-T-25.

**Exact prompt for the AI:**

```text
STEP 15 — BUILD-11 — Build UI-05 Insights & Threshold Monitor for HRA-001.
Read UI-05 in docs/12_UI_Framework.docx, BR-09/BR-12 and RULE-07 in docs/05_BRD.docx, threshold columns in docs/08_Database_Design.xlsx, and US-14/15/16 acceptance criteria. Implement pages/05_Insights_Threshold_Monitor.py using the shared filters. Show occupancy time series with a threshold reference line, breach markers, breach-only toggle, department/date breach table, and threshold value/scope/owner/approval/effective dates. Use strict greater-than comparison: 85.01% breaches 85%, exactly 85.00% does not. Label the current 85% threshold as ASSUMED / academic assumption unless approval_status says otherwise. Keep language non-clinical; this page highlights records for operational review and does not signal clinical urgency or recommend treatment.
```

**How to check:** Known values 85.01, 85.00 and 84.99 against 85.00; toggle breach-only; verify effective dates and status display; confirm date/department selection is consistent.

**Tests that must pass:** TC-F-16, TC-F-17, TC-F-18, TC-F-24, TC-T-21, TC-T-25.

**Commit:** `git add pages/05_Insights_Threshold_Monitor.py && git commit -m "BUILD-11: build UI-05 threshold insights"`

---

### BUILD-12 — UI-07 Data Quality

**Goal:** Expose raw-versus-clean row counts, missingness, duplicates, outliers, repairs and quality issue filters.

**Files:** `pages/07_Data_Quality.py`, `src/cleaning.py`, `src/data_loader.py` only for small integration fixes.

**Stories / features:** US-17, US-18; F-09.  
**BR / OQ:** BR-11; supports data consistency for OQ-10 and the whole dashboard.  
**Tests:** TC-F-28, TC-F-29, TC-F-32–TC-F-34; TC-T-11, TC-T-12, TC-T-25.

**Exact prompt for the AI:**

```text
STEP 15 — BUILD-12 — Build UI-07 Data Quality for HRA-001.
Read UI-07 in docs/12_UI_Framework.docx, US-17/18 acceptance criteria, Step 10 data_quality_issues.csv and validation_report.txt, src/cleaning.py and tests/test_data.py. Implement pages/07_Data_Quality.py. Show quality KPI cards for raw missing values, duplicate rows, outliers flagged, rows repaired/removed, and final clean row counts. Show issue counts by source table and issue type, a filterable issue log and clear before/after status. Support table and issue-type filters. Reconcile counts to Step 10: 281 missing used_amount values, 3 exact duplicate records, 6 high-use outliers, without claiming these are defects in the clean SQLite tables. The clean database must continue to pass PK/FK/range checks. Use the same shared filter state where date/department context applies. Avoid exposing raw stack traces.
```

**How to check:** Reconcile quality cards with the quality issue log and validation report; filter table=daily_utilization and issue=missing; clearing filters restores totals; raw data issues do not leak into the clean database.

**Tests that must pass:** TC-F-28, TC-F-29, TC-F-32, TC-F-33, TC-F-34, TC-T-11, TC-T-12, TC-T-25.

**Commit:** `git add pages/07_Data_Quality.py src && git commit -m "BUILD-12: build UI-07 data quality"`

---

### BUILD-13 — UI-08 About & Metric Definitions

**Goal:** Explain scope, data provenance, metric formulas, assumptions, threshold status and non-clinical limitations.

**Files:** `pages/08_About_Metric_Definitions.py`.

**Stories / features:** US-15, US-18; F-07, F-09.  
**BR / OQ:** BR-11, BR-12; define interpretation for OQ-01–OQ-10.  
**Tests:** TC-F-17, TC-F-30–TC-F-32; TC-T-25.

**Exact prompt for the AI:**

```text
STEP 15 — BUILD-13 — Build UI-08 About & Metric Definitions for HRA-001.
Read the approved scope and formulas in docs/01_Project_Understanding.docx, docs/05_BRD.docx and docs/08_Database_Design.xlsx, and UI-08 in docs/12_UI_Framework.docx. Implement pages/08_About_Metric_Definitions.py. Include a short project summary, hypothetical hospital disclaimer, synthetic-only data notice, all KPI formulas and units, date/denominator conventions, definition of open/discharged encounters, threshold owner/scope/status/effective dates, 85% assumption warning, refresh/version information and out-of-scope limitations. Explicitly state that the dashboard is an academic descriptive-analytics prototype, not a clinical decision-support or hospital transaction system. Do not make claims about real hospital outcomes. Keep page text aligned with the BRD.
```

**How to check:** Compare formulas and assumptions against BRD and Step 8; open About page; verify synthetic and non-clinical notices are visible and readable on mobile.

**Tests that must pass:** TC-F-17, TC-F-30, TC-F-31, TC-F-32, TC-T-25.

**Commit:** `git add pages/08_About_Metric_Definitions.py && git commit -m "BUILD-13: build UI-08 about and metric definitions"`

---

### BUILD-14 — End-to-end integration, full tests and performance fixes

**Goal:** Integrate all modules/pages, remove placeholders, run the complete functional and technical suite, fix genuine defects and record evidence.

**Files:** `app.py`, `pages/*.py`, `src/*.py`, `tests/*.py` (change a test only if proven incorrect), `docs/04_Traceability_Matrix.xlsx`, `docs/13_Test_Cases.docx` (execution results only after tests are actually run).

**Stories / features:** US-01–US-18; F-01–F-09.  
**BR / OQ:** BR-01–BR-12; OQ-01–OQ-10.  
**Tests:** TC-F-01–TC-F-34; TC-T-01–TC-T-26.

**Exact prompt for the AI:**

```text
STEP 15 — BUILD-14 — Integrate and verify the complete HRA-001 application.
Read the complete project documents, BUILD_PLAN.md, the master RTM, tests/test_data.py, tests/test_analysis.py, tests/test_app.py and docs/13_Test_Cases.docx. Run `python -m pytest -q` and report every pass/fail/skip with the test ID. Then run the 34 functional cases TC-F-01–TC-F-34 manually against the app, using the exact fixtures and expected results in the test document; record evidence and date. Fix application code first. Do not weaken or delete a valid test; if you believe a test is wrong, explain the contradiction against BRD/Step 8/acceptance criteria and wait for approval before changing it. Verify all 8 pages render, global filters persist, no-data and exception cases are safe, exports open, and all metrics reconcile across pages. Measure first dashboard load against the TRD target (<5s for the agreed demo environment), typical filter rerun (<3s), and AppTest Overview target in TC-T-26 (<3s under its stated test environment). Check privacy, SQL parameterisation, iframe escaping, read-only DB access and mobile layout. Update RTM test mappings/status only from actual evidence; do not mark unrun tests as Pass. Return a defect list, fix summary and final test matrix.
```

**How to check:** Run `python -m pytest -q`; manually execute and sign off TC-F-01–TC-F-34; `streamlit run app.py`; verify all OQs; run `pip check`; inspect app on desktop and approximately 390px phone width.

**Tests that must pass:** All TC-T-01–TC-T-26 and all TC-F-01–TC-F-34. No `Not run`, `Blocked` or unexplained `Skipped` status may remain in the final test execution record. Record environment and evidence.

**Commit:** `git add . && git commit -m "BUILD-14: integrate and pass full test suite"`

---

### BUILD-15 — README, data guide and user/developer documentation

**Goal:** Make the repository independently understandable and reproducible for the student, mentor and evaluator.

**Files:** `README.md`, `data/README.md`, optionally `docs/README.md`, screenshots in `docs/screenshots/`.

**Stories / features:** Supports all stories and F-01–F-09.  
**BR / OQ:** BR-11 and all OQs through metric documentation.  
**Tests:** NFR-09, NFR-11, NFR-12; verify commands reproduce BUILD-01 and BUILD-14.

**Exact prompt for the AI:**

```text
STEP 15 — BUILD-15 — Write the HRA-001 README and data documentation.
Read all project documents, the final code, requirements.txt, validation_report.txt, the master RTM and the test execution record. Write a professional README.md with project summary, problem statement, stakeholder users, architecture, exact folder tree, technology stack, setup commands for Windows, run commands, test commands, screen descriptions, OQ-to-screen coverage, database schema summary, KPI formulas, synthetic-data patterns and quality issues, deployment URL placeholder until it exists, limitations, troubleshooting and academic disclaimer. Write data/README.md describing the four SQLite tables, the 40-column view, row counts, raw-vs-clean distinction, date coverage and how to regenerate the dataset with seed 42. Include screenshots only after they are captured from the actual working app. Do not claim deployment or test completion that has not been verified. Keep mentor name as pending unless supplied.
```

**How to check:** Follow README from a clean clone and fresh `.venv`; verify each path/command; verify claims agree with the actual test report, Step 8 schema and deployed status.

**Tests that must pass:** Re-run the setup and test commands from README; documentation accuracy review against RTM and source docs.

**Commit:** `git add README.md data/README.md docs && git commit -m "BUILD-15: document setup, data and application"`

---

### BUILD-16 — GitHub release and Streamlit Community Cloud deployment

**Goal:** Publish the tested app from the GitHub repository and verify the live URL without exposing secrets or real data.

**Files:** `app.py`, `requirements.txt`, `.python-version`, `.streamlit/config.toml`, `data/app.db`, `README.md`, any deployment-only fixes.

**Stories / features:** All Must stories; F-01–F-09.  
**BR / OQ:** BR-01–BR-12; OQ-01–OQ-10.  
**Tests:** All TC-F/TC-T; NFR-01, NFR-04, NFR-05, NFR-07, NFR-08, NFR-11, NFR-12.

**Exact prompt for the AI:**

```text
STEP 15 — BUILD-16 — Deploy HRA-001 to GitHub and Streamlit Community Cloud.
Read docs/07_TRD.docx deployment checklist, README.md, requirements.txt, .python-version, .streamlit/config.toml and the final test execution report. First confirm all tests pass locally and `pip check` is clean. Confirm the SQLite DB and all required synthetic assets are committed, the app uses read-only database access, and there are no credentials, secrets, personal data, temporary files or local virtual-environment contents in Git. Provide the exact Git status/add/commit/push commands. Deploy from the repository main branch with entrypoint app.py using Streamlit Community Cloud. In Advanced settings choose Python 3.12. After deployment, inspect build logs, open the public URL in a clean browser, verify UI-01–UI-08, global date/department filters, KPI values, downloads and synthetic-data notices. Do not claim success until the actual app URL is opened and the smoke check is recorded. Update README.md with the live URL and deployment date only after verification. Keep a local fallback and screenshots for academic submission.
```

**How to check:** Push to GitHub; create the Community Cloud app by selecting repository, branch `main`, entrypoint `app.py`; select Python 3.12 in Advanced settings; review deploy logs; open the deployed URL in a private/clean browser session; execute the post-deploy smoke checklist; save the verified URL.

**Tests that must pass:** All tests from BUILD-14 remain passing after deployment; repeat UI smoke checks on the live app; confirm the live deployment is not showing stale code and its data row counts match the local build.

**Commit:** `git add . && git commit -m "BUILD-16: deploy tested app and document live URL"`

---

## 6. Definition of Done (DoD)

The project is done only when every applicable item below is verified with evidence:

1. **Must business requirements:** BR-01, BR-02, BR-03, BR-06, BR-09, BR-10 and BR-11 meet their acceptance criteria. BR-04, BR-05, BR-07 and BR-08 are also implemented to answer all ten project OQs. BR-12 threshold metadata is implemented and labelled as an assumption until approved.
2. **Operational questions:** OQ-01 through OQ-10 can be answered from the generated synthetic data and visible in the application; the OQ-to-screen mapping is complete.
3. **Traceability:** Every BR has source HMW, user story, UI screen and at least one test reference in `docs/04_Traceability_Matrix.xlsx`. No orphan HMW/BR/OQ; all existing IDs remain unchanged.
4. **Data integrity:** Four base-table row counts match Step 10; exact schema/PK/FK/type checks pass; joined view has 1,825 rows × 40 columns; FK check returns zero violations; application DB connections enforce FK and are read-only.
5. **Cleaning:** Intentional raw quality issues are documented and counted; raw files remain preserved; clean database has no required-field nulls, duplicate fact keys or invalid range values.
6. **Metrics:** Weighted occupancy, available beds, event counts, ALOS, daily/weekly/monthly admission aggregation, staff/resource utilisation and threshold breaches match the BRD and tiny fixture tests.
7. **UI:** All eight screens exist and render; common filter state is preserved; empty results and errors are safe; mobile layout is readable; each chart has a title, labels, units and period context.
8. **Tests:** All TC-T-01–TC-T-26 pass and all TC-F-01–TC-F-34 are executed and marked with actual Pass/Fail evidence. No test is marked Pass without execution. Valid tests are not deleted or weakened to obtain a green result.
9. **Performance and quality:** Agreed demo environment demonstrates first load <5 seconds and typical filter rerun <3 seconds; AppTest target from TC-T-26 is recorded; `pip check` is clean.
10. **Documentation:** README setup works from a clean clone; data guide, all project documents, user stories, UI framework, test cases, final RTM and screenshots are present. PRD remains marked pending until Step 6 is completed.
11. **Deployment:** GitHub `main` is the source of truth; Streamlit Community Cloud app is publicly reachable at a verified URL; Python 3.12 and pinned dependencies are recorded; no secrets or personal data are committed.
12. **Handover:** Provide repo URL, live app URL, test report, known limitations and a local fallback package to the academic reviewer.

## 7. Commands — install, run, test and commit

### Clone (replace `<github-username>` with your GitHub username)

```bash
git clone https://github.com/<github-username>/2503201450005-hospital-resource-utilization-analysis.git
cd 2503201450005-hospital-resource-utilization-analysis
```

### Windows PowerShell setup

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
pip check
```

If PowerShell blocks activation, use Git Bash:

```bash
source .venv/Scripts/activate
```

### Run the app and tests

```bash
streamlit run app.py
python -m pytest -q
```

### Recreate the synthetic dataset only when needed

```bash
python src/generate_data.py
```

Do not regenerate the dataset during routine app runs; seed 42 makes generation reproducible, but regenerated output should be reviewed and committed as an intentional data-version change.

### Commit one build task at a time

```bash
git status
git add .
git commit -m "BUILD-XX: short task summary"
git push origin main
```

## 8. Ten likely viva questions with short answers

1. **What problem does HRA-001 solve?** It consolidates synthetic operational data so managers can examine bed capacity, patient flow, staff and shared-resource use consistently across dates and departments.
2. **Why is the application descriptive analytics and not a clinical system?** It summarises historical synthetic operations; it does not diagnose, predict patient outcomes, recommend treatment or assign resources.
3. **What is the difference between BRD and TRD?** BRD states what the business needs and how success is measured; TRD describes the technical architecture, modules, data access and quality constraints used to implement it.
4. **Why is the RTM important?** It links OQs, HMWs, BRs, features, database fields, user stories, UI screens and tests so requirements are not lost and can be verified.
5. **Why are there four base tables?** Departments and utilization categories are master/reference tables; patient encounters and daily utilization are event/fact tables with stable primary and foreign keys.
6. **Why is bed occupancy weighted?** The numerator and denominator are total occupied and available bed-days; averaging daily percentages would give small and large departments/days equal influence and can distort the overall rate.
7. **How is ALOS calculated?** For discharged encounters only, average the date difference between discharge and admission; open encounters are excluded and the project convention treats same-day stays as zero days.
8. **Why keep raw data-quality defects if the database is clean?** They demonstrate a repeatable cleaning process and make missingness, duplicates and outliers auditable without contaminating analytical metrics.
9. **What is the purpose of pytest and Streamlit AppTest?** pytest validates data integrity and calculation functions; AppTest checks that the Streamlit entry point and page scripts render without unhandled errors.
10. **How is the application deployed?** The code is pushed to GitHub, Streamlit Community Cloud is connected to the repository, `app.py` is selected as entrypoint with Python 3.12, and the live URL is smoke-tested.

## 9. Deployment references

- Streamlit Community Cloud deployment workflow: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy
- Community Cloud file organisation (root `requirements.txt`, `.streamlit/config.toml`, local app files): https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/file-organization
- Community Cloud Python version selection: https://docs.streamlit.io/deploy/streamlit-community-cloud/manage-your-app/upgrade-python
