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


@router.post("/cars", response_model=CarResponse)
def create_car(car: CarCreate, db: Session = Depends(get_db)):

    new_car = Car(
        make=car.make,
        model=car.model,
        production_year=car.production_year,
        license_plate=car.license_plate,
    )
    db.add(new_car)

    for garage_data in car.garages:
        garage = db.query(Garage).filter(Garage.id == garage_data.id).first()
        if not garage:
            raise HTTPException(status_code=404, detail=f"Garage with ID {garage_data.id} not found")
        if garage.capacity <= 0:
            raise HTTPException(status_code=400, detail=f"Garage with ID {garage_data.id} is full")

        garage.capacity -= 1
        new_car.garages.append(garage)

    db.commit()
    db.refresh(new_car)
    return new_car


@router.get("/cars", response_model=list[CarResponse])
def list_cars(db: Session = Depends(get_db)):
    return db.query(Car).all()


@router.get("/cars/{car_id}", response_model=CarResponse)
def get_car(car_id: int, db: Session = Depends(get_db)):
    car = db.query(Car).options(joinedload(Car.garages)).filter(Car.id == car_id).first()
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    return car


@router.put("/cars/{car_id}", response_model=CarResponse)
def update_car(car_id: int, updated_car: CarUpdate, db: Session = Depends(get_db)):
    car = db.query(Car).filter(Car.id == car_id).first()
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")
    for key, value in updated_car.dict().items():
        setattr(car, key, value)
    db.commit()
    db.refresh(car)
    return car


@router.delete("/cars/{car_id}")
def delete_car(car_id: int, db: Session = Depends(get_db)):
    car = db.query(Car).filter(Car.id == car_id).first()
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")

    for garage in car.garages:
        garage.capacity += 1

    db.delete(car)
    db.commit()
    return {"detail": "Car deleted successfully"}


@router.get("/cars", response_model=list[CarResponse])
def list_cars(
    db: Session = Depends(get_db),
    make: str = None,
    garage_id: int = None,
    production_year_from: int = None,
    production_year_to: int = None,
):
    query = db.query(Car)

    if make:
        query = query.filter(Car.make == make)
    if garage_id:
        query = query.join(Car.garages).filter(Garage.id == garage_id)
    if production_year_from:
        query = query.filter(Car.production_year >= production_year_from)
    if production_year_to:
        query = query.filter(Car.production_year <= production_year_to)

    cars = query.options(joinedload(Car.garages)).all()
    return cars
