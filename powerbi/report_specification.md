# CrisisFlow — Power BI Executive Emergency Report Specification
════════════════════════════════════════════════════════════════════
Microsoft Fabric Power BI 3-Page Executive Report powered by the `CrisisModel` Semantic Model.

---

## Page 1: Response Performance

### Executive KPI Header Cards
1. **Active Incidents**: Card visual | Source: `[Active Incidents]` | Target: Real-time count
2. **Critical Incidents**: Card visual with red indicator | Source: `[Critical Incidents]`
3. **Average Response Time**: Card visual | Source: `[Avg Response Time]` | Format: `0.0 min`
4. **SLA Compliance Rate**: Card visual with conditional formatting | Source: `[SLA Compliance Rate]` | Target: > 90%
5. **Available Ambulances**: Card visual | Source: `[Available Ambulances]` | Indicator: Green (>3), Yellow (1-2), Red (0)

### Visual Layout
- **Visual 1 (Top Left - Column Chart)**: *Response Time by Zone*
  - X-axis: `zone` (HITEC City, Gachibowli, Madhapur, Banjara Hills, etc.)
  - Y-axis: `[Avg Response Time]`
  - Reference Line: 8.0 min SLA Benchmark
- **Visual 2 (Top Right - Donut Chart)**: *Incidents by Severity*
  - Legend: `severity` (Critical, High, Medium, Low)
  - Values: `[Total Incidents]`
  - Palette: Red (#EF4444), Orange (#F97316), Yellow (#EAB308), Blue (#3B82F6)
- **Visual 3 (Bottom Left - Line & Area Chart)**: *24-Hour Incident Volume & Response Trend*
  - X-axis: `hour_of_day`
  - Values: `[Total Incidents]`, `[Avg Response Time]`
- **Visual 4 (Bottom Right - Gauge / Matrix)**: *SLA Compliance by Zone & Severity*
  - Rows: `zone`
  - Columns: `severity`
  - Values: `[SLA Compliance Rate]`

---

## Page 2: Resource Intelligence

### Executive KPI Header Cards
1. **Fleet Utilization Rate**: `[Ambulance Utilization]`
2. **Active Dispatches**: `SUM(gold_response_performance[total_dispatches])`
3. **Hospital Beds Available**: `[Hospital Available Beds]`
4. **Avg Hospital Occupancy**: `[Avg Hospital Occupancy]`
5. **Resource Shortage Events**: `COUNT(Alerts[resource.shortage])`

### Visual Layout
- **Visual 1 (Left Half - Horizontal Bar Chart)**: *Ambulance Fleet Status & Utilization*
  - Y-axis: `resource_id` / `call_sign`
  - X-axis: `mission_count` & `total_operational_minutes`
  - Color: Categorized by status (Available, En Route, Transporting)
- **Visual 2 (Top Right - Clustered Bar Chart)**: *Hospital Capacity & Occupancy Matrix*
  - Y-axis: `hospital_name`
  - X-axis: `available_beds`, `icu_beds`, `trauma_beds`, `burn_capacity`
  - Tooltips: Specialty care matching
- **Visual 3 (Bottom Right - Treemap / Matrix)**: *Resource Distribution by Operating Zone*
  - Category: `zone`
  - Size: `[Total Incidents]`
  - Color Intensity: `[Ambulance Utilization]`

---

## Page 3: Decision Quality

### Executive KPI Header Cards
1. **Optimizer Confidence**: `[Optimizer Confidence]` (Target: > 90%)
2. **Human Override Rate**: `[Human Override Rate]` (Target: < 5%)
3. **Average Decision Solve Time**: `42 ms` (Deterministic engine benchmark)
4. **ETA Forecast Accuracy**: `[ETA Forecast Accuracy]` (Target: > 92%)
5. **Total Automated Decisions**: `[Total Automated Decisions]`

### Visual Layout
- **Visual 1 (Top Left - Scatter Plot / Bubble)**: *Optimizer Confidence vs. Effective Response ETA*
  - X-axis: `eta_minutes`
  - Y-axis: `confidence`
  - Bubble Size: `people_at_risk`
  - Color: `severity`
- **Visual 2 (Top Right - Stacked Bar Chart)**: *Human Override Frequency by Incident Severity*
  - X-axis: `severity`
  - Y-axis: `decision_count`
  - Legend: `human_override` (True / False)
- **Visual 3 (Bottom - Interactive Table / Audit Trail)**: *Decision Audit Explorer*
  - Columns: `audit_id`, `incident_id`, `created_at`, `selected_ambulance`, `selected_hospital`, `confidence`, `eta_minutes`, `human_override`
  - Detail Tooltip: Score Breakdown (distance, traffic, equipment, hospital capacity)
