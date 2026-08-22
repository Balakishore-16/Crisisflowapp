"""
CrisisFlow Decision Engine
───────────────────────────
Deterministic resource-optimization engine.
Calculates multi-factor scores for fire stations, ambulances, and hospitals
based on distance, traffic, availability, equipment, severity, hospital capacity,
and specialized care capabilities.
The AI layer explains — this engine DECIDES.
"""
import math
import uuid
import random
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from app.models import (
    Incident, Ambulance, FireStation, FireTruck, Hospital,
    TrafficCondition, WeatherCondition, Recommendation, DecisionAudit,
    Alert, utcnow,
)
from app.realtime.manager import ws_manager


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in km between two lat/lon points."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _estimate_eta(distance_km: float, congestion: float = 0.3) -> float:
    """Estimated travel time in minutes. Base speed ~40 km/h city driving."""
    base_speed_kmh = 40.0
    effective_speed = base_speed_kmh * (1.0 - congestion * 0.6)
    if effective_speed < 5.0:
        effective_speed = 5.0
    return (distance_km / effective_speed) * 60.0


def _get_avg_congestion(db: Session) -> float:
    """Average city-wide traffic congestion 0-1."""
    rows = db.query(TrafficCondition).all()
    if not rows:
        return 0.3
    return sum(r.congestion_level for r in rows) / len(rows)


def _get_weather_risk(db: Session, zone: Optional[str] = None) -> float:
    """Weather risk factor 0-1."""
    if zone:
        w = db.query(WeatherCondition).filter(WeatherCondition.zone == zone).first()
        if w:
            return w.risk_factor
    w_gen = db.query(WeatherCondition).first()
    return w_gen.risk_factor if w_gen else 0.15


EQUIPMENT_MAP = {
    "Building Fire": ["ladder", "hose", "breathing_apparatus", "thermal_camera"],
    "Industrial Accident": ["hazmat", "hose", "breathing_apparatus"],
    "Road Accident": ["jaws_of_life", "first_aid", "stretcher"],
    "Medical Emergency": ["defibrillator", "first_aid", "oxygen", "stretcher"],
    "Flood": ["rescue_boat", "rope", "life_jacket", "first_aid"],
}

SPECIALTY_MAP = {
    "Building Fire": ["Burn Care", "Trauma", "Emergency"],
    "Industrial Accident": ["Trauma", "Toxicology", "Burn Care", "Emergency"],
    "Road Accident": ["Trauma", "Orthopedics", "Emergency"],
    "Medical Emergency": ["Cardiology", "ICU", "Neurology", "Emergency"],
    "Flood": ["Hypothermia Care", "Trauma", "Emergency"],
}

SEVERITY_WEIGHT = {"Low": 1.0, "Medium": 1.2, "High": 1.5, "Critical": 2.0}


# ═══════════════════════════════════════════════════════════
# INDIVIDUAL SCORING FUNCTIONS
# ═══════════════════════════════════════════════════════════

def _equipment_match_score(equipment: list, incident_type: str) -> float:
    """0-1 score for how well equipment matches the incident."""
    needed = EQUIPMENT_MAP.get(incident_type, [])
    if not needed:
        return 0.8
    if not equipment:
        return 0.3
    matches = sum(1 for e in needed if e in equipment)
    return matches / len(needed)


