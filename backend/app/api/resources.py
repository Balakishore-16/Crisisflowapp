from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from app.database import get_db
from app.models import Ambulance, FireStation, FireTruck, Hospital, RiskZone, utcnow
from app.schemas import (
    AmbulanceResponse, FireStationResponse, FireTruckResponse,
    HospitalResponse, RiskZoneResponse, LocationUpdateRequest, LocationUpdateResponse,
)
from app.services.fabric_service import fabric_service
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


@router.get("/resources/{resource_id}")
def get_resource_by_id(resource_id: str, db: Session = Depends(get_db)):
    """Lookup any resource (Ambulance, FireTruck, or FireStation) by its ID."""
    amb = db.query(Ambulance).filter(Ambulance.id == resource_id).first()
    if amb:
        return {"resource_type": "Ambulance", "data": AmbulanceResponse.model_validate(amb)}
    truck = db.query(FireTruck).filter(FireTruck.id == resource_id).first()
    if truck:
        return {"resource_type": "FireTruck", "data": FireTruckResponse.model_validate(truck)}
    station = db.query(FireStation).filter(FireStation.id == resource_id).first()
    if station:
        return {"resource_type": "FireStation", "data": FireStationResponse.model_validate(station)}
    raise HTTPException(404, f"Resource {resource_id} not found")


# ─── Ambulances ───
@router.get("/ambulances", response_model=List[AmbulanceResponse])
def list_ambulances(db: Session = Depends(get_db)):
    return db.query(Ambulance).all()


@router.get("/ambulances/{amb_id}", response_model=AmbulanceResponse)
def get_ambulance(amb_id: str, db: Session = Depends(get_db)):
    amb = db.query(Ambulance).filter(Ambulance.id == amb_id).first()
    if not amb:
        raise HTTPException(404, "Ambulance not found")
    return amb


@router.put("/ambulances/{amb_id}/status")
async def update_ambulance_status(amb_id: str, status: str, db: Session = Depends(get_db)):
    amb = db.query(Ambulance).filter(Ambulance.id == amb_id).first()
    if not amb:
        raise HTTPException(404, "Ambulance not found")
    amb.status = status
    if status == "Available":
        amb.current_incident_id = None
    amb.updated_at = utcnow()
    db.commit()

    # Emit standard business event
    await fabric_service.publish_event(
        event_type="resource.status_changed",
        payload={
            "resource_id": amb.id,
            "resource_type": "Ambulance",
            "call_sign": amb.call_sign,
            "status": status,
            "location": amb.location,
            "zone": amb.zone,
        },
        entity_id=amb.id,
        zone=amb.zone,
    )

    await ws_manager.broadcast("RESOURCE_UPDATED", {
        "type": "ambulance", "id": amb_id, "status": status,
    }, entity_id=amb.id, zone=amb.zone)

    return {"id": amb_id, "status": status}


# ─── Fire Stations ───
@router.get("/fire-stations", response_model=List[FireStationResponse])
def list_fire_stations(db: Session = Depends(get_db)):
    return db.query(FireStation).all()


@router.get("/fire-stations/{station_id}", response_model=FireStationResponse)
def get_fire_station(station_id: str, db: Session = Depends(get_db)):
    station = db.query(FireStation).filter(FireStation.id == station_id).first()
    if not station:
        raise HTTPException(404, "Fire station not found")
    return station


# ─── Fire Trucks ───
@router.get("/fire-trucks", response_model=List[FireTruckResponse])
def list_fire_trucks(db: Session = Depends(get_db)):
    return db.query(FireTruck).all()


@router.get("/fire-trucks/{truck_id}", response_model=FireTruckResponse)
def get_fire_truck(truck_id: str, db: Session = Depends(get_db)):
    truck = db.query(FireTruck).filter(FireTruck.id == truck_id).first()
    if not truck:
        raise HTTPException(404, "Fire truck not found")
    return truck


@router.put("/fire-trucks/{truck_id}/status")
async def update_fire_truck_status(truck_id: str, status: str, db: Session = Depends(get_db)):
    truck = db.query(FireTruck).filter(FireTruck.id == truck_id).first()
    if not truck:
        raise HTTPException(404, "Fire truck not found")
    truck.status = status
    if status == "Available":
        truck.current_incident_id = None
    truck.updated_at = utcnow()
    db.commit()

    await fabric_service.publish_event(
        event_type="resource.status_changed",
        payload={
            "resource_id": truck.id,
            "resource_type": "FireTruck",
            "call_sign": truck.call_sign,
            "status": status,
            "location": truck.location,
            "zone": truck.zone,
        },
        entity_id=truck.id,
        zone=truck.zone,
    )

    await ws_manager.broadcast("RESOURCE_UPDATED", {
        "type": "fire_truck", "id": truck_id, "status": status,
    }, entity_id=truck.id, zone=truck.zone)

    return {"id": truck_id, "status": status}


# ─── Hospitals ───
@router.get("/hospitals", response_model=List[HospitalResponse])
def list_hospitals(db: Session = Depends(get_db)):
    return db.query(Hospital).all()


@router.get("/hospitals/{hospital_id}", response_model=HospitalResponse)
def get_hospital(hospital_id: str, db: Session = Depends(get_db)):
    h = db.query(Hospital).filter(Hospital.id == hospital_id).first()
    if not h:
        raise HTTPException(404, "Hospital not found")
    return h


