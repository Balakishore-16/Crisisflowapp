# CrisisFlow — Fabric Activator Rules
# ═════════════════════════════════════
# Configure these rules in Microsoft Fabric Activator
# to trigger automated alerts on emergency conditions.

## Rule 1: Critical Incident Alert
- **Condition:** `severity == "Critical"`
- **Source:** Eventhouse → Incidents table
- **Action:** Send Teams notification to Emergency Commander
- **Message:** "🚨 CRITICAL: {incident_type} at {location} — {people_at_risk} people at risk"

## Rule 2: Resource Shortage
- **Condition:** Available ambulances < 3
- **Source:** Eventhouse → ResourceEvents (latest per resource)
- **Action:** Send email alert to Resource Manager
- **Message:** "⚠️ LOW RESOURCES: Only {count} ambulances available"

## Rule 3: Hospital Overload
- **Condition:** `occupancy > 0.90`
- **Source:** Eventhouse → HospitalEvents (latest per hospital)
- **Action:** Send Teams alert
- **Message:** "🏥 HOSPITAL ALERT: {hospital_name} at {occupancy}% capacity"

## Rule 4: High Risk Zone
- **Condition:** `risk_score > 85`
- **Source:** Eventhouse → RiskEvents (latest per zone)
- **Action:** Send notification
- **Message:** "⚠️ HIGH RISK: {zone_name} risk score {risk_score}"

## Rule 5: Slow Response Time
- **Condition:** `eta_minutes > 15`
- **Source:** Eventhouse → DispatchEvents
- **Action:** Escalation alert
- **Message:** "⏰ SLOW RESPONSE: {incident_id} ETA {eta_minutes} min exceeds 15 min SLA"

## Setup Steps
1. Open Fabric Activator in your workspace
2. Connect to the Eventhouse KQL database
3. Create each rule with the conditions above
4. Configure action destinations (Teams, Email, Power Automate)
5. Activate rules
