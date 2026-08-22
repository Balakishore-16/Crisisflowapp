"""
CrisisFlow External AQICN Air Quality Service
═════════════════════════════════════════════
Integrates AQICN Air Quality Index & PM2.5 sensors for environmental risk assessment.
Enabled only when AQICN_API_KEY is configured; falls back gracefully when absent.
"""
import os
import time
import logging
import httpx
from typing import Dict, Any

logger = logging.getLogger("crisisflow.air_quality")

AQICN_API_KEY = os.getenv("AQICN_API_KEY", "").strip()


def _compute_aqi_risk(aqi: int) -> str:
    """Classify Air Quality Index into environmental risk level."""
    if aqi >= 300:
        return "CRITICAL"
    elif aqi >= 150:
        return "HIGH"
    elif aqi >= 100:
        return "MEDIUM"
    return "LOW"


async def get_air_quality(latitude: float, longitude: float) -> Dict[str, Any]:
    """
    Retrieve Air Quality telemetry from AQICN for industrial / chemical hazard risk.
    """
    if not AQICN_API_KEY:
        return {
            "source": "unavailable",
            "aqi": 45,
            "pm25": 12.0,
            "risk_level": "LOW",
            "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        }

    try:
        url = f"https://api.waqi.info/feed/geo:{latitude};{longitude}/?token={AQICN_API_KEY}"
        async with httpx.AsyncClient(timeout=3.0) as client:
            res = await client.get(url)
            if res.status_code == 200:
                data = res.json()
                if data.get("status") == "ok" and "data" in data:
                    aq_data = data["data"]
                    aqi = int(aq_data.get("aqi", 45))
                    iaqi = aq_data.get("iaqi", {})
                    pm25 = float(iaqi.get("pm25", {}).get("v", 12.0))
                    risk_level = _compute_aqi_risk(aqi)

                    return {
                        "source": "aqicn",
                        "aqi": aqi,
                        "pm25": pm25,
                        "risk_level": risk_level,
                        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                    }
    except Exception as e:
        logger.warning(f"AQICN request failed ({e}). Returning fallback air quality.")

    return {
        "source": "unavailable",
        "aqi": 45,
        "pm25": 12.0,
        "risk_level": "LOW",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }
