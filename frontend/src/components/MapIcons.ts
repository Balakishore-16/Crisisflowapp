/* ─── CrisisFlow Professional SVG Emergency Map Icons ─── */
import L from 'leaflet';

/**
 * Generates status dot HTML indicator
 * LIVE = green pulse, STALE = yellow, OFFLINE = gray
 */
const getStatusDotHtml = (source?: string, status?: string) => {
    if (status === 'Offline') {
        return `<span style="position:absolute;top:-2px;right:-2px;width:10px;height:10px;border-radius:50%;background:#64748b;border:2px solid #ffffff"></span>`;
    }
    if (source === 'LIVE_GPS' || source === 'SIMULATION') {
        return `<span style="position:absolute;top:-2px;right:-2px;width:10px;height:10px;border-radius:50%;background:#22c55e;border:2px solid #ffffff;box-shadow:0 0 6px #22c55e"></span>`;
    }
    return `<span style="position:absolute;top:-2px;right:-2px;width:10px;height:10px;border-radius:50%;background:#eab308;border:2px solid #ffffff"></span>`;
};

/**
 * Rotated heading arrow pointer overlay for moving vehicles
 */
const getHeadingArrowHtml = (heading?: number) => {
    if (heading === undefined || heading === null) return '';
    return `<div style="position:absolute;width:100%;height:100%;top:0;left:0;transform:rotate(${heading}deg);pointer-events:none;display:flex;justify-content:center;align-items:-start">
        <div style="width:0;height:0;border-left:4px solid transparent;border-right:4px solid transparent;border-bottom:7px solid #ffffff;margin-top:-6px"></div>
    </div>`;
};

// ─── SVG PATH STRINGS (Clean emergency command center vector line-art) ───

// Incident Alert (Triangle Warning)
const SVG_ALERT = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></svg>`;

// Warning Exclamation
const SVG_WARNING = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><line x1="12" y1="8" x2="12" y2="12"/><line x1="12" y1="16" x2="12.01" y2="16"/></svg>`;

// Flame Incident
const SVG_FIRE = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M8.5 14.5A2.5 2.5 0 0 0 11 12c0-1.38-.5-2-1-3-1.072-2.143-.224-4.054 2-6 .5 2.5 2 4.9 4 6.5 2 1.6 3 3.5 3 5.5a7 7 0 1 1-14 0c0-1.153.433-2.294 1-3a2.5 2.5 0 0 0 2.5 2.5z"/></svg>`;

// Vehicle Collision / Accident
const SVG_ACCIDENT = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 17h2c.6 0 1-.4 1-1v-3c0-.9-.7-1.7-1.5-1.9C18.7 10.6 16 10 16 10s-1.3-1.4-2.2-2.3c-.5-.4-1.1-.7-1.8-.7H5c-.6 0-1.1.4-1.4.9l-1.4 2.9A3.7 3.7 0 0 0 2 12v4c0 .6.4 1 1 1h2"/><circle cx="7" cy="17" r="2"/><circle cx="17" cy="17" r="2"/><path d="M5 10h11"/></svg>`;

// Ambulance SVG
const SVG_AMBULANCE = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><rect x="1" y="6" width="15" height="10" rx="2"/><path d="M16 8h4l3 3v5h-7V8z"/><circle cx="5.5" cy="18.5" r="2.5"/><circle cx="18.5" cy="18.5" r="2.5"/><path d="M7 11h4M9 9v4"/></svg>`;

// Fire Truck SVG
const SVG_FIRE_TRUCK = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="1" y="8" width="14" height="8" rx="1"/><path d="M15 10h5l3 3v3h-8v-6z"/><circle cx="5.5" cy="18.5" r="2.5"/><circle cx="17.5" cy="18.5" r="2.5"/><path d="M6 5l3 3M11 5L8 8"/></svg>`;

