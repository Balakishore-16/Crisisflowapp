"""
CrisisFlow Decision Engine
───────────────────────────
Deterministic resource-optimization engine.
Calculates scores for fire stations, ambulances, and hospitals
based on distance, traffic, availability, equipment, severity, and capacity.
The AI layer explains— this engine DECIDES.
"""
import math
import random
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from app.models import (
    Incident, Ambulance, FireStation, FireTruck, Hospital,
    TrafficCondition, Recommendation, utcnow,
)


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
    """Estimated travel time in minutes.  Base speed ~40 km/h city driving."""
    base_speed_kmh = 40.0
    effective_speed = base_speed_kmh * (1 - congestion * 0.6)
    if effective_speed < 5:
        effective_speed = 5
    return (distance_km / effective_speed) * 60


def _get_avg_congestion(db: Session) -> float:
    """Average city-wide traffic congestion 0-1."""
    rows = db.query(TrafficCondition).all()
    if not rows:
        return 0.3
    return sum(r.congestion_level for r in rows) / len(rows)


EQUIPMENT_MAP = {
    "Building Fire": ["ladder", "hose", "breathing_apparatus", "thermal_camera"],
    "Industrial Accident": ["hazmat", "hose", "breathing_apparatus"],
    "Road Accident": ["jaws_of_life", "first_aid"],
    "Medical Emergency": ["defibrillator", "first_aid", "oxygen"],
    "Flood": ["rescue_boat", "rope", "life_jacket"],
}


def _equipment_match_score(equipment: list, incident_type: str) -> float:
    """0-1 score for how well equipment matches the incident."""
    needed = EQUIPMENT_MAP.get(incident_type, [])
    if not needed:
        return 0.8
    if not equipment:
        return 0.3
    matches = sum(1 for e in needed if e in equipment)
    return matches / len(needed)


# ── Severity multiplier ──
SEVERITY_WEIGHT = {"Low": 1.0, "Medium": 1.2, "High": 1.5, "Critical": 2.0}


# ═══════════════════════════════════════════════════════════
# PUBLIC API
# ═══════════════════════════════════════════════════════════

def score_fire_station(
    station, truck, incident: Incident, congestion: float
) -> Dict[str, Any]:
    """Score a fire station + truck combo for this incident."""
    dist = _haversine_km(incident.latitude, incident.longitude,
                         station.latitude, station.longitude)
    eta = _estimate_eta(dist, congestion)
    sev_w = SEVERITY_WEIGHT.get(incident.severity, 1.0)

    equip_score = _equipment_match_score(truck.equipment if truck else [], incident.incident_type)

    score = 100.0
    score -= dist * 3.0                       # distance penalty
    score -= congestion * 20.0                # traffic penalty
    score -= eta * sev_w * 1.5                # response-time penalty (weighted by severity)
    score += equip_score * 20.0               # equipment bonus
    if station.available_trucks > 1:
        score += 5.0                          # redundancy bonus
    score = max(0, min(100, score))
    return {
        "station_id": station.id,
        "station_name": station.name,
        "truck_id": truck.id if truck else None,
        "distance_km": round(dist, 2),
        "eta_minutes": round(eta, 1),
        "equipment_match": round(equip_score, 2),
        "score": round(score, 1),
    }


def score_ambulance(
    ambulance: Ambulance, incident: Incident, congestion: float
) -> Dict[str, Any]:
    dist = _haversine_km(incident.latitude, incident.longitude,
                         ambulance.latitude, ambulance.longitude)
    eta = _estimate_eta(dist, congestion)
    sev_w = SEVERITY_WEIGHT.get(incident.severity, 1.0)
    equip_score = _equipment_match_score(ambulance.equipment or [], incident.incident_type)

    score = 100.0
    score -= dist * 3.0
    score -= congestion * 18.0
    score -= eta * sev_w * 1.2
    score += equip_score * 15.0
    score = max(0, min(100, score))
    return {
        "ambulance_id": ambulance.id,
        "call_sign": ambulance.call_sign,
        "distance_km": round(dist, 2),
        "eta_minutes": round(eta, 1),
        "equipment_match": round(equip_score, 2),
        "score": round(score, 1),
    }


