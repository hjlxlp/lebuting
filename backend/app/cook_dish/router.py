import random

from fastapi import APIRouter, Query

from app.core import current_month, get_conn, infer_meal, now_str
from app.cook_dish.db import row_to_food, row_to_record, row_to_type
from app.cook_dish.schemas import (
    CookDishExcludeBody,
    CookDishFoodCreate,
    CookDishFoodUpdate,
    CookDishRecordCreate,
    CookDishSpinBody,
    CookDishTypeCreate,
    CookDishTypeUpdate,
)
from app.response import fail, ok

router = APIRouter()


def _get_food(conn, food_id: int):
    row = conn.execute(
        "SELECT * FROM cook_dish_foods WHERE id = ?", (food_id,)
    ).fetchone()
    if row is None:
        return None
    return row_to_food(row)


def _get_food_by_name(conn, name: str):
    row = conn.execute(
        "SELECT * FROM cook_dish_foods WHERE name = ?", (name,)
    ).fetchone()
    if row is None:
        return None
    return row_to_food(row)


def _get_type_by_name(conn, name: str):
    row = conn.execute(
        "SELECT * FROM cook_dish_types WHERE name = ?", (name,)
    ).fetchone()
    if row is None:
        return None
    return row_to_type(row)


def _wheel_pool(conn, type_filter: str | None = None) -> list[dict]:
    sql = "SELECT * FROM cook_dish_foods WHERE excluded = 0"
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
        "SELECT cooked_at FROM cook_dish_records WHERE food_id = ? ORDER BY cooked_at DESC",
        (food_id,),
    ).fetchall()
    total = len(rows)
    month_count = sum(1 for r in rows if r["cooked_at"].startswith(month))
    last_cooked_at = rows[0]["cooked_at"] if rows else ""
    label = f"{food['name']} · {food['type']}"
    return {
        "food_id": food_id,
        "label": label,
        "total": total,
        "month_count": month_count,
        "last_cooked_at": last_cooked_at,
    }


def _get_type(conn, type_id: int):
    row = conn.execute(
        "SELECT * FROM cook_dish_types WHERE id = ?", (type_id,)
    ).fetchone()
    if row is None:
        return None
    return row_to_type(row)


def _type_exists(conn, name: str) -> bool:
    row = conn.execute(
        "SELECT id FROM cook_dish_types WHERE name = ?", (name,)
    ).fetchone()
    return row is not None


@router.get("/types")
def list_types():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM cook_dish_types ORDER BY sort_order, id"
        ).fetchall()
        return ok([row_to_type(r) for r in rows])


@router.post("/types")
def create_type(body: CookDishTypeCreate):
    name = body.name.strip()
    if not name:
        return fail("名称不能为空")
    ts = now_str()
    with get_conn() as conn:
        existing = _get_type_by_name(conn, name)
        if existing is not None:
            return fail("分类名称已存在")
        order = conn.execute("SELECT COUNT(*) FROM cook_dish_types").fetchone()[0]
        cur = conn.execute(
            "INSERT INTO cook_dish_types (name, sort_order, created_at) VALUES (?, ?, ?)",
            (name, order, ts),
        )
        return ok(_get_type(conn, cur.lastrowid))


@router.put("/types/{type_id}")
def update_type(type_id: int, body: CookDishTypeUpdate):
    name = body.name.strip()
    if not name:
        return fail("名称不能为空")
    with get_conn() as conn:
        old = _get_type(conn, type_id)
        if old is None:
            return fail("分类不存在", code=404)
        if name != old["name"]:
            dup = _get_type_by_name(conn, name)
            if dup is not None and dup["id"] != type_id:
                return fail("分类名称已存在")
            conn.execute(
                "UPDATE cook_dish_types SET name=? WHERE id=?", (name, type_id)
            )
            conn.execute(
                "UPDATE cook_dish_foods SET type=? WHERE type=?",
                (name, old["name"]),
            )
            conn.execute(
                "UPDATE cook_dish_records SET food_type=? WHERE food_type=?",
                (name, old["name"]),
            )
        return ok(_get_type(conn, type_id))


@router.delete("/types/{type_id}")
def delete_type(type_id: int):
    with get_conn() as conn:
        typ = _get_type(conn, type_id)
        if typ is None:
            return fail("分类不存在", code=404)
        count = conn.execute(
            "SELECT COUNT(*) FROM cook_dish_foods WHERE type = ?", (typ["name"],)
        ).fetchone()[0]
        if count > 0:
            return fail(f"该分类下还有 {count} 个候选，无法删除")
        conn.execute("DELETE FROM cook_dish_types WHERE id = ?", (type_id,))
        return ok(None)


@router.get("/foods")
def list_foods(
    type: str | None = Query(default=None),
    excluded: bool | None = Query(default=None),
):
    sql = "SELECT * FROM cook_dish_foods WHERE 1=1"
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
def create_food(body: CookDishFoodCreate):
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
        existing = _get_food_by_name(conn, name)
        if existing is not None:
            return fail("候选名称已存在")
        cur = conn.execute(
            "INSERT INTO cook_dish_foods (name, type, excluded, note, created_at, updated_at) VALUES (?, ?, 0, ?, ?, ?)",
            (name, typ, (body.note or "").strip(), ts, ts),
        )
        food = _get_food(conn, cur.lastrowid)
        return ok(food)


