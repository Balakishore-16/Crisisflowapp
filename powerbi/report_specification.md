# CrisisFlow — Power BI Report Specification
# ════════════════════════════════════════════
# Connect Power BI to the Fabric Lakehouse/Eventhouse semantic model.

## Data Source
- **Real-time**: Fabric Eventhouse KQL Database (DirectQuery for near-real-time)
- **Historical**: Fabric Lakehouse (Import/DirectQuery)

## Semantic Model
Create a semantic model in Fabric with relationships:
- FactIncidents → DimDate (created_at → date_key)
- FactIncidents → DimLocation (location → location_id)
- FactIncidents → DimIncidentType (incident_type → type_id)
- FactDispatches → FactIncidents (incident_id)
- FactDispatches → DimResource (fire_station_id, ambulance_id)
- FactDispatches → DimHospital (hospital_id)

## Report Pages

### Page 1: Emergency Overview
**KPIs:**
- Total Incidents (card)
- Critical Incidents (card, red)
- Average Response Time (card)
- Active Incidents (card)
- Resolved Rate (card, %)

**Visuals:**
- Incidents over time (line chart, by day/hour)
- Current status breakdown (donut chart)

### Page 2: Incident Intelligence
- Incidents by type (bar chart)
- Severity distribution (pie chart)
- Incidents over time by severity (stacked area)
- Geographic incident map (filled map or ArcGIS)
- Top locations by incident count (table)

### Page 3: Resource Intelligence
- Ambulance utilization (gauge)
- Fire truck utilization (gauge)
- Resource availability over time (line chart)
- Average response time by resource (bar chart)
- Resources by status (stacked bar)

### Page 4: Hospital Intelligence
- Hospital occupancy (bar chart, conditional formatting)
- ICU capacity by hospital (bar chart)
- Trauma capacity (bar chart)
- Burn capacity (bar chart)
- Hospital status distribution (donut)

### Page 5: Risk Intelligence
- Risk zones map (filled map with risk score)
- Risk score trend (line chart)
- High risk zones list (table)
- Incident density heatmap
- Contributing factors (matrix)

### Page 6: Response Performance
- Response time trend (line chart)
- Response time by incident type (bar)
- SLA compliance rate (KPI card)
- Dispatch-to-arrival time distribution (histogram)
- Resolution time trend (line chart)

## DAX Measures (Key)
```dax
Active Incidents = CALCULATE(COUNT(FactIncidents[incident_id]),
    FactIncidents[status] IN {"Detected","Analyzing","Awaiting Response","Dispatched","Response In Progress"})

Avg Response Time = AVERAGE(FactDispatches[eta_minutes])

Resolution Rate = DIVIDE(
    CALCULATE(COUNT(FactIncidents[incident_id]), FactIncidents[status] = "Resolved"),
    COUNT(FactIncidents[incident_id]))

Critical Rate = DIVIDE(
    CALCULATE(COUNT(FactIncidents[incident_id]), FactIncidents[severity] = "Critical"),
    COUNT(FactIncidents[incident_id]))
```
