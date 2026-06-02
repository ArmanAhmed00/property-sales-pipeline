
from pathlib import Path
import pandas as pd

SRC_DIR = Path('data/data')
DEST_DIR = Path('data/data_csv')
DEST_DIR.mkdir(parents=True, exist_ok=True)

for txt_path in sorted(SRC_DIR.glob('*.txt')):
    csv_path = DEST_DIR / f"{txt_path.stem}.csv"
    if csv_path.exists():
        print(f'Skipping existing {csv_path.name}')
        continue
    print(f'Converting {txt_path.name} -> {csv_path.name}')
    reader = pd.read_csv(txt_path, sep='|', low_memory=False, chunksize=100_000)
    first = True
    for chunk in reader:
        if first:
            chunk.to_csv(csv_path, index=False, mode='w')
            first = False
        else:
            chunk.to_csv(csv_path, index=False, mode='a', header=False)
    print(f'Wrote {csv_path.name} ({csv_path.stat().st_size} bytes)')
