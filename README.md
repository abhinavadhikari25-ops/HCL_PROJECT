# HRA-001 test suite

Run from the project root:

```bash
python -m pytest -q
```

## Current test status

The Step 13 authoring baseline currently yields **22 passed, 3 skipped** in the supplied workspace. The skips are intentional until Step 15:

- `src.cleaning.clean_daily_utilization(raw_df)` — expected return is `(cleaned_dataframe, issue_summary)` where the summary contains `duplicates_removed`, `missing_values_repaired`, and `outliers_flagged`.
- `src.analysis` — implement the functions referenced in `test_analysis.py` using the exact formulas and semantics shown by the tiny deterministic fixtures.
- Streamlit AppTest — install the pinned Streamlit dependency and implement `app.py` plus the page scripts listed in `test_app.py`.

The test contract deliberately fixes these interfaces before implementation so the code can be built to verifiable acceptance criteria in Step 15.

All source data and database fixtures must remain synthetic. Tests that exercise foreign-key failures use a temporary copy of `data/app.db` and never modify the project database.
