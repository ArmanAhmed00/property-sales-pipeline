from __future__ import annotations

import os
from pathlib import Path
import pandas as pd

# --- Configuration Section ---
PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = Path(os.environ.get("DVF_RAW_DIR", DATA_DIR / "raw")).expanduser().resolve()
PROCESSED_DIR = DATA_DIR / "processed"
REPORTS_DIR = PROJECT_ROOT / "reports"
TABLES_DIR = REPORTS_DIR / "tables"
FIGURES_DIR = REPORTS_DIR / "figures"

YEARS = [2021, 2022, 2023, 2024, 2025]
FILE_TEMPLATE = "valeursfoncieres-{year}.txt.zip"
FILE_NAMES = [FILE_TEMPLATE.format(year=year) for year in YEARS]


def ensure_project_dirs() -> None:
    """Ensures all required project directories exist."""
    for path in [DATA_DIR / "raw", PROCESSED_DIR, TABLES_DIR, FIGURES_DIR]:
        path.mkdir(parents=True, exist_ok=True)


def expected_raw_files(raw_dir: Path = RAW_DIR) -> list[Path]:
    """Returns a list of expected raw data file paths."""
    return [raw_dir / FILE_TEMPLATE.format(year=year) for year in YEARS]


# --- Data Loading Section ---
def data_inventory(raw_dir: Path = RAW_DIR) -> pd.DataFrame:
    """Generates an inventory report of raw data files."""
    rows = []
    for file_path in expected_raw_files(raw_dir):
        year = int(file_path.name.split("-")[-1].split(".")[0])
        exists = file_path.exists()
        rows.append(
            {
                "year": year,
                "file_name": file_path.name,
                "exists": exists,
                "size_mb": round(file_path.stat().st_size / (1024 * 1024), 2) if exists else 0,
                "path": str(file_path),
            }
        )
    return pd.DataFrame(rows)


def validate_files(raw_dir: Path = RAW_DIR) -> None:
    """Validates that all expected raw files exist; raises FileNotFoundError if not."""
    missing = [path.name for path in expected_raw_files(raw_dir) if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing DVF files: " + ", ".join(missing))


def read_year(path: Path, sample_rows: int | None = None) -> pd.DataFrame:
    """Reads a single DVF file, optionally sampling rows across chunks."""
    year = int(path.name.split("-")[-1].split(".")[0])
    if sample_rows is None:
        df = pd.read_csv(path, sep="|", low_memory=False)
    else:
        samples = []
        current = 0
        for chunk in pd.read_csv(path, sep="|", chunksize=100_000, low_memory=False):
            if len(chunk) > sample_rows:
                chunk = chunk.sample(sample_rows, random_state=year)
            samples.append(chunk)
            current += len(chunk)
            if current > sample_rows:
                combined = pd.concat(samples, ignore_index=True)
                samples = [combined.sample(sample_rows, random_state=year)]
                current = sample_rows
        df = pd.concat(samples, ignore_index=True)

    df["source_year"] = year
    df["source_file"] = path.name
    return df


def load_dvf(raw_dir: Path = RAW_DIR, sample_rows: int | None = None) -> pd.DataFrame:
    """Loads and concatenates DVF data across all target years."""
    validate_files(raw_dir)
    frames = [read_year(path, sample_rows=sample_rows) for path in expected_raw_files(raw_dir)]
    return pd.concat(frames, ignore_index=True)


def save_inventory(raw_dir: Path = RAW_DIR) -> pd.DataFrame:
    """Saves the data inventory tracking sheet to the reports directory."""
    ensure_project_dirs()
    inventory = data_inventory(raw_dir)
    inventory.to_csv(TABLES_DIR / "data_inventory.csv", index=False)
    return inventory