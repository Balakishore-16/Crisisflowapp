# 🚨 CrisisFlow — Microsoft Fabric Emergency Response & Resource Optimization Platform

> CrisisFlow transforms raw emergency events into explainable, multi-factor resource-allocation decisions powered by a complete **Microsoft Fabric Real-Time Intelligence, Lakehouse Medallion, and Power BI** stack.

---

## 1. System Architecture

```
                                  CRISISFLOW COMMAND CENTER
                                       (React / Vite)
                                             │
                                             ▼
                                    FASTAPI BACKEND API
                                             │
                  ┌──────────────────────────┴──────────────────────────┐
                  ▼                                                     ▼
        DETERMINISTIC DECISION ENGINE                             WEBSOCKET HUB
      (Multi-Factor Optimization & Audit)                      (Real-Time Telemetry)
                  │
                  ▼
        OPERATIONAL DATABASE (SQLite / Fabric SQL DB)
                  │
                  ▼
        MICROSOFT FABRIC EVENTSTREAM (Azure EventHub Producer)
                  │
                  ▼
        FABRIC EVENTHOUSE (KQL Real-Time Database)
                  │
        ┌─────────┴─────────────────────────────┐
        ▼                                       ▼
  FABRIC ACTIVATOR                      ONELAKE / LAKEHOUSE
 (Autonomous Alert Rules)                       │
        │                                       ▼
        ▼                               BRONZE LAYER (raw_*)
  EMERGENCY ALERTS                              │
 (Teams / SMS / Escalation)                     ▼
                                        SILVER LAYER (clean_* & quarantine_records)
                                                │
                                                ▼
                                        GOLD LAYER (gold_* aggregates)
                                                │
                                                ▼
                                        CRISISMODEL SEMANTIC MODEL
                                                │
                                                ▼
                                        POWER BI EXECUTIVE DASHBOARD
```

---

## 2. End-to-End Data Flow

1. **Detection & Ingestion**: Incident reported via UI or external sensor $\rightarrow$ Ingested by FastAPI `/api/incidents` or `/api/simulation/run`.
2. **Decision Engine & Multi-Factor Scoring**: Evaluates candidate ambulances, fire units, and receiving hospitals considering distance, traffic delays, vehicle equipment match, and hospital specialty care.
3. **Explainability & Decision Audit**: Generates structured human-readable rationale and persists complete score breakdown in `DecisionAudit` table.
4. **Real-Time Eventstream Ingestion**: Publishes standard business event envelope (`EVT-XXXX`) to Microsoft Fabric Eventstream / Azure EventHub without blocking core dispatch.
5. **Real-Time Telemetry & Activator Alerts**: Eventhouse KQL database receives streams; Fabric Activator triggers automated alarms on critical conditions.
6. **Medallion Data Engineering Pipeline**:
   - **Bronze**: Raw events landing in Delta format.
   - **Silver Notebook (`01_bronze_to_silver.py`)**: Schema validation, deduplication, timestamp & Hyderabad coordinate bounding box sanitization, quarantine routing.
   - **Gold Notebook (`02_silver_to_gold.py`)**: Computes analytical metrics (P50/P90 response times, SLA compliance, zone strain, fleet utilization, decision quality).
7. **Semantic Model & Power BI Reporting**: DirectLake `CrisisModel` Semantic Model feeds the 3-page Power BI dashboard.

---

## 3. Database Entities & Schemas

- **`Incident`**: `id`, `incident_type`, `location`, `zone`, `latitude`, `longitude`, `floor`, `building`, `severity`, `people_at_risk`, `description`, `status`, `spread_risk`, `created_at`, `updated_at`.
- **`Ambulance`**: `id`, `resource_code`, `resource_type`, `call_sign`, `location`, `zone`, `latitude`, `longitude`, `status`, `equipment`, `capacity`, `current_incident_id`, `updated_at`.
- **`FireStation` & `FireTruck`**: Station bases, equipment inventory, truck availability, real-time GPS locations.
- **`Hospital`**: `id`, `name`, `location`, `zone`, `latitude`, `longitude`, `total_beds`, `available_beds`, `emergency_capacity`, `icu_beds`, `trauma_beds`, `burn_capacity`, `specialties`, `occupancy`, `status`.
- **`Dispatch`**: `id`, `incident_id`, `resource_id`, `hospital_id`, `route`, `eta_minutes`, `distance_km`, `confidence`, `status`, `assigned_at`, `completed_at`.
- **`Recommendation`**: `id`, `incident_id`, `resource_id`, `hospital_id`, `route`, `eta_minutes`, `score`, `confidence`, `algorithm`, `reasons`, `score_breakdown`.
- **`DecisionAudit`**: `id`, `incident_id`, `candidate_resources`, `candidate_hospitals`, `rejected_candidates`, `selected_resource`, `selected_hospital`, `score_breakdown`, `confidence`, `algorithm`, `reason`, `human_override`, `final_decision`.
- **`Alert`**: `id`, `alert_type`, `severity`, `message`, `zone`, `entity_id`, `acknowledged`.
- **`RoadBlock` & `WeatherEvent`**: Real-time traffic blockages and precipitation telemetry.

---

## 4. Standard Event Envelope

All events emitted to Microsoft Fabric follow the uniform envelope:

```json
{
  "event_id": "EVT-78a5b090c10c",
  "event_type": "incident.created",
  "timestamp": "2026-08-22T06:55:00.000000Z",
  "source": "crisisflow-api",
  "entity_id": "INC-2451",
  "zone": "Gachibowli",
  "payload": {
    "incident_id": "INC-2451",
    "incident_type": "Road Accident",
    "location": "Gachibowli Junction",
    "severity": "Critical",
    "people_at_risk": 12
  }
}
```

