from __future__ import annotations

import numpy as np
import pandas as pd

from .dvf_utils import PROCESSED_DIR, TABLES_DIR, ensure_project_dirs


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalizes column names to lowercase snake_case."""
    result = df.copy()
    result.columns = (
        result.columns.str.strip()
        .str.lower()
        .str.replace(" ", "_", regex=False)
        .str.replace("'", "_", regex=False)
    )
    return result


def missing_report(df: pd.DataFrame) -> pd.DataFrame:
    """Generates a summary dataframe tracking missing data rates."""
    return (
        pd.DataFrame(
            {
                "column": df.columns,
                "missing_count": df.isna().sum().values,
                "missing_rate": (df.isna().mean().values * 100).round(2),
                "dtype": [str(dtype) for dtype in df.dtypes],
            }
        )
        .sort_values(["missing_rate", "missing_count"], ascending=False)
        .reset_index(drop=True)
    )


def french_number_to_float(series: pd.Series) -> pd.Series:
    """Converts French formatted numbers (using commas) to standard floats."""
    return pd.to_numeric(series.astype("string").str.replace(",", ".", regex=False), errors="coerce")


def clean_dvf(df: pd.DataFrame, missing_threshold: float = 80.0) -> tuple[pd.DataFrame, dict]:
    """Runs the complete data cleaning pipeline on raw DVF data."""
    cleaned = normalize_columns(df)
    summary: dict[str, object] = {
        "input_rows": len(cleaned),
        "input_columns": len(cleaned.columns),
    }

    # Drop high missing values
    report = missing_report(cleaned)
    high_missing = report.loc[report["missing_rate"] > missing_threshold, "column"].tolist()
    cleaned = cleaned.drop(columns=high_missing)
    summary["dropped_high_missing_columns"] = high_missing

    # Normalize Dates
    if "date_mutation" in cleaned.columns:
        cleaned["date_mutation"] = pd.to_datetime(cleaned["date_mutation"], format="%d/%m/%Y", errors="coerce")

    # Clean numeric fields
    numeric_to_fix = ["valeur_fonciere", "surface_reelle_bati", "surface_terrain", "nombre_pieces_principales", "code_postal"]
    for column in numeric_to_fix:
        if column in cleaned.columns:
            cleaned[column] = french_number_to_float(cleaned[column])

    # Handle critical missing fields
    required = [column for column in ["date_mutation", "valeur_fonciere"] if column in cleaned.columns]
    before_required = len(cleaned)
    if required:
        cleaned = cleaned.dropna(subset=required)
    summary["rows_removed_missing_required"] = before_required - len(cleaned)

    # De-duplicate
    before_duplicates = len(cleaned)
    cleaned = cleaned.drop_duplicates()
    summary["duplicate_rows_removed"] = before_duplicates - len(cleaned)

    # Ensure strictly positive land value
    if "valeur_fonciere" in cleaned.columns:
        before_positive = len(cleaned)
        cleaned = cleaned[cleaned["valeur_fonciere"] > 0]
        summary["rows_removed_non_positive_value"] = before_positive - len(cleaned)

    # Clean infinite values
    numeric_cols = cleaned.select_dtypes(include="number").columns
    cleaned.loc[:, numeric_cols] = cleaned.loc[:, numeric_cols].replace([np.inf, -np.inf], np.nan)

    summary["output_rows"] = len(cleaned)
    summary["output_columns"] = len(cleaned.columns)
    return cleaned, summary


def save_cleaning_outputs(df: pd.DataFrame, summary: dict) -> None:
    """Saves cleaning reports and the sample cleaned dataset."""
    ensure_project_dirs()
    missing_report(df).head(30).to_csv(TABLES_DIR / "missing_values_top.csv", index=False)
    pd.DataFrame([summary]).to_csv(TABLES_DIR / "cleaning_summary.csv", index=False)
    df.to_csv(PROCESSED_DIR / "dvf_clean_sample.csv", index=False)