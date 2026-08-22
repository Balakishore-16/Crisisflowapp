/* ─── Leaflet MarkerCluster Group Component ─── */
import { useEffect, useRef } from 'react';
import { useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet.markercluster';
import 'leaflet.markercluster/dist/MarkerCluster.css';
import 'leaflet.markercluster/dist/MarkerCluster.Default.css';

export default function MarkerClusterGroup() {
    const map = useMap();
    const clusterGroupRef = useRef<L.MarkerClusterGroup | null>(null);

    useEffect(() => {
        if (!clusterGroupRef.current) {
            clusterGroupRef.current = L.markerClusterGroup({
                maxClusterRadius: 40,
                spiderfyOnMaxZoom: true,
                showCoverageOnHover: false,
                zoomToBoundsOnClick: true,
                disableClusteringAtZoom: 16,
            });
            map.addLayer(clusterGroupRef.current);
        }

        return () => {
            if (clusterGroupRef.current) {
                map.removeLayer(clusterGroupRef.current);
                clusterGroupRef.current = null;
            }
        };
    }, [map]);

    return null;
}
