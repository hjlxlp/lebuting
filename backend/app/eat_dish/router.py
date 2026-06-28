import random

from fastapi import APIRouter, Query

from app.core import current_month, get_conn, infer_meal, now_str
from app.eat_dish.db import row_to_food, row_to_record, row_to_type
from app.eat_dish.schemas import (
    EatDishExcludeBody,
    EatDishFoodCreate,
    EatDishFoodUpdate,
    EatDishRecordCreate,
    EatDishSpinBody,
    EatDishTypeCreate,
    EatDishTypeUpdate,
)
from app.error_codes import (
    ERR_DUPLICATE,
    ERR_NOT_FOUND,
    ERR_TYPE_IN_USE,
    ERR_WHEEL_POOL,
    ERR_WHEEL_TYPE,
)
from app.response import fail, ok

router = APIRouter()


def _get_food(conn, food_id: int):
    row = conn.execute(
        "SELECT * FROM eat_dish_foods WHERE id = ?", (food_id,)
    ).fetchone()
    if row is None:
        return None
    return row_to_food(row)


def _get_food_by_name(conn, name: str):
    row = conn.execute(
        "SELECT * FROM eat_dish_foods WHERE name = ?", (name,)
    ).fetchone()
    if row is None:
        return None
    return row_to_food(row)


def _get_type_by_name(conn, name: str):
    row = conn.execute(
        "SELECT * FROM eat_dish_types WHERE name = ?", (name,)
    ).fetchone()
    if row is None:
        return None
    return row_to_type(row)


def _wheel_pool(conn, type_filter: str | None = None) -> list[dict]:
    sql = "SELECT * FROM eat_dish_foods WHERE excluded = 0"
    params: list = []
    if type_filter:
        sql += " AND type = ?"
        params.append(type_filter)
    sql += " ORDER BY id"
    rows = conn.execute(sql, params).fetchall()
    return [row_to_food(r) for r in rows]


def _food_stats(conn, food_id: int, month: str | None = None) -> dict | None:
    food = _get_food(conn, food_id)
    if food is None:
        return None
    month = month or current_month()
    rows = conn.execute(
        "SELECT eaten_at FROM eat_dish_records WHERE food_id = ? ORDER BY eaten_at DESC",
        (food_id,),
    ).fetchall()
    total = len(rows)
    month_count = sum(1 for r in rows if r["eaten_at"].startswith(month))
    last_eaten_at = rows[0]["eaten_at"] if rows else ""
    label = f"{food['name']} · {food['type']}"
    return {
        "food_id": food_id,
        "label": label,
        "total": total,
        "month_count": month_count,
        "last_eaten_at": last_eaten_at,
    }


def _get_type(conn, type_id: int):
    row = conn.execute(
        "SELECT * FROM eat_dish_types WHERE id = ?", (type_id,)
    ).fetchone()
    if row is None:
        return None
    return row_to_type(row)


def _type_exists(conn, name: str) -> bool:
    row = conn.execute(
        "SELECT id FROM eat_dish_types WHERE name = ?", (name,)
    ).fetchone()
    return row is not None


def _get_type_id(conn, name: str) -> int | None:
    row = conn.execute(
        "SELECT id FROM eat_dish_types WHERE name = ?", (name,)
    ).fetchone()
    if row is None:
        return None
    return row["id"]


@router.get("/types")
def list_types():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM eat_dish_types ORDER BY sort_order, id"
        ).fetchall()
        return ok([row_to_type(r) for r in rows])


@router.post("/types")
def create_type(body: EatDishTypeCreate):
    name = body.name.strip()
    if not name:
        return fail("名称不能为空")
    ts = now_str()
    with get_conn() as conn:
        existing = _get_type_by_name(conn, name)
        if existing is not None:
            return fail("分类名称已存在", ERR_DUPLICATE)
        order = conn.execute("SELECT COUNT(*) FROM eat_dish_types").fetchone()[0]
        cur = conn.execute(
            "INSERT INTO eat_dish_types (name, sort_order, created_at) VALUES (?, ?, ?)",
            (name, order, ts),
        )
        return ok(_get_type(conn, cur.lastrowid))


