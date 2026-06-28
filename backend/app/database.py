from app.core import get_conn
from app.cook_dish.db import init_cook_dish_db, sync_cook_dish_types
from app.eat_dish.db import init_eat_dish_db, sync_eat_dish_types
from app.migrations import run_migrations


def init_db() -> None:
    init_eat_dish_db()
    init_cook_dish_db()
    with get_conn() as conn:
        run_migrations(conn)
        sync_eat_dish_types(conn)
        sync_cook_dish_types(conn)
