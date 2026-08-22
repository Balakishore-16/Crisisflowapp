"""
CrisisFlow Database Seeder
══════════════════════════
Populates the database with realistic emergency infrastructure data
for the Hyderabad metro area (demonstration).
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from app.database import init_db, SessionLocal
from app.models import (
    Incident, Ambulance, FireStation, FireTruck, Hospital,
    TrafficCondition, WeatherCondition, RiskZone, ActivityLog,
)


def run_seed():
    init_db()
    db = SessionLocal()

    # ════════════════════════════════════════
    # FIRE STATIONS (6)
    # ════════════════════════════════════════
    fire_stations = [
        FireStation(id="FS-01", name="Station Alpha", location="Hitech City",
                    latitude=17.4486, longitude=78.3772, available_trucks=3, status="Available"),
        FireStation(id="FS-02", name="Station Bravo", location="Madhapur",
                    latitude=17.4400, longitude=78.3950, available_trucks=2, status="Available"),
        FireStation(id="FS-03", name="Station Charlie", location="Kukatpally",
                    latitude=17.4947, longitude=78.3996, available_trucks=2, status="Available"),
        FireStation(id="FS-04", name="Station Delta", location="Secunderabad",
                    latitude=17.4344, longitude=78.5013, available_trucks=2, status="Available"),
        FireStation(id="FS-05", name="Station Echo", location="LB Nagar",
                    latitude=17.3486, longitude=78.5528, available_trucks=2, status="Available"),
        FireStation(id="FS-06", name="Station Foxtrot", location="Jubilee Hills",
                    latitude=17.4318, longitude=78.4075, available_trucks=2, status="Available"),
    ]
    for s in fire_stations:
        db.merge(s)

    # ════════════════════════════════════════
    # FIRE TRUCKS (12)
    # ════════════════════════════════════════
    fire_trucks = [
        FireTruck(id="FT-01", station_id="FS-01", call_sign="Alpha-1", location="Hitech City",
                  latitude=17.4486, longitude=78.3772, status="Available",
                  equipment=["ladder", "hose", "breathing_apparatus", "thermal_camera"]),
        FireTruck(id="FT-02", station_id="FS-01", call_sign="Alpha-2", location="Hitech City",
                  latitude=17.4486, longitude=78.3772, status="Available",
                  equipment=["hose", "breathing_apparatus", "foam"]),
        FireTruck(id="FT-03", station_id="FS-01", call_sign="Alpha-3", location="Hitech City",
                  latitude=17.4486, longitude=78.3772, status="Available",
                  equipment=["ladder", "hose", "rescue_equipment"]),
        FireTruck(id="FT-04", station_id="FS-02", call_sign="Bravo-1", location="Madhapur",
                  latitude=17.4400, longitude=78.3950, status="Available",
                  equipment=["ladder", "hose", "breathing_apparatus", "thermal_camera"]),
        FireTruck(id="FT-05", station_id="FS-02", call_sign="Bravo-2", location="Madhapur",
                  latitude=17.4400, longitude=78.3950, status="Available",
                  equipment=["hose", "foam", "hazmat"]),
        FireTruck(id="FT-06", station_id="FS-03", call_sign="Charlie-1", location="Kukatpally",
                  latitude=17.4947, longitude=78.3996, status="Available",
                  equipment=["ladder", "hose", "breathing_apparatus"]),
        FireTruck(id="FT-07", station_id="FS-03", call_sign="Charlie-2", location="Kukatpally",
                  latitude=17.4947, longitude=78.3996, status="Available",
                  equipment=["hose", "rescue_equipment"]),
        FireTruck(id="FT-08", station_id="FS-04", call_sign="Delta-1", location="Secunderabad",
                  latitude=17.4344, longitude=78.5013, status="Available",
                  equipment=["ladder", "hose", "breathing_apparatus", "thermal_camera"]),
        FireTruck(id="FT-09", station_id="FS-04", call_sign="Delta-2", location="Secunderabad",
                  latitude=17.4344, longitude=78.5013, status="Maintenance",
                  equipment=["hose", "foam"]),
        FireTruck(id="FT-10", station_id="FS-05", call_sign="Echo-1", location="LB Nagar",
                  latitude=17.3486, longitude=78.5528, status="Available",
                  equipment=["ladder", "hose", "breathing_apparatus"]),
        FireTruck(id="FT-11", station_id="FS-05", call_sign="Echo-2", location="LB Nagar",
                  latitude=17.3486, longitude=78.5528, status="Available",
                  equipment=["hose", "rescue_equipment", "jaws_of_life"]),
        FireTruck(id="FT-12", station_id="FS-06", call_sign="Foxtrot-1", location="Jubilee Hills",
                  latitude=17.4318, longitude=78.4075, status="Available",
                  equipment=["ladder", "hose", "breathing_apparatus", "thermal_camera"]),
    ]
    for t in fire_trucks:
        db.merge(t)

    # ════════════════════════════════════════
    # AMBULANCES (16)
    # ════════════════════════════════════════
    ambulances = [
        Ambulance(id="A-01", call_sign="Medic-01", location="Hitech City",
                  latitude=17.4455, longitude=78.3800, status="Available",
                  equipment=["defibrillator", "first_aid", "oxygen", "stretcher"], capacity=2),
        Ambulance(id="A-02", call_sign="Medic-02", location="Madhapur",
                  latitude=17.4420, longitude=78.3930, status="Available",
                  equipment=["defibrillator", "first_aid", "oxygen"], capacity=2),
        Ambulance(id="A-03", call_sign="Medic-03", location="Gachibowli",
                  latitude=17.4401, longitude=78.3489, status="Available",
                  equipment=["first_aid", "oxygen", "stretcher"], capacity=3),
        Ambulance(id="A-04", call_sign="Medic-04", location="Kukatpally",
                  latitude=17.4950, longitude=78.4010, status="Available",
                  equipment=["defibrillator", "first_aid", "oxygen"], capacity=2),
        Ambulance(id="A-05", call_sign="Medic-05", location="Secunderabad",
                  latitude=17.4350, longitude=78.5000, status="Available",
                  equipment=["first_aid", "oxygen", "stretcher"], capacity=2),
        Ambulance(id="A-06", call_sign="Medic-06", location="Ameerpet",
                  latitude=17.4374, longitude=78.4482, status="Available",
                  equipment=["defibrillator", "first_aid", "oxygen"], capacity=2),
        Ambulance(id="A-07", call_sign="Medic-07", location="Jubilee Hills",
                  latitude=17.4320, longitude=78.4080, status="Available",
                  equipment=["first_aid", "oxygen"], capacity=2),
        Ambulance(id="A-08", call_sign="Medic-08", location="LB Nagar",
                  latitude=17.3500, longitude=78.5520, status="Available",
                  equipment=["defibrillator", "first_aid", "oxygen", "stretcher"], capacity=3),
        Ambulance(id="A-09", call_sign="Medic-09", location="ECIL",
                  latitude=17.4680, longitude=78.5718, status="Available",
                  equipment=["first_aid", "oxygen"], capacity=2),
        Ambulance(id="A-10", call_sign="Medic-10", location="Charminar",
                  latitude=17.3616, longitude=78.4747, status="Available",
                  equipment=["defibrillator", "first_aid", "oxygen"], capacity=2),
        Ambulance(id="A-11", call_sign="Medic-11", location="Banjara Hills",
                  latitude=17.4250, longitude=78.4400, status="Available",
                  equipment=["first_aid", "oxygen", "stretcher"], capacity=2),
        Ambulance(id="A-12", call_sign="Medic-12", location="Begumpet",
                  latitude=17.4440, longitude=78.4700, status="Available",
                  equipment=["defibrillator", "first_aid", "oxygen"], capacity=2),
        Ambulance(id="A-13", call_sign="Medic-13", location="Miyapur",
                  latitude=17.4967, longitude=78.3557, status="Available",
                  equipment=["first_aid", "oxygen"], capacity=2),
        Ambulance(id="A-14", call_sign="Medic-14", location="Dilsukhnagar",
                  latitude=17.3687, longitude=78.5260, status="Available",
                  equipment=["defibrillator", "first_aid", "oxygen", "stretcher"], capacity=3),
        Ambulance(id="A-15", call_sign="Medic-15", location="Tolichowki",
                  latitude=17.4058, longitude=78.4183, status="Maintenance",
                  equipment=["first_aid", "oxygen"], capacity=2),
        Ambulance(id="A-16", call_sign="Medic-16", location="Uppal",
                  latitude=17.4050, longitude=78.5600, status="Available",
                  equipment=["defibrillator", "first_aid", "oxygen"], capacity=2),
    ]
    for a in ambulances:
        db.merge(a)

    # ════════════════════════════════════════
    # HOSPITALS (8)
    # ════════════════════════════════════════
    hospitals = [
        Hospital(id="H-01", name="City Hospital", location="Madhapur",
                 latitude=17.4420, longitude=78.3900,
                 emergency_capacity=60, icu_beds=15, trauma_beds=12, burn_capacity=8,
                 occupancy=0.45, status="Available"),
        Hospital(id="H-02", name="Metro General Hospital", location="Hitech City",
                 latitude=17.4500, longitude=78.3810,
                 emergency_capacity=45, icu_beds=10, trauma_beds=8, burn_capacity=5,
                 occupancy=0.55, status="Available"),
        Hospital(id="H-03", name="Central Medical Center", location="Secunderabad",
                 latitude=17.4380, longitude=78.4980,
                 emergency_capacity=80, icu_beds=20, trauma_beds=15, burn_capacity=10,
                 occupancy=0.60, status="Available"),
        Hospital(id="H-04", name="South City Hospital", location="LB Nagar",
                 latitude=17.3520, longitude=78.5500,
                 emergency_capacity=40, icu_beds=8, trauma_beds=6, burn_capacity=3,
                 occupancy=0.35, status="Available"),
        Hospital(id="H-05", name="Apollo Emergency", location="Jubilee Hills",
                 latitude=17.4300, longitude=78.4100,
                 emergency_capacity=70, icu_beds=18, trauma_beds=14, burn_capacity=7,
                 occupancy=0.50, status="Available"),
        Hospital(id="H-06", name="KIMS Hospital", location="Begumpet",
                 latitude=17.4440, longitude=78.4720,
                 emergency_capacity=55, icu_beds=12, trauma_beds=10, burn_capacity=6,
                 occupancy=0.65, status="Available"),
        Hospital(id="H-07", name="Yashoda Hospital", location="Somajiguda",
                 latitude=17.4260, longitude=78.4530,
                 emergency_capacity=50, icu_beds=14, trauma_beds=11, burn_capacity=4,
                 occupancy=0.40, status="Available"),
        Hospital(id="H-08", name="Gandhi Hospital", location="Musheerabad",
                 latitude=17.4050, longitude=78.4750,
                 emergency_capacity=90, icu_beds=22, trauma_beds=18, burn_capacity=12,
                 occupancy=0.72, status="Busy"),
    ]
    for h in hospitals:
        db.merge(h)

    # ════════════════════════════════════════
    # TRAFFIC CONDITIONS (8)
    # ════════════════════════════════════════
    traffic = [
        TrafficCondition(id="TR-01", route_name="Route A", from_location="Hitech City",
                         to_location="Madhapur", congestion_level=0.25, estimated_delay_minutes=3),
        TrafficCondition(id="TR-02", route_name="Route B", from_location="Hitech City",
                         to_location="Kukatpally", congestion_level=0.45, estimated_delay_minutes=7),
        TrafficCondition(id="TR-03", route_name="Route C", from_location="Madhapur",
                         to_location="Jubilee Hills", congestion_level=0.20, estimated_delay_minutes=2),
        TrafficCondition(id="TR-04", route_name="Route D", from_location="Secunderabad",
                         to_location="Ameerpet", congestion_level=0.60, estimated_delay_minutes=10),
        TrafficCondition(id="TR-05", route_name="Route E", from_location="LB Nagar",
                         to_location="Charminar", congestion_level=0.35, estimated_delay_minutes=5),
        TrafficCondition(id="TR-06", route_name="Route F", from_location="Gachibowli",
                         to_location="Hitech City", congestion_level=0.30, estimated_delay_minutes=4),
        TrafficCondition(id="TR-07", route_name="Route G", from_location="ECIL",
                         to_location="Secunderabad", congestion_level=0.55, estimated_delay_minutes=9),
        TrafficCondition(id="TR-08", route_name="Route H", from_location="Miyapur",
                         to_location="Kukatpally", congestion_level=0.40, estimated_delay_minutes=6),
    ]
    for t in traffic:
        db.merge(t)

    # ════════════════════════════════════════
    # WEATHER CONDITIONS
    # ════════════════════════════════════════
    weather = [
        WeatherCondition(id="W-01", location="Hyderabad Metro",
                         condition="Partly Cloudy", temperature=32.0,
                         wind_speed=12.0, humidity=65.0, visibility=8.0, risk_factor=0.15),
    ]
    for w in weather:
        db.merge(w)

    # ════════════════════════════════════════
    # RISK ZONES (6)
    # ════════════════════════════════════════
    risk_zones = [
        RiskZone(id="RZ-01", name="Hitech City Commercial", latitude=17.4435, longitude=78.3772,
                 radius=1.5, risk_level="Medium", risk_score=45,
                 factors=["High-rise density", "High occupancy", "Limited access roads"]),
        RiskZone(id="RZ-02", name="ECIL Industrial Belt", latitude=17.4680, longitude=78.5718,
                 radius=2.0, risk_level="High", risk_score=72,
                 factors=["Chemical storage", "Industrial machinery", "Worker density"]),
        RiskZone(id="RZ-03", name="Old City Charminar", latitude=17.3616, longitude=78.4747,
                 radius=1.0, risk_level="High", risk_score=68,
                 factors=["Narrow roads", "Dense population", "Old structures"]),
        RiskZone(id="RZ-04", name="Ameerpet Metro Hub", latitude=17.4374, longitude=78.4482,
                 radius=0.8, risk_level="Medium", risk_score=40,
                 factors=["High pedestrian traffic", "Metro construction"]),
        RiskZone(id="RZ-05", name="Kukatpally Residential", latitude=17.4947, longitude=78.3996,
                 radius=1.2, risk_level="Low", risk_score=25,
                 factors=["Residential area", "Moderate traffic"]),
        RiskZone(id="RZ-06", name="LB Nagar Flood Zone", latitude=17.3486, longitude=78.5528,
                 radius=1.5, risk_level="High", risk_score=70,
                 factors=["Low-lying area", "Poor drainage", "Seasonal flooding"]),
    ]
    for rz in risk_zones:
        db.merge(rz)

    # ════════════════════════════════════════
    # SEED INCIDENTS (4 — baseline normal ops)
    # ════════════════════════════════════════
    seed_incidents = [
        Incident(id="INC-2397", incident_type="Medical Emergency",
                 location="Ameerpet Metro", latitude=17.4374, longitude=78.4482,
                 severity="Medium", people_at_risk=2,
                 description="Medical emergency at Ameerpet Metro station. 2 passengers require assistance.",
                 status="Resolved", is_simulated=True),
        Incident(id="INC-2398", incident_type="Road Accident",
                 location="Jubilee Hills Road 36", latitude=17.4318, longitude=78.4075,
                 severity="Low", people_at_risk=3,
                 description="Minor fender-bender on Road 36. 3 people with minor injuries.",
                 status="Resolved", is_simulated=True),
        Incident(id="INC-2399", incident_type="Building Fire",
                 location="Kukatpally Housing Board", latitude=17.4947, longitude=78.3996,
                 floor=2, building="Building 12", severity="Medium", people_at_risk=15,
                 description="Small kitchen fire in Building 12. Residents evacuated.",
                 status="Resolved", is_simulated=True),
        Incident(id="INC-2400", incident_type="Medical Emergency",
                 location="LB Nagar Circle", latitude=17.3486, longitude=78.5528,
                 severity="High", people_at_risk=1,
                 description="Cardiac emergency at LB Nagar. Patient requires immediate transport.",
                 status="Dispatched", is_simulated=True),
    ]
    for inc in seed_incidents:
        db.merge(inc)

    db.commit()
    db.close()
    print("✓ CrisisFlow database seeded successfully")
    print(f"  → {len(fire_stations)} Fire Stations")
    print(f"  → {len(fire_trucks)} Fire Trucks")
    print(f"  → {len(ambulances)} Ambulances")
    print(f"  → {len(hospitals)} Hospitals")
    print(f"  → {len(traffic)} Traffic Routes")
    print(f"  → {len(risk_zones)} Risk Zones")
    print(f"  → {len(seed_incidents)} Seed Incidents")


if __name__ == "__main__":
    run_seed()
