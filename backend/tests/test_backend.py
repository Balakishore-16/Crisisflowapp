"""
CrisisFlow Comprehensive Backend Test Suite
═════════════════════════════════════════════
Tests for:
- Incident creation and validation
- Decision engine multi-factor scoring and explainability breakdown
- Decision audit persistence and retrieval
- Resource exhaustion handling & shortage event emission
- Hospital selection & specialty match
- Simulation scenarios execution
- Fabric Event envelope serialization & fallback resilience
- REST API endpoints & WebSocket manager
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base, get_db
from app.models import (
    Incident, Ambulance, FireStation, FireTruck, Hospital,
    TrafficCondition, WeatherCondition, Recommendation, DecisionAudit, Alert,
)
from app.services.decision_engine import (
    generate_recommendation, score_ambulance, score_hospital, score_fire_station,
    auto_detect_severity, assess_spread_risk,
)
from app.services.fabric_service import fabric_service
from app.services.simulation_service import (
    simulate_major_accident, simulate_fire, simulate_flood,
    simulate_medical, simulate_industrial, simulate_resource_exhaustion,
)
from main import app
from seed import run_seed

client = TestClient(app)


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    """Seed the database before running tests."""
    run_seed()
    yield


# ─── 1. Health & Status Tests ───
def test_health_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "operational"
    assert data["service"] == "CrisisFlow"
    assert "fabric" in data
    assert "ai" in data


def test_fabric_status_endpoint():
    response = client.get("/api/fabric/status")
    assert response.status_code == 200
    data = response.json()
    assert "eventstream" in data
    assert "eventhouse" in data
    assert "sql_database" in data
    assert "overall" in data


# ─── 2. Incident API & Validation Tests ───
def test_create_incident():
    payload = {
        "incident_type": "Road Accident",
        "location": "Gachibowli Junction",
        "zone": "Gachibowli",
        "latitude": 17.4401,
        "longitude": 78.3489,
        "severity": "Auto Detect",
        "people_at_risk": 8,
        "description": "Multi-vehicle collision on ORR link",
    }
    response = client.post("/api/incidents", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["id"].startswith("INC-")
    assert data["incident_type"] == "Road Accident"
    assert data["severity"] == "Medium"
    assert data["zone"] == "Gachibowli"


def test_get_incidents_list():
    response = client.get("/api/incidents")
    assert response.status_code == 200
    incidents = response.json()
    assert isinstance(incidents, list)
    assert len(incidents) >= 1


# ─── 3. Decision Engine & Scoring Breakdown Tests ───
def test_decision_engine_recommendation_and_audit():
    # Create test incident
    payload = {
        "incident_type": "Building Fire",
        "location": "Cyber Gateway, HITEC City",
        "zone": "HITEC City",
        "latitude": 17.4486,
        "longitude": 78.3772,
        "floor": 6,
        "severity": "Critical",
        "people_at_risk": 45,
        "description": "High-rise fire test incident",
    }
    res = client.post("/api/incidents", json=payload)
    assert res.status_code == 200
    inc_id = res.json()["id"]

    # Trigger analysis
    analyze_res = client.post(f"/api/incidents/{inc_id}/analyze")
    assert analyze_res.status_code == 200
    data = analyze_res.json()
    assert data["recommendation"] is not None
    rec = data["recommendation"]
    assert rec["eta_minutes"] is not None
    assert rec["confidence"] > 0
    assert "score_breakdown" in rec
    assert "distance" in rec["score_breakdown"]
    assert "traffic" in rec["score_breakdown"]
    assert "equipment" in rec["score_breakdown"]

    # Verify DecisionAudit API retrieval
    audit_res = client.get(f"/api/decision-audit/{inc_id}")
    assert audit_res.status_code == 200
    audit_data = audit_res.json()
    assert audit_data["incident_id"] == inc_id
    assert "candidate_resources" in audit_data
    assert "rejected_candidates" in audit_data
    assert "score_breakdown" in audit_data


def test_duplicate_incident_detection():
    # Create original incident
    p1 = {
        "incident_type": "Road Accident",
        "location": "Madhapur Main Rd",
        "zone": "HITEC City",
        "latitude": 17.4450,
        "longitude": 78.3800,
        "severity": "High",
        "people_at_risk": 3
    }
    r1 = client.post("/api/incidents", json=p1)
    assert r1.status_code == 200
    orig_id = r1.json()["id"]

    # Create duplicate incident nearby (within 200m)
    p2 = {
        "incident_type": "Road Accident",
        "location": "Madhapur Metro Near Main Rd",
        "zone": "HITEC City",
        "latitude": 17.4452,
        "longitude": 78.3802,
        "severity": "High",
        "people_at_risk": 2
    }
    r2 = client.post("/api/incidents", json=p2)
    assert r2.status_code == 200
    dup_data = r2.json()
    assert dup_data["is_duplicate"] == True
    assert dup_data["duplicate_of_id"] is not None


# ─── 4. Dispatch with Human Override Tests ───
def test_dispatch_with_human_override():
    payload = {
        "incident_type": "Medical Emergency",
        "location": "Banjara Hills Rd 12",
        "zone": "Banjara Hills",
        "latitude": 17.4250,
        "longitude": 78.4400,
        "severity": "High",
        "people_at_risk": 2,
    }
    inc_res = client.post("/api/incidents", json=payload)
    inc_id = inc_res.json()["id"]
    client.post(f"/api/incidents/{inc_id}/analyze")

    # Dispatch with manual hospital override
    dispatch_payload = {
        "ambulance_id": "A-11",
        "hospital_id": "H-05",
        "human_override": True,
        "notes": "Commander selected Apollo Emergency due to specialized cardiology team availability.",
    }
    dsp_res = client.post(f"/api/incidents/{inc_id}/dispatch", json=dispatch_payload)
    assert dsp_res.status_code == 200
    dsp_data = dsp_res.json()
    assert dsp_data["incident_id"] == inc_id
    assert dsp_data["ambulance_id"] == "A-11"
    assert dsp_data["hospital_id"] == "H-05"

    # Verify audit recorded override
    audit_res = client.get(f"/api/decision-audit/{inc_id}")
    assert audit_res.status_code == 200
    assert audit_res.json()["human_override"] == True


# ─── 5. Resource Exhaustion Test ───
def test_resource_exhaustion_scenario():
    response = client.post("/api/simulation/run", json={"scenario_name": "RESOURCE_EXHAUSTION"})
    assert response.status_code == 200
    data = response.json()
    assert data["incident"] is not None

    # Check alert was emitted
    alert_res = client.get("/api/alerts")
    assert alert_res.status_code == 200
    alerts = alert_res.json()
    shortage_alerts = [a for a in alerts if a["alert_type"] == "resource.shortage"]
    assert len(shortage_alerts) >= 1


# ─── 6. All 6 Simulation Scenarios Execution ───
@pytest.mark.parametrize("scenario", [
    "MAJOR_ACCIDENT",
    "BUILDING_FIRE",
    "FLASH_FLOOD",
    "MEDICAL_EMERGENCY",
    "INDUSTRIAL_ACCIDENT",
])
def test_simulation_scenarios(scenario):
    response = client.post("/api/simulation/run", json={"scenario_name": scenario})
    assert response.status_code == 200
    data = response.json()
    assert data["incident"] is not None
    assert data["recommendation"] is not None
    assert data["decision_audit"] is not None


# ─── 7. Resources & Hospitals Endpoints ───
def test_get_resources():
    response = client.get("/api/resources")
    assert response.status_code == 200
    data = response.json()
    assert "ambulances" in data
    assert "fire_stations" in data
    assert "fire_trucks" in data
    assert len(data["ambulances"]) >= 20


def test_get_hospitals():
    response = client.get("/api/hospitals")
    assert response.status_code == 200
    hospitals = response.json()
    assert len(hospitals) >= 10


def test_get_single_resource_lookup():
    response = client.get("/api/resources/A-01")
    assert response.status_code == 200
    data = response.json()
    assert data["resource_type"] == "Ambulance"
    assert data["data"]["id"] == "A-01"


# ─── 8. Alerts & Telemetry Endpoints ───
def test_create_and_acknowledge_alert():
    payload = {
        "alert_type": "flood.risk",
        "severity": "High",
        "message": "Waterlogging detected at Madhapur underpass",
        "zone": "Madhapur",
    }
    create_res = client.post("/api/alerts", json=payload)
    assert create_res.status_code == 200
    alert_id = create_res.json()["id"]

    ack_res = client.post(f"/api/alerts/{alert_id}/acknowledge")
    assert ack_res.status_code == 200
    assert ack_res.json()["acknowledged"] == True


def test_get_roadblocks_and_weather():
    rb_res = client.get("/api/roadblocks")
    assert rb_res.status_code == 200
    assert isinstance(rb_res.json(), list)

    w_res = client.get("/api/weather")
    assert w_res.status_code == 200
    assert isinstance(w_res.json(), list)


def test_bulk_acknowledge_and_dispatch():
    # Create two test incidents
    res1 = client.post("/api/incidents", json={
        "incident_type": "Road Accident", "location": "Madhapur Link", "zone": "Madhapur",
        "latitude": 17.4420, "longitude": 78.3930, "severity": "High", "people_at_risk": 3
    })
    res2 = client.post("/api/incidents", json={
        "incident_type": "Medical Emergency", "location": "HITEC City Sector", "zone": "HITEC City",
        "latitude": 17.4486, "longitude": 78.3772, "severity": "Medium", "people_at_risk": 1
    })
    id1, id2 = res1.json()["id"], res2.json()["id"]

    # Bulk acknowledge
    ack_res = client.post("/api/incidents/bulk/acknowledge", json={"incident_ids": [id1, id2]})
    assert ack_res.status_code == 200
    ack_data = ack_res.json()
    assert id1 in ack_data["successful"]
    assert id2 in ack_data["successful"]

    # Timeline test
    time_res = client.get(f"/api/incidents/{id1}/timeline")
    assert time_res.status_code == 200
    events = time_res.json()
    assert len(events) >= 1

    # Bulk dispatch
    dsp_res = client.post("/api/incidents/bulk/dispatch", json={"incident_ids": [id1, id2]})
    assert dsp_res.status_code == 200
    dsp_data = dsp_res.json()
    assert id1 in dsp_data["successful"]
    assert id2 in dsp_data["successful"]


# ─── 9. Fabric Event Envelope Serialization & Fallback Resilience ───
def test_event_envelope_serialization():
    envelope = fabric_service.create_event_envelope(
        event_type="incident.created",
        payload={"test_key": "test_value"},
        entity_id="INC-TEST",
        zone="HITEC City",
    )
    assert envelope.event_id.startswith("EVT-")
    assert envelope.source == "crisisflow-api"
    assert envelope.event_type == "incident.created"
    assert envelope.entity_id == "INC-TEST"
    assert envelope.zone == "HITEC City"
    assert envelope.payload["test_key"] == "test_value"