# ─── Risk Zones ───
@router.get("/risk-zones", response_model=List[RiskZoneResponse])
def list_risk_zones(db: Session = Depends(get_db)):
    return db.query(RiskZone).all()


# ─── Live Location Telemetry ───
@router.post("/resources/{resource_id}/location", response_model=LocationUpdateResponse)
async def update_resource_location(
    resource_id: str,
    payload: LocationUpdateRequest,
    db: Session = Depends(get_db),
):
    """
    Accept real-time GPS or Simulation location telemetry for a resource.
    Validates lat/lon, detects GPS anomalies, records history, emits Fabric events,
    and broadcasts to live frontend WebSocket subscribers.
    """
    import uuid
    import math
    from app.models import LocationHistory
    from app.schemas import LocationUpdateResponse

    amb = db.query(Ambulance).filter(Ambulance.id == resource_id).first()
    truck = db.query(FireTruck).filter(FireTruck.id == resource_id).first() if not amb else None

    if not amb and not truck:
        raise HTTPException(404, f"Resource {resource_id} not found")

    target = amb or truck
    res_type = "Ambulance" if amb else "FireTruck"

    # GPS Anomaly / Impossible movement check
    anomaly_flag = None
    if target.latitude and target.longitude and target.last_location_update:
        dlat = math.radians(payload.latitude - target.latitude)
        dlon = math.radians(payload.longitude - target.longitude)
        a = (math.sin(dlat / 2) ** 2 +
             math.cos(math.radians(target.latitude)) * math.cos(math.radians(payload.latitude)) *
             math.sin(dlon / 2) ** 2)
        dist_km = 6371.0 * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        last_up = target.last_location_update
        if hasattr(last_up, "tzinfo") and last_up.tzinfo is not None:
            last_up = last_up.replace(tzinfo=None)
        now_dt = datetime.now(timezone.utc).replace(tzinfo=None)
        dt_sec = max(1.0, (now_dt - last_up).total_seconds())
        speed_calculated = (dist_km / dt_sec) * 3600.0
        if dist_km > 5.0 and speed_calculated > 500.0:
            anomaly_flag = "GPS_ANOMALY"

    loc_source = payload.source or "LIVE_GPS"
    loc_status = "LIVE"

    target.latitude = payload.latitude
    target.longitude = payload.longitude
    target.speed_kmh = payload.speed_kmh or 0.0
    target.heading = payload.heading or 0.0
    target.location_accuracy = payload.accuracy_m or 5.0
    target.location_source = loc_source
    target.location_status = loc_status
    target.last_location_update = utcnow()
    target.updated_at = utcnow()
    if payload.status:
        target.status = payload.status

    hist_id = f"LOC-{uuid.uuid4().hex[:12]}"
    hist = LocationHistory(
        id=hist_id,
        resource_id=target.id,
        resource_type=res_type,
        latitude=payload.latitude,
        longitude=payload.longitude,
        speed_kmh=payload.speed_kmh or 0.0,
        heading=payload.heading or 0.0,
        accuracy_m=payload.accuracy_m or 5.0,
        status=target.status,
        location_source=loc_source,
        location_status=loc_status,
        anomaly_flag=anomaly_flag,
        timestamp=utcnow(),
    )
    db.add(hist)
    db.commit()

    await fabric_service.publish_event(
        event_type="resource.location.updated",
        payload={
            "resource_id": target.id,
            "resource_type": res_type,
            "call_sign": target.call_sign,
            "latitude": target.latitude,
            "longitude": target.longitude,
            "speed_kmh": target.speed_kmh,
            "heading": target.heading,
            "status": target.status,
            "location_source": loc_source,
            "location_status": loc_status,
            "anomaly_flag": anomaly_flag,
            "zone": target.zone,
        },
        entity_id=target.id,
        zone=target.zone,
    )

    await ws_manager.broadcast("RESOURCE_LOCATION_UPDATED", {
        "event_type": "resource.location.updated",
        "resource_id": target.id,
        "resource_type": res_type,
        "call_sign": target.call_sign,
        "latitude": target.latitude,
        "longitude": target.longitude,
        "speed_kmh": target.speed_kmh,
        "heading": target.heading,
        "status": target.status,
        "location_source": loc_source,
        "location_status": loc_status,
        "anomaly_flag": anomaly_flag,
        "timestamp": utcnow().isoformat(),
    }, entity_id=target.id, zone=target.zone)

    return LocationUpdateResponse(
        success=True,
        resource_id=target.id,
        latitude=target.latitude,
        longitude=target.longitude,
        location_source=loc_source,
        location_status=loc_status,
        anomaly_flag=anomaly_flag,
        timestamp=utcnow(),
        message="Resource location updated successfully",
    )


@router.get("/resources/{resource_id}/location-history")
def get_resource_location_history(resource_id: str, limit: int = 50, db: Session = Depends(get_db)):
    """Retrieve historical location telemetry trail for Fabric & route performance analysis."""
    from app.models import LocationHistory
    return (
        db.query(LocationHistory)
        .filter(LocationHistory.resource_id == resource_id)
        .order_by(LocationHistory.timestamp.desc())
        .limit(limit)
        .all()
    )
