"""
CrisisFlow Database Seeder
══════════════════════════
Populates the database with realistic, deterministic emergency infrastructure
and historical telemetry for the Hyderabad metro demonstration area.
Target dataset:
  - 50 Incidents
  - 25 Ambulances
  - 10 Fire Trucks & 6 Fire Stations
  - 15 Hospitals
  - 20 Dispatches
  - 100+ Decision Audits
  - 30 Alerts
  - 50 Weather Events
  - 20 Road Blocks
"""
import sys
import os
import random
from datetime import datetime, timedelta, timezone

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.insert(0, os.path.dirname(__file__))

from app.database import init_db, SessionLocal, Base, engine
from app.models import (
    Incident, Ambulance, FireStation, FireTruck, Hospital,
    TrafficCondition, WeatherCondition, WeatherEvent, RoadBlock,
    RiskZone, Dispatch, Recommendation, DecisionAudit, Alert, ActivityLog,
)


def run_seed():
    # Recreate tables to apply updated schema definitions cleanly
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    db.query(ActivityLog).delete()
    db.query(DecisionAudit).delete()
    db.query(Recommendation).delete()
    db.query(Dispatch).delete()
    db.query(Alert).delete()
    db.query(RoadBlock).delete()
    db.query(WeatherEvent).delete()
    db.query(WeatherCondition).delete()
    db.query(TrafficCondition).delete()
    db.query(RiskZone).delete()
    db.query(Incident).delete()
    db.query(FireTruck).delete()
    db.query(FireStation).delete()
    db.query(Ambulance).delete()
    db.query(Hospital).delete()
    db.commit()

    now = datetime.now(timezone.utc)

    # ════════════════════════════════════════
    # 1. FIRE STATIONS (6)
    # ════════════════════════════════════════
    fire_stations = [
        FireStation(id="FS-01", name="Station Alpha (HITEC)", location="HITEC City Cyber Towers", zone="HITEC City",
                    latitude=17.4486, longitude=78.3772, available_trucks=3, status="Available"),
        FireStation(id="FS-02", name="Station Bravo (Madhapur)", location="Madhapur Main Road", zone="Madhapur",
                    latitude=17.4400, longitude=78.3950, available_trucks=2, status="Available"),
        FireStation(id="FS-03", name="Station Charlie (Kukatpally)", location="KPHB Colony", zone="Kukatpally",
                    latitude=17.4947, longitude=78.3996, available_trucks=2, status="Available"),
        FireStation(id="FS-04", name="Station Delta (Secunderabad)", location="Clock Tower", zone="Secunderabad",
                    latitude=17.4344, longitude=78.5013, available_trucks=2, status="Available"),
        FireStation(id="FS-05", name="Station Echo (LB Nagar)", location="LB Nagar Ring Road", zone="LB Nagar",
                    latitude=17.3486, longitude=78.5528, available_trucks=2, status="Available"),
        FireStation(id="FS-06", name="Station Foxtrot (Jubilee)", location="Jubilee Hills Checkpost", zone="Jubilee Hills",
                    latitude=17.4318, longitude=78.4075, available_trucks=2, status="Available"),
    ]
    for s in fire_stations:
        db.add(s)

    # ════════════════════════════════════════
    # 2. FIRE TRUCKS (10)
    # ════════════════════════════════════════
    fire_trucks = [
        FireTruck(id="FT-01", station_id="FS-01", resource_code="FT-ALPHA-1", call_sign="Alpha-1", location="HITEC City",
                  zone="HITEC City", latitude=17.4486, longitude=78.3772, status="Available",
                  equipment=["ladder", "hose", "breathing_apparatus", "thermal_camera"]),
        FireTruck(id="FT-02", station_id="FS-01", resource_code="FT-ALPHA-2", call_sign="Alpha-2", location="HITEC City",
                  zone="HITEC City", latitude=17.4486, longitude=78.3772, status="Available",
                  equipment=["hose", "breathing_apparatus", "foam", "hazmat"]),
        FireTruck(id="FT-03", station_id="FS-02", resource_code="FT-BRAVO-1", call_sign="Bravo-1", location="Madhapur",
                  zone="Madhapur", latitude=17.4400, longitude=78.3950, status="Available",
                  equipment=["ladder", "hose", "breathing_apparatus", "thermal_camera"]),
        FireTruck(id="FT-04", station_id="FS-02", resource_code="FT-BRAVO-2", call_sign="Bravo-2", location="Madhapur",
                  zone="Madhapur", latitude=17.4400, longitude=78.3950, status="Available",
                  equipment=["hose", "foam", "hazmat"]),
        FireTruck(id="FT-05", station_id="FS-03", resource_code="FT-CHARLIE-1", call_sign="Charlie-1", location="Kukatpally",
                  zone="Kukatpally", latitude=17.4947, longitude=78.3996, status="Available",
                  equipment=["ladder", "hose", "breathing_apparatus"]),
        FireTruck(id="FT-06", station_id="FS-03", resource_code="FT-CHARLIE-2", call_sign="Charlie-2", location="Kukatpally",
                  zone="Kukatpally", latitude=17.4947, longitude=78.3996, status="Available",
                  equipment=["hose", "rescue_equipment", "jaws_of_life"]),
        FireTruck(id="FT-07", station_id="FS-04", resource_code="FT-DELTA-1", call_sign="Delta-1", location="Secunderabad",
                  zone="Secunderabad", latitude=17.4344, longitude=78.5013, status="Available",
                  equipment=["ladder", "hose", "breathing_apparatus", "thermal_camera"]),
        FireTruck(id="FT-08", station_id="FS-04", resource_code="FT-DELTA-2", call_sign="Delta-2", location="Secunderabad",
                  zone="Secunderabad", latitude=17.4344, longitude=78.5013, status="Available",
                  equipment=["hose", "foam"]),
        FireTruck(id="FT-09", station_id="FS-05", resource_code="FT-ECHO-1", call_sign="Echo-1", location="LB Nagar",
                  zone="LB Nagar", latitude=17.3486, longitude=78.5528, status="Available",
                  equipment=["ladder", "hose", "breathing_apparatus", "jaws_of_life"]),
        FireTruck(id="FT-10", station_id="FS-06", resource_code="FT-FOXTROT-1", call_sign="Foxtrot-1", location="Jubilee Hills",
                  zone="Jubilee Hills", latitude=17.4318, longitude=78.4075, status="Available",
                  equipment=["ladder", "hose", "breathing_apparatus", "thermal_camera"]),
    ]
    for t in fire_trucks:
        db.add(t)

    # ════════════════════════════════════════
    # 3. AMBULANCES (25)
    # ════════════════════════════════════════
    ambulance_configs = [
        ("A-01", "AMB-101", "Medic-01", "HITEC City Cyber Towers", "HITEC City", 17.4455, 78.3800, 2, ["defibrillator", "first_aid", "oxygen", "stretcher"]),
        ("A-02", "AMB-102", "Medic-02", "Madhapur Inorbit", "Madhapur", 17.4420, 78.3930, 2, ["defibrillator", "first_aid", "oxygen"]),
        ("A-03", "AMB-103", "Medic-03", "Gachibowli Stadium", "Gachibowli", 17.4401, 78.3489, 3, ["first_aid", "oxygen", "stretcher", "trauma_kit"]),
        ("A-04", "AMB-104", "Medic-04", "Kukatpally Y-Junction", "Kukatpally", 17.4950, 78.4010, 2, ["defibrillator", "first_aid", "oxygen"]),
        ("A-05", "AMB-105", "Medic-05", "Secunderabad Station", "Secunderabad", 17.4350, 78.5000, 2, ["first_aid", "oxygen", "stretcher", "cardiac_monitor"]),
        ("A-06", "AMB-106", "Medic-06", "Ameerpet Metro", "Ameerpet", 17.4374, 78.4482, 2, ["defibrillator", "first_aid", "oxygen"]),
        ("A-07", "AMB-107", "Medic-07", "Jubilee Hills Road 36", "Jubilee Hills", 17.4320, 78.4080, 2, ["first_aid", "oxygen", "stretcher"]),
        ("A-08", "AMB-108", "Medic-08", "LB Nagar Ring", "LB Nagar", 17.3500, 78.5520, 3, ["defibrillator", "first_aid", "oxygen", "stretcher"]),
        ("A-09", "AMB-109", "Medic-09", "ECIL X Roads", "ECIL", 17.4680, 78.5718, 2, ["first_aid", "oxygen", "toxicology_kit"]),
        ("A-10", "AMB-110", "Medic-10", "Charminar Monument", "Charminar", 17.3616, 78.4747, 2, ["defibrillator", "first_aid", "oxygen"]),
        ("A-11", "AMB-111", "Medic-11", "Banjara Hills Rd 12", "Banjara Hills", 17.4250, 78.4400, 2, ["first_aid", "oxygen", "stretcher", "defibrillator"]),
        ("A-12", "AMB-112", "Medic-12", "Begumpet Airport Link", "Begumpet", 17.4440, 78.4700, 2, ["defibrillator", "first_aid", "oxygen"]),
        ("A-13", "AMB-113", "Medic-13", "Miyapur Metro Depot", "Miyapur", 17.4967, 78.3557, 2, ["first_aid", "oxygen", "stretcher"]),
        ("A-14", "AMB-114", "Medic-14", "Dilsukhnagar Bus Stand", "Dilsukhnagar", 17.3687, 78.5260, 3, ["defibrillator", "first_aid", "oxygen", "stretcher"]),
        ("A-15", "AMB-115", "Medic-15", "Tolichowki Flyover", "Tolichowki", 17.4058, 78.4183, 2, ["first_aid", "oxygen"]),
        ("A-16", "AMB-116", "Medic-16", "Uppal Stadium", "Uppal", 17.4050, 78.5600, 2, ["defibrillator", "first_aid", "oxygen"]),
        ("A-17", "AMB-117", "Medic-17", "Financial District", "Gachibowli", 17.4180, 78.3420, 2, ["first_aid", "oxygen", "stretcher", "defibrillator"]),
        ("A-18", "AMB-118", "Medic-18", "Kondapur Botanical Garden", "Kondapur", 17.4580, 78.3620, 2, ["first_aid", "oxygen", "stretcher"]),
        ("A-19", "AMB-119", "Medic-19", "Jeedimetla Industrial Hub", "Jeedimetla", 17.5186, 78.4712, 3, ["hazmat", "first_aid", "oxygen", "burn_kit", "trauma_kit"]),
        ("A-20", "AMB-120", "Medic-20", "Sanath Nagar", "Sanath Nagar", 17.4550, 78.4350, 2, ["defibrillator", "first_aid", "oxygen"]),
        ("A-21", "AMB-121", "Medic-21", "Somajiguda Circle", "Somajiguda", 17.4260, 78.4530, 2, ["first_aid", "oxygen", "stretcher"]),
        ("A-22", "AMB-122", "Medic-22", "Panjagutta Junction", "Panjagutta", 17.4280, 78.4480, 2, ["defibrillator", "first_aid", "oxygen"]),
        ("A-23", "AMB-123", "Medic-23", "Mehdipatnam Bus Depot", "Mehdipatnam", 17.3950, 78.4380, 3, ["first_aid", "oxygen", "stretcher", "trauma_kit"]),
        ("A-24", "AMB-124", "Medic-24", "Attapur Pillar 140", "Attapur", 17.3780, 78.4320, 2, ["defibrillator", "first_aid", "oxygen"]),
        ("A-25", "AMB-125", "Medic-25", "Kothapet Fruit Market", "Kothapet", 17.3620, 78.5420, 2, ["first_aid", "oxygen", "stretcher"]),
    ]
    for aid, code, call_sign, loc, zone, lat, lon, cap, eq in ambulance_configs:
        amb = Ambulance(
            id=aid,
            resource_code=code,
            resource_type="Ambulance",
            call_sign=call_sign,
            location=loc,
            zone=zone,
            latitude=lat,
            longitude=lon,
            status="Available",
            equipment=eq,
            capacity=cap,
        )
        db.add(amb)

    # ════════════════════════════════════════
    # 4. HOSPITALS (15)
    # ════════════════════════════════════════
    hospitals_data = [
        ("H-01", "City Care Hospital", "Madhapur", "Madhapur", 17.4420, 78.3900, 100, 28, 60, 15, 12, 8, ["Trauma", "Burn Care", "Emergency", "Cardiology"], 0.45),
        ("H-02", "Metro General Hospital", "HITEC City", "HITEC City", 17.4500, 78.3810, 80, 22, 45, 10, 8, 5, ["Emergency", "Trauma", "Neurology"], 0.55),
        ("H-03", "Central Medical Institute", "Secunderabad", "Secunderabad", 17.4380, 78.4980, 150, 45, 80, 20, 15, 10, ["Trauma", "Cardiology", "Burn Care", "Emergency"], 0.60),
        ("H-04", "South City Super Specialty", "LB Nagar", "LB Nagar", 17.3520, 78.5500, 70, 30, 40, 8, 6, 3, ["Emergency", "Orthopedics", "Trauma"], 0.35),
        ("H-05", "Apollo Emergency Trauma Center", "Jubilee Hills", "Jubilee Hills", 17.4300, 78.4100, 120, 35, 70, 18, 14, 7, ["Trauma", "Cardiology", "Neurology", "Burn Care", "Emergency"], 0.50),
        ("H-06", "KIMS Multi-Specialty", "Begumpet", "Begumpet", 17.4440, 78.4720, 110, 25, 55, 12, 10, 6, ["Cardiology", "ICU", "Emergency", "Toxicology"], 0.65),
        ("H-07", "Yashoda Hospital", "Somajiguda", "Somajiguda", 17.4260, 78.4530, 95, 32, 50, 14, 11, 4, ["Cardiology", "Trauma", "Emergency"], 0.40),
        ("H-08", "Gandhi Memorial Government Hospital", "Musheerabad", "Secunderabad", 17.4050, 78.4750, 200, 40, 90, 22, 18, 12, ["Trauma", "Burn Care", "Toxicology", "Emergency"], 0.72),
        ("H-09", "Continental Hospital", "Financial District", "Gachibowli", 17.4180, 78.3420, 130, 42, 65, 16, 14, 6, ["Trauma", "Emergency", "Cardiology", "Orthopedics"], 0.48),
        ("H-10", "AIG Hospitals", "Gachibowli", "Gachibowli", 17.4410, 78.3610, 140, 50, 70, 20, 15, 5, ["Emergency", "ICU", "Gastroenterology", "Cardiology"], 0.52),
        ("H-11", "Care Hospital", "Banjara Hills", "Banjara Hills", 17.4170, 78.4480, 115, 38, 55, 15, 12, 4, ["Cardiology", "Trauma", "Emergency"], 0.58),
        ("H-12", "Rainbow Emergency Hospital", "Kondapur", "Kondapur", 17.4620, 78.3580, 65, 20, 35, 8, 6, 2, ["Pediatric Trauma", "Emergency"], 0.44),
        ("H-13", "Omni Hospital", "Kothapet", "LB Nagar", 17.3650, 78.5380, 75, 24, 40, 9, 7, 3, ["Emergency", "Trauma", "Orthopedics"], 0.46),
        ("H-14", "MaxCure Institute", "Madhapur", "Madhapur", 17.4470, 78.3840, 85, 26, 45, 10, 8, 4, ["Emergency", "Orthopedics", "Trauma"], 0.42),
        ("H-15", "Industrial Health Trauma Care", "Jeedimetla", "Jeedimetla", 17.5190, 78.4720, 90, 30, 50, 14, 12, 8, ["Toxicology", "Burn Care", "Trauma", "Emergency"], 0.38),
    ]
    for hid, name, loc, zone, lat, lon, total, avail, emerg, icu, trauma, burn, specs, occ in hospitals_data:
        hosp = Hospital(
            id=hid,
            name=name,
            location=loc,
            zone=zone,
            latitude=lat,
            longitude=lon,
            total_beds=total,
            available_beds=avail,
            emergency_capacity=emerg,
            icu_beds=icu,
            trauma_beds=trauma,
            burn_capacity=burn,
            specialties=specs,
            occupancy=occ,
            status="Available",
        )
        db.add(hosp)

    # ════════════════════════════════════════
    # 5. RISK ZONES (6)
    # ════════════════════════════════════════
    risk_zones = [
        RiskZone(id="RZ-01", name="Hitech City Commercial Corridor", latitude=17.4435, longitude=78.3772,
                 radius=1.5, risk_level="Medium", risk_score=45,
                 factors=["High-rise commercial density", "High daytime occupancy", "Flyover choke points"]),
        RiskZone(id="RZ-02", name="Jeedimetla & ECIL Industrial Belt", latitude=17.5186, longitude=78.4712,
                 radius=2.5, risk_level="Critical", risk_score=88,
                 factors=["Chemical storage facilities", "High thermal processes", "Dense worker presence"]),
        RiskZone(id="RZ-03", name="Old City Charminar Historical Zone", latitude=17.3616, longitude=78.4747,
                 radius=1.2, risk_level="High", risk_score=72,
                 factors=["Narrow access roads", "High population density", "Aging infrastructure"]),
        RiskZone(id="RZ-04", name="Ameerpet Transit Hub", latitude=17.4374, longitude=78.4482,
                 radius=0.8, risk_level="Medium", risk_score=40,
                 factors=["High pedestrian volumes", "Metro interchange junction"]),
        RiskZone(id="RZ-05", name="Kukatpally High-Density Residential", latitude=17.4947, longitude=78.3996,
                 radius=1.8, risk_level="Low", risk_score=25,
                 factors=["Residential colonies", "Multiple arterial exit lanes"]),
        RiskZone(id="RZ-06", name="LB Nagar Lowline Flood Inundation Zone", latitude=17.3486, longitude=78.5528,
                 radius=2.0, risk_level="High", risk_score=76,
                 factors=["Low-lying basin", "Lake overflow vulnerability", "Stormwater backflow"]),
    ]
    for rz in risk_zones:
        db.add(rz)

    # ════════════════════════════════════════
    # 6. TRAFFIC CONDITIONS (8)
    # ════════════════════════════════════════
    traffic = [
        TrafficCondition(id="TR-01", route_name="Route A (HITEC-Madhapur)", from_location="HITEC City",
                         to_location="Madhapur", congestion_level=0.25, estimated_delay_minutes=3.0),
        TrafficCondition(id="TR-02", route_name="Route B (HITEC-Kukatpally)", from_location="HITEC City",
                         to_location="Kukatpally", congestion_level=0.45, estimated_delay_minutes=7.0),
        TrafficCondition(id="TR-03", route_name="Route C (Madhapur-Jubilee)", from_location="Madhapur",
                         to_location="Jubilee Hills", congestion_level=0.20, estimated_delay_minutes=2.0),
        TrafficCondition(id="TR-04", route_name="Route D (Secunderabad-Ameerpet)", from_location="Secunderabad",
                         to_location="Ameerpet", congestion_level=0.60, estimated_delay_minutes=10.0),
        TrafficCondition(id="TR-05", route_name="Route E (LB Nagar-Charminar)", from_location="LB Nagar",
                         to_location="Charminar", congestion_level=0.35, estimated_delay_minutes=5.0),
        TrafficCondition(id="TR-06", route_name="Route F (Gachibowli-HITEC)", from_location="Gachibowli",
                         to_location="HITEC City", congestion_level=0.30, estimated_delay_minutes=4.0),
        TrafficCondition(id="TR-07", route_name="Route G (ECIL-Secunderabad)", from_location="ECIL",
                         to_location="Secunderabad", congestion_level=0.55, estimated_delay_minutes=9.0),
        TrafficCondition(id="TR-08", route_name="Route H (Miyapur-Kukatpally)", from_location="Miyapur",
                         to_location="Kukatpally", congestion_level=0.40, estimated_delay_minutes=6.0),
    ]
    for t in traffic:
        db.add(t)

    # ════════════════════════════════════════
    # 7. WEATHER CONDITIONS & WEATHER EVENTS (50)
    # ════════════════════════════════════════
    w_main = WeatherCondition(
        id="W-01", location="Hyderabad Central", zone="Hyderabad Metro",
        condition="Partly Cloudy", temperature=31.5, wind_speed=12.0,
        humidity=62.0, visibility=8.5, rainfall_mm_hr=0.0, flood_depth_m=0.0, risk_factor=0.15,
    )
    db.add(w_main)

    zones_list = ["HITEC City", "Gachibowli", "Madhapur", "Banjara Hills", "Jubilee Hills", "Secunderabad", "Kukatpally", "LB Nagar", "Jeedimetla", "Charminar"]
    for i in range(1, 51):
        z = zones_list[(i - 1) % len(zones_list)]
        we = WeatherEvent(
            id=f"WE-{1000 + i}",
            location=f"{z} Telemetry Point {i % 4 + 1}",
            zone=z,
            condition="Heavy Rain" if i % 7 == 0 else ("Thunderstorm" if i % 11 == 0 else "Partly Cloudy"),
            rainfall_mm_hr=random.uniform(40.0, 85.0) if i % 7 == 0 else random.uniform(0.0, 10.0),
            flood_depth_m=random.uniform(0.3, 0.7) if i % 7 == 0 else 0.0,
            wind_speed=random.uniform(8.0, 35.0),
            risk_factor=random.uniform(0.6, 0.9) if i % 7 == 0 else random.uniform(0.1, 0.3),
            created_at=now - timedelta(hours=50 - i),
        )
        db.add(we)

    # ════════════════════════════════════════
    # 8. ROAD BLOCKS (20)
    # ════════════════════════════════════════
    roadblock_reasons = [
        "Construction & Metro Work",
        "Waterlogging / Flash Flood Inundation",
        "Multi-Vehicle Collision Investigation",
        "Tree Fall & Power Line Repair",
        "VIP Movement Security Corridor",
    ]
    for i in range(1, 21):
        z = zones_list[(i - 1) % len(zones_list)]
        rb = RoadBlock(
            id=f"RB-{100 + i}",
            road_name=f"{z} Arterial Sector {i % 5 + 1}",
            zone=z,
            reason=roadblock_reasons[(i - 1) % len(roadblock_reasons)],
            severity="High" if i % 3 == 0 else "Medium",
            latitude=17.4000 + (i * 0.006),
            longitude=78.4000 + (i * 0.007),
            delay_minutes=random.uniform(8.0, 28.0),
            is_active=True if i <= 15 else False,
            created_at=now - timedelta(hours=24 - i),
        )
        db.add(rb)

    # ════════════════════════════════════════
    # 9. INCIDENTS (50) & DISPATCHES (20) & DECISION AUDITS (100+)
    # ════════════════════════════════════════
    incident_types = ["Building Fire", "Road Accident", "Medical Emergency", "Flood", "Industrial Accident"]
    severities = ["Critical", "High", "Medium", "Low"]

    for i in range(1, 51):
        inc_id = f"INC-{2350 + i}"
        itype = incident_types[(i - 1) % len(incident_types)]
        zone = zones_list[(i - 1) % len(zones_list)]
        sev = severities[(i - 1) % len(severities)]
        status = "Resolved" if i <= 35 else ("Dispatched" if i <= 45 else "Detected")
        people = random.randint(1, 35) if sev in ("Critical", "High") else random.randint(1, 5)
        created_time = now - timedelta(hours=60 - i)

        inc = Incident(
            id=inc_id,
            incident_type=itype,
            location=f"{zone} Central Sector {i % 6 + 1}",
            zone=zone,
            latitude=17.4000 + ((i % 10) * 0.012),
            longitude=78.3600 + ((i % 10) * 0.018),
            floor=random.randint(1, 10) if itype in ("Building Fire", "Industrial Accident") else None,
            building=f"Tower {chr(65 + (i % 6))}" if itype == "Building Fire" else None,
            severity=sev,
            people_at_risk=people,
            description=f"Automated incident record for {itype} in {zone}. {people} persons impacted.",
            status=status,
            spread_risk="High" if sev == "Critical" else "Medium",
            created_at=created_time,
            updated_at=created_time + timedelta(minutes=15),
            is_simulated=True,
        )
        db.add(inc)

        # Generate recommendation & audit for each incident
        rec_id = f"REC-{3000 + i}"
        amb_assigned = f"A-{(i % 25) + 1:02d}"
        hosp_assigned = f"H-{(i % 15) + 1:02d}"
        st_assigned = f"FS-{(i % 6) + 1:02d}"
        eta = round(random.uniform(4.5, 14.0), 1)
        conf = round(random.uniform(84.0, 96.5), 1)

        breakdown = {
            "distance": round(random.uniform(75.0, 95.0), 1),
            "traffic": round(random.uniform(70.0, 90.0), 1),
            "availability": 100.0,
            "equipment": round(random.uniform(80.0, 100.0), 1),
            "hospital_capacity": round(random.uniform(70.0, 92.0), 1),
            "eta": round(max(0.0, 100.0 - eta * 3.0), 1),
        }

        reasons = [
            f"Ambulance {amb_assigned} selected as optimal proximity unit ({eta} min ETA)",
            f"Hospital {hosp_assigned} has active capacity and matching specialty care",
            "Route optimized for minimal congestion delay",
        ]

        rec = Recommendation(
            id=rec_id,
            incident_id=inc_id,
            resource_id=amb_assigned,
            fire_station_id=st_assigned if itype in ("Building Fire", "Industrial Accident") else None,
            fire_station_name=f"Station Alpha" if st_assigned == "FS-01" else "Station Support",
            fire_truck_id=f"FT-{(i % 10) + 1:02d}" if itype in ("Building Fire", "Industrial Accident") else None,
            ambulance_id=amb_assigned,
            hospital_id=hosp_assigned,
            hospital_name=f"Hospital-{hosp_assigned}",
            route="Route A (Expressway)" if i % 2 == 0 else "Route B (Main Arterial)",
            eta_minutes=eta,
            score=conf,
            confidence=conf,
            algorithm="MultiFactor-Optimization-v1",
            reasons=reasons,
            score_breakdown=breakdown,
            data_considered=["distance", "traffic", "availability", "equipment", "severity", "hospital_capacity", "response_time"],
            explanation=f"Decision Engine recommended {amb_assigned} and {hosp_assigned} with {conf}% confidence.",
            created_at=created_time + timedelta(seconds=12),
        )
        db.add(rec)

        # Primary Audit Record
        audit1 = DecisionAudit(
            id=f"AUD-{5000 + (i * 2) - 1}",
            incident_id=inc_id,
            candidate_resources=[{"id": amb_assigned, "score": conf, "eta": eta}],
            candidate_hospitals=[{"id": hosp_assigned, "score": conf, "eta": eta}],
            rejected_candidates=[{"id": f"A-{((i + 3) % 25) + 1:02d}", "reason": "Higher ETA / Suboptimal proximity"}],
            selected_resource={"ambulance_id": amb_assigned, "eta_minutes": eta},
            selected_hospital={"hospital_id": hosp_assigned},
            score_breakdown=breakdown,
            score=conf,
            confidence=conf,
            eta_minutes=eta,
            algorithm="Deterministic-MultiFactor-Optimizer-v1",
            reason="; ".join(reasons),
            human_override=False,
            final_decision={"ambulance_id": amb_assigned, "hospital_id": hosp_assigned, "eta_minutes": eta},
            created_at=created_time + timedelta(seconds=12),
        )
        db.add(audit1)

        # Second historical audit revision for thorough dataset depth (100+ audits)
        audit2 = DecisionAudit(
            id=f"AUD-{5000 + (i * 2)}",
            incident_id=inc_id,
            candidate_resources=[{"id": amb_assigned, "score": conf, "eta": eta}],
            candidate_hospitals=[{"id": hosp_assigned, "score": conf, "eta": eta}],
            rejected_candidates=[],
            selected_resource={"ambulance_id": amb_assigned, "eta_minutes": eta},
            selected_hospital={"hospital_id": hosp_assigned},
            score_breakdown=breakdown,
            score=conf,
            confidence=conf,
            eta_minutes=eta,
            algorithm="MultiFactor-Evaluator-v1",
            reason="Re-evaluation confirmed optimal route.",
            human_override=False,
            final_decision={"ambulance_id": amb_assigned, "hospital_id": hosp_assigned},
            created_at=created_time + timedelta(seconds=30),
        )
        db.add(audit2)

        # Create 20 Dispatches for historical analytics
        if i <= 20:
            dsp_id = f"DSP-{8000 + i}"
            assigned_time = created_time + timedelta(minutes=1)
            completed_time = assigned_time + timedelta(minutes=int(eta) + 8)
            dsp = Dispatch(
                id=dsp_id,
                incident_id=inc_id,
                resource_id=amb_assigned,
                fire_station_id=st_assigned if itype in ("Building Fire", "Industrial Accident") else None,
                fire_truck_id=f"FT-{(i % 10) + 1:02d}" if itype in ("Building Fire", "Industrial Accident") else None,
                ambulance_id=amb_assigned,
                hospital_id=hosp_assigned,
                route="Route A (Expressway)",
                eta_minutes=eta,
                distance_km=round(eta * 0.65, 2),
                confidence=conf,
                reasons=reasons,
                status="Completed" if i <= 15 else "Dispatched",
                assigned_at=assigned_time,
                completed_at=completed_time if i <= 15 else None,
                created_at=assigned_time,
            )
            db.add(dsp)

    # ════════════════════════════════════════
    # 10. ALERTS (30)
    # ════════════════════════════════════════
    alert_templates = [
        ("critical.incident", "Critical", "🚨 CRITICAL: High-Rise Building Fire detected in HITEC City"),
        ("resource.shortage", "Critical", "⚠️ LOW RESOURCES: Only 1 ambulance currently idle in Gachibowli sector"),
        ("hospital.capacity", "High", "🏥 HOSPITAL OVERLOAD: Metro General Hospital at 92% occupancy"),
        ("flood.risk", "High", "🌊 FLOOD RISK: Canal overflow detected in Madhapur basin (depth 0.65m)"),
        ("response.escalation", "Medium", "⏰ RESPONSE SLA ALERT: Incident response ETA exceeds 12 minute threshold"),
    ]
    for i in range(1, 31):
        atype, sev, msg = alert_templates[(i - 1) % len(alert_templates)]
        z = zones_list[(i - 1) % len(zones_list)]
        al = Alert(
            id=f"ALT-{9000 + i}",
            alert_type=atype,
            severity=sev,
            message=f"{msg} ({z})",
            zone=z,
            entity_id=f"INC-{2350 + i}",
            acknowledged=True if i <= 20 else False,
            created_at=now - timedelta(hours=35 - i),
        )
        db.add(al)

    db.commit()
    db.close()
    print("✓ CrisisFlow complete enterprise dataset seeded successfully:")
    print(f"  → {len(fire_stations)} Fire Stations")
    print(f"  → {len(fire_trucks)} Fire Trucks")
    print(f"  → {len(ambulance_configs)} Ambulances")
    print(f"  → {len(hospitals_data)} Hospitals")
    print(f"  → {len(risk_zones)} Risk Zones")
    print(f"  → {len(traffic)} Traffic Routes")
    print(f"  → 50 Weather Events & Conditions")
    print(f"  → 20 Road Blocks")
    print(f"  → 50 Incidents")
    print(f"  → 20 Dispatches")
    print(f"  → 100 Decision Audits")
    print(f"  → 30 Alerts")


if __name__ == "__main__":
    run_seed()
