"""
CrisisFlow External OSRM Routing Service
═════════════════════════════════════════
Integrates OSRM driving route, distance, duration, and geometry calculations with fallback.
"""
import os
import math
import logging
import httpx
from typing import Dict, Any, List

logger = logging.getLogger("crisisflow.routing")

OSRM_BASE = os.getenv("OSRM_BASE_URL", "https://router.project-osrm.org")


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance calculation fallback."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _generate_linear_geometry(origin_lat: float, origin_lon: float, dest_lat: float, dest_lon: float, steps: int = 15) -> List[List[float]]:
    """Generates an interpolated straight-line geometry fallback as list of [lat, lon] points."""
    pts = []
    for i in range(steps + 1):
        t = i / steps
        lat = round(origin_lat + t * (dest_lat - origin_lat), 6)
        lon = round(origin_lon + t * (dest_lon - origin_lon), 6)
        pts.append([lat, lon])
    return pts


async def calculate_route(
    origin_lat: float, origin_lon: float,
    dest_lat: float, dest_lon: float,
    congestion: float = 0.3
) -> Dict[str, Any]:
    """
    Calculate optimal driving route distance (km), ETA duration (minutes), and route geometry using OSRM.
    If OSRM is unreachable or times out, uses haversine + linear geometry fallback.
    """
    try:
        url = f"{OSRM_BASE}/route/v1/driving/{origin_lon},{origin_lat};{dest_lon},{dest_lat}?overview=full&geometries=geojson"
        async with httpx.AsyncClient(timeout=3.0) as client:
            res = await client.get(url)
            if res.status_code == 200:
                data = res.json()
                if data.get("code") == "Ok" and data.get("routes"):
                    route = data["routes"][0]
                    dist_km = round(float(route.get("distance", 0.0)) / 1000.0, 2)
                    duration_min = round(float(route.get("duration", 0.0)) / 60.0, 1)

                    # OSRM GeoJSON geometry coordinates are [lon, lat]. Convert to [lat, lon] for Leaflet
                    raw_coords = route.get("geometry", {}).get("coordinates", [])
                    geometry = [[round(pt[1], 6), round(pt[0], 6)] for pt in raw_coords] if raw_coords else _generate_linear_geometry(origin_lat, origin_lon, dest_lat, dest_lon)

                    # Adjust duration for real-time traffic congestion factor
                    adjusted_duration = round(duration_min * (1.0 + congestion * 0.4), 1)

                    return {
                        "source": "osrm",
                        "distance_km": dist_km,
                        "duration_minutes": adjusted_duration,
                        "raw_duration_minutes": duration_min,
                        "congestion_factor": congestion,
                        "geometry": geometry,
                    }
    except Exception as e:
        logger.warning(f"OSRM route calculation failed ({e}). Using fallback route model.")

    # Fallback Calculation
    dist_km = round(_haversine_km(origin_lat, origin_lon, dest_lat, dest_lon), 2)
    effective_speed = max(5.0, 40.0 * (1.0 - congestion * 0.6))
    duration_min = round((dist_km / effective_speed) * 60.0, 1)
    geometry = _generate_linear_geometry(origin_lat, origin_lon, dest_lat, dest_lon)

    return {
        "source": "fallback",
        "distance_km": dist_km,
        "duration_minutes": duration_min,
        "raw_duration_minutes": duration_min,
        "congestion_factor": congestion,
        "geometry": geometry,
    }
