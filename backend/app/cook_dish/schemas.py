from pydantic import BaseModel, Field, field_validator

from app.validators import (
    validate_datetime_optional,
    validate_meal_optional,
    validate_source_optional,
)


class CookDishFoodCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    type: str = Field(min_length=1, max_length=20)
    note: str = Field(default="", max_length=200)


class CookDishFoodUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    type: str = Field(min_length=1, max_length=20)
    note: str = Field(default="", max_length=200)


class CookDishExcludeBody(BaseModel):
    excluded: bool


class CookDishSpinBody(BaseModel):
    type: str | None = Field(default=None, max_length=20)


class CookDishRecordCreate(BaseModel):
    food_id: int = Field(gt=0)
    cooked_at: str | None = None
    meal: str | None = None
    source: str | None = None
    note: str = Field(default="", max_length=200)

    @field_validator("meal")
    @classmethod
    def check_meal(cls, v: str | None) -> str | None:
        return validate_meal_optional(v)

    @field_validator("source")
    @classmethod
    def check_source(cls, v: str | None) -> str | None:
        return validate_source_optional(v)

    @field_validator("cooked_at")
    @classmethod
    def check_cooked_at(cls, v: str | None) -> str | None:
        return validate_datetime_optional(v)


class CookDishTypeCreate(BaseModel):
    name: str = Field(min_length=1, max_length=20)


class CookDishTypeUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=20)