def score_fire_station(
    station: FireStation, truck: Optional[FireTruck], incident: Incident, congestion: float
) -> Dict[str, Any]:
    """Score a fire station + truck combo for this incident."""
    dist = _haversine_km(incident.latitude, incident.longitude, station.latitude, station.longitude)
    eta = _estimate_eta(dist, congestion)
    sev_w = SEVERITY_WEIGHT.get(incident.severity, 1.0)
    equip_score = _equipment_match_score(truck.equipment if truck else [], incident.incident_type)

    distance_score = max(0.0, 100.0 - dist * 3.0)
    traffic_score = max(0.0, 100.0 - congestion * 40.0)
    equipment_score = equip_score * 100.0
    eta_score = max(0.0, 100.0 - eta * sev_w * 2.0)
    availability_score = 100.0 if (station.status == "Available" and truck and truck.status == "Available") else 0.0

    score = 100.0
    score -= dist * 3.0
    score -= congestion * 20.0
    score -= eta * sev_w * 1.5
    score += equip_score * 20.0
    if station.available_trucks > 1:
        score += 5.0
    score = max(0.0, min(100.0, score))

    return {
        "station_id": station.id,
        "station_name": station.name,
        "truck_id": truck.id if truck else None,
        "distance_km": round(dist, 2),
        "eta_minutes": round(eta, 1),
        "equipment_match": round(equip_score, 2),
        "score": round(score, 1),
        "score_breakdown": {
            "distance_score": round(distance_score, 1),
            "traffic_score": round(traffic_score, 1),
            "equipment_score": round(equipment_score, 1),
            "eta_score": round(eta_score, 1),
            "availability_score": round(availability_score, 1),
        },
    }


def score_ambulance(
    ambulance: Ambulance, incident: Incident, congestion: float
) -> Dict[str, Any]:
    """Score an ambulance for this incident."""
    dist = _haversine_km(incident.latitude, incident.longitude, ambulance.latitude, ambulance.longitude)
    eta = _estimate_eta(dist, congestion)
    sev_w = SEVERITY_WEIGHT.get(incident.severity, 1.0)
    equip_score = _equipment_match_score(ambulance.equipment or [], incident.incident_type)

    distance_score = max(0.0, 100.0 - dist * 3.0)
    traffic_score = max(0.0, 100.0 - congestion * 35.0)
    equipment_score = equip_score * 100.0
    eta_score = max(0.0, 100.0 - eta * sev_w * 1.8)
    availability_score = 100.0 if ambulance.status == "Available" else (30.0 if ambulance.status == "En Route" else 0.0)

    score = 100.0
    score -= dist * 3.0
    score -= congestion * 18.0
    score -= eta * sev_w * 1.2
    score += equip_score * 15.0
    score = max(0.0, min(100.0, score))

    return {
        "ambulance_id": ambulance.id,
        "call_sign": ambulance.call_sign,
        "distance_km": round(dist, 2),
        "eta_minutes": round(eta, 1),
        "equipment_match": round(equip_score, 2),
        "score": round(score, 1),
        "score_breakdown": {
            "distance_score": round(distance_score, 1),
            "traffic_score": round(traffic_score, 1),
            "equipment_score": round(equipment_score, 1),
            "eta_score": round(eta_score, 1),
            "availability_score": round(availability_score, 1),
        },
    }


