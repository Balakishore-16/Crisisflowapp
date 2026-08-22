"""CrisisFlow SQLAlchemy Models"""
from datetime import datetime, timezone
from sqlalchemy import (
    Column, String, Integer, Float, Text, DateTime, Boolean, ForeignKey, JSON
)
from app.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class Incident(Base):
    __tablename__ = "incidents"
    id = Column(String(30), primary_key=True)
    incident_type = Column(String(50), nullable=False)
    location = Column(String(200), nullable=False)
    zone = Column(String(100), nullable=True, default="Central")
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    floor = Column(Integer, nullable=True)
    building = Column(String(100), nullable=True)
    severity = Column(String(20), nullable=False, default="Medium")
    people_at_risk = Column(Integer, default=0)
    description = Column(Text, nullable=True)
    status = Column(String(30), default="Detected")
    spread_risk = Column(String(20), nullable=True)
    is_duplicate = Column(Boolean, default=False)
    duplicate_of_id = Column(String(30), nullable=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
    is_simulated = Column(Boolean, default=False)


class Ambulance(Base):
    __tablename__ = "ambulances"
    id = Column(String(30), primary_key=True)
    resource_code = Column(String(30), nullable=True)
    resource_type = Column(String(30), default="Ambulance")
    call_sign = Column(String(30), nullable=False)
    location = Column(String(200), nullable=False)
    zone = Column(String(100), nullable=True, default="Central")
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    status = Column(String(30), default="Available")
    equipment = Column(JSON, default=list)
    capacity = Column(Integer, default=2)
    current_incident_id = Column(String(30), nullable=True)
    last_location_update = Column(DateTime, default=utcnow)
    location_accuracy = Column(Float, default=5.0)
    location_source = Column(String(30), default="SIMULATION")
    speed_kmh = Column(Float, default=0.0)
    heading = Column(Float, default=0.0)
    location_status = Column(String(20), default="LIVE")
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)


class FireStation(Base):
    __tablename__ = "fire_stations"
    id = Column(String(30), primary_key=True)
    name = Column(String(100), nullable=False)
    location = Column(String(200), nullable=False)
    zone = Column(String(100), nullable=True, default="Central")
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    available_trucks = Column(Integer, default=2)
    status = Column(String(30), default="Available")
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)


class FireTruck(Base):
    __tablename__ = "fire_trucks"
    id = Column(String(30), primary_key=True)
    station_id = Column(String(30), ForeignKey("fire_stations.id"), nullable=False)
    resource_code = Column(String(30), nullable=True)
    resource_type = Column(String(30), default="FireTruck")
    call_sign = Column(String(30), nullable=False)
    location = Column(String(200), nullable=False)
    zone = Column(String(100), nullable=True, default="Central")
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    status = Column(String(30), default="Available")
    equipment = Column(JSON, default=list)
    current_incident_id = Column(String(30), nullable=True)
    last_location_update = Column(DateTime, default=utcnow)
    location_accuracy = Column(Float, default=5.0)
    location_source = Column(String(30), default="SIMULATION")
    speed_kmh = Column(Float, default=0.0)
    heading = Column(Float, default=0.0)
    location_status = Column(String(20), default="LIVE")
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)


class LocationHistory(Base):
    __tablename__ = "location_history"
    id = Column(String(50), primary_key=True)
    resource_id = Column(String(30), nullable=False)
    resource_type = Column(String(30), default="Ambulance")
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    speed_kmh = Column(Float, default=0.0)
    heading = Column(Float, default=0.0)
    accuracy_m = Column(Float, default=5.0)
    status = Column(String(30), default="Available")
    location_source = Column(String(30), default="LIVE_GPS")
    location_status = Column(String(20), default="LIVE")
    anomaly_flag = Column(String(50), nullable=True)
    timestamp = Column(DateTime, default=utcnow)


class Hospital(Base):
    __tablename__ = "hospitals"
    id = Column(String(30), primary_key=True)
    name = Column(String(200), nullable=False)
    location = Column(String(200), nullable=False)
    zone = Column(String(100), nullable=True, default="Central")
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    total_beds = Column(Integer, default=100)
    available_beds = Column(Integer, default=30)
    emergency_capacity = Column(Integer, default=50)
    icu_beds = Column(Integer, default=10)
    trauma_beds = Column(Integer, default=8)
    burn_capacity = Column(Integer, default=5)
    specialties = Column(JSON, default=list)
    occupancy = Column(Float, default=0.0)
    status = Column(String(30), default="Available")
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)


class TrafficCondition(Base):
    __tablename__ = "traffic_conditions"
    id = Column(String(30), primary_key=True)
    route_name = Column(String(100), nullable=False)
    from_location = Column(String(200))
    to_location = Column(String(200))
    congestion_level = Column(Float, default=0.3)
    estimated_delay_minutes = Column(Float, default=0.0)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)


class WeatherCondition(Base):
    __tablename__ = "weather_conditions"
    id = Column(String(30), primary_key=True)
    location = Column(String(200))
    zone = Column(String(100), default="Hyderabad Metro")
    condition = Column(String(50), default="Clear")
    temperature = Column(Float, default=30.0)
    wind_speed = Column(Float, default=10.0)
    humidity = Column(Float, default=60.0)
    visibility = Column(Float, default=10.0)
    rainfall_mm_hr = Column(Float, default=0.0)
    flood_depth_m = Column(Float, default=0.0)
    risk_factor = Column(Float, default=0.1)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)


class WeatherEvent(Base):
    __tablename__ = "weather_events"
    id = Column(String(30), primary_key=True)
    location = Column(String(200), nullable=False)
    zone = Column(String(100), nullable=False)
    condition = Column(String(50), default="Clear")
    rainfall_mm_hr = Column(Float, default=0.0)
    flood_depth_m = Column(Float, default=0.0)
    wind_speed = Column(Float, default=10.0)
    risk_factor = Column(Float, default=0.1)
    created_at = Column(DateTime, default=utcnow)


class RiskZone(Base):
    __tablename__ = "risk_zones"
    id = Column(String(30), primary_key=True)
    name = Column(String(100), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    radius = Column(Float, default=1.0)
    risk_level = Column(String(30), default="Low")
    risk_score = Column(Integer, default=20)
    factors = Column(JSON, default=list)
    active_incidents = Column(Integer, default=0)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)


class RoadBlock(Base):
    __tablename__ = "road_blocks"
    id = Column(String(30), primary_key=True)
    road_name = Column(String(100), nullable=False)
    zone = Column(String(100), nullable=False)
    reason = Column(String(200), nullable=False)
    severity = Column(String(30), default="Medium")
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    delay_minutes = Column(Float, default=15.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=utcnow)


class Dispatch(Base):
    __tablename__ = "dispatches"
    id = Column(String(30), primary_key=True)
    incident_id = Column(String(30), ForeignKey("incidents.id"), nullable=False)
    resource_id = Column(String(30), nullable=True)
    fire_station_id = Column(String(30), nullable=True)
    fire_truck_id = Column(String(30), nullable=True)
    ambulance_id = Column(String(30), nullable=True)
    hospital_id = Column(String(30), nullable=True)
    route = Column(String(100), nullable=True)
    eta_minutes = Column(Float, nullable=True)
    distance_km = Column(Float, nullable=True, default=0.0)
    confidence = Column(Float, nullable=True)
    reasons = Column(JSON, default=list)
    status = Column(String(30), default="Dispatched")
    assigned_at = Column(DateTime, default=utcnow)
    completed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)


class Recommendation(Base):
    __tablename__ = "recommendations"
    id = Column(String(30), primary_key=True)
    incident_id = Column(String(30), ForeignKey("incidents.id"), nullable=False)
    resource_id = Column(String(30), nullable=True)
    fire_station_id = Column(String(30), nullable=True)
    fire_station_name = Column(String(100), nullable=True)
    fire_truck_id = Column(String(30), nullable=True)
    ambulance_id = Column(String(30), nullable=True)
    hospital_id = Column(String(30), nullable=True)
    hospital_name = Column(String(200), nullable=True)
    route = Column(String(100), nullable=True)
    eta_minutes = Column(Float, nullable=True)
    score = Column(Float, nullable=True)
    confidence = Column(Float, nullable=True)
    algorithm = Column(String(50), default="MultiFactor-Optimizer-v1")
    reasons = Column(JSON, default=list)
    score_breakdown = Column(JSON, default=dict)
    explanation = Column(Text, nullable=True)
    data_considered = Column(JSON, default=list)
    created_at = Column(DateTime, default=utcnow)


class DecisionAudit(Base):
    __tablename__ = "decision_audits"
    id = Column(String(40), primary_key=True)
    incident_id = Column(String(30), ForeignKey("incidents.id"), nullable=False)
    candidate_resources = Column(JSON, default=list)
    candidate_hospitals = Column(JSON, default=list)
    rejected_candidates = Column(JSON, default=list)
    selected_resource = Column(JSON, default=dict)
    selected_hospital = Column(JSON, default=dict)
    score_breakdown = Column(JSON, default=dict)
    score = Column(Float, nullable=True)
    confidence = Column(Float, nullable=True)
    eta_minutes = Column(Float, nullable=True)
    algorithm = Column(String(50), default="Deterministic-Optimization-v1")
    reason = Column(Text, nullable=True)
    human_override = Column(Boolean, default=False)
    final_decision = Column(JSON, default=dict)
    created_at = Column(DateTime, default=utcnow)


class Alert(Base):
    __tablename__ = "alerts"
    id = Column(String(30), primary_key=True)
    alert_type = Column(String(50), nullable=False)
    severity = Column(String(30), nullable=False, default="Critical")
    message = Column(Text, nullable=False)
    zone = Column(String(100), nullable=True)
    entity_id = Column(String(30), nullable=True)
    acknowledged = Column(Boolean, default=False)
    created_at = Column(DateTime, default=utcnow)


class SimulationRun(Base):
    __tablename__ = "simulation_runs"
    id = Column(String(40), primary_key=True)
    scenario_name = Column(String(50), nullable=False)
    zone = Column(String(100), nullable=False)
    severity = Column(String(30), nullable=False)
    status = Column(String(30), default="Completed")
    details = Column(JSON, default=dict)
    created_at = Column(DateTime, default=utcnow)


class ActivityLog(Base):
    __tablename__ = "activity_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    incident_id = Column(String(30), nullable=True)
    event_type = Column(String(50), nullable=False)
    message = Column(Text, nullable=False)
    severity = Column(String(30), default="info")
    icon = Column(String(10), default="📋")
    timestamp = Column(DateTime, default=utcnow)
