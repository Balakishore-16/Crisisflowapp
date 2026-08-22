"""CrisisFlow API — Incident Routes"""
import random
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Incident, Recommendation, Dispatch, ActivityLog, Ambulance, FireStation, FireTruck
from app.schemas import IncidentCreate, IncidentResponse, IncidentUpdate, RecommendationResponse, DispatchResponse
from app.services.decision_engine import auto_detect_severity, assess_spread_risk, generate_recommendation
from app.services.ai_service import get_ai_provider
from app.services.fabric_service import fabric_service
from app.services.simulation_service import analyze_incident
from app.realtime.manager import ws_manager

router = APIRouter(prefix="/api", tags=["incidents"])


@router.get("/incidents", response_model=list[IncidentResponse])
def list_incidents(db: Session = Depends(get_db)):
    return db.query(Incident).order_by(Incident.created_at.desc()).all()


@router.get("/incidents/{incident_id}", response_model=IncidentResponse)
def get_incident(incident_id: str, db: Session = Depends(get_db)):
    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if not inc:
        raise HTTPException(404, "Incident not found")
    return inc


@router.post("/incidents", response_model=IncidentResponse)
async def create_incident(data: IncidentCreate, db: Session = Depends(get_db)):
    count = db.query(Incident).count()
    inc_id = f"INC-{2400 + count + 1}"

    severity = data.severity
    if severity == "Auto Detect":
        severity = auto_detect_severity(data.incident_type, data.people_at_risk, data.floor)

    incident = Incident(
        id=inc_id,
        incident_type=data.incident_type,
        location=data.location,
        latitude=data.latitude,
        longitude=data.longitude,
        floor=data.floor,
        building=data.building,
        severity=severity,
        people_at_risk=data.people_at_risk,
        description=data.description,
        status="Detected",
        is_simulated=False,
    )
    incident.spread_risk = assess_spread_risk(incident)
    db.add(incident)
    db.commit()
    db.refresh(incident)

    # Publish to Fabric
    fabric_service.publish_event_sync("INCIDENT_CREATED", {
        "incident_id": incident.id,
        "incident_type": incident.incident_type,
        "location": incident.location,
        "latitude": incident.latitude,
        "longitude": incident.longitude,
        "severity": incident.severity,
        "people_at_risk": incident.people_at_risk,
    })

    # Activity log
    log = ActivityLog(incident_id=inc_id, event_type="INCIDENT_CREATED",
                      message=f"New {incident.incident_type} at {incident.location}",
                      severity="critical" if incident.severity in ("Critical", "High") else "info",
                      icon="🚨")
    db.add(log)
    db.commit()

    await ws_manager.broadcast("INCIDENT_CREATED", {
        "id": incident.id, "incident_type": incident.incident_type,
        "location": incident.location, "latitude": incident.latitude,
        "longitude": incident.longitude, "severity": incident.severity,
        "people_at_risk": incident.people_at_risk, "status": incident.status,
        "floor": incident.floor, "building": incident.building,
        "spread_risk": incident.spread_risk,
    })

    return incident


@router.put("/incidents/{incident_id}", response_model=IncidentResponse)
async def update_incident(incident_id: str, data: IncidentUpdate, db: Session = Depends(get_db)):
    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if not inc:
        raise HTTPException(404, "Incident not found")
    if data.status:
        inc.status = data.status
    if data.severity:
        inc.severity = data.severity
    if data.people_at_risk is not None:
        inc.people_at_risk = data.people_at_risk
    if data.description:
        inc.description = data.description
    inc.updated_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(inc)
    await ws_manager.broadcast("INCIDENT_UPDATED", {
        "id": inc.id, "status": inc.status, "severity": inc.severity,
    })
    return inc


@router.delete("/incidents/{incident_id}")
def delete_incident(incident_id: str, db: Session = Depends(get_db)):
    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if not inc:
        raise HTTPException(404, "Incident not found")
    db.delete(inc)
    db.commit()
    return {"message": "Deleted", "id": incident_id}


@router.post("/incidents/{incident_id}/analyze")
async def analyze(incident_id: str, db: Session = Depends(get_db)):
    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if not inc:
        raise HTTPException(404, "Incident not found")
    result = await analyze_incident(db, inc)
    return result


