"""CrisisFlow API — Incident Routes"""
import uuid
import random
from typing import Optional, List
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import (
    Incident, Recommendation, DecisionAudit, Dispatch, ActivityLog,
    Ambulance, FireStation, FireTruck, Hospital, utcnow,
)
from app.schemas import (
    IncidentCreate, IncidentResponse, IncidentUpdate,
    RecommendationResponse, DispatchResponse, DispatchRequest, DecisionAuditResponse,
    BulkAcknowledgeRequest, BulkDispatchRequest, BulkOperationResponse, TimelineEventResponse,
)
from app.services.decision_engine import auto_detect_severity, assess_spread_risk, generate_recommendation
from app.services.ai_service import get_ai_provider
from app.services.fabric_service import fabric_service
from app.services.simulation_service import analyze_incident
from app.realtime.manager import ws_manager

router = APIRouter(prefix="/api", tags=["incidents"])


# ─── List & Create ───
@router.get("/incidents", response_model=List[IncidentResponse])
def list_incidents(db: Session = Depends(get_db)):
    return db.query(Incident).order_by(Incident.created_at.desc()).all()


@router.post("/incidents", response_model=IncidentResponse)
async def create_incident(data: IncidentCreate, db: Session = Depends(get_db)):
    count = db.query(Incident).count()
    inc_id = f"INC-{2400 + count + 1}"

    severity = data.severity
    if severity == "Auto Detect":
        severity = auto_detect_severity(data.incident_type, data.people_at_risk, data.floor)

    # Duplicate Report Detection (check active incidents within 0.5km)
    import math
    def _dist_km(lat1, lon1, lat2, lon2):
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = (math.sin(dlat / 2) ** 2 +
             math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
             math.sin(dlon / 2) ** 2)
        return 6371.0 * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    existing_active = db.query(Incident).filter(Incident.status != "Resolved").all()
    duplicate_match = None
    for act in existing_active:
        d_km = _dist_km(data.latitude, data.longitude, act.latitude, act.longitude)
        if d_km <= 0.5 and (act.incident_type == data.incident_type or act.zone == (data.zone or "Central")):
            duplicate_match = act
            break

    incident = Incident(
        id=inc_id,
        incident_type=data.incident_type,
        location=data.location,
        zone=data.zone or "Central",
        latitude=data.latitude,
        longitude=data.longitude,
        floor=data.floor,
        building=data.building,
        severity=severity,
        people_at_risk=data.people_at_risk,
        description=data.description,
        status="Detected",
        is_duplicate=duplicate_match is not None,
        duplicate_of_id=duplicate_match.id if duplicate_match else None,
        is_simulated=False,
    )
    incident.spread_risk = assess_spread_risk(incident)
    db.add(incident)
    db.commit()
    db.refresh(incident)

    if duplicate_match:
        log_dup = ActivityLog(
            incident_id=inc_id,
            event_type="DUPLICATE_REPORT_FLAGGED",
            message=f"⚠️ DUPLICATE REPORT DETECTED: Incident {inc_id} matches active incident {duplicate_match.id} near {incident.location}. Linked as duplicate report.",
            severity="warning",
            icon="⚠️",
            timestamp=utcnow(),
        )
        db.add(log_dup)
        db.commit()

    # Publish standard business event to Fabric
    await fabric_service.publish_event(
        event_type="incident.created",
        payload={
            "incident_id": incident.id,
            "incident_type": incident.incident_type,
            "location": incident.location,
            "latitude": incident.latitude,
            "longitude": incident.longitude,
            "severity": incident.severity,
            "people_at_risk": incident.people_at_risk,
            "status": incident.status,
            "zone": incident.zone,
        },
        entity_id=incident.id,
        zone=incident.zone,
    )

    # Activity log
    log = ActivityLog(
        incident_id=inc_id,
        event_type="INCIDENT_CREATED",
        message=f"New {incident.incident_type} at {incident.location} ({incident.zone})",
        severity="critical" if incident.severity in ("Critical", "High") else "info",
        icon="🚨",
    )
    db.add(log)
    db.commit()

    # Realtime WebSocket broadcast
    await ws_manager.broadcast("INCIDENT_CREATED", {
        "id": incident.id,
        "incident_type": incident.incident_type,
        "location": incident.location,
        "zone": incident.zone,
        "latitude": incident.latitude,
        "longitude": incident.longitude,
        "severity": incident.severity,
        "people_at_risk": incident.people_at_risk,
        "status": incident.status,
        "floor": incident.floor,
        "building": incident.building,
        "spread_risk": incident.spread_risk,
    }, entity_id=incident.id, zone=incident.zone)

    return incident


