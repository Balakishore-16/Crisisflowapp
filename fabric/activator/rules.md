# CrisisFlow — Fabric Activator Automated Alert Rules
═════════════════════════════════════════════════════
Configure these operational trigger rules in Microsoft Fabric Activator
connected to your Eventhouse KQL Database to drive autonomous emergency actions.

```
                      FABRIC REAL-TIME INTELLIGENCE
┌────────────────────────────────────────────────────────────────────────┐
│                                                                        │
│   Eventstream (Kafka / EventHub)                                       │
│          │                                                             │
│          v                                                             │
│   Eventhouse KQL Tables (Incidents, ResourceEvents, Weather, Dispatches)│
│          │                                                             │
│          v                                                             │
│   Fabric Activator Rule Engine                                         │
│          │                                                             │
│     ┌────┴────────────┬────────────────┬───────────────┬────────────┐  │
│     v                 v                v               v            v  │
│   Rule 1            Rule 2           Rule 3          Rule 4       Rule 5
│  (Critical)       (Shortage)       (Capacity)       (Flood)      (SLA) │
│     │                 │                │               │            │  │
│     v                 v                v               v            v  │
│   Emergency        Commander        Hospital        Evacuation   Supervisor
│   Broadcast         Alert           Re-Route         Trigger      Escalate │
└────────────────────────────────────────────────────────────────────────┘
```

---

## Rule 1: Critical Incident Alert
- **Description**: Triggers immediate high-priority alert when a Critical incident is logged.
- **Source**: Eventhouse $\rightarrow$ `Incidents` table
- **KQL Query**:
  ```kusto
  Incidents
  | where timestamp > ago(5m)
  | where severity == "Critical" and status == "Detected"
  | project incident_id, incident_type, location, zone, people_at_risk, timestamp
  ```
- **Action**: Emit `critical.incident` alert $\rightarrow$ Teams Notification to Emergency Commander $\rightarrow$ Trigger siren broadcast.
- **Message**: `🚨 CRITICAL INCIDENT: {incident_type} at {location} ({zone}) with {people_at_risk} people at risk.`

---

## Rule 2: Resource Shortage Alert
- **Description**: Detects when fleet capacity drops below safe operating threshold in any zone.
- **Source**: Eventhouse $\rightarrow$ `ResourceEvents` table
- **KQL Query**:
  ```kusto
  ResourceEvents
  | where timestamp > ago(10m)
  | summarize arg_max(timestamp, *) by resource_id
  | where resource_type == "Ambulance" and status == "Available"
  | summarize available_count = count()
  | where available_count < 2
  ```
- **Action**: Emit `resource.shortage` alert $\rightarrow$ Trigger inter-zone vehicle repositioning recommendation.
- **Message**: `⚠️ RESOURCE SHORTAGE: Critical ambulance shortage — only {available_count} unit(s) idle across the city.`

---

## Rule 3: Hospital Capacity Alert
- **Description**: Warns dispatchers when critical trauma/ICU bed capacity at receiving hospitals is depleted.
- **Source**: Eventhouse $\rightarrow$ `HospitalEvents` table
- **KQL Query**:
  ```kusto
  HospitalEvents
  | where timestamp > ago(10m)
  | summarize arg_max(timestamp, *) by hospital_id
  | where available_beds < 10 or occupancy > 0.90
  | project hospital_id, hospital_name, available_beds, occupancy, timestamp
  ```
- **Action**: Emit `hospital.capacity` alert $\rightarrow$ Reroute inbound ambulances to secondary trauma centers.
- **Message**: `🏥 HOSPITAL CAPACITY ALERT: {hospital_name} has only {available_beds} beds remaining ({occupancy * 100}% occupancy).`

---

## Rule 4: Flood Risk Alert
- **Description**: Detects telemetry indicating hazardous urban water levels exceeding safe navigation thresholds.
- **Source**: Eventhouse $\rightarrow$ `WeatherEvents` table
- **KQL Query**:
  ```kusto
  WeatherEvents
  | where timestamp > ago(15m)
  | where flood_depth_m > 0.50 or rainfall_mm_hr > 70.0
  | project location, zone, flood_depth_m, rainfall_mm_hr, timestamp
  ```
- **Action**: Emit `flood.risk` alert $\rightarrow$ Autonomous route blocking in dispatch engine $\rightarrow$ Evacuation advisory.
- **Message**: `🌊 FLOOD HAZARD: Water level {flood_depth_m}m in {zone} ({location}). Routes compromised.`

---

## Rule 5: Response Escalation SLA Alert
- **Description**: Escalates dispatches where traffic or routing delays threaten response time targets.
- **Source**: Eventhouse $\rightarrow$ `DispatchEvents` table
- **KQL Query**:
  ```kusto
  DispatchEvents
  | where timestamp > ago(30m)
  | where eta_minutes > 12.0 and status in ("Dispatched", "En Route")
  | project dispatch_id, incident_id, ambulance_id, eta_minutes, timestamp
  ```
- **Action**: Emit `response.escalation` alert $\rightarrow$ Commander dashboard escalation banner.
- **Message**: `⏰ SLA ESCALATION: Dispatch {dispatch_id} for Incident {incident_id} ETA is {eta_minutes} min (Target SLA: 8.0 min).`
