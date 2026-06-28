import sqlite3

from app.core import get_conn, now_str

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS eat_dish_foods (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  name        TEXT NOT NULL,
  type        TEXT NOT NULL,
  excluded    INTEGER NOT NULL DEFAULT 0,
  note        TEXT NOT NULL DEFAULT '',
  created_at  TEXT NOT NULL,
  updated_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS eat_dish_records (
  id          INTEGER PRIMARY KEY AUTOINCREMENT,
  food_id     INTEGER NOT NULL,
  food_name   TEXT NOT NULL,
  food_type   TEXT NOT NULL,
  eaten_at    TEXT NOT NULL,
  meal        TEXT,
  source      TEXT NOT NULL DEFAULT 'wheel',
  note        TEXT NOT NULL DEFAULT '',
  FOREIGN KEY (food_id) REFERENCES eat_dish_foods(id)
);

CREATE INDEX IF NOT EXISTS idx_eat_dish_foods_excluded ON eat_dish_foods(excluded);
CREATE INDEX IF NOT EXISTS idx_eat_dish_records_eaten_at ON eat_dish_records(eaten_at);
CREATE INDEX IF NOT EXISTS idx_eat_dish_records_food_id ON eat_dish_records(food_id);
"""

SEED_FOODS = [
    ("成都你六姐", "火锅", 0, "公司楼下"),
    ("兰州拉面", "面食", 0, ""),
    ("麦当劳", "快餐", 0, ""),
    ("寿司郎", "日料", 1, ""),
    ("张亮麻辣烫", "火锅", 0, ""),
    ("沙县小吃", "快餐", 0, ""),
]

SEED_RECORDS = [
    (1, "成都你六姐", "火锅", "2026-06-25 12:30:00", "lunch"),
    (1, "成都你六姐", "火锅", "2026-06-18 19:00:00", "dinner"),
    (2, "兰州拉面", "面食", "2026-06-20 12:15:00", "lunch"),
    (3, "麦当劳", "快餐", "2026-06-22 18:40:00", "dinner"),
    (5, "张亮麻辣烫", "火锅", "2026-06-26 12:00:00", "lunch"),
]


def _table_names(conn: sqlite3.Connection) -> set[str]:
    rows = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    ).fetchall()
    return {r[0] for r in rows}


def _migrate_legacy_tables(conn: sqlite3.Connection) -> None:
    names = _table_names(conn)
    if "foods" in names and "eat_dish_foods" not in names:
        conn.execute("ALTER TABLE foods RENAME TO eat_dish_foods")
    if "eat_records" in names and "eat_dish_records" not in names:
        conn.execute("ALTER TABLE eat_records RENAME TO eat_dish_records")


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
        "eaten_at": row["eaten_at"],
        "meal": row["meal"] or "",
        "source": row["source"],
        "note": row["note"] or "",
    }


def init_eat_dish_db() -> None:
    with get_conn() as conn:
        _migrate_legacy_tables(conn)
        conn.executescript(SCHEMA_SQL)
        count = conn.execute("SELECT COUNT(*) FROM eat_dish_foods").fetchone()[0]
        if count == 0:
            ts = now_str()
            for name, typ, excluded, note in SEED_FOODS:
                conn.execute(
                    "INSERT INTO eat_dish_foods (name, type, excluded, note, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?)",
                    (name, typ, excluded, note, ts, ts),
                )
            for food_id, name, typ, eaten_at, meal in SEED_RECORDS:
                conn.execute(
                    "INSERT INTO eat_dish_records (food_id, food_name, food_type, eaten_at, meal, source) VALUES (?, ?, ?, ?, ?, 'wheel')",
                    (food_id, name, typ, eaten_at, meal),
                )
