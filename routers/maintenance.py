from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from datetime import date, timedelta
from models import MaintenanceRequest, Garage, Car
from schemas import MaintenanceRequestCreate, MaintenanceRequestResponse, MaintenanceRequestUpdate
from db import SessionLocal
from sqlalchemy import func
from datetime import datetime

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=MaintenanceRequestResponse)
def create_request(request: MaintenanceRequestCreate, db: Session = Depends(get_db)):

    garage = db.query(Garage).filter(Garage.id == request.garageId).first()
    car = db.query(Car).filter(Car.id == request.carId).first()

    if not request.serviceType:
        raise HTTPException(status_code=400, detail="Service type is required")
    garage = db.query(Garage).filter(Garage.id == request.garageId).first()
    if not garage:
        raise HTTPException(status_code=404, detail="Garage not found")
    car = db.query(Car).filter(Car.id == request.carId).first()
    if not car:
        raise HTTPException(status_code=404, detail="Car not found")

    existing_requests = db.query(MaintenanceRequest).filter(
        MaintenanceRequest.garageId == request.garageId,
        MaintenanceRequest.scheduledDate == request.scheduledDate
    ).count()

    if existing_requests >= garage.capacity:
        raise HTTPException(status_code=400, detail="No available capacity for the selected date")

    new_request = MaintenanceRequest(**request.dict())
    db.add(new_request)
    db.commit()
    db.refresh(new_request)
    return new_request


@router.put("/{request_id}", response_model=MaintenanceRequestResponse)
def update_request(request_id: int, request: MaintenanceRequestUpdate, db: Session = Depends(get_db)):
    existing_request = db.query(MaintenanceRequest).filter(MaintenanceRequest.id == request_id).first()

    if not existing_request:
        raise HTTPException(status_code=404, detail="Request not found")

    garage = db.query(Garage).filter(Garage.id == request.garageId).first()
    if not garage:
        raise HTTPException(status_code=404, detail="Garage not found")

    existing_requests = db.query(MaintenanceRequest).filter(
        MaintenanceRequest.garageId == request.garageId,
        MaintenanceRequest.scheduledDate == request.scheduledDate,
        MaintenanceRequest.id != request_id
    ).count()

    if existing_requests >= garage.capacity:
        raise HTTPException(status_code=400, detail="No available capacity for the selected date")

    for key, value in request.dict().items():
        setattr(existing_request, key, value)

    db.commit()
    db.refresh(existing_request)
    return existing_request


@router.delete("/{request_id}")
def delete_request(request_id: int, db: Session = Depends(get_db)):
    request = db.query(MaintenanceRequest).filter(MaintenanceRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")

    db.delete(request)
    db.commit()
    return {"detail": "Request deleted successfully"}


@router.get("/monthlyRequestsReport")
def monthly_requests_report(
    garageId: int = None,
    startMonth: str = None,
    endMonth: str = None,
    db: Session = Depends(get_db)
):
    try:
        start_date = datetime.strptime(startMonth, "%Y-%m").date().replace(day=1)
        end_date = datetime.strptime(endMonth, "%Y-%m").date().replace(day=1)
        end_date = (end_date.replace(day=1) + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM.")

    query = db.query(
        func.strftime("%Y-%m", MaintenanceRequest.scheduledDate).label("month"),
        func.count(MaintenanceRequest.id).label("requests")
    ).filter(
        MaintenanceRequest.scheduledDate >= start_date,
        MaintenanceRequest.scheduledDate <= end_date
    )

    if garageId:
        query = query.filter(MaintenanceRequest.garageId == garageId)

    query = query.group_by("month").order_by("month")
    results = query.all()

    response = [
        {
            "yearMonth": {
                "year": int(row.month.split("-")[0]),
                "monthValue": int(row.month.split("-")[1])
            },
            "requests": row.requests
        }
        for row in results
    ]

    return response


@router.get("/{request_id}", response_model=MaintenanceRequestResponse)
def get_request(request_id: int, db: Session = Depends(get_db)):
    request = db.query(MaintenanceRequest).filter(MaintenanceRequest.id == request_id).first()
    if not request:
        raise HTTPException(status_code=404, detail="Request not found")
    return request


@router.get("/stats")
def request_statistics(
    db: Session = Depends(get_db),
    garageId: int = None,
    startMonth: str = None,
    endMonth: str = None
):

    if not startMonth or not endMonth:
        raise HTTPException(status_code=400, detail="Start and end months are required")

    try:
        start_date = datetime.strptime(startMonth, "%Y-%m").date()
        end_date = datetime.strptime(endMonth, "%Y-%m").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid month format. Use YYYY-MM")

    query = db.query(
        func.strftime("%Y-%m", MaintenanceRequest.scheduledDate).label("month"),
        func.count(MaintenanceRequest.id).label("request_count")
    ).filter(
        MaintenanceRequest.scheduledDate >= start_date,
        MaintenanceRequest.scheduledDate <= end_date
    )

    if garageId:
        query = query.filter(MaintenanceRequest.garageId == garageId)

    query = query.group_by("month").order_by("month")

    results = query.all()
    stats = []
    current_date = start_date
    while current_date <= end_date:
        current_month = current_date.strftime("%Y-%m")
        count = next((row.request_count for row in results if row.month == current_month), 0)
        stats.append({"month": current_month, "request_count": count})
        current_date = (current_date.replace(day=1) + timedelta(days=32)).replace(day=1)

    return stats


@router.get("/", response_model=list[MaintenanceRequestResponse])
def get_all_requests(
    carId: int = None,
    garageId: int = None,
    startDate: str = None,
    endDate: str = None,
    db: Session = Depends(get_db),
):

    query = db.query(MaintenanceRequest)

    if carId:
        query = query.filter(MaintenanceRequest.carId == carId)

    if garageId:
        query = query.filter(MaintenanceRequest.garageId == garageId)

    if startDate:
        try:
            start_date = datetime.strptime(startDate, "%Y-%m-%d").date()
            query = query.filter(MaintenanceRequest.scheduledDate >= start_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid startDate format. Use YYYY-MM-DD")

    if endDate:
        try:
            end_date = datetime.strptime(endDate, "%Y-%m-%d").date()
            query = query.filter(MaintenanceRequest.scheduledDate <= end_date)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid endDate format. Use YYYY-MM-DD")

    results = query.all()
    return results


