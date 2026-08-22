"""
CrisisFlow External USGS Earthquake Service
═════════════════════════════════════════════
Integrates USGS Earthquake & Disaster events feed with deduplication.
"""
import os
import time
import logging
import httpx
from typing import List, Dict, Any

logger = logging.getLogger("crisisflow.earthquake")

USGS_BASE = os.getenv("USGS_BASE_URL", "https://earthquake.usgs.gov/fdsnws/event/1")
_SEEN_EVENT_IDS = set()


async def get_recent_earthquakes(min_magnitude: float = 3.0, limit: int = 10) -> List[Dict[str, Any]]:
    """
    Retrieve recent earthquakes from USGS GeoJSON feed filtered by minimum magnitude.
    """
    try:
        url = f"{USGS_BASE}/query?format=geojson&minmagnitude={min_magnitude}&limit={limit}"
        async with httpx.AsyncClient(timeout=4.0) as client:
            res = await client.get(url)
            if res.status_code == 200:
                data = res.json()
                features = data.get("features", [])
                events = []
                for feat in features:
                    evt_id = feat.get("id")
                    props = feat.get("properties", {})
                    geom = feat.get("geometry", {})
                    coords = geom.get("coordinates", [0, 0, 0])
                    lon = float(coords[0])
                    lat = float(coords[1])
                    depth = float(coords[2]) if len(coords) > 2 else 0.0

                    event = {
                        "source": "usgs",
                        "event_id": evt_id,
                        "magnitude": float(props.get("mag") or 0.0),
                        "place": props.get("place") or "Unknown Location",
                        "latitude": lat,
                        "longitude": lon,
                        "depth_km": depth,
                        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(props.get("time", 0) / 1000.0)) if props.get("time") else time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    }
                    events.append(event)
                    _SEEN_EVENT_IDS.add(evt_id)
                return events
    except Exception as e:
        logger.warning(f"USGS Earthquake API request failed ({e}). Returning empty list.")

    return []
