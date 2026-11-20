"""Descriptive and exploratory statistics for HRA-001."""
from __future__ import annotations

from typing import Any, Dict, Optional, Sequence, Union
import numpy as np
import pandas as pd


def descriptive_statistics(series: Union[pd.Series, Sequence[float]]) -> Dict[str, Any]:
    """Calculate sample descriptive statistics for a numeric series."""
    s = pd.Series(series, dtype=float).dropna()
    if s.empty:
        return {
            "count": 0,
            "mean": None,
            "median": None,
            "std": None,
            "min": None,
            "max": None,
            "q25": None,
            "q75": None,
            "iqr": None,
        }

    q25 = float(s.quantile(0.25))
    q75 = float(s.quantile(0.75))
    std_val = float(s.std(ddof=1)) if len(s) > 1 else 0.0

    return {
        "count": int(len(s)),
        "mean": float(s.mean()),
        "median": float(s.median()),
        "std": std_val,
        "min": float(s.min()),
        "max": float(s.max()),
        "q25": q25,
        "q75": q75,
        "iqr": float(q75 - q25),
    }


def pearson_correlation(x: Sequence[float], y: Sequence[float]) -> Optional[float]:
    """Calculate sample Pearson correlation coefficient."""
    s1 = pd.Series(x, dtype=float)
    s2 = pd.Series(y, dtype=float)
    valid = pd.DataFrame({"x": s1, "y": s2}).dropna()
    if len(valid) < 2:
        return None
    if valid["x"].nunique() <= 1 or valid["y"].nunique() <= 1:
        return None
    corr = valid["x"].corr(valid["y"])
    return float(corr) if not np.isnan(corr) else None


def detect_iqr_outliers(series: Union[pd.Series, Sequence[float]]) -> pd.Series:
    """Identify extreme values using Tukey's IQR rule (Q1 - 1.5*IQR, Q3 + 1.5*IQR)."""
    s = pd.Series(series, dtype=float).dropna()
    if len(s) < 4:
        return pd.Series([], dtype=float)
    q25 = s.quantile(0.25)
    q75 = s.quantile(0.75)
    iqr = q75 - q25
    lower_bound = q25 - 1.5 * iqr
    upper_bound = q75 + 1.5 * iqr
    return s[(s < lower_bound) | (s > upper_bound)]
