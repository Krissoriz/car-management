from datetime import datetime, timedelta

from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session
from db import SessionLocal
from models import Garage, MaintenanceRequest
from schemas import GarageResponse, GarageCreate

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/garages", response_model=GarageResponse)
def create_garage(garage: GarageCreate, db: Session = Depends(get_db)):
    new_garage = Garage(**garage.dict())
    db.add(new_garage)
    db.commit()
    db.refresh(new_garage)
    return new_garage


@router.get("/garages", response_model=list[GarageResponse])
def list_garages(db: Session = Depends(get_db)):
    return db.query(Garage).all()


@router.get("/garages/{garage_id}", response_model=GarageResponse)
def get_garage(garage_id: int, db: Session = Depends(get_db)):
    garage = db.query(Garage).filter(Garage.id == garage_id).first()
    if not garage:
        raise HTTPException(status_code=404, detail="Garage not found")
    return garage


@router.put("/garages/{garage_id}", response_model=GarageResponse)
def update_garage(garage_id: int, updated_data: GarageCreate, db: Session = Depends(get_db)):
    garage = db.query(Garage).filter(Garage.id == garage_id).first()
    if not garage:
        raise HTTPException(status_code=404, detail="Garage not found")

    for key, value in updated_data.dict().items():
        setattr(garage, key, value)

    db.commit()
    db.refresh(garage)
    return garage


@router.delete("/garages/{garage_id}")
def delete_garage(garage_id: int, db: Session = Depends(get_db)):
    garage = db.query(Garage).filter(Garage.id == garage_id).first()
    if not garage:
        raise HTTPException(status_code=404, detail="Garage not found")

    db.delete(garage)
    db.commit()
    return {"detail": "Garage deleted successfully"}


@router.get("/garages", response_model=list[GarageResponse])
def list_garages(city: str = None, db: Session = Depends(get_db)):
    query = db.query(Garage)
    if city:
        query = query.filter(Garage.city == city)
    return query.all()


@router.get("/garages/{garage_id}/stats")
def get_garage_stats(
    garage_id: int,
    start_date: str,
    end_date: str,
    db: Session = Depends(get_db),
):
    # Валидация на входните дати
    try:
        start_date = datetime.strptime(start_date, "%Y-%m-%d")
        end_date = datetime.strptime(end_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use 'YYYY-MM-DD'.")

    if start_date > end_date:
        raise HTTPException(status_code=400, detail="Start date must be before end date.")

    # Проверка дали сервизът съществува
    garage = db.query(Garage).filter(Garage.id == garage_id).first()
    if not garage:
        raise HTTPException(status_code=404, detail="Garage not found")

    # Генериране на статистика за всяка дата в диапазона
    current_date = start_date
    stats = []

    while current_date <= end_date:
        # Брой заявки за текущата дата
        request_count = (
            db.query(func.count(MaintenanceRequest.id))
            .filter(
                MaintenanceRequest.garage_id == garage_id,
                MaintenanceRequest.date == current_date,
            )
            .scalar()
        )

        # Свободен капацитет
        free_capacity = max(garage.capacity - request_count, 0)

        stats.append({
            "date": current_date.strftime("%Y-%m-%d"),
            "requests": request_count,
            "free_capacity": free_capacity,
        })

        current_date += timedelta(days=1)

    return stats
