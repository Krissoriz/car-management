from pydantic import BaseModel


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
