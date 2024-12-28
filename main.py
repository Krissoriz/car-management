from fastapi import FastAPI

from db import init_db
from routers import garages

app = FastAPI()

# Създаване на базата данни при стартиране
init_db()

# Добавяне на маршрути
app.include_router(garages.router, prefix="/api/v1", tags=["Garages"])