# ─── Bulk Actions (Defined before /{incident_id} routes to prevent path conflict) ───
@router.post("/incidents/bulk/acknowledge", response_model=BulkOperationResponse)
async def bulk_acknowledge_incidents(
    request: BulkAcknowledgeRequest = Body(...),
    db: Session = Depends(get_db),
):
    successful = []
    failed = []
    errors = {}

    for inc_id in request.incident_ids:
        try:
            inc = db.query(Incident).filter(Incident.id == inc_id).first()
            if not inc:
                failed.append(inc_id)
                errors[inc_id] = "Incident not found"
                continue

            if inc.status in ("Resolved", "Dispatched", "Response In Progress"):
                successful.append(inc_id)
                continue

            inc.status = "Awaiting Response"
            inc.updated_at = utcnow()

            log = ActivityLog(
                incident_id=inc.id,
                event_type="INCIDENT_ACKNOWLEDGED",
                message=f"Incident {inc.id} acknowledged by commander",
                severity="info",
                icon="👁️",
            )
            db.add(log)

            await fabric_service.publish_event(
                event_type="incident.acknowledged",
                payload={
                    "incident_id": inc.id,
                    "status": inc.status,
                    "zone": inc.zone,
                },
                entity_id=inc.id,
                zone=inc.zone,
            )

            await ws_manager.broadcast("INCIDENT_UPDATED", {
                "id": inc.id,
                "status": inc.status,
                "zone": inc.zone,
            }, entity_id=inc.id, zone=inc.zone)

            successful.append(inc_id)
        except Exception as e:
            failed.append(inc_id)
            errors[inc_id] = str(e)

    db.commit()
    msg = f"{len(successful)} incident(s) acknowledged."
    if failed:
        msg += f" {len(failed)} failed."
    return BulkOperationResponse(
        successful=successful,
        failed=failed,
        errors=errors,
        message=msg,
    )


@router.post("/incidents/bulk/dispatch", response_model=BulkOperationResponse)
async def bulk_dispatch_incidents(
    request: BulkDispatchRequest = Body(...),
    db: Session = Depends(get_db),
):
    successful = []
    failed = []
    errors = {}

    for inc_id in request.incident_ids:
        try:
            inc = db.query(Incident).filter(Incident.id == inc_id).first()
            if not inc:
                failed.append(inc_id)
                errors[inc_id] = "Incident not found"
                continue

            if inc.status in ("Dispatched", "Response In Progress", "Resolved"):
                successful.append(inc_id)
                continue

            rec = (
                db.query(Recommendation)
                .filter(Recommendation.incident_id == inc_id)
                .order_by(Recommendation.created_at.desc())
                .first()
            )
            if not rec:
                rec, _ = generate_recommendation(db, inc)
                db.add(rec)
                db.commit()

            dispatch_id = f"DSP-{uuid.uuid4().hex[:8]}"
            dispatch = Dispatch(
                id=dispatch_id,
                incident_id=inc.id,
                resource_id=rec.ambulance_id or rec.fire_truck_id,
                fire_station_id=rec.fire_station_id,
                fire_truck_id=rec.fire_truck_id,
                ambulance_id=rec.ambulance_id,
                hospital_id=rec.hospital_id,
                route=rec.route,
                eta_minutes=rec.eta_minutes,
                distance_km=0.0,
                confidence=rec.confidence,
                reasons=rec.reasons,
                status="Dispatched",
                assigned_at=utcnow(),
                created_at=utcnow(),
            )
            db.add(dispatch)

            inc.status = "Dispatched"
            inc.updated_at = utcnow()

            if rec.ambulance_id:
                amb = db.query(Ambulance).filter(Ambulance.id == rec.ambulance_id).first()
                if amb:
                    amb.status = "En Route"
                    amb.current_incident_id = inc.id
                    amb.updated_at = utcnow()

            if rec.fire_truck_id:
                truck = db.query(FireTruck).filter(FireTruck.id == rec.fire_truck_id).first()
                if truck:
                    truck.status = "En Route"
                    truck.current_incident_id = inc.id
                    truck.updated_at = utcnow()

            if rec.fire_station_id:
                station = db.query(FireStation).filter(FireStation.id == rec.fire_station_id).first()
                if station:
                    station.status = "Dispatched"
                    station.available_trucks = max(0, station.available_trucks - 1)
                    station.updated_at = utcnow()

            log = ActivityLog(
                incident_id=inc.id,
                event_type="DISPATCH_CREATED",
                message=f"Batch dispatch executed for {inc.id}",
                severity="critical",
                icon="🚨",
            )
            db.add(log)
            db.commit()

            await fabric_service.publish_event(
                event_type="dispatch.created",
                payload={
                    "dispatch_id": dispatch.id,
                    "incident_id": inc.id,
                    "ambulance_id": rec.ambulance_id,
                    "hospital_id": rec.hospital_id,
                    "eta_minutes": dispatch.eta_minutes,
                },
                entity_id=dispatch.id,
                zone=inc.zone,
            )

            await ws_manager.broadcast("DISPATCH_CREATED", {
                "dispatch_id": dispatch.id,
                "incident_id": inc.id,
                "ambulance_id": rec.ambulance_id,
                "hospital_id": rec.hospital_id,
                "status": "Dispatched",
            }, entity_id=dispatch.id, zone=inc.zone)

            await ws_manager.broadcast("INCIDENT_UPDATED", {
                "id": inc.id,
                "status": inc.status,
            }, entity_id=inc.id, zone=inc.zone)

            successful.append(inc_id)
        except Exception as e:
            failed.append(inc_id)
            errors[inc_id] = str(e)

    db.commit()
    msg = f"{len(successful)} incident(s) dispatched."
    if failed:
        msg += f" {len(failed)} failed."
    return BulkOperationResponse(
        successful=successful,
        failed=failed,
        errors=errors,
        message=msg,
    )


