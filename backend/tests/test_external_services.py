import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import pytest
import asyncio
from fastapi.testclient import TestClient

from main import app
from app.services.external.weather_service import get_weather
from app.services.external.routing_service import calculate_route
from app.services.external.osm_service import search_nearby_facilities
from app.services.external.earthquake_service import get_recent_earthquakes
from app.services.external.air_quality_service import get_air_quality

client = TestClient(app)


@pytest.fixture
def anyio_backend():
    return 'asyncio'


# ─── 1. Open-Meteo Weather Service ───
@pytest.mark.anyio
async def test_open_meteo_weather_service():
    res = await get_weather(17.4486, 78.3772)
    assert "source" in res
    assert res["source"] in ("open-meteo", "rainviewer", "fallback")
    assert "temperature" in res
    assert "precipitation_mm" in res
    assert "risk_level" in res
    assert res["risk_level"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")


# ─── 2. OSRM Routing Service ───
@pytest.mark.anyio
async def test_osrm_routing_service():
    res = await calculate_route(17.4486, 78.3772, 17.4420, 78.3930, congestion=0.4)
    assert "source" in res
    assert res["source"] in ("osrm", "fallback")
    assert "distance_km" in res
    assert "duration_minutes" in res
    assert res["distance_km"] > 0
    assert res["duration_minutes"] > 0


# ─── 3. Overpass OSM Facility Discovery ───
@pytest.mark.anyio
async def test_osm_facility_service():
    facilities = await search_nearby_facilities(17.4486, 78.3772, radius_meters=3000)
    assert isinstance(facilities, list)
    if facilities:
        f = facilities[0]
        assert f["source"] == "openstreetmap"
        assert "name" in f
        assert "latitude" in f
        assert "longitude" in f


# ─── 4. AQICN Air Quality Service (Fallback / Key Validation) ───
@pytest.mark.anyio
async def test_air_quality_service():
    res = await get_air_quality(17.4486, 78.3772)
    assert "source" in res
    assert res["source"] in ("aqicn", "unavailable")
    assert "aqi" in res
    assert "risk_level" in res
    assert res["risk_level"] in ("LOW", "MEDIUM", "HIGH", "CRITICAL")


# ─── 5. USGS Earthquake Feed ───
@pytest.mark.anyio
async def test_usgs_earthquake_service():
    events = await get_recent_earthquakes(min_magnitude=3.0, limit=5)
    assert isinstance(events, list)
    if events:
        evt = events[0]
        assert evt["source"] == "usgs"
        assert "event_id" in evt
        assert "magnitude" in evt
        assert evt["magnitude"] >= 3.0


# ─── 6. External API REST Endpoints Test ───
def test_external_weather_endpoint():
    res = client.get("/api/external/weather?lat=17.4486&lon=78.3772")
    assert res.status_code == 200
    data = res.json()
    assert "source" in data
    assert "risk_level" in data


def test_external_route_endpoint():
    res = client.get("/api/external/route?origin_lat=17.4486&origin_lon=78.3772&dest_lat=17.4420&dest_lon=78.3930")
    assert res.status_code == 200
    data = res.json()
    assert "source" in data
    assert "distance_km" in data
    assert "duration_minutes" in data


def test_external_facilities_endpoint():
    res = client.get("/api/external/facilities?lat=17.4486&lon=78.3772&radius=3000")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_external_air_quality_endpoint():
    res = client.get("/api/external/air-quality?lat=17.4486&lon=78.3772")
    assert res.status_code == 200
    data = res.json()
    assert "source" in data


def test_external_earthquakes_endpoint():
    res = client.get("/api/external/earthquakes?min_mag=3.0&limit=5")
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_post_resource_location_update():
    # Fetch first ambulance ID
    amb_res = client.get("/api/ambulances")
    assert amb_res.status_code == 200
    ambulances = amb_res.json()
    assert len(ambulances) > 0
    amb_id = ambulances[0]["id"]

    # Post location update
    payload = {
        "latitude": 17.4435,
        "longitude": 78.3772,
        "accuracy_m": 4.5,
        "speed_kmh": 48.5,
        "heading": 135.0,
        "source": "LIVE_GPS",
        "status": "En Route"
    }
    loc_res = client.post(f"/api/resources/{amb_id}/location", json=payload)
    assert loc_res.status_code == 200
    loc_data = loc_res.json()
    assert loc_data["success"] == True
    assert loc_data["resource_id"] == amb_id
    assert loc_data["location_source"] == "LIVE_GPS"

    # Test history retrieval
    hist_res = client.get(f"/api/resources/{amb_id}/location-history")
    assert hist_res.status_code == 200
    hist_data = hist_res.json()
    assert len(hist_data) >= 1
    assert hist_data[0]["location_source"] == "LIVE_GPS"
