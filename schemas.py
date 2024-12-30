from pydantic import BaseModel
from typing import List
from datetime import date


class GarageBase(BaseModel):
    name: str
    location: str
    city: str
    capacity: int


class GarageCreate(GarageBase):
    pass


class GarageUpdate(GarageBase):
    pass


class GarageResponse(GarageBase):
    id: int

    class Config:
        from_attributes = True


class CarBase(BaseModel):
    make: str
    model: str
    productionYear: int
    licensePlate: str


class CarCreate(CarBase):
    garageIds: List[int]


class CarUpdate(CarBase):
    pass


class CarResponse(CarBase):
    id: int
    garages: List[GarageResponse]

    class Config:
        from_attributes = True


class MaintenanceRequestBase(BaseModel):
    garageId: int
    carId: int
    scheduledDate: date
    serviceType: str


class MaintenanceRequestCreate(MaintenanceRequestBase):
    pass


class MaintenanceRequestUpdate(MaintenanceRequestBase):
    pass


class MaintenanceRequestResponse(MaintenanceRequestBase):
    id: int

    class Config:
        from_attributes = True
