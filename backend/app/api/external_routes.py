"""
CrisisFlow API — External Telemetry & Public API Routes
════════════════════════════════════════════════════════
Provides unified REST access to normalized external data sources:
- Open-Meteo & RainViewer Weather
- OSRM Routing & Navigation
- OpenStreetMap / Overpass Facility Discovery
- AQICN Air Quality Index
- USGS Earthquake Feed
"""
from typing import Optional, List
from fastapi import APIRouter, Query, HTTPException

from app.services.external.weather_service import get_weather
from app.services.external.routing_service import calculate_route
from app.services.external.osm_service import search_nearby_facilities
from app.services.external.air_quality_service import get_air_quality
from app.services.external.earthquake_service import get_recent_earthquakes

router = APIRouter(prefix="/api/external", tags=["external"])


@router.get("/weather")
async def fetch_weather(
    lat: float = Query(17.4486, description="Latitude"),
    lon: float = Query(78.3772, description="Longitude"),
):
    """Fetch normalized weather and precipitation telemetry."""
    return await get_weather(lat, lon)


@router.get("/route")
async def fetch_route(
    origin_lat: float = Query(..., description="Origin Latitude"),
    origin_lon: float = Query(..., description="Origin Longitude"),
    dest_lat: float = Query(..., description="Destination Latitude"),
    dest_lon: float = Query(..., description="Destination Longitude"),
    congestion: float = Query(0.3, description="Traffic Congestion 0-1"),
):
    """Calculate driving route distance and ETA duration via OSRM."""
    return await calculate_route(origin_lat, origin_lon, dest_lat, dest_lon, congestion)


@router.get("/facilities")
async def fetch_osm_facilities(
    lat: float = Query(17.4486, description="Latitude"),
    lon: float = Query(78.3772, description="Longitude"),
    radius: int = Query(5000, description="Search radius in meters"),
):
    """Discover nearby emergency medical facilities via OpenStreetMap / Overpass."""
    return await search_nearby_facilities(lat, lon, radius)


@router.get("/air-quality")
async def fetch_air_quality(
    lat: float = Query(17.4486, description="Latitude"),
    lon: float = Query(78.3772, description="Longitude"),
):
    """Fetch Air Quality Index (AQI) and PM2.5 sensors from AQICN."""
    return await get_air_quality(lat, lon)


@router.get("/earthquakes")
async def fetch_earthquakes(
    min_mag: float = Query(3.0, description="Minimum magnitude"),
    limit: int = Query(10, description="Max event count"),
):
    """Retrieve recent seismic events from USGS Earthquake feed."""
    return await get_recent_earthquakes(min_mag, limit)
