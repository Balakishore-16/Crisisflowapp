"""CrisisFlow API — Decision Engine & Audit Routes"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Recommendation, DecisionAudit
from app.schemas import RecommendationResponse, DecisionAuditResponse

router = APIRouter(prefix="/api", tags=["decisions"])


@router.get("/recommendations", response_model=List[RecommendationResponse])
def list_recommendations(limit: int = 50, db: Session = Depends(get_db)):
    """List recent decision engine recommendations."""
    return (
        db.query(Recommendation)
        .order_by(Recommendation.created_at.desc())
        .limit(limit)
        .all()
    )


@router.get("/recommendations/{recommendation_id}", response_model=RecommendationResponse)
def get_recommendation_by_id(recommendation_id: str, db: Session = Depends(get_db)):
    """Get a specific recommendation by its ID."""
    rec = db.query(Recommendation).filter(Recommendation.id == recommendation_id).first()
    if not rec:
        raise HTTPException(404, "Recommendation not found")
    return rec


@router.get("/decision-audit/{incident_id}", response_model=DecisionAuditResponse)
def get_decision_audit(incident_id: str, db: Session = Depends(get_db)):
    """
    Get the complete decision audit log for an incident,
    including candidate resources considered, rejected candidates with reasons,
    and multi-factor score breakdown.
    """
    audit = (
        db.query(DecisionAudit)
        .filter(DecisionAudit.incident_id == incident_id)
        .order_by(DecisionAudit.created_at.desc())
        .first()
    )
    if not audit:
        raise HTTPException(404, f"No decision audit record found for incident {incident_id}")
    return audit


@router.get("/decision-audits", response_model=List[DecisionAuditResponse])
def list_decision_audits(limit: int = 50, db: Session = Depends(get_db)):
    """List recent decision audits across all incidents."""
    return (
        db.query(DecisionAudit)
        .order_by(DecisionAudit.created_at.desc())
        .limit(limit)
        .all()
    )
