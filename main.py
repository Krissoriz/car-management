from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from db import init_db
from routers import garages, cars, maintenance

app = FastAPI()

init_db()

app.include_router(garages.router, prefix="/garages", tags=["Garages"])
app.include_router(cars.router, prefix="/cars", tags=["Cars"])
app.include_router(maintenance.router, prefix="/maintenance", tags=["Maintenance Requests"])

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)