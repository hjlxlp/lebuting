from app.cook_dish.db import init_cook_dish_db
from app.eat_dish.db import init_eat_dish_db


def init_db() -> None:
    init_eat_dish_db()
    init_cook_dish_db()
