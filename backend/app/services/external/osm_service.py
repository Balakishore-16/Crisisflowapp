"""
CrisisFlow External OpenStreetMap / Overpass Facility Service
══════════════════════════════════════════════════════════════
Queries Overpass API for nearby hospitals, clinics, and emergency facilities.
Includes TTL caching to avoid repeated Overpass requests for the same area.
"""
import os
import time
import logging
import httpx
from typing import List, Dict, Any

logger = logging.getLogger("crisisflow.osm")

OVERPASS_BASE = os.getenv("OVERPASS_BASE_URL", "https://overpass-api.de/api/interpreter")

_OSM_CACHE: Dict[str, Dict[str, Any]] = {}
CACHE_TTL_SECONDS = 1800  # 30 minutes


async def search_nearby_facilities(
    latitude: float, longitude: float, radius_meters: int = 5000
) -> List[Dict[str, Any]]:
    """
    Search Overpass OSM for nearby hospitals and emergency medical facilities.
    """
    cache_key = f"{round(latitude, 2)},{round(longitude, 2)},{radius_meters}"
    now_ts = time.time()

    if cache_key in _OSM_CACHE:
        cached = _OSM_CACHE[cache_key]
        if now_ts - cached["_cached_at"] < CACHE_TTL_SECONDS:
            return cached["data"]

    query = f"""
    [out:json][timeout:5];
    (
      node["amenity"="hospital"](around:{radius_meters},{latitude},{longitude});
      way["amenity"="hospital"](around:{radius_meters},{latitude},{longitude});
      node["amenity"="clinic"](around:{radius_meters},{latitude},{longitude});
    );
    out center 15;
    """

    try:
        async with httpx.AsyncClient(timeout=4.0) as client:
            res = await client.post(OVERPASS_BASE, data={"data": query})
            if res.status_code == 200:
                data = res.json()
                elements = data.get("elements", [])
                facilities = []
                for el in elements:
                    tags = el.get("tags", {})
                    name = tags.get("name") or tags.get("name:en") or "Emergency Facility"
                    f_lat = el.get("lat") or el.get("center", {}).get("lat")
                    f_lon = el.get("lon") or el.get("center", {}).get("lon")
                    if f_lat and f_lon:
                        facilities.append({
                            "source": "openstreetmap",
                            "name": name,
                            "facility_type": tags.get("amenity", "hospital"),
                            "latitude": float(f_lat),
                            "longitude": float(f_lon),
                            "emergency": tags.get("emergency", "yes"),
                        })
                if facilities:
                    _OSM_CACHE[cache_key] = {"_cached_at": now_ts, "data": facilities}
                    return facilities
    except Exception as e:
        logger.warning(f"Overpass OSM query failed ({e}). Returning empty facility list.")

    return []
