from pydantic import BaseModel, Field


class CookDishFoodCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    type: str = Field(min_length=1, max_length=20)
    note: str = ""


class CookDishFoodUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    type: str = Field(min_length=1, max_length=20)
    note: str = ""


class CookDishExcludeBody(BaseModel):
    excluded: bool


class CookDishSpinBody(BaseModel):
    type: str | None = None


class CookDishRecordCreate(BaseModel):
    food_id: int
    cooked_at: str | None = None
    meal: str | None = None
    source: str | None = None
    note: str = ""
