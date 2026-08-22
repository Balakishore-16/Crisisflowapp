# CrisisFlow — Fabric Semantic Model (`CrisisModel`)
═════════════════════════════════════════════════════
DirectLake / DirectQuery Semantic Model definition for Microsoft Fabric Power BI.

## 1. Model Architecture & Star Schema
The Semantic Model connects Gold layer Delta tables to conformed Dimension tables.

```
       ┌─────────────────┐       ┌─────────────────┐
       │     DimDate     │       │   DimLocation   │
       └────────┬────────┘       └────────┬────────┘
                │                         │
                v                         v
   ┌───────────────────────────────────────────┐
   │        gold_response_performance          │
   └────────────────────┬──────────────────────┘
                        │
       ┌────────────────┼────────────────┐
       v                v                v
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│  DimResource │ │ DimHospital  │ │ DimSeverity  │
└──────────────┘ └──────────────┘ └──────────────┘
```

---

## 2. Core DAX Measures

### Response Performance Measures
```dax
Avg Response Time = 
AVERAGE(gold_response_performance[avg_response_time_min])

P50 Response Time = 
MEDIAN(gold_response_performance[p50_response_time_min])

P90 Response Time = 
PERCENTILE.INC(gold_response_performance[p90_response_time_min], 0.90)

SLA Compliance Rate = 
DIVIDE(
    CALCULATE(SUM(gold_response_performance[total_dispatches]), gold_response_performance[sla_compliance_pct] = 100),
    SUM(gold_response_performance[total_dispatches]),
    0
)
```

### Volume & Severity Measures
```dax
Total Incidents = 
SUM(gold_zone_demand[incident_count])

Active Incidents = 
CALCULATE(
    COUNT(clean_incidents[incident_id]),
    clean_incidents[status] IN {"Detected", "Analyzing", "Awaiting Response", "Dispatched", "Response In Progress"}
)

Critical Incidents = 
SUM(gold_zone_demand[critical_incidents])

Critical Incident Rate = 
DIVIDE([Critical Incidents], [Total Incidents], 0)
```

### Resource Intelligence Measures
```dax
Ambulance Utilization = 
AVERAGE(gold_resource_utilisation[avg_mission_eta_min])

Available Ambulances = 
CALCULATE(
    COUNT(clean_resources[resource_id]),
    clean_resources[resource_type] = "Ambulance",
    clean_resources[status] = "Available"
)

Available Fire Units = 
CALCULATE(
    COUNT(clean_resources[resource_id]),
    clean_resources[resource_type] = "FireTruck",
    clean_resources[status] = "Available"
)

Hospital Available Beds = 
SUM(clean_hospitals[available_beds])

Avg Hospital Occupancy = 
AVERAGE(clean_hospitals[occupancy])
```

### Decision Quality Measures
```dax
Optimizer Confidence = 
AVERAGE(gold_decision_quality[avg_optimizer_confidence_pct])

Human Override Rate = 
AVERAGE(gold_decision_quality[human_override_rate_pct])

ETA Forecast Accuracy = 
100 - ABS(AVERAGE(gold_decision_quality[predicted_eta_avg]) - [Avg Response Time])

Total Automated Decisions = 
SUM(gold_decision_quality[decision_count])
```