# ─── Individual Incident Detail & Operations ───
@router.get("/incidents/{incident_id}", response_model=IncidentResponse)
def get_incident(incident_id: str, db: Session = Depends(get_db)):
    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if not inc:
        raise HTTPException(404, "Incident not found")
    return inc


@router.put("/incidents/{incident_id}", response_model=IncidentResponse)
async def update_incident(incident_id: str, data: IncidentUpdate, db: Session = Depends(get_db)):
    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if not inc:
        raise HTTPException(404, "Incident not found")
    if data.status:
        inc.status = data.status
    if data.severity:
        inc.severity = data.severity
    if data.zone:
        inc.zone = data.zone
    if data.people_at_risk is not None:
        inc.people_at_risk = data.people_at_risk
    if data.description:
        inc.description = data.description
    inc.updated_at = utcnow()
    db.commit()
    db.refresh(inc)

    await fabric_service.publish_event(
        event_type="incident.updated",
        payload={
            "incident_id": inc.id,
            "status": inc.status,
            "severity": inc.severity,
            "zone": inc.zone,
        },
        entity_id=inc.id,
        zone=inc.zone,
    )

    await ws_manager.broadcast("INCIDENT_UPDATED", {
        "id": inc.id,
        "status": inc.status,
        "severity": inc.severity,
        "zone": inc.zone,
    }, entity_id=inc.id, zone=inc.zone)

    return inc


@router.delete("/incidents/{incident_id}")
def delete_incident(incident_id: str, db: Session = Depends(get_db)):
    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if not inc:
        raise HTTPException(404, "Incident not found")
    db.delete(inc)
    db.commit()
    return {"message": "Deleted", "id": incident_id}


