"""
CrisisFlow Simulation Service
──────────────────────────────
Deterministic, repeatable emergency scenario generator and background physics simulation.
All scenarios execute through the REAL incident creation, optimization, recommendation,
decision audit, and eventstream pipeline.
"""
import uuid
import random
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from app.models import (
    Incident, Ambulance, FireStation, FireTruck, Hospital,
    TrafficCondition, WeatherCondition, WeatherEvent, RoadBlock,
    RiskZone, ActivityLog, SimulationRun, Dispatch, utcnow,
)
from app.services.decision_engine import (
    generate_recommendation, auto_detect_severity, assess_spread_risk,
)
from app.services.ai_service import get_ai_provider
from app.services.fabric_service import fabric_service
from app.realtime.manager import ws_manager


def _next_incident_id(db: Session) -> str:
    count = db.query(Incident).count()
    return f"INC-{2400 + count + 1}"


def _create_activity(db: Session, incident_id: str, event_type: str,
                     message: str, severity: str = "info", icon: str = "📋"):
    log = ActivityLog(
        incident_id=incident_id,
        event_type=event_type,
        message=message,
        severity=severity,
        icon=icon,
        timestamp=utcnow(),
    )
    db.add(log)
    db.commit()
    return log


async def _broadcast_activity(incident_id: str, event_type: str,
                               message: str, icon: str = "📋", zone: str = "Central"):
    await ws_manager.broadcast("ACTIVITY", {
        "incident_id": incident_id,
        "event_type": event_type,
        "message": message,
        "icon": icon,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }, entity_id=incident_id, zone=zone)


# ═══════════════════════════════════════════════════════════
# ANALYZE INCIDENT (END-TO-END PIPELINE)
# ═══════════════════════════════════════════════════════════

async def analyze_incident(db: Session, incident: Incident) -> Dict[str, Any]:
    """Full pipeline: classify → score → recommend → explain → audit → eventstream."""
    incident.status = "Analyzing"
    incident.spread_risk = assess_spread_risk(incident)
    db.commit()

    _create_activity(db, incident.id, "INCIDENT_ANALYZING",
                     f"🧠 Analyzing incident {incident.id} ({incident.severity})", "info", "🧠")
    await _broadcast_activity(incident.id, "INCIDENT_ANALYZING",
                               f"🧠 Decision Engine analyzing {incident.id}", "🧠", zone=incident.zone)

    # Deterministic Decision Engine Optimization
    rec, audit = generate_recommendation(db, incident)

    if rec:
        # AI explanation synthesis
        ai = get_ai_provider()
        rec.explanation = ai.explain_recommendation(incident, rec)
        db.commit()

        incident.status = "Awaiting Response"
        db.commit()

        _create_activity(db, incident.id, "RECOMMENDATION_GENERATED",
                         f"🚒 Recommendation generated for {incident.id} | Score: {rec.score}% | ETA: {rec.eta_minutes} min",
                         "info", "🎯")
        await _broadcast_activity(incident.id, "RECOMMENDATION_GENERATED",
                                   f"🎯 Recommendation generated for {incident.id}", "🎯", zone=incident.zone)

        # Publish decision event to Fabric
        await fabric_service.publish_event(
            event_type="decision.created",
            payload={
                "incident_id": incident.id,
                "recommendation_id": rec.id,
                "ambulance_id": rec.ambulance_id,
                "fire_station_id": rec.fire_station_id,
                "hospital_id": rec.hospital_id,
                "eta_minutes": rec.eta_minutes,
                "confidence": rec.confidence,
                "score_breakdown": rec.score_breakdown,
                "audit_id": audit.id if audit else None,
            },
            entity_id=rec.id,
            zone=incident.zone,
        )

        # WebSocket broadcast
        await ws_manager.broadcast("RECOMMENDATION_GENERATED", {
            "incident_id": incident.id,
            "recommendation_id": rec.id,
            "fire_station_id": rec.fire_station_id,
            "fire_station_name": rec.fire_station_name,
            "fire_truck_id": rec.fire_truck_id,
            "ambulance_id": rec.ambulance_id,
            "hospital_id": rec.hospital_id,
            "hospital_name": rec.hospital_name,
            "route": rec.route,
            "eta_minutes": rec.eta_minutes,
            "score": rec.score,
            "confidence": rec.confidence,
            "reasons": rec.reasons,
            "score_breakdown": rec.score_breakdown,
            "explanation": rec.explanation,
            "audit_id": audit.id if audit else None,
        }, entity_id=rec.id, zone=incident.zone)

    await ws_manager.broadcast("INCIDENT_UPDATED", {
        "id": incident.id, "status": incident.status,
        "severity": incident.severity, "spread_risk": incident.spread_risk,
    }, entity_id=incident.id, zone=incident.zone)

    return {
        "incident": {
            "id": incident.id,
            "incident_type": incident.incident_type,
            "location": incident.location,
            "zone": incident.zone,
            "severity": incident.severity,
            "status": incident.status,
            "spread_risk": incident.spread_risk,
            "people_at_risk": incident.people_at_risk,
        },
        "recommendation": {
            "id": rec.id if rec else None,
            "fire_station": rec.fire_station_name if rec else None,
            "fire_truck": rec.fire_truck_id if rec else None,
            "ambulance": rec.ambulance_id if rec else None,
            "hospital": rec.hospital_name if rec else None,
            "route": rec.route if rec else None,
            "eta_minutes": rec.eta_minutes if rec else None,
            "score": rec.score if rec else None,
            "confidence": rec.confidence if rec else None,
            "reasons": rec.reasons if rec else [],
            "score_breakdown": rec.score_breakdown if rec else {},
            "explanation": rec.explanation if rec else None,
        } if rec else None,
        "decision_audit": {
            "id": audit.id if audit else None,
            "confidence": audit.confidence if audit else None,
            "score_breakdown": audit.score_breakdown if audit else {},
            "rejected_candidates_count": len(audit.rejected_candidates) if audit else 0,
        } if audit else None,
    }