@router.get("/foods/{food_id}")
def get_food(food_id: int):
    with get_conn() as conn:
        food = _get_food(conn, food_id)
        if food is None:
            return fail("候选不存在", code=404)
        return ok(food)


@router.put("/foods/{food_id}")
def update_food(food_id: int, body: CookDishFoodUpdate):
    name = body.name.strip()
    if not name:
        return fail("名称不能为空")
    typ = body.type.strip()
    if not typ:
        return fail("类型不能为空")
    ts = now_str()
    with get_conn() as conn:
        if _get_food(conn, food_id) is None:
            return fail("候选不存在", code=404)
        if not _type_exists(conn, typ):
            return fail("类型不存在，请先在分类管理中添加")
        dup = _get_food_by_name(conn, name)
        if dup is not None and dup["id"] != food_id:
            return fail("候选名称已存在")
        conn.execute(
            "UPDATE cook_dish_foods SET name=?, type=?, note=?, updated_at=? WHERE id=?",
            (name, typ, (body.note or "").strip(), ts, food_id),
        )
        return ok(_get_food(conn, food_id))


@router.delete("/foods/{food_id}")
def delete_food(food_id: int):
    with get_conn() as conn:
        if _get_food(conn, food_id) is None:
            return fail("候选不存在", code=404)
        conn.execute("DELETE FROM cook_dish_records WHERE food_id = ?", (food_id,))
        conn.execute("DELETE FROM cook_dish_foods WHERE id = ?", (food_id,))
        return ok(None)


@router.patch("/foods/{food_id}/exclude")
def set_excluded(food_id: int, body: CookDishExcludeBody):
    with get_conn() as conn:
        if _get_food(conn, food_id) is None:
            return fail("候选不存在", code=404)
        conn.execute(
            "UPDATE cook_dish_foods SET excluded=?, updated_at=? WHERE id=?",
            (1 if body.excluded else 0, now_str(), food_id),
        )
        return ok(_get_food(conn, food_id))


@router.get("/food-types")
def list_food_types():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT name FROM cook_dish_types ORDER BY sort_order, id"
        ).fetchall()
        return ok([r["name"] for r in rows])


@router.get("/wheel/pool")
def wheel_pool(type: str | None = Query(default=None)):
    with get_conn() as conn:
        pool = _wheel_pool(conn, type)
        return ok(pool)


@router.post("/wheel/spin")
def wheel_spin(body: CookDishSpinBody | None = None):
    type_filter = None
    if body is not None and body.type:
        type_filter = body.type.strip() or None
    with get_conn() as conn:
        pool = _wheel_pool(conn, type_filter)
        if len(pool) < 2:
            return fail("至少要有 2 个可选项才能转", code=1001)
        food = random.choice(pool)
        return ok({"food": food, "pool_size": len(pool)})


@router.post("/records")
def create_record(body: CookDishRecordCreate):
    with get_conn() as conn:
        food = _get_food(conn, body.food_id)
        if food is None:
            return fail("候选不存在", code=404)
        cooked_at = (body.cooked_at or now_str()).strip()
        meal = (body.meal or infer_meal()).strip()
        source = (body.source or "wheel").strip()
        cur = conn.execute(
            "INSERT INTO cook_dish_records (food_id, food_name, food_type, cooked_at, meal, source, note) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (
                food["id"],
                food["name"],
                food["type"],
                cooked_at,
                meal,
                source,
                (body.note or "").strip(),
            ),
        )
        row = conn.execute(
            "SELECT * FROM cook_dish_records WHERE id = ?", (cur.lastrowid,)
        ).fetchone()
        return ok(row_to_record(row))


@router.get("/records")
def list_records(
    month: str | None = Query(default=None),
    food_id: int | None = Query(default=None),
):
    sql = "SELECT * FROM cook_dish_records WHERE 1=1"
    params: list = []
    if month:
        sql += " AND cooked_at LIKE ?"
        params.append(f"{month}%")
    if food_id is not None:
        sql += " AND food_id = ?"
        params.append(food_id)
    sql += " ORDER BY cooked_at DESC"
    with get_conn() as conn:
        rows = conn.execute(sql, params).fetchall()
        return ok([row_to_record(r) for r in rows])


@router.delete("/records/{record_id}")
def delete_record(record_id: int):
    with get_conn() as conn:
        row = conn.execute(
            "SELECT id FROM cook_dish_records WHERE id = ?", (record_id,)
        ).fetchone()
        if row is None:
            return fail("记录不存在", code=404)
        conn.execute("DELETE FROM cook_dish_records WHERE id = ?", (record_id,))
        return ok(None)


@router.get("/stats/summary")
def stats_summary(month: str | None = Query(default=None)):
    month = month or current_month()
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT * FROM cook_dish_records ORDER BY cooked_at DESC"
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
                    "last_cooked_at": r["cooked_at"],
                }
            stat = stats_map[fid]
            stat["total"] += 1
            if r["cooked_at"].startswith(month):
                stat["month_count"] += 1
            if r["cooked_at"] > stat["last_cooked_at"]:
                stat["last_cooked_at"] = r["cooked_at"]
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
            return fail("候选不存在", code=404)
        return ok(stat)