@router.put("/types/{type_id}")
def update_type(type_id: int, body: EatDishTypeUpdate):
    name = body.name.strip()
    if not name:
        return fail("名称不能为空")
    with get_conn() as conn:
        old = _get_type(conn, type_id)
        if old is None:
            return fail("分类不存在", ERR_NOT_FOUND)
        if name != old["name"]:
            dup = _get_type_by_name(conn, name)
            if dup is not None and dup["id"] != type_id:
                return fail("分类名称已存在", ERR_DUPLICATE)
            conn.execute(
                "UPDATE eat_dish_types SET name=? WHERE id=?", (name, type_id)
            )
            conn.execute(
                "UPDATE eat_dish_foods SET type=? WHERE type_id=?",
                (name, type_id),
            )
            conn.execute(
                "UPDATE eat_dish_records SET food_type=? WHERE food_type=?",
                (name, old["name"]),
            )
        return ok(_get_type(conn, type_id))


@router.delete("/types/{type_id}")
def delete_type(type_id: int):
    with get_conn() as conn:
        typ = _get_type(conn, type_id)
        if typ is None:
            return fail("分类不存在", ERR_NOT_FOUND)
        count = conn.execute(
            "SELECT COUNT(*) FROM eat_dish_foods WHERE type_id = ?", (type_id,)
        ).fetchone()[0]
        if count > 0:
            return fail(f"该分类下还有 {count} 个候选，无法删除", ERR_TYPE_IN_USE)
        conn.execute("DELETE FROM eat_dish_types WHERE id = ?", (type_id,))
        return ok(None)


@router.get("/foods")
def list_foods(
    type: str | None = Query(default=None),
    excluded: bool | None = Query(default=None),
):
    sql = "SELECT * FROM eat_dish_foods WHERE 1=1"
    params: list = []
    if type is not None:
        sql += " AND type = ?"
        params.append(type)
    if excluded is not None:
        sql += " AND excluded = ?"
        params.append(1 if excluded else 0)
    sql += " ORDER BY id"
    with get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()
        return ok([row_to_food(r) for r in rows])


@router.post("/foods")
def create_food(body: EatDishFoodCreate):
    name = body.name.strip()
    if not name:
        return fail("名称不能为空")
    typ = body.type.strip()
    if not typ:
        return fail("类型不能为空")
    ts = now_str()
    with get_conn() as conn:
        if not _type_exists(conn, typ):
            return fail("类型不存在，请先在分类管理中添加")
        type_id = _get_type_id(conn, typ)
        existing = _get_food_by_name(conn, name)
        if existing is not None:
            return fail("候选名称已存在", ERR_DUPLICATE)
        cur = conn.execute(
            "INSERT INTO eat_dish_foods (name, type, type_id, excluded, note, created_at, updated_at) VALUES (?, ?, ?, 0, ?, ?, ?)",
            (name, typ, type_id, (body.note or "").strip(), ts, ts),
        )
        food = _get_food(conn, cur.lastrowid)
        return ok(food)


@router.get("/foods/{food_id}")
def get_food(food_id: int):
    with get_conn() as conn:
        food = _get_food(conn, food_id)
        if food is None:
            return fail("候选不存在", ERR_NOT_FOUND)
        return ok(food)


@router.put("/foods/{food_id}")
def update_food(food_id: int, body: EatDishFoodUpdate):
    name = body.name.strip()
    if not name:
        return fail("名称不能为空")
    typ = body.type.strip()
    if not typ:
        return fail("类型不能为空")
    ts = now_str()
    with get_conn() as conn:
        if _get_food(conn, food_id) is None:
            return fail("候选不存在", ERR_NOT_FOUND)
        if not _type_exists(conn, typ):
            return fail("类型不存在，请先在分类管理中添加")
        type_id = _get_type_id(conn, typ)
        dup = _get_food_by_name(conn, name)
        if dup is not None and dup["id"] != food_id:
            return fail("候选名称已存在", ERR_DUPLICATE)
        conn.execute(
            "UPDATE eat_dish_foods SET name=?, type=?, type_id=?, note=?, updated_at=? WHERE id=?",
            (name, typ, type_id, (body.note or "").strip(), ts, food_id),
        )
        return ok(_get_food(conn, food_id))


@router.delete("/foods/{food_id}")
def delete_food(food_id: int):
    with get_conn() as conn:
        if _get_food(conn, food_id) is None:
            return fail("候选不存在", ERR_NOT_FOUND)
        conn.execute("DELETE FROM eat_dish_records WHERE food_id = ?", (food_id,))
        conn.execute("DELETE FROM eat_dish_foods WHERE id = ?", (food_id,))
        return ok(None)


