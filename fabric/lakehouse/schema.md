# CrisisFlow — Lakehouse Schema
# ═══════════════════════════════
# Delta tables for historical analytics in Fabric Lakehouse

## Fact Tables

### FactIncidents
| Column | Type | Description |
|--------|------|-------------|
| incident_id | string | Primary key |
| incident_type | string | Building Fire, Road Accident, etc. |
| location | string | Location name |
| latitude | double | GPS latitude |
| longitude | double | GPS longitude |
| severity | string | Low, Medium, High, Critical |
| people_at_risk | int | Estimated persons at risk |
| status | string | Current status |
| spread_risk | string | Fire spread risk level |
| created_at | timestamp | Incident detection time |
| resolved_at | timestamp | Resolution time (nullable) |

### FactDispatches
| Column | Type | Description |
|--------|------|-------------|
| dispatch_id | string | Primary key |
| incident_id | string | FK to FactIncidents |
| fire_station_id | string | Assigned fire station |
| ambulance_id | string | Assigned ambulance |
| hospital_id | string | Target hospital |
| route | string | Selected route |
| eta_minutes | double | Estimated response time |
| confidence | double | Decision confidence % |
| dispatched_at | timestamp | Dispatch time |

### FactResourceEvents
| Column | Type | Description |
|--------|------|-------------|
| event_id | string | Primary key |
| resource_type | string | ambulance, fire_truck, fire_station |
| resource_id | string | Resource identifier |
| status | string | Available, En Route, etc. |
| incident_id | string | Associated incident (nullable) |
| timestamp | timestamp | Event time |

### FactResponseTimes
| Column | Type | Description |
|--------|------|-------------|
| incident_id | string | FK |
| dispatch_time | timestamp | When dispatched |
| arrival_time | timestamp | When arrived on scene |
| resolution_time | timestamp | When resolved |
| response_minutes | double | Total response time |

### FactHospitalEvents
Similar to HospitalEvents in Eventhouse.

## Dimension Tables

### DimDate
Standard date dimension with year, month, day, hour, day_of_week.

### DimLocation
| Column | Type |
|--------|------|
| location_id | string |
| name | string |
| latitude | double |
| longitude | double |
| zone | string |
| city | string |

### DimIncidentType
| Column | Type |
|--------|------|
| type_id | string |
| name | string |
| category | string |
| default_severity | string |

### DimResource
| Column | Type |
|--------|------|
| resource_id | string |
| type | string |
| name | string |
| station_id | string |
| equipment | array<string> |

### DimHospital
| Column | Type |
|--------|------|
| hospital_id | string |
| name | string |
| location | string |
| emergency_capacity | int |
| specializations | array<string> |
