/* ─── Incidents Page ─── */
import { useState, useEffect } from 'react';
import { AlertTriangle, Plus, Search, Filter, X } from 'lucide-react';
import {
    getIncidents, createIncident, analyzeIncident,
    getRecommendation, dispatchResponse,
} from '../services/api';
import type { Incident, Recommendation } from '../types';

const TYPES = ['Building Fire', 'Road Accident', 'Medical Emergency', 'Flood', 'Industrial Accident'];
const SEVERITIES = ['Auto Detect', 'Low', 'Medium', 'High', 'Critical'];

const severityBadge = (s: string) => {
    const c = s === 'Critical' ? 'badge-critical' : s === 'High' ? 'badge-high'
        : s === 'Medium' ? 'badge-medium' : 'badge-low';
    return <span className={`badge ${c}`}>{s}</span>;
};
const statusBadge = (s: string) => {
    const c = s === 'Dispatched' || s === 'Response In Progress' ? 'badge-dispatched'
        : s === 'Resolved' ? 'badge-available' : s === 'Awaiting Response' ? 'badge-high' : 'badge-medium';
    return <span className={`badge ${c}`}>{s}</span>;
};

export default function Incidents() {
    const [incidents, setIncidents] = useState<Incident[]>([]);
    const [showForm, setShowForm] = useState(false);
    const [search, setSearch] = useState('');
    const [filterType, setFilterType] = useState('');
    const [detail, setDetail] = useState<Incident | null>(null);
    const [rec, setRec] = useState<Recommendation | null>(null);
    const [loading, setLoading] = useState(false);
    const [form, setForm] = useState({
        incident_type: 'Building Fire', location: '', latitude: 17.4435, longitude: 78.3772,
        building: '', floor: 0, people_at_risk: 0, description: '', severity: 'Auto Detect',
    });

    const load = async () => {
        const data = await getIncidents();
        setIncidents(data);
    };
    useEffect(() => { load(); }, []);

    const handleCreate = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        try {
            const inc = await createIncident(form);
            await load();
            setShowForm(false);
            // Auto-analyze
            const result = await analyzeIncident(inc.id);
            await load();
            if (result.recommendation) {
                setDetail(result.incident);
                setRec(result.recommendation);
            }
        } catch (err) { console.error(err); }
        setLoading(false);
    };

    const viewDetail = async (inc: Incident) => {
        setDetail(inc);
        setRec(null);
        try { setRec(await getRecommendation(inc.id)); } catch { }
    };

    const handleDispatch = async () => {
        if (!detail) return;
        setLoading(true);
        try {
            await dispatchResponse(detail.id);
            await load();
            setDetail(prev => prev ? { ...prev, status: 'Dispatched' } : null);
        } catch (e) { console.error(e); }
        setLoading(false);
    };

    const filtered = incidents.filter(i =>
        (i.id + i.incident_type + i.location + i.severity).toLowerCase().includes(search.toLowerCase())
        && (!filterType || i.incident_type === filterType)
    );

    return (
        <div className="space-y-4">
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-xl font-bold text-white flex items-center gap-2">
                        <AlertTriangle size={22} className="text-crisis-red" /> Incidents
                    </h1>
                    <p className="text-xs text-slate-500 mt-0.5">{incidents.length} total incidents</p>
                </div>
                <button onClick={() => setShowForm(true)} className="btn-primary flex items-center gap-2">
                    <Plus size={16} /> Create Emergency
                </button>
            </div>

            {/* Filters */}
            <div className="flex gap-3 flex-wrap">
                <div className="flex items-center gap-2 bg-navy-800 rounded-lg px-3 py-2 flex-1 min-w-[200px]">
                    <Search size={14} className="text-slate-500" />
                    <input value={search} onChange={e => setSearch(e.target.value)}
                        placeholder="Search incidents..." className="bg-transparent text-sm text-white outline-none flex-1" />
                </div>
                <select value={filterType} onChange={e => setFilterType(e.target.value)}
                    className="bg-navy-800 text-sm text-slate-300 rounded-lg px-3 py-2 border border-white/5 outline-none">
                    <option value="">All Types</option>
                    {TYPES.map(t => <option key={t} value={t}>{t}</option>)}
                </select>
            </div>

            {/* Table */}
            <div className="card overflow-x-auto">
                <table className="w-full text-xs">
                    <thead>
                        <tr className="border-b border-white/5 text-slate-500">
                            <th className="text-left p-3 font-medium">ID</th>
                            <th className="text-left p-3 font-medium">Type</th>
                            <th className="text-left p-3 font-medium">Location</th>
                            <th className="text-left p-3 font-medium">Severity</th>
                            <th className="text-left p-3 font-medium">People</th>
                            <th className="text-left p-3 font-medium">Status</th>
                            <th className="text-left p-3 font-medium">Time</th>
                            <th className="text-left p-3 font-medium">Action</th>
                        </tr>
                    </thead>
                    <tbody>
                        {filtered.map(inc => (
                            <tr key={inc.id}
                                className="border-b border-white/3 hover:bg-white/2 transition-colors cursor-pointer"
                                onClick={() => viewDetail(inc)}>
                                <td className="p-3 font-mono text-slate-400">{inc.id}</td>
                                <td className="p-3 text-white">{inc.incident_type}</td>
                                <td className="p-3 text-slate-300">{inc.location}</td>
                                <td className="p-3">{severityBadge(inc.severity)}</td>
                                <td className="p-3 text-slate-300">{inc.people_at_risk}</td>
                                <td className="p-3">{statusBadge(inc.status)}</td>
                                <td className="p-3 text-slate-500">{inc.created_at ? new Date(inc.created_at).toLocaleTimeString() : ''}</td>
                                <td className="p-3">
                                    <button className="text-crisis-blue hover:underline" onClick={e => { e.stopPropagation(); viewDetail(inc); }}>
                                        Details →
                                    </button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
                {filtered.length === 0 && (
                    <div className="p-8 text-center text-slate-600 text-sm">No incidents found</div>
                )}
            </div>

            {/* Detail Panel */}
            {detail && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60" onClick={() => setDetail(null)}>
                    <div className="card w-full max-w-lg max-h-[85vh] overflow-y-auto m-4" onClick={e => e.stopPropagation()}>
                        <div className="p-4 border-b border-white/5 flex items-center justify-between">
                            <div>
                                <div className="text-xs text-slate-500">{detail.id}</div>
                                <div className="text-lg font-bold text-white">{detail.incident_type}</div>
                            </div>
                            <button onClick={() => setDetail(null)} className="text-slate-400 hover:text-white"><X size={20} /></button>
                        </div>
                        <div className="p-4 space-y-3 text-sm">
                            <div className="grid grid-cols-2 gap-3">
                                <div><div className="text-xs text-slate-500">Location</div><div className="text-white">{detail.location}</div></div>
                                <div><div className="text-xs text-slate-500">Severity</div>{severityBadge(detail.severity)}</div>
                                <div><div className="text-xs text-slate-500">People at Risk</div><div className="text-white">{detail.people_at_risk}</div></div>
                                <div><div className="text-xs text-slate-500">Status</div>{statusBadge(detail.status)}</div>
                                {detail.floor && <div><div className="text-xs text-slate-500">Floor</div><div className="text-white">{detail.floor}</div></div>}
                                {detail.spread_risk && <div><div className="text-xs text-slate-500">Spread Risk</div><div className="text-white">{detail.spread_risk}</div></div>}
                            </div>
                            {detail.description && <div><div className="text-xs text-slate-500 mb-1">Description</div><div className="text-slate-300 text-xs">{detail.description}</div></div>}

                            {rec && (
                                <div className="bg-navy-800 rounded-lg p-3 space-y-2 border border-crisis-purple/20">
                                    <div className="text-xs font-semibold text-crisis-purple flex items-center gap-1">🧠 AI RECOMMENDATION</div>
                                    <div className="grid grid-cols-2 gap-2 text-xs">
                                        {rec.fire_station_name && <div><span className="text-slate-500">🚒</span> {rec.fire_station_name}</div>}
                                        {rec.ambulance_id && <div><span className="text-slate-500">🚑</span> {rec.ambulance_id}</div>}
                                        {rec.hospital_name && <div><span className="text-slate-500">🏥</span> {rec.hospital_name}</div>}
                                        {rec.route && <div><span className="text-slate-500">🛣️</span> {rec.route}</div>}
                                    </div>
                                    <div className="flex gap-4">
                                        <div className="text-xs"><span className="text-slate-500">ETA:</span> <span className="text-crisis-cyan font-bold">{rec.eta_minutes} min</span></div>
                                        <div className="text-xs"><span className="text-slate-500">Confidence:</span> <span className="text-crisis-green font-bold">{rec.confidence}%</span></div>
                                    </div>
                                    <div className="space-y-1">{rec.reasons.map((r, i) => (
                                        <div key={i} className="text-xs text-slate-300 flex gap-1"><span className="text-crisis-green">✓</span> {r}</div>
                                    ))}</div>
                                </div>
                            )}

                            {detail.status === 'Awaiting Response' && rec && (
                                <button onClick={handleDispatch} disabled={loading} className="btn-danger w-full">
                                    {loading ? '⏳ Dispatching...' : '🚨 DISPATCH RESPONSE'}
                                </button>
                            )}
                        </div>
                    </div>
                </div>
            )}

            {/* Create Form Modal */}
            {showForm && (
                <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60" onClick={() => setShowForm(false)}>
                    <div className="card w-full max-w-lg max-h-[85vh] overflow-y-auto m-4" onClick={e => e.stopPropagation()}>
                        <div className="p-4 border-b border-white/5 flex items-center justify-between">
                            <h2 className="text-lg font-bold text-white">🚨 Create Emergency</h2>
                            <button onClick={() => setShowForm(false)} className="text-slate-400 hover:text-white"><X size={20} /></button>
                        </div>
                        <form onSubmit={handleCreate} className="p-4 space-y-3">
                            <div>
                                <label className="text-xs text-slate-400 block mb-1">Incident Type</label>
                                <select value={form.incident_type} onChange={e => setForm({ ...form, incident_type: e.target.value })}
                                    className="w-full bg-navy-800 text-white text-sm rounded-lg px-3 py-2 border border-white/5 outline-none">
                                    {TYPES.map(t => <option key={t} value={t}>{t}</option>)}
                                </select>
                            </div>
                            <div>
                                <label className="text-xs text-slate-400 block mb-1">Location</label>
                                <input value={form.location} onChange={e => setForm({ ...form, location: e.target.value })}
                                    required placeholder="e.g. Tower A, Hitech City"
                                    className="w-full bg-navy-800 text-white text-sm rounded-lg px-3 py-2 border border-white/5 outline-none" />
                            </div>
                            <div className="grid grid-cols-2 gap-3">
                                <div>
                                    <label className="text-xs text-slate-400 block mb-1">Latitude</label>
                                    <input type="number" step="0.0001" value={form.latitude}
                                        onChange={e => setForm({ ...form, latitude: parseFloat(e.target.value) || 0 })}
                                        className="w-full bg-navy-800 text-white text-sm rounded-lg px-3 py-2 border border-white/5 outline-none" />
                                </div>
                                <div>
                                    <label className="text-xs text-slate-400 block mb-1">Longitude</label>
                                    <input type="number" step="0.0001" value={form.longitude}
                                        onChange={e => setForm({ ...form, longitude: parseFloat(e.target.value) || 0 })}
                                        className="w-full bg-navy-800 text-white text-sm rounded-lg px-3 py-2 border border-white/5 outline-none" />
                                </div>
                            </div>
                            <div className="grid grid-cols-2 gap-3">
                                <div>
                                    <label className="text-xs text-slate-400 block mb-1">Building</label>
                                    <input value={form.building} onChange={e => setForm({ ...form, building: e.target.value })}
                                        placeholder="Optional"
                                        className="w-full bg-navy-800 text-white text-sm rounded-lg px-3 py-2 border border-white/5 outline-none" />
                                </div>
                                <div>
                                    <label className="text-xs text-slate-400 block mb-1">Floor</label>
                                    <input type="number" value={form.floor} onChange={e => setForm({ ...form, floor: parseInt(e.target.value) || 0 })}
                                        className="w-full bg-navy-800 text-white text-sm rounded-lg px-3 py-2 border border-white/5 outline-none" />
                                </div>
                            </div>
                            <div className="grid grid-cols-2 gap-3">
                                <div>
                                    <label className="text-xs text-slate-400 block mb-1">People at Risk</label>
                                    <input type="number" value={form.people_at_risk} onChange={e => setForm({ ...form, people_at_risk: parseInt(e.target.value) || 0 })}
                                        className="w-full bg-navy-800 text-white text-sm rounded-lg px-3 py-2 border border-white/5 outline-none" />
                                </div>
                                <div>
                                    <label className="text-xs text-slate-400 block mb-1">Severity</label>
                                    <select value={form.severity} onChange={e => setForm({ ...form, severity: e.target.value })}
                                        className="w-full bg-navy-800 text-white text-sm rounded-lg px-3 py-2 border border-white/5 outline-none">
                                        {SEVERITIES.map(s => <option key={s} value={s}>{s}</option>)}
                                    </select>
                                </div>
                            </div>
                            <div>
                                <label className="text-xs text-slate-400 block mb-1">Description</label>
                                <textarea value={form.description} onChange={e => setForm({ ...form, description: e.target.value })}
                                    rows={3} placeholder="Incident details..."
                                    className="w-full bg-navy-800 text-white text-sm rounded-lg px-3 py-2 border border-white/5 outline-none resize-none" />
                            </div>
                            <button type="submit" disabled={loading} className="btn-primary w-full">
                                {loading ? '⏳ Creating...' : '🚨 CREATE INCIDENT'}
                            </button>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}