@router.patch("/foods/{food_id}/exclude")
def set_excluded(food_id: int, body: EatDishExcludeBody):
    with get_conn() as conn:
        if _get_food(conn, food_id) is None:
            return fail("候选不存在", ERR_NOT_FOUND)
        conn.execute(
            "UPDATE eat_dish_foods SET excluded=?, updated_at=? WHERE id=?",
            (1 if body.excluded else 0, now_str(), food_id),
        )
        return ok(_get_food(conn, food_id))


@router.get("/wheel/pool")
def wheel_pool(type: str | None = Query(default=None)):
    with get_conn() as conn:
        pool = _wheel_pool(conn, type)
        return ok(pool)


@router.post("/wheel/spin")
def wheel_spin(body: EatDishSpinBody | None = None):
    type_filter = None
    if body is not None and body.type:
        type_filter = body.type.strip() or None
    with get_conn() as conn:
        if type_filter and not _type_exists(conn, type_filter):
            return fail("分类不存在", ERR_WHEEL_TYPE)
        pool = _wheel_pool(conn, type_filter)
        if len(pool) < 2:
            msg = (
                "该分类下可选项不足 2 个"
                if type_filter
                else "至少要有 2 个可选项才能转"
            )
            return fail(msg, ERR_WHEEL_POOL)
        food = random.choice(pool)
        return ok({"food": food, "pool_size": len(pool)})


@router.post("/records")
def create_record(body: EatDishRecordCreate):
    with get_conn() as conn:
        food = _get_food(conn, body.food_id)
        if food is None:
            return fail("候选不存在", ERR_NOT_FOUND)
        eaten_at = (body.eaten_at or now_str()).strip()
        meal = (body.meal or infer_meal()).strip()
        source = (body.source or "wheel").strip()
        cur = conn.execute(
            "INSERT INTO eat_dish_records (food_id, food_name, food_type, eaten_at, meal, source, note) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                food["id"],
                food["name"],
                food["type"],
                eaten_at,
                meal,
                source,
                (body.note or "").strip(),
            ),
        )
        row = conn.execute(
            "SELECT * FROM eat_dish_records WHERE id = ?", (cur.lastrowid,)
        ).fetchone()
        return ok(row_to_record(row))


@router.get("/records")
def list_records(
    month: str | None = Query(default=None),
    food_id: int | None = Query(default=None),
):
    sql = "SELECT * FROM eat_dish_records WHERE 1=1"
    params: list = []
    if month:
        sql += " AND eaten_at LIKE ?"
        params.append(f"{month}%")
    if food_id is not None:
        sql += " AND food_id = ?"
        params.append(food_id)
    sql += " ORDER BY eaten_at DESC"
    with get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()
        return ok([row_to_record(r) for r in rows])


@router.delete("/records/{record_id}")
def delete_record(record_id: int):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id FROM eat_dish_records WHERE id = ?", (record_id,)
        ).fetchone()
        if row is None:
            return fail("记录不存在", ERR_NOT_FOUND)
        conn.execute("DELETE FROM eat_dish_records WHERE id = ?", (record_id,))
        return ok(None)


@router.get("/stats/summary")
def stats_summary(month: str | None = Query(default=None)):
    month = month or current_month()
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM eat_dish_records ORDER BY eaten_at DESC"
        ).fetchall()
        stats_map: dict[int, dict] = {}
        for r in rows:
            fid = r["food_id"]
            if fid not in stats_map:
                stats_map[fid] = {
                    "food_id": fid,
                    "label": f"{r['food_name']} · {r['food_type']}",
                    "total": 0,
                    "month_count": 0,
                    "last_eaten_at": r["eaten_at"],
                }
            stat = stats_map[fid]
            stat["total"] += 1
            if r["eaten_at"].startswith(month):
                stat["month_count"] += 1
            if r["eaten_at"] > stat["last_eaten_at"]:
                stat["last_eaten_at"] = r["eaten_at"]
        ranking = sorted(
            stats_map.values(), key=lambda x: x["month_count"], reverse=True
        )
        total_count = sum(s["month_count"] for s in ranking)
        return ok({"month": month, "total_count": total_count, "ranking": ranking})


@router.get("/stats/food/{food_id}")
def stats_food(food_id: int, month: str | None = Query(default=None)):
    with get_conn() as conn:
        stat = _food_stats(conn, food_id, month)
        if stat is None:
            return fail("候选不存在", ERR_NOT_FOUND)
        return ok(stat)
