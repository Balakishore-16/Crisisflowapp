"""CrisisFlow Pydantic Schemas"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime


# ─── Incident ───
class IncidentCreate(BaseModel):
    incident_type: str = Field(..., description="Building Fire, Road Accident, Medical Emergency, Flood, Industrial Accident")
    location: str
    zone: Optional[str] = "Central"
    latitude: float
    longitude: float
    floor: Optional[int] = None
    building: Optional[str] = None
    severity: str = "Auto Detect"
    people_at_risk: int = 0
    description: Optional[str] = None


class IncidentResponse(BaseModel):
    id: str
    incident_type: str
    location: str
    zone: Optional[str] = "Central"
    latitude: float
    longitude: float
    floor: Optional[int] = None
    building: Optional[str] = None
    severity: str
    people_at_risk: int
    description: Optional[str] = None
    status: str
    spread_risk: Optional[str] = None
    is_duplicate: bool = False
    duplicate_of_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    is_simulated: bool = False

    class Config:
        from_attributes = True


class IncidentUpdate(BaseModel):
    status: Optional[str] = None
    severity: Optional[str] = None
    zone: Optional[str] = None
    people_at_risk: Optional[int] = None
    description: Optional[str] = None


class BulkAcknowledgeRequest(BaseModel):
    incident_ids: List[str] = Field(..., min_items=1)


class BulkDispatchRequest(BaseModel):
    incident_ids: List[str] = Field(..., min_items=1)


class BulkOperationResponse(BaseModel):
    successful: List[str] = []
    failed: List[str] = []
    errors: Dict[str, str] = {}
    message: str


class LocationUpdateRequest(BaseModel):
    latitude: float = Field(..., ge=-90.0, le=90.0)
    longitude: float = Field(..., ge=-180.0, le=180.0)
    timestamp: Optional[str] = None
    accuracy_m: Optional[float] = 5.0
    speed_kmh: Optional[float] = 0.0
    heading: Optional[float] = 0.0
    source: Optional[str] = "LIVE_GPS"  # LIVE_GPS | SIMULATION | MANUAL
    status: Optional[str] = None


class LocationUpdateResponse(BaseModel):
    success: bool = True
    resource_id: str
    latitude: float
    longitude: float
    location_source: str
    location_status: str
    anomaly_flag: Optional[str] = None
    timestamp: datetime
    message: str = ""


class TimelineEventResponse(BaseModel):
    id: str
    incident_id: str
    event_type: str
    title: str
    description: str
    severity: str = "info"
    icon: str = "📋"
    timestamp: datetime


# ─── Resources ───
class AmbulanceResponse(BaseModel):
    id: str
    resource_code: Optional[str] = None
    resource_type: str = "Ambulance"
    call_sign: str
    location: str
    zone: Optional[str] = "Central"
    latitude: float
    longitude: float
    status: str
    equipment: list = []
    capacity: int
    current_incident_id: Optional[str] = None
    last_location_update: Optional[datetime] = None
    location_accuracy: Optional[float] = 5.0
    location_source: Optional[str] = "SIMULATION"
    speed_kmh: Optional[float] = 0.0
    heading: Optional[float] = 0.0
    location_status: Optional[str] = "LIVE"
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class FireStationResponse(BaseModel):
    id: str
    name: str
    location: str
    zone: Optional[str] = "Central"
    latitude: float
    longitude: float
    available_trucks: int
    status: str
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class FireTruckResponse(BaseModel):
    id: str
    station_id: str
    resource_code: Optional[str] = None
    resource_type: str = "FireTruck"
    call_sign: str
    location: str
    zone: Optional[str] = "Central"
    latitude: float
    longitude: float
    status: str
    equipment: list = []
    current_incident_id: Optional[str] = None
    last_location_update: Optional[datetime] = None
    location_accuracy: Optional[float] = 5.0
    location_source: Optional[str] = "SIMULATION"
    speed_kmh: Optional[float] = 0.0
    heading: Optional[float] = 0.0
    location_status: Optional[str] = "LIVE"
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class HospitalResponse(BaseModel):
    id: str
    name: str
    location: str
    zone: Optional[str] = "Central"
    latitude: float
    longitude: float
    total_beds: int = 100
    available_beds: int = 30
    emergency_capacity: int = 50
    icu_beds: int = 10
    trauma_beds: int = 8
    burn_capacity: int = 5
    specialties: list = []
    occupancy: float = 0.0
    status: str = "Available"
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RiskZoneResponse(BaseModel):
    id: str
    name: str
    latitude: float
    longitude: float
    radius: float
    risk_level: str
    risk_score: int
    factors: list = []
    active_incidents: int
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RoadBlockResponse(BaseModel):
    id: str
    road_name: str
    zone: str
    reason: str
    severity: str
    latitude: float
    longitude: float
    delay_minutes: float
    is_active: bool = True
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class WeatherEventResponse(BaseModel):
    id: str
    location: str
    zone: str
    condition: str
    rainfall_mm_hr: float
    flood_depth_m: float
    wind_speed: float
    risk_factor: float
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ─── Recommendation ───
class RecommendationResponse(BaseModel):
    id: str
    incident_id: str
    resource_id: Optional[str] = None
    fire_station_id: Optional[str] = None
    fire_station_name: Optional[str] = None
    fire_truck_id: Optional[str] = None
    ambulance_id: Optional[str] = None
    hospital_id: Optional[str] = None
    hospital_name: Optional[str] = None
    route: Optional[str] = None
    eta_minutes: Optional[float] = None
    score: Optional[float] = None
    confidence: Optional[float] = None
    algorithm: Optional[str] = None
    reasons: list = []
    score_breakdown: dict = {}
    explanation: Optional[str] = None
    data_considered: list = []
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ─── Decision Audit ───
class DecisionAuditResponse(BaseModel):
    id: str
    incident_id: str
    candidate_resources: list = []
    candidate_hospitals: list = []
    rejected_candidates: list = []
    selected_resource: dict = {}
    selected_hospital: dict = {}
    score_breakdown: dict = {}
    score: Optional[float] = None
    confidence: Optional[float] = None
    eta_minutes: Optional[float] = None
    algorithm: str
    reason: Optional[str] = None
    human_override: bool = False
    final_decision: dict = {}
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ─── Dispatch ───
class DispatchRequest(BaseModel):
    ambulance_id: Optional[str] = None
    fire_truck_id: Optional[str] = None
    hospital_id: Optional[str] = None
    human_override: bool = False
    notes: Optional[str] = None


class DispatchResponse(BaseModel):
    id: str
    incident_id: str
    resource_id: Optional[str] = None
    fire_station_id: Optional[str] = None
    fire_truck_id: Optional[str] = None
    ambulance_id: Optional[str] = None
    hospital_id: Optional[str] = None
    route: Optional[str] = None
    eta_minutes: Optional[float] = None
    distance_km: Optional[float] = None
    confidence: Optional[float] = None
    reasons: list = []
    status: str
    assigned_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ─── Alert ───
class AlertCreate(BaseModel):
    alert_type: str
    severity: str = "Critical"
    message: str
    zone: Optional[str] = None
    entity_id: Optional[str] = None


class AlertResponse(BaseModel):
    id: str
    alert_type: str
    severity: str
    message: str
    zone: Optional[str] = None
    entity_id: Optional[str] = None
    acknowledged: bool = False
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ─── Simulation Run ───
class SimulationRunRequest(BaseModel):
    scenario_name: str = Field(..., description="MAJOR_ACCIDENT, BUILDING_FIRE, FLASH_FLOOD, MEDICAL_EMERGENCY, INDUSTRIAL_ACCIDENT, RESOURCE_EXHAUSTION")


class SimulationRunResponse(BaseModel):
    id: str
    scenario_name: str
    zone: str
    severity: str
    status: str
    details: dict = {}
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ─── Activity Log ───
class ActivityLogResponse(BaseModel):
    id: int
    incident_id: Optional[str] = None
    event_type: str
    message: str
    severity: str
    icon: str
    timestamp: Optional[datetime] = None

    class Config:
        from_attributes = True


# ─── Analytics ───
class AnalyticsResponse(BaseModel):
    total_incidents: int = 0
    active_incidents: int = 0
    critical_incidents: int = 0
    resolved_incidents: int = 0
    total_dispatches: int = 0
    avg_response_time: float = 0.0
    available_ambulances: int = 0
    total_ambulances: int = 0
    available_fire_trucks: int = 0
    total_fire_trucks: int = 0
    available_hospitals: int = 0
    total_hospitals: int = 0
    high_risk_zones: int = 0
    incidents_by_type: dict = {}
    incidents_by_severity: dict = {}
    incidents_by_status: dict = {}
    hospital_capacity: list = []
    resource_utilization: dict = {}
    response_time_trend: list = []
    incident_trend: list = []


# ─── Fabric Status ───
class FabricStatusResponse(BaseModel):
    eventstream: str = "NOT_CONFIGURED"
    eventhouse: str = "NOT_CONFIGURED"
    onelake: str = "NOT_CONFIGURED"
    lakehouse: str = "NOT_CONFIGURED"
    powerbi: str = "NOT_CONFIGURED"
    activator: str = "NOT_CONFIGURED"
    sql_database: str = "LOCAL_SQLITE"
    ai: str = "LOCAL"
    overall: str = "LOCAL_MODE"
    last_event_time: Optional[str] = None
    message: str = "Microsoft Fabric configuration"


# ─── Standard Event Envelope ───
class EventEnvelope(BaseModel):
    event_id: str
    event_type: str
    timestamp: str
    source: str = "crisisflow-api"
    entity_id: Optional[str] = None
    zone: Optional[str] = None
    payload: Dict[str, Any] = {}


# ─── WebSocket Events ───
class WSEvent(BaseModel):
    event_type: str
    data: dict = {}
    timestamp: Optional[str] = None