Supported business events: `incident.created`, `incident.updated`, `dispatch.created`, `dispatch.completed`, `resource.status_changed`, `hospital.capacity_changed`, `weather.updated`, `road.blocked`, `resource.shortage`, `decision.created`, `alert.created`, `simulation.started`, `simulation.completed`.

---

## 5. Simulation Scenarios & Demo Presentation

CrisisFlow includes 6 deterministic scenarios accessible via `POST /api/simulation/run`:

1. **MAJOR ACCIDENT** (Gachibowli): 6 vehicles, 12 casualties, heavy traffic, critical trauma prioritization.
2. **BUILDING FIRE** (HITEC City): Floor 7 high-rise commercial fire, 85 people at risk, multi-alarm fire & ambulance dispatch.
3. **FLASH FLOOD** (Madhapur): 78 mm/hr intense rainfall, 0.65m standing water, autonomous road blocking & flood alerts.
4. **MEDICAL EMERGENCY** (Banjara Hills): Cardiac arrest, priority matching to Cardiology specialty hospitals.
5. **INDUSTRIAL ACCIDENT** (Jeedimetla): Chemical reactor breach, 18 casualties, hazmat and burn/trauma triage.
6. **RESOURCE EXHAUSTION**: Simulates fleet depletion (0 ambulances idle) $\rightarrow$ Activates inter-zone repositioning engine and emits `resource.shortage` alert.

### ⏱️ Recommended 3-Minute Hackathon Demo Script
- **0:00 - 0:20**: Architecture Overview (FastAPI $\rightarrow$ Decision Engine $\rightarrow$ Fabric Eventstream $\rightarrow$ Lakehouse Medallion $\rightarrow$ Power BI).
- **0:20 - 0:50**: Launch **Major Accident** scenario; show instant incident detection and multi-factor resource scoring.
- **0:50 - 1:20**: Show Explainability & Decision Audit (Candidate evaluation, rejected units with reasons, score breakdown).
- **1:20 - 1:50**: Demonstrate **Resource Exhaustion** scenario and automated `resource.shortage` alert.
- **1:50 - 2:20**: Walk through Lakehouse Medallion layer (Bronze raw events $\rightarrow$ Silver clean/quarantine $\rightarrow$ Gold aggregates).
- **2:20 - 2:45**: Showcase Power BI 3-Page Executive Dashboard (Response Performance, Resource Intelligence, Decision Quality).
- **2:45 - 3:00**: Highlight Fabric Activator automated alert rules and resilience guarantees.

---

## 6. Lakehouse Medallion Architecture

- **Bronze**: `raw_incidents`, `raw_resources`, `raw_hospitals`, `raw_dispatches`, `raw_decisions`, `raw_alerts`, `raw_weather`, `raw_road_events`.
- **Silver (`01_bronze_to_silver.py`)**: `clean_incidents`, `clean_resources`, `clean_hospitals`, `clean_dispatches`, `clean_decisions`, `clean_weather`, and `quarantine_records`.
- **Gold (`02_silver_to_gold.py`)**:
  - `gold_response_performance`: Avg, P50, P90 response times, SLA compliance (<8 min target).
  - `gold_zone_demand`: Hourly incident volume, critical severity counts, zone strain index.
  - `gold_resource_utilisation`: Fleet utilization %, active vs idle ready units.
  - `gold_decision_quality`: Optimizer confidence %, human override rate %, solve time.
  - `gold_incident_trends`: 24-hour and 7-day rolling incident velocity.

---

## 7. Power BI 3-Page Executive Report

1. **Page 1: Response Performance**: Active/critical KPIs, Response time by zone column chart, Severity donut, SLA trend line.
2. **Page 2: Resource Intelligence**: Fleet utilization bars, Hospital capacity matrix, Resource availability by zone treemap.
3. **Page 3: Decision Quality**: Optimizer confidence vs ETA scatter, Human override rate by severity, Interactive Decision Audit Explorer.

---

## 8. Fabric Activator Alert Rules

1. **Rule 1 (Critical Incident)**: `severity == "Critical"` $\rightarrow$ Emergency Commander Alert.
2. **Rule 2 (Resource Shortage)**: `available_ambulances < 2` $\rightarrow$ Repositioning Trigger.
3. **Rule 3 (Hospital Capacity)**: `available_beds < 10` or `occupancy > 0.90` $\rightarrow$ Ambulance Reroute Alert.
4. **Rule 4 (Flood Hazard)**: `flood_depth_m > 0.50` $\rightarrow$ Road Block & Evacuation Advisory.
5. **Rule 5 (SLA Escalation)**: `eta_minutes > 12.0` $\rightarrow$ Commander Escalation Banner.

---

## 9. Quick Start & Local Execution

### Backend Setup

```powershell
cd backend
pip install "sqlalchemy>=2.0" python-dotenv "websockets>=12.0" aiosqlite pytest azure-eventhub azure-identity
python seed.py
uvicorn main:app --reload --port 8000
```

- API Docs: `http://localhost:8000/docs`
- Health: `http://localhost:8000/api/health`
- Fabric Status: `http://localhost:8000/api/fabric/status`

### Frontend Setup

```powershell
cd frontend
npm install
npm run dev
```

- UI Command Center: `http://localhost:5173`

### Run Verification & Test Suites

```powershell
# Run backend pytest suite (18 automated tests)
pytest backend/tests/test_backend.py -v

# Run 20-step End-to-End verification audit
python backend/tests/verify_e2e.py
```
