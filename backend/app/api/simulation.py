"""CrisisFlow API — Simulation Routes"""
from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas import SimulationRunRequest
from app.services.simulation_service import (
    simulate_major_accident, simulate_fire, simulate_medical,
    simulate_flood, simulate_industrial, simulate_resource_exhaustion,
    simulate_accident,
)

router = APIRouter(tags=["simulation"])


@router.post("/api/simulation/run")
async def run_simulation_scenario(
    request: SimulationRunRequest = Body(...),
    db: Session = Depends(get_db),
):
    """
    Execute any of the 6 repeatable emergency scenarios:
    - MAJOR_ACCIDENT
    - BUILDING_FIRE
    - FLASH_FLOOD
    - MEDICAL_EMERGENCY
    - INDUSTRIAL_ACCIDENT
    - RESOURCE_EXHAUSTION
    """
    scenario = request.scenario_name.upper().replace(" ", "_")

    if scenario in ("MAJOR_ACCIDENT", "ACCIDENT", "ROAD_ACCIDENT"):
        return await simulate_major_accident(db)
    elif scenario in ("BUILDING_FIRE", "FIRE"):
        return await simulate_fire(db)
    elif scenario in ("FLASH_FLOOD", "FLOOD"):
        return await simulate_flood(db)
    elif scenario in ("MEDICAL_EMERGENCY", "MEDICAL"):
        return await simulate_medical(db)
    elif scenario in ("INDUSTRIAL_ACCIDENT", "INDUSTRIAL"):
        return await simulate_industrial(db)
    elif scenario in ("RESOURCE_EXHAUSTION", "EXHAUSTION", "RESOURCE_SHORTAGE"):
        return await simulate_resource_exhaustion(db)
    else:
        raise HTTPException(
            400,
            f"Unknown scenario '{request.scenario_name}'. Valid options: MAJOR_ACCIDENT, BUILDING_FIRE, FLASH_FLOOD, MEDICAL_EMERGENCY, INDUSTRIAL_ACCIDENT, RESOURCE_EXHAUSTION",
        )


# ─── Legacy / Convenience Route Aliases ───
@router.post("/api/simulate/fire")
async def sim_fire(db: Session = Depends(get_db)):
    return await simulate_fire(db)


@router.post("/api/simulate/accident")
async def sim_accident(db: Session = Depends(get_db)):
    return await simulate_major_accident(db)


@router.post("/api/simulate/medical")
async def sim_medical(db: Session = Depends(get_db)):
    return await simulate_medical(db)


@router.post("/api/simulate/flood")
async def sim_flood(db: Session = Depends(get_db)):
    return await simulate_flood(db)


@router.post("/api/simulate/industrial")
async def sim_industrial(db: Session = Depends(get_db)):
    return await simulate_industrial(db)


@router.post("/api/simulate/exhaustion")
async def sim_exhaustion(db: Session = Depends(get_db)):
    return await simulate_resource_exhaustion(db)