# ═══════════════════════════════════════════════════════════
# 6 REPEATABLE DEMO SCENARIOS
# ═══════════════════════════════════════════════════════════

async def simulate_major_accident(db: Session) -> Dict[str, Any]:
    """
    Scenario 1: MAJOR ACCIDENT
    Zone: Gachibowli | Severity: Critical | Vehicles: 6 | Casualties: 12 | Heavy Traffic
    """
    inc_id = _next_incident_id(db)
    incident = Incident(
        id=inc_id,
        incident_type="Road Accident",
        location="Gachibowli Junction, Outer Ring Road",
        zone="Gachibowli",
        latitude=17.4401,
        longitude=78.3489,
        severity="Critical",
        people_at_risk=12,
        description="Major 6-vehicle pileup on Gachibowli ORR flyover. 12 casualties reported, 3 trapped in crushed vehicle.",
        status="Detected",
        spread_risk="Low",
        is_simulated=True,
    )
    db.add(incident)

    # Set traffic conditions
    tr = db.query(TrafficCondition).filter(TrafficCondition.from_location == "Gachibowli").first()
    if tr:
        tr.congestion_level = 0.85
        tr.estimated_delay_minutes = 12.0

    # Record simulation run
    sim_run = SimulationRun(
        id=f"SIM-{uuid.uuid4().hex[:8]}",
        scenario_name="MAJOR_ACCIDENT",
        zone="Gachibowli",
        severity="Critical",
        status="Completed",
        details={"vehicles": 6, "casualties": 12, "ambulances_required": 3, "traffic": "Heavy"},
        created_at=utcnow(),
    )
    db.add(sim_run)
    db.commit()
    db.refresh(incident)

    await fabric_service.publish_event(
        event_type="incident.created",
        payload={
            "incident_id": incident.id,
            "incident_type": incident.incident_type,
            "location": incident.location,
            "zone": incident.zone,
            "severity": incident.severity,
            "people_at_risk": incident.people_at_risk,
        },
        entity_id=incident.id,
        zone=incident.zone,
    )

    _create_activity(db, inc_id, "INCIDENT_DETECTED",
                     f"🚗 Critical 6-Vehicle Collision in {incident.zone} ({incident.people_at_risk} victims)", "critical", "🚗")
    await _broadcast_activity(inc_id, "INCIDENT_DETECTED",
                               f"🚗 Critical Pileup in Gachibowli ({incident.people_at_risk} victims)", "🚗", zone=incident.zone)

    await ws_manager.broadcast("INCIDENT_CREATED", {
        "id": incident.id, "incident_type": incident.incident_type,
        "location": incident.location, "zone": incident.zone,
        "latitude": incident.latitude, "longitude": incident.longitude,
        "severity": incident.severity, "people_at_risk": incident.people_at_risk,
        "status": incident.status, "is_simulated": True,
    }, entity_id=incident.id, zone=incident.zone)

    await asyncio.sleep(0.2)
    return await analyze_incident(db, incident)


