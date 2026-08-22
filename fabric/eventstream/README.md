# CrisisFlow — Eventstream Configuration
# ════════════════════════════════════════
# This document describes the Fabric Eventstream setup for CrisisFlow.

## Architecture

```
CrisisFlow Backend (FastAPI)
         │
         ▼
  Azure Event Hub / Custom App Source
         │
         ▼
  Fabric Eventstream
         │
    ┌────┴────┐
    ▼         ▼
Eventhouse  Lakehouse
(KQL DB)   (Delta/Parquet)
```

## Setup Steps

### 1. Create Eventstream
- Go to your Fabric Workspace
- Create new Eventstream: `crisisflow-events`
- Add Custom App source (Event Hub compatible)
- Copy the connection string and event hub name

### 2. Configure Backend
Set these environment variables:
```
FABRIC_EVENTHUB_CONNECTION_STRING=<from Eventstream custom app>
FABRIC_EVENTHUB_NAME=<from Eventstream>
```

### 3. Add Destinations

#### Eventhouse (Real-Time)
- Add Eventhouse destination
- Target KQL Database: `crisisflow-kql`
- Map incoming JSON fields to KQL table columns
- Enable real-time ingestion

#### Lakehouse (Historical)
- Add Lakehouse destination
- Target: `crisisflow-lakehouse`
- Format: Delta
- Partitioning: by event_type and date

### 4. Event Schema

All CrisisFlow events follow this schema:
```json
{
  "event_type": "INCIDENT_CREATED | INCIDENT_ANALYZED | RECOMMENDATION_GENERATED | DISPATCH_CREATED | RESOURCE_UPDATED | HOSPITAL_UPDATED",
  "timestamp": "ISO 8601",
  "source": "CrisisFlow",
  "incident_id": "string",
  "...additional fields per event type"
}
```

### 5. Transformations (optional)
- Add computed column: `severity_score` (Critical=4, High=3, Medium=2, Low=1)
- Add computed column: `event_date` from timestamp
- Filter out heartbeat/ping events
