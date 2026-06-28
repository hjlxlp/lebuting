from pydantic import BaseModel, Field, field_validator

from app.validators import (
    validate_datetime_optional,
    validate_meal_optional,
    validate_source_optional,
)


class EatDishFoodCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    type: str = Field(min_length=1, max_length=20)
    note: str = Field(default="", max_length=200)


class EatDishFoodUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    type: str = Field(min_length=1, max_length=20)
    note: str = Field(default="", max_length=200)


class EatDishExcludeBody(BaseModel):
    excluded: bool


class EatDishSpinBody(BaseModel):
    type: str | None = Field(default=None, max_length=20)


class EatDishRecordCreate(BaseModel):
    food_id: int = Field(gt=0)
    eaten_at: str | None = None
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

    @field_validator("eaten_at")
    @classmethod
    def check_eaten_at(cls, v: str | None) -> str | None:
        return validate_datetime_optional(v)


class EatDishTypeCreate(BaseModel):
    name: str = Field(min_length=1, max_length=20)


class EatDishTypeUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=20)