async def simulate_fire(db: Session) -> Dict[str, Any]:
    """
    Scenario 2: BUILDING FIRE
    Zone: HITEC City | Severity: Critical | Floor: 7 | People at risk: 85 | High fire spread risk
    """
    inc_id = _next_incident_id(db)
    incident = Incident(
        id=inc_id,
        incident_type="Building Fire",
        location="Tower A, Cyber Gateway, HITEC City",
        zone="HITEC City",
        latitude=17.4435,
        longitude=78.3772,
        floor=7,
        building="Tower A",
        severity="Critical",
        people_at_risk=85,
        description="Major commercial fire reported on 7th floor of Tower A. 85 occupants trapped above fire line. Rapid smoke migration.",
        status="Detected",
        spread_risk="High",
        is_simulated=True,
    )
    db.add(incident)

    sim_run = SimulationRun(
        id=f"SIM-{uuid.uuid4().hex[:8]}",
        scenario_name="BUILDING_FIRE",
        zone="HITEC City",
        severity="Critical",
        status="Completed",
        details={"floor": 7, "people_at_risk": 85, "spread_risk": "High", "fire_units_required": 3},
        created_at=utcnow(),
    )
    db.add(sim_run)
    db.commit()
    db.refresh(incident)

    await fabric_service.publish_event(
        event_type="incident.created",
        payload={
            "incident_id": incident.id,
            "incident_type": incident.incident_type,
            "location": incident.location,
            "zone": incident.zone,
            "severity": incident.severity,
            "floor": incident.floor,
            "people_at_risk": incident.people_at_risk,
        },
        entity_id=incident.id,
        zone=incident.zone,
    )

    _create_activity(db, inc_id, "INCIDENT_DETECTED",
                     f"🔥 4-Alarm High-Rise Fire at {incident.location} (Floor {incident.floor})", "critical", "🔥")
    await _broadcast_activity(inc_id, "INCIDENT_DETECTED",
                               f"🔥 Major Fire at {incident.location}", "🔥", zone=incident.zone)

    await ws_manager.broadcast("INCIDENT_CREATED", {
        "id": incident.id, "incident_type": incident.incident_type,
        "location": incident.location, "zone": incident.zone,
        "latitude": incident.latitude, "longitude": incident.longitude,
        "severity": incident.severity, "people_at_risk": incident.people_at_risk,
        "status": incident.status, "floor": incident.floor, "building": incident.building,
        "spread_risk": incident.spread_risk, "is_simulated": True,
    }, entity_id=incident.id, zone=incident.zone)

    await asyncio.sleep(0.2)
    return await analyze_incident(db, incident)


