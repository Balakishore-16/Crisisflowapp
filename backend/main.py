"""
CrisisFlow — Main FastAPI Application
══════════════════════════════════════
AI-Powered Real-Time Emergency Response & Resource Optimization Platform
"""
import sys
import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import datetime, timezone

# Ensure UTF-8 output encoding across Windows consoles
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

load_dotenv()

from app.database import init_db, SessionLocal
from app.realtime.manager import ws_manager
from app.api import incidents, resources, simulation, analytics, fabric_routes, decisions, alerts, external_routes

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("crisisflow")

# Background simulation task handle
_sim_task = None


async def background_simulation():
    """Run background simulation ticks every 8 seconds."""
    from app.services.simulation_service import run_background_simulation
    while True:
        try:
            db = SessionLocal()
            await run_background_simulation(db)
            db.close()
        except Exception as e:
            logger.error(f"Background simulation error: {e}")
        await asyncio.sleep(8)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    logger.info("🚨 CrisisFlow starting up...")
    init_db()

    # Run seed if database is empty
    from app.models import Incident
    db = SessionLocal()
    if db.query(Incident).count() == 0:
        logger.info("Empty database — running seed...")
        db.close()
        from seed import run_seed
        run_seed()
    else:
        db.close()

    # Start background simulation
    global _sim_task
    _sim_task = asyncio.create_task(background_simulation())
    logger.info("✓ CrisisFlow ready — Command Center operational")
    yield

    # Shutdown
    if _sim_task:
        _sim_task.cancel()
    from app.services.fabric_service import fabric_service
    await fabric_service.close()
    logger.info("CrisisFlow shutdown complete")


app = FastAPI(
    title="CrisisFlow API",
    description="AI-Powered Real-Time Emergency Response & Resource Optimization Platform",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(incidents.router)
app.include_router(resources.router)
app.include_router(decisions.router)
app.include_router(alerts.router)
app.include_router(simulation.router)
app.include_router(analytics.router)
app.include_router(fabric_routes.router)
app.include_router(external_routes.router)


@app.get("/api/health")
def health():
    from app.services.fabric_service import fabric_service
    from app.services.ai_service import get_ai_status
    fabric_stat = fabric_service.get_status()
    return {
        "status": "operational",
        "service": "CrisisFlow",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "fabric": fabric_stat["overall"],
        "fabric_details": fabric_stat,
        "ai": get_ai_status(),
        "websocket_connections": len(ws_manager.active_connections),
    }


@app.websocket("/ws/api/realtime")
async def websocket_endpoint(websocket: WebSocket):
    await ws_manager.connect(websocket)
    logger.info(f"WebSocket client connected ({len(ws_manager.active_connections)} total)")
    try:
        while True:
            data = await websocket.receive_text()
            # Client keep-alive pings
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
        logger.info(f"WebSocket client disconnected ({len(ws_manager.active_connections)} total)")
    except Exception:
        ws_manager.disconnect(websocket)
