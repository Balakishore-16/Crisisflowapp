/* ─── CrisisFlow API Service ─── */

const API_BASE = '/api';

async function request<T>(path: string, options?: RequestInit): Promise<T> {
    const res = await fetch(`${API_BASE}${path}`, {
        headers: { 'Content-Type': 'application/json' },
        ...options,
    });
    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail || res.statusText);
    }
    return res.json();
}

// Health
export const getHealth = () => request<any>('/health');

// Incidents
export const getIncidents = () => request<any[]>('/incidents');
export const getIncident = (id: string) => request<any>(`/incidents/${id}`);
export const createIncident = (data: any) =>
    request<any>('/incidents', { method: 'POST', body: JSON.stringify(data) });
export const updateIncident = (id: string, data: any) =>
    request<any>(`/incidents/${id}`, { method: 'PUT', body: JSON.stringify(data) });
export const deleteIncident = (id: string) =>
    request<any>(`/incidents/${id}`, { method: 'DELETE' });
export const analyzeIncident = (id: string) =>
    request<any>(`/incidents/${id}/analyze`, { method: 'POST' });
export const getRecommendation = (id: string) =>
    request<any>(`/incidents/${id}/recommendation`);
export const dispatchResponse = (id: string, data?: any) =>
    request<any>(`/incidents/${id}/dispatch`, { method: 'POST', body: data ? JSON.stringify(data) : undefined });
export const bulkAcknowledge = (incident_ids: string[]) =>
    request<any>('/incidents/bulk/acknowledge', { method: 'POST', body: JSON.stringify({ incident_ids }) });
export const bulkDispatch = (incident_ids: string[]) =>
    request<any>('/incidents/bulk/dispatch', { method: 'POST', body: JSON.stringify({ incident_ids }) });
export const getIncidentTimeline = (id: string) =>
    request<any[]>(`/incidents/${id}/timeline`);
export const fetchRoute = (origin_lat: number, origin_lon: number, dest_lat: number, dest_lon: number) =>
    request<any>(`/external/route?origin_lat=${origin_lat}&origin_lon=${origin_lon}&dest_lat=${dest_lat}&dest_lon=${dest_lon}`);

// Simulation
export const simulateFire = () => request<any>('/simulate/fire', { method: 'POST' });
export const simulateAccident = () => request<any>('/simulate/accident', { method: 'POST' });
export const simulateMedical = () => request<any>('/simulate/medical', { method: 'POST' });
export const simulateFlood = () => request<any>('/simulate/flood', { method: 'POST' });
export const simulateIndustrial = () => request<any>('/simulate/industrial', { method: 'POST' });

// Resources
export const getResources = () => request<any>('/resources');
export const getAmbulances = () => request<any[]>('/ambulances');
export const getFireStations = () => request<any[]>('/fire-stations');
export const getFireTrucks = () => request<any[]>('/fire-trucks');

// Hospitals
export const getHospitals = () => request<any[]>('/hospitals');

// Analytics
export const getAnalytics = () => request<any>('/analytics');
export const getActivityLogs = (limit = 50) =>
    request<any[]>(`/activity-logs?limit=${limit}`);

// Risk Zones
export const getRiskZones = () => request<any[]>('/risk-zones');

// Fabric
export const getFabricStatus = () => request<any>('/fabric/status');
