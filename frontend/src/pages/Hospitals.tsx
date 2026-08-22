/* ─── Hospitals Page ─── */
import { useState, useEffect } from 'react';
import { Building2, Heart, Activity, Thermometer } from 'lucide-react';
import { getHospitals } from '../services/api';
import type { Hospital } from '../types';

const statusBadge = (s: string) => {
    const c = s === 'Available' ? 'badge-available' : s === 'Busy' ? 'badge-high'
        : s === 'Full' ? 'badge-critical' : 'badge-medium';
    return <span className={`badge ${c}`}>{s}</span>;
};

const occBar = (occ: number) => {
    const pct = Math.round(occ * 100);
    const color = pct > 80 ? 'bg-crisis-red' : pct > 60 ? 'bg-crisis-orange' : 'bg-crisis-green';
    return (
        <div className="flex items-center gap-2">
            <div className="flex-1 h-1.5 bg-navy-700 rounded-full overflow-hidden">
                <div className={`h-full rounded-full ${color}`} style={{ width: `${pct}%` }} />
            </div>
            <span className="text-xs font-mono text-slate-400 w-10 text-right">{pct}%</span>
        </div>
    );
};

export default function Hospitals() {
    const [hospitals, setHospitals] = useState<Hospital[]>([]);

    useEffect(() => { getHospitals().then(setHospitals); }, []);

    return (
        <div className="space-y-4">
            <div>
                <h1 className="text-xl font-bold text-white flex items-center gap-2">
                    <Building2 size={22} className="text-crisis-green" /> Hospitals
                </h1>
                <p className="text-xs text-slate-500 mt-0.5">{hospitals.length} hospitals in network</p>
            </div>

            {/* Summary */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <div className="card p-4">
                    <div className="text-xs text-slate-500 uppercase mb-1">Available</div>
                    <div className="text-2xl font-bold text-crisis-green">
                        {hospitals.filter(h => h.status === 'Available').length}
                    </div>
                </div>
                <div className="card p-4">
                    <div className="text-xs text-slate-500 uppercase mb-1">Total ICU Beds</div>
                    <div className="text-2xl font-bold text-crisis-blue">
                        {hospitals.reduce((s, h) => s + h.icu_beds, 0)}
                    </div>
                </div>
                <div className="card p-4">
                    <div className="text-xs text-slate-500 uppercase mb-1">Total Trauma</div>
                    <div className="text-2xl font-bold text-crisis-orange">
                        {hospitals.reduce((s, h) => s + h.trauma_beds, 0)}
                    </div>
                </div>
                <div className="card p-4">
                    <div className="text-xs text-slate-500 uppercase mb-1">Total Burn</div>
                    <div className="text-2xl font-bold text-crisis-red">
                        {hospitals.reduce((s, h) => s + h.burn_capacity, 0)}
                    </div>
                </div>
            </div>

            {/* Hospital Cards */}
            <div className="grid md:grid-cols-2 gap-4">
                {hospitals.map(h => (
                    <div key={h.id} className="card card-hover p-4 space-y-3">
                        <div className="flex items-center justify-between">
                            <div>
                                <div className="text-sm font-bold text-white">{h.name}</div>
                                <div className="text-xs text-slate-500">{h.location}</div>
                            </div>
                            {statusBadge(h.status)}
                        </div>

                        <div className="text-xs text-slate-500">Occupancy</div>
                        {occBar(h.occupancy)}

                        <div className="grid grid-cols-4 gap-2">
                            <div className="bg-navy-800 rounded-lg p-2 text-center">
                                <div className="text-[10px] text-slate-500 uppercase">Emergency</div>
                                <div className="text-sm font-bold text-white">{h.emergency_capacity}</div>
                            </div>
                            <div className="bg-navy-800 rounded-lg p-2 text-center">
                                <div className="text-[10px] text-slate-500 uppercase">ICU</div>
                                <div className="text-sm font-bold text-crisis-blue">{h.icu_beds}</div>
                            </div>
                            <div className="bg-navy-800 rounded-lg p-2 text-center">
                                <div className="text-[10px] text-slate-500 uppercase">Trauma</div>
                                <div className="text-sm font-bold text-crisis-orange">{h.trauma_beds}</div>
                            </div>
                            <div className="bg-navy-800 rounded-lg p-2 text-center">
                                <div className="text-[10px] text-slate-500 uppercase">Burn</div>
                                <div className="text-sm font-bold text-crisis-red">{h.burn_capacity}</div>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
