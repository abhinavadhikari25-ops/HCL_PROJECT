"""Data cleaning pipeline and quality validation for HRA-001."""
from __future__ import annotations

from typing import Any, Dict, Optional, Tuple
import pandas as pd
import numpy as np


def clean_daily_utilization(raw_df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Clean daily utilization extract deterministically.

    Steps:
      1. Remove exact/business-key duplicates on (metric_date, dept_id, category_id).
      2. Repair missing used_amount values using group median fallback (dept + category -> category -> 0.0).
      3. Flag high-use outliers (> 150% of available_amount) without discarding data lineage.

    Returns:
        (cleaned_dataframe, issue_summary)
    """
    df = raw_df.copy()

    # 1. Deduplication on composite business key
    key_cols = ["metric_date", "dept_id", "category_id"]
    dup_mask = df.duplicated(subset=key_cols, keep="first")
    duplicates_removed = int(dup_mask.sum())
    df = df[~dup_mask].copy()

    # 2. Repair missing used_amount
    missing_mask = df["used_amount"].isna()
    missing_count = int(missing_mask.sum())

    if missing_count > 0:
        # Group-based fallback: median of (dept_id, category_id)
        dept_cat_median = df.groupby(["dept_id", "category_id"])["used_amount"].transform("median")
        cat_median = df.groupby("category_id")["used_amount"].transform("median")
        global_median = df["used_amount"].median() if not df["used_amount"].dropna().empty else 0.0

        repaired = df["used_amount"].fillna(dept_cat_median).fillna(cat_median).fillna(global_median)
        df["used_amount"] = repaired.round(2)

    # 3. Detect and flag outliers (> 150% capacity)
    outlier_mask = (df["available_amount"] > 0) & (df["used_amount"] > df["available_amount"] * 1.5)
    outliers_flagged = int(outlier_mask.sum())
    df["is_high_use_outlier"] = outlier_mask.astype(int)

    # Enforce correct types
    df["available_amount"] = df["available_amount"].astype(float)
    df["used_amount"] = df["used_amount"].astype(float)
    if "dept_id" in df.columns:
        df["dept_id"] = df["dept_id"].astype(int)
    if "category_id" in df.columns:
        df["category_id"] = df["category_id"].astype(int)

    summary = {
        "raw_rows": len(raw_df),
        "cleaned_rows": len(df),
        "duplicates_removed": duplicates_removed,
        "missing_values_repaired": missing_count,
        "outliers_flagged": outliers_flagged,
    }
    return df, summary


def clean_encounters(raw_df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """Clean patient encounters extract."""
    df = raw_df.copy()
    dup_mask = df.duplicated(subset=["encounter_code"], keep="first")
    duplicates_removed = int(dup_mask.sum())
    df = df[~dup_mask].copy()

    summary = {
        "raw_rows": len(raw_df),
        "cleaned_rows": len(df),
        "duplicates_removed": duplicates_removed,
    }
    return df, summary
