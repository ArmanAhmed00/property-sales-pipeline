from __future__ import annotations

import numpy as np
import pandas as pd

from .dvf_utils import PROCESSED_DIR, TABLES_DIR, ensure_project_dirs


def iqr_bounds(series: pd.Series, multiplier: float = 1.5) -> tuple[float, float]:
    """Calculates the lower and upper bounds using the IQR rule."""
    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1
    return q1 - multiplier * iqr, q3 + multiplier * iqr


def mark_outliers(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Appends binary flag columns indicating IQR outliers for key metrics."""
    result = df.copy()
    rows = []
    for column in ["valeur_fonciere", "price_per_m2"]:
        if column not in result.columns:
            continue
        valid = result[column].dropna()
        lower, upper = iqr_bounds(valid)
        flag = f"is_{column}_outlier"
        result[flag] = result[column].lt(lower) | result[column].gt(upper)
        rows.append(
            {
                "column": column,
                "lower_bound": lower,
                "upper_bound": upper,
                "outlier_count": int(result[flag].sum()),
                "outlier_rate": round(float(result[flag].mean() * 100), 2),
            }
        )
    return result, pd.DataFrame(rows)


def add_features(df: pd.DataFrame) -> pd.DataFrame:
    """Engineers date, department, property types, and ratio features."""
    featured = df.copy()

    # Temporal extractions
    if "date_mutation" in featured.columns:
        featured["year"] = featured["date_mutation"].dt.year
        featured["month"] = featured["date_mutation"].dt.month
        featured["quarter"] = featured["date_mutation"].dt.quarter

    # Department coding
    if "code_departement" in featured.columns:
        featured["department"] = featured["code_departement"].astype("string").str.zfill(2)
    elif "code_postal" in featured.columns:
        featured["department"] = featured["code_postal"].round().astype("Int64").astype("string").str.zfill(5).str[:2]

    if "type_local" in featured.columns:
        featured["property_type"] = featured["type_local"].fillna("Unknown").astype("string")

    # Real estate financial engineering metrics
    if {"valeur_fonciere", "surface_reelle_bati"}.issubset(featured.columns):
        surface = pd.to_numeric(featured["surface_reelle_bati"], errors="coerce")
        value = pd.to_numeric(featured["valeur_fonciere"], errors="coerce")
        featured["price_per_m2"] = np.where(surface.gt(0).fillna(False), value / surface, np.nan)

    if {"surface_reelle_bati", "surface_terrain"}.issubset(featured.columns):
        built = pd.to_numeric(featured["surface_reelle_bati"], errors="coerce")
        land = pd.to_numeric(featured["surface_terrain"], errors="coerce")
        featured["built_to_land_ratio"] = np.where(land.gt(0).fillna(False), built / land, np.nan)

    # Post-process infinities
    numeric_cols = featured.select_dtypes(include="number").columns
    featured.loc[:, numeric_cols] = featured.loc[:, numeric_cols].replace([np.inf, -np.inf], np.nan)
    return featured


def feature_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Generates structural and distribution statistics for engineered features."""
    rows = []
    target_cols = ["year", "month", "quarter", "department", "property_type", "price_per_m2", "built_to_land_ratio"]
    for column in target_cols:
        if column in df.columns:
            rows.append(
                {
                    "feature": column,
                    "non_null_count": int(df[column].notna().sum()),
                    "missing_rate": round(float(df[column].isna().mean() * 100), 2),
                    "unique_values": int(df[column].nunique(dropna=True)),
                }
            )
    return pd.DataFrame(rows)


def save_feature_outputs(df: pd.DataFrame) -> pd.DataFrame:
    """Main execution step to apply features, identify outliers, and save summaries."""
    ensure_project_dirs()
    
    # Generate features & tag outliers
    featured_df = add_features(df)
    featured_df, outlier_report = mark_outliers(featured_df)
    
    # Save statistics
    summary = feature_summary(featured_df)
    summary.to_csv(TABLES_DIR / "feature_summary.csv", index=False)
    outlier_report.to_csv(TABLES_DIR / "outlier_summary.csv", index=False)
    
    # Save structured file outputs
    featured_df.to_csv(PROCESSED_DIR / "dvf_features_sample.csv", index=False)
    return summary