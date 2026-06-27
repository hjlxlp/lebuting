from typing import Any

from fastapi.responses import JSONResponse


def ok(data: Any = None) -> dict:
    return {"code": 0, "message": "ok", "data": data}


def fail(message: str, code: int = 1, http_status: int = 400) -> JSONResponse:
    return JSONResponse(
        status_code=http_status,
        content={"code": code, "message": message, "data": None},
    )