@router.get("/incidents/{incident_id}/timeline", response_model=List[TimelineEventResponse])
def get_incident_timeline(incident_id: str, db: Session = Depends(get_db)):
    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if not inc:
        raise HTTPException(404, "Incident not found")

    logs = (
        db.query(ActivityLog)
        .filter(ActivityLog.incident_id == incident_id)
        .order_by(ActivityLog.timestamp.asc())
        .all()
    )

    events: List[TimelineEventResponse] = []

    if not logs:
        events.append(TimelineEventResponse(
            id=f"evt-{inc.id}-created",
            incident_id=inc.id,
            event_type="INCIDENT_CREATED",
            title="Incident Detected",
            description=f"{inc.incident_type} reported at {inc.location} ({inc.zone})",
            severity="critical" if inc.severity in ("Critical", "High") else "info",
            icon="🚨",
            timestamp=inc.created_at or utcnow(),
        ))
        rec = db.query(Recommendation).filter(Recommendation.incident_id == incident_id).first()
        if rec and rec.created_at:
            events.append(TimelineEventResponse(
                id=f"evt-{inc.id}-rec",
                incident_id=inc.id,
                event_type="RECOMMENDATION_GENERATED",
                title="AI Recommendation Generated",
                description=f"Optimal resource identified with {rec.confidence}% confidence (ETA: {rec.eta_minutes} min)",
                severity="info",
                icon="🧠",
                timestamp=rec.created_at,
            ))
        dsp = db.query(Dispatch).filter(Dispatch.incident_id == incident_id).first()
        if dsp and dsp.assigned_at:
            events.append(TimelineEventResponse(
                id=f"evt-{inc.id}-dsp",
                incident_id=inc.id,
                event_type="DISPATCH_CREATED",
                title="Units Dispatched",
                description=f"Resource {dsp.ambulance_id or dsp.fire_truck_id or 'Unit'} dispatched to scene",
                severity="critical",
                icon="🚑",
                timestamp=dsp.assigned_at,
            ))
        if inc.status == "Resolved" and inc.updated_at:
            events.append(TimelineEventResponse(
                id=f"evt-{inc.id}-resolved",
                incident_id=inc.id,
                event_type="INCIDENT_RESOLVED",
                title="Incident Resolved",
                description="All operations completed and scene cleared.",
                severity="available",
                icon="✅",
                timestamp=inc.updated_at,
            ))
    else:
        for idx, log in enumerate(logs):
            title = log.event_type.replace("_", " ").title()
            events.append(TimelineEventResponse(
                id=f"evt-{inc.id}-{log.id or idx}",
                incident_id=inc.id,
                event_type=log.event_type,
                title=title,
                description=log.message,
                severity=log.severity,
                icon=log.icon or "📋",
                timestamp=log.timestamp or utcnow(),
            ))

    return events


@router.post("/incidents/{incident_id}/analyze")
async def analyze(incident_id: str, db: Session = Depends(get_db)):
    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if not inc:
        raise HTTPException(404, "Incident not found")
    result = await analyze_incident(db, inc)
    return result


@router.get("/incidents/{incident_id}/recommendation", response_model=RecommendationResponse)
def get_recommendation(incident_id: str, db: Session = Depends(get_db)):
    rec = (
        db.query(Recommendation)
        .filter(Recommendation.incident_id == incident_id)
        .order_by(Recommendation.created_at.desc())
        .first()
    )
    if not rec:
        raise HTTPException(404, "No recommendation found for this incident")
    return rec


@router.get("/incidents/{incident_id}/audit", response_model=DecisionAuditResponse)
def get_incident_audit(incident_id: str, db: Session = Depends(get_db)):
    audit = (
        db.query(DecisionAudit)
        .filter(DecisionAudit.incident_id == incident_id)
        .order_by(DecisionAudit.created_at.desc())
        .first()
    )
    if not audit:
        raise HTTPException(404, f"No decision audit found for incident {incident_id}")
    return audit


