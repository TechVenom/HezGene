import { useRef, useCallback, useEffect, useState } from 'react';
import { WS_BASE } from '../api';

export interface WSMessage {
  stage: string;
  function?: string;
  message?: string;
  warning?: string;
  mutant?: any;
  mutant_result?: any;
  mutant_index?: number;
  rankings?: any[];
  baseline_score?: number;
  winner?: any;
  original_source?: string;
  dna?: any;
  results?: any[];
  total_mutants?: number;
  traceback?: string;
  [key: string]: any;
}

export function useWebSocket(sessionId: string | null) {
  const wsRef = useRef<WebSocket | null>(null);
  const [messages, setMessages] = useState<WSMessage[]>([]);
  const [connected, setConnected] = useState(false);
  const [currentStage, setCurrentStage] = useState<string>('');
  const reconnectAttempt = useRef(0);
  const reconnectTimeout = useRef<any>(null);

  const connect = useCallback(() => {
    if (!sessionId) return;
    
    // Don't connect if already connecting or open
    if (wsRef.current && (wsRef.current.readyState === WebSocket.OPEN || wsRef.current.readyState === WebSocket.CONNECTING)) {
        return;
    }

    const ws = new WebSocket(`${WS_BASE}/ws/evolve/${sessionId}`);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
      reconnectAttempt.current = 0; // Reset on successful connection
    };

    ws.onmessage = (event) => {
      try {
        // Sanitize invalid JSON values like Infinity or NaN that might be sent by Python
        const sanitizedData = event.data
          .replace(/:\s*Infinity/g, ': -1')
          .replace(/:\s*-Infinity/g, ': -1')
          .replace(/:\s*NaN/g, ': null');
          
        const data: WSMessage = JSON.parse(sanitizedData);
        if (data.type === 'pong') return;
        setMessages((prev) => [...prev, data]);
        if (data.stage) setCurrentStage(data.stage);
      } catch {
        // ignore parse errors
      }
    };

    ws.onclose = (event) => {
      setConnected(false);
      wsRef.current = null;
      
      // Connection dropped — reconnect with backoff
      if (!event.wasClean && sessionId) {
        const delay = Math.min(1000 * Math.pow(2, reconnectAttempt.current), 30000);
        reconnectTimeout.current = setTimeout(() => {
            reconnectAttempt.current += 1;
            connect();
        }, delay);
      }
    };

    ws.onerror = () => {
      setConnected(false);
    };
  }, [sessionId]);

  const disconnect = useCallback(() => {
    if (reconnectTimeout.current) clearTimeout(reconnectTimeout.current);
    if (wsRef.current) {
      wsRef.current.close(1000, "Clean disconnect");
      wsRef.current = null;
    }
  }, []);

  const reset = useCallback(() => {
    setMessages([]);
    setCurrentStage('');
  }, []);

  // Auto-connect when sessionId changes
  useEffect(() => {
    if (sessionId) {
      connect();
    }
    return () => {
      disconnect();
    };
  }, [sessionId, connect, disconnect]);

  // Keep-alive ping
  useEffect(() => {
    if (!connected || !wsRef.current) return;
    const interval = setInterval(() => {
      if (wsRef.current?.readyState === WebSocket.OPEN) {
        wsRef.current.send('ping');
      }
    }, 15000);
    return () => clearInterval(interval);
  }, [connected]);

  return {
    messages,
    connected,
    currentStage,
    connect,
    disconnect,
    reset,
  };
}
