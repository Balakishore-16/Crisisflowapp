/* ─── Types for CrisisFlow ─── */

export interface Incident {
    id: string;
    incident_type: string;
    location: string;
    zone?: string;
    latitude: number;
    longitude: number;
    floor?: number | null;
    building?: string | null;
    severity: string;
    people_at_risk: number;
    description?: string | null;
    status: string;
    spread_risk?: string | null;
    is_duplicate?: boolean;
    duplicate_of_id?: string | null;
    created_at?: string;
    updated_at?: string;
    is_simulated?: boolean;
}

export interface BulkOperationResponse {
    successful: string[];
    failed: string[];
    errors: Record<string, string>;
    message: string;
}

export interface TimelineEvent {
    id: string;
    incident_id: string;
    event_type: string;
    title: string;
    description: string;
    severity: string;
    icon: string;
    timestamp: string;
}

export interface Ambulance {
    id: string;
    call_sign: string;
    location: string;
    latitude: number;
    longitude: number;
    status: string;
    equipment: string[];
    capacity: number;
    current_incident_id?: string | null;
}

export interface FireStation {
    id: string;
    name: string;
    location: string;
    latitude: number;
    longitude: number;
    available_trucks: number;
    status: string;
}

export interface FireTruck {
    id: string;
    station_id: string;
    call_sign: string;
    location: string;
    latitude: number;
    longitude: number;
    status: string;
    equipment: string[];
    current_incident_id?: string | null;
}

export interface Hospital {
    id: string;
    name: string;
    location: string;
    latitude: number;
    longitude: number;
    emergency_capacity: number;
    icu_beds: number;
    trauma_beds: number;
    burn_capacity: number;
    occupancy: number;
    status: string;
}

export interface RiskZone {
    id: string;
    name: string;
    latitude: number;
    longitude: number;
    radius: number;
    risk_level: string;
    risk_score: number;
    factors: string[];
    active_incidents: number;
}

export interface Recommendation {
    id: string;
    incident_id: string;
    fire_station_id?: string;
    fire_station_name?: string;
    fire_truck_id?: string;
    ambulance_id?: string;
    hospital_id?: string;
    hospital_name?: string;
    route?: string;
    eta_minutes?: number;
    score?: number;
    confidence?: number;
    reasons: string[];
    explanation?: string;
    data_considered: string[];
    created_at?: string;
}

export interface Dispatch {
    id: string;
    incident_id: string;
    fire_station_id?: string;
    fire_truck_id?: string;
    ambulance_id?: string;
    hospital_id?: string;
    route?: string;
    eta_minutes?: number;
    confidence?: number;
    reasons: string[];
    status: string;
    created_at?: string;
}

export interface ActivityLog {
    id: number;
    incident_id?: string;
    event_type: string;
    message: string;
    severity: string;
    icon: string;
    timestamp?: string;
}

export interface Analytics {
    total_incidents: number;
    active_incidents: number;
    critical_incidents: number;
    resolved_incidents: number;
    total_dispatches: number;
    avg_response_time: number;
    available_ambulances: number;
    total_ambulances: number;
    available_fire_trucks: number;
    total_fire_trucks: number;
    available_hospitals: number;
    total_hospitals: number;
    high_risk_zones: number;
    incidents_by_type: Record<string, number>;
    incidents_by_severity: Record<string, number>;
    incidents_by_status: Record<string, number>;
    hospital_capacity: HospitalCapacity[];
    resource_utilization: Record<string, { total: number; available: number; utilization: number }>;
    response_time_trend: any[];
    incident_trend: any[];
}

export interface HospitalCapacity {
    name: string;
    occupancy: number;
    emergency_capacity: number;
    icu_beds: number;
    trauma_beds: number;
    burn_capacity: number;
    status: string;
}

export interface FabricStatus {
    eventstream: string;
    eventhouse: string;
    onelake: string;
    lakehouse: string;
    powerbi: string;
    activator: string;
    ai: string;
    overall: string;
    last_event_time?: string;
    message: string;
}

export interface WSEvent {
    event_type: string;
    data: Record<string, any>;
    timestamp: string;
}
