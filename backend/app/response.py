from typing import Any

from app.error_codes import ERR_GENERAL, OK


def ok(data: Any = None) -> dict:
    return {"code": OK, "message": "ok", "data": data}


def fail(message: str, code: int = ERR_GENERAL) -> dict:
    """业务错误：HTTP 始终 200，由 code != 0 表示失败，message 给前端展示。"""
    return {"code": code, "message": message, "data": None}
