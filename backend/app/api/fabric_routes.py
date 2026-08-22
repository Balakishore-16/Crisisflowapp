"""CrisisFlow API — Fabric Status Routes"""
from fastapi import APIRouter
from app.services.fabric_service import fabric_service
from app.services.ai_service import get_ai_status
from app.schemas import FabricStatusResponse

router = APIRouter(prefix="/api/fabric", tags=["fabric"])


@router.get("/status", response_model=FabricStatusResponse)
def get_fabric_status():
    status = fabric_service.get_status()
    ai = get_ai_status()
    status["ai"] = ai["status"]
    return FabricStatusResponse(**status)