async def simulate_flood(db: Session) -> Dict[str, Any]:
    """
    Scenario 3: FLASH FLOOD
    Zone: Madhapur | Severity: High | Rainfall: 78 mm/hr | Flood depth: 0.65m | Evacuation active
    """
    inc_id = _next_incident_id(db)
    incident = Incident(
        id=inc_id,
        incident_type="Flood",
        location="Madhapur Lowline Canal & Metro Link",
        zone="Madhapur",
        latitude=17.4486,
        longitude=78.3908,
        severity="High",
        people_at_risk=45,
        description="Sudden flash flood inundation. 78 mm/hr intense precipitation causing 0.65m standing water. 4 roads submerged.",
        status="Detected",
        spread_risk="High",
        is_simulated=True,
    )
    db.add(incident)

    # Add weather event and road block
    we = WeatherEvent(
        id=f"WE-{uuid.uuid4().hex[:6]}",
        location="Madhapur Basin",
        zone="Madhapur",
        condition="Heavy Thunderstorm",
        rainfall_mm_hr=78.0,
        flood_depth_m=0.65,
        wind_speed=45.0,
        risk_factor=0.85,
        created_at=utcnow(),
    )
    db.add(we)

    rb = RoadBlock(
        id=f"RB-{uuid.uuid4().hex[:6]}",
        road_name="Madhapur 100ft Road",
        zone="Madhapur",
        reason="0.65m Waterlogging / Flash Flood",
        severity="High",
        latitude=17.4486,
        longitude=78.3908,
        delay_minutes=25.0,
        is_active=True,
        created_at=utcnow(),
    )
    db.add(rb)

    sim_run = SimulationRun(
        id=f"SIM-{uuid.uuid4().hex[:8]}",
        scenario_name="FLASH_FLOOD",
        zone="Madhapur",
        severity="High",
        status="Completed",
        details={"rainfall_mm_hr": 78, "flood_depth_m": 0.65, "roads_affected": 4, "evacuation": True},
        created_at=utcnow(),
    )
    db.add(sim_run)
    db.commit()
    db.refresh(incident)

    await fabric_service.publish_event(
        event_type="incident.created",
        payload={
            "incident_id": incident.id,
            "incident_type": incident.incident_type,
            "location": incident.location,
            "zone": incident.zone,
            "severity": incident.severity,
            "rainfall_mm_hr": 78.0,
            "flood_depth_m": 0.65,
        },
        entity_id=incident.id,
        zone=incident.zone,
    )

    _create_activity(db, inc_id, "INCIDENT_DETECTED",
                     f"🌊 Flash Flood in {incident.zone} — depth 0.65m, 4 roads blocked", "high", "🌊")
    await _broadcast_activity(inc_id, "INCIDENT_DETECTED",
                               f"🌊 Flash Flood in Madhapur (0.65m depth)", "🌊", zone=incident.zone)

    await ws_manager.broadcast("INCIDENT_CREATED", {
        "id": incident.id, "incident_type": incident.incident_type,
        "location": incident.location, "zone": incident.zone,
        "latitude": incident.latitude, "longitude": incident.longitude,
        "severity": incident.severity, "people_at_risk": incident.people_at_risk,
        "status": incident.status, "spread_risk": incident.spread_risk, "is_simulated": True,
    }, entity_id=incident.id, zone=incident.zone)

    await asyncio.sleep(0.2)
    return await analyze_incident(db, incident)


async def simulate_medical(db: Session) -> Dict[str, Any]:
    """
    Scenario 4: MEDICAL EMERGENCY (Cardiac Emergency)
    Zone: Banjara Hills | Severity: High | Patients: 2 | Specialty: Cardiology
    """
    inc_id = _next_incident_id(db)
    incident = Incident(
        id=inc_id,
        incident_type="Medical Emergency",
        location="Road No. 12, Banjara Hills",
        zone="Banjara Hills",
        latitude=17.4250,
        longitude=78.4400,
        severity="High",
        people_at_risk=2,
        description="Acute cardiac arrest and severe respiratory distress at commercial center. CPR in progress.",
        status="Detected",
        spread_risk="Low",
        is_simulated=True,
    )
    db.add(incident)

    sim_run = SimulationRun(
        id=f"SIM-{uuid.uuid4().hex[:8]}",
        scenario_name="MEDICAL_EMERGENCY",
        zone="Banjara Hills",
        severity="High",
        status="Completed",
        details={"condition": "Cardiac Emergency", "patients": 2, "specialty_needed": "Cardiology"},
        created_at=utcnow(),
    )
    db.add(sim_run)
    db.commit()
    db.refresh(incident)

    await fabric_service.publish_event(
        event_type="incident.created",
        payload={
            "incident_id": incident.id,
            "incident_type": incident.incident_type,
            "location": incident.location,
            "zone": incident.zone,
            "severity": incident.severity,
            "specialty": "Cardiology",
        },
        entity_id=incident.id,
        zone=incident.zone,
    )

    _create_activity(db, inc_id, "INCIDENT_DETECTED",
                     f"🏥 Cardiac Emergency in {incident.zone} — Cardiology triage dispatched", "high", "🏥")
    await _broadcast_activity(inc_id, "INCIDENT_DETECTED",
                               f"🏥 Cardiac Emergency in Banjara Hills", "🏥", zone=incident.zone)

    await ws_manager.broadcast("INCIDENT_CREATED", {
        "id": incident.id, "incident_type": incident.incident_type,
        "location": incident.location, "zone": incident.zone,
        "latitude": incident.latitude, "longitude": incident.longitude,
        "severity": incident.severity, "people_at_risk": incident.people_at_risk,
        "status": incident.status, "is_simulated": True,
    }, entity_id=incident.id, zone=incident.zone)

    await asyncio.sleep(0.2)
    return await analyze_incident(db, incident)


