from __future__ import annotations

import argparse
import shutil
from pathlib import Path

YEARS = [2021, 2022, 2023, 2024, 2025]
FILE_TEMPLATE = "valeursfoncieres-{year}.txt.zip"
PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
LOCAL_SOURCE = PROJECT_ROOT / "data" / "local_data"
FILE_NAMES = [FILE_TEMPLATE.format(year=year) for year in YEARS]


def ensure_dirs() -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)


def copy_from(source: Path) -> None:
    ensure_dirs()
    source = Path(source)
    for name in FILE_NAMES:
        source_file = source / name
        if not source_file.exists():
            raise FileNotFoundError(f"Missing {name}")
        target = RAW_DIR / name
        if not target.exists():
            shutil.copy2(source_file, target)
            print(f"Copied {name}")
        else:
            print(f"Already present {name}")


def inventory(directory: Path = RAW_DIR) -> None:
    ensure_dirs()
    for name in FILE_NAMES:
        file_path = directory / name
        if file_path.exists():
            size = file_path.stat().st_size / 1024 / 1024
            print(f"OK       {name:32} {size:8.2f} MB")
        else:
            print(f"MISSING  {name}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--copy-from", type=Path)
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    if args.copy_from:
        copy_from(args.copy_from.expanduser().resolve())
    elif LOCAL_SOURCE.exists():
        copy_from(LOCAL_SOURCE)
    inventory()
