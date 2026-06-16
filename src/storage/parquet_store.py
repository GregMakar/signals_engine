from pathlib import Path
from dataclasses import asdict, is_dataclass
import pandas as pd

class ParquetStore:
    def __init__(self, base_dir: str | Path = "data/clean"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def save_records(self, records: list, name: str) -> Path:
        rows = [
            asdict(record) if is_dataclass(record) else record
            for record in records
        ]

        df = pd.DataFrame(rows)
        path = self.base_dir / f"{name}.parquet"
        tmp_path = self.base_dir / f"{name}.tmp.parquet"

        df.to_parquet(tmp_path, engine="pyarrow", compression="zstd", index=False)
        tmp_path.replace(path)

        return path

    def load(self, name: str) -> pd.DataFrame:
        path = self.base_dir / f"{name}.parquet"

        if not path.exists():
            raise FileNotFoundError(path)

        return pd.read_parquet(path, engine="pyarrow")