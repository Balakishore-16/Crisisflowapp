"""
CrisisFlow Simulation Service
──────────────────────────────
Generates realistic emergency events and background simulation changes.
All simulated data is clearly labelled as SIMULATION.
"""
import random
import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, Optional
from sqlalchemy.orm import Session
from app.models import (
    Incident, Ambulance, FireStation, FireTruck, Hospital,
    TrafficCondition, WeatherCondition, RiskZone, ActivityLog, utcnow,
)
from app.services.decision_engine import (
    generate_recommendation, auto_detect_severity, assess_spread_risk,
)
from app.services.ai_service import get_ai_provider
from app.services.fabric_service import fabric_service
from app.realtime.manager import ws_manager


# ── Hyderabad-area coordinates for realistic simulation ──
SIMULATION_LOCATIONS = [
    {"name": "Tower A, Hitech City", "lat": 17.4435, "lon": 78.3772, "building": "Tower A", "floor": 7},
    {"name": "Gachibowli IT Park", "lat": 17.4401, "lon": 78.3489, "building": "Block C", "floor": 4},
    {"name": "Madhapur Junction", "lat": 17.4486, "lon": 78.3908, "building": None, "floor": None},
    {"name": "Kukatpally Housing Board", "lat": 17.4947, "lon": 78.3996, "building": "Building 12", "floor": 3},
    {"name": "Secunderabad Railway", "lat": 17.4344, "lon": 78.5013, "building": None, "floor": None},
    {"name": "Jubilee Hills Road 36", "lat": 17.4318, "lon": 78.4075, "building": None, "floor": None},
    {"name": "Ameerpet Metro", "lat": 17.4374, "lon": 78.4482, "building": None, "floor": None},
    {"name": "LB Nagar Circle", "lat": 17.3486, "lon": 78.5528, "building": None, "floor": None},
    {"name": "ECIL X Roads", "lat": 17.4680, "lon": 78.5718, "building": "Factory B", "floor": 1},
    {"name": "Charminar Old City", "lat": 17.3616, "lon": 78.4747, "building": None, "floor": None},
]


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
    )
    db.add(log)
    db.commit()
    return log


