/* ─── CrisisFlow Dashboard ─── */
import { useState, useEffect, useCallback } from 'react';
import {
    AlertTriangle, Flame, Ambulance as AmbIcon, Truck, Building2,
    Clock, MapPin, Shield, Zap, Brain, Navigation
} from 'lucide-react';
import { MapContainer, TileLayer, Marker, Popup, Circle, Polyline, useMap } from 'react-leaflet';
import {
    getAnalytics, getIncidents, getAmbulances, getFireStations,
    getHospitals, getRiskZones, getActivityLogs,
    simulateFire, simulateAccident, simulateMedical, simulateFlood, simulateIndustrial,
    getRecommendation, dispatchResponse, fetchRoute
} from '../services/api';
import { useWebSocket } from '../hooks/useWebSocket';
import type { Analytics, Incident, Recommendation, ActivityLog, WSEvent } from '../types';
import {
    createIncidentSvgIcon, createAmbulanceSvgIcon,
    createFireStationSvgIcon, createHospitalSvgIcon,
    createUserLiveGpsSvgIcon
} from '../components/MapIcons';

function MapController() {
    const map = useMap();
    useEffect(() => {
        const handler = (e: any) => map.flyTo([e.detail.lat, e.detail.lng], 15);
        window.addEventListener('map-fly-to', handler);
        return () => window.removeEventListener('map-fly-to', handler);
    }, [map]);
    return null;
}