// Hospital Medical Cross SVG
const SVG_HOSPITAL = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="M12 6v12M6 12h12"/><rect x="3" y="3" width="18" height="18" rx="4"/></svg>`;

// Live Target Navigation SVG
const SVG_TARGET = `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polygon points="12 2 15 8 12 6 9 8 12 2"/><circle cx="12" cy="12" r="3"/></svg>`;

// ─── ICON FACTORIES ───

/**
 * Creates clean Incident Marker based on Severity
 */
export const createIncidentSvgIcon = (severity: string, incidentType: string) => {
    let bgColor = '#eab308'; // Medium yellow
    let svgIcon = SVG_WARNING;
    let size = 30;

    if (severity === 'Critical') {
        bgColor = '#dc2626'; // Red
        svgIcon = SVG_ALERT;
        size = 34;
    } else if (severity === 'High') {
        bgColor = '#ea580c'; // Orange
        svgIcon = incidentType.includes('Fire') ? SVG_FIRE : (incidentType.includes('Accident') ? SVG_ACCIDENT : SVG_ALERT);
        size = 32;
    } else if (severity === 'Low') {
        bgColor = '#2563eb'; // Blue dot
        size = 24;
        return L.divIcon({
            className: 'custom-leaflet-marker',
            html: `<div style="background:#2563eb;width:16px;height:16px;border-radius:50%;border:2px solid #ffffff;box-shadow:0 2px 6px rgba(0,0,0,0.3)"></div>`,
            iconSize: [16, 16],
            iconAnchor: [8, 8],
        });
    }

    return L.divIcon({
        className: 'custom-leaflet-marker',
        html: `<div style="position:relative;background:${bgColor};width:${size}px;height:${size}px;border-radius:50%;display:flex;align-items:center;justify-content:center;color:#ffffff;border:2.5px solid #ffffff;box-shadow:0 3px 10px rgba(0,0,0,0.35)">${svgIcon}</div>`,
        iconSize: [size, size],
        iconAnchor: [size / 2, size / 2],
    });
};

/**
 * Creates Ambulance Marker with optional Heading Arrow and Live Status Dot
 */
export const createAmbulanceSvgIcon = (heading?: number, source?: string, status?: string) => {
    const statusDot = getStatusDotHtml(source, status);
    const headingArrow = getHeadingArrowHtml(heading);

    return L.divIcon({
        className: 'custom-leaflet-marker smooth-marker-move',
        html: `<div style="position:relative;background:#0284c7;width:34px;height:34px;border-radius:50%;display:flex;align-items:center;justify-content:center;color:#ffffff;border:2.5px solid #ffffff;box-shadow:0 3px 10px rgba(2,132,199,0.4)">
            ${SVG_AMBULANCE}
            ${statusDot}
            ${headingArrow}
        </div>`,
        iconSize: [34, 34],
        iconAnchor: [17, 17],
    });
};

/**
 * Creates Fire Station / Rescue Unit Marker
 */
export const createFireStationSvgIcon = () => {
    return L.divIcon({
        className: 'custom-leaflet-marker',
        html: `<div style="position:relative;background:#ea580c;width:32px;height:32px;border-radius:50%;display:flex;align-items:center;justify-content:center;color:#ffffff;border:2.5px solid #ffffff;box-shadow:0 3px 10px rgba(234,88,12,0.4)">
            ${SVG_FIRE_TRUCK}
        </div>`,
        iconSize: [32, 32],
        iconAnchor: [16, 16],
    });
};

/**
 * Creates Hospital Facility Marker
 */
export const createHospitalSvgIcon = () => {
    return L.divIcon({
        className: 'custom-leaflet-marker',
        html: `<div style="position:relative;background:#16a34a;width:34px;height:34px;border-radius:50%;display:flex;align-items:center;justify-content:center;color:#ffffff;border:2.5px solid #ffffff;box-shadow:0 3px 10px rgba(22,163,74,0.4)">
            ${SVG_HOSPITAL}
        </div>`,
        iconSize: [34, 34],
        iconAnchor: [17, 17],
    });
};

/**
 * Creates User Live GPS Marker
 */
export const createUserLiveGpsSvgIcon = () => {
    return L.divIcon({
        className: 'custom-leaflet-marker live-pulse',
        html: `<div style="position:relative;background:#dc2626;width:38px;height:38px;border-radius:50%;display:flex;align-items:center;justify-content:center;color:#ffffff;border:3px solid #ffffff;box-shadow:0 0 12px rgba(220,38,38,0.6)">
            ${SVG_TARGET}
        </div>`,
        iconSize: [38, 38],
        iconAnchor: [19, 19],
    });
};
