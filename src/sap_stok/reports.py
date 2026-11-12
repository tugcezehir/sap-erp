from pathlib import Path

import pandas as pd

from .config import REPORTS


def save_csv(df: pd.DataFrame, name: str) -> Path:
    REPORTS.mkdir(parents=True, exist_ok=True)
    path = REPORTS / name
    df.to_csv(path, index=False, encoding="utf-8-sig")
    return path


def save_excel(sheets: dict[str, pd.DataFrame], name: str = "stok_raporu.xlsx") -> Path:
    REPORTS.mkdir(parents=True, exist_ok=True)
    path = REPORTS / name
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        for sheet, df in sheets.items():
            df.to_excel(writer, sheet_name=sheet[:31], index=False)
    return path
