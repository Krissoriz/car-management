from fastapi import FastAPI

from db import init_db
from routers import garages, cars

app = FastAPI()

init_db()

app.include_router(garages.router, prefix="/api/v1", tags=["Garages"])
app.include_router(cars.router, prefix="/api/v1", tags=["Cars"])
