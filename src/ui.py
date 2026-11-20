"""Shared UI helpers for HRA-001 Hospital Resource Utilization Analysis.

Tailwind is loaded only inside trusted, static HTML strings rendered with
Streamlit's st.iframe. All dynamic text is HTML-escaped before interpolation.
Do not pass user-provided HTML or raw database text as iframe markup.
"""

from __future__ import annotations

import html
from datetime import date
from typing import Any, Iterable, Mapping, Sequence

import streamlit as st


PROJECT_TITLE = "Hospital Resource Utilization Analysis"
PROJECT_TAGLINE = "Operational analytics | Synthetic academic dataset"

ACCENTS = {
    "teal": "border-teal-600",
    "navy": "border-slate-800",
    "amber": "border-amber-500",
    "slate": "border-slate-400",
}


def _safe(value: Any) -> str:
    """Escape dynamic values before inserting them into an HTML iframe."""
    return html.escape(str(value), quote=True)


def render_header(
    title: str = PROJECT_TITLE,
    subtitle: str = PROJECT_TAGLINE,
    status: str = "SYNTHETIC DATA",
) -> None:
    """Render the Tailwind-styled application header in a Streamlit iframe."""
    title_html = _safe(title)
    subtitle_html = _safe(subtitle)
    status_html = _safe(status)
    markup = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    html, body {{ margin: 0; padding: 0; background: transparent;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
  </style>
</head>
<body>
  <header class="rounded-2xl bg-slate-900 px-5 py-4 text-white shadow-sm">
    <div class="flex flex-wrap items-center justify-between gap-3">
      <div class="min-w-0">
        <p class="text-xs font-semibold uppercase tracking-[0.18em] text-teal-300">HRA-001 · ABES MCA Data Analytics</p>
        <h1 class="mt-1 text-xl font-bold leading-tight sm:text-2xl">{title_html}</h1>
        <p class="mt-1 text-sm text-slate-300">{subtitle_html}</p>
      </div>
      <span class="rounded-full border border-teal-300/40 bg-teal-400/10 px-3 py-1 text-xs font-bold tracking-wide text-teal-200">{status_html}</span>
    </div>
  </header>
</body>
</html>"""
    st.iframe(markup, height=126, alt=f"Application header: {title}")


def render_kpi_card(
    label: str,
    value: Any,
    delta: str | None = None,
    footnote: str | None = None,
    accent: str = "teal",
) -> None:
    """Render one Tailwind KPI card in an isolated iframe.

    `accent` is selected from a fixed allow-list; dynamic text is escaped.
    """
    accent_class = ACCENTS.get(accent, ACCENTS["teal"])
    label_html = _safe(label)
    value_html = _safe(value)
    delta_html = _safe(delta) if delta is not None else ""
    footnote_html = _safe(footnote) if footnote is not None else ""
    delta_block = (
        f'<p class="mt-2 text-xs font-semibold text-teal-700">{delta_html}</p>'
        if delta is not None else ""
    )
    footnote_block = (
        f'<p class="mt-2 text-xs text-slate-500">{footnote_html}</p>'
        if footnote is not None else ""
    )
    markup = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    html, body {{ margin: 0; padding: 0; background: transparent;
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; }}
  </style>
</head>
<body>
  <section class="h-full rounded-xl border border-slate-200 {accent_class} border-l-4 bg-white p-4 shadow-sm">
    <p class="text-xs font-semibold uppercase tracking-wide text-slate-500">{label_html}</p>
    <p class="mt-2 text-3xl font-bold tracking-tight text-slate-900">{value_html}</p>
    {delta_block}
    {footnote_block}
  </section>
</body>
</html>"""
    st.iframe(markup, height=142, alt=f"KPI card: {label}, value {value}")


def render_kpi_row(cards: Sequence[Mapping[str, Any]]) -> None:
    """Render up to four KPI cards in a responsive Streamlit column row.

    Each card mapping accepts: label, value, optional delta, footnote, accent.
    """
    if not cards:
        return
    columns = st.columns(min(4, len(cards)))
    for index, card in enumerate(cards):
        with columns[index % len(columns)]:
            render_kpi_card(
                label=card.get("label", "Metric"),
                value=card.get("value", "—"),
                delta=card.get("delta"),
                footnote=card.get("footnote"),
                accent=card.get("accent", "teal"),
            )


def render_global_filters(
    department_names: Iterable[str],
    min_date: date,
    max_date: date,
) -> dict[str, Any]:
    """Render shared sidebar filters using stable session-state keys.

    Call this function from each page with the same dataset date limits and
    department labels. Returns an inclusive date range and department scope.
    """
    if min_date > max_date:
        raise ValueError("min_date cannot be after max_date")

    departments = sorted({str(name) for name in department_names if str(name).strip()})
    all_label = "All departments"
    options = [all_label, *departments]

    if "hra_global_date_range" not in st.session_state:
        st.session_state["hra_global_date_range"] = (min_date, max_date)
    if "hra_global_department" not in st.session_state:
        st.session_state["hra_global_department"] = all_label
    elif st.session_state["hra_global_department"] not in options:
        st.session_state["hra_global_department"] = all_label

    st.sidebar.markdown("### Global filters")
    selected_dates = st.sidebar.date_input(
        "Reporting date range",
        min_value=min_date,
        max_value=max_date,
        key="hra_global_date_range",
        help="The selected start and end dates are inclusive.",
    )
    department = st.sidebar.selectbox(
        "Department scope",
        options=options,
        key="hra_global_department",
    )

    if isinstance(selected_dates, (tuple, list)) and len(selected_dates) == 2:
        date_range = (selected_dates[0], selected_dates[1])
    elif isinstance(selected_dates, date):
        date_range = (selected_dates, selected_dates)
    else:
        date_range = None

    return {
        "date_range": date_range,
        "department": None if department == all_label else department,
        "department_label": department,
    }
