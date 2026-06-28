import sqlite3

from app.core import get_conn, now_str

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
"""

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


def init_cook_dish_db() -> None:
    with get_conn() as conn:
        conn.executescript(SCHEMA_SQL)
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