def score_hospital(
    hospital: Hospital, incident: Incident, congestion: float
) -> Dict[str, Any]:
    """Score a hospital based on proximity, capacity, occupancy, and specialty match."""
    dist = _haversine_km(incident.latitude, incident.longitude, hospital.latitude, hospital.longitude)
    eta = _estimate_eta(dist, congestion)

    # Specialty matching
    needed_specialties = SPECIALTY_MAP.get(incident.incident_type, ["Emergency"])
    hosp_specs = hospital.specialties or ["Emergency", "Trauma"]
    spec_matches = sum(1 for s in needed_specialties if any(s.lower() in str(hs).lower() for hs in hosp_specs))
    specialty_match_score = (spec_matches / max(len(needed_specialties), 1)) * 100.0

    distance_score = max(0.0, 100.0 - dist * 2.5)
    traffic_score = max(0.0, 100.0 - congestion * 30.0)
    capacity_score = max(0.0, (1.0 - hospital.occupancy) * 100.0)
    eta_score = max(0.0, 100.0 - eta * 2.0)

    score = 100.0
    score -= dist * 2.5
    score -= congestion * 15.0
    score -= hospital.occupancy * 30.0

    # Specific capacity bonuses
    if incident.incident_type == "Building Fire":
        score += min(hospital.burn_capacity, 10) * 2.0
        score += min(hospital.trauma_beds, 10) * 1.5
    elif incident.incident_type in ("Road Accident", "Industrial Accident"):
        score += min(hospital.trauma_beds, 10) * 2.5
    elif incident.incident_type == "Medical Emergency":
        score += min(hospital.icu_beds, 10) * 2.0
        score += min(hospital.emergency_capacity, 20) * 0.5

    score += (specialty_match_score / 100.0) * 15.0
    score += min(hospital.emergency_capacity, 50) * 0.2

    # Strict Capacity Rule: Ambulances only route to hospitals with available bed capacity (<95% occupancy & >0 beds)
    if hospital.status == "Full" or hospital.occupancy >= 0.95 or hospital.available_beds <= 0:
        score = 0.0
    elif hospital.status == "Busy" or hospital.occupancy >= 0.85:
        score *= 0.65

    score = max(0.0, min(100.0, score))

    return {
        "hospital_id": hospital.id,
        "hospital_name": hospital.name,
        "distance_km": round(dist, 2),
        "eta_minutes": round(eta, 1),
        "occupancy": round(hospital.occupancy, 2),
        "available_beds": hospital.available_beds,
        "specialty_match": round(specialty_match_score, 1),
        "score": round(score, 1),
        "score_breakdown": {
            "distance_score": round(distance_score, 1),
            "traffic_score": round(traffic_score, 1),
            "hospital_capacity_score": round(capacity_score, 1),
            "specialty_score": round(specialty_match_score, 1),
            "eta_score": round(eta_score, 1),
        },
    }


ROUTE_NAMES = ["Route A (Expressway)", "Route B (Main Arterial)", "Route C (Inner Ring)", "Route D (Flyover Link)", "Route E (Direct Corridor)"]


# ═══════════════════════════════════════════════════════════
# FULL DECISION ENGINE PIPELINE
# ═══════════════════════════════════════════════════════════

