from pydantic import BaseModel, Field


class FoodCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    type: str = Field(min_length=1, max_length=20)
    note: str = ""


class FoodUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    type: str = Field(min_length=1, max_length=20)
    note: str = ""


class ExcludeBody(BaseModel):
    excluded: bool


class SpinBody(BaseModel):
    type: str | None = None


class RecordCreate(BaseModel):
    food_id: int
    eaten_at: str | None = None
    meal: str | None = None
    source: str | None = None
    note: str = ""