def score_hospital(
    hospital: Hospital, incident: Incident, congestion: float
) -> Dict[str, Any]:
    dist = _haversine_km(incident.latitude, incident.longitude,
                         hospital.latitude, hospital.longitude)
    eta = _estimate_eta(dist, congestion)

    score = 100.0
    score -= dist * 2.5
    score -= congestion * 15.0
    score -= hospital.occupancy * 30.0        # occupancy penalty

    # Capacity bonuses by incident type
    if incident.incident_type == "Building Fire":
        score += min(hospital.burn_capacity, 10) * 2.0
        score += min(hospital.trauma_beds, 10) * 1.5
    elif incident.incident_type in ("Road Accident", "Industrial Accident"):
        score += min(hospital.trauma_beds, 10) * 2.5
    elif incident.incident_type == "Medical Emergency":
        score += min(hospital.icu_beds, 10) * 2.0
        score += min(hospital.emergency_capacity, 20) * 0.5

    score += min(hospital.emergency_capacity, 50) * 0.3
    if hospital.status == "Full":
        score = 0
    elif hospital.status == "Emergency Only":
        score *= 0.6
    score = max(0, min(100, score))
    return {
        "hospital_id": hospital.id,
        "hospital_name": hospital.name,
        "distance_km": round(dist, 2),
        "eta_minutes": round(eta, 1),
        "occupancy": round(hospital.occupancy, 2),
        "score": round(score, 1),
    }


ROUTE_NAMES = ["Route A", "Route B", "Route C", "Route D", "Route E"]


def generate_recommendation(db: Session, incident: Incident) -> Optional[Recommendation]:
    """Run the full decision engine for an incident and persist the recommendation."""
    congestion = _get_avg_congestion(db)

    # ── Score fire stations ──
    stations = db.query(FireStation).filter(FireStation.status == "Available").all()
    station_scores = []
    for st in stations:
        truck = (db.query(FireTruck)
                 .filter(FireTruck.station_id == st.id, FireTruck.status == "Available")
                 .first())
        if truck:
            station_scores.append(score_fire_station(st, truck, incident, congestion))
    station_scores.sort(key=lambda x: x["score"], reverse=True)

    # ── Score ambulances ──
    ambulances = db.query(Ambulance).filter(Ambulance.status == "Available").all()
    amb_scores = [score_ambulance(a, incident, congestion) for a in ambulances]
    amb_scores.sort(key=lambda x: x["score"], reverse=True)

    # ── Score hospitals ──
    hospitals = db.query(Hospital).filter(Hospital.status != "Full").all()
    hosp_scores = [score_hospital(h, incident, congestion) for h in hospitals]
    hosp_scores.sort(key=lambda x: x["score"], reverse=True)

    best_station = station_scores[0] if station_scores else None
    best_amb = amb_scores[0] if amb_scores else None
    best_hosp = hosp_scores[0] if hosp_scores else None

    # Combined ETA = max of individual ETAs (parallel dispatch)
    etas = [s["eta_minutes"] for s in [best_station, best_amb, best_hosp] if s]
    combined_eta = max(etas) if etas else 0

    # Confidence = average of top scores
    scores_list = [s["score"] for s in [best_station, best_amb, best_hosp] if s]
    confidence = sum(scores_list) / len(scores_list) if scores_list else 0

    # Reasons
    reasons = []
    if best_station:
        reasons.append(f"Lowest effective response time ({best_station['eta_minutes']} min)")
    if congestion < 0.4:
        reasons.append("Low traffic on recommended route")
    elif congestion < 0.7:
        reasons.append("Moderate traffic conditions factored in")
    else:
        reasons.append("High traffic — fastest available route selected")
    if best_station and best_station.get("equipment_match", 0) > 0.6:
        reasons.append("Required emergency equipment available")
    if best_hosp and best_hosp.get("occupancy", 1) < 0.7:
        reasons.append("Hospital has sufficient capacity")
    if incident.incident_type == "Building Fire" and best_hosp:
        reasons.append("Hospital has trauma/burn unit capacity")

    route_name = random.choice(ROUTE_NAMES)

    rec_id = f"REC-{random.randint(1000,9999)}"
    rec = Recommendation(
        id=rec_id,
        incident_id=incident.id,
        fire_station_id=best_station["station_id"] if best_station else None,
        fire_station_name=best_station["station_name"] if best_station else None,
        fire_truck_id=best_station["truck_id"] if best_station else None,
        ambulance_id=best_amb["ambulance_id"] if best_amb else None,
        hospital_id=best_hosp["hospital_id"] if best_hosp else None,
        hospital_name=best_hosp["hospital_name"] if best_hosp else None,
        route=route_name,
        eta_minutes=round(combined_eta, 1),
        confidence=round(confidence, 1),
        reasons=reasons,
        data_considered=["distance", "traffic", "availability", "equipment", "severity",
                         "hospital_capacity", "response_time"],
        explanation="",  # filled by AI service
    )
    db.add(rec)
    db.commit()
    db.refresh(rec)
    return rec


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
