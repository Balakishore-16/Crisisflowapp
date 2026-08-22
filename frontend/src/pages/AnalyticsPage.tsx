/* ─── Analytics Page ─── */
import { useState, useEffect } from 'react';
import { BarChart3 } from 'lucide-react';
import {
    BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
    PieChart, Pie, Cell, Legend,
} from 'recharts';
import { getAnalytics } from '../services/api';
import type { Analytics } from '../types';

const COLORS = ['#ef4444', '#f97316', '#eab308', '#22c55e', '#3b82f6', '#a855f7', '#06b6d4'];

export default function AnalyticsPage() {
    const [data, setData] = useState<Analytics | null>(null);

    useEffect(() => { getAnalytics().then(setData); }, []);

    if (!data) return <div className="text-slate-500 text-center py-20">Loading analytics...</div>;

    // Transform data for charts
    const typeData = Object.entries(data.incidents_by_type).map(([name, value]) => ({ name, value }));
    const sevData = Object.entries(data.incidents_by_severity).map(([name, value]) => ({ name, value }));
    const statusData = Object.entries(data.incidents_by_status).map(([name, value]) => ({ name, value }));
    const hospData = data.hospital_capacity.map(h => ({
        name: h.name.length > 15 ? h.name.substring(0, 15) + '…' : h.name,
        occupancy: h.occupancy,
        emergency: h.emergency_capacity,
        icu: h.icu_beds,
        trauma: h.trauma_beds,
    }));

    const utilData = Object.entries(data.resource_utilization).map(([key, val]) => ({
        name: key.replace('_', ' '),
        utilization: val.utilization,
        available: val.available,
        total: val.total,
    }));

    return (
        <div className="space-y-4">
            <div>
                <h1 className="text-xl font-bold text-white flex items-center gap-2">
                    <BarChart3 size={22} className="text-crisis-purple" /> Analytics
                </h1>
                <p className="text-xs text-slate-500 mt-0.5">Emergency intelligence insights — all data from backend</p>
            </div>

            {/* KPI Row */}
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-3">
                {[
                    { label: 'Total Incidents', value: data.total_incidents, color: 'text-white' },
                    { label: 'Active', value: data.active_incidents, color: 'text-crisis-red' },
                    { label: 'Critical', value: data.critical_incidents, color: 'text-crisis-orange' },
                    { label: 'Resolved', value: data.resolved_incidents, color: 'text-crisis-green' },
                    { label: 'Dispatches', value: data.total_dispatches, color: 'text-crisis-purple' },
                    { label: 'Avg Response', value: `${data.avg_response_time} min`, color: 'text-crisis-cyan' },
                ].map(k => (
                    <div key={k.label} className="card p-4">
                        <div className="text-xs text-slate-500 uppercase mb-1">{k.label}</div>
                        <div className={`text-2xl font-bold ${k.color}`}>{k.value}</div>
                    </div>
                ))}
            </div>

            {/* Charts Row 1 */}
            <div className="grid lg:grid-cols-2 gap-4">
                {/* Incidents by Type */}
                <div className="card p-4">
                    <h3 className="text-sm font-semibold text-white mb-4">Incidents by Type</h3>
                    <ResponsiveContainer width="100%" height={280}>
                        <BarChart data={typeData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                            <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#94a3b8' }} angle={-20} textAnchor="end" height={60} />
                            <YAxis tick={{ fontSize: 10, fill: '#94a3b8' }} />
                            <Tooltip contentStyle={{ background: '#131a2e', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, fontSize: 12 }} />
                            <Bar dataKey="value" fill="#3b82f6" radius={[4, 4, 0, 0]}>
                                {typeData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                            </Bar>
                        </BarChart>
                    </ResponsiveContainer>
                </div>

                {/* Severity Distribution */}
                <div className="card p-4">
                    <h3 className="text-sm font-semibold text-white mb-4">Severity Distribution</h3>
                    <ResponsiveContainer width="100%" height={280}>
                        <PieChart>
                            <Pie data={sevData} cx="50%" cy="50%" innerRadius={60} outerRadius={110}
                                dataKey="value" nameKey="name" paddingAngle={3}>
                                {sevData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                            </Pie>
                            <Tooltip contentStyle={{ background: '#131a2e', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, fontSize: 12 }} />
                            <Legend wrapperStyle={{ fontSize: 11, color: '#94a3b8' }} />
                        </PieChart>
                    </ResponsiveContainer>
                </div>
            </div>

            {/* Charts Row 2 */}
            <div className="grid lg:grid-cols-2 gap-4">
                {/* Hospital Capacity */}
                <div className="card p-4">
                    <h3 className="text-sm font-semibold text-white mb-4">Hospital Occupancy (%)</h3>
                    <ResponsiveContainer width="100%" height={280}>
                        <BarChart data={hospData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                            <XAxis dataKey="name" tick={{ fontSize: 9, fill: '#94a3b8' }} angle={-25} textAnchor="end" height={60} />
                            <YAxis tick={{ fontSize: 10, fill: '#94a3b8' }} domain={[0, 100]} />
                            <Tooltip contentStyle={{ background: '#131a2e', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, fontSize: 12 }} />
                            <Bar dataKey="occupancy" fill="#f97316" radius={[4, 4, 0, 0]}>
                                {hospData.map((h, i) => (
                                    <Cell key={i} fill={h.occupancy > 80 ? '#ef4444' : h.occupancy > 60 ? '#f97316' : '#22c55e'} />
                                ))}
                            </Bar>
                        </BarChart>
                    </ResponsiveContainer>
                </div>

                {/* Resource Utilization */}
                <div className="card p-4">
                    <h3 className="text-sm font-semibold text-white mb-4">Resource Utilization</h3>
                    <ResponsiveContainer width="100%" height={280}>
                        <BarChart data={utilData} layout="vertical" margin={{ top: 5, right: 20, bottom: 5, left: 40 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                            <XAxis type="number" domain={[0, 100]} tick={{ fontSize: 10, fill: '#94a3b8' }} />
                            <YAxis dataKey="name" type="category" tick={{ fontSize: 11, fill: '#94a3b8' }} width={100} />
                            <Tooltip contentStyle={{ background: '#131a2e', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, fontSize: 12 }}
                                formatter={(v: any) => [`${v}%`, 'Utilization']} />
                            <Bar dataKey="utilization" fill="#a855f7" radius={[0, 4, 4, 0]} />
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </div>

            {/* Status Distribution */}
            <div className="card p-4">
                <h3 className="text-sm font-semibold text-white mb-4">Incidents by Status</h3>
                <ResponsiveContainer width="100%" height={250}>
                    <BarChart data={statusData} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.05)" />
                        <XAxis dataKey="name" tick={{ fontSize: 10, fill: '#94a3b8' }} angle={-20} textAnchor="end" height={60} />
                        <YAxis tick={{ fontSize: 10, fill: '#94a3b8' }} />
                        <Tooltip contentStyle={{ background: '#131a2e', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, fontSize: 12 }} />
                        <Bar dataKey="value" fill="#06b6d4" radius={[4, 4, 0, 0]}>
                            {statusData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                        </Bar>
                    </BarChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
}
