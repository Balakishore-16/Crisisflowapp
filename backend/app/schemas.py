"""CrisisFlow Pydantic Schemas"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ─── Incident ───
class IncidentCreate(BaseModel):
    incident_type: str = Field(..., description="Building Fire, Road Accident, Medical Emergency, Flood, Industrial Accident")
    location: str
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
    latitude: float
    longitude: float
    floor: Optional[int] = None
    building: Optional[str] = None
    severity: str
    people_at_risk: int
    description: Optional[str] = None
    status: str
    spread_risk: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    is_simulated: bool = False

    class Config:
        from_attributes = True


class IncidentUpdate(BaseModel):
    status: Optional[str] = None
    severity: Optional[str] = None
    people_at_risk: Optional[int] = None
    description: Optional[str] = None


# ─── Resources ───
class AmbulanceResponse(BaseModel):
    id: str
    call_sign: str
    location: str
    latitude: float
    longitude: float
    status: str
    equipment: list = []
    capacity: int
    current_incident_id: Optional[str] = None

    class Config:
        from_attributes = True


class FireStationResponse(BaseModel):
    id: str
    name: str
    location: str
    latitude: float
    longitude: float
    available_trucks: int
    status: str

    class Config:
        from_attributes = True


class FireTruckResponse(BaseModel):
    id: str
    station_id: str
    call_sign: str
    location: str
    latitude: float
    longitude: float
    status: str
    equipment: list = []
    current_incident_id: Optional[str] = None

    class Config:
        from_attributes = True


class HospitalResponse(BaseModel):
    id: str
    name: str
    location: str
    latitude: float
    longitude: float
    emergency_capacity: int
    icu_beds: int
    trauma_beds: int
    burn_capacity: int
    occupancy: float
    status: str

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

    class Config:
        from_attributes = True


# ─── Recommendation ───
class RecommendationResponse(BaseModel):
    id: str
    incident_id: str
    fire_station_id: Optional[str] = None
    fire_station_name: Optional[str] = None
    fire_truck_id: Optional[str] = None
    ambulance_id: Optional[str] = None
    hospital_id: Optional[str] = None
    hospital_name: Optional[str] = None
    route: Optional[str] = None
    eta_minutes: Optional[float] = None
    confidence: Optional[float] = None
    reasons: list = []
    explanation: Optional[str] = None
    data_considered: list = []
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


# ─── Dispatch ───
class DispatchResponse(BaseModel):
    id: str
    incident_id: str
    fire_station_id: Optional[str] = None
    fire_truck_id: Optional[str] = None
    ambulance_id: Optional[str] = None
    hospital_id: Optional[str] = None
    route: Optional[str] = None
    eta_minutes: Optional[float] = None
    confidence: Optional[float] = None
    reasons: list = []
    status: str
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
    eventstream: str = "NOT_CONNECTED"
    eventhouse: str = "NOT_CONNECTED"
    onelake: str = "NOT_CONNECTED"
    lakehouse: str = "NOT_CONNECTED"
    powerbi: str = "NOT_CONNECTED"
    activator: str = "NOT_CONNECTED"
    ai: str = "NOT_CONNECTED"
    overall: str = "DISCONNECTED"
    last_event_time: Optional[str] = None
    message: str = "Fabric connection required"


# ─── WebSocket Events ───
class WSEvent(BaseModel):
    event_type: str
    data: dict = {}
    timestamp: Optional[str] = None