async def _broadcast_activity(incident_id: str, event_type: str,
                               message: str, icon: str = "📋"):
    await ws_manager.broadcast("ACTIVITY", {
        "incident_id": incident_id,
        "event_type": event_type,
        "message": message,
        "icon": icon,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


# ═══════════════════════════════════════════════════════════
# Simulate specific incident types
# ═══════════════════════════════════════════════════════════

async def simulate_fire(db: Session) -> Dict[str, Any]:
    """Simulate a building fire — the primary hackathon demo."""
    loc = SIMULATION_LOCATIONS[0]  # Tower A
    inc_id = _next_incident_id(db)

    incident = Incident(
        id=inc_id,
        incident_type="Building Fire",
        location=loc["name"],
        latitude=loc["lat"],
        longitude=loc["lon"],
        floor=loc.get("floor", 7),
        building=loc.get("building", "Tower A"),
        severity="Critical",
        people_at_risk=85,
        description="Major fire reported on floor 7 of Tower A, Hitech City. "
                    "Multiple occupants trapped. Smoke visible from adjacent buildings.",
        status="Detected",
        spread_risk="High",
        is_simulated=True,
    )
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

    # Activity logs
    _create_activity(db, inc_id, "INCIDENT_DETECTED",
                     f"🔥 Building Fire detected at {incident.location}", "critical", "🔥")
    await _broadcast_activity(inc_id, "INCIDENT_DETECTED",
                               f"🔥 Building Fire detected at {incident.location}", "🔥")

    await ws_manager.broadcast("INCIDENT_CREATED", {
        "id": incident.id,
        "incident_type": incident.incident_type,
        "location": incident.location,
        "latitude": incident.latitude,
        "longitude": incident.longitude,
        "severity": incident.severity,
        "people_at_risk": incident.people_at_risk,
        "status": incident.status,
        "floor": incident.floor,
        "building": incident.building,
        "spread_risk": incident.spread_risk,
        "description": incident.description,
        "is_simulated": True,
    })

    # Auto-analyze
    await asyncio.sleep(0.3)
    result = await analyze_incident(db, incident)
    return result


async def simulate_accident(db: Session) -> Dict[str, Any]:
    loc = random.choice(SIMULATION_LOCATIONS[2:6])
    inc_id = _next_incident_id(db)
    people = random.randint(2, 12)
    incident = Incident(
        id=inc_id,
        incident_type="Road Accident",
        location=loc["name"],
        latitude=loc["lat"],
        longitude=loc["lon"],
        severity=auto_detect_severity("Road Accident", people),
        people_at_risk=people,
        description=f"Multi-vehicle collision at {loc['name']}. {people} casualties reported.",
        status="Detected",
        spread_risk="Low",
        is_simulated=True,
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)

    fabric_service.publish_event_sync("INCIDENT_CREATED", {
        "incident_id": incident.id, "incident_type": incident.incident_type,
        "location": incident.location, "severity": incident.severity,
    })

    _create_activity(db, inc_id, "INCIDENT_DETECTED",
                     f"🚗 Road Accident detected at {incident.location}", "high", "🚗")
    await _broadcast_activity(inc_id, "INCIDENT_DETECTED",
                               f"🚗 Road Accident at {incident.location}", "🚗")
    await ws_manager.broadcast("INCIDENT_CREATED", {
        "id": incident.id, "incident_type": incident.incident_type,
        "location": incident.location, "latitude": incident.latitude,
        "longitude": incident.longitude, "severity": incident.severity,
        "people_at_risk": incident.people_at_risk, "status": incident.status,
        "is_simulated": True,
    })
    await asyncio.sleep(0.2)
    return await analyze_incident(db, incident)


async def simulate_medical(db: Session) -> Dict[str, Any]:
    loc = random.choice(SIMULATION_LOCATIONS)
    inc_id = _next_incident_id(db)
    people = random.randint(1, 5)
    incident = Incident(
        id=inc_id,
        incident_type="Medical Emergency",
        location=loc["name"],
        latitude=loc["lat"],
        longitude=loc["lon"],
        floor=loc.get("floor"),
        building=loc.get("building"),
        severity=auto_detect_severity("Medical Emergency", people),
        people_at_risk=people,
        description=f"Medical emergency at {loc['name']}. {people} patient(s) require immediate care.",
        status="Detected",
        spread_risk="Low",
        is_simulated=True,
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)

    fabric_service.publish_event_sync("INCIDENT_CREATED", {
        "incident_id": incident.id, "incident_type": incident.incident_type,
        "location": incident.location, "severity": incident.severity,
    })

    _create_activity(db, inc_id, "INCIDENT_DETECTED",
                     f"🏥 Medical Emergency at {incident.location}", "warning", "🏥")
    await _broadcast_activity(inc_id, "INCIDENT_DETECTED",
                               f"🏥 Medical Emergency at {incident.location}", "🏥")
    await ws_manager.broadcast("INCIDENT_CREATED", {
        "id": incident.id, "incident_type": incident.incident_type,
        "location": incident.location, "latitude": incident.latitude,
        "longitude": incident.longitude, "severity": incident.severity,
        "people_at_risk": incident.people_at_risk, "status": incident.status,
        "is_simulated": True,
    })
    await asyncio.sleep(0.2)
    return await analyze_incident(db, incident)


async def simulate_flood(db: Session) -> Dict[str, Any]:
    loc = random.choice(SIMULATION_LOCATIONS[6:])
    inc_id = _next_incident_id(db)
    people = random.randint(20, 200)
    incident = Incident(
        id=inc_id,
        incident_type="Flood",
        location=loc["name"],
        latitude=loc["lat"],
        longitude=loc["lon"],
        severity=auto_detect_severity("Flood", people),
        people_at_risk=people,
        description=f"Flash flooding at {loc['name']}. {people} residents at risk. "
                    f"Water level rising rapidly.",
        status="Detected",
        spread_risk="High",
        is_simulated=True,
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)

    fabric_service.publish_event_sync("INCIDENT_CREATED", {
        "incident_id": incident.id, "incident_type": incident.incident_type,
        "location": incident.location, "severity": incident.severity,
    })

    _create_activity(db, inc_id, "INCIDENT_DETECTED",
                     f"🌊 Flood detected at {incident.location}", "high", "🌊")
    await _broadcast_activity(inc_id, "INCIDENT_DETECTED",
                               f"🌊 Flood at {incident.location}", "🌊")
    await ws_manager.broadcast("INCIDENT_CREATED", {
        "id": incident.id, "incident_type": incident.incident_type,
        "location": incident.location, "latitude": incident.latitude,
        "longitude": incident.longitude, "severity": incident.severity,
        "people_at_risk": incident.people_at_risk, "status": incident.status,
        "is_simulated": True,
    })
    await asyncio.sleep(0.2)
    return await analyze_incident(db, incident)


async def simulate_industrial(db: Session) -> Dict[str, Any]:
    loc = SIMULATION_LOCATIONS[8]  # Factory
    inc_id = _next_incident_id(db)
    people = random.randint(10, 50)
    incident = Incident(
        id=inc_id,
        incident_type="Industrial Accident",
        location=loc["name"],
        latitude=loc["lat"],
        longitude=loc["lon"],
        floor=loc.get("floor", 1),
        building=loc.get("building", "Factory B"),
        severity="High",
        people_at_risk=people,
        description=f"Industrial accident at {loc['name']}. Chemical spill reported. "
                    f"{people} workers in affected area.",
        status="Detected",
        spread_risk="High",
        is_simulated=True,
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)

    fabric_service.publish_event_sync("INCIDENT_CREATED", {
        "incident_id": incident.id, "incident_type": incident.incident_type,
        "location": incident.location, "severity": incident.severity,
    })

    _create_activity(db, inc_id, "INCIDENT_DETECTED",
                     f"🏭 Industrial Accident at {incident.location}", "high", "🏭")
    await _broadcast_activity(inc_id, "INCIDENT_DETECTED",
                               f"🏭 Industrial Accident at {incident.location}", "🏭")
    await ws_manager.broadcast("INCIDENT_CREATED", {
        "id": incident.id, "incident_type": incident.incident_type,
        "location": incident.location, "latitude": incident.latitude,
        "longitude": incident.longitude, "severity": incident.severity,
        "people_at_risk": incident.people_at_risk, "status": incident.status,
        "is_simulated": True,
    })
    await asyncio.sleep(0.2)
    return await analyze_incident(db, incident)


# ═══════════════════════════════════════════════════════════
# Analyze an incident end-to-end
# ═══════════════════════════════════════════════════════════

async def analyze_incident(db: Session, incident: Incident) -> Dict[str, Any]:
    """Full pipeline: classify → score → recommend → explain."""
    incident.status = "Analyzing"
    incident.spread_risk = assess_spread_risk(incident)
    db.commit()

    _create_activity(db, incident.id, "INCIDENT_ANALYZING",
                     f"🧠 Analyzing severity for {incident.id}", "info", "🧠")
    await _broadcast_activity(incident.id, "INCIDENT_ANALYZING",
                               f"🧠 Incident {incident.id} classified as {incident.severity}", "🧠")

    fabric_service.publish_event_sync("INCIDENT_ANALYZED", {
        "incident_id": incident.id, "severity": incident.severity,
        "spread_risk": incident.spread_risk,
    })

    # Decision Engine
    rec = generate_recommendation(db, incident)

    if rec:
        # AI explanation
        ai = get_ai_provider()
        rec.explanation = ai.explain_recommendation(incident, rec)
        db.commit()

        incident.status = "Awaiting Response"
        db.commit()

        _create_activity(db, incident.id, "RECOMMENDATION_GENERATED",
                         f"🚒 {rec.fire_station_name or 'N/A'} selected for {incident.id}",
                         "info", "🚒")
        if rec.ambulance_id:
            _create_activity(db, incident.id, "AMBULANCE_SELECTED",
                             f"🚑 Ambulance {rec.ambulance_id} selected", "info", "🚑")
        if rec.hospital_name:
            _create_activity(db, incident.id, "HOSPITAL_SELECTED",
                             f"🏥 {rec.hospital_name} selected", "info", "🏥")

        await _broadcast_activity(incident.id, "RECOMMENDATION_GENERATED",
                                   f"🚒 {rec.fire_station_name} selected | ETA {rec.eta_minutes} min", "🚒")
        if rec.ambulance_id:
            await _broadcast_activity(incident.id, "AMBULANCE_SELECTED",
                                       f"🚑 Ambulance {rec.ambulance_id} assigned", "🚑")
        if rec.hospital_name:
            await _broadcast_activity(incident.id, "HOSPITAL_SELECTED",
                                       f"🏥 {rec.hospital_name} recommended", "🏥")

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
            "confidence": rec.confidence,
            "reasons": rec.reasons,
            "explanation": rec.explanation,
        })

        fabric_service.publish_event_sync("RECOMMENDATION_GENERATED", {
            "incident_id": incident.id,
            "fire_station": rec.fire_station_name,
            "ambulance": rec.ambulance_id,
            "hospital": rec.hospital_name,
            "eta_minutes": rec.eta_minutes,
            "confidence": rec.confidence,
        })

    await ws_manager.broadcast("INCIDENT_UPDATED", {
        "id": incident.id, "status": incident.status,
        "severity": incident.severity, "spread_risk": incident.spread_risk,
    })

    return {
        "incident": {
            "id": incident.id,
            "incident_type": incident.incident_type,
            "location": incident.location,
            "severity": incident.severity,
            "status": incident.status,
            "spread_risk": incident.spread_risk,
            "people_at_risk": incident.people_at_risk,
        },
        "recommendation": {
            "id": rec.id,
            "fire_station": rec.fire_station_name,
            "fire_truck": rec.fire_truck_id,
            "ambulance": rec.ambulance_id,
            "hospital": rec.hospital_name,
            "route": rec.route,
            "eta_minutes": rec.eta_minutes,
            "confidence": rec.confidence,
            "reasons": rec.reasons,
            "explanation": rec.explanation,
        } if rec else None,
    }


