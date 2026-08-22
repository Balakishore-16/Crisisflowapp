/* ─── CrisisFlow Command Center — Incidents Page ─── */
import { useState, useEffect, useMemo, useRef, useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import {
    AlertTriangle, Plus, Search, X, Download, CheckCircle, Send,
    ChevronLeft, ChevronRight, Clock, MapPin, Brain, Truck, Building2, Activity,
} from 'lucide-react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';

import {
    getIncidents, createIncident, analyzeIncident,
    getRecommendation, dispatchResponse, bulkAcknowledge,
    bulkDispatch, getIncidentTimeline,
} from '../services/api';
import { useWebSocket } from '../hooks/useWebSocket';
import type { Incident, Recommendation, TimelineEvent } from '../types';

// Constants
const TYPES = [
    'Building Fire',
    'Road Accident',
    'Medical Emergency',
    'Flood',
    'Industrial Accident',
];

const SEVERITIES = ['Critical', 'High', 'Medium', 'Low'];

const STATUSES = [
    'Detected',
    'Analyzing',
    'Awaiting Response',
    'Dispatched',
    'Response In Progress',
    'Resolved',
];

const PAGE_SIZE_OPTIONS = [10, 25, 50, 100];

// Custom Leaflet Pin Maker
const makeMapIcon = (color: string, emoji: string) =>
    L.divIcon({
        className: '',
        html: `<div style="background:${color};width:28px;height:28px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:14px;border:2px solid rgba(255,255,255,0.8);box-shadow:0 2px 6px rgba(0,0,0,0.4)">${emoji}</div>`,
        iconSize: [28, 28],
        iconAnchor: [14, 14],
    });

const getMapIcon = (type: string) => {
    if (type.includes('Fire')) return makeMapIcon('#ef4444', '🔥');
    if (type.includes('Accident')) return makeMapIcon('#f97316', '🚗');
    if (type.includes('Medical')) return makeMapIcon('#a855f7', '🏥');
    if (type.includes('Flood')) return makeMapIcon('#3b82f6', '🌊');
    return makeMapIcon('#eab308', '🏭');
};

function MiniMapController({ center }: { center: [number, number] }) {
    const map = useMap();
    useEffect(() => {
        map.setView(center, 14);
    }, [center, map]);
    return null;
}

// Badge Helpers
const severityBadge = (s: string) => {
    const c = s === 'Critical' ? 'badge-critical'
        : s === 'High' ? 'badge-high'
            : s === 'Medium' ? 'badge-medium' : 'badge-low';
    return <span className={`badge ${c}`}>{s}</span>;
};

const statusBadge = (s: string) => {
    const c = s === 'Dispatched' || s === 'Response In Progress' ? 'badge-dispatched'
        : s === 'Resolved' ? 'badge-available'
            : s === 'Awaiting Response' ? 'badge-high' : 'badge-medium';
    return <span className={`badge ${c}`}>{s}</span>;
};

// Time formatters
function formatRelativeTime(dateString?: string, now = new Date()): string {
    if (!dateString) return '—';
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return dateString;
    const diffSec = Math.floor((now.getTime() - date.getTime()) / 1000);
    if (diffSec < 10) return 'just now';
    if (diffSec < 60) return `${diffSec}s ago`;
    const diffMin = Math.floor(diffSec / 60);
    if (diffMin < 60) return `${diffMin}m ago`;
    const diffHours = Math.floor(diffMin / 60);
    if (diffHours < 24) return `${diffHours}h ago`;
    const diffDays = Math.floor(diffHours / 24);
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
}

function formatAbsoluteTime(dateString?: string): string {
    if (!dateString) return '—';
    const date = new Date(dateString);
    if (isNaN(date.getTime())) return dateString;
    return date.toLocaleString();
}

// CSV Exporter
function exportToCSV(incidentsToExport: Incident[], filenamePrefix = 'crisisflow-incidents') {
    const headers = [
        'ID', 'Type', 'Severity', 'Status', 'Zone', 'Location',
        'People At Risk', 'Description', 'Created At', 'Updated At'
    ];
    const escape = (v: any) => {
        if (v === null || v === undefined) return '""';
        const str = String(v).replace(/"/g, '""');
        return `"${str}"`;
    };

    const rows = incidentsToExport.map(inc => [
        escape(inc.id),
        escape(inc.incident_type),
        escape(inc.severity),
        escape(inc.status),
        escape(inc.zone || 'Central'),
        escape(inc.location),
        escape(inc.people_at_risk),
        escape(inc.description || ''),
        escape(inc.created_at || ''),
        escape(inc.updated_at || ''),
    ].join(','));

    const csvContent = [headers.join(','), ...rows].join('\r\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    const dateStr = new Date().toISOString().split('T')[0];
    link.setAttribute('href', url);
    link.setAttribute('download', `${filenamePrefix}-${dateStr}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
}

export default function Incidents() {
    const [searchParams, setSearchParams] = useSearchParams();

    // Data states
    const [incidents, setIncidents] = useState<Incident[]>([]);
    const [loading, setLoading] = useState(false);
    const [initialLoaded, setInitialLoaded] = useState(false);
    const [notification, setNotification] = useState<{ type: 'success' | 'error' | 'info'; message: string } | null>(null);

    // Filter states initialized from URL params
    const searchParam = searchParams.get('search') || '';
    const typeParam = searchParams.get('type') || '';
    const severityParam = searchParams.get('severity') || '';
    const statusParam = searchParams.get('status') || '';

    const [search, setSearch] = useState(searchParam);
    const [filterType, setFilterType] = useState(typeParam);
    const [filterSeverity, setFilterSeverity] = useState(severityParam);
    const [filterStatus, setFilterStatus] = useState(statusParam);

    // Pagination
    const [page, setPage] = useState(1);
    const [pageSize, setPageSize] = useState(25);

    // Selection
    const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
    const masterCheckboxRef = useRef<HTMLInputElement | null>(null);

    // Time display mode
    const [timeMode, setTimeMode] = useState<'relative' | 'absolute'>('relative');
    const [currentTime, setCurrentTime] = useState(new Date());

    // Drawer state
    const [drawerIncident, setDrawerIncident] = useState<Incident | null>(null);
    const [drawerRec, setDrawerRec] = useState<Recommendation | null>(null);
    const [drawerTimeline, setDrawerTimeline] = useState<TimelineEvent[]>([]);
    const [drawerLoading, setDrawerLoading] = useState(false);
    const [dispatchingId, setDispatchingId] = useState<string | null>(null);
    const drawerRef = useRef<HTMLDivElement | null>(null);

    // Create Incident Modal
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [createForm, setCreateForm] = useState({
        incident_type: 'Building Fire', location: '', zone: 'HITEC City',
        latitude: 17.4486, longitude: 78.3772, building: '', floor: 0,
        people_at_risk: 0, description: '', severity: 'Auto Detect',
    });

    // Bulk operation in-flight
    const [bulkLoading, setBulkLoading] = useState(false);

    // Shared relative time ticker (updates every 10 seconds for all rows)
    useEffect(() => {
        const interval = setInterval(() => setCurrentTime(new Date()), 10000);
        return () => clearInterval(interval);
    }, []);

    // Load incidents
    const loadData = useCallback(async (quiet = false) => {
        if (!quiet) setLoading(true);
        try {
            const data = await getIncidents();
            setIncidents(data);
            setInitialLoaded(true);

            // Reconcile selections (remove any IDs that no longer exist)
            setSelectedIds(prev => {
                const existingIds = new Set(data.map(d => d.id));
                const next = new Set<string>();
                prev.forEach(id => {
                    if (existingIds.has(id)) next.add(id);
                });
                return next;
            });
        } catch (err: any) {
            console.error('Failed to load incidents:', err);
            setNotification({ type: 'error', message: 'Unable to load incidents from server. Please retry.' });
        } finally {
            if (!quiet) setLoading(false);
        }
    }, []);

    useEffect(() => {
        loadData();
    }, [loadData]);

    // WebSocket real-time subscription
    useWebSocket((event) => {
        if (event.event_type === 'INCIDENT_CREATED' || event.event_type === 'INCIDENT_UPDATED' || event.event_type === 'DISPATCH_CREATED') {
            loadData(true);
            // If the drawer is currently open for the affected incident, refresh drawer details
            if (drawerIncident && event.data && (event.data.id === drawerIncident.id || event.data.incident_id === drawerIncident.id)) {
                refreshDrawerData(drawerIncident.id);
            }
        }
    });

    // Synchronize filters with URL search params
    useEffect(() => {
        const params: Record<string, string> = {};
        if (search.trim()) params.search = search.trim();
        if (filterType) params.type = filterType;
        if (filterSeverity) params.severity = filterSeverity;
        if (filterStatus) params.status = filterStatus;

        setSearchParams(params, { replace: true });
        setPage(1); // Reset to page 1 on filter modification
    }, [search, filterType, filterSeverity, filterStatus, setSearchParams]);

    // Filter computation (AND condition)
    const filteredIncidents = useMemo(() => {
        return incidents.filter(inc => {
            if (search.trim()) {
                const term = search.toLowerCase().trim();
                const matchId = (inc.id || '').toLowerCase().includes(term);
                const matchType = (inc.incident_type || '').toLowerCase().includes(term);
                const matchLoc = (inc.location || '').toLowerCase().includes(term);
                const matchZone = (inc.zone || '').toLowerCase().includes(term);
                const matchDesc = (inc.description || '').toLowerCase().includes(term);
                const matchSev = (inc.severity || '').toLowerCase().includes(term);
                if (!matchId && !matchType && !matchLoc && !matchZone && !matchDesc && !matchSev) {
                    return false;
                }
            }
            if (filterType && inc.incident_type !== filterType) return false;
            if (filterSeverity && inc.severity !== filterSeverity) return false;
            if (filterStatus && inc.status !== filterStatus) return false;
            return true;
        });
    }, [incidents, search, filterType, filterSeverity, filterStatus]);

    // Pagination computations
    const totalRecords = filteredIncidents.length;
    const totalPages = Math.max(1, Math.ceil(totalRecords / pageSize));
    const safePage = Math.min(page, totalPages);

    const paginatedIncidents = useMemo(() => {
        const start = (safePage - 1) * pageSize;
        return filteredIncidents.slice(start, start + pageSize);
    }, [filteredIncidents, safePage, pageSize]);

    // Page-scoped Selection Logic
    const currentPageIds = useMemo(() => paginatedIncidents.map(i => i.id), [paginatedIncidents]);
    const isAllCurrentPageSelected = currentPageIds.length > 0 && currentPageIds.every(id => selectedIds.has(id));
    const isSomeCurrentPageSelected = currentPageIds.some(id => selectedIds.has(id)) && !isAllCurrentPageSelected;

    // Master checkbox tri-state sync
    useEffect(() => {
        if (masterCheckboxRef.current) {
            masterCheckboxRef.current.indeterminate = isSomeCurrentPageSelected;
        }
    }, [isSomeCurrentPageSelected]);

    const handleSelectAllCurrentPage = () => {
        setSelectedIds(prev => {
            const next = new Set(prev);
            if (isAllCurrentPageSelected) {
                currentPageIds.forEach(id => next.delete(id));
            } else {
                currentPageIds.forEach(id => next.add(id));
            }
            return next;
        });
    };

    const handleToggleRow = (id: string, e: React.MouseEvent) => {
        e.stopPropagation();
        setSelectedIds(prev => {
            const next = new Set(prev);
            if (next.has(id)) next.delete(id);
            else next.add(id);
            return next;
        });
    };

    const handleClearSelection = () => {
        setSelectedIds(new Set());
    };

    const handleClearFilters = () => {
        setSearch('');
        setFilterType('');
        setFilterSeverity('');
        setFilterStatus('');
    };

    // Quick-View Drawer Data Fetching
    const refreshDrawerData = async (incidentId: string) => {
        try {
            const [recData, timelineData] = await Promise.all([
                getRecommendation(incidentId).catch(() => null),
                getIncidentTimeline(incidentId).catch(() => []),
            ]);
            setDrawerRec(recData);
            setDrawerTimeline(timelineData);
        } catch (e) {
            console.error('Drawer refresh error:', e);
        }
    };

    const openDrawer = async (inc: Incident) => {
        setDrawerIncident(inc);
        setDrawerRec(null);
        setDrawerTimeline([]);
        setDrawerLoading(true);
        try {
            const [recData, timelineData] = await Promise.all([
                getRecommendation(inc.id).catch(() => null),
                getIncidentTimeline(inc.id).catch(() => []),
            ]);
            setDrawerRec(recData);
            setDrawerTimeline(timelineData);
        } catch (e) {
            console.error('Error loading incident details:', e);
        } finally {
            setDrawerLoading(false);
        }
    };

    const closeDrawer = () => {
        setDrawerIncident(null);
        setDrawerRec(null);
        setDrawerTimeline([]);
    };

    // ESC key closes drawer
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.key === 'Escape') {
                if (drawerIncident) closeDrawer();
                if (showCreateModal) setShowCreateModal(false);
            }
        };
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [drawerIncident, showCreateModal]);

    // Bulk Operations
    const handleBulkAcknowledge = async () => {
        if (selectedIds.size === 0) return;
        setBulkLoading(true);
        try {
            const ids = Array.from(selectedIds);
            const res = await bulkAcknowledge(ids);
            await loadData(true);
            setNotification({
                type: res.failed.length > 0 ? 'info' : 'success',
                message: res.message || `${res.successful.length} incidents acknowledged.`,
            });
            handleClearSelection();
        } catch (err: any) {
            console.error('Bulk acknowledge error:', err);
            setNotification({ type: 'error', message: 'Bulk acknowledgement failed.' });
        } finally {
            setBulkLoading(false);
        }
    };

    const handleBulkDispatch = async () => {
        if (selectedIds.size === 0) return;
        setBulkLoading(true);
        try {
            const ids = Array.from(selectedIds);
            const res = await bulkDispatch(ids);
            await loadData(true);
            setNotification({
                type: res.failed.length > 0 ? 'info' : 'success',
                message: res.message || `${res.successful.length} incidents dispatched.`,
            });
            handleClearSelection();
        } catch (err: any) {
            console.error('Bulk dispatch error:', err);
            setNotification({ type: 'error', message: 'Bulk dispatch failed.' });
        } finally {
            setBulkLoading(false);
        }
    };

    const handleExportCSV = () => {
        const itemsToExport = selectedIds.size > 0
            ? incidents.filter(i => selectedIds.has(i.id))
            : filteredIncidents;
        exportToCSV(itemsToExport);
        setNotification({
            type: 'success',
            message: `Exported ${itemsToExport.length} incident(s) to CSV.`,
        });
    };

    // Single Dispatch from Drawer
    const handleDrawerDispatch = async (incId: string) => {
        setDispatchingId(incId);
        try {
            await dispatchResponse(incId);
            await loadData(true);
            await refreshDrawerData(incId);
            setDrawerIncident(prev => prev ? { ...prev, status: 'Dispatched' } : null);
            setNotification({ type: 'success', message: `Emergency response dispatched for ${incId}` });
        } catch (err: any) {
            console.error('Dispatch error:', err);
            setNotification({ type: 'error', message: `Failed to dispatch response for ${incId}` });
        } finally {
            setDispatchingId(null);
        }
    };

    // Create Incident Handler
    const handleCreateSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setLoading(true);
        try {
            const created = await createIncident(createForm);
            setShowCreateModal(false);
            setNotification({ type: 'success', message: `Incident ${created.id} logged successfully.` });
            await loadData(true);
            // Auto analyze & open drawer
            const analyzed = await analyzeIncident(created.id);
            await loadData(true);
            openDrawer(analyzed.incident || created);
        } catch (err: any) {
            console.error('Incident creation failed:', err);
            setNotification({ type: 'error', message: 'Failed to create incident.' });
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="space-y-4 relative">
            {/* Header & Title Bar */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div>
                    <h1 className="text-xl font-bold text-white flex items-center gap-2">
                        <AlertTriangle size={22} className="text-crisis-red" /> Incidents Command Center
                    </h1>
                    <p className="text-xs text-slate-500 mt-0.5">
                        {totalRecords} incident(s) matched | {incidents.length} total operational records
                    </p>
                </div>

                <div className="flex items-center gap-2 flex-wrap">
                    {/* Absolute / Relative Time Toggle */}
                    <div className="flex items-center bg-navy-800 rounded-lg p-0.5 border border-white/5 text-xs">
                        <span className="px-2 text-slate-400 font-medium">Time:</span>
                        <button
                            type="button"
                            onClick={() => setTimeMode('relative')}
                            className={`px-2.5 py-1 rounded-md transition-colors font-medium ${timeMode === 'relative' ? 'bg-crisis-blue text-white' : 'text-slate-400 hover:text-slate-200'}`}
                            aria-label="Toggle relative time"
                        >
                            Relative
                        </button>
                        <button
                            type="button"
                            onClick={() => setTimeMode('absolute')}
                            className={`px-2.5 py-1 rounded-md transition-colors font-medium ${timeMode === 'absolute' ? 'bg-crisis-blue text-white' : 'text-slate-400 hover:text-slate-200'}`}
                            aria-label="Toggle absolute time"
                        >
                            Absolute
                        </button>
                    </div>

                    <button
                        onClick={handleExportCSV}
                        className="flex items-center gap-1.5 px-3 py-2 rounded-lg bg-navy-800 hover:bg-navy-700 text-slate-300 text-xs font-semibold border border-white/5 transition-colors"
                        title="Export filtered incidents to CSV"
                        aria-label="Export to CSV"
                    >
                        <Download size={14} /> Export CSV
                    </button>

                    <button
                        onClick={() => setShowCreateModal(true)}
                        className="btn-primary flex items-center gap-2 text-xs py-2 px-3.5"
                        aria-label="Create emergency incident"
                    >
                        <Plus size={16} /> Log Incident
                    </button>
                </div>
            </div>

            {/* Notification Banner */}
            {notification && (
                <div className={`p-3 rounded-lg flex items-center justify-between text-xs transition-all ${notification.type === 'error' ? 'bg-red-500/15 border border-red-500/30 text-red-400' : notification.type === 'success' ? 'bg-green-500/15 border border-green-500/30 text-green-400' : 'bg-blue-500/15 border border-blue-500/30 text-blue-400'}`}>
                    <div className="flex items-center gap-2 font-medium">
                        {notification.type === 'error' ? <AlertTriangle size={15} /> : <CheckCircle size={15} />}
                        {notification.message}
                    </div>
                    <button onClick={() => setNotification(null)} className="hover:opacity-70 text-slate-400">
                        <X size={14} />
                    </button>
                </div>
            )}

            {/* Advanced Filters Toolbar */}
            <div className="card p-3 space-y-3">
                <div className="flex flex-wrap gap-2.5 items-center">
                    {/* Search Bar */}
                    <div className="flex items-center gap-2 bg-navy-800 rounded-lg px-3 py-2 flex-1 min-w-[220px] border border-white/5">
                        <Search size={14} className="text-slate-500 shrink-0" />
                        <input
                            value={search}
                            onChange={e => setSearch(e.target.value)}
                            placeholder="Search by ID, zone, type, location..."
                            className="bg-transparent text-xs text-white outline-none flex-1 placeholder:text-slate-500"
                            aria-label="Search incidents"
                        />
                        {search && (
                            <button onClick={() => setSearch('')} className="text-slate-400 hover:text-white" aria-label="Clear search">
                                <X size={13} />
                            </button>
                        )}
                    </div>

                    {/* Type Filter */}
                    <select
                        value={filterType}
                        onChange={e => setFilterType(e.target.value)}
                        className="bg-navy-800 text-xs text-slate-300 rounded-lg px-3 py-2 border border-white/5 outline-none cursor-pointer"
                        aria-label="Filter by type"
                    >
                        <option value="">All Types</option>
                        {TYPES.map(t => <option key={t} value={t}>{t}</option>)}
                    </select>

                    {/* Severity Filter */}
                    <select
                        value={filterSeverity}
                        onChange={e => setFilterSeverity(e.target.value)}
                        className="bg-navy-800 text-xs text-slate-300 rounded-lg px-3 py-2 border border-white/5 outline-none cursor-pointer"
                        aria-label="Filter by severity"
                    >
                        <option value="">All Severities</option>
                        {SEVERITIES.map(s => <option key={s} value={s}>{s}</option>)}
                    </select>

                    {/* Status Filter */}
                    <select
                        value={filterStatus}
                        onChange={e => setFilterStatus(e.target.value)}
                        className="bg-navy-800 text-xs text-slate-300 rounded-lg px-3 py-2 border border-white/5 outline-none cursor-pointer"
                        aria-label="Filter by status"
                    >
                        <option value="">All Statuses</option>
                        {STATUSES.map(st => <option key={st} value={st}>{st}</option>)}
                    </select>

                    {/* Clear Filters Button */}
                    {(search || filterType || filterSeverity || filterStatus) && (
                        <button
                            onClick={handleClearFilters}
                            className="text-xs text-crisis-red hover:underline flex items-center gap-1 font-medium px-2 py-1"
                            aria-label="Clear all active filters"
                        >
                            <X size={12} /> Clear Filters
                        </button>
                    )}
                </div>
            </div>

            {/* Floating Bulk Action Toolbar */}
            {selectedIds.size > 0 && (
                <div className="sticky top-2 z-20 bg-navy-900/95 backdrop-blur border border-crisis-blue/30 rounded-xl p-3 shadow-xl flex flex-wrap items-center justify-between gap-3 animate-in fade-in slide-in-from-top-2">
                    <div className="flex items-center gap-2">
                        <span className="w-2.5 h-2.5 rounded-full bg-crisis-blue animate-pulse" />
                        <span className="text-xs font-bold text-white">
                            {selectedIds.size} incident{selectedIds.size > 1 ? 's' : ''} selected
                        </span>
                        <span className="text-[11px] text-slate-500">
                            (Page {safePage} of {totalPages})
                        </span>
                    </div>

                    <div className="flex items-center gap-2 flex-wrap">
                        <button
                            onClick={handleBulkAcknowledge}
                            disabled={bulkLoading}
                            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-navy-800 hover:bg-navy-700 text-slate-200 text-xs font-semibold border border-white/10 transition-colors disabled:opacity-50"
                            aria-label="Acknowledge selected incidents"
                        >
                            <CheckCircle size={14} className="text-crisis-green" />
                            {bulkLoading ? 'Processing...' : 'Acknowledge Selected'}
                        </button>

                        <button
                            onClick={handleBulkDispatch}
                            disabled={bulkLoading}
                            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-crisis-red/90 hover:bg-crisis-red text-white text-xs font-semibold shadow-md transition-colors disabled:opacity-50"
                            aria-label="Batch dispatch response"
                        >
                            <Send size={14} />
                            {bulkLoading ? 'Dispatching...' : 'Batch Dispatch'}
                        </button>

                        <button
                            onClick={handleExportCSV}
                            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-navy-800 hover:bg-navy-700 text-slate-300 text-xs font-semibold border border-white/10 transition-colors"
                            aria-label="Export selected records to CSV"
                        >
                            <Download size={14} /> Export Selected
                        </button>

                        <button
                            onClick={handleClearSelection}
                            className="text-xs text-slate-400 hover:text-white px-2 py-1.5 transition-colors"
                            aria-label="Clear selection"
                        >
                            Deselect All
                        </button>
                    </div>
                </div>
            )}

            {/* Table Container */}
            <div className="card overflow-hidden flex flex-col">
                <div className="overflow-x-auto max-h-[620px] relative">
                    <table className="w-full text-xs text-left">
                        <thead className="sticky top-0 bg-navy-900 z-10 border-b border-white/5 text-slate-400 font-semibold uppercase tracking-wider text-[11px]">
                            <tr>
                                <th className="p-3 w-10 text-center">
                                    <input
                                        type="checkbox"
                                        ref={masterCheckboxRef}
                                        checked={isAllCurrentPageSelected}
                                        onChange={handleSelectAllCurrentPage}
                                        className="rounded border-slate-600 bg-navy-800 text-crisis-blue cursor-pointer w-3.5 h-3.5"
                                        aria-label="Select all on current page"
                                    />
                                </th>
                                <th className="p-3">ID</th>
                                <th className="p-3">Type</th>
                                <th className="p-3">Zone / Location</th>
                                <th className="p-3">Severity</th>
                                <th className="p-3">People</th>
                                <th className="p-3">Status</th>
                                <th className="p-3">Time</th>
                                <th className="p-3 text-right">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-white/5">
                            {loading && !initialLoaded ? (
                                Array.from({ length: 10 }).map((_, idx) => (
                                    <tr key={idx} className="animate-pulse">
                                        <td className="p-3"><div className="w-4 h-4 bg-white/5 rounded mx-auto" /></td>
                                        <td className="p-3"><div className="w-16 h-3 bg-white/5 rounded" /></td>
                                        <td className="p-3"><div className="w-24 h-3 bg-white/5 rounded" /></td>
                                        <td className="p-3"><div className="w-36 h-3 bg-white/5 rounded" /></td>
                                        <td className="p-3"><div className="w-16 h-4 bg-white/5 rounded-full" /></td>
                                        <td className="p-3"><div className="w-8 h-3 bg-white/5 rounded" /></td>
                                        <td className="p-3"><div className="w-20 h-4 bg-white/5 rounded-full" /></td>
                                        <td className="p-3"><div className="w-16 h-3 bg-white/5 rounded" /></td>
                                        <td className="p-3"><div className="w-12 h-3 bg-white/5 rounded ml-auto" /></td>
                                    </tr>
                                ))
                            ) : paginatedIncidents.length === 0 ? (
                                <tr>
                                    <td colSpan={9} className="p-12 text-center text-slate-500">
                                        <div className="flex flex-col items-center gap-2">
                                            <AlertTriangle size={32} className="text-slate-600 mb-1" />
                                            <p className="text-sm font-semibold text-slate-300">No incidents match the current filters</p>
                                            <p className="text-xs text-slate-500">Try adjusting your search criteria or filter selections.</p>
                                            {(search || filterType || filterSeverity || filterStatus) && (
                                                <button
                                                    onClick={handleClearFilters}
                                                    className="mt-2 btn-primary text-xs py-1.5 px-3"
                                                >
                                                    Clear All Filters
                                                </button>
                                            )}
                                        </div>
                                    </td>
                                </tr>
                            ) : (
                                paginatedIncidents.map(inc => {
                                    const isSelected = selectedIds.has(inc.id);
                                    return (
                                        <tr
                                            key={inc.id}
                                            onClick={() => openDrawer(inc)}
                                            className={`hover:bg-white/5 transition-colors cursor-pointer ${isSelected ? 'bg-crisis-blue/5' : ''}`}
                                        >
                                            <td className="p-3 text-center" onClick={e => handleToggleRow(inc.id, e)}>
                                                <input
                                                    type="checkbox"
                                                    checked={isSelected}
                                                    onChange={() => { }}
                                                    className="rounded border-slate-600 bg-navy-800 text-crisis-blue cursor-pointer w-3.5 h-3.5"
                                                    aria-label={`Select incident ${inc.id}`}
                                                />
                                            </td>
                                            <td className="p-3 font-mono font-bold text-slate-300">
                                                <div className="flex items-center gap-1">
                                                    <span>{inc.id}</span>
                                                    {inc.is_duplicate && (
                                                        <span className="text-[10px] bg-yellow-500/20 text-yellow-400 border border-yellow-500/40 px-1 py-0.5 rounded font-sans" title={`Duplicate of ${inc.duplicate_of_id}`}>
                                                            ⚠️ DUP
                                                        </span>
                                                    )}
                                                </div>
                                            </td>
                                            <td className="p-3 font-medium text-white">
                                                {inc.incident_type}
                                            </td>
                                            <td className="p-3 text-slate-300 max-w-[220px] truncate" title={`${inc.location} (${inc.zone || 'Central'})`}>
                                                <span className="font-semibold text-slate-200">{inc.zone || 'Central'}</span>
                                                <span className="text-slate-500 ml-1.5">• {inc.location}</span>
                                            </td>
                                            <td className="p-3">
                                                {severityBadge(inc.severity)}
                                            </td>
                                            <td className="p-3 text-slate-300 font-mono">
                                                {inc.people_at_risk}
                                            </td>
                                            <td className="p-3">
                                                {statusBadge(inc.status)}
                                            </td>
                                            <td className="p-3 text-slate-400 font-mono whitespace-nowrap" title={formatAbsoluteTime(inc.created_at)}>
                                                {timeMode === 'relative'
                                                    ? formatRelativeTime(inc.created_at, currentTime)
                                                    : (inc.created_at ? new Date(inc.created_at).toLocaleTimeString() : '—')}
                                            </td>
                                            <td className="p-3 text-right">
                                                <button
                                                    onClick={(e) => { e.stopPropagation(); openDrawer(inc); }}
                                                    className="text-crisis-blue hover:text-blue-400 font-semibold text-xs inline-flex items-center gap-1"
                                                    aria-label={`View quick details for ${inc.id}`}
                                                >
                                                    View <ChevronRight size={14} />
                                                </button>
                                            </td>
                                        </tr>
                                    );
                                })
                            )}
                        </tbody>
                    </table>
                </div>

                {/* Sticky Pagination Bar */}
                <div className="border-t border-white/5 px-4 py-3 bg-navy-900/90 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs">
                    <div className="flex items-center gap-3 text-slate-400">
                        <span>
                            Showing <strong className="text-white">{totalRecords > 0 ? (safePage - 1) * pageSize + 1 : 0}</strong>–<strong className="text-white">{Math.min(safePage * pageSize, totalRecords)}</strong> of <strong className="text-white">{totalRecords}</strong>
                        </span>

                        <div className="flex items-center gap-1.5 ml-2">
                            <span>Rows:</span>
                            <select
                                value={pageSize}
                                onChange={e => {
                                    setPageSize(Number(e.target.value));
                                    setPage(1);
                                }}
                                className="bg-navy-800 text-slate-300 rounded px-2 py-1 border border-white/5 outline-none font-medium cursor-pointer"
                                aria-label="Rows per page"
                            >
                                {PAGE_SIZE_OPTIONS.map(opt => (
                                    <option key={opt} value={opt}>{opt}</option>
                                ))}
                            </select>
                        </div>
                    </div>

                    <div className="flex items-center gap-2">
                        <button
                            onClick={() => setPage(p => Math.max(1, p - 1))}
                            disabled={safePage <= 1}
                            className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-navy-800 hover:bg-navy-700 text-slate-300 disabled:opacity-40 disabled:hover:bg-navy-800 transition-colors font-medium border border-white/5"
                            aria-label="Previous page"
                        >
                            <ChevronLeft size={14} /> Previous
                        </button>

                        <span className="px-2 text-slate-300 font-mono">
                            Page <strong className="text-white">{safePage}</strong> of <strong className="text-white">{totalPages}</strong>
                        </span>

                        <button
                            onClick={() => setPage(p => Math.min(totalPages, p + 1))}
                            disabled={safePage >= totalPages}
                            className="flex items-center gap-1 px-3 py-1.5 rounded-lg bg-navy-800 hover:bg-navy-700 text-slate-300 disabled:opacity-40 disabled:hover:bg-navy-800 transition-colors font-medium border border-white/5"
                            aria-label="Next page"
                        >
                            Next <ChevronRight size={14} />
                        </button>
                    </div>
                </div>
            </div>

            {/* ═══════════════════════════════════════════════════════════
          QUICK-VIEW INCIDENT DRAWER (Right-Side Panel)
      ═══════════════════════════════════════════════════════════ */}
            {drawerIncident && (
                <div
                    className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs flex justify-end animate-in fade-in duration-200"
                    onClick={closeDrawer}
                    role="dialog"
                    aria-modal="true"
                    aria-label={`Incident details for ${drawerIncident.id}`}
                >
                    <div
                        ref={drawerRef}
                        className="w-full sm:w-[480px] lg:w-[560px] h-full bg-navy-900 border-l border-white/10 shadow-2xl flex flex-col overflow-hidden animate-in slide-in-from-right duration-300"
                        onClick={e => e.stopPropagation()}
                    >
                        {/* Drawer Header */}
                        <div className="p-4 border-b border-white/5 flex items-center justify-between shrink-0 bg-navy-950/80">
                            <div>
                                <div className="flex items-center gap-2">
                                    <span className="font-mono text-xs text-slate-400 font-bold">{drawerIncident.id}</span>
                                    {severityBadge(drawerIncident.severity)}
                                    {statusBadge(drawerIncident.status)}
                                </div>
                                <h2 className="text-base font-bold text-white mt-1">
                                    {drawerIncident.incident_type}
                                </h2>
                            </div>

                            <button
                                onClick={closeDrawer}
                                className="w-8 h-8 rounded-lg bg-navy-800 hover:bg-navy-700 text-slate-400 hover:text-white flex items-center justify-center transition-colors"
                                aria-label="Close drawer"
                            >
                                <X size={18} />
                            </button>
                        </div>

                        {/* Drawer Body (Scrollable) */}
                        <div className="flex-1 overflow-y-auto p-4 space-y-5 text-xs">
                            {drawerLoading && (
                                <div className="p-2.5 bg-crisis-blue/10 border border-crisis-blue/20 rounded-lg text-crisis-blue text-xs flex items-center gap-2 animate-pulse">
                                    <span className="w-2 h-2 rounded-full bg-crisis-blue" /> Fetching live intelligence & timeline...
                                </div>
                            )}

                            {/* SECTION 1 — SUMMARY */}
                            <div className="card p-3 space-y-2.5">
                                <h3 className="text-slate-400 font-bold uppercase tracking-wider text-[10px] flex items-center gap-1.5">
                                    <Activity size={13} className="text-crisis-blue" /> Incident Summary
                                </h3>

                                <div className="grid grid-cols-2 gap-2 text-slate-300">
                                    <div>
                                        <span className="text-slate-500 block text-[11px]">Zone</span>
                                        <span className="font-semibold text-white">{drawerIncident.zone || 'Central'}</span>
                                    </div>
                                    <div>
                                        <span className="text-slate-500 block text-[11px]">People at Risk</span>
                                        <span className="font-semibold text-white">{drawerIncident.people_at_risk}</span>
                                    </div>
                                    <div className="col-span-2">
                                        <span className="text-slate-500 block text-[11px]">Location</span>
                                        <span className="font-medium text-slate-200">{drawerIncident.location}</span>
                                    </div>
                                    {drawerIncident.building && (
                                        <div>
                                            <span className="text-slate-500 block text-[11px]">Building</span>
                                            <span className="font-medium text-white">{drawerIncident.building}</span>
                                        </div>
                                    )}
                                    {drawerIncident.floor && (
                                        <div>
                                            <span className="text-slate-500 block text-[11px]">Floor</span>
                                            <span className="font-medium text-white">Floor {drawerIncident.floor}</span>
                                        </div>
                                    )}
                                    {drawerIncident.spread_risk && (
                                        <div>
                                            <span className="text-slate-500 block text-[11px]">Spread Risk</span>
                                            <span className="font-medium text-crisis-orange">{drawerIncident.spread_risk}</span>
                                        </div>
                                    )}
                                    <div>
                                        <span className="text-slate-500 block text-[11px]">Reported</span>
                                        <span className="font-mono text-slate-300" title={formatAbsoluteTime(drawerIncident.created_at)}>
                                            {formatRelativeTime(drawerIncident.created_at, currentTime)}
                                        </span>
                                    </div>
                                    {drawerIncident.updated_at && (
                                        <div>
                                            <span className="text-slate-500 block text-[11px]">Last Updated</span>
                                            <span className="font-mono text-slate-300" title={formatAbsoluteTime(drawerIncident.updated_at)}>
                                                {formatRelativeTime(drawerIncident.updated_at, currentTime)}
                                            </span>
                                        </div>
                                    )}
                                </div>

                                {drawerIncident.description && (
                                    <div className="pt-2 border-t border-white/5">
                                        <span className="text-slate-500 block text-[11px] mb-1">Description</span>
                                        <p className="text-slate-300 leading-relaxed bg-navy-800/60 p-2 rounded">
                                            {drawerIncident.description}
                                        </p>
                                    </div>
                                )}
                            </div>

                            {/* SECTION 2 — LOCATION & MINI MAP */}
                            <div className="card p-3 space-y-2.5">
                                <h3 className="text-slate-400 font-bold uppercase tracking-wider text-[10px] flex items-center gap-1.5">
                                    <MapPin size={13} className="text-crisis-red" /> Geospatial Coordinates & Map
                                </h3>

                                <div className="flex items-center justify-between text-slate-400 font-mono text-[11px] bg-navy-800 p-2 rounded">
                                    <span>Lat: <strong className="text-slate-200">{drawerIncident.latitude.toFixed(4)}</strong></span>
                                    <span>Long: <strong className="text-slate-200">{drawerIncident.longitude.toFixed(4)}</strong></span>
                                </div>

                                <div className="h-44 w-full rounded-lg overflow-hidden border border-white/5 relative z-0">
                                    <MapContainer
                                        center={[drawerIncident.latitude, drawerIncident.longitude]}
                                        zoom={14}
                                        scrollWheelZoom={false}
                                        style={{ height: '100%', width: '100%' }}
                                    >
                                        <TileLayer url="https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png" />
                                        <MiniMapController center={[drawerIncident.latitude, drawerIncident.longitude]} />
                                        <Marker
                                            position={[drawerIncident.latitude, drawerIncident.longitude]}
                                            icon={getMapIcon(drawerIncident.incident_type)}
                                        >
                                            <Popup>
                                                <div className="text-xs">
                                                    <strong>{drawerIncident.incident_type}</strong>
                                                    <div>{drawerIncident.location}</div>
                                                </div>
                                            </Popup>
                                        </Marker>
                                    </MapContainer>
                                </div>
                            </div>

                            {/* SECTION 3 — RESOURCE ASSIGNMENT & AI OPTIMIZER */}
                            <div className="card p-3 space-y-2.5">
                                <h3 className="text-slate-400 font-bold uppercase tracking-wider text-[10px] flex items-center gap-1.5">
                                    <Brain size={13} className="text-crisis-purple" /> Resource Optimization & Dispatch
                                </h3>

                                {drawerRec ? (
                                    <div className="bg-navy-800/80 border border-crisis-purple/20 rounded-lg p-3 space-y-2.5">
                                        <div className="flex items-center justify-between">
                                            <span className="text-[10px] font-bold text-crisis-purple uppercase tracking-wider">
                                                Multi-Factor Recommendation
                                            </span>
                                            <span className="font-mono text-crisis-green font-bold">
                                                {drawerRec.confidence}% Confidence
                                            </span>
                                        </div>

                                        <div className="grid grid-cols-2 gap-2 text-[11px]">
                                            {drawerRec.ambulance_id && (
                                                <div className="flex items-center gap-1.5 text-slate-200">
                                                    <Truck size={13} className="text-crisis-blue" />
                                                    <span>Ambulance: <strong>{drawerRec.ambulance_id}</strong></span>
                                                </div>
                                            )}
                                            {drawerRec.fire_truck_id && (
                                                <div className="flex items-center gap-1.5 text-slate-200">
                                                    <Truck size={13} className="text-crisis-orange" />
                                                    <span>Fire Unit: <strong>{drawerRec.fire_truck_id}</strong></span>
                                                </div>
                                            )}
                                            {drawerRec.hospital_name && (
                                                <div className="flex items-center gap-1.5 text-slate-200 col-span-2">
                                                    <Building2 size={13} className="text-crisis-green" />
                                                    <span>Receiving Hospital: <strong>{drawerRec.hospital_name}</strong></span>
                                                </div>
                                            )}
                                            {drawerRec.route && (
                                                <div className="col-span-2 text-slate-400">
                                                    Route: <strong className="text-slate-200">{drawerRec.route}</strong>
                                                </div>
                                            )}
                                            <div className="col-span-2 flex items-center gap-4 pt-1 text-slate-300 font-mono">
                                                <span>Estimated ETA: <strong className="text-crisis-cyan">{drawerRec.eta_minutes} mins</strong></span>
                                            </div>
                                        </div>

                                        {drawerRec.reasons && drawerRec.reasons.length > 0 && (
                                            <div className="pt-2 border-t border-white/5 space-y-1">
                                                <span className="text-[10px] text-slate-500 uppercase">Rationale:</span>
                                                {drawerRec.reasons.map((r, i) => (
                                                    <div key={i} className="text-[11px] text-slate-300 flex items-start gap-1.5">
                                                        <span className="text-crisis-green font-bold">✓</span> {r}
                                                    </div>
                                                ))}
                                            </div>
                                        )}
                                    </div>
                                ) : (
                                    <div className="p-3 bg-navy-800/50 rounded-lg text-slate-500 text-center">
                                        No active resource recommendation assigned.
                                    </div>
                                )}

                                {/* Action Buttons */}
                                {drawerIncident.status !== 'Resolved' && (
                                    <div className="pt-1">
                                        {drawerIncident.status === 'Detected' || drawerIncident.status === 'Awaiting Response' ? (
                                            <button
                                                onClick={() => handleDrawerDispatch(drawerIncident.id)}
                                                disabled={dispatchingId === drawerIncident.id}
                                                className="btn-danger w-full flex items-center justify-center gap-2 py-2.5 font-bold shadow-lg"
                                                aria-label="Dispatch emergency units"
                                            >
                                                <Send size={15} />
                                                {dispatchingId === drawerIncident.id ? 'Dispatching Units...' : '🚨 DISPATCH EMERGENCY RESPONSE'}
                                            </button>
                                        ) : (
                                            <div className="text-center py-2 px-3 bg-navy-800 rounded text-slate-400 font-medium">
                                                Response In Progress ({drawerIncident.status})
                                            </div>
                                        )}
                                    </div>
                                )}
                            </div>

                            {/* SECTION 4 — CHRONOLOGICAL TIMELINE */}
                            <div className="card p-3 space-y-3">
                                <h3 className="text-slate-400 font-bold uppercase tracking-wider text-[10px] flex items-center gap-1.5">
                                    <Clock size={13} className="text-crisis-cyan" /> Chronological Incident Timeline
                                </h3>

                                {drawerTimeline.length === 0 ? (
                                    <div className="text-slate-500 py-3 text-center">
                                        Loading historical timeline events...
                                    </div>
                                ) : (
                                    <div className="relative pl-5 space-y-4 before:content-[''] before:absolute before:left-2 before:top-2 before:bottom-2 before:w-0.5 before:bg-white/10">
                                        {drawerTimeline.map((evt, idx) => (
                                            <div key={evt.id || idx} className="relative group">
                                                <div className="absolute -left-5 top-0.5 w-3.5 h-3.5 rounded-full bg-navy-900 border-2 border-crisis-blue flex items-center justify-center text-[8px]" />
                                                <div className="text-slate-300">
                                                    <div className="flex items-center justify-between">
                                                        <span className="font-bold text-white text-[11px]">{evt.title}</span>
                                                        <span className="font-mono text-slate-500 text-[10px]" title={formatAbsoluteTime(evt.timestamp)}>
                                                            {formatRelativeTime(evt.timestamp, currentTime)}
                                                        </span>
                                                    </div>
                                                    <p className="text-slate-400 mt-0.5 text-[11px] leading-relaxed">
                                                        {evt.description}
                                                    </p>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* Drawer Footer */}
                        <div className="p-3 border-t border-white/5 bg-navy-950 shrink-0 flex items-center justify-between text-slate-500 text-[11px]">
                            <span>Status: <strong className="text-slate-300">{drawerIncident.status}</strong></span>
                            <button
                                onClick={closeDrawer}
                                className="px-3 py-1.5 rounded bg-navy-800 hover:bg-navy-700 text-slate-300 font-medium transition-colors"
                            >
                                Close Panel
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* ═══════════════════════════════════════════════════════════
          CREATE EMERGENCY MODAL
      ═══════════════════════════════════════════════════════════ */}
            {showCreateModal && (
                <div
                    className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-xs p-4"
                    onClick={() => setShowCreateModal(false)}
                    role="dialog"
                    aria-modal="true"
                    aria-label="Create new emergency incident"
                >
                    <div className="card w-full max-w-lg max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
                        <div className="p-4 border-b border-white/5 flex items-center justify-between sticky top-0 bg-navy-900 z-10">
                            <h2 className="text-base font-bold text-white flex items-center gap-2">
                                <AlertTriangle size={18} className="text-crisis-red" /> Log Emergency Incident
                            </h2>
                            <button onClick={() => setShowCreateModal(false)} className="text-slate-400 hover:text-white" aria-label="Close dialog">
                                <X size={18} />
                            </button>
                        </div>

                        <form onSubmit={handleCreateSubmit} className="p-4 space-y-3 text-xs">
                            <div>
                                <label className="text-slate-400 block mb-1 font-medium">Incident Type</label>
                                <select
                                    value={createForm.incident_type}
                                    onChange={e => setCreateForm({ ...createForm, incident_type: e.target.value })}
                                    className="w-full bg-navy-800 text-white rounded-lg px-3 py-2 border border-white/5 outline-none"
                                >
                                    {TYPES.map(t => <option key={t} value={t}>{t}</option>)}
                                </select>
                            </div>

                            <div className="grid grid-cols-2 gap-3">
                                <div>
                                    <label className="text-slate-400 block mb-1 font-medium">Zone</label>
                                    <input
                                        value={createForm.zone}
                                        onChange={e => setCreateForm({ ...createForm, zone: e.target.value })}
                                        placeholder="e.g. HITEC City"
                                        required
                                        className="w-full bg-navy-800 text-white rounded-lg px-3 py-2 border border-white/5 outline-none"
                                    />
                                </div>
                                <div>
                                    <label className="text-slate-400 block mb-1 font-medium">Severity</label>
                                    <select
                                        value={createForm.severity}
                                        onChange={e => setCreateForm({ ...createForm, severity: e.target.value })}
                                        className="w-full bg-navy-800 text-white rounded-lg px-3 py-2 border border-white/5 outline-none"
                                    >
                                        <option value="Auto Detect">Auto Detect</option>
                                        {SEVERITIES.map(s => <option key={s} value={s}>{s}</option>)}
                                    </select>
                                </div>
                            </div>

                            <div>
                                <label className="text-slate-400 block mb-1 font-medium">Location Details</label>
                                <input
                                    value={createForm.location}
                                    onChange={e => setCreateForm({ ...createForm, location: e.target.value })}
                                    required
                                    placeholder="e.g. Cyber Towers Main Junction"
                                    className="w-full bg-navy-800 text-white rounded-lg px-3 py-2 border border-white/5 outline-none"
                                />
                            </div>

                            <div className="grid grid-cols-2 gap-3">
                                <div>
                                    <label className="text-slate-400 block mb-1 font-medium">Latitude</label>
                                    <input
                                        type="number"
                                        step="0.0001"
                                        value={createForm.latitude}
                                        onChange={e => setCreateForm({ ...createForm, latitude: parseFloat(e.target.value) || 0 })}
                                        className="w-full bg-navy-800 text-white rounded-lg px-3 py-2 border border-white/5 outline-none font-mono"
                                    />
                                </div>
                                <div>
                                    <label className="text-slate-400 block mb-1 font-medium">Longitude</label>
                                    <input
                                        type="number"
                                        step="0.0001"
                                        value={createForm.longitude}
                                        onChange={e => setCreateForm({ ...createForm, longitude: parseFloat(e.target.value) || 0 })}
                                        className="w-full bg-navy-800 text-white rounded-lg px-3 py-2 border border-white/5 outline-none font-mono"
                                    />
                                </div>
                            </div>

                            <div className="grid grid-cols-3 gap-3">
                                <div>
                                    <label className="text-slate-400 block mb-1 font-medium">People at Risk</label>
                                    <input
                                        type="number"
                                        min="0"
                                        value={createForm.people_at_risk}
                                        onChange={e => setCreateForm({ ...createForm, people_at_risk: parseInt(e.target.value) || 0 })}
                                        className="w-full bg-navy-800 text-white rounded-lg px-3 py-2 border border-white/5 outline-none"
                                    />
                                </div>
                                <div>
                                    <label className="text-slate-400 block mb-1 font-medium">Building</label>
                                    <input
                                        value={createForm.building}
                                        onChange={e => setCreateForm({ ...createForm, building: e.target.value })}
                                        placeholder="Optional"
                                        className="w-full bg-navy-800 text-white rounded-lg px-3 py-2 border border-white/5 outline-none"
                                    />
                                </div>
                                <div>
                                    <label className="text-slate-400 block mb-1 font-medium">Floor</label>
                                    <input
                                        type="number"
                                        value={createForm.floor}
                                        onChange={e => setCreateForm({ ...createForm, floor: parseInt(e.target.value) || 0 })}
                                        className="w-full bg-navy-800 text-white rounded-lg px-3 py-2 border border-white/5 outline-none"
                                    />
                                </div>
                            </div>

                            <div>
                                <label className="text-slate-400 block mb-1 font-medium">Operational Description</label>
                                <textarea
                                    value={createForm.description}
                                    onChange={e => setCreateForm({ ...createForm, description: e.target.value })}
                                    rows={3}
                                    placeholder="Describe emergency conditions, casualties, hazards..."
                                    className="w-full bg-navy-800 text-white rounded-lg px-3 py-2 border border-white/5 outline-none resize-none"
                                />
                            </div>

                            <div className="pt-2">
                                <button type="submit" disabled={loading} className="btn-primary w-full py-2.5 font-bold">
                                    {loading ? 'Creating Incident...' : '🚨 CREATE & ANALYZE INCIDENT'}
                                </button>
                            </div>
                        </form>
                    </div>
                </div>
            )}
        </div>
    );
}
