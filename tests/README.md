# HRA-001 Test Suite

## Running Tests
Run from the project root:
```bash
pytest tests/ -v
```

## Structure
- `tests/test_data.py`: Schema validation, row count verification, foreign key integrity checks, and data cleaning contract tests.
- `tests/test_analysis.py`: Analytical and KPI formula contracts (weighted bed occupancy, ALOS, staff/resource utilization, statistics).
- `tests/test_app.py`: Streamlit AppTest smoke and multipage rendering checks.
