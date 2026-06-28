from typing import Any


def ok(data: Any = None) -> dict:
    return {"code": 0, "message": "ok", "data": data}


def fail(message: str, code: int = 1) -> dict:
    """业务错误：HTTP 始终 200，由 code != 0 表示失败，message 给前端展示。"""
    return {"code": code, "message": message, "data": None}