async def simulate_industrial(db: Session) -> Dict[str, Any]:
    """
    Scenario 5: INDUSTRIAL ACCIDENT
    Zone: Jeedimetla | Severity: Critical | Chemical Exposure: True | Casualties: 18 | Specialty: Trauma
    """
    inc_id = _next_incident_id(db)
    incident = Incident(
        id=inc_id,
        incident_type="Industrial Accident",
        location="Industrial Phase 2, Jeedimetla Industrial Area",
        zone="Jeedimetla",
        latitude=17.5186,
        longitude=78.4712,
        floor=1,
        building="Chemical Plant Unit 4",
        severity="Critical",
        people_at_risk=18,
        description="Chemical reactor breach with toxic vapor cloud exposure. 18 workers symptomatic, hazmat containment required.",
        status="Detected",
        spread_risk="High",
        is_simulated=True,
    )
    db.add(incident)

    sim_run = SimulationRun(
        id=f"SIM-{uuid.uuid4().hex[:8]}",
        scenario_name="INDUSTRIAL_ACCIDENT",
        zone="Jeedimetla",
        severity="Critical",
        status="Completed",
        details={"chemical_exposure": True, "casualties": 18, "fire_units": 2, "ambulances": 3, "specialty": "Trauma/Toxicology"},
        created_at=utcnow(),
    )
    db.add(sim_run)
    db.commit()
    db.refresh(incident)

    await fabric_service.publish_event(
        event_type="incident.created",
        payload={
            "incident_id": incident.id,
            "incident_type": incident.incident_type,
            "location": incident.location,
            "zone": incident.zone,
            "severity": incident.severity,
            "chemical_exposure": True,
            "people_at_risk": 18,
        },
        entity_id=incident.id,
        zone=incident.zone,
    )

    _create_activity(db, inc_id, "INCIDENT_DETECTED",
                     f"🏭 Chemical Vapor Breach in {incident.zone} (Hazmat & Trauma required)", "critical", "🏭")
    await _broadcast_activity(inc_id, "INCIDENT_DETECTED",
                               f"🏭 Chemical Reactor Accident in Jeedimetla", "🏭", zone=incident.zone)

    await ws_manager.broadcast("INCIDENT_CREATED", {
        "id": incident.id, "incident_type": incident.incident_type,
        "location": incident.location, "zone": incident.zone,
        "latitude": incident.latitude, "longitude": incident.longitude,
        "severity": incident.severity, "people_at_risk": incident.people_at_risk,
        "status": incident.status, "spread_risk": incident.spread_risk, "is_simulated": True,
    }, entity_id=incident.id, zone=incident.zone)

    await asyncio.sleep(0.2)
    return await analyze_incident(db, incident)


