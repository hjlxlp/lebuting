from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import API_PORT
from app.database import init_db
from app.cook_dish.router import router as cook_dish_router
from app.eat_dish.router import router as eat_dish_router


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="lebuting-api", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(eat_dish_router, prefix="/api/eat-dish")
app.include_router(cook_dish_router, prefix="/api/cook-dish")


@app.get("/health")
def health():
    return {"status": "ok", "service": "lebuting-api", "port": API_PORT}
