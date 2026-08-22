"""CrisisFlow API — Alerts, RoadBlocks, Weather Routes"""
import random
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Alert, RoadBlock, WeatherEvent, WeatherCondition, utcnow
from app.schemas import AlertCreate, AlertResponse, RoadBlockResponse, WeatherEventResponse
from app.services.fabric_service import fabric_service
from app.realtime.manager import ws_manager

router = APIRouter(prefix="/api", tags=["alerts"])


@router.get("/alerts", response_model=List[AlertResponse])
def list_alerts(acknowledged: Optional[bool] = None, limit: int = 50, db: Session = Depends(get_db)):
    """List operational alerts."""
    query = db.query(Alert)
    if acknowledged is not None:
        query = query.filter(Alert.acknowledged == acknowledged)
    return query.order_by(Alert.created_at.desc()).limit(limit).all()


@router.post("/alerts", response_model=AlertResponse)
async def create_alert(data: AlertCreate, db: Session = Depends(get_db)):
    """Create a new emergency alert."""
    alert_id = f"ALT-{random.randint(1000, 9999)}"
    alert = Alert(
        id=alert_id,
        alert_type=data.alert_type,
        severity=data.severity,
        message=data.message,
        zone=data.zone or "Central",
        entity_id=data.entity_id,
        acknowledged=False,
        created_at=utcnow(),
    )
    db.add(alert)
    db.commit()
    db.refresh(alert)

    # Publish to Fabric Eventstream
    await fabric_service.publish_event(
        event_type="alert.created",
        payload={
            "alert_id": alert.id,
            "alert_type": alert.alert_type,
            "severity": alert.severity,
            "message": alert.message,
        },
        entity_id=alert.id,
        zone=alert.zone,
    )

    # WebSocket broadcast
    await ws_manager.broadcast("ALERT_CREATED", {
        "id": alert.id,
        "alert_type": alert.alert_type,
        "severity": alert.severity,
        "message": alert.message,
        "zone": alert.zone,
    }, entity_id=alert.id, zone=alert.zone)

    return alert


@router.post("/alerts/{alert_id}/acknowledge", response_model=AlertResponse)
async def acknowledge_alert(alert_id: str, db: Session = Depends(get_db)):
    """Acknowledge an alert."""
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(404, "Alert not found")
    alert.acknowledged = True
    db.commit()
    db.refresh(alert)
    return alert


@router.get("/roadblocks", response_model=List[RoadBlockResponse])
def list_roadblocks(active_only: bool = True, db: Session = Depends(get_db)):
    """List traffic roadblocks and route obstructions."""
    query = db.query(RoadBlock)
    if active_only:
        query = query.filter(RoadBlock.is_active == True)
    return query.order_by(RoadBlock.created_at.desc()).all()


@router.get("/weather", response_model=List[WeatherEventResponse])
def list_weather_events(limit: int = 50, db: Session = Depends(get_db)):
    """List weather telemetry events."""
    events = db.query(WeatherEvent).order_by(WeatherEvent.created_at.desc()).limit(limit).all()
    return events
