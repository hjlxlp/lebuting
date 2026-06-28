import re

MEAL_VALUES = frozenset({"breakfast", "lunch", "dinner", "snack"})
SOURCE_VALUES = frozenset({"wheel", "manual"})

DATETIME_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}(:\d{2})?$")


def validate_meal_optional(value: str | None) -> str | None:
    if value is None or value == "":
        return value
    if value not in MEAL_VALUES:
        raise ValueError("餐段须为 breakfast、lunch、dinner 或 snack")
    return value


def validate_source_optional(value: str | None) -> str | None:
    if value is None or value == "":
        return value
    if value not in SOURCE_VALUES:
        raise ValueError("来源须为 wheel 或 manual")
    return value


def validate_datetime_optional(value: str | None) -> str | None:
    if value is None or value == "":
        return value
    text = value.strip()
    if not DATETIME_PATTERN.match(text):
        raise ValueError("时间格式须为 YYYY-MM-DD HH:MM 或 YYYY-MM-DD HH:MM:SS")
    return text
