"""CrisisFlow API — Analytics Routes"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models import Incident, Ambulance, FireTruck, Hospital, Dispatch, RiskZone, ActivityLog
from app.schemas import AnalyticsResponse, ActivityLogResponse

router = APIRouter(prefix="/api", tags=["analytics"])


@router.get("/analytics", response_model=AnalyticsResponse)
def get_analytics(db: Session = Depends(get_db)):
    total = db.query(Incident).count()
    active = db.query(Incident).filter(
        Incident.status.in_(["Detected", "Analyzing", "Awaiting Response", "Dispatched", "Response In Progress"])
    ).count()
    critical = db.query(Incident).filter(Incident.severity == "Critical").count()
    resolved = db.query(Incident).filter(Incident.status == "Resolved").count()
    total_dispatches = db.query(Dispatch).count()

    # Average response time from dispatches
    avg_rt = db.query(func.avg(Dispatch.eta_minutes)).scalar() or 0.0

    # Resources
    total_amb = db.query(Ambulance).count()
    avail_amb = db.query(Ambulance).filter(Ambulance.status == "Available").count()
    total_ft = db.query(FireTruck).count()
    avail_ft = db.query(FireTruck).filter(FireTruck.status == "Available").count()

    # Hospitals
    total_hosp = db.query(Hospital).count()
    avail_hosp = db.query(Hospital).filter(Hospital.status.in_(["Available", "Busy"])).count()

    # Risk
    high_risk = db.query(RiskZone).filter(RiskZone.risk_level.in_(["High", "Critical"])).count()

    # Incidents by type
    type_counts = {}
    for row in db.query(Incident.incident_type, func.count()).group_by(Incident.incident_type).all():
        type_counts[row[0]] = row[1]

    # Incidents by severity
    sev_counts = {}
    for row in db.query(Incident.severity, func.count()).group_by(Incident.severity).all():
        sev_counts[row[0]] = row[1]

    # Incidents by status
    status_counts = {}
    for row in db.query(Incident.status, func.count()).group_by(Incident.status).all():
        status_counts[row[0]] = row[1]

    # Hospital capacity
    hospitals = db.query(Hospital).all()
    hospital_capacity = [
        {"name": h.name, "occupancy": round(h.occupancy * 100, 1),
         "emergency_capacity": h.emergency_capacity, "icu_beds": h.icu_beds,
         "trauma_beds": h.trauma_beds, "burn_capacity": h.burn_capacity,
         "status": h.status}
        for h in hospitals
    ]

    # Resource utilization
    resource_util = {
        "ambulances": {"total": total_amb, "available": avail_amb,
                       "utilization": round((total_amb - avail_amb) / max(total_amb, 1) * 100, 1)},
        "fire_trucks": {"total": total_ft, "available": avail_ft,
                        "utilization": round((total_ft - avail_ft) / max(total_ft, 1) * 100, 1)},
    }

    return AnalyticsResponse(
        total_incidents=total,
        active_incidents=active,
        critical_incidents=critical,
        resolved_incidents=resolved,
        total_dispatches=total_dispatches,
        avg_response_time=round(avg_rt, 1),
        available_ambulances=avail_amb,
        total_ambulances=total_amb,
        available_fire_trucks=avail_ft,
        total_fire_trucks=total_ft,
        available_hospitals=avail_hosp,
        total_hospitals=total_hosp,
        high_risk_zones=high_risk,
        incidents_by_type=type_counts,
        incidents_by_severity=sev_counts,
        incidents_by_status=status_counts,
        hospital_capacity=hospital_capacity,
        resource_utilization=resource_util,
    )


@router.get("/activity-logs", response_model=list[ActivityLogResponse])
def get_activity_logs(limit: int = 50, db: Session = Depends(get_db)):
    return (db.query(ActivityLog)
            .order_by(ActivityLog.timestamp.desc())
            .limit(limit)
            .all())
