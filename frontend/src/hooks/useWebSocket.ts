import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import type { SourceDocument, WebSocketEvent } from "../types";

type UseWebSocketOptions = {
  onToken: (token: string) => void;
  onSources: (sources: SourceDocument[]) => void;
  onDone: (metadata: Record<string, unknown>) => void;
  onError: (message: string) => void;
};

const DEFAULT_WS_URL = "ws://localhost:8000/ws/chat";

export function useWebSocket(options: UseWebSocketOptions) {
  const wsUrl = useMemo(
    () => import.meta.env.VITE_CHAT_WS_URL ?? DEFAULT_WS_URL,
    [],
  );
  const socketRef = useRef<WebSocket | null>(null);
  const retryRef = useRef(0);
  const reconnectTimerRef = useRef<number | null>(null);
  const shouldReconnectRef = useRef(true);
  const [connected, setConnected] = useState(false);

  const connect = useCallback(() => {
    if (!shouldReconnectRef.current || socketRef.current?.readyState === WebSocket.OPEN) {
      return;
    }

    const socket = new WebSocket(wsUrl);
    socketRef.current = socket;

    socket.onopen = () => {
      retryRef.current = 0;
      setConnected(true);
    };

    socket.onclose = () => {
      setConnected(false);
      if (!shouldReconnectRef.current) {
        return;
      }
      const delay = Math.min(1000 * 2 ** retryRef.current, 15000);
      retryRef.current += 1;
      reconnectTimerRef.current = window.setTimeout(connect, delay);
    };

    socket.onerror = () => {
      options.onError("Connection error. Reconnecting...");
      socket.close();
    };

    socket.onmessage = (event) => {
      let payload: WebSocketEvent;
      try {
        payload = JSON.parse(event.data) as WebSocketEvent;
      } catch {
        options.onError("Received an invalid chat event.");
        return;
      }
      if (payload.type === "token") {
        options.onToken(payload.data);
      } else if (payload.type === "sources") {
        options.onSources(payload.data);
      } else if (payload.type === "done") {
        options.onDone(payload.metadata);
      } else if (payload.type === "error") {
        options.onError(payload.message);
      }
    };
  }, [options, wsUrl]);

  useEffect(() => {
    shouldReconnectRef.current = true;
    connect();
    return () => {
      shouldReconnectRef.current = false;
      if (reconnectTimerRef.current) {
        window.clearTimeout(reconnectTimerRef.current);
      }
      socketRef.current?.close();
    };
  }, [connect]);

  const sendQuery = useCallback((sessionId: string, message: string) => {
    const socket = socketRef.current;
    if (!socket || socket.readyState !== WebSocket.OPEN) {
      options.onError("Chat is reconnecting. Please try again in a moment.");
      return false;
    }

    socket.send(JSON.stringify({ type: "query", session_id: sessionId, message }));
    return true;
  }, [options]);

  return { connected, sendQuery };
}
