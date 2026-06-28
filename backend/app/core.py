import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Iterator

from app.config import DATA_DIR, DB_PATH


def now_str() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def current_month() -> str:
    return datetime.now().strftime("%Y-%m")


@contextmanager
def get_conn() -> Iterator[sqlite3.Connection]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def infer_meal(dt: datetime | None = None) -> str:
    dt = dt or datetime.now()
    minutes = dt.hour * 60 + dt.minute
    if 300 <= minutes < 630:
        return "breakfast"
    if 630 <= minutes < 870:
        return "lunch"
    if 870 <= minutes < 1230:
        return "dinner"
    return "snack"
