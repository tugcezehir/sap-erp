from pathlib import Path

import pandas as pd

from .config import DB_PATH
from .db import connect

EXTRA_DATE_COLUMNS = {"latest_possible_goods_receipt"}


def _parse_dates(df: pd.DataFrame) -> pd.DataFrame:
    for col in df.columns:
        if "date" in col or col in EXTRA_DATE_COLUMNS:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def list_tables(path: Path = DB_PATH) -> list[str]:
    with connect(path) as con:
        rows = con.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        ).fetchall()
    return [r[0] for r in rows]


def load_table(name: str, path: Path = DB_PATH) -> pd.DataFrame:
    with connect(path) as con:
        df = pd.read_sql_query(f'SELECT * FROM "{name}"', con)
    return _parse_dates(df)


def load_all(path: Path = DB_PATH) -> dict[str, pd.DataFrame]:
    return {t: load_table(t, path) for t in list_tables(path)}
