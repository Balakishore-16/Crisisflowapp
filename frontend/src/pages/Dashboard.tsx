/* ─── CrisisFlow Dashboard ─── */
import { useState, useEffect, useCallback } from 'react';
import {
    AlertTriangle, Flame, Ambulance as AmbIcon, Truck, Building2,
    Clock, MapPin, Shield, Zap, Radio, Brain, ChevronRight, Target
} from 'lucide-react';
import { MapContainer, TileLayer, Marker, Popup, Circle, useMap } from 'react-leaflet';
import L from 'leaflet';
import {
    getAnalytics, getIncidents, getAmbulances, getFireStations,
    getHospitals, getRiskZones, getActivityLogs,
    simulateFire, simulateAccident, simulateMedical, simulateFlood, simulateIndustrial,
    getRecommendation, dispatchResponse,
} from '../services/api';
import { useWebSocket } from '../hooks/useWebSocket';
import type { Analytics, Incident, Recommendation, ActivityLog, WSEvent } from '../types';

function MapController() {
    const map = useMap();
    useEffect(() => {
        // Auto-locate GPS on page load so it is not a fixed map
        if ('geolocation' in navigator) {
            navigator.geolocation.getCurrentPosition(
                (pos) => map.setView([pos.coords.latitude, pos.coords.longitude], 13),
                () => console.warn('GPS denied or unavailable')
            );
        }

        const handler = (e: any) => map.flyTo([e.detail.lat, e.detail.lng], 14);
        window.addEventListener('map-fly-to', handler);
        return () => window.removeEventListener('map-fly-to', handler);
    }, [map]);
    return null;
}

// Custom Leaflet icons
const makeIcon = (color: string, emoji: string) =>
    L.divIcon({
        className: '',
        html: `<div style="background:${color};width:32px;height:32px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:16px;border:2px solid rgba(255,255,255,0.3);box-shadow:0 2px 8px rgba(0,0,0,0.4)">${emoji}</div>`,
        iconSize: [32, 32],
        iconAnchor: [16, 16],
    });

const ICONS = {
    fire: makeIcon('#ef4444', '🔥'),
    accident: makeIcon('#f97316', '🚗'),
    medical: makeIcon('#a855f7', '🏥'),
    flood: makeIcon('#3b82f6', '🌊'),
    industrial: makeIcon('#eab308', '🏭'),
    ambulance: makeIcon('#3b82f6', '🚑'),
    station: makeIcon('#f97316', '🚒'),
    hospital: makeIcon('#22c55e', '🏥'),
};

const incidentIcon = (type: string) => {
    if (type.includes('Fire')) return ICONS.fire;
    if (type.includes('Accident')) return ICONS.accident;
    if (type.includes('Medical')) return ICONS.medical;
    if (type.includes('Flood')) return ICONS.flood;
    return ICONS.industrial;
};

const severityBadge = (sev: string) => {
    const cls = sev === 'Critical' ? 'badge-critical' : sev === 'High' ? 'badge-high'
        : sev === 'Medium' ? 'badge-medium' : 'badge-low';
    return <span className={`badge ${cls}`}>{sev}</span>;
};

const statusBadge = (status: string) => {
    const cls = status === 'Dispatched' || status === 'Response In Progress' ? 'badge-dispatched'
        : status === 'Resolved' ? 'badge-available'
            : status === 'Awaiting Response' ? 'badge-high' : 'badge-medium';
    return <span className={`badge ${cls}`}>{status}</span>;
};

