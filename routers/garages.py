from datetime import datetime, timedelta, date

from fastapi import APIRouter, HTTPException, Depends, Query
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


@router.post("/", response_model=GarageResponse)
def create_garage(garage: GarageCreate, db: Session = Depends(get_db)):
    if garage.capacity < 1:
        raise HTTPException(status_code=400, detail="Garage capacity must be greater than 0")

    new_garage = Garage(**garage.dict())
    db.add(new_garage)
    db.commit()
    db.refresh(new_garage)
    return new_garage


@router.get("/all", response_model=list[GarageResponse], operation_id="list_all_garages")
def list_all_garages(db: Session = Depends(get_db)):
    return db.query(Garage).all()


@router.get("/{garage_id}", response_model=GarageResponse)
def get_garage(garage_id: int, db: Session = Depends(get_db)):
    garage = db.query(Garage).filter(Garage.id == garage_id).first()
    if not garage:
        raise HTTPException(status_code=404, detail="Garage not found")
    return garage


@router.put("/{garage_id}", response_model=GarageResponse)
def update_garage(garage_id: int, updated_data: GarageCreate, db: Session = Depends(get_db)):
    garage = db.query(Garage).filter(Garage.id == garage_id).first()
    if not garage:
        raise HTTPException(status_code=404, detail="Garage not found")

    for key, value in updated_data.dict().items():
        setattr(garage, key, value)

    db.commit()
    db.refresh(garage)
    return garage


@router.delete("/{garage_id}")
def delete_garage(garage_id: int, db: Session = Depends(get_db)):
    garage = db.query(Garage).filter(Garage.id == garage_id).first()
    if not garage:
        raise HTTPException(status_code=404, detail="Garage not found")

    db.delete(garage)
    db.commit()
    return {"detail": "Garage deleted successfully"}


@router.get("/", response_model=list[GarageResponse])
def list_garages(city: str = None, db: Session = Depends(get_db)):
    query = db.query(Garage)
    if city:
        query = query.filter(Garage.city == city)
    return query.all()


@router.get("/dailyAvailabilityReport")
def daily_availability_report(
    garageId: int,
    startDate: date = Query(..., description="Start date in format YYYY-MM-DD"),
    endDate: date = Query(..., description="End date in format YYYY-MM-DD"),
    db: Session = Depends(get_db),
):

    if startDate > endDate:
        raise HTTPException(status_code=400, detail="Start date must be before end date.")

    garage = db.query(Garage).filter(Garage.id == garageId).first()
    if not garage:
        raise HTTPException(status_code=404, detail="Garage not found")

    current_date = startDate
    report = []

    while current_date <= endDate:

        request_count = (
            db.query(func.count(MaintenanceRequest.id))
            .filter(
                MaintenanceRequest.garageId == garageId,
                MaintenanceRequest.scheduledDate == current_date,
            )
            .scalar()
        )

        free_capacity = max(garage.capacity - request_count, 0)

        report.append({
            "date": current_date.strftime("%Y-%m-%d"),
            "requests": request_count,
            "free_capacity": free_capacity,
        })

        current_date += timedelta(days=1)

    return report
