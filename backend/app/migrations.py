"""SQLite  schema 版本与增量迁移。"""

import sqlite3

CURRENT_VERSION = 2


def _ensure_version_table(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS lebuting_schema (
          id INTEGER PRIMARY KEY CHECK (id = 1),
          version INTEGER NOT NULL DEFAULT 0
        )
        """
    )
    row = conn.execute(
        "SELECT version FROM lebuting_schema WHERE id = 1"
    ).fetchone()
    if row is None:
        conn.execute("INSERT INTO lebuting_schema (id, version) VALUES (1, 0)")


def get_schema_version(conn: sqlite3.Connection) -> int:
    _ensure_version_table(conn)
    return conn.execute(
        "SELECT version FROM lebuting_schema WHERE id = 1"
    ).fetchone()[0]


def _set_schema_version(conn: sqlite3.Connection, version: int) -> None:
    conn.execute(
        "UPDATE lebuting_schema SET version = ? WHERE id = 1", (version,)
    )


def column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    return any(r["name"] == column for r in rows)


def _migration_v1_baseline(conn: sqlite3.Connection) -> None:
    """基线：各模块 init 已 CREATE IF NOT EXISTS。"""


def _migration_v2_type_id(conn: sqlite3.Connection) -> None:
    pairs = (
        ("eat_dish_foods", "eat_dish_types"),
        ("cook_dish_foods", "cook_dish_types"),
    )
    for foods_table, types_table in pairs:
        if not column_exists(conn, foods_table, "type_id"):
            conn.execute(
                f"""
                ALTER TABLE {foods_table}
                ADD COLUMN type_id INTEGER REFERENCES {types_table}(id)
                """
            )
        conn.execute(
            f"""
            UPDATE {foods_table}
            SET type_id = (
              SELECT id FROM {types_table} WHERE name = {foods_table}.type
            )
            WHERE type_id IS NULL
            """
        )


def run_migrations(conn: sqlite3.Connection) -> None:
    _ensure_version_table(conn)
    version = get_schema_version(conn)
    if version < 1:
        _migration_v1_baseline(conn)
        _set_schema_version(conn, 1)
        version = 1
    if version < 2:
        _migration_v2_type_id(conn)
        _set_schema_version(conn, 2)


def backfill_type_ids(
    conn: sqlite3.Connection, foods_table: str, types_table: str
) -> None:
    if not column_exists(conn, foods_table, "type_id"):
        return
    conn.execute(
        f"""
        UPDATE {foods_table}
        SET type_id = (
          SELECT id FROM {types_table} WHERE name = {foods_table}.type
        )
        WHERE type_id IS NULL
        """
    )
