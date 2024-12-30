from datetime import date

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session, joinedload
from models import Car, Garage
from schemas import CarCreate, CarUpdate, CarResponse
from db import SessionLocal

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=CarResponse)
def create_car(car: CarCreate, db: Session = Depends(get_db)):

    if car.productionYear < 1886 or car.productionYear > date.today().year:
        raise HTTPException(status_code=400, detail="Invalid production year")

    new_car = Car(
        make=car.make,
        model=car.model,
        productionYear=car.productionYear,
        licensePlate=car.licensePlate,
    )
    db.add(new_car)

    for garage_id in car.garageIds:
        garage = db.query(Garage).filter(Garage.id == garage_id).first()
        if not garage:
            raise HTTPException(status_code=404, detail=f"Garage with ID {garage_id} not found")
        if garage.capacity <= 0:
            raise HTTPException(status_code=400, detail=f"Garage with ID {garage_id} is full")

        garage.capacity -= 1
        new_car.garages.append(garage)

    db.commit()
    db.refresh(new_car)
    return new_car


@router.get("/all", response_model=list[CarResponse], operation_id="list_all_cars")
def list_all_cars(db: Session = Depends(get_db)):
    return db.query(Car).all()


@router.get("/{car_id}", response_model=CarResponse)
def get_car(car_id: int, db: Session = Depends(get_db)):
    car = db.query(Car).options(joinedload(Car.garages)).filter(Car.id == car_id).first()
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    return car


@router.put("/{car_id}", response_model=CarResponse)
def update_car(car_id: int, updated_car: CarUpdate, db: Session = Depends(get_db)):
    car = db.query(Car).filter(Car.id == car_id).first()
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    for key, value in updated_car.dict().items():
        setattr(car, key, value)
    db.commit()
    db.refresh(car)
    return car


@router.delete("/{car_id}")
def delete_car(car_id: int, db: Session = Depends(get_db)):
    car = db.query(Car).filter(Car.id == car_id).first()
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")

    for garage in car.garages:
        garage.capacity += 1

    db.delete(car)
    db.commit()
    return {"detail": "Car deleted successfully"}


@router.get("/", response_model=list[CarResponse])
def list_cars(
    db: Session = Depends(get_db),
    carMake: str = None,
    garageId: int = None,
    fromYear: int = None,
    toYear: int = None,
):
    query = db.query(Car)

    if carMake:
        query = query.filter(Car.make.ilike(f"%{carMake}%"))
    if garageId:
        query = query.join(Car.garages).filter(Garage.id == garageId)
    if fromYear:
        query = query.filter(Car.productionYear >= fromYear)
    if toYear:
        query = query.filter(Car.productionYear <= toYear)

    cars = query.options(joinedload(Car.garages)).all()
    return cars
