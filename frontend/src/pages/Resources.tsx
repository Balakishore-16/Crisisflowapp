import { useState, useEffect } from 'react';
import { Truck, Ambulance as AmbIcon, Building } from 'lucide-react';
import { getAmbulances, getFireStations, getFireTrucks } from '../services/api';
import type { Ambulance, FireStation, FireTruck } from '../types';

const statusBadge = (s: string) => {
    const c = s === 'Available' ? 'badge-available' : s === 'Dispatched' ? 'badge-dispatched'
        : s === 'En Route' ? 'badge-en-route' : s === 'Maintenance' ? 'badge-medium' : 'badge-low';
    return <span className={`badge ${c}`}>{s}</span>;
};

export default function Resources() {
    const [tab, setTab] = useState<'ambulances' | 'fire_trucks' | 'fire_stations'>('ambulances');
    const [ambulances, setAmbulances] = useState<Ambulance[]>([]);
    const [trucks, setTrucks] = useState<FireTruck[]>([]);
    const [stations, setStations] = useState<FireStation[]>([]);

    useEffect(() => {
        Promise.all([getAmbulances(), getFireTrucks(), getFireStations()])
            .then(([a, t, s]) => { setAmbulances(a); setTrucks(t); setStations(s); });
    }, []);

    const tabs = [
        { key: 'ambulances' as const, label: 'Ambulances', icon: AmbIcon, count: ambulances.length },
        { key: 'fire_trucks' as const, label: 'Fire Trucks', icon: Truck, count: trucks.length },
        { key: 'fire_stations' as const, label: 'Fire Stations', icon: Building, count: stations.length },
    ];

    return (
        <div className="space-y-4">
            <div>
                <h1 className="text-xl font-bold text-white flex items-center gap-2">
                    <Truck size={22} className="text-crisis-orange" /> Resources
                </h1>
                <p className="text-xs text-slate-500 mt-0.5">Emergency resource management</p>
            </div>

            {/* Tabs */}
            <div className="flex gap-2">
                {tabs.map(t => (
                    <button key={t.key} onClick={() => setTab(t.key)}
                        className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all
                    ${tab === t.key ? 'bg-crisis-blue/10 text-crisis-blue border border-crisis-blue/20'
                                : 'text-slate-400 hover:text-white bg-navy-800 border border-white/5'}`}>
                        <t.icon size={16} /> {t.label}
                        <span className="text-xs bg-white/5 px-1.5 py-0.5 rounded">{t.count}</span>
                    </button>
                ))}
            </div>

            {/* Ambulances */}
            {tab === 'ambulances' && (
                <div className="card overflow-x-auto">
                    <table className="w-full text-xs">
                        <thead>
                            <tr className="border-b border-white/5 text-slate-500">
                                <th className="text-left p-3 font-medium">ID</th>
                                <th className="text-left p-3 font-medium">Call Sign</th>
                                <th className="text-left p-3 font-medium">Location</th>
                                <th className="text-left p-3 font-medium">Status</th>
                                <th className="text-left p-3 font-medium">Equipment</th>
                                <th className="text-left p-3 font-medium">Capacity</th>
                                <th className="text-left p-3 font-medium">Incident</th>
                            </tr>
                        </thead>
                        <tbody>
                            {ambulances.map(a => (
                                <tr key={a.id} className="border-b border-white/3 hover:bg-white/2 transition-colors">
                                    <td className="p-3 font-mono text-slate-400">{a.id}</td>
                                    <td className="p-3 text-white font-medium">{a.call_sign}</td>
                                    <td className="p-3 text-slate-300">{a.location}</td>
                                    <td className="p-3">{statusBadge(a.status)}</td>
                                    <td className="p-3 text-slate-400">{(a.equipment || []).join(', ')}</td>
                                    <td className="p-3 text-slate-300">{a.capacity}</td>
                                    <td className="p-3 font-mono text-slate-500">{a.current_incident_id || '—'}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}

            {/* Fire Trucks */}
            {tab === 'fire_trucks' && (
                <div className="card overflow-x-auto">
                    <table className="w-full text-xs">
                        <thead>
                            <tr className="border-b border-white/5 text-slate-500">
                                <th className="text-left p-3 font-medium">ID</th>
                                <th className="text-left p-3 font-medium">Call Sign</th>
                                <th className="text-left p-3 font-medium">Station</th>
                                <th className="text-left p-3 font-medium">Location</th>
                                <th className="text-left p-3 font-medium">Status</th>
                                <th className="text-left p-3 font-medium">Equipment</th>
                                <th className="text-left p-3 font-medium">Incident</th>
                            </tr>
                        </thead>
                        <tbody>
                            {trucks.map(t => (
                                <tr key={t.id} className="border-b border-white/3 hover:bg-white/2 transition-colors">
                                    <td className="p-3 font-mono text-slate-400">{t.id}</td>
                                    <td className="p-3 text-white font-medium">{t.call_sign}</td>
                                    <td className="p-3 text-slate-400">{t.station_id}</td>
                                    <td className="p-3 text-slate-300">{t.location}</td>
                                    <td className="p-3">{statusBadge(t.status)}</td>
                                    <td className="p-3 text-slate-400">{(t.equipment || []).join(', ')}</td>
                                    <td className="p-3 font-mono text-slate-500">{t.current_incident_id || '—'}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}

            {/* Fire Stations */}
            {tab === 'fire_stations' && (
                <div className="card overflow-x-auto">
                    <table className="w-full text-xs">
                        <thead>
                            <tr className="border-b border-white/5 text-slate-500">
                                <th className="text-left p-3 font-medium">ID</th>
                                <th className="text-left p-3 font-medium">Name</th>
                                <th className="text-left p-3 font-medium">Location</th>
                                <th className="text-left p-3 font-medium">Available Trucks</th>
                                <th className="text-left p-3 font-medium">Status</th>
                            </tr>
                        </thead>
                        <tbody>
                            {stations.map(s => (
                                <tr key={s.id} className="border-b border-white/3 hover:bg-white/2 transition-colors">
                                    <td className="p-3 font-mono text-slate-400">{s.id}</td>
                                    <td className="p-3 text-white font-medium">{s.name}</td>
                                    <td className="p-3 text-slate-300">{s.location}</td>
                                    <td className="p-3 text-crisis-green font-bold">{s.available_trucks}</td>
                                    <td className="p-3">{statusBadge(s.status)}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}

            {/* Summary Cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="card p-4">
                    <div className="text-xs text-slate-500 uppercase mb-1">Ambulances Available</div>
                    <div className="text-2xl font-bold text-crisis-blue">
                        {ambulances.filter(a => a.status === 'Available').length}
                        <span className="text-sm text-slate-500 font-normal"> / {ambulances.length}</span>
                    </div>
                </div>
                <div className="card p-4">
                    <div className="text-xs text-slate-500 uppercase mb-1">Fire Trucks Available</div>
                    <div className="text-2xl font-bold text-crisis-orange">
                        {trucks.filter(t => t.status === 'Available').length}
                        <span className="text-sm text-slate-500 font-normal"> / {trucks.length}</span>
                    </div>
                </div>
                <div className="card p-4">
                    <div className="text-xs text-slate-500 uppercase mb-1">Stations Operational</div>
                    <div className="text-2xl font-bold text-crisis-green">
                        {stations.filter(s => s.status === 'Available').length}
                        <span className="text-sm text-slate-500 font-normal"> / {stations.length}</span>
                    </div>
                </div>
            </div>
        </div>
    );
}
