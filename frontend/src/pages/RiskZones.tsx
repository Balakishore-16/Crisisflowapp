import { useState, useEffect } from 'react';
import { MapPin, AlertTriangle, Shield } from 'lucide-react';
import { MapContainer, TileLayer, Circle, Popup } from 'react-leaflet';
import { getRiskZones } from '../services/api';
import type { RiskZone } from '../types';

const riskColor = (level: string) =>
    level === 'Critical' ? '#ef4444' : level === 'High' ? '#f97316'
        : level === 'Medium' ? '#eab308' : '#3b82f6';

const riskBadge = (level: string) => {
    const c = level === 'Critical' ? 'badge-critical' : level === 'High' ? 'badge-high'
        : level === 'Medium' ? 'badge-medium' : 'badge-low';
    return <span className={`badge ${c}`}>{level}</span>;
};

export default function RiskZones() {
    const [zones, setZones] = useState<RiskZone[]>([]);

    useEffect(() => { getRiskZones().then(setZones); }, []);

    return (
        <div className="space-y-4">
            <div>
                <h1 className="text-xl font-bold text-white flex items-center gap-2">
                    <MapPin size={22} className="text-crisis-orange" /> Risk Zones
                </h1>
                <p className="text-xs text-slate-500 mt-0.5">{zones.length} monitored zones</p>
            </div>

            {/* Summary */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <div className="card p-4">
                    <div className="text-xs text-slate-500 uppercase mb-1">Critical Zones</div>
                    <div className="text-2xl font-bold text-crisis-red">{zones.filter(z => z.risk_level === 'Critical').length}</div>
                </div>
                <div className="card p-4">
                    <div className="text-xs text-slate-500 uppercase mb-1">High Risk</div>
                    <div className="text-2xl font-bold text-crisis-orange">{zones.filter(z => z.risk_level === 'High').length}</div>
                </div>
                <div className="card p-4">
                    <div className="text-xs text-slate-500 uppercase mb-1">Medium Risk</div>
                    <div className="text-2xl font-bold text-crisis-yellow">{zones.filter(z => z.risk_level === 'Medium').length}</div>
                </div>
                <div className="card p-4">
                    <div className="text-xs text-slate-500 uppercase mb-1">Low Risk</div>
                    <div className="text-2xl font-bold text-crisis-blue">{zones.filter(z => z.risk_level === 'Low').length}</div>
                </div>
            </div>

            {/* Map */}
            <div className="card overflow-hidden" style={{ height: 400 }}>
                <div className="p-3 border-b border-white/5 flex items-center gap-2">
                    <Shield size={14} className="text-crisis-orange" />
                    <span className="text-sm font-semibold text-white">Risk Zone Map</span>
                </div>
                <MapContainer center={[17.420, 78.450]} zoom={12}
                    style={{ height: 'calc(100% - 44px)', width: '100%' }} zoomControl={false}>
                    <TileLayer url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
                        attribution='&copy; CARTO' />
                    {zones.map(z => (
                        <Circle key={z.id} center={[z.latitude, z.longitude]} radius={z.radius * 1000}
                            pathOptions={{ color: riskColor(z.risk_level), fillOpacity: 0.15, weight: 2 }}>
                            <Popup>
                                <div className="text-xs space-y-1">
                                    <div className="font-bold">{z.name}</div>
                                    <div>Risk: {z.risk_level} ({z.risk_score}/100)</div>
                                    <div>Factors: {z.factors.join(', ')}</div>
                                </div>
                            </Popup>
                        </Circle>
                    ))}
                </MapContainer>
            </div>

            {/* Zone List */}
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
                {zones.map(z => (
                    <div key={z.id} className="card card-hover p-4 space-y-3">
                        <div className="flex items-center justify-between">
                            <div className="text-sm font-bold text-white">{z.name}</div>
                            {riskBadge(z.risk_level)}
                        </div>
                        <div className="flex items-center gap-2">
                            <div className="flex-1 h-2 bg-navy-700 rounded-full overflow-hidden">
                                <div className="h-full rounded-full" style={{
                                    width: `${z.risk_score}%`,
                                    background: riskColor(z.risk_level),
                                }} />
                            </div>
                            <span className="text-xs font-mono text-slate-400">{z.risk_score}</span>
                        </div>
                        <div className="space-y-1">
                            {z.factors.map((f, i) => (
                                <div key={i} className="text-xs text-slate-400 flex items-center gap-1">
                                    <AlertTriangle size={10} className="text-crisis-orange shrink-0" /> {f}
                                </div>
                            ))}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
