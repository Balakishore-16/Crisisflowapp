# CrisisFlow — Microsoft Fabric Medallion Lakehouse Architecture
═══════════════════════════════════════════════════════════════════
Delta Lake medallion architecture in Microsoft Fabric OneLake / Lakehouse.

```
                  MICROSOFT FABRIC ONELAKE / LAKEHOUSE
┌────────────────────────────────────────────────────────────────────────┐
│                                                                        │
│   BRONZE (Raw Ingestion)       SILVER (Cleaned & Curated)      GOLD (Business Analytics) │
│  ┌───────────────────────┐    ┌─────────────────────────┐    ┌─────────────────────────┐ │
│  │ raw_incidents         │    │ clean_incidents         │    │ gold_response_perf      │ │
│  │ raw_resources         │───>│ clean_resources         │───>│ gold_zone_demand        │ │
│  │ raw_hospitals         │    │ clean_hospitals         │    │ gold_resource_util      │ │
│  │ raw_dispatches        │    │ clean_dispatches        │    │ gold_decision_quality   │ │
│  │ raw_decisions         │    │ clean_decisions         │    │ gold_incident_trends    │ │
│  │ raw_alerts            │    │ clean_weather           │    └─────────────────────────┘ │
│  │ raw_weather           │    │                         │                 │              │
│  │ raw_road_events       │    │ quarantine_records      │                 v              │
│  └───────────────────────┘    └─────────────────────────┘          Power BI Semantic     │
│                                                                         Model            │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 1. Bronze Layer (Raw Streaming & Batch Ingestion)
Populated continuously by Fabric Eventstream and scheduled Fabric SQL replication.

| Table Name | Source | Description | Format |
|------------|--------|-------------|--------|
| `raw_incidents` | Eventstream / DB | Raw incident creation and status mutation JSON events | Delta Table |
| `raw_resources` | Eventstream / DB | Telemetry from ambulances, fire trucks, and stations | Delta Table |
| `raw_hospitals` | Eventstream / DB | Real-time hospital capacity and occupancy snapshots | Delta Table |
| `raw_dispatches` | Eventstream / DB | Raw resource dispatch and unit deployment events | Delta Table |
| `raw_decisions` | Eventstream / DB | Decision Engine recommendation and audit records | Delta Table |
| `raw_alerts` | Eventstream / DB | System and Activator operational alert triggers | Delta Table |
| `raw_weather` | Weather Service | IoT weather station sensor telemetry (rain, wind, flood) | Delta Table |
| `raw_road_events`| Traffic Service | Road blocks, construction, and congestion telemetry | Delta Table |

---

## 2. Silver Layer (Cleaned, Validated, Deduplicated & Enriched)
Processed by Fabric Notebook `01_bronze_to_silver.py`. Guaranteed idempotent via Delta MERGE.

### `clean_incidents`
| Column | Type | Nullable | Constraints / Description |
|--------|------|----------|---------------------------|
| `incident_id` | STRING | No | Primary Key (`INC-XXXX`) |
| `incident_type` | STRING | No | Building Fire, Road Accident, Medical Emergency, Flood, Industrial Accident |
| `location` | STRING | No | Canonical street / building name |
| `zone` | STRING | No | Normalized Zone (HITEC City, Gachibowli, Madhapur, etc.) |
| `latitude` | DOUBLE | No | GPS Latitude (Hyderabad bounds: 17.20 - 17.65) |
| `longitude` | DOUBLE | No | GPS Longitude (Hyderabad bounds: 78.20 - 78.70) |
| `floor` | INT | Yes | Floor number for multi-story buildings |
| `building` | STRING | Yes | Building identifier |
| `severity` | STRING | No | Normalized: `Critical`, `High`, `Medium`, `Low` |
| `people_at_risk` | INT | No | Non-negative integer |
| `description` | STRING | Yes | Incident description |
| `status` | STRING | No | Normalized: `Detected`, `Analyzing`, `Awaiting Response`, `Dispatched`, `Response In Progress`, `Resolved` |
| `spread_risk` | STRING | Yes | `High`, `Medium`, `Low` |
| `is_simulated` | BOOLEAN | No | Synthetic simulation marker |
| `created_at` | TIMESTAMP | No | Normalized UTC timestamp |
| `updated_at` | TIMESTAMP | No | Normalized UTC timestamp |
| `ingested_at` | TIMESTAMP | No | Silver pipeline processing timestamp |

### `clean_resources`
| Column | Type | Description |
|--------|------|-------------|
| `resource_id` | STRING | Primary Key (`A-XX`, `FT-XX`, `FS-XX`) |
| `resource_code` | STRING | Operational call sign code |
| `resource_type` | STRING | `Ambulance`, `FireTruck`, `FireStation` |
| `call_sign` | STRING | Radio call sign |
| `location` | STRING | Current base location |
| `zone` | STRING | Operating zone |
| `latitude` | DOUBLE | Current GPS latitude |
| `longitude` | DOUBLE | Current GPS longitude |
| `status` | STRING | Normalized: `Available`, `En Route`, `On Scene`, `Transporting`, `Maintenance` |
| `equipment` | ARRAY<STRING> | Standardized equipment array |
| `capacity` | INT | Patient / personnel capacity |
| `current_incident_id` | STRING | FK to `clean_incidents` (nullable) |
| `updated_at` | TIMESTAMP | Last location/status ping |

### `clean_hospitals`
| Column | Type | Description |
|--------|------|-------------|
| `hospital_id` | STRING | Primary Key (`H-XX`) |
| `name` | STRING | Hospital name |
| `location` | STRING | Facility location |
| `zone` | STRING | Geographic zone |
| `latitude` | DOUBLE | GPS latitude |
| `longitude` | DOUBLE | GPS longitude |
| `total_beds` | INT | Total bed capacity |
| `available_beds` | INT | Available unoccupied beds |
| `emergency_capacity` | INT | ER bay capacity |
| `icu_beds` | INT | Intensive Care Unit bed count |
| `trauma_beds` | INT | Dedicated trauma surgery beds |
| `burn_capacity` | INT | Specialized burn unit capacity |
| `specialties` | ARRAY<STRING> | Cardiology, Trauma, Burn Care, Neurology, etc. |
| `occupancy` | DOUBLE | Real-time occupancy ratio (0.00 - 1.00) |
| `status` | STRING | `Available`, `Busy`, `Full`, `Emergency Only` |
| `updated_at` | TIMESTAMP | Telemetry update timestamp |

### `clean_dispatches`
| Column | Type | Description |
|--------|------|-------------|
| `dispatch_id` | STRING | Primary Key (`DSP-XXXX`) |
| `incident_id` | STRING | FK to `clean_incidents` |
| `resource_id` | STRING | FK to `clean_resources` |
| `ambulance_id` | STRING | Assigned ambulance identifier |
| `fire_truck_id` | STRING | Assigned fire truck identifier |
| `fire_station_id` | STRING | Assigned fire station |
| `hospital_id` | STRING | Destination hospital FK |
| `route` | STRING | Selected navigation corridor |
| `eta_minutes` | DOUBLE | Estimated response time in minutes |
| `distance_km` | DOUBLE | Travel distance in km |
| `confidence` | DOUBLE | Decision engine confidence score |
| `status` | STRING | `Dispatched`, `En Route`, `On Scene`, `Completed` |
| `human_override` | BOOLEAN | Indicates commander manual intervention |
| `assigned_at` | TIMESTAMP | Dispatch order timestamp |
| `completed_at` | TIMESTAMP | Mission completion timestamp |

### `clean_decisions`
| Column | Type | Description |
|--------|------|-------------|
| `audit_id` | STRING | Primary Key (`AUD-XXXX`) |
| `incident_id` | STRING | Associated incident |
| `candidate_count` | INT | Total candidate resources evaluated |
| `rejected_count` | INT | Candidates disqualified with reasons |
| `selected_ambulance`| STRING | Selected ambulance ID |
| `selected_hospital` | STRING | Selected hospital ID |
| `score` | DOUBLE | Composite optimization score (0-100) |
| `confidence` | DOUBLE | Confidence percentage (0-100) |
| `eta_minutes` | DOUBLE | Estimated response duration |
| `distance_score` | DOUBLE | Proximity sub-score |
| `traffic_score` | DOUBLE | Traffic sub-score |
| `equipment_score` | DOUBLE | Equipment matching sub-score |
| `capacity_score` | DOUBLE | Hospital capacity sub-score |
| `algorithm` | STRING | Decision engine version |
| `human_override` | BOOLEAN | True if operator overrode decision |
| `created_at` | TIMESTAMP | Recommendation timestamp |

### `quarantine_records`
| Column | Type | Description |
|--------|------|-------------|
| `quarantine_id` | STRING | Primary Key |
| `source_table` | STRING | Origin raw table |
| `record_payload` | STRING | Raw JSON payload |
| `failure_reason` | STRING | Validation failure reason (e.g., missing required fields, invalid coordinates) |
| `quarantined_at` | TIMESTAMP | Pipeline timestamp |

---

## 3. Gold Layer (Business & Executive Analytics)
Aggregated by Fabric Notebook `02_silver_to_gold.py`. Directly fuels the **CrisisModel Semantic Model** and **Power BI Dashboards**.

### `gold_response_performance`
- **Grain**: Zone, Incident Type, Severity, Time Band (Hour)
- **Metrics**:
  - `avg_response_time_min`: Average ETA / response time
  - `p50_response_time_min`: 50th percentile (median) response time
  - `p90_response_time_min`: 90th percentile response time
  - `sla_target_min`: SLA benchmark (8.0 min for Critical, 12.0 min for High)
  - `sla_compliance_rate`: % of dispatches meeting SLA
  - `total_dispatches`: Dispatch count

### `gold_zone_demand`
- **Grain**: Zone, Incident Type, Severity, Date
- **Metrics**:
  - `incident_count`: Incident volume
  - `critical_incident_count`: Critical severity count
  - `total_casualties`: Casualties / people at risk
  - `peak_demand_hour`: Peak surge hour
  - `demand_index`: Composite zone strain index (0 - 100)

### `gold_resource_utilisation`
- **Grain**: Resource Type, Zone, Date
- **Metrics**:
  - `total_fleet_units`: Fleet size
  - `active_units`: Units deployed or en route
  - `idle_available_units`: Idle ready units
  - `fleet_utilization_pct`: Active / Total fleet %
  - `shortage_event_count`: Resource exhaustion incident count

### `gold_decision_quality`
- **Grain**: Date, Algorithm Version, Severity
- **Metrics**:
  - `avg_optimizer_confidence`: Average optimization confidence %
  - `human_override_rate_pct`: Operator override frequency %
  - `avg_solve_time_ms`: Decision engine compute duration
  - `eta_accuracy_pct`: Forecast ETA vs actual arrival accuracy
  - `decision_count`: Total automated decisions made

### `gold_incident_trends`
- **Grain**: Date, Zone, Incident Type
- **Metrics**:
  - `rolling_24h_incidents`: 24-hour rolling velocity
  - `rolling_7d_incidents`: 7-day rolling volume
  - `resolution_rate_pct`: % of incidents resolved within 60 mins
