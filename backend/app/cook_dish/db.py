import sqlite3

from app.core import get_conn, now_str
from app.migrations import backfill_type_ids

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS cook_dish_foods (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  name        TEXT NOT NULL,
  type        TEXT NOT NULL,
  excluded    INTEGER NOT NULL DEFAULT 0,
  note        TEXT NOT NULL DEFAULT '',
  created_at  TEXT NOT NULL,
  updated_at  TEXT NOT NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_cook_dish_foods_name ON cook_dish_foods(name);

CREATE TABLE IF NOT EXISTS cook_dish_records (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  food_id     INTEGER NOT NULL,
  food_name   TEXT NOT NULL,
  food_type   TEXT NOT NULL,
  cooked_at   TEXT NOT NULL,
  meal        TEXT,
  source      TEXT NOT NULL DEFAULT 'wheel',
  note        TEXT NOT NULL DEFAULT '',
  FOREIGN KEY (food_id) REFERENCES cook_dish_foods(id)
);

CREATE INDEX IF NOT EXISTS idx_cook_dish_foods_excluded ON cook_dish_foods(excluded);
CREATE INDEX IF NOT EXISTS idx_cook_dish_records_cooked_at ON cook_dish_records(cooked_at);
CREATE INDEX IF NOT EXISTS idx_cook_dish_records_food_id ON cook_dish_records(food_id);

CREATE TABLE IF NOT EXISTS cook_dish_types (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  name        TEXT NOT NULL UNIQUE,
  sort_order  INTEGER NOT NULL DEFAULT 0,
  created_at  TEXT NOT NULL
);
"""

DEFAULT_TYPES = [
    "家常菜", "快手菜", "硬菜", "汤羹", "凉菜", "烘焙", "素菜", "下饭菜", "其他",
]

SEED_FOODS = [
    ("番茄炒蛋", "家常菜", 0, "15 分钟"),
    ("红烧肉", "硬菜", 0, "需慢炖"),
    ("酸辣土豆丝", "快手菜", 0, ""),
    ("紫菜蛋花汤", "汤羹", 0, ""),
    ("凉拌黄瓜", "凉菜", 1, "夏天常做"),
    ("宫保鸡丁", "下饭菜", 0, ""),
]

SEED_RECORDS = [
    (1, "番茄炒蛋", "家常菜", "2026-06-25 18:30:00", "dinner"),
    (2, "红烧肉", "硬菜", "2026-06-20 12:00:00", "lunch"),
    (1, "番茄炒蛋", "家常菜", "2026-06-18 19:00:00", "dinner"),
    (6, "宫保鸡丁", "下饭菜", "2026-06-26 18:00:00", "dinner"),
]


def _table_names(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
    return {r[0] for r in rows}


def _migrate_legacy_tables(conn: sqlite3.Connection) -> None:
    names = _table_names(conn)
    if "cook_foods" in names and "cook_dish_foods" not in names:
        conn.execute("ALTER TABLE cook_foods RENAME TO cook_dish_foods")
    if "cook_records" in names and "cook_dish_records" not in names:
        conn.execute("ALTER TABLE cook_records RENAME TO cook_dish_records")


def row_to_food(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "name": row["name"],
        "type": row["type"],
        "excluded": bool(row["excluded"]),
        "note": row["note"] or "",
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def row_to_record(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "food_id": row["food_id"],
        "food_name": row["food_name"],
        "food_type": row["food_type"],
        "cooked_at": row["cooked_at"],
        "meal": row["meal"] or "",
        "source": row["source"],
        "note": row["note"] or "",
    }


def row_to_type(row: sqlite3.Row) -> dict:
    return {
        "id": row["id"],
        "name": row["name"],
        "sort_order": row["sort_order"],
    }


def sync_cook_dish_types(conn: sqlite3.Connection) -> None:
    ts = now_str()
    count = conn.execute("SELECT COUNT(*) FROM cook_dish_types").fetchone()[0]
    seen: set[str] = set()
    if count == 0:
        for i, name in enumerate(DEFAULT_TYPES):
            conn.execute(
                "INSERT INTO cook_dish_types (name, sort_order, created_at) VALUES (?, ?, ?)",
                (name, i, ts),
            )
            seen.add(name)
    else:
        rows = conn.execute("SELECT name FROM cook_dish_types").fetchall()
        seen = {r["name"] for r in rows}
    max_order = conn.execute(
        "SELECT COALESCE(MAX(sort_order), -1) FROM cook_dish_types"
    ).fetchone()[0]
    order = max_order + 1
    rows = conn.execute("SELECT DISTINCT type FROM cook_dish_foods").fetchall()
    for r in rows:
        typ = (r["type"] or "").strip()
        if typ and typ not in seen:
            conn.execute(
                "INSERT INTO cook_dish_types (name, sort_order, created_at) VALUES (?, ?, ?)",
                (typ, order, ts),
            )
            seen.add(typ)
            order += 1
    backfill_type_ids(conn, "cook_dish_foods", "cook_dish_types")


def init_cook_dish_db() -> None:
    with get_conn() as conn:
        _migrate_legacy_tables(conn)
        conn.executescript(SCHEMA_SQL)
        sync_cook_dish_types(conn)
        count = conn.execute("SELECT COUNT(*) FROM cook_dish_foods").fetchone()[0]
        if count == 0:
            ts = now_str()
            for name, typ, excluded, note in SEED_FOODS:
                conn.execute(
                    "INSERT INTO cook_dish_foods (name, type, excluded, note, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                    (name, typ, excluded, note, ts, ts),
                )
            for food_id, name, typ, cooked_at, meal in SEED_RECORDS:
                conn.execute(
                    "INSERT INTO cook_dish_records (food_id, food_name, food_type, cooked_at, meal, source) VALUES (?, ?, ?, ?, ?, 'wheel')",
                    (food_id, name, typ, cooked_at, meal),
                )
