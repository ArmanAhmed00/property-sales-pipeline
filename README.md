# Property Sales Pipeline

A simple Python pipeline for loading, cleaning, and exploring French real estate transaction data from the DVF dataset.

## What is included

- `data/` — raw input files and converted CSV output.
- `notebooks/` — analysis notebooks for loading, cleaning, EDA, and feature engineering.
- `src/` — Python modules for data utilities, cleaning, and feature engineering.
- `data/download.py` — helper to prepare raw DVF zip files from `data/local_data` or another source folder.
- `data/convert_txt_to_csv.py` — converter for `.txt` DVF files in `data/data` into `.csv` files in `data/data_csv`.

## Getting started

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Convert raw TXT files to CSV (if needed):

```bash
python3 data/convert_txt_to_csv.py
```

3. If you have DVF zip files locally, copy them into the raw data folder:

```bash
python3 data/download.py
```

This script will automatically use files in `data/local_data` if present.

## Run the cleaning pipeline

From the repository root:

```bash
python3 -m src.data_cleaning --save
```

This loads the DVF files, cleans the dataset, and saves summary reports and a cleaned sample file.

## Key files

- `src/dvf_utils.py` — loading, inventory, and raw data helpers.
- `src/data_cleaning.py` — cleaning pipeline and save utilities.
- `src/features.py` — feature engineering and outlier tagging.
- `notebooks/01_loading_and_overview.ipynb` — notebook for initial data loading and overview.

## Notes

- The repository works with French DVF data and expects the source files to use pipe (`|`) separators.
- Keep raw data in `data/data` or `data/local_data`, and converted CSV files in `data/data_csv`.
