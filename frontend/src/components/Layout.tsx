/* ─── CrisisFlow Layout ─── */
import { NavLink, Outlet } from 'react-router-dom';
import { useState, useEffect } from 'react';
import {
    LayoutDashboard, AlertTriangle, Truck, Building2, MapPin,
    BarChart3, FileText, RadioTower, Menu, X, Activity,
} from 'lucide-react';
import { getFabricStatus } from '../services/api';
import type { FabricStatus } from '../types';

const NAV = [
    { to: '/', icon: LayoutDashboard, label: 'Dashboard' },
    { to: '/incidents', icon: AlertTriangle, label: 'Incidents' },
    { to: '/resources', icon: Truck, label: 'Resources' },
    { to: '/hospitals', icon: Building2, label: 'Hospitals' },
    { to: '/risk-zones', icon: MapPin, label: 'Risk Zones' },
    { to: '/analytics', icon: BarChart3, label: 'Analytics' },
    { to: '/reports', icon: FileText, label: 'Reports' },
];

export default function Layout() {
    const [fabricStatus, setFabricStatus] = useState<FabricStatus | null>(null);
    const [time, setTime] = useState(new Date());
    const [mobileOpen, setMobileOpen] = useState(false);

    useEffect(() => {
        const t = setInterval(() => setTime(new Date()), 1000);
        return () => clearInterval(t);
    }, []);

    useEffect(() => {
        const load = () => getFabricStatus().then(setFabricStatus).catch(() => { });
        load();
        const t = setInterval(load, 10000);
        return () => clearInterval(t);
    }, []);

    const isConnected = fabricStatus?.overall === 'CONNECTED';

    return (
        <div className="flex h-screen overflow-hidden">
            {/* Sidebar */}
            <aside className={`
        fixed inset-y-0 left-0 z-50 w-60 bg-navy-900 border-r border-white/5
        transform transition-transform duration-200
        lg:relative lg:translate-x-0
        ${mobileOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
                <div className="flex items-center gap-2 px-5 py-4 border-b border-white/5">
                    <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-crisis-red to-crisis-orange flex items-center justify-center text-white font-bold text-sm">
                        CF
                    </div>
                    <div>
                        <h1 className="text-sm font-bold text-white tracking-wide">CrisisFlow</h1>
                        <p className="text-[10px] text-slate-500 uppercase tracking-widest">Command Center</p>
                    </div>
                </div>

                <nav className="px-3 py-4 space-y-1">
                    {NAV.map(n => (
                        <NavLink
                            key={n.to}
                            to={n.to}
                            onClick={() => setMobileOpen(false)}
                            className={({ isActive }) =>
                                `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-all
                ${isActive
                                    ? 'bg-crisis-blue/10 text-crisis-blue border border-crisis-blue/20'
                                    : 'text-slate-400 hover:text-white hover:bg-white/5'}`
                            }
                        >
                            <n.icon size={18} />
                            {n.label}
                        </NavLink>
                    ))}
                </nav>

                {/* Fabric Status Mini */}
                <div className="absolute bottom-0 left-0 right-0 p-3 border-t border-white/5">
                    <div className="card p-3 text-xs space-y-1.5">
                        <div className="flex items-center gap-2 font-semibold text-slate-300 mb-2">
                            <RadioTower size={14} />
                            Microsoft Fabric
                        </div>
                        {(['eventstream', 'eventhouse', 'onelake', 'lakehouse', 'powerbi', 'activator'] as const).map(k => (
                            <div key={k} className="flex justify-between items-center">
                                <span className="capitalize text-slate-500">{k}</span>
                                <span className={fabricStatus?.[k] === 'CONNECTED' ? 'text-crisis-green' : 'text-slate-600'}>
                                    {fabricStatus?.[k] === 'CONNECTED' ? '● CONNECTED' : '○'}
                                </span>
                            </div>
                        ))}
                        <div className="flex justify-between items-center pt-1 border-t border-white/5">
                            <span className="text-slate-500">AI</span>
                            <span className={fabricStatus?.ai === 'CONNECTED' ? 'text-crisis-green' : 'text-crisis-purple'}>
                                {fabricStatus?.ai === 'CONNECTED' ? '● Azure AI' : '● Local Engine'}
                            </span>
                        </div>
                    </div>
                </div>
            </aside>

            {/* Main */}
            <div className="flex-1 flex flex-col overflow-hidden">
                {/* Top Bar */}
                <header className="h-14 border-b border-white/5 bg-navy-900/80 backdrop-blur flex items-center justify-between px-4 shrink-0">
                    <button className="lg:hidden text-slate-400" onClick={() => setMobileOpen(!mobileOpen)}>
                        {mobileOpen ? <X size={20} /> : <Menu size={20} />}
                    </button>

                    <div className="flex items-center gap-6 ml-auto">
                        {/* Live Indicator */}
                        <div className="flex items-center gap-2 text-xs">
                            <span className={`w-2 h-2 rounded-full ${isConnected ? 'bg-crisis-green live-pulse' : 'bg-crisis-orange live-pulse'}`} />
                            <span className={isConnected ? 'text-crisis-green font-semibold' : 'text-crisis-orange font-semibold'}>
                                {isConnected ? 'LIVE' : 'DEMO'}
                            </span>
                        </div>

                        <div className="hidden sm:flex items-center gap-2 text-xs text-slate-500">
                            <Activity size={12} />
                            <span>{isConnected ? 'Fabric Connected' : 'Local Simulation'}</span>
                        </div>

                        <div className="text-xs text-slate-400 font-mono">
                            {time.toLocaleTimeString()}
                        </div>
                    </div>
                </header>

                {/* Content */}
                <main className="flex-1 overflow-y-auto p-4 lg:p-6">
                    <Outlet />
                </main>
            </div>

            {/* Mobile overlay */}
            {mobileOpen && (
                <div className="fixed inset-0 bg-black/50 z-40 lg:hidden" onClick={() => setMobileOpen(false)} />
            )}
        </div>
    );
}
