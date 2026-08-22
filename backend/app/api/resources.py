"""CrisisFlow API — Resource, Hospital, Risk Zone routes"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Ambulance, FireStation, FireTruck, Hospital, RiskZone
from app.schemas import (
    AmbulanceResponse, FireStationResponse, FireTruckResponse,
    HospitalResponse, RiskZoneResponse,
)
from app.realtime.manager import ws_manager

router = APIRouter(prefix="/api", tags=["resources"])


# ─── Resources combined ───
@router.get("/resources")
def get_all_resources(db: Session = Depends(get_db)):
    ambulances = db.query(Ambulance).all()
    fire_stations = db.query(FireStation).all()
    fire_trucks = db.query(FireTruck).all()
    return {
        "ambulances": [AmbulanceResponse.model_validate(a) for a in ambulances],
        "fire_stations": [FireStationResponse.model_validate(s) for s in fire_stations],
        "fire_trucks": [FireTruckResponse.model_validate(t) for t in fire_trucks],
        "summary": {
            "total_ambulances": len(ambulances),
            "available_ambulances": sum(1 for a in ambulances if a.status == "Available"),
            "total_fire_trucks": len(fire_trucks),
            "available_fire_trucks": sum(1 for t in fire_trucks if t.status == "Available"),
            "total_fire_stations": len(fire_stations),
            "available_fire_stations": sum(1 for s in fire_stations if s.status == "Available"),
        },
    }


# ─── Ambulances ───
@router.get("/ambulances", response_model=list[AmbulanceResponse])
def list_ambulances(db: Session = Depends(get_db)):
    return db.query(Ambulance).all()


@router.put("/ambulances/{amb_id}/status")
async def update_ambulance_status(amb_id: str, status: str, db: Session = Depends(get_db)):
    amb = db.query(Ambulance).filter(Ambulance.id == amb_id).first()
    if not amb:
        raise HTTPException(404, "Ambulance not found")
    amb.status = status
    if status == "Available":
        amb.current_incident_id = None
    db.commit()
    await ws_manager.broadcast("RESOURCE_UPDATED", {
        "type": "ambulance", "id": amb_id, "status": status,
    })
    return {"id": amb_id, "status": status}


# ─── Fire Stations ───
@router.get("/fire-stations", response_model=list[FireStationResponse])
def list_fire_stations(db: Session = Depends(get_db)):
    return db.query(FireStation).all()


# ─── Fire Trucks ───
@router.get("/fire-trucks", response_model=list[FireTruckResponse])
def list_fire_trucks(db: Session = Depends(get_db)):
    return db.query(FireTruck).all()


@router.put("/fire-trucks/{truck_id}/status")
async def update_fire_truck_status(truck_id: str, status: str, db: Session = Depends(get_db)):
    truck = db.query(FireTruck).filter(FireTruck.id == truck_id).first()
    if not truck:
        raise HTTPException(404, "Fire truck not found")
    truck.status = status
    if status == "Available":
        truck.current_incident_id = None
    db.commit()
    await ws_manager.broadcast("RESOURCE_UPDATED", {
        "type": "fire_truck", "id": truck_id, "status": status,
    })
    return {"id": truck_id, "status": status}


# ─── Hospitals ───
@router.get("/hospitals", response_model=list[HospitalResponse])
def list_hospitals(db: Session = Depends(get_db)):
    return db.query(Hospital).all()


# ─── Risk Zones ───
@router.get("/risk-zones", response_model=list[RiskZoneResponse])
def list_risk_zones(db: Session = Depends(get_db)):
    return db.query(RiskZone).all()
