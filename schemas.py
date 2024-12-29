from pydantic import BaseModel
from typing import List


class GarageBase(BaseModel):
    name: str
    location: str
    city: str
    capacity: int


class GarageCreate(GarageBase):
    pass


class GarageResponse(GarageBase):
    id: int

    class Config:
        from_attributes = True


class CarBase(BaseModel):
    make: str
    model: str
    production_year: int
    license_plate: str


class CarCreate(CarBase):
    garages: List[GarageResponse]


class CarUpdate(CarBase):
    pass


class CarResponse(CarBase):
    id: int
    garages: List[GarageResponse]

    class Config:
        from_attributes = True