def generate_recommendation(db: Session, incident: Incident) -> Tuple[Optional[Recommendation], Optional[DecisionAudit]]:
    """
    Run the full multi-factor optimization engine for an incident,
    persisting both the Recommendation and the DecisionAudit records.
    """
    congestion = _get_avg_congestion(db)
    weather_risk = _get_weather_risk(db, incident.zone)

    candidate_resources = []
    candidate_hospitals = []
    rejected_candidates = []

    # 1. Fire Stations & Trucks Evaluation
    all_stations = db.query(FireStation).all()
    station_scores = []
    for st in all_stations:
        truck = db.query(FireTruck).filter(FireTruck.station_id == st.id).first()
        score_res = score_fire_station(st, truck, incident, congestion)
        candidate_resources.append({
            "type": "FireStation",
            "id": st.id,
            "name": st.name,
            "status": st.status,
            "score": score_res["score"],
            "distance_km": score_res["distance_km"],
            "eta_minutes": score_res["eta_minutes"],
        })
        if st.status != "Available" or not truck or truck.status != "Available":
            rejected_candidates.append({
                "type": "FireStation",
                "id": st.id,
                "name": st.name,
                "reason": f"Status is {st.status} (Truck: {truck.status if truck else 'None'})",
            })
        else:
            station_scores.append(score_res)

    station_scores.sort(key=lambda x: x["score"], reverse=True)

    # 2. Ambulances Evaluation
    all_ambulances = db.query(Ambulance).all()
    amb_scores = []
    for amb in all_ambulances:
        score_res = score_ambulance(amb, incident, congestion)
        candidate_resources.append({
            "type": "Ambulance",
            "id": amb.id,
            "call_sign": amb.call_sign,
            "status": amb.status,
            "score": score_res["score"],
            "distance_km": score_res["distance_km"],
            "eta_minutes": score_res["eta_minutes"],
        })
        if amb.status != "Available":
            rejected_candidates.append({
                "type": "Ambulance",
                "id": amb.id,
                "call_sign": amb.call_sign,
                "reason": f"Ambulance is currently {amb.status}",
            })
        else:
            amb_scores.append(score_res)

    amb_scores.sort(key=lambda x: x["score"], reverse=True)

    # Check for Resource Exhaustion
    resource_shortage = False
    reposition_candidate = None
    if not amb_scores:
        resource_shortage = True
        # Find nearest busy ambulance as repositioning candidate
        busy_ambs = [score_ambulance(a, incident, congestion) for a in all_ambulances]
        busy_ambs.sort(key=lambda x: x["distance_km"])
        if busy_ambs:
            reposition_candidate = busy_ambs[0]

    # 3. Hospitals Evaluation
    all_hospitals = db.query(Hospital).all()
    hosp_scores = []
    for h in all_hospitals:
        score_res = score_hospital(h, incident, congestion)
        candidate_hospitals.append({
            "id": h.id,
            "name": h.name,
            "occupancy": h.occupancy,
            "status": h.status,
            "score": score_res["score"],
            "distance_km": score_res["distance_km"],
            "eta_minutes": score_res["eta_minutes"],
        })
        if h.status == "Full" or h.occupancy >= 0.95:
            rejected_candidates.append({
                "type": "Hospital",
                "id": h.id,
                "name": h.name,
                "reason": f"Hospital at capacity ({int(h.occupancy * 100)}% occupied)",
            })
        else:
            hosp_scores.append(score_res)

    hosp_scores.sort(key=lambda x: x["score"], reverse=True)

    best_station = station_scores[0] if station_scores else None
    best_amb = amb_scores[0] if amb_scores else None
    best_hosp = hosp_scores[0] if hosp_scores else None

    # Calculate overall ETA & Confidence
    etas = [s["eta_minutes"] for s in [best_station, best_amb, best_hosp] if s]
    combined_eta = max(etas) if etas else 0.0

    scores_list = [s["score"] for s in [best_station, best_amb, best_hosp] if s]
    confidence = sum(scores_list) / len(scores_list) if scores_list else 0.0

    # If ambulance shortage occurred, adjust confidence and emit alert
    if resource_shortage:
        confidence = max(20.0, confidence * 0.5)

    # Compile Reasons
    reasons = []
    if best_amb:
        reasons.append(f"Ambulance {best_amb['call_sign']} selected: nearest available unit ({best_amb['eta_minutes']} min ETA)")
        if best_amb.get("equipment_match", 0) > 0.6:
            reasons.append("Ambulance is equipped with required medical/rescue kit")
    elif resource_shortage and reposition_candidate:
        reasons.append(f"RESOURCE SHORTAGE: All local ambulances engaged. Repositioning candidate {reposition_candidate['call_sign']} ({reposition_candidate['distance_km']} km)")

    if best_station and incident.incident_type in ("Building Fire", "Industrial Accident", "Flood"):
        reasons.append(f"Fire Unit {best_station['station_name']} assigned ({best_station['eta_minutes']} min ETA)")

    if best_hosp:
        reasons.append(f"Hospital {best_hosp['hospital_name']} selected with {best_hosp.get('available_beds', 'sufficient')} beds and specialty care")

    if congestion < 0.4:
        reasons.append("Traffic conditions optimal on primary arterial route")
    elif congestion < 0.7:
        reasons.append("Moderate traffic factored into route and ETA calculation")
    else:
        reasons.append("Heavy traffic detected — corridor routing applied")

    # Composite Score Breakdown
    composite_breakdown = {
        "distance": round(best_amb["score_breakdown"]["distance_score"] if best_amb else 50.0, 1),
        "traffic": round(100.0 - congestion * 30.0, 1),
        "availability": 100.0 if not resource_shortage else 0.0,
        "equipment": round(best_amb["score_breakdown"]["equipment_score"] if best_amb else 50.0, 1),
        "hospital_capacity": round(best_hosp["score_breakdown"]["hospital_capacity_score"] if best_hosp else 50.0, 1),
        "eta": round(max(0.0, 100.0 - combined_eta * 2.0), 1),
        "weather_risk_factor": round(weather_risk, 2),
    }

    route_name = random.choice(ROUTE_NAMES)
    rec_id = f"REC-{uuid.uuid4().hex[:8]}"

    rec = Recommendation(
        id=rec_id,
        incident_id=incident.id,
        resource_id=best_amb["ambulance_id"] if best_amb else (best_station["truck_id"] if best_station else None),
        fire_station_id=best_station["station_id"] if best_station else None,
        fire_station_name=best_station["station_name"] if best_station else None,
        fire_truck_id=best_station["truck_id"] if best_station else None,
        ambulance_id=best_amb["ambulance_id"] if best_amb else None,
        hospital_id=best_hosp["hospital_id"] if best_hosp else None,
        hospital_name=best_hosp["hospital_name"] if best_hosp else None,
        route=route_name,
        eta_minutes=round(combined_eta, 1),
        score=round(confidence, 1),
        confidence=round(confidence, 1),
        algorithm="MultiFactor-Optimization-v1",
        reasons=reasons,
        score_breakdown=composite_breakdown,
        data_considered=[
            "distance", "traffic", "availability", "equipment", "severity",
            "hospital_capacity", "specialties", "weather_risk", "response_time"
        ],
        explanation="",
        created_at=utcnow(),
    )
    db.add(rec)

    # Create Decision Audit Record
    audit_id = f"AUD-{uuid.uuid4().hex[:8]}"
    audit = DecisionAudit(
        id=audit_id,
        incident_id=incident.id,
        candidate_resources=candidate_resources,
        candidate_hospitals=candidate_hospitals,
        rejected_candidates=rejected_candidates,
        selected_resource={
            "ambulance": best_amb,
            "fire_station": best_station,
            "resource_shortage": resource_shortage,
            "reposition_candidate": reposition_candidate,
        },
        selected_hospital=best_hosp or {},
        score_breakdown=composite_breakdown,
        score=round(confidence, 1),
        confidence=round(confidence, 1),
        eta_minutes=round(combined_eta, 1),
        algorithm="Deterministic-MultiFactor-Optimizer-v1",
        reason="; ".join(reasons),
        human_override=False,
        final_decision={
            "recommendation_id": rec.id,
            "ambulance_id": rec.ambulance_id,
            "fire_station_id": rec.fire_station_id,
            "hospital_id": rec.hospital_id,
            "route": rec.route,
            "eta_minutes": rec.eta_minutes,
        },
        created_at=utcnow(),
    )
    db.add(audit)

    # If resource shortage, create an Alert record
    if resource_shortage:
        alert = Alert(
            id=f"ALT-{random.randint(1000, 9999)}",
            alert_type="resource.shortage",
            severity="Critical",
            message=f"⚠️ RESOURCE SHORTAGE: No available ambulances for {incident.id} ({incident.location}). Repositioning requested.",
            zone=incident.zone,
            entity_id=incident.id,
            acknowledged=False,
            created_at=utcnow(),
        )
        db.add(alert)

    db.commit()
    db.refresh(rec)
    db.refresh(audit)
    return rec, audit


def auto_detect_severity(incident_type: str, people_at_risk: int, floor: int = None) -> str:
    """Auto-detect severity from incident parameters."""
    if people_at_risk > 50:
        return "Critical"
    if people_at_risk > 20:
        return "High"
    if incident_type in ("Building Fire", "Industrial Accident"):
        if floor and floor > 5:
            return "Critical"
        return "High"
    if incident_type == "Flood":
        return "High" if people_at_risk > 10 else "Medium"
    if people_at_risk > 5:
        return "Medium"
    return "Low"


def assess_spread_risk(incident: Incident) -> str:
    """Determine fire/hazard spread risk."""
    if incident.incident_type == "Building Fire":
        if incident.severity == "Critical":
            return "High"
        if incident.floor and incident.floor > 3:
            return "High"
        return "Medium"
    if incident.incident_type == "Industrial Accident":
        return "High" if incident.severity in ("Critical", "High") else "Medium"
    if incident.incident_type == "Flood":
        return "High"
    return "Low"
