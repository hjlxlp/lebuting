import sqlite3

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.error_codes import ERR_DUPLICATE, ERR_INVALID_PARAM
from app.response import fail


def _validation_message(exc: RequestValidationError) -> str:
    errors = exc.errors()
    if len(errors) == 0:
        return "参数格式错误"
    err = errors[0]
    err_type = err.get("type", "")
    if err_type in ("missing", "string_too_short"):
        return "请填写完整信息"
    if err_type == "string_too_long":
        return "内容过长"
    return "参数格式错误"


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(RequestValidationError)
    async def validation_handler(_: Request, exc: RequestValidationError):
        return JSONResponse(
            status_code=200,
            content=fail(_validation_message(exc), ERR_INVALID_PARAM),
        )

    @app.exception_handler(sqlite3.IntegrityError)
    async def integrity_handler(_: Request, __: sqlite3.IntegrityError):
        return JSONResponse(
            status_code=200,
            content=fail("名称已存在", ERR_DUPLICATE),
        )
