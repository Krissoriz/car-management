from sqlalchemy import Column, String, Integer, Table, ForeignKey, Date
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

car_garage_association = Table(
    "car_garage",
    Base.metadata,
    Column("car_id", Integer, ForeignKey("cars.id"), primary_key=True),
    Column("garage_id", Integer, ForeignKey("garages.id"), primary_key=True),
)


class Garage(Base):
    __tablename__ = "garages"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    location = Column(String, nullable=False)
    city = Column(String, nullable=False)
    capacity = Column(Integer, nullable=False)

    cars = relationship("Car", secondary=car_garage_association, back_populates="garages")
    requests = relationship("MaintenanceRequest", back_populates="garage")


class Car(Base):
    __tablename__ = "cars"
    id = Column(Integer, primary_key=True, index=True)
    make = Column(String)
    model = Column(String)
    productionYear = Column(Integer)
    licensePlate = Column(String)

    garages = relationship("Garage", secondary=car_garage_association, back_populates="cars")
    requests = relationship("MaintenanceRequest", back_populates="car")


class MaintenanceRequest(Base):
    __tablename__ = "maintenance_requests"

    id = Column(Integer, primary_key=True, index=True)
    garageId = Column(Integer, ForeignKey("garages.id"), nullable=False)
    carId = Column(Integer, ForeignKey("cars.id"), nullable=False)
    scheduledDate = Column(Date, nullable=False)
    serviceType = Column(String, nullable=False)

    garage = relationship("Garage", back_populates="requests")
    car = relationship("Car", back_populates="requests")
