from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from db import SessionLocal
from models import Garage
from schemas import GarageResponse, GarageCreate

router = APIRouter()

# Създаване на връзка с базата данни


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
