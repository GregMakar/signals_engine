from pathlib import Path
from dataclasses import asdict, is_dataclass
from datetime import date, datetime
import json

import pandas as pd


class ParquetStore:
    def __init__(self, base_dir: str | Path = "data/clean"):
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def _safe_value(self, value):
        """
        Convert values into Parquet-safe values.

        Important:
        - dict/list fields become JSON strings
        - datetime/date fields become ISO strings
        """

        if value is None:
            return None

        if isinstance(value, (datetime, date)):
            return value.isoformat()

        if isinstance(value, (dict, list)):
            return json.dumps(value, default=str, ensure_ascii=False)

        return value

    def _to_row(self, record) -> dict:
        if is_dataclass(record):
            row = asdict(record)
        elif isinstance(record, dict):
            row = record
        else:
            raise TypeError(f"Unsupported record type: {type(record)}")

        return {
            key: self._safe_value(value)
            for key, value in row.items()
        }

    def save_records(self, records: list, name: str) -> Path:
        path = self.base_dir / f"{name}.parquet"
        tmp_path = self.base_dir / f"{name}.tmp.parquet"

        if not records:
            df = pd.DataFrame()
        else:
            rows = [self._to_row(record) for record in records]
            df = pd.DataFrame(rows)

        df.to_parquet(
            tmp_path,
            engine="pyarrow",
            compression="zstd",
            index=False,
        )

        tmp_path.replace(path)

        return path

    def load(self, name: str) -> pd.DataFrame:
        path = self.base_dir / f"{name}.parquet"

        if not path.exists():
            raise FileNotFoundError(path)

        return pd.read_parquet(path, engine="pyarrow")