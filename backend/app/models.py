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
    id = Column(String(20), primary_key=True)
    incident_type = Column(String(50), nullable=False)
    location = Column(String(200), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    floor = Column(Integer, nullable=True)
    building = Column(String(100), nullable=True)
    severity = Column(String(20), nullable=False, default="Medium")
    people_at_risk = Column(Integer, default=0)
    description = Column(Text, nullable=True)
    status = Column(String(30), default="Detected")
    spread_risk = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)
    is_simulated = Column(Boolean, default=False)


class Ambulance(Base):
    __tablename__ = "ambulances"
    id = Column(String(20), primary_key=True)
    call_sign = Column(String(20), nullable=False)
    location = Column(String(200), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    status = Column(String(20), default="Available")
    equipment = Column(JSON, default=list)
    capacity = Column(Integer, default=2)
    current_incident_id = Column(String(20), nullable=True)


class FireStation(Base):
    __tablename__ = "fire_stations"
    id = Column(String(20), primary_key=True)
    name = Column(String(100), nullable=False)
    location = Column(String(200), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    available_trucks = Column(Integer, default=2)
    status = Column(String(20), default="Available")


class FireTruck(Base):
    __tablename__ = "fire_trucks"
    id = Column(String(20), primary_key=True)
    station_id = Column(String(20), ForeignKey("fire_stations.id"), nullable=False)
    call_sign = Column(String(20), nullable=False)
    location = Column(String(200), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    status = Column(String(20), default="Available")
    equipment = Column(JSON, default=list)
    current_incident_id = Column(String(20), nullable=True)


class Hospital(Base):
    __tablename__ = "hospitals"
    id = Column(String(20), primary_key=True)
    name = Column(String(200), nullable=False)
    location = Column(String(200), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    emergency_capacity = Column(Integer, default=50)
    icu_beds = Column(Integer, default=10)
    trauma_beds = Column(Integer, default=8)
    burn_capacity = Column(Integer, default=5)
    occupancy = Column(Float, default=0.0)
    status = Column(String(20), default="Available")


class TrafficCondition(Base):
    __tablename__ = "traffic_conditions"
    id = Column(String(20), primary_key=True)
    route_name = Column(String(100), nullable=False)
    from_location = Column(String(200))
    to_location = Column(String(200))
    congestion_level = Column(Float, default=0.3)
    estimated_delay_minutes = Column(Float, default=0.0)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)


class WeatherCondition(Base):
    __tablename__ = "weather_conditions"
    id = Column(String(20), primary_key=True)
    location = Column(String(200))
    condition = Column(String(50), default="Clear")
    temperature = Column(Float, default=30.0)
    wind_speed = Column(Float, default=10.0)
    humidity = Column(Float, default=60.0)
    visibility = Column(Float, default=10.0)
    risk_factor = Column(Float, default=0.1)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)


class RiskZone(Base):
    __tablename__ = "risk_zones"
    id = Column(String(20), primary_key=True)
    name = Column(String(100), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    radius = Column(Float, default=1.0)
    risk_level = Column(String(20), default="Low")
    risk_score = Column(Integer, default=20)
    factors = Column(JSON, default=list)
    active_incidents = Column(Integer, default=0)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)


class Dispatch(Base):
    __tablename__ = "dispatches"
    id = Column(String(20), primary_key=True)
    incident_id = Column(String(20), ForeignKey("incidents.id"), nullable=False)
    fire_station_id = Column(String(20), nullable=True)
    fire_truck_id = Column(String(20), nullable=True)
    ambulance_id = Column(String(20), nullable=True)
    hospital_id = Column(String(20), nullable=True)
    route = Column(String(100), nullable=True)
    eta_minutes = Column(Float, nullable=True)
    confidence = Column(Float, nullable=True)
    reasons = Column(JSON, default=list)
    status = Column(String(20), default="Dispatched")
    created_at = Column(DateTime, default=utcnow)
    updated_at = Column(DateTime, default=utcnow, onupdate=utcnow)


class Recommendation(Base):
    __tablename__ = "recommendations"
    id = Column(String(20), primary_key=True)
    incident_id = Column(String(20), ForeignKey("incidents.id"), nullable=False)
    fire_station_id = Column(String(20), nullable=True)
    fire_station_name = Column(String(100), nullable=True)
    fire_truck_id = Column(String(20), nullable=True)
    ambulance_id = Column(String(20), nullable=True)
    hospital_id = Column(String(20), nullable=True)
    hospital_name = Column(String(200), nullable=True)
    route = Column(String(100), nullable=True)
    eta_minutes = Column(Float, nullable=True)
    confidence = Column(Float, nullable=True)
    reasons = Column(JSON, default=list)
    explanation = Column(Text, nullable=True)
    data_considered = Column(JSON, default=list)
    created_at = Column(DateTime, default=utcnow)


class ActivityLog(Base):
    __tablename__ = "activity_logs"
    id = Column(Integer, primary_key=True, autoincrement=True)
    incident_id = Column(String(20), nullable=True)
    event_type = Column(String(50), nullable=False)
    message = Column(Text, nullable=False)
    severity = Column(String(20), default="info")
    icon = Column(String(10), default="📋")
    timestamp = Column(DateTime, default=utcnow)
