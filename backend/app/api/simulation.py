"""CrisisFlow API — Simulation Routes"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.simulation_service import (
    simulate_fire, simulate_accident, simulate_medical,
    simulate_flood, simulate_industrial,
)

router = APIRouter(prefix="/api/simulate", tags=["simulation"])


@router.post("/fire")
async def sim_fire(db: Session = Depends(get_db)):
    result = await simulate_fire(db)
    return result


@router.post("/accident")
async def sim_accident(db: Session = Depends(get_db)):
    result = await simulate_accident(db)
    return result


@router.post("/medical")
async def sim_medical(db: Session = Depends(get_db)):
    result = await simulate_medical(db)
    return result


@router.post("/flood")
async def sim_flood(db: Session = Depends(get_db)):
    result = await simulate_flood(db)
    return result


@router.post("/industrial")
async def sim_industrial(db: Session = Depends(get_db)):
    result = await simulate_industrial(db)
    return result