@router.get("/incidents/{incident_id}/recommendation", response_model=RecommendationResponse)
def get_recommendation(incident_id: str, db: Session = Depends(get_db)):
    rec = (db.query(Recommendation)
           .filter(Recommendation.incident_id == incident_id)
           .order_by(Recommendation.created_at.desc())
           .first())
    if not rec:
        raise HTTPException(404, "No recommendation found for this incident")
    return rec


@router.post("/incidents/{incident_id}/dispatch", response_model=DispatchResponse)
async def dispatch_response(incident_id: str, db: Session = Depends(get_db)):
    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if not inc:
        raise HTTPException(404, "Incident not found")

    rec = (db.query(Recommendation)
           .filter(Recommendation.incident_id == incident_id)
           .order_by(Recommendation.created_at.desc())
           .first())
    if not rec:
        # Auto-analyze if frontend skips the Admin panel!
        await analyze_incident(db, inc)
        rec = (db.query(Recommendation)
               .filter(Recommendation.incident_id == incident_id)
               .order_by(Recommendation.created_at.desc())
               .first())
        if not rec:
            raise HTTPException(400, "Failed to auto-generate routing recommendation.")

    # Create dispatch
    dispatch_id = f"DSP-{random.randint(1000,9999)}"
    dispatch = Dispatch(
        id=dispatch_id,
        incident_id=incident_id,
        fire_station_id=rec.fire_station_id,
        fire_truck_id=rec.fire_truck_id,
        ambulance_id=rec.ambulance_id,
        hospital_id=rec.hospital_id,
        route=rec.route,
        eta_minutes=rec.eta_minutes,
        confidence=rec.confidence,
        reasons=rec.reasons,
        status="Dispatched",
    )
    db.add(dispatch)

    # Update incident status
    inc.status = "Dispatched"
    inc.updated_at = datetime.now(timezone.utc)

    # Update resource statuses
    if rec.ambulance_id:
        amb = db.query(Ambulance).filter(Ambulance.id == rec.ambulance_id).first()
        if amb:
            amb.status = "En Route"
            amb.current_incident_id = incident_id

    if rec.fire_truck_id:
        truck = db.query(FireTruck).filter(FireTruck.id == rec.fire_truck_id).first()
        if truck:
            truck.status = "En Route"
            truck.current_incident_id = incident_id

    if rec.fire_station_id:
        station = db.query(FireStation).filter(FireStation.id == rec.fire_station_id).first()
        if station:
            station.status = "Dispatched"
            station.available_trucks = max(0, station.available_trucks - 1)

    db.commit()
    db.refresh(dispatch)

    # Activity logs
    log = ActivityLog(incident_id=incident_id, event_type="DISPATCH_CREATED",
                      message=f"🚨 Response dispatched for {incident_id}",
                      severity="critical", icon="🚨")
    db.add(log)
    db.commit()

    # Publish to Fabric
    fabric_service.publish_event_sync("DISPATCH_CREATED", {
        "dispatch_id": dispatch.id,
        "incident_id": incident_id,
        "fire_station": rec.fire_station_name,
        "ambulance": rec.ambulance_id,
        "hospital": rec.hospital_name,
        "eta_minutes": rec.eta_minutes,
    })

    # Broadcast
    await ws_manager.broadcast("DISPATCH_CREATED", {
        "dispatch_id": dispatch.id,
        "incident_id": incident_id,
        "fire_station_id": rec.fire_station_id,
        "fire_station_name": rec.fire_station_name,
        "ambulance_id": rec.ambulance_id,
        "hospital_id": rec.hospital_id,
        "hospital_name": rec.hospital_name,
        "status": "Dispatched",
    })
    await ws_manager.broadcast("INCIDENT_UPDATED", {
        "id": inc.id, "status": inc.status,
    })
    if rec.ambulance_id:
        await ws_manager.broadcast("RESOURCE_UPDATED", {
            "type": "ambulance", "id": rec.ambulance_id, "status": "En Route",
        })
    if rec.fire_truck_id:
        await ws_manager.broadcast("RESOURCE_UPDATED", {
            "type": "fire_truck", "id": rec.fire_truck_id, "status": "En Route",
        })

    return dispatch