async def simulate_resource_exhaustion(db: Session) -> Dict[str, Any]:
    """
    Scenario 6: RESOURCE EXHAUSTION
    Simulates high demand exhausting all available ambulances.
    System detects shortage, selects repositioning candidate, emits resource.shortage alert, without crashing.
    """
    # 1. Temporarily set all ambulances to En Route/Busy
    ambulances = db.query(Ambulance).all()
    for a in ambulances:
        a.status = "En Route"
    db.commit()

    # 2. Create high priority incident
    inc_id = _next_incident_id(db)
    incident = Incident(
        id=inc_id,
        incident_type="Road Accident",
        location="Begumpet Flyover Junction",
        zone="Begumpet",
        latitude=17.4440,
        longitude=78.4700,
        severity="Critical",
        people_at_risk=6,
        description="Mass casualty vehicle collision during severe resource strain. 0 local ambulances idle.",
        status="Detected",
        spread_risk="Low",
        is_simulated=True,
    )
    db.add(incident)

    sim_run = SimulationRun(
        id=f"SIM-{uuid.uuid4().hex[:8]}",
        scenario_name="RESOURCE_EXHAUSTION",
        zone="Begumpet",
        severity="Critical",
        status="Completed",
        details={"available_ambulances_before": 0, "resource_shortage": True, "repositioning_triggered": True},
        created_at=utcnow(),
    )
    db.add(sim_run)
    db.commit()
    db.refresh(incident)

    # 3. Publish incident and trigger shortage analysis
    await fabric_service.publish_event(
        event_type="resource.shortage",
        payload={
            "incident_id": incident.id,
            "zone": incident.zone,
            "message": "All ambulances engaged. Inter-zone repositioning required.",
        },
        entity_id=incident.id,
        zone=incident.zone,
    )

    _create_activity(db, inc_id, "RESOURCE_SHORTAGE",
                     f"⚠️ 0 Ambulances Available for {incident.id}! Autonomous Repositioning Engine activated.", "critical", "⚠️")
    await _broadcast_activity(inc_id, "RESOURCE_SHORTAGE",
                               f"⚠️ Critical Ambulance Shortage in Begumpet", "⚠️", zone=incident.zone)

    # Run analysis (Decision Engine handles shortage smoothly)
    result = await analyze_incident(db, incident)

    # Free up 2 ambulances after the demonstration tick
    for a in ambulances[:2]:
        a.status = "Available"
    db.commit()

    return result


# Legacy alias
async def simulate_accident(db: Session) -> Dict[str, Any]:
    return await simulate_major_accident(db)


# ═══════════════════════════════════════════════════════════
# BACKGROUND SIMULATION TICK
# ═══════════════════════════════════════════════════════════