export default function Dashboard() {
    const [analytics, setAnalytics] = useState<Analytics | null>(null);
    const [incidents, setIncidents] = useState<Incident[]>([]);
    const [ambulances, setAmbulances] = useState<any[]>([]);
    const [stations, setStations] = useState<any[]>([]);
    const [hospitals, setHospitals] = useState<any[]>([]);
    const [riskZones, setRiskZones] = useState<any[]>([]);
    const [activities, setActivities] = useState<ActivityLog[]>([]);
    const [selectedIncident, setSelectedIncident] = useState<Incident | null>(null);
    const [recommendation, setRecommendation] = useState<Recommendation | null>(null);
    const [simulating, setSimulating] = useState('');
    const [dispatching, setDispatching] = useState(false);
    const [adminCity, setAdminCity] = useState<string>('Locating Region...');

    const loadData = useCallback(async () => {
        try {
            const [a, i, am, st, h, rz, al] = await Promise.all([
                getAnalytics(), getIncidents(), getAmbulances(), getFireStations(),
                getHospitals(), getRiskZones(), getActivityLogs(30),
            ]);
            setAnalytics(a);
            setIncidents(i);
            setAmbulances(am);
            setStations(st);
            setHospitals(h);
            setRiskZones(rz);
            setActivities(al);
        } catch (e) { console.error('Load error:', e); }
    }, []);

    useEffect(() => { loadData(); }, [loadData]);

    // Admin Geolocation Label
    useEffect(() => {
        if ('geolocation' in navigator) {
            navigator.geolocation.getCurrentPosition(
                async (pos) => {
                    try {
                        const res = await fetch(`https://nominatim.openstreetmap.org/reverse?format=json&lat=${pos.coords.latitude}&lon=${pos.coords.longitude}`);
                        const data = await res.json();
                        setAdminCity(data.address?.city || data.address?.town || data.address?.county || 'Active Region');
                    } catch { }
                },
                () => setAdminCity('Global View'),
                { enableHighAccuracy: false, maximumAge: 60000 }
            );
        } else {
            setAdminCity('Global View');
        }
    }, []);

    // WebSocket
    const onWsEvent = useCallback((evt: WSEvent) => {
        if (['INCIDENT_CREATED', 'INCIDENT_UPDATED', 'DISPATCH_CREATED',
            'RESOURCE_UPDATED', 'RECOMMENDATION_GENERATED', 'SIMULATION_TICK'].includes(evt.event_type)) {
            loadData();
        }
        if (evt.event_type === 'ACTIVITY') {
            setActivities(prev => [{ ...evt.data, id: Date.now(), timestamp: evt.timestamp } as any, ...prev].slice(0, 30));
        }
    }, [loadData]);
    const { connected } = useWebSocket(onWsEvent);

    // Simulation handlers
    const runSim = async (type: string, fn: () => Promise<any>) => {
        setSimulating(type);
        try {
            const result = await fn();
            if (result?.incident) {
                setSelectedIncident(result.incident as any);
                if (result.recommendation) setRecommendation(result.recommendation);
            }
            await loadData();
        } catch (e) { console.error(e); }
        setSimulating('');
    };

    // Load recommendation for selected incident
    const loadRec = async (inc: Incident) => {
        setSelectedIncident(inc);
        setRecommendation(null);
        try {
            const rec = await getRecommendation(inc.id);
            setRecommendation(rec);
        } catch { }
    };

    // Dispatch
    const handleDispatch = async () => {
        if (!selectedIncident) return;
        setDispatching(true);
        try {
            await dispatchResponse(selectedIncident.id);
            await loadData();
            setSelectedIncident(prev => prev ? { ...prev, status: 'Dispatched' } : null);
        } catch (e) { console.error(e); }
        setDispatching(false);
    };

    const locateMe = () => {
        if ('geolocation' in navigator) {
            navigator.geolocation.getCurrentPosition(
                (pos) => window.dispatchEvent(new CustomEvent('map-fly-to', { detail: { lat: pos.coords.latitude, lng: pos.coords.longitude } })),
                (err) => alert('Please enable location permissions.')
            );
        }
    };

    const kpis = [
        { label: 'Active Incidents', value: analytics?.active_incidents ?? '—', icon: AlertTriangle, color: 'text-crisis-red', bg: 'bg-crisis-red/10' },
        { label: 'Critical', value: analytics?.critical_incidents ?? '—', icon: Flame, color: 'text-crisis-orange', bg: 'bg-crisis-orange/10' },
        { label: 'Ambulances', value: `${analytics?.available_ambulances ?? '—'}/${analytics?.total_ambulances ?? '—'}`, icon: AmbIcon, color: 'text-crisis-blue', bg: 'bg-crisis-blue/10' },
        { label: 'Fire Trucks', value: `${analytics?.available_fire_trucks ?? '—'}/${analytics?.total_fire_trucks ?? '—'}`, icon: Truck, color: 'text-crisis-orange', bg: 'bg-crisis-orange/10' },
        { label: 'Hospitals', value: `${analytics?.available_hospitals ?? '—'}/${analytics?.total_hospitals ?? '—'}`, icon: Building2, color: 'text-crisis-green', bg: 'bg-crisis-green/10' },
        { label: 'Avg Response', value: analytics ? `${analytics.avg_response_time} min` : '—', icon: Clock, color: 'text-crisis-cyan', bg: 'bg-crisis-cyan/10' },
    ];

    return (
        <div className="space-y-4">
            {/* Header */}
            <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                    <h1 className="text-xl font-bold text-white flex items-center gap-2">
                        <Shield size={22} className="text-crisis-blue" />
                        Command Center
                    </h1>
                    <p className="text-xs text-slate-500 mt-0.5">Real-time emergency intelligence overview</p>
                </div>
                <div className="flex items-center gap-2 text-xs">
                    <span className={`w-2 h-2 rounded-full ${connected ? 'bg-crisis-green live-pulse' : 'bg-crisis-red'}`} />
                    <span className="text-slate-400">{connected ? 'WebSocket Connected' : 'Reconnecting...'}</span>
                </div>
            </div>

            {/* KPI Cards */}
            <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
                {kpis.map(k => (
                    <div key={k.label} className="card card-hover p-4">
                        <div className="flex items-center gap-2 mb-2">
                            <div className={`w-8 h-8 rounded-lg ${k.bg} flex items-center justify-center`}>
                                <k.icon size={16} className={k.color} />
                            </div>
                        </div>
                        <div className="text-2xl font-bold text-white">{k.value}</div>
                        <div className="text-xs text-slate-500 mt-1">{k.label}</div>
                    </div>
                ))}
            </div>

            {/* Simulation Buttons */}
            <div className="card p-4">
                <div className="flex items-center gap-2 mb-3">
                    <Zap size={16} className="text-crisis-yellow" />
                    <span className="text-sm font-semibold text-white">Live Field Triggers</span>
                </div>
                <div className="flex flex-wrap gap-2">
                    {[
                        { label: '🔥 Simulate Building Fire', fn: simulateFire, key: 'fire' },
                        { label: '🚗 Simulate Major Accident', fn: simulateAccident, key: 'accident' },
                        { label: '🏥 Simulate Medical Emergency', fn: simulateMedical, key: 'medical' },
                        { label: '🌊 Simulate Flood', fn: simulateFlood, key: 'flood' },
                        { label: '🏭 Simulate Industrial Accident', fn: simulateIndustrial, key: 'industrial' },
                    ].map(s => (
                        <button
                            key={s.key}
                            onClick={() => runSim(s.key, s.fn)}
                            disabled={!!simulating}
                            className="px-4 py-2 rounded-lg bg-navy-700 hover:bg-navy-600 text-sm font-medium
                         text-white transition-all border border-white/5 hover:border-white/10
                         disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {simulating === s.key ? '⏳ Processing...' : s.label}
                        </button>
                    ))}
                </div>
            </div>

            {/* Main grid: Map + Recommendation + Activity */}
            <div className="grid lg:grid-cols-3 gap-4">
                {/* Map */}
                <div className="lg:col-span-2 card overflow-hidden" style={{ height: 480 }}>
                    <div className="p-3 border-b border-white/5 flex items-center gap-2">
                        <MapPin size={14} className="text-crisis-blue" />
                        <span className="text-sm font-semibold text-white">Live Emergency Map</span>
                        <div className="ml-auto flex items-center gap-2">
                            <span className="text-xs text-slate-500 font-semibold">{adminCity}</span>
                            <button onClick={locateMe} className="p-1 hover:bg-slate-200 rounded text-slate-500 hover:text-crisis-blue transition-colors" title="Locate Me">
                                <Target size={16} />
                            </button>
                        </div>
                    </div>
                    <MapContainer
                        center={[17.420, 78.450]}
                        zoom={12}
                        style={{ height: 'calc(100% - 44px)', width: '100%' }}
                        zoomControl={false}
                    >
                        <TileLayer
                            url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                            attribution='&copy; OpenStreetMap contributors'
                        />
                        <MapController />
                        {/* Incidents */}
                        {incidents.filter(i => i.status !== 'Resolved').map(inc => (
                            <Marker key={inc.id} position={[inc.latitude, inc.longitude]}
                                icon={incidentIcon(inc.incident_type)}
                                eventHandlers={{ click: () => loadRec(inc) }}>
                                <Popup>
                                    <div className="text-xs space-y-1">
                                        <div className="font-bold">{inc.incident_type}</div>
                                        <div>{inc.location}</div>
                                        <div>Severity: {inc.severity}</div>
                                        <div>People at Risk: {inc.people_at_risk}</div>
                                        <div>Status: {inc.status}</div>
                                    </div>
                                </Popup>
                            </Marker>
                        ))}
                        {/* Ambulances */}
                        {ambulances.map(a => (
                            <Marker key={a.id} position={[a.latitude, a.longitude]} icon={ICONS.ambulance}>
                                <Popup><div className="text-xs"><b>{a.call_sign}</b><br />{a.location}<br />Status: {a.status}</div></Popup>
                            </Marker>
                        ))}
                        {/* Fire Stations */}
                        {stations.map(s => (
                            <Marker key={s.id} position={[s.latitude, s.longitude]} icon={ICONS.station}>
                                <Popup><div className="text-xs"><b>{s.name}</b><br />{s.location}<br />Trucks: {s.available_trucks}</div></Popup>
                            </Marker>
                        ))}
                        {/* Hospitals */}
                        {hospitals.map(h => (
                            <Marker key={h.id} position={[h.latitude, h.longitude]} icon={ICONS.hospital}>
                                <Popup><div className="text-xs"><b>{h.name}</b><br />{h.location}<br />Occupancy: {Math.round(h.occupancy * 100)}%<br />Status: {h.status}</div></Popup>
                            </Marker>
                        ))}
                        {/* Risk Zones */}
                        {riskZones.map(rz => (
                            <Circle key={rz.id}
                                center={[rz.latitude, rz.longitude]}
                                radius={rz.radius * 1000}
                                pathOptions={{
                                    color: rz.risk_level === 'Critical' ? '#ef4444' : rz.risk_level === 'High' ? '#f97316'
                                        : rz.risk_level === 'Medium' ? '#eab308' : '#3b82f6',
                                    fillOpacity: 0.1,
                                    weight: 1,
                                }}
                            />
                        ))}
                    </MapContainer>
                </div>

                {/* Right column: Recommendation + Activity */}
                <div className="space-y-4">
                    {/* AI Recommendation Card */}
                    {selectedIncident && (
                        <div className="card border-crisis-purple/30 overflow-hidden">
                            <div className="p-3 bg-gradient-to-r from-crisis-purple/10 to-transparent border-b border-white/5">
                                <div className="flex items-center gap-2">
                                    <Brain size={16} className="text-crisis-purple" />
                                    <span className="text-sm font-bold text-white">PRIORITY DECISION</span>
                                </div>
                            </div>
                            <div className="p-4 space-y-3">
                                <div className="flex items-center justify-between">
                                    <div>
                                        <div className="text-xs text-slate-500">{selectedIncident.id}</div>
                                        <div className="font-semibold text-white">{selectedIncident.incident_type}</div>
                                        <div className="text-xs text-slate-400">{selectedIncident.location}</div>
                                    </div>
                                    {severityBadge(selectedIncident.severity)}
                                </div>

                                {recommendation ? (
                                    <>
                                        <div className="grid grid-cols-2 gap-2">
                                            {recommendation.fire_station_name && (
                                                <div className="bg-navy-800 rounded-lg p-2">
                                                    <div className="text-[10px] text-slate-500 uppercase">🚒 Fire Station</div>
                                                    <div className="text-sm font-semibold text-white">{recommendation.fire_station_name}</div>
                                                </div>
                                            )}
                                            {recommendation.ambulance_id && (
                                                <div className="bg-navy-800 rounded-lg p-2">
                                                    <div className="text-[10px] text-slate-500 uppercase">🚑 Ambulance</div>
                                                    <div className="text-sm font-semibold text-white">{recommendation.ambulance_id}</div>
                                                </div>
                                            )}
                                            {recommendation.hospital_name && (
                                                <div className="bg-navy-800 rounded-lg p-2">
                                                    <div className="text-[10px] text-slate-500 uppercase">🏥 Hospital</div>
                                                    <div className="text-sm font-semibold text-white">{recommendation.hospital_name}</div>
                                                </div>
                                            )}
                                            {recommendation.route && (
                                                <div className="bg-navy-800 rounded-lg p-2">
                                                    <div className="text-[10px] text-slate-500 uppercase">🛣️ Route</div>
                                                    <div className="text-sm font-semibold text-white">{recommendation.route}</div>
                                                </div>
                                            )}
                                        </div>

                                        <div className="flex gap-3">
                                            <div className="bg-navy-800 rounded-lg p-2 flex-1 text-center">
                                                <div className="text-[10px] text-slate-500">⏱️ ETA</div>
                                                <div className="text-lg font-bold text-crisis-cyan">{recommendation.eta_minutes} min</div>
                                            </div>
                                            <div className="bg-navy-800 rounded-lg p-2 flex-1 text-center">
                                                <div className="text-[10px] text-slate-500">🎯 Confidence</div>
                                                <div className="text-lg font-bold text-crisis-green">{recommendation.confidence}%</div>
                                            </div>
                                        </div>

                                        {/* Reasons */}
                                        <div>
                                            <div className="text-xs font-semibold text-slate-400 mb-1.5">Why this recommendation?</div>
                                            <div className="space-y-1">
                                                {recommendation.reasons.map((r: string, i: number) => (
                                                    <div key={i} className="flex items-start gap-2 text-xs text-slate-300">
                                                        <span className="text-crisis-green mt-0.5">✓</span>
                                                        <span>{r}</span>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>

                                        {/* Dispatch Button */}
                                        {selectedIncident.status === 'Awaiting Response' && (
                                            <button
                                                onClick={handleDispatch}
                                                disabled={dispatching}
                                                className="btn-danger w-full flex items-center justify-center gap-2"
                                            >
                                                <Radio size={16} />
                                                {dispatching ? '⏳ DISPATCHING...' : '🚨 DISPATCH RESPONSE'}
                                            </button>
                                        )}
                                        {selectedIncident.status === 'Dispatched' && (
                                            <div className="text-center text-sm text-crisis-green font-semibold py-2">
                                                ✓ Response Dispatched
                                            </div>
                                        )}
                                    </>
                                ) : (
                                    <div className="text-xs text-slate-500 text-center py-4">
                                        {selectedIncident.status === 'Detected' ? 'Analyzing incident...' : 'No recommendation available'}
                                    </div>
                                )}
                            </div>
                        </div>
                    )}

                    {/* Activity Feed */}
                    <div className="card" style={{ maxHeight: selectedIncident ? 280 : 480 }}>
                        <div className="p-3 border-b border-white/5 flex items-center gap-2">
                            <Radio size={14} className="text-crisis-green" />
                            <span className="text-sm font-semibold text-white">Live Activity</span>
                        </div>
                        <div className="overflow-y-auto" style={{ maxHeight: selectedIncident ? 236 : 436 }}>
                            {activities.map((a, i) => (
                                <div key={a.id || i} className="px-3 py-2 border-b border-white/3 hover:bg-white/2 transition-colors">
                                    <div className="flex items-start gap-2">
                                        <span className="text-base shrink-0">{a.icon}</span>
                                        <div className="flex-1 min-w-0">
                                            <div className="text-xs text-slate-300 truncate">{a.message}</div>
                                            <div className="text-[10px] text-slate-600 mt-0.5">
                                                {a.timestamp ? new Date(a.timestamp).toLocaleTimeString() : ''}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            ))}
                            {activities.length === 0 && (
                                <div className="p-6 text-center text-xs text-slate-600">No activity yet</div>
                            )}
                        </div>
                    </div>
                </div>
            </div>

            {/* Recent Incidents Table */}
            <div className="card">
                <div className="p-3 border-b border-white/5 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <AlertTriangle size={14} className="text-crisis-red" />
                        <span className="text-sm font-semibold text-white">Recent Incidents</span>
                    </div>
                    <a href="/incidents" className="text-xs text-crisis-blue hover:underline flex items-center gap-1">
                        View All <ChevronRight size={12} />
                    </a>
                </div>
                <div className="overflow-x-auto">
                    <table className="w-full text-xs">
                        <thead>
                            <tr className="border-b border-white/5 text-slate-500">
                                <th className="text-left p-3 font-medium">ID</th>
                                <th className="text-left p-3 font-medium">Type</th>
                                <th className="text-left p-3 font-medium">Location</th>
                                <th className="text-left p-3 font-medium">Severity</th>
                                <th className="text-left p-3 font-medium">People</th>
                                <th className="text-left p-3 font-medium">Status</th>
                                <th className="text-left p-3 font-medium">Action</th>
                            </tr>
                        </thead>
                        <tbody>
                            {incidents.slice(0, 8).map(inc => (
                                <tr key={inc.id}
                                    className="border-b border-white/3 hover:bg-white/2 transition-colors cursor-pointer"
                                    onClick={() => loadRec(inc)}>
                                    <td className="p-3 font-mono text-slate-400">{inc.id}</td>
                                    <td className="p-3 text-white">{inc.incident_type}</td>
                                    <td className="p-3 text-slate-300">{inc.location}</td>
                                    <td className="p-3">{severityBadge(inc.severity)}</td>
                                    <td className="p-3 text-slate-300">{inc.people_at_risk}</td>
                                    <td className="p-3">{statusBadge(inc.status)}</td>
                                    <td className="p-3">
                                        <button onClick={(e) => { e.stopPropagation(); loadRec(inc); }}
                                            className="text-crisis-blue hover:text-crisis-cyan text-xs">
                                            Details →
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
        </div>
    );
}
