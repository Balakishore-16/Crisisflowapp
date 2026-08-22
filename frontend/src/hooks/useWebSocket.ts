/* ─── WebSocket Hook ─── */
import { useEffect, useRef, useCallback, useState } from 'react';
import type { WSEvent } from '../types';

type WSCallback = (event: WSEvent) => void;

export function useWebSocket(onEvent: WSCallback) {
    const wsRef = useRef<WebSocket | null>(null);
    const [connected, setConnected] = useState(false);
    const callbackRef = useRef(onEvent);
    callbackRef.current = onEvent;

    const connect = useCallback(() => {
        const protocol = window.location.protocol === 'https:' ? 'wss' : 'ws';
        const wsUrl = `${protocol}://${window.location.host}/ws/api/realtime`;
        const ws = new WebSocket(wsUrl);

        ws.onopen = () => {
            setConnected(true);
            console.log('🔌 WebSocket connected');
        };

        ws.onmessage = (evt) => {
            try {
                const data: WSEvent = JSON.parse(evt.data);
                callbackRef.current(data);
            } catch (e) {
                console.error('WS parse error:', e);
            }
        };

        ws.onclose = () => {
            setConnected(false);
            console.log('🔌 WebSocket disconnected — reconnecting in 3s');
            setTimeout(connect, 3000);
        };

        ws.onerror = () => {
            ws.close();
        };

        wsRef.current = ws;
    }, []);

    useEffect(() => {
        connect();
        return () => {
            if (wsRef.current) wsRef.current.close();
        };
    }, [connect]);

    return { connected };
}