async def run_background_simulation(db: Session):
    """Background simulation tick for live vehicle tracking, hospital occupancy, and traffic drift."""
    traffic = db.query(TrafficCondition).all()
    for t in traffic:
        t.congestion_level = max(0.05, min(0.95, t.congestion_level + random.uniform(-0.05, 0.05)))
        t.estimated_delay_minutes = t.congestion_level * random.uniform(2.0, 15.0)
    db.commit()

    hospitals = db.query(Hospital).all()
    for h in hospitals:
        h.occupancy = max(0.15, min(0.95, h.occupancy + random.uniform(-0.02, 0.02)))
        h.available_beds = max(0, int(h.total_beds * (1.0 - h.occupancy)))
        if h.occupancy > 0.90:
            h.status = "Full"
        elif h.occupancy > 0.75:
            h.status = "Busy"
        else:
            h.status = "Available"
    db.commit()

    # Live vehicle movement logic using exact location pipeline
    import math
    def move_towards(lat1, lon1, lat2, lon2, step=0.004):
        dist = math.hypot(lat2 - lat1, lon2 - lon1)
        if dist < step:
            return lat2, lon2, 0.0, 0.0, True
        ratio = step / dist
        new_lat = lat1 + (lat2 - lat1) * ratio
        new_lon = lon1 + (lon2 - lon1) * ratio
        heading = (math.degrees(math.atan2(lon2 - lon1, lat2 - lat1)) + 360) % 360
        speed_kmh = random.uniform(42.0, 65.0)
        return new_lat, new_lon, heading, speed_kmh, False

    # Move active ambulances
    ambulances = db.query(Ambulance).filter(Ambulance.status.in_(["En Route", "Transporting"])).all()
    for amb in ambulances:
        dispatch = db.query(Dispatch).filter(Dispatch.incident_id == amb.current_incident_id).order_by(Dispatch.created_at.desc()).first()
        incident = db.query(Incident).filter(Incident.id == amb.current_incident_id).first()
        if not dispatch or not incident:
            continue

        target_lat, target_lon = incident.latitude, incident.longitude
        if amb.status == "Transporting":
            hospital = db.query(Hospital).filter(Hospital.id == dispatch.hospital_id).first()
            if hospital:
                target_lat, target_lon = hospital.latitude, hospital.longitude

        new_lat, new_lon, heading, speed_kmh, reached = move_towards(amb.latitude, amb.longitude, target_lat, target_lon)

        # Update via location pipeline (simulates real GPS telemetry stream)
        amb.latitude = new_lat
        amb.longitude = new_lon
        amb.speed_kmh = speed_kmh
        amb.heading = heading
        amb.location_source = "SIMULATION"
        amb.location_status = "LIVE"
        amb.last_location_update = utcnow()
        amb.updated_at = utcnow()

        hist_id = f"LOC-{uuid.uuid4().hex[:12]}"
        hist = LocationHistory(
            id=hist_id,
            resource_id=amb.id,
            resource_type="Ambulance",
            latitude=amb.latitude,
            longitude=amb.longitude,
            speed_kmh=speed_kmh,
            heading=heading,
            accuracy_m=5.0,
            status=amb.status,
            location_source="SIMULATION",
            location_status="LIVE",
            timestamp=utcnow(),
        )
        db.add(hist)
        db.commit()

        # Fabric eventstream
        await fabric_service.publish_event(
            event_type="resource.location.updated",
            payload={
                "resource_id": amb.id,
                "resource_type": "Ambulance",
                "call_sign": amb.call_sign,
                "latitude": amb.latitude,
                "longitude": amb.longitude,
                "speed_kmh": amb.speed_kmh,
                "heading": amb.heading,
                "status": amb.status,
                "location_source": "SIMULATION",
                "location_status": "LIVE",
                "zone": amb.zone,
            },
            entity_id=amb.id,
            zone=amb.zone,
        )

        # WebSocket broadcast
        await ws_manager.broadcast("RESOURCE_LOCATION_UPDATED", {
            "event_type": "resource.location.updated",
            "resource_id": amb.id,
            "resource_type": "Ambulance",
            "call_sign": amb.call_sign,
            "latitude": amb.latitude,
            "longitude": amb.longitude,
            "speed_kmh": amb.speed_kmh,
            "heading": amb.heading,
            "status": amb.status,
            "location_source": "SIMULATION",
            "location_status": "LIVE",
            "timestamp": utcnow().isoformat(),
        }, entity_id=amb.id, zone=amb.zone)

        await ws_manager.broadcast("RESOURCE_UPDATED", {
            "type": "ambulance", "id": amb.id, "latitude": amb.latitude,
            "longitude": amb.longitude, "status": amb.status,
        }, entity_id=amb.id, zone=amb.zone)

        if reached:
            if amb.status == "En Route":
                amb.status = "Transporting"
                _create_activity(db, incident.id, "AMBULANCE_ON_SCENE",
                                 f"🚑 Ambulance {amb.call_sign} on scene at {incident.location}.", "info", "🏥")
                if incident.status == "Dispatched":
                    incident.status = "Response In Progress"
                db.commit()

                await fabric_service.publish_event(
                    event_type="resource.arrived",
                    payload={"resource_id": amb.id, "incident_id": incident.id, "location": incident.location},
                    entity_id=amb.id, zone=incident.zone,
                )

                await ws_manager.broadcast("INCIDENT_UPDATED", {
                    "id": incident.id, "status": incident.status,
                }, entity_id=incident.id, zone=incident.zone)
            elif amb.status == "Transporting":
                amb.status = "Available"
                amb.current_incident_id = None
                incident.status = "Resolved"
                _create_activity(db, incident.id, "INCIDENT_RESOLVED",
                                 f"✅ Patient delivered to medical facility. Incident {incident.id} Resolved.", "info", "✅")
                db.commit()

                await fabric_service.publish_event(
                    event_type="dispatch.status_changed",
                    payload={"incident_id": incident.id, "status": "Resolved"},
                    entity_id=incident.id, zone=incident.zone,
                )

                await ws_manager.broadcast("INCIDENT_UPDATED", {
                    "id": incident.id, "status": incident.status,
                }, entity_id=incident.id, zone=incident.zone)

    # Weather drift
    weather = db.query(WeatherCondition).all()
    for w in weather:
        w.temperature += random.uniform(-0.3, 0.3)
        w.wind_speed = max(0.0, w.wind_speed + random.uniform(-1.0, 1.0))
    db.commit()

    await ws_manager.broadcast("SIMULATION_TICK", {
        "traffic_updated": True,
        "hospitals_updated": True,
        "weather_updated": True,
    })
