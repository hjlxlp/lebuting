from pydantic import BaseModel, Field


class EatDishFoodCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    type: str = Field(min_length=1, max_length=20)
    note: str = ""


class EatDishFoodUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    type: str = Field(min_length=1, max_length=20)
    note: str = ""


class EatDishExcludeBody(BaseModel):
    excluded: bool


class EatDishSpinBody(BaseModel):
    type: str | None = None


class EatDishRecordCreate(BaseModel):
    food_id: int
    eaten_at: str | None = None
    meal: str | None = None
    source: str | None = None
    note: str = ""


class EatDishTypeCreate(BaseModel):
    name: str = Field(min_length=1, max_length=20)


class EatDishTypeUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=20)
