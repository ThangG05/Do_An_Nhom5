"use client";

import { createContext, useCallback, useContext, useEffect, useRef, useState } from "react";
import { createWebSocketTicket } from "@/lib/api";
import { getAccessToken } from "@/lib/auth";

type RealtimeContextValue = { send: (payload: Record<string, unknown>) => void; connected: boolean };
const RealtimeContext = createContext<RealtimeContextValue>({
  send: () => { throw new Error("Kết nối thời gian thực chưa sẵn sàng."); },
  connected: false,
});

function socketUrl(ticket: string) {
  const base = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1").replace(/^http/, "ws");
  return `${base}/chat/ws?ticket=${encodeURIComponent(ticket)}`;
}

/** Maintains exactly one authenticated WebSocket for the whole browser tab. */
export function RealtimeProvider({ children }: { children: React.ReactNode }) {
  const socketRef = useRef<WebSocket | null>(null);
  const retryRef = useRef<number | null>(null);
  const disposedRef = useRef(false);
  const [version, setVersion] = useState(0);
  const [connected, setConnected] = useState(false);

  const send = useCallback((payload: Record<string, unknown>) => {
    const socket = socketRef.current;
    if (!socket || socket.readyState !== WebSocket.OPEN) throw new Error("Kết nối thời gian thực chưa sẵn sàng.");
    socket.send(JSON.stringify(payload));
  }, []);

  useEffect(() => {
    const refresh = () => setVersion(value => value + 1);
    window.addEventListener("hvnh-auth-changed", refresh);
    return () => window.removeEventListener("hvnh-auth-changed", refresh);
  }, []);

  useEffect(() => {
    disposedRef.current = false;
    if (!getAccessToken()) return;
    let heartbeat: number | null = null;

    const scheduleRetry = () => {
      if (disposedRef.current || retryRef.current !== null || !getAccessToken()) return;
      retryRef.current = window.setTimeout(() => { retryRef.current = null; void connect(); }, 2_000);
    };
    const connect = async () => {
      try {
        const ticket = await createWebSocketTicket();
        if (disposedRef.current) return;
        const socket = new WebSocket(socketUrl(ticket));
        socketRef.current = socket;
        socket.onopen = () => { setConnected(true); };
        socket.onmessage = event => {
          try {
            const data = JSON.parse(event.data);
            window.dispatchEvent(new CustomEvent("hvnh-realtime", { detail: data }));
            if (data.event === "notification.created") {
              window.dispatchEvent(new Event(data.type === "MESSAGE" ? "messages-changed" : "notifications-changed"));
            }
          } catch { /* Ignore malformed frames without breaking the connection. */ }
        };
        socket.onclose = () => {
          if (heartbeat !== null) { window.clearInterval(heartbeat); heartbeat = null; }
          if (socketRef.current === socket) socketRef.current = null;
          setConnected(false);
          scheduleRetry();
        };
        socket.onerror = () => socket.close();
        heartbeat = window.setInterval(() => { if (socket.readyState === WebSocket.OPEN) socket.send("ping"); }, 25_000);
      } catch { scheduleRetry(); }
    };
    void connect();
    return () => {
      disposedRef.current = true;
      setConnected(false);
      if (retryRef.current !== null) window.clearTimeout(retryRef.current);
      if (heartbeat !== null) window.clearInterval(heartbeat);
      socketRef.current?.close();
      socketRef.current = null;
    };
  }, [version]);

  return <RealtimeContext.Provider value={{ send, connected }}>{children}</RealtimeContext.Provider>;
}

export function useRealtime() {
  return useContext(RealtimeContext);
}
