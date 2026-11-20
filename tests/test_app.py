"""Streamlit AppTest smoke, multipage rendering and performance checks.

The app/page scripts are implementation deliverables for Step 15. Page file names
are fixed here to make the UI acceptance contract unambiguous.
"""
from __future__ import annotations

import time
from pathlib import Path

import pytest

streamlit = pytest.importorskip("streamlit", reason="Streamlit is installed/configured with the Step 15 application")
from streamlit.testing.v1 import AppTest

ROOT = Path(__file__).resolve().parents[1]
HOME_APP = ROOT / "app.py"
PAGES = {
    "UI-02": ROOT / "pages" / "02_Patient_Flow_Trend.py",
    "UI-03": ROOT / "pages" / "03_Department_Resource_Compare.py",
    "UI-04": ROOT / "pages" / "04_EDA_Statistics.py",
    "UI-05": ROOT / "pages" / "05_Insights_Threshold_Monitor.py",
    "UI-06": ROOT / "pages" / "06_Data_Explorer_Downloads.py",
    "UI-07": ROOT / "pages" / "07_Data_Quality.py",
    "UI-08": ROOT / "pages" / "08_About_Metric_Definitions.py",
}


def _run_script(path: Path, timeout: float = 3.0):
    assert path.exists(), f"Expected application/page script is missing: {path}"
    return AppTest.from_file(str(path)).run(timeout=timeout)


def test_home_overview_app_starts_without_exception():
    at = _run_script(HOME_APP)
    assert not at.exception
    assert len(at.title) + len(at.header) + len(at.subheader) > 0


@pytest.mark.parametrize("ui_id,page_path", list(PAGES.items()))
def test_every_multipage_screen_renders(ui_id, page_path):
    at = _run_script(page_path)
    assert not at.exception, f"{ui_id} failed: {at.exception}"
    assert len(at.title) + len(at.header) + len(at.subheader) > 0


def test_overview_app_render_time_is_under_three_seconds():
    start = time.perf_counter()
    at = _run_script(HOME_APP, timeout=3.0)
    elapsed = time.perf_counter() - start
    assert not at.exception
    assert elapsed < 3.0, f"Overview render took {elapsed:.3f}s (target < 3.0s)"