# ═══════════════════════════════════════════════════════════
# Background simulation — called on a timer
# ═══════════════════════════════════════════════════════════

async def run_background_simulation(db: Session):
    """Small background changes to keep the system feeling alive, including live vehicle tracking."""
    # Random traffic changes
    traffic = db.query(TrafficCondition).all()
    for t in traffic:
        t.congestion_level = max(0.05, min(0.95,
            t.congestion_level + random.uniform(-0.1, 0.1)))
        t.estimated_delay_minutes = t.congestion_level * random.uniform(2, 15)
    db.commit()

    # Random hospital occupancy drift
    hospitals = db.query(Hospital).all()
    for h in hospitals:
        h.occupancy = max(0.1, min(0.95,
            h.occupancy + random.uniform(-0.03, 0.03)))
        if h.occupancy > 0.9:
            h.status = "Full"
        elif h.occupancy > 0.75:
            h.status = "Busy"
        else:
            h.status = "Available"
    db.commit()

    # Live vehicle movement logic
    import math
    def move_towards(lat1, lon1, lat2, lon2, step=0.003):
        dist = math.hypot(lat2 - lat1, lon2 - lon1)
        if dist < step:
            return lat2, lon2, True
        ratio = step / dist
        return lat1 + (lat2 - lat1) * ratio, lon1 + (lon2 - lon1) * ratio, False

    # Move ambulances
    from app.models import Dispatch
    ambulances = db.query(Ambulance).filter(Ambulance.status.in_(["En Route", "Transporting"])).all()
    for amb in ambulances:
        # Get target location
        dispatch = db.query(Dispatch).filter(Dispatch.incident_id == amb.current_incident_id).order_by(Dispatch.created_at.desc()).first()
        incident = db.query(Incident).filter(Incident.id == amb.current_incident_id).first()
        if not dispatch or not incident:
            continue
            
        target_lat, target_lon = incident.latitude, incident.longitude
        if amb.status == "Transporting":
            hospital = db.query(Hospital).filter(Hospital.id == dispatch.hospital_id).first()
            if not hospital:
                continue
                
            # If hospital is over 95% full, dynamically reroute to another hospital with capacity
            if hospital.occupancy > 0.95:
                alt_hospital = db.query(Hospital).filter(Hospital.occupancy < 0.85).first()
                if alt_hospital:
                    _create_activity(db, incident.id, "REROUTE",
                        f"⚠️ {hospital.name} is FULL. Ambulance {amb.call_sign} dynamically rerouted to {alt_hospital.name}.", "high", "⚠️")
                    await _broadcast_activity(incident.id, "REROUTE", f"Rerouted {amb.call_sign} to {alt_hospital.name} due to capacity.", "⚠️")
                    dispatch.hospital_id = alt_hospital.id
                    db.commit()
                    hospital = alt_hospital
                    
            target_lat, target_lon = hospital.latitude, hospital.longitude

        # Calculate new location
        new_lat, new_lon, reached = move_towards(amb.latitude, amb.longitude, target_lat, target_lon)
        amb.latitude = new_lat
        amb.longitude = new_lon
        db.commit()

        # Broadcast live GPS ping for the vehicle
        await ws_manager.broadcast("RESOURCE_UPDATED", {
            "type": "ambulance", "id": amb.id, "latitude": amb.latitude, 
            "longitude": amb.longitude, "status": amb.status
        })

        if reached:
            if amb.status == "En Route":
                amb.status = "Transporting"
                _create_activity(db, incident.id, "AMBULANCE_ON_SCENE",
                        f"🚑 Ambulance reached {incident.location} — picking up patients.", "info", "🏥")
                if incident.status == "Dispatched":
                    incident.status = "Response In Progress"
                db.commit()
                await ws_manager.broadcast("RESOURCE_UPDATED", {
                    "type": "ambulance", "id": amb.id, "status": amb.status
                })
                await ws_manager.broadcast("INCIDENT_UPDATED", {
                    "id": incident.id, "status": incident.status
                })
            elif amb.status == "Transporting":
                hosp = db.query(Hospital).filter(Hospital.id == dispatch.hospital_id).first()
                amb.status = "Available"
                amb.current_incident_id = None
                if hosp:
                    hosp.occupancy = min(1.0, hosp.occupancy + 0.1) # Simulate admit
                if incident.status == "Response In Progress":
                    incident.status = "Resolved"
                    _create_activity(db, incident.id, "INCIDENT_RESOLVED",
                        f"✅ Patient admitted at {hosp.name if hosp else 'hospital'}. Incident Resolved.", "info", "✅")
                db.commit()
                await ws_manager.broadcast("RESOURCE_UPDATED", {
                    "type": "ambulance", "id": amb.id, "status": amb.status
                })
                await ws_manager.broadcast("INCIDENT_UPDATED", {
                    "id": incident.id, "status": incident.status
                })

    # Move Fire Trucks
    fire_trucks = db.query(FireTruck).filter(FireTruck.status == "En Route").all()
    for truck in fire_trucks:
        incident = db.query(Incident).filter(Incident.id == truck.current_incident_id).first()
        if not incident:
            continue
            
        new_lat, new_lon, reached = move_towards(truck.latitude, truck.longitude, incident.latitude, incident.longitude)
        truck.latitude = new_lat
        truck.longitude = new_lon
        db.commit()
        
        await ws_manager.broadcast("RESOURCE_UPDATED", {
            "type": "fire_truck", "id": truck.id, "latitude": truck.latitude, 
            "longitude": truck.longitude, "status": truck.status
        })

        if reached:
            truck.status = "On Scene"
            _create_activity(db, incident.id, "TRUCK_ON_SCENE",
                    f"🚒 {truck.call_sign} arrived and is fighting the incident.", "info", "💦")
            db.commit()
            await ws_manager.broadcast("RESOURCE_UPDATED", {
                "type": "fire_truck", "id": truck.id, "status": truck.status
            })

    # Random weather changes
    weather = db.query(WeatherCondition).all()
    for w in weather:
        w.temperature += random.uniform(-0.5, 0.5)
        w.wind_speed = max(0, w.wind_speed + random.uniform(-2, 2))
        w.risk_factor = max(0, min(1, w.risk_factor + random.uniform(-0.05, 0.05)))
    db.commit()

    # Broadcast updates
    await ws_manager.broadcast("SIMULATION_TICK", {
        "traffic_updated": True,
        "hospitals_updated": True,
        "weather_updated": True,
    })