const severityBadge = (sev: string) => {
    const cls = sev === 'Critical' ? 'badge-critical' : sev === 'High' ? 'badge-high'
        : sev === 'Medium' ? 'badge-medium' : 'badge-low';
    return <span className={`badge ${cls}`}>{sev}</span>;
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

    // Live User GPS Location
    const [userLocation, setUserLocation] = useState<{ lat: number; lng: number } | null>(null);
    const [locating, setLocating] = useState(false);

    // Map Layer Toggles
    const [showIncidents, setShowIncidents] = useState(true);
    const [showAmbulances, setShowAmbulances] = useState(true);
    const [showHospitals, setShowHospitals] = useState(true);
    const [showRoutes, setShowRoutes] = useState(true);
    const [showRiskZones, setShowRiskZones] = useState(true);

    // Active Polyline Geometries
    const [activeRouteGeometry, setActiveRouteGeometry] = useState<[number, number][]>([]);

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

    // Real-time WebSocket Telemetry Handler (Smooth movement & status updates)
    const onWsEvent = useCallback((evt: WSEvent) => {
        if (evt.event_type === 'RESOURCE_LOCATION_UPDATED' && evt.data) {
            setAmbulances(prev => prev.map(amb => amb.id === evt.data.resource_id ? {
                ...amb,
                latitude: evt.data.latitude,
                longitude: evt.data.longitude,
                speed_kmh: evt.data.speed_kmh,
                heading: evt.data.heading,
                location_source: evt.data.location_source,
                location_status: evt.data.location_status,
                status: evt.data.status || amb.status,
            } : amb));
        }

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

    // Load recommendation & OSRM route for selected incident
    const loadRec = async (inc: Incident) => {
        setSelectedIncident(inc);
        setRecommendation(null);
        setActiveRouteGeometry([]);
        try {
            const rec = await getRecommendation(inc.id);
            setRecommendation(rec);

            // Fetch route geometry if ambulance assigned
            if (rec.ambulance_id) {
                const amb = ambulances.find(a => a.id === rec.ambulance_id);
                if (amb) {
                    const routeRes = await fetchRoute(amb.latitude, amb.longitude, inc.latitude, inc.longitude);
                    if (routeRes && routeRes.geometry) {
                        setActiveRouteGeometry(routeRes.geometry);
                    } else {
                        setActiveRouteGeometry([[amb.latitude, amb.longitude], [inc.latitude, inc.longitude]]);
                    }
                }
            }
        } catch { }
    };

    // Dispatch Handler
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

    // Locate Me Handler (Live User Location)
    const handleLocateLivePosition = () => {
        if (!('geolocation' in navigator)) {
            alert('Geolocation API is not supported by your browser.');
            return;
        }
        setLocating(true);
        navigator.geolocation.getCurrentPosition(
            (pos) => {
                const lat = pos.coords.latitude;
                const lng = pos.coords.longitude;
                setUserLocation({ lat, lng });
                window.dispatchEvent(new CustomEvent('map-fly-to', { detail: { lat, lng } }));
                setLocating(false);
            },
            (err) => {
                console.error('Geolocation error:', err);
                alert('Unable to retrieve your live GPS location. Please check browser permissions.');
                setLocating(false);
            },
            { enableHighAccuracy: true, timeout: 10000 }
        );
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
                    <p className="text-xs text-slate-500 mt-0.5">Real-time emergency intelligence overview & geospatial tracking</p>
                </div>
                <div className="flex items-center gap-2 text-xs">
                    <span className={`w-2 h-2 rounded-full ${connected ? 'bg-crisis-green live-pulse' : 'bg-crisis-red'}`} />
                    <span className="text-slate-400">{connected ? 'WebSocket Live Telemetry Connected' : 'Reconnecting...'}</span>
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

            {/* Simulation Triggers */}
            <div className="card p-4">
                <div className="flex items-center gap-2 mb-3">
                    <Zap size={16} className="text-crisis-yellow" />
                    <span className="text-sm font-semibold text-white">Live Emergency Triggers & OSRM Simulation</span>
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
                {/* Map Panel */}
                <div className="lg:col-span-2 card overflow-hidden flex flex-col relative" style={{ height: 520 }}>
                    <div className="p-3 border-b border-white/5 flex items-center justify-between flex-wrap gap-2">
                        <div className="flex items-center gap-2">
                            <MapPin size={14} className="text-crisis-blue" />
                            <span className="text-sm font-semibold text-white">Live Emergency Map</span>
                            <span className="text-xs text-slate-500">• Hyderabad Operational Zone</span>
                        </div>

                        {/* Map Header Controls & Live Location Button */}
                        <div className="flex items-center gap-3 text-xs text-slate-300">
                            <label className="flex items-center gap-1 cursor-pointer">
                                <input type="checkbox" checked={showIncidents} onChange={e => setShowIncidents(e.target.checked)} className="rounded text-crisis-blue" />
                                Incidents
                            </label>
                            <label className="flex items-center gap-1 cursor-pointer">
                                <input type="checkbox" checked={showAmbulances} onChange={e => setShowAmbulances(e.target.checked)} className="rounded text-crisis-blue" />
                                Units
                            </label>
                            <label className="flex items-center gap-1 cursor-pointer">
                                <input type="checkbox" checked={showHospitals} onChange={e => setShowHospitals(e.target.checked)} className="rounded text-crisis-blue" />
                                Hospitals
                            </label>
                            <label className="flex items-center gap-1 cursor-pointer">
                                <input type="checkbox" checked={showRoutes} onChange={e => setShowRoutes(e.target.checked)} className="rounded text-crisis-blue" />
                                Routes
                            </label>
                            <label className="flex items-center gap-1 cursor-pointer">
                                <input type="checkbox" checked={showRiskZones} onChange={e => setShowRiskZones(e.target.checked)} className="rounded text-crisis-blue" />
                                Risk Zones
                            </label>

                            {/* Prominent Clean Live Location Button */}
                            <button
                                onClick={handleLocateLivePosition}
                                disabled={locating}
                                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-crisis-blue hover:bg-blue-600 text-white font-bold text-xs shadow-md transition-all border border-blue-400/30"
                                aria-label="Center map to my live location"
                            >
                                <Navigation size={13} className={locating ? 'animate-spin' : ''} />
                                {locating ? 'Locating...' : 'Live Location'}
                            </button>
                        </div>
                    </div>

                    <MapContainer
                        center={[17.442, 78.390]}
                        zoom={13}
                        style={{ height: '100%', width: '100%' }}
                        zoomControl={false}
                    >
                        <TileLayer
                            url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png"
                            attribution='&copy; OpenStreetMap & CARTO'
                        />
                        <MapController />

                        {/* Route Polylines */}
                        {showRoutes && activeRouteGeometry.length > 0 && (
                            <Polyline
                                positions={activeRouteGeometry}
                                pathOptions={{ color: '#0284c7', weight: 4, opacity: 0.9, dashArray: '8, 8' }}
                            />
                        )}

                        {/* User Live GPS Marker */}
                        {userLocation && (
                            <Marker position={[userLocation.lat, userLocation.lng]} icon={createUserLiveGpsSvgIcon()}>
                                <Popup>
                                    <div className="text-xs space-y-1 text-slate-900">
                                        <div className="font-bold flex items-center gap-1">
                                            <span>Your Live Location</span>
                                            <span className="text-[10px] bg-red-100 text-red-800 font-mono px-1 rounded">LIVE GPS</span>
                                        </div>
                                        <div>Latitude: <strong>{userLocation.lat.toFixed(5)}</strong></div>
                                        <div>Longitude: <strong>{userLocation.lng.toFixed(5)}</strong></div>
                                    </div>
                                </Popup>
                            </Marker>
                        )}

                        {/* Incidents (Vector SVG Icons) */}
                        {showIncidents && incidents.filter(i => i.status !== 'Resolved').map(inc => (
                            <Marker
                                key={inc.id}
                                position={[inc.latitude, inc.longitude]}
                                icon={createIncidentSvgIcon(inc.severity, inc.incident_type)}
                                eventHandlers={{ click: () => loadRec(inc) }}
                            >
                                <Popup>
                                    <div className="text-xs space-y-1 text-slate-900">
                                        <div className="font-bold">{inc.id} — {inc.incident_type}</div>
                                        <div>{inc.location} ({inc.zone || 'Central'})</div>
                                        <div>Severity: <strong className="text-crisis-red">{inc.severity}</strong></div>
                                        <div>People at Risk: {inc.people_at_risk}</div>
                                        <div>Status: <strong>{inc.status}</strong></div>
                                    </div>
                                </Popup>
                            </Marker>
                        ))}

                        {/* Ambulances & Emergency Resource Telemetry Vector Markers */}
                        {showAmbulances && ambulances.map(a => (
                            <Marker
                                key={a.id}
                                position={[a.latitude, a.longitude]}
                                icon={createAmbulanceSvgIcon(a.heading, a.location_source, a.status)}
                            >
                                <Popup>
                                    <div className="text-xs space-y-1 min-w-[160px] text-slate-900">
                                        <div className="font-bold flex items-center justify-between">
                                            <span>Ambulance {a.call_sign}</span>
                                            <span className="text-[10px] bg-blue-100 text-blue-800 font-mono px-1 rounded">
                                                {a.location_source || 'SIMULATION'}
                                            </span>
                                        </div>
                                        <div>Status: <strong className="text-blue-600">{a.status}</strong></div>
                                        {a.speed_kmh > 0 && <div>Speed: <strong>{Math.round(a.speed_kmh)} km/h</strong></div>}
                                        {a.heading !== undefined && a.heading !== null && <div>Heading: <strong>{Math.round(a.heading)}°</strong></div>}
                                        {a.current_incident_id && <div>Incident: <strong>{a.current_incident_id}</strong></div>}
                                        <div className="text-[10px] text-slate-500 font-mono pt-1 border-t border-slate-200">
                                            Lat: {a.latitude.toFixed(4)}, Lon: {a.longitude.toFixed(4)}
                                        </div>
                                    </div>
                                </Popup>
                            </Marker>
                        ))}

                        {/* Fire Stations (Vector SVG Markers) */}
                        {showAmbulances && stations.map(s => (
                            <Marker key={s.id} position={[s.latitude, s.longitude]} icon={createFireStationSvgIcon()}>
                                <Popup>
                                    <div className="text-xs text-slate-900">
                                        <b>{s.name}</b><br />
                                        {s.location}<br />
                                        Available Trucks: <strong>{s.available_trucks}</strong>
                                    </div>
                                </Popup>
                            </Marker>
                        ))}

                        {/* Hospitals (Vector SVG Markers) */}
                        {showHospitals && hospitals.map(h => (
                            <Marker key={h.id} position={[h.latitude, h.longitude]} icon={createHospitalSvgIcon()}>
                                <Popup>
                                    <div className="text-xs text-slate-900 space-y-1">
                                        <b>{h.name}</b><br />
                                        <div>Beds: <strong>{h.available_beds} / {h.total_beds}</strong></div>
                                        <div>Occupancy: {Math.round(h.occupancy * 100)}%</div>
                                        <div>Status: <strong className="text-green-600">{h.status}</strong></div>
                                    </div>
                                </Popup>
                            </Marker>
                        ))}

                        {/* Risk Zones */}
                        {showRiskZones && riskZones.map(rz => (
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
                                    <div className="space-y-2.5 pt-2 border-t border-white/5 text-xs">
                                        <div className="flex justify-between text-slate-300">
                                            <span>ETA: <strong className="text-white">{recommendation.eta_minutes} min</strong></span>
                                            <span>Score: <strong className="text-crisis-green">{recommendation.score}%</strong></span>
                                        </div>
                                        {recommendation.ambulance_id && (
                                            <div className="text-slate-300">Ambulance: <strong>{recommendation.ambulance_id}</strong></div>
                                        )}
                                        {recommendation.hospital_name && (
                                            <div className="text-slate-300">Hospital: <strong>{recommendation.hospital_name}</strong></div>
                                        )}

                                        {selectedIncident.status !== 'Dispatched' && selectedIncident.status !== 'Resolved' && (
                                            <button
                                                onClick={handleDispatch}
                                                disabled={dispatching}
                                                className="btn-danger w-full mt-2 py-2 font-bold text-xs"
                                            >
                                                {dispatching ? 'Dispatching...' : '🚨 DISPATCH EMERGENCY RESPONSE'}
                                            </button>
                                        )}
                                    </div>
                                ) : (
                                    <div className="text-xs text-slate-500 py-2 text-center animate-pulse">Calculating optimal dispatch...</div>
                                )}
                            </div>
                        </div>
                    )}

                    {/* Activity Feed */}
                    <div className="card p-4 overflow-hidden flex flex-col" style={{ height: selectedIncident ? 280 : 520 }}>
                        <div className="flex items-center gap-2 mb-3">
                            <span className="w-2 h-2 rounded-full bg-crisis-blue animate-pulse" />
                            <span className="text-sm font-semibold text-white">Live Event Audit Feed</span>
                        </div>
                        <div className="flex-1 overflow-y-auto space-y-2 text-xs">
                            {activities.map((a, i) => (
                                <div key={a.id || i} className="p-2 rounded bg-navy-800/60 border border-white/5 space-y-0.5">
                                    <div className="flex items-center justify-between text-[11px]">
                                        <span className="font-semibold text-slate-300">{a.icon || '📋'} {a.event_type}</span>
                                        <span className="font-mono text-slate-500 text-[10px]">
                                            {a.timestamp ? new Date(a.timestamp).toLocaleTimeString() : ''}
                                        </span>
                                    </div>
                                    <div className="text-slate-400 leading-tight">{a.message}</div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
