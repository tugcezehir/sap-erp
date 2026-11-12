import sqlite3
from contextlib import contextmanager
from pathlib import Path

from .config import DB_PATH


@contextmanager
def connect(path: Path = DB_PATH):
    if not path.exists():
        raise FileNotFoundError(f"Veritabanı bulunamadı: {path}")
    con = sqlite3.connect(path)
    try:
        yield con
    finally:
        con.close()