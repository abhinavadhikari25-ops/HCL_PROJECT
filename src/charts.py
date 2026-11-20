"""Reusable Plotly chart builders for HRA-001."""
from __future__ import annotations

from typing import Any, Dict, List, Optional
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Color tokens from TRD & UI Framework
COLOR_NAVY = "#17365D"
COLOR_TEAL = "#0E86D4"
COLOR_AMBER = "#E38B29"
COLOR_SLATE = "#64748B"
COLOR_RED = "#DC2626"
COLOR_GREEN = "#16A34A"
COLOR_LIGHT_BG = "#F8FAFC"


def apply_standard_layout(fig: go.Figure, title: str, height: int = 400) -> go.Figure:
    """Apply consistent styling, typography, and responsive margins."""
    fig.update_layout(
        title={
            "text": f"<b>{title}</b>",
            "x": 0.02,
            "xanchor": "left",
            "font": {"size": 15, "color": "#0F172A", "family": "Segoe UI, sans-serif"},
        },
        height=height,
        margin={"l": 40, "r": 30, "t": 50, "b": 40},
        plot_bgcolor="#FFFFFF",
        paper_bgcolor="#FFFFFF",
        font={"family": "Segoe UI, Inter, sans-serif", "size": 12, "color": "#334155"},
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "right", "x": 1},
        hovermode="x unified",
    )
    fig.update_xaxes(showgrid=True, gridwidth=1, gridcolor="#F1F5F9", zeroline=False)
    fig.update_yaxes(showgrid=True, gridwidth=1, gridcolor="#F1F5F9", zeroline=False)
    return fig


def plot_occupancy_trend(
    df: pd.DataFrame,
    date_col: str = "metric_date",
    rate_col: str = "occupancy_rate_pct",
    threshold: float = 85.0,
    title: str = "Bed Occupancy Trend vs Threshold",
) -> go.Figure:
    """Plot time-series occupancy rate with an 85% warning threshold line."""
    fig = go.Figure()

    if not df.empty:
        fig.add_trace(
            go.Scatter(
                x=df[date_col],
                y=df[rate_col],
                mode="lines",
                name="Occupancy Rate (%)",
                line={"color": COLOR_TEAL, "width": 2.5},
                hovertemplate="%{x|%Y-%m-%d}<br>Occupancy: %{y:.1f}%<extra></extra>",
            )
        )

        # Highlight breaches
        breaches = df[df[rate_col] > threshold]
        if not breaches.empty:
            fig.add_trace(
                go.Scatter(
                    x=breaches[date_col],
                    y=breaches[rate_col],
                    mode="markers",
                    name="Threshold Breach (>85%)",
                    marker={"color": COLOR_RED, "size": 7, "symbol": "circle"},
                    hovertemplate="%{x|%Y-%m-%d}<br>Breach: %{y:.1f}%<extra></extra>",
                )
            )

    # Reference line for 85% threshold
    fig.add_hline(
        y=threshold,
        line_dash="dash",
        line_color=COLOR_RED,
        line_width=1.8,
        annotation_text=f"Assumed Threshold ({threshold:.0f}%)",
        annotation_position="top right",
        annotation_font_color=COLOR_RED,
    )
    fig.update_yaxes(range=[0, max(100.0, df[rate_col].max() + 5 if not df.empty else 100.0)])
    return apply_standard_layout(fig, title)


def plot_patient_flow(df: pd.DataFrame, title: str = "Patient Admissions vs Discharges") -> go.Figure:
    """Clustered bar chart of daily admissions and discharges."""
    fig = go.Figure()
    if not df.empty:
        fig.add_trace(
            go.Bar(
                x=df["metric_date"],
                y=df["admissions"],
                name="Admissions",
                marker_color=COLOR_NAVY,
            )
        )
        fig.add_trace(
            go.Bar(
                x=df["metric_date"],
                y=df["discharges"],
                name="Discharges",
                marker_color=COLOR_AMBER,
            )
        )
    fig.update_layout(barmode="group")
    return apply_standard_layout(fig, title)


def plot_department_occupancy_bars(
    dept_df: pd.DataFrame,
    threshold: float = 85.0,
    title: str = "Department Bed Occupancy Ranking",
) -> go.Figure:
    """Horizontal sorted bar chart of department occupancy rates."""
    fig = go.Figure()
    if not dept_df.empty:
        sorted_df = dept_df.sort_values("occupancy_rate_pct", ascending=True)
        colors = [COLOR_RED if x > threshold else COLOR_TEAL for x in sorted_df["occupancy_rate_pct"]]

        fig.add_trace(
            go.Bar(
                y=sorted_df["dept_name"],
                x=sorted_df["occupancy_rate_pct"],
                orientation="h",
                marker_color=colors,
                text=[f"{x:.1f}%" for x in sorted_df["occupancy_rate_pct"]],
                textposition="auto",
                hovertemplate="%{y}<br>Occupancy: %{x:.1f}%<extra></extra>",
            )
        )
        fig.add_vline(x=threshold, line_dash="dash", line_color=COLOR_RED)
    fig.update_xaxes(title="Occupancy Rate (%)", range=[0, 105])
    return apply_standard_layout(fig, title)


def plot_staff_utilization_bars(
    staff_df: pd.DataFrame,
    title: str = "Staff Utilization by Role & Department",
) -> go.Figure:
    """Grouped bar chart comparing Doctor, Nurse, Technician utilization."""
    fig = go.Figure()
    if not staff_df.empty:
        for role, col, color in [
            ("Doctor", "doctor_utilization_pct", COLOR_NAVY),
            ("Nurse", "nurse_utilization_pct", COLOR_TEAL),
            ("Technician", "technician_utilization_pct", COLOR_AMBER),
        ]:
            if col in staff_df.columns:
                fig.add_trace(
                    go.Bar(
                        x=staff_df["dept_name"],
                        y=staff_df[col],
                        name=role,
                        marker_color=color,
                        text=[f"{v:.0f}%" if pd.notna(v) else "N/A" for v in staff_df[col]],
                        textposition="auto",
                    )
                )
    fig.update_layout(barmode="group")
    fig.update_yaxes(title="Utilization (%)", range=[0, 105])
    return apply_standard_layout(fig, title)


def plot_los_distribution(encounters_df: pd.DataFrame, title: str = "Length of Stay Distribution (Days)") -> go.Figure:
    """Box plot of LOS across departments for discharged encounters."""
    fig = go.Figure()
    discharged = encounters_df[encounters_df["encounter_status"] == "DISCHARGED"].copy()
    if not discharged.empty:
        adm = pd.to_datetime(discharged["admission_date"])
        dis = pd.to_datetime(discharged["discharge_date"])
        discharged["los_days"] = (dis - adm).dt.days

        fig = px.box(
            discharged,
            x="dept_name",
            y="los_days",
            color="dept_name",
            color_discrete_sequence=[COLOR_NAVY, COLOR_TEAL, COLOR_AMBER, COLOR_SLATE, "#059669"],
            points="outliers",
        )
        fig.update_layout(showlegend=False)
    return apply_standard_layout(fig, title)