@router.post("/incidents/{incident_id}/dispatch", response_model=DispatchResponse)
async def dispatch_response(
    incident_id: str,
    body: Optional[DispatchRequest] = None,
    db: Session = Depends(get_db),
):
    inc = db.query(Incident).filter(Incident.id == incident_id).first()
    if not inc:
        raise HTTPException(404, "Incident not found")

    rec = (
        db.query(Recommendation)
        .filter(Recommendation.incident_id == incident_id)
        .order_by(Recommendation.created_at.desc())
        .first()
    )
    if not rec:
        raise HTTPException(400, "No recommendation found — analyze the incident first")

    # Determine assigned units (respecting human override if provided)
    ambulance_id = (body.ambulance_id if body and body.ambulance_id else rec.ambulance_id)
    fire_truck_id = (body.fire_truck_id if body and body.fire_truck_id else rec.fire_truck_id)
    hospital_id = (body.hospital_id if body and body.hospital_id else rec.hospital_id)
    human_override = bool(body and body.human_override)

    dispatch_id = f"DSP-{uuid.uuid4().hex[:8]}"
    dispatch = Dispatch(
        id=dispatch_id,
        incident_id=incident_id,
        resource_id=ambulance_id or fire_truck_id,
        fire_station_id=rec.fire_station_id,
        fire_truck_id=fire_truck_id,
        ambulance_id=ambulance_id,
        hospital_id=hospital_id,
        route=rec.route,
        eta_minutes=rec.eta_minutes,
        distance_km=0.0,
        confidence=rec.confidence,
        reasons=rec.reasons,
        status="Dispatched",
        assigned_at=utcnow(),
        created_at=utcnow(),
    )
    db.add(dispatch)

    # Update incident status
    inc.status = "Dispatched"
    inc.updated_at = utcnow()

    # Update resource statuses
    if ambulance_id:
        amb = db.query(Ambulance).filter(Ambulance.id == ambulance_id).first()
        if amb:
            amb.status = "En Route"
            amb.current_incident_id = incident_id
            amb.updated_at = utcnow()

    if fire_truck_id:
        truck = db.query(FireTruck).filter(FireTruck.id == fire_truck_id).first()
        if truck:
            truck.status = "En Route"
            truck.current_incident_id = incident_id
            truck.updated_at = utcnow()

    if rec.fire_station_id:
        station = db.query(FireStation).filter(FireStation.id == rec.fire_station_id).first()
        if station:
            station.status = "Dispatched"
            station.available_trucks = max(0, station.available_trucks - 1)
            station.updated_at = utcnow()

    # If human override, update DecisionAudit record
    audit = (
        db.query(DecisionAudit)
        .filter(DecisionAudit.incident_id == incident_id)
        .order_by(DecisionAudit.created_at.desc())
        .first()
    )
    if audit:
        audit.human_override = human_override
        audit.final_decision = {
            "dispatch_id": dispatch.id,
            "ambulance_id": ambulance_id,
            "fire_truck_id": fire_truck_id,
            "hospital_id": hospital_id,
            "human_override": human_override,
            "override_notes": body.notes if body else None,
        }

    db.commit()
    db.refresh(dispatch)

    # Activity log
    log = ActivityLog(
        incident_id=incident_id,
        event_type="DISPATCH_CREATED",
        message=f"🚨 Response dispatched for {incident_id}" + (" (Human Override)" if human_override else ""),
        severity="critical",
        icon="🚨",
    )
    db.add(log)
    db.commit()

    # Publish standard dispatch event to Fabric
    await fabric_service.publish_event(
        event_type="dispatch.created",
        payload={
            "dispatch_id": dispatch.id,
            "incident_id": incident_id,
            "ambulance_id": ambulance_id,
            "fire_station_id": rec.fire_station_id,
            "hospital_id": hospital_id,
            "eta_minutes": dispatch.eta_minutes,
            "confidence": dispatch.confidence,
            "human_override": human_override,
        },
        entity_id=dispatch.id,
        zone=inc.zone,
    )

    # Realtime WebSocket broadcasts
    await ws_manager.broadcast("DISPATCH_CREATED", {
        "dispatch_id": dispatch.id,
        "incident_id": incident_id,
        "fire_station_id": rec.fire_station_id,
        "fire_station_name": rec.fire_station_name,
        "ambulance_id": ambulance_id,
        "hospital_id": hospital_id,
        "hospital_name": rec.hospital_name,
        "status": "Dispatched",
        "human_override": human_override,
    }, entity_id=dispatch.id, zone=inc.zone)

    await ws_manager.broadcast("INCIDENT_UPDATED", {
        "id": inc.id,
        "status": inc.status,
    }, entity_id=inc.id, zone=inc.zone)

    if ambulance_id:
        await ws_manager.broadcast("RESOURCE_UPDATED", {
            "type": "ambulance", "id": ambulance_id, "status": "En Route",
        }, entity_id=ambulance_id, zone=inc.zone)

    if fire_truck_id:
        await ws_manager.broadcast("RESOURCE_UPDATED", {
            "type": "fire_truck", "id": fire_truck_id, "status": "En Route",
        }, entity_id=fire_truck_id, zone=inc.zone)

    return dispatch
